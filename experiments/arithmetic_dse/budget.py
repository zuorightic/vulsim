"""Shared, fail-closed physical-backend ledger, charged before every launch.

The repository checkpoint bootstraps a clone with past usage, never zero usage.
Unfinished reservations remain charged at their full time allowance. Physical stages and experiment generator/validation/support leaves are charged.
Outer wrappers are excluded to avoid double counting.
"""
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]
POLICY = ROOT/'experiments/arithmetic_dse/configs/backend_policy_v5.json'
CHECKPOINT = ROOT/'experiments/arithmetic/evidence/step5/usage_before.json'
LEDGER = ROOT/'experiments/arithmetic/backend_usage.json'
STAGE_LIMITS = {'synth':'max_synthesis_calls', 'grt':'max_global_route_calls',
                'final':'max_detailed_route_calls'}


class BudgetExceeded(RuntimeError):
    pass


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def usage(entries):
    return {**{stage:sum(e['stage'] == stage for e in entries) for stage in STAGE_LIMITS},
            'support_calls':sum(e['stage'] is None for e in entries),
            'walltime_s':sum(e['walltime_s'] for e in entries),
            'CPU_time_s':sum(e['CPU_time_s'] for e in entries),
            'pending':sum(e['status'] == 'reserved' for e in entries)}


def cpu_seconds(resource_log):
    text = Path(resource_log).read_text()
    values = re.findall(r'(?:User|System) time \(seconds\):\s*([\d.]+)', text)
    if len(values) != 2:
        raise ValueError('missing GNU time CPU usage')
    return sum(map(float, values))


class Ledger:
    def __init__(self, path=LEDGER, policy=POLICY, checkpoint=CHECKPOINT):
        self.path, self.policy, self.checkpoint = map(Path, (path, policy, checkpoint))

    @contextmanager
    def _transaction(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(self.path.suffix+'.lock')
        # The persistent marker prevents deleting only the ledger to replenish
        # usage. An intentional clone has neither the live ledger nor marker.
        with lock_path.open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            lock.seek(0)
            initialized = bool(lock.read())
            if self.path.exists():
                state = json.loads(self.path.read_text())
                if state['policy_sha256'] != digest(self.policy):
                    raise ValueError('budget policy changed: explicit versioned ledger migration required')
                if state['checkpoint_sha256'] != digest(self.checkpoint):
                    raise ValueError('budget checkpoint changed: explicit ledger migration required')
            else:
                if initialized:
                    raise ValueError('live budget ledger missing after initialization; restore it from evidence')
                checkpoint = json.loads(self.checkpoint.read_text())
                state = {'version':'physical-budget-ledger-v1', 'policy_sha256':digest(self.policy),
                         'checkpoint_sha256':digest(self.checkpoint), 'entries':checkpoint['entries']}
            yield state
            state['usage'] = usage(state['entries'])
            with tempfile.NamedTemporaryFile(mode='w', dir=self.path.parent, delete=False) as output:
                temporary = Path(output.name)
                json.dump(state, output, ensure_ascii=False, indent=2)
                output.write('\n')
                output.flush()
                os.fsync(output.fileno())
            os.replace(temporary, self.path)
            lock.seek(0)
            lock.write('initialized\n')
            lock.truncate()
            lock.flush()
            os.fsync(lock.fileno())

    def summary(self):
        with self._transaction() as state:
            return usage(state['entries'])

    def migrate(self, previous_policy, previous_checkpoint, reason):
        """Explicit migration; preserve every entry and require a matching checkpoint.

        The old transaction validates its hashes and holds the same ledger lock.
        A policy edit never silently invokes this operation.
        """
        old = Ledger(self.path, previous_policy, previous_checkpoint)
        if not reason.strip():
            raise ValueError('migration reason required')
        with old._transaction() as state:
            total = usage(state['entries'])
            if total['pending']:
                raise ValueError('cannot migrate an unsettled ledger')
            if json.loads(self.checkpoint.read_text())['entries'] != state['entries']:
                raise ValueError('migration checkpoint must preserve every historical entry')
            limits = json.loads(self.policy.read_text())['resources']
            if (any(total[k] > limits[v] for k,v in STAGE_LIMITS.items()) or
                    total['walltime_s'] > limits['max_global_walltime_h']*3600 or
                    total['CPU_time_s'] > limits['max_tool_CPU_time_h']*3600):
                raise ValueError('new policy cannot fund historical usage')
            audit = {'reason':reason, 'at':datetime.now(timezone.utc).isoformat(),
                     'from_policy_sha256':state['policy_sha256'],
                     'from_checkpoint_sha256':state['checkpoint_sha256'],
                     'to_policy_sha256':digest(self.policy),
                     'to_checkpoint_sha256':digest(self.checkpoint), 'usage':total}
            state.setdefault('migrations', []).append(audit)
            state['policy_sha256'] = digest(self.policy)
            state['checkpoint_sha256'] = digest(self.checkpoint)
            return audit

    def reserve(self, stage, timeout_s, threads, purpose, command, output, *, context=None):
        if stage not in [None, *STAGE_LIMITS]:
            raise ValueError('unknown physical stage')
        if not math.isfinite(timeout_s) or timeout_s <= 0 or threads < 1:
            raise ValueError('invalid resource reservation')
        if context is not None:
            allowed={'target_platform','admission_id','admission_sha256','task_id','model_version','sample_id','case_id'}
            if (not isinstance(context,dict) or context.keys()-allowed
                    or any(not isinstance(v,str) or not v for v in context.values())):
                raise ValueError('invalid platform/admission accounting context')
        policy = json.loads(self.policy.read_text())['resources']
        with self._transaction() as state:
            total = usage(state['entries'])
            # Serial physical jobs: a crashed reservation blocks admission until
            # explicitly reconciled with its command evidence, never auto-refunded.
            if total['pending']:
                raise BudgetExceeded('unfinished backend reservation requires evidence reconciliation')
            if stage and total[stage] >= policy[STAGE_LIMITS[stage]]:
                raise BudgetExceeded(f'{stage} call cap exhausted before launch')
            # GNU time is actual CPU usage, not threads times wall time. Reserve
            # an explicit CPU allowance and enforce it with run_command as well.
            cpu_allowance = min(timeout_s*threads, policy['max_tool_CPU_time_h']*3600-total['CPU_time_s'])
            if (total['walltime_s']+timeout_s > policy['max_global_walltime_h']*3600
                or cpu_allowance <= 0):
                raise BudgetExceeded('cumulative time budget exhausted before launch')
            reservation = {'id':uuid.uuid4().hex, 'kind':'live', 'stage':stage, 'status':'reserved',
                           'purpose':purpose, 'command':list(map(str, command)), 'output':str(output),
                           'reserved_at':datetime.now(timezone.utc).isoformat(),
                           'walltime_s':timeout_s, 'CPU_time_s':cpu_allowance}
            if context is not None:
                reservation.update(context)
            state['entries'].append(reservation)
            return reservation.copy()

    def finish(self, reservation, record):
        with self._transaction() as state:
            entry = next(e for e in state['entries'] if e['id'] == reservation['id'])
            if entry['status'] != 'reserved':
                raise ValueError('reservation already settled')
            entry.update(status='completed' if record['exit_code'] == 0 else 'failed',
                         walltime_s=record['walltime_s'], exit_code=record['exit_code'],
                         timed_out=record['timed_out'], command_record=record['log'].removesuffix('.log')+'.command.json')
            try:
                entry['CPU_time_s'] = cpu_seconds(record['gnu_time'])
                entry['CPU_accounting'] = 'GNU_time_leaf_command'
            except (OSError, ValueError):
                entry['CPU_accounting'] = 'full_reservation_missing_CPU_evidence'


def usage_by(entries,field):
    if field not in ('target_platform','admission_id','model_version'):
        raise ValueError('unsupported accounting dimension')
    keys=sorted({e.get(field,'historical_unattributed') for e in entries})
    return {key:usage([e for e in entries if e.get(field,'historical_unattributed')==key]) for key in keys}


def stage_plan(tasks,historical,resources,*,support_walltime_s=0):
    """Fund an explicit platform/stage cold-run list; never assume cache reuse."""
    if (not tasks or len({t['id'] for t in tasks})!=len(tasks)
            or not math.isfinite(support_walltime_s) or support_walltime_s<0):
        raise ValueError('finite unique nonempty task list required')
    counts={s:0 for s in STAGE_LIMITS}
    by_platform={}
    order=list(STAGE_LIMITS)
    for task in tasks:
        if task['platform'] not in ('asap7','nangate45','sky130hd','gf180') or task['stage'] not in order:
            raise ValueError('unsupported task platform/stage')
        if any(not math.isfinite(task[k]) or task[k]<=0 for k in ('period_ps','abc_target_ps')):
            raise ValueError('both physical target axes are required')
        local=by_platform.setdefault(task['platform'],{s:0 for s in order})
        for stage in order[:order.index(task['stage'])+1]:
            counts[stage]+=1;local[stage]+=1
    requested={s:historical[s]+counts[s] for s in counts}
    shortfall={s:max(0,requested[s]-resources[k]) for s,k in STAGE_LIMITS.items()}
    wall=(counts['synth']*resources['synthesis_timeout_s']
          +counts['grt']*resources['floorplan_through_global_route_timeout_s']
          +counts['final']*resources['detailed_route_extraction_timeout_s']+support_walltime_s)
    cpu=wall*resources['threads_per_tool']
    time_funded=(historical['walltime_s']+wall<=resources['max_global_walltime_h']*3600
                 and historical['CPU_time_s']+cpu<=resources['max_tool_CPU_time_h']*3600)
    return {'status':'ready' if not historical['pending'] and not any(shortfall.values()) and time_funded else 'blocked',
            'new_calls':counts,'new_calls_by_platform':by_platform,'requested_calls':requested,
            'call_shortfall':shortfall,'worst_case_leaf_walltime_s':wall,'CPU_envelope_s':cpu,
            'time_funded':time_funded,'cold_runs':True,'cache_credit':0,'main_matrix_authorized':False}


def main():
    import argparse
    from .reference import case_manifest
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-plan', action='store_true', help='require a ready revised stage admission package')
    args = parser.parse_args()
    ledger=Ledger()
    history = ledger.summary()
    entries=json.loads(ledger.path.read_text())['entries']
    from .contracts import check_partition
    scope = check_partition(case_manifest())
    print(json.dumps({'usage':history,'by_platform':usage_by(entries,'target_platform'),'by_admission':usage_by(entries,'admission_id'),'scope':scope,
        'status':'pending_revised_platform_stage_admission',
        'effective_policy':str(POLICY.relative_to(ROOT)),
        'resource_caps_unchanged':True,
        'reason':'actual platform/stage list, capacity and funding must be validated in steps3_5_7; the old nine-case forecast is retired',
        'cold_main_matrix_only':{'synth':688,'grt':688,'includes_training_or_rechecks':False}},indent=2))
    return 1 if args.check_plan else 0


if __name__ == '__main__':
    raise SystemExit(main())
