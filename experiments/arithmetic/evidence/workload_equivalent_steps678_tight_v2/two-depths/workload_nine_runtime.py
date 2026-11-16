"""Explicit 9-job / 2-thread successor, with the same cumulative ledger.

Frozen v11 sources/admissions are retained. An explicitly authorized bridge
allows their named active leaves to finish while new v12 leaves share the same
nine slots. The ledger's v11 identity stays valid until all leaves settle; a
full checkpoint and Ledger.migrate then record the final policy transition.
"""
import argparse
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
import gzip
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
from unittest.mock import patch

from .sampling_time_contract import ROOT, canonical
from .workload_abcd import read, write, sha
from . import budget
from .budget import Ledger
from .workload_backend import measurement_sources, PURPOSE
from .workload_capacity import clock
from .platforms import profile

SOURCE = Path(__file__).resolve()
POLICY = ROOT/'experiments/arithmetic_dse/configs/backend_policy_v12.json'
CHECKPOINT = ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/nine-worker-checkpoint.json.gz'
BRIDGE = CHECKPOINT.with_name('nine-worker-active-bridge.json')
DEFAULT = ROOT.parent/'vulsim-artifacts/workload-equivalent-two-depths-v1'
VERSION = 'workload-nine-jobs-two-threads-v1'


def prepare_policy():
    value = deepcopy(read(budget.POLICY))
    value.update(version='arithmetic-backend-policy-v12',
        revision_reason='User requests nine parallel physical jobs, two threads each; cumulative usage retained.',
        supersedes='arithmetic-backend-policy-v11')
    value['resources'].update(parallel_jobs=9,threads_per_tool=2)
    value['budget_authorization']['resources_unchanged'] = 'superseded by explicit 2026-11-16 authorization below'
    value['concurrency_authorization'] = dict(
        user_instruction='请你把实验改成9并行，每个2线程',date='2026-11-16',
        previous_jobs=4,previous_threads=4,parallel_jobs=9,threads_per_tool=2,
        active_predecessor_leaves='finish with original limits; migration only after release',
        unchanged_usage_caps=True,default_memory_limit_MiB=8192,
        memory_successors='only named, retained 8GiB memory failures may receive a frozen 16GiB exception',
        scheduler_memory_admission='do not start another leaf with less than 8GiB MemAvailable')
    value['budget_accounting']['checkpoint_rule'] = 'v12 migration checkpoint preserves every settled historical entry; no usage reset'
    value['budget_accounting']['concurrency'] = 'kernel-locked whole-job leases, maximum nine; two threads per leaf; no automatic retry'
    if POLICY.exists() and read(POLICY)!=value:
        raise ValueError('v12 policy already exists with different contents')
    if not POLICY.exists():
        write(POLICY,value)
    return value


class NineLedger(Ledger):
    def __init__(self):
        super().__init__(path=budget.LEDGER,policy=POLICY,checkpoint=CHECKPOINT,snapshot=None)

    @contextmanager
    def _transaction(self):
        state=read(self.path)
        if state['policy_sha256']==sha(POLICY):
            with super()._transaction() as current:
                yield current
            return
        bridge=verify_bridge()
        # The predecessor must still be able to settle with its frozen v11
        # reader. Only this new caller uses v12 resource limits; both callers
        # hold the original transaction lock and the same whole-job leases.
        old=Ledger(path=self.path,policy=budget.POLICY,checkpoint=budget.CHECKPOINT)
        with old._transaction() as current:
            allowed=set(bridge['predecessor_job_ids'])
            for job in current.get('jobs',[]):
                if job['status'] in ('active','unsettled') and job['id'] not in allowed:
                    if job['admission_id'] not in bridge.get('new_admission_ids',[]) and not (
                        job['admission_id'].startswith('matrix-') or job['admission_id']=='montgomery-A-reference-9x2'):
                        raise ValueError('undeclared job during nine-worker bridge')
            yield current


def verify_bridge():
    bridge=read(BRIDGE)
    if (bridge['status']!='active_handoff_authorized' or bridge['parallel_jobs']!=9 or
        bridge['new_threads_per_tool']!=2 or bridge['new_policy_sha256']!=sha(POLICY) or
        bridge['old_policy_sha256']!=sha(budget.POLICY) or
        bridge['old_checkpoint_sha256']!=sha(budget.CHECKPOINT) or
        bridge['runtime_source_sha256']!=sha(SOURCE)):
        raise ValueError('nine-worker bridge identity changed')
    return bridge


def activate_bridge(root=DEFAULT):
    prepare_policy(); root=Path(root)
    if BRIDGE.exists():
        return verify_bridge()
    state=read(budget.LEDGER)
    active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
    if (len(active)!=1 or active[0]['status']!='active' or
        active[0]['admission_id']!='final-karatsuba256' or
        state['policy_sha256']!=sha(budget.POLICY)):
        raise ValueError('active bridge is limited to the one named old Karatsuba leaf')
    bridge=dict(status='active_handoff_authorized',parallel_jobs=9,new_threads_per_tool=2,
        user_instruction='可否不等待最后一个旧 Karatsuba 任务结束，开始9并行实验呢',
        authorized_at=datetime.now(timezone.utc).isoformat(),
        predecessor_job_ids=[j['id'] for j in active],predecessor_jobs=active,
        old_policy_sha256=sha(budget.POLICY),old_checkpoint_sha256=sha(budget.CHECKPOINT),
        new_policy_sha256=sha(POLICY),runtime_source_sha256=sha(SOURCE),
        ledger=str(budget.LEDGER),root=str(root),usage_reset=False,
        rule='same locked ledger and job leases; old leaf occupies one of nine slots; new leaves use v12 limits',
        final_migration='only after all old and new leaves settle; retain complete history')
    write(BRIDGE,bridge); write(root/'resource-bridge.json',bridge)
    return verify_bridge()


def active_predecessors():
    if not BRIDGE.exists():
        return 0
    allowed=set(verify_bridge()['predecessor_job_ids'])
    return sum(j['id'] in allowed and j['status'] in ('active','unsettled')
        for j in read(budget.LEDGER).get('jobs',[]))


def old_jobs_settled():
    state = read(budget.LEDGER)
    return not budget.usage(state['entries'])['pending'] and not any(
        j['status'] in ('active','unsettled') for j in state.get('jobs',[]))


def migrate(root=DEFAULT):
    prepare_policy(); root=Path(root); root.mkdir(parents=True,exist_ok=True)
    state=read(budget.LEDGER)
    if state['policy_sha256']==sha(POLICY):
        NineLedger().summary()
        return read(root/'resource-migration.json')
    if not old_jobs_settled():
        raise ValueError('old physical leaves must settle before v12 migration')
    if state['policy_sha256']!=sha(budget.POLICY):
        raise ValueError('unexpected previous ledger policy')
    CHECKPOINT.parent.mkdir(parents=True,exist_ok=True)
    checkpoint=dict(version='physical-budget-v12-migration-checkpoint',entries=state['entries'],
        previous_policy_sha256=state['policy_sha256'],previous_checkpoint_sha256=state['checkpoint_sha256'])
    data=gzip.compress(canonical(checkpoint),mtime=0)
    if CHECKPOINT.exists() and CHECKPOINT.read_bytes()!=data:
        raise ValueError('migration checkpoint already frozen')
    CHECKPOINT.write_bytes(data)
    before_ids=[e['id'] for e in state['entries']]
    audit=NineLedger().migrate(budget.POLICY,budget.CHECKPOINT,
        'User-authorized 9 physical jobs x 2 threads; drain old leaves; preserve complete usage and claims')
    after=read(budget.LEDGER)
    if before_ids!=[e['id'] for e in after['entries']] or after.get('jobs')!=state.get('jobs'):
        raise ValueError('migration changed historical entries or task claims')
    receipt=dict(version=VERSION,status='migrated',audit=audit,parallel_jobs=9,threads_per_tool=2,
        checkpoint=str(CHECKPOINT),checkpoint_sha256=sha(CHECKPOINT),policy_sha256=sha(POLICY),
        historical_entries=len(before_ids),historical_claims=len(after.get('jobs',[])),
        all_entries_and_claims_preserved=True,old_frozen_sources_modified=False,
        ledger=str(budget.LEDGER),usage=NineLedger().summary(),source_sha256=sha(SOURCE))
    write(root/'resource-migration.json',receipt)
    return receipt


def admit(batch,tasks,role='final_evaluation',extra_inputs=()):
    batch=Path(batch).resolve()
    if batch.exists():
        return verify(batch)
    if role not in ('final_evaluation','clock_calibration') or not 1<=len(tasks)<=100:
        raise ValueError('finite named workload batch required')
    policy=read(POLICY)['resources']; used=NineLedger().summary(); rows=[]; files={}
    for original in tasks:
        task=dict(original); rtl=Path(task['rtl']).resolve(); receipt=Path(task['simulation_receipt']).resolve()
        if task.get('simulation_status')!='passed' or not 0<task['period_ps']<1000000:
            raise ValueError('valid functional receipt and finite clock required')
        task.update(rtl=str(rtl),rtl_sha256=sha(rtl),threads=2,abc_target_ps=task['period_ps'],
            memory_limit_MiB=task.get('capacity_memory_MiB',8192),
            synth_timeout_s=3600 if task.get('large') else 300,
            grt_timeout_s=7200 if task.get('large') else 1200,support_timeout_s=300)
        if task['memory_limit_MiB']!=8192:
            prior=Path(task['memory_failure_manifest']); failed=read(prior)
            if task['memory_limit_MiB']!=16384 or failed.get('status')!='failed' or 'memory_limit' not in failed.get('failure_reason',''):
                raise ValueError('16GiB exception requires a retained memory failure')
            files[str(prior)]=sha(prior)
        files.update({str(rtl):sha(rtl),str(receipt):sha(receipt)})
        for name in ('complete_selection_freeze','source_selection_file'):
            if task.get(name):
                p=Path(task[name]); files[str(p)]=sha(p)
        if task['case']=='montgomery256':
            from .workload_tight_continue import PROXY,PROVER
            task['verification_override']=dict(proxy=str(PROXY),proxy_sha256=sha(PROXY),
                prover=str(PROVER),prover_sha256=sha(PROVER),sufficient_condition_only=True)
            files.update({str(p):sha(p) for p in (PROXY,PROVER)})
        rows.append(task)
    if len({t['id'] for t in rows})!=len(rows):
        raise ValueError('duplicate task identity')
    for p in extra_inputs:
        p=Path(p).resolve(); files[str(p)]=sha(p)
    sources=measurement_sources()+[SOURCE,ROOT/'experiments/arithmetic_dse/workload_capacity.py',POLICY]
    files.update({str(p):sha(p) for p in sources})
    wall=sum(t['synth_timeout_s']+t['grt_timeout_s']+4*t['support_timeout_s']+60 for t in rows)
    if (used['synth']+len(rows)>policy['max_synthesis_calls'] or used['grt']+len(rows)>policy['max_global_route_calls'] or
        used['walltime_s']+wall>policy['max_global_walltime_h']*3600 or
        used['CPU_time_s']+2*wall>policy['max_tool_CPU_time_h']*3600):
        raise ValueError('finite nine-worker batch envelope unfunded')
    if shutil.disk_usage(batch.parent).free<8*1024**3:
        raise ValueError('insufficient retained-evidence storage')
    batch.mkdir(parents=True)
    for p in sources:
        dest=batch/'measurement-source'/p.relative_to(ROOT); dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(p,dest)
    write(batch/'freeze.json',dict(version=VERSION,files=files,application_PPA_for_selection=False,
        selection_frozen_before_measurement=True,role=role,tasks=rows))
    admission=dict(version=VERSION,id=batch.name,purpose=PURPOSE,role=role,tasks=rows,
        policy_sha256=sha(POLICY),freeze_sha256=sha(batch/'freeze.json'),
        source_sha256=sha(SOURCE),parallel_jobs=9,threads_per_tool=2,automatic_retries=0,
        call_caps=dict(synth=len(rows),grt=len(rows),support=4*len(rows)),
        worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,starting_usage=used,
        created_at=datetime.now(timezone.utc).isoformat(),old_admissions_modified=False,
        qualification='diagnostic_only')
    write(batch/'admission.json',admission)
    write(batch/'progress.json',dict(status='admitted',completed=[],errors=[],active=[]))
    return verify(batch)


def verify(batch):
    batch=Path(batch); a=read(batch/'admission.json'); f=read(batch/'freeze.json')
    if a['version']!=VERSION or a['policy_sha256']!=sha(POLICY) or a['freeze_sha256']!=sha(batch/'freeze.json'):
        raise ValueError('nine-worker admission changed')
    if a['tasks']!=f['tasks'] or a['source_sha256']!=sha(SOURCE):
        raise ValueError('nine-worker task or runtime changed')
    for name,h in f['files'].items():
        if sha(name)!=h:
            raise ValueError('frozen nine-worker input changed: '+name)
    return a


def verify_admission(args,p,rtl,ledger):
    a=verify(args.admission.parent); task=next(t for t in a['tasks'] if t['id']==args.task_id)
    if (a['id']!=args.admission_id or str(rtl)!=task['rtl'] or sha(rtl)!=task['rtl_sha256'] or
        args.period_ps!=task['period_ps'] or args.abc_target_ps!=task['period_ps'] or
        args.threads!=2 or args.memory_limit_mib!=task['memory_limit_MiB'] or args.stage!='grt' or
        args.synth_timeout_s!=task['synth_timeout_s'] or args.route_timeout_s!=task['grt_timeout_s'] or
        p['profile_sha256']!=profile('asap7')['profile_sha256'] or args.io_delay_max_ps is not None or
        args.resume_synth_from or args.sample_contract):
        raise ValueError('invocation differs from frozen two-thread task')
    return sha(args.admission)


class TaskLedger(NineLedger):
    def __init__(self,batch,task):
        super().__init__(); self.batch,self.task=batch,task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.batch); t=self.task
        if t not in a['tasks'] or threads!=2 or purpose!=a['role']:
            raise ValueError('unregistered two-thread leaf')
        previous=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id'] and e.get('task_id')==t['id']]
        if stage in ('synth','grt'):
            if timeout_s!=t[stage+'_timeout_s'] or any(e['stage']==stage for e in previous):
                raise ValueError('physical stage already attempted or timeout changed')
        elif stage is not None or timeout_s>t['support_timeout_s'] or sum(e['stage'] is None for e in previous)>=4:
            raise ValueError('support allowance exceeded')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)


def _run_task(batch,task_id):
    from . import backend,platform_probe
    from .processes import run_command
    batch=Path(batch).resolve(); a=verify(batch); t=next(t for t in a['tasks'] if t['id']==task_id)
    ledger=TaskLedger(batch,t); ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=t['id']); out=batch/'runs'/t['id']
    args=SimpleNamespace(out=out,platform='asap7',threads=2,stage='grt',memory_limit_mib=t['memory_limit_MiB'],
        period_ps=t['period_ps'],period_role='frozen_case_target',abc_target_ps=t['period_ps'],io_delay_max_ps=None,
        budget_purpose=a['role'],admission_id=a['id'],task_id=t['id'],sample_contract=None,
        admission=batch/'admission.json',resume_synth_from=None,orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),
        rtl=Path(t['rtl']),top='Workload',synth_timeout_s=t['synth_timeout_s'],route_timeout_s=t['grt_timeout_s'],
        selection_freeze=batch/'freeze.json')
    override=t.get('verification_override')
    if override:
        os.environ['KEPLER_FORMAL_EXE']=override['proxy']
    elif os.environ.get('KEPLER_FORMAL_EXE'):
        raise ValueError('undeclared verification override')
    with ledger.job(ctx),patch.object(backend,'POLICY',POLICY),patch.object(platform_probe,'verify_admission',verify_admission):
        if backend._evaluate(args,ledger):
            raise RuntimeError(read(out/'manifest.json').get('failure_reason','backend failed'))
        m=read(out/'manifest.json'); base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        env=dict(os.environ,OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',YOSYS_MAX_THREADS='2',QT_QPA_PLATFORM='offscreen')
        def execute(extra,stem,timeout,stage):
            reservation=ledger.reserve(stage,timeout,2,a['role'],base+extra,out/stem,context=ctx)
            result=run_command(base+extra,out,stem,timeout,env,t['memory_limit_MiB'],cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation,result); write(out/(stem+'.command.json'),dict(result,budget_reservation_id=reservation['id']))
            m['commands'].append(dict(result,budget_reservation_id=reservation['id']))
            if result['exit_code']:
                raise RuntimeError('fixed-DB readout failed')
        try:
            clock(out,t,execute,m)
            classes=read(out/'clock-readout/result.json')['classes']
            if not classes['threshold_check_-0.1']['slack_ps']<0<=classes['threshold_check_0.1']['slack_ps']:
                raise ValueError('full setup threshold bracket failed')
            if override:
                proofs=list((out/'logs').rglob('4_rsz_lec_check.proof.json'))
                if len(proofs)!=1:
                    raise ValueError('actual CTS proof receipt missing')
                proof=read(proofs[0])
                if proof['status']!='proven' or proof['verifier_sha256']!=override['proxy_sha256'] or proof['prover_sha256']!=override['prover_sha256']:
                    raise ValueError('consumed CTS proof differs')
                write(out/'verification-receipt.json',dict(status='proven',proof=str(proofs[0]),proof_sha256=sha(proofs[0]),
                    actual_ORFS_consumption_checked=True,netlists_modified=False))
        finally:
            m['evidence_sha256'].update({str(p.relative_to(out)):sha(p) for p in (out/'clock-readout').rglob('*') if p.is_file()})
            write(out/'manifest.json',m)
    return t['id']


def run_task(batch,task_id):
    """Publish success only after readout, proof and ledger settlement finish."""
    batch=Path(batch).resolve(); a=verify(batch)
    t=next(t for t in a['tasks'] if t['id']==task_id); out=batch/'runs'/task_id
    try:
        result=_run_task(batch,task_id)
    except Exception as error:
        if out.exists():
            write(out/'measurement-outcome.json',dict(status='failed',task_id=task_id,
                reason=str(error),source_sha256=sha(SOURCE),automatic_retries=0))
        raise
    manifest=out/'manifest.json'; clock_result=out/'clock-readout/result.json'
    state=read(budget.LEDGER)
    claims=[j for j in state.get('jobs',[]) if j['admission_id']==a['id'] and j['task_id']==task_id]
    if len(claims)!=1 or claims[0]['status']!='released':
        raise ValueError('completed measurement must have a settled job claim')
    outcome=dict(status='completed',task_id=task_id,manifest_sha256=sha(manifest),
        clock_readout_sha256=sha(clock_result),job_id=claims[0]['id'],ledger_settled=True,
        complete_setup_bracket_checked=True,threads_per_tool=2,source_sha256=sha(SOURCE))
    if t.get('verification_override'):
        outcome['verification_receipt_sha256']=sha(out/'verification-receipt.json')
    write(out/'measurement-outcome.json',outcome)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=('policy','migrate','task','status'))
    p.add_argument('--root',type=Path,default=DEFAULT); p.add_argument('--task-id'); args=p.parse_args()
    result=prepare_policy() if args.action=='policy' else migrate(args.root) if args.action=='migrate' else run_task(args.root,args.task_id) if args.action=='task' else NineLedger().summary()
    print(result)
