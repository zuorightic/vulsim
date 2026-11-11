"""Bounded outer monitor: seal/replay artifacts after the v2 worker settles."""
import argparse
from pathlib import Path
import time

from .model_fast_preflight import read,write,sha
from .operator_stage4 import atomic,support
from .budget import Ledger,usage

ROOT=Path(__file__).resolve().parents[2]


def close_resources(root,work,evidence):
    receipts=list(work.rglob('commands.json'))
    ids={r['budget_reservation_id'] for path in receipts for r in read(path)}
    prefixes=[]
    for path in (root/'batches').glob('batch-*/admission.json'):
        if int(path.parent.name.split('-')[-1])<2:continue
        for r in read(path)['source_target_requests']:prefixes.append(str(root/'raw'/r['source_id']/('target-'+str(r['SDC_ps'])))+'/')
        prefixes.append(str(root/'support'/('archive-'+path.parent.name))+'/')
    entries=[e for e in read(Ledger().path)['entries'] if e['id'] in ids or any(str(e.get('output','')).startswith(p) for p in prefixes)]
    result=dict(version='operator-v2-work-resource-closure-v1',scope='v2 support receipt IDs and exact batches002 onward; prior six pilot points retain old fees',
        entries=entries,usage=usage(entries),receipt_sha256={str(p):sha(p) for p in receipts},
        ledger_not_reset=True,old_failures_retained=True,full_D_ready=False)
    if result['usage']['pending']:raise ValueError('scoped work not yet settled')
    write(root/'v2-work-resource-closure.json',result)
    if evidence.exists():
        write(evidence/'publication-closure.json',dict(version=result['version'],scope=result['scope'],usage=result['usage'],
            entries_columns=['id','stage','status','walltime_s','CPU_time_s'],
            entries=[[e['id'],e.get('stage'),e['status'],e['walltime_s'],e['CPU_time_s']] for e in entries],
            receipt_sha256=result['receipt_sha256'],full_resource_record=str(root/'v2-work-resource-closure.json'),
            full_resource_record_sha256=sha(root/'v2-work-resource-closure.json'),
            evidence_manifest_sha256=sha(evidence/'manifest.json'),ledger_not_reset=True,old_failures_retained=True,full_D_ready=False))
        if sum(p.stat().st_size for p in evidence.iterdir())>5*1024**2 or any(p.stat().st_size>1024**2 for p in evidence.iterdir()):
            raise ValueError('final evidence including resource closure exceeds compact envelope; preserve provisional package')


def finish(root,work,out,max_wait):
    status=root/'v2-evidence-status.json';started=time.monotonic()
    atomic(status,dict(phase='waiting_for_frozen_work_package',max_wait_s=max_wait,full_D_ready=False))
    terminals={'isolated_functions_passed','failed_independent','validation_failed_test_locked','stopped_preserve_failure',
        'bounded_fitting_still_pending','bounded_independent_still_pending'}
    while time.monotonic()-started<max_wait:
        state=read(root/'v2-work-status.json')
        if state['phase'] in terminals:break
        time.sleep(15)
    else:
        atomic(status,dict(phase='monitor_timeout_preserve_worker',worker=state,full_D_ready=False));return
    if state['phase'] not in {'isolated_functions_passed','failed_independent','validation_failed_test_locked'}:
        close_resources(root,work,Path('/nonexistent-v2-evidence'))
        atomic(status,dict(phase='worker_stopped_without_final_function',worker=state,full_D_ready=False));return
    try:
        atomic(status,dict(phase='sealing_local_evidence',worker_phase=state['phase'],full_D_ready=False))
        support(work,'v2-evidence-pack',[str(__import__('sys').executable),'-B','-m','experiments.arithmetic_dse.operator_condition_evidence_v2',
            '--root',str(root),'--work',str(work),'--out',str(out)],600)
        support(work,'v2-evidence-replay',[str(__import__('sys').executable),'-I','-B',str(out/'replay.py'),'--evidence',str(out)],300)
        close_resources(root,work,out)
        atomic(status,dict(phase='evidence_replay_and_resource_closure_passed',worker_phase=state['phase'],evidence=str(out),
            isolated_functions_qualified=state['phase']=='isolated_functions_passed',S_G_joint_qualified=False,full_D_ready=False))
    except Exception as error:
        atomic(status,dict(phase='preserve_publication_failure',worker_phase=state['phase'],error=str(error),full_D_ready=False));raise


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('root','work','out'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--max-wait',type=int,default=14400);a=p.parse_args()
    if not 60<=a.max_wait<=14400:raise ValueError('bounded outer monitor required')
    finish(a.root.resolve(),a.work.resolve(),a.out.resolve(),a.max_wait)
