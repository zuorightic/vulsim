"""Fresh, finite step6--8 physical batches; exact targets are batch inputs.

Reuse the established ASAP7 recipe, scalar SDC checks, full RR/IR/RO readout,
shared append-only ledger and process cleanup. Never resume the stopped queue.
Calibration implementations are frozen independently from final selections.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import os
from pathlib import Path
import shutil
from types import SimpleNamespace
from unittest.mock import patch

from .sampling_time_contract import ROOT
from .workload_abcd import read,write,sha
from .budget import Ledger,POLICY
from .platforms import profile
from . import workload_backend as predecessor
from .workload_capacity import clock

VERSION='equivalent-period-nine-case-physical-v1'


def verify_freeze(root):
    doc=read(root/'freeze.json')
    if doc['application_PPA_for_selection'] or doc['version']!=VERSION:
        raise ValueError('invalid premeasurement freeze')
    for name,identity in doc['files'].items():
        if sha(name)!=identity:raise ValueError('frozen input changed: '+name)
    return doc


def admit(root,tasks,role):
    root=Path(root).resolve();root.mkdir(parents=True,exist_ok=False)
    if role not in ('clock_calibration','final_evaluation'):raise ValueError('undeclared data role')
    identities=set();files={};rows=[]
    for task in tasks:
        task=dict(task);rtl=Path(task['rtl']).resolve()
        if task['id'] in identities:raise ValueError('duplicate task ID')
        identities.add(task['id']);task['rtl']=str(rtl);task['rtl_sha256']=sha(rtl)
        if task.get('simulation_status')!='passed':raise ValueError('functional pass required before backend')
        if not 0<task['period_ps']<1000000:raise ValueError('finite positive clock required')
        task.update(abc_target_ps=task['period_ps'],threads=4,memory_limit_MiB=8192,
                    synth_timeout_s=3600 if task.get('large') else 300,
                    grt_timeout_s=7200 if task.get('large') else 1200,support_timeout_s=300)
        files[str(rtl)]=sha(rtl)
        receipt=Path(task['simulation_receipt']);files[str(receipt)]=sha(receipt)
        rows.append(task)
    if not rows or len(rows)>100:raise ValueError('finite physical batch required')
    source_paths=predecessor.measurement_sources()+[Path(__file__),ROOT/'experiments/arithmetic_dse/workload_capacity.py']
    sources={str(p.relative_to(ROOT)):sha(p) for p in source_paths}
    for name,h in sources.items():
        p=root/'measurement-source'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/name,p)
    write(root/'freeze.json',dict(version=VERSION,files=files,application_PPA_for_selection=False,
        role=role,selection_frozen_before_measurement=True,tasks=rows))
    limits=read(POLICY)['resources'];u=Ledger().summary()
    wall=sum(t['synth_timeout_s']+t['grt_timeout_s']+4*t['support_timeout_s']+60 for t in rows)
    if (u['pending'] or u['synth']+len(rows)>limits['max_synthesis_calls'] or
        u['grt']+len(rows)>limits['max_global_route_calls'] or
        u['walltime_s']+wall>limits['max_global_walltime_h']*3600 or
        u['CPU_time_s']+4*wall>limits['max_tool_CPU_time_h']*3600):raise ValueError('finite batch envelope unfunded')
    if shutil.disk_usage(root).free<max(8*1024**3,len(rows)*256*1024**2):raise ValueError('insufficient retained-evidence storage')
    a=dict(version=VERSION,id=root.name,purpose=predecessor.PURPOSE,role=role,tasks=rows,
        sources=sources,policy_sha256=sha(POLICY),freeze_sha256=sha(root/'freeze.json'),
        created_at=datetime.now(timezone.utc).isoformat(),starting_usage=u,parallel_jobs=3,
        call_caps=dict(synth=len(rows),grt=len(rows),support=4*len(rows)),
        worst_case_leaf_walltime_s=wall,CPU_envelope_s=4*wall,
        automatic_retries=0,application_PPA_feedback=False,old_queue_resumed=False,
        qualification='diagnostic_only',resource_note='same 4 threads / 8 GiB; finite larger time envelopes for large designs')
    write(root/'admission.json',a);write(root/'progress.json',dict(status='admitted',completed=[],errors=[],active=[]))
    return a


def verify(root):
    a=read(root/'admission.json')
    if a['version']!=VERSION or a['policy_sha256']!=sha(POLICY) or a['freeze_sha256']!=sha(root/'freeze.json'):
        raise ValueError('physical batch identity changed')
    verify_freeze(root)
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(root/'measurement-source'/name)!=h:raise ValueError('measurement source changed: '+name)
    return a


def verify_admission(args,p,rtl,ledger):
    root=args.admission.parent;a=verify(root)
    task=next((t for t in a['tasks'] if t['id']==args.task_id),None)
    if task is None:raise ValueError('task outside frozen batch')
    if (a['id']!=args.admission_id or str(rtl)!=task['rtl'] or sha(rtl)!=task['rtl_sha256'] or
        args.period_ps!=task['period_ps'] or args.abc_target_ps!=task['period_ps'] or
        args.memory_limit_mib!=task['memory_limit_MiB'] or args.threads!=task['threads'] or
        args.synth_timeout_s!=task['synth_timeout_s'] or args.route_timeout_s!=task['grt_timeout_s'] or
        p['profile_sha256']!=profile('asap7')['profile_sha256'] or args.stage!='grt' or
        args.io_delay_max_ps is not None or args.sample_contract or args.resume_synth_from):
        raise ValueError('invocation differs from frozen physical task')
    return sha(root/'admission.json')


class FinalLedger(Ledger):
    def __init__(self,root,task):super().__init__();self.root,self.task=root,task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.root);t=self.task
        if t not in a['tasks'] or threads!=4:raise ValueError('unregistered physical leaf')
        mine=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id'] and e.get('task_id')==t['id']]
        if stage in ('synth','grt'):
            if timeout_s!=t[stage+'_timeout_s'] or any(e['stage']==stage for e in mine):
                raise ValueError('physical stage already attempted or timeout differs')
        elif stage is not None or timeout_s>t['support_timeout_s'] or sum(e['stage'] is None for e in mine)>=4:
            raise ValueError('support envelope exceeded')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)


def run_task(root,t):
    from .backend import _evaluate
    from .processes import run_command
    a=verify(root);ledger=FinalLedger(root,t);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=t['id'])
    out=root/'runs'/t['id']
    args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='grt',memory_limit_mib=t['memory_limit_MiB'],
        period_ps=t['period_ps'],period_role='frozen_case_target',abc_target_ps=t['period_ps'],io_delay_max_ps=None,
        budget_purpose=a['role'],admission_id=a['id'],task_id=t['id'],sample_contract=None,
        admission=root/'admission.json',resume_synth_from=None,orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),
        rtl=Path(t['rtl']),top='Workload',synth_timeout_s=t['synth_timeout_s'],route_timeout_s=t['grt_timeout_s'],
        selection_freeze=root/'freeze.json')
    with ledger.job(ctx):
        if _evaluate(args,ledger):raise ValueError(read(out/'manifest.json').get('failure_reason','backend failed'))
        m=read(out/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',QT_QPA_PLATFORM='offscreen')
        def execute(extra,stem,timeout,stage):
            # clock() requests 120 seconds; this is within the frozen support
            # envelope and remains in the same whole-job lease.
            reservation=ledger.reserve(stage,timeout,4,a['role'],base+extra,out/stem,context=ctx)
            rec=run_command(base+extra,out,stem,timeout,env,t['memory_limit_MiB'],cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation,rec);write(out/(stem+'.command.json'),dict(rec,budget_reservation_id=reservation['id']))
            m['commands'].append(dict(rec,budget_reservation_id=reservation['id']))
            if rec['exit_code']:raise RuntimeError('fixed-DB clock readout failed')
        try:
            clock(out,t,execute,m)
            result=read(out/'clock-readout/result.json');classes=result['classes']
            if not classes['threshold_check_-0.1']['slack_ps']<0<=classes['threshold_check_0.1']['slack_ps']:
                raise ValueError('full clock bracket failed')
        finally:
            m['evidence_sha256'].update({str(p.relative_to(out)):sha(p) for p in (out/'clock-readout').rglob('*') if p.is_file()})
            write(out/'manifest.json',m)
    return t['id']


def run(root):
    root=Path(root).resolve();a=verify(root);p=read(root/'progress.json')
    if p['active']:raise ValueError('batch already active')
    attempted=set(p['completed'])|{e['task'] for e in p['errors']}
    tasks=[t for t in a['tasks'] if t['id'] not in attempted]
    if any((root/'runs'/t['id']).exists() for t in tasks):raise ValueError('unsettled attempt cannot silently restart')
    p.update(status='running',active=[t['id'] for t in tasks]);write(root/'progress.json',p)
    # The old dispatcher recognizes the common workload shell. Replace only
    # its admission validator, for this process and the frozen batch lifetime.
    with patch.object(predecessor,'verify_admission',verify_admission):
        with ThreadPoolExecutor(max_workers=a['parallel_jobs']) as pool:
            futures={pool.submit(run_task,root,t):t for t in tasks}
            for future in as_completed(futures):
                t=futures[future]
                try:future.result();p['completed'].append(t['id']);print('PHYSICAL_PASS '+t['id'],flush=True)
                except Exception as e:p['errors'].append(dict(task=t['id'],reason=str(e)));print('PHYSICAL_FAIL '+t['id']+' '+str(e),flush=True)
                p['active'].remove(t['id']);write(root/'progress.json',p)
    p['status']='batch_settled';write(root/'progress.json',p);return p


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['admit','run']);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--tasks',type=Path);p.add_argument('--role',choices=['clock_calibration','final_evaluation'])
    args=p.parse_args();print(admit(args.root,read(args.tasks),args.role) if args.action=='admit' else run(args.root))
