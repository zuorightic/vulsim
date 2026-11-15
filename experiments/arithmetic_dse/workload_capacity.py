"""Explicit finite capacity successors for settled workload tool timeouts.

Only the leaf resource envelope changes. The frozen RTL, constraints, mapping
scripts, tools and profile remain identical. A successful synthesis checkpoint
is reused in a fresh directory; a synthesis timeout restarts synthesis once.
No optimization result is returned to the model or selector.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timezone
import os
from pathlib import Path
import shutil

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify as verify_parent
from .budget import Ledger,POLICY
from .processes import run_command
from .platforms import profile,verify_wire_readback
from .backend import ASSETS,stage_metrics,verify_orfs_area,BackendCommandError
from .model_fast_sdc import rtl_ports
from .sdc_storage_v5 import verify_sdc

VERSION='nine-workload-explicit-capacity-successor-v1'
SUFFIX=Path('asap7/arithmetic_probe/base')
CHECKPOINTS=('1_2_yosys.v','1_2_yosys.sdc','1_synth.odb','1_synth.sdc')


def admit(root,batch,ids,synth_timeout,grt_timeout):
    _,parent=verify_parent(root);folder=root/'capacity'/batch
    if folder.exists():raise ValueError('preserve existing capacity admission')
    if not ids or not (300<=synth_timeout<=3600 and 1200<=grt_timeout<=7200):
        raise ValueError('finite named capacity task and bounded resource envelope required')
    tasks=[]
    for task_id in ids:
        t=next(t for t in parent['tasks'] if t['id']==task_id)
        source=root/'runs'/task_id;m=read(source/'manifest.json')
        failed=[c for c in m['commands'] if c.get('timed_out') or c.get('memory_limit_exceeded')]
        if (m['status']!='failed' or not failed or any(c['cleanup']['remaining_live_pids'] for c in failed)):
            raise ValueError('capacity successor requires a settled retained timeout/memory failure')
        reuse=any(x['stage']=='synth' for x in m['metrics'])
        checkpoints={n:sha(source/'results'/SUFFIX/n) for n in CHECKPOINTS} if reuse else {}
        for n,h in checkpoints.items():
            if m['evidence_sha256'].get(str(Path('results')/SUFFIX/n))!=h:
                raise ValueError('changed synthesis checkpoint')
        tasks.append(dict(t,source=str(source),source_manifest_sha256=sha(source/'manifest.json'),
                          reuse_synth=reuse,checkpoints=checkpoints))
    limits=read(POLICY)['resources'];u=Ledger().summary()
    wall=sum((0 if t['reuse_synth'] else synth_timeout)+grt_timeout+3*120 for t in tasks)
    if (u['synth']+sum(not t['reuse_synth'] for t in tasks)>limits['max_synthesis_calls']
            or u['grt']+len(tasks)>limits['max_global_route_calls']
            or u['walltime_s']+wall>limits['max_global_walltime_h']*3600
            or u['CPU_time_s']+4*wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('finite capacity envelope unfunded')
    folder.mkdir(parents=True)
    source_files=[Path(__file__),ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl']
    hashes={}
    for p in source_files:
        n=p.relative_to(ROOT);dest=folder/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest);hashes[str(n)]=sha(p)
    a=dict(version=VERSION,id=parent['id']+'-'+batch,tasks=tasks,
           parent_admission_sha256=sha(root/'admission.json'),sources=hashes,
           synth_timeout_s=synth_timeout,grt_timeout_s=grt_timeout,threads=4,memory_limit_MiB=8192,
           worst_case_leaf_walltime_s=wall,CPU_envelope_s=4*wall,
           created_at=datetime.now(timezone.utc).isoformat(),automatic_retries=0,
           frozen_selection_unchanged=True,application_PPA_feedback=False,
           rationale='retained resource failures only; same optimization recipe with larger time envelope')
    write(folder/'admission.json',a);write(folder/'progress.json',dict(completed=[],errors=[],active=[],status='admitted'))
    return a


def verify(root,folder):
    verify_parent(root);a=read(folder/'admission.json')
    if a['version']!=VERSION or sha(root/'admission.json')!=a['parent_admission_sha256']:
        raise ValueError('capacity admission identity changed')
    for n,h in a['sources'].items():
        if sha(ROOT/n)!=h or sha(folder/'source'/n)!=h:raise ValueError('capacity source changed: '+n)
    return a


class CapacityLedger(Ledger):
    def __init__(self,root,folder,task):super().__init__();self.root,self.folder,self.task=root,folder,task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.root,self.folder);t=self.task
        if t not in a['tasks'] or threads!=4 or purpose!='final_evaluation':raise ValueError('unregistered capacity leaf')
        entries=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id'] and e.get('task_id')==t['id']]
        if stage in ('synth','grt'):
            if (timeout_s!=a[stage+'_timeout_s'] or any(e['stage']==stage for e in entries)
                    or (stage=='synth' and t['reuse_synth'])):raise ValueError('capacity stage already attempted or not admitted')
        elif stage is not None or timeout_s!=120 or sum(e['stage'] is None for e in entries)>=3:
            raise ValueError('capacity support allowance exhausted')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)


def clock(out,t,execute,m):
    result=out/'results'/SUFFIX;folder=out/'clock-readout';folder.mkdir()
    fixed={str(result/n):sha(result/n) for n in ('5_1_grt.odb','5_1_grt.sdc')}
    if any(s in (result/'5_1_grt.sdc').read_text() for s in
           ('set_false_path','set_multicycle_path','set_max_delay','set_clock_groups','set_disable_timing')):
        raise ValueError('unsupported clock timing exception')
    p=profile('asap7');text=(ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl').read_text()
    output=folder/'period.tsv'
    for key,value in dict(PERIOD=t['period_ps'],OUTPUT=output,TRANSITION=p['clock_transition_ps'],
                          SETUP=p['setup_uncertainty_ps'],HOLD=p['hold_uncertainty_ps']).items():
        text=text.replace('@'+key+'@',str(value))
    script=folder/'period.tcl';script.write_text(text)
    execute(['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=workload_clock_limit',
             'VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'clock-readout',120,None)
    if any(sha(n)!=h for n,h in fixed.items()):raise ValueError('checkpoint changed during clock readout')
    rows={n:dict(slack_ps=float(s),required_period_ps=float(v)) for n,s,v in
          (line.split('\t') for line in output.read_text().splitlines()[1:])}
    full=rows['full_setup_threshold'];metric=m['metrics'][-1]
    if abs(full['slack_ps']-metric['setup_worst_slack_ps'])>.005:raise ValueError('full clock WNS mismatch')
    write(folder/'result.json',dict(task=t['id'],target_ps=t['period_ps'],classes=rows,fixed_inputs=fixed,
          full_setup_minimum_period_ps=full['required_period_ps'],maximum_frequency_MHz=1e6/full['required_period_ps'],
          area_um2=metric['cell_area_um2'],hold_WNS_ps=metric['hold_worst_slack_ps'],
          hold_review_required=metric['hold_review_required'],scope='fixed grt full RR/IR/RO, IOmax=0.2T; hold separate'))


def run_task(root,folder,t):
    a=verify(root,folder);source=Path(t['source']);old=read(source/'manifest.json')
    if sha(source/'manifest.json')!=t['source_manifest_sha256']:raise ValueError('retained failed manifest changed')
    for path,h in old['files_sha256'].items():
        if sha(path)!=h:raise ValueError('capacity physical/source asset changed: '+path)
    for lib in old['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('capacity Liberty changed')
    for tool in old['tools'].values():
        if sha(tool['path'])!=tool['sha256']:raise ValueError('capacity executable changed')
    out=folder/'runs'/t['id'];out.mkdir(parents=True,exist_ok=False)
    for n in ('input.sv','liberty_cells.json'):shutil.copy2(source/n,out/n)
    if sha(out/'input.sv')!=t['rtl_sha256']:raise ValueError('capacity RTL differs from selected implementation')
    shutil.copytree(source/'flow-scripts',out/'flow-scripts',symlinks=True)
    (out/'config.mk').write_text((source/'config.mk').read_text().replace(str(source),str(out)))
    command=next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/synth.log'))
    command=[s.replace(str(source),str(out)) for s in command]
    m=dict(old,status='running',commands=[],metrics=[],retry_count=0,
           started_at=datetime.now(timezone.utc).isoformat(),admission_id=a['id'],
           source_attempt=str(source),source_manifest_sha256=t['source_manifest_sha256'],
           capacity_admission_sha256=sha(folder/'admission.json'),sdc_contracts={})
    m['capacity_execution_sources']={str(p):sha(p) for p in
        [Path(__file__),out/'config.mk',out/'input.sv']+
        [p for p in (out/'flow-scripts').iterdir() if p.is_file()]}
    for k in ('failure_reason','failure_stage','failure_code','finished_at','evidence_sha256','active_reservation'):
        m.pop(k,None)
    result,reports,logs=(out/n/SUFFIX for n in ('results','reports','logs'))
    if t['reuse_synth']:
        result.mkdir(parents=True)
        for n,h in t['checkpoints'].items():
            shutil.copy2(source/'results'/SUFFIX/n,result/n)
            if sha(result/n)!=h:raise ValueError('capacity synthesis checkpoint changed')
            command.append('--assume-old='+str(result/n))
        m['metrics']=[x for x in old['metrics'] if x['stage']=='synth']
        m['checkpoint_reuse']=dict(mode='fresh full post-synthesis grt chain',checkpoints=t['checkpoints'])
    ledger=CapacityLedger(root,folder,t);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=t['id'])
    env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen')
    def execute(args,stem,timeout,stage):
        verify(root,folder);m['active_stage']=stage or stem;write(out/'manifest.json',m)
        reservation=ledger.reserve(stage,timeout,4,'final_evaluation',command+args,out/stem,context=ctx)
        rec=run_command(command+args,out,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,rec);rec['budget_reservation_id']=reservation['id'];m['commands'].append(rec)
        write(out/'manifest.json',m)
        if rec['exit_code']:
            reason='timeout' if rec['timed_out'] else 'memory_limit' if rec['memory_limit_exceeded'] else 'command_failed'
            raise BackendCommandError(stem,reason)
    with ledger.job(ctx):
        m['budget_job_id']=ledger.job_id
        try:
            p=profile('asap7');cells=read(out/'liberty_cells.json')['cells'];ports=rtl_ports((out/'input.sv').read_text(),'Workload')
            for stage,db,sdc in [('synth','1_synth.odb','1_synth.sdc'),('grt','5_1_grt.odb','5_1_grt.sdc')]:
                if stage=='synth' and t['reuse_synth']:continue
                execute([stage],stage,a[stage+'_timeout_s'],stage)
                m['sdc_contracts'][stage]=verify_sdc((result/sdc).read_text(),p,t['period_ps'],ports,serialization_stage=stage)
                execute(['run',f'RUN_SCRIPT={ASSETS}/snapshot.tcl',f'RUN_LOG_NAME_STEM=vulsim_{stage}',
                         f'VULSIM_EVAL_STAGE={stage}',f'VULSIM_EVAL_DB={db}',f'VULSIM_EVAL_SDC={sdc}'],stage+'-snapshot',120,None)
                metric=stage_metrics(reports,stage,cells,t['period_ps'],selected=p)
                metric['wire_RC_readback']=verify_wire_readback(reports/f'vulsim_{stage}_layer_rc.tsv',p)
                native=read(logs/('1_synth.json' if stage=='synth' else '5_1_grt.json'))
                key=('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell'
                metric['orfs_area_crosscheck']=verify_orfs_area(metric['cell_area_um2'],native[key])
                metric['orfs_stdcell_area_um2']=native[key];m['metrics'].append(metric)
                if not metric['timing_coverage_complete']:raise ValueError('timing_coverage_incomplete')
            clock(out,t,execute,m);m['status']='completed'
        except Exception as e:
            m.update(status='failed',failure_reason=str(e),failure_stage=m.get('active_stage'),
                     failure_code=e.code if isinstance(e,BackendCommandError) else 'evidence_rejected')
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(f.relative_to(out)):sha(f) for n in ('logs','reports','results','clock-readout')
                                  for f in (out/n).rglob('*') if f.is_file()}
            write(out/'manifest.json',m);write(out/'metrics.json',m['metrics'])
    if m['status']!='completed':raise ValueError(m['failure_reason'])
    return t['id']


def run(root,batch):
    folder=root/'capacity'/batch;a=verify(root,folder);progress=read(folder/'progress.json')
    if progress['active']:raise ValueError('capacity batch already active')
    attempted=set(progress['completed'])|{e['task'] for e in progress['errors']}
    tasks=[t for t in a['tasks'] if t['id'] not in attempted]
    if any((folder/'runs'/t['id']).exists() for t in tasks):raise ValueError('unsettled capacity attempt')
    progress.update(status='running',active=[t['id'] for t in tasks]);write(folder/'progress.json',progress)
    with ThreadPoolExecutor(max_workers=min(4,len(tasks) or 1)) as pool:
        futures={pool.submit(run_task,root,folder,t):t for t in tasks}
        for f in as_completed(futures):
            t=futures[f]
            try:f.result();progress['completed'].append(t['id'])
            except Exception as e:progress['errors'].append(dict(task=t['id'],reason=str(e)))
            progress['active'].remove(t['id']);write(folder/'progress.json',progress)
    progress['status']='batch_settled';write(folder/'progress.json',progress);return progress


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True)
    p.add_argument('--task',action='append');p.add_argument('--synth-timeout',type=int,default=1800)
    p.add_argument('--grt-timeout',type=int,default=3600);a=p.parse_args();root=a.root.resolve()
    print(admit(root,a.batch,a.task,a.synth_timeout,a.grt_timeout) if a.action=='admit' else run(root,a.batch))
