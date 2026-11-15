"""One explicitly approved 16 GiB / eight-hour Montgomery continuation.

Reuse its successful synthesis and complete placement without changing the optimization
recipe. The original 8 GiB failure remains retained. This admission grants no
other workload or method a larger memory envelope.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime,timezone
import os
from pathlib import Path
import shutil
import time

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify as verify_parent
from .workload_checkpoint import checkpoints
from .workload_capacity import SUFFIX,clock
from .backend import ASSETS,stage_metrics,verify_orfs_area,BackendCommandError
from .model_fast_sdc import rtl_ports
from .sdc_storage_v5 import verify_sdc
from .platforms import profile,verify_wire_readback
from .processes import run_command
from .budget import Ledger,POLICY,BudgetExceeded

VERSION='nine-workload-explicit-long-memory-successor-v1'
TASK='montgomery256-T1500-D'


def authorization(root,source):
    path=root/'authorizations/montgomery-memory16-long-v1.json'
    if not path.is_file():raise ValueError('new explicit user confirmation is required for the eight-hour continuation')
    auth=read(path)
    if (auth.get('status')!='user_confirmed' or not auth.get('user_reply')
            or auth.get('task')!=TASK or auth.get('memory_limit_MiB')!=16384
            or auth.get('threads')!=4 or auth.get('grt_timeout_s')!=28800):
        raise ValueError('long continuation authorization scope differs')
    if auth.get('source_manifest_sha256')!=sha(source/'manifest.json'):
        raise ValueError('approved long continuation source changed')
    return path,auth


def admit(root,batch,source):
    auth_path,auth=authorization(root,source)
    _,parent=verify_parent(root);folder=root/'capacity'/batch;source=source.resolve()
    if folder.exists() or not source.is_relative_to(root):raise ValueError('fresh same-comparison memory pilot required')
    task=next(t for t in parent['tasks'] if t['id']==TASK)
    m=read(source/'manifest.json')
    failed=[c for c in m['commands'] if c['timed_out']]
    if (m['task_id']!=TASK or m['status']!='failed' or not failed
            or any(c['cleanup']['remaining_live_pids'] for c in failed)
            or sha(source/'input.sv')!=task['rtl_sha256']):
        raise ValueError('long continuation requires the exact settled Montgomery timeout')
    phase,hashes,proof=checkpoints(source,m)
    if phase!='post_placement':raise ValueError('long continuation requires the retained complete placement checkpoint')
    used=Ledger().summary();limits=read(POLICY)['resources'];wall=28800+240
    if (used['grt']+1>limits['max_global_route_calls']
            or used['walltime_s']+wall>limits['max_global_walltime_h']*3600
            or used['CPU_time_s']+4*wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('finite memory pilot envelope unfunded')
    folder.mkdir(parents=True);sources={}
    shutil.copy2(auth_path,folder/'authorization.json')
    for name in ('workload_memory_long.py','workload_capacity.py','workload_checkpoint.py'):
        path=Path(__file__).with_name(name);relative=path.relative_to(ROOT);dest=folder/'source'/relative
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);sources[str(relative)]=sha(path)
    path=ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl'
    relative=path.relative_to(ROOT);dest=folder/'source'/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(path,dest);sources[str(relative)]=sha(path)
    t=dict(task,source=str(source),source_manifest_sha256=sha(source/'manifest.json'),
           completed_phase=phase,checkpoints=hashes,successful_CTS_proof=proof)
    a=dict(version=VERSION,id=parent['id']+'-'+batch,tasks=[t],sources=sources,
           parent_admission_sha256=sha(root/'admission.json'),
           created_at=datetime.now(timezone.utc).isoformat(),
           user_authorization=auth['user_reply'],authorization_sha256=sha(folder/'authorization.json'),
           user_authorization_scope='Montgomery256 T1500 selected D only; explicit eight-hour continuation from retained placement; same RTL and recipe',
           memory_limit_MiB=16384,threads=4,grt_timeout_s=28800,support_timeout_s=120,
           call_caps=dict(synth=0,grt=1,support=2),worst_case_leaf_walltime_s=wall,CPU_envelope_s=4*wall,
           automatic_retries=0,application_PPA_feedback=False,scope='explicit single-point capacity exception; no cold-runtime claim')
    write(folder/'admission.json',a)
    write(folder/'progress.json',dict(status='admitted',completed=[],errors=[],active=[]))
    verify(root,folder);return dict(task=TASK,phase=phase,memory_limit_MiB=16384,grt_timeout_s=28800)


def verify(root,folder):
    verify_parent(root);a=read(folder/'admission.json')
    if (a['version']!=VERSION or sha(root/'admission.json')!=a['parent_admission_sha256']
            or a['memory_limit_MiB']!=16384 or a['threads']!=4 or a['grt_timeout_s']!=28800
            or len(a['tasks'])!=1 or a['tasks'][0]['id']!=TASK):
        raise ValueError('unregistered memory pilot resources or identity')
    auth_path,_=authorization(root,Path(a['tasks'][0]['source']))
    if sha(auth_path)!=a['authorization_sha256'] or sha(folder/'authorization.json')!=a['authorization_sha256']:
        raise ValueError('long continuation authorization changed')
    for n,h in a['sources'].items():
        if sha(ROOT/n)!=h or sha(folder/'source'/n)!=h:raise ValueError('memory pilot source changed')
    return a


class MemoryLedger(Ledger):
    def __init__(self,root,folder):super().__init__();self.root,self.folder=root,folder
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.root,self.folder)
        entries=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        if threads!=4 or purpose!='final_evaluation':raise ValueError('unregistered memory pilot invocation')
        if stage=='grt':
            if timeout_s!=28800 or any(e['stage']=='grt' for e in entries):raise ValueError('memory pilot grt already attempted')
        elif stage is not None or timeout_s!=120 or sum(e['stage'] is None for e in entries)>=2:
            raise ValueError('memory pilot support limit exhausted')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)


def run(root,batch):
    folder=root/'capacity'/batch;a=verify(root,folder);t=a['tasks'][0];source=Path(t['source'])
    progress=read(folder/'progress.json')
    if progress['status']!='admitted':raise ValueError('memory pilot already started')
    if sha(source/'manifest.json')!=t['source_manifest_sha256']:raise ValueError('memory pilot source manifest changed')
    old=read(source/'manifest.json')
    for path,h in old['files_sha256'].items():
        if sha(path)!=h:raise ValueError('memory pilot physical/source asset changed: '+path)
    for lib in old['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('memory pilot library changed')
    for tool in old['tools'].values():
        if sha(tool['path'])!=tool['sha256']:raise ValueError('memory pilot executable changed')
    out=folder/'runs'/TASK
    if out.exists():raise ValueError('preserve existing memory pilot attempt')
    ledger=MemoryLedger(root,folder);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=TASK)
    progress.update(status='waiting_for_slot',active=[TASK]);write(folder/'progress.json',progress)
    with ExitStack() as stack:
        while True:
            try:stack.enter_context(ledger.job(ctx));break
            except BudgetExceeded as error:
                if str(error)!='all backend job slots occupied':raise
                time.sleep(2)
        out.mkdir(parents=True)
        for n,h in t['checkpoints'].items():
            original=source/'results'/SUFFIX/n
            if sha(original)!=h:raise ValueError('memory pilot checkpoint changed')
            dest=out/'results'/SUFFIX/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,dest)
        for n in ('input.sv','liberty_cells.json'):shutil.copy2(source/n,out/n)
        shutil.copytree(source/'flow-scripts',out/'flow-scripts',symlinks=True)
        config=out/'config.mk';config.write_text((source/'config.mk').read_text().replace(str(source),str(out)))
        base=next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/grt.log'))
        base=[s.replace(str(source),str(out)) for s in base if not s.startswith('--assume-old=')]
        result,reports,logs=(out/n/SUFFIX for n in ('results','reports','logs'))
        assume=['--assume-old='+str(result/n) for n in t['checkpoints']]
        m=dict(old,status='running',commands=[],metrics=[x for x in old['metrics'] if x['stage']=='synth'],
               memory_limit_MiB=16384,admission_id=a['id'],budget_job_id=ledger.job_id,
               source_attempt=str(source),source_manifest_sha256=t['source_manifest_sha256'],
               capacity_admission_sha256=sha(folder/'admission.json'),
               checkpoint_reuse=dict(mode='complete synthesis and placement; explicit 16 GiB eight-hour successor',checkpoints=t['checkpoints']),
               started_at=datetime.now(timezone.utc).isoformat())
        for key in ('failure_reason','failure_stage','failure_code','finished_at','evidence_sha256','active_reservation'):m.pop(key,None)
        m['capacity_execution_sources']={str(p):sha(p) for p in
            [Path(__file__),config,out/'input.sv']+[p for p in (out/'flow-scripts').iterdir() if p.is_file()]}
        env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen')
        progress['status']='running';write(folder/'progress.json',progress)
        def execute(args,stem,timeout,stage):
            verify(root,folder);m['active_stage']=stage or stem;write(out/'manifest.json',m)
            command=base+(assume if stage=='grt' else [])+args
            reservation=ledger.reserve(stage,timeout,4,'final_evaluation',command,out/stem,context=ctx)
            rec=run_command(command,out,stem,timeout,env,16384,cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation,rec);rec['budget_reservation_id']=reservation['id'];m['commands'].append(rec)
            write(out/'manifest.json',m)
            if rec['exit_code']:
                code='timeout' if rec['timed_out'] else 'memory_limit' if rec['memory_limit_exceeded'] else 'command_failed'
                raise BackendCommandError(stem,code)
        try:
            execute(['grt'],'grt',28800,'grt')
            p=profile('asap7');ports=rtl_ports((out/'input.sv').read_text(),'Workload')
            m['sdc_contracts']['grt']=verify_sdc((result/'5_1_grt.sdc').read_text(),p,t['period_ps'],ports,serialization_stage='grt')
            execute(['run',f'RUN_SCRIPT={ASSETS}/snapshot.tcl','RUN_LOG_NAME_STEM=vulsim_grt',
                     'VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],
                    'grt-snapshot',120,None)
            metric=stage_metrics(reports,'grt',read(out/'liberty_cells.json')['cells'],t['period_ps'],selected=p)
            metric['wire_RC_readback']=verify_wire_readback(reports/'vulsim_grt_layer_rc.tsv',p)
            native=read(logs/'5_1_grt.json')['globalroute__design__instance__area__stdcell']
            metric['orfs_area_crosscheck']=verify_orfs_area(metric['cell_area_um2'],native);m['metrics'].append(metric)
            if not metric['timing_coverage_complete']:raise ValueError('incomplete memory-pilot timing coverage')
            clock(out,t,execute,m);m['status']='completed';progress['completed'].append(TASK)
        except Exception as error:
            m.update(status='failed',failure_reason=str(error),failure_stage=m.get('active_stage'),
                     failure_code=error.code if isinstance(error,BackendCommandError) else 'evidence_rejected')
            progress['errors'].append(dict(task=TASK,reason=str(error)))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(p.relative_to(out)):sha(p) for name in ('logs','reports','results','clock-readout')
                                  for p in (out/name).rglob('*') if p.is_file()}
            write(out/'manifest.json',m);write(out/'metrics.json',m['metrics'])
            progress.update(status='batch_settled',active=[]);write(folder/'progress.json',progress)
    return progress


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True);p.add_argument('--source',type=Path)
    args=p.parse_args();root=args.root.resolve()
    print(admit(root,args.batch,args.source) if args.action=='admit' else run(root,args.batch))
