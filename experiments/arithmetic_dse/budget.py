"""Shared, fail-closed physical-backend ledger, charged before every launch.

The repository checkpoint bootstraps a clone with past usage, never zero usage.
Unfinished reservations remain charged at their full time allowance. Only leaf
backend commands are recorded here; generator/validation/outer wrappers are not.
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

    def reserve(self, stage, timeout_s, threads, purpose, command, output):
        if stage not in [None, *STAGE_LIMITS]:
            raise ValueError('unknown physical stage')
        if not math.isfinite(timeout_s) or timeout_s <= 0 or threads < 1:
            raise ValueError('invalid resource reservation')
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


def plan_cost(family_targets, case_targets, *, historical, prototype_reserve,
              repeat_reserve, retry_reserve, targets_frozen):
    """Conservative cold-cache count; an absent case-target list is NOT free.

    Every family/case pair is budgeted until the exact required feature set is
    frozen. The future planner can supply fewer families only with an explicit
    coverage manifest; scalar PPA similarity never earns a cache credit.
    """
    if not family_targets:
        raise ValueError('nonempty family mapping required')
    for targets in family_targets.values():
        if not targets or any(not math.isfinite(t) or t <= 0 for t in targets):
            raise ValueError('invalid characterization targets')
    base = sum(len(set(targets)) for targets in family_targets.values())
    if case_targets is None:
        supplemental = 9*len(family_targets)  # declared nine-case upper scenario
    else:
        if len(case_targets) != 9 or any(not math.isfinite(t) or t <= 0 for t in case_targets):
            raise ValueError('all nine case targets required')
        supplemental = sum(len(set(case_targets)-set(targets)) for targets in family_targets.values())
    # The current fresh-directory runner repeats synth/grt for each detail
    # recheck. Do not assume a future checkpoint-continuation implementation.
    extra = 16+prototype_reserve+repeat_reserve+retry_reserve
    if any(not isinstance(value, int) or value < 0 for value in [prototype_reserve,repeat_reserve,retry_reserve]):
        raise ValueError('nonnegative integer reserves required')
    requested = {'synth':historical['synth']+base+supplemental+36+9*4+extra,
                 'grt':historical['grt']+base+supplemental+36+9*2+extra,
                 'final':historical['final']+16+repeat_reserve+retry_reserve}
    return {'base_characterization':base, 'supplemental_characterization':supplemental,
            'supplemental_scope':'nineteen_by_nine_upper_scenario' if case_targets is None else 'exact_targets_all_declared_families',
            'targets_frozen':targets_frozen and case_targets is not None,
            'requested_calls':requested, 'unfunded_cache_credit':0}


def planning_status(plan, resources):
    shortfall = {stage:max(0,plan['requested_calls'][stage]-resources[key]) for stage,key in STAGE_LIMITS.items()}
    return {'status':'ready' if not any(shortfall.values()) else 'blocked',
            'call_shortfall':shortfall, 'targets_frozen':plan['targets_frozen'],
            'time_capacity_requires_large_kernel_trials':True}


def required_data_plan(families, case_targets, *, historical, reserves,
                       actual_collection_manifest_frozen=False):
    """Reference plus exact-query coverage, with probes in the prototype pool.

    The unknown-target upper scenario stays conservative until a real list of
    required feature/context/stage pairs is frozen. It confers no coverage.
    """
    plan = plan_cost({family:[1500] for family in families},case_targets,
                     historical=historical,targets_frozen=case_targets is not None,**reserves)
    plan.update(collection_protocol='target-conditioned-characterization-v3',
                universal_six_point_requirement=False,
                representative_probes='included_in_prototype_reserve_not_an_extra_grid',
                actual_collection_manifest_frozen=actual_collection_manifest_frozen)
    return plan


def main():
    import argparse
    from .reference import case_manifest
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check-plan', action='store_true', help='require a ready revised stage admission package')
    args = parser.parse_args()
    history = Ledger().summary()
    from .contracts import check_partition
    scope = check_partition(case_manifest())
    print(json.dumps({'usage':history,'scope':scope,
        'status':'pending_revised_platform_stage_admission',
        'effective_policy':str(POLICY.relative_to(ROOT)),
        'resource_caps_unchanged':True,
        'reason':'actual platform/stage list, capacity and funding must be validated in steps3_5_7; the old nine-case forecast is retired',
        'cold_main_matrix_only':{'synth':688,'grt':688,'includes_training_or_rechecks':False}},indent=2))
    return 1 if args.check_plan else 0


if __name__ == '__main__':
    raise SystemExit(main())
