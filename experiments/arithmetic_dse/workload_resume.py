"""Resume a retained workload CTS timeout after complete exact-pair CEC.

Reuse the complete placement checkpoint and successful synthesis. Replay CTS
with the same optimization; accept the cached proof only for byte-identical
pre/post-repair netlists. Read the final full-interface clock independently.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime,timezone
import os
from pathlib import Path
import shutil
import sys
import time

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify as verify_parent
from .workload_cec import verify_proof
from .workload_capacity import clock,SUFFIX
from .model_m2_cec_resume import render_cts
from .backend import ASSETS,stage_metrics,verify_orfs_area,BackendCommandError
from .model_fast_sdc import rtl_ports
from .sdc_storage_v5 import verify_sdc
from .platforms import profile,verify_wire_readback
from .processes import run_command
from .budget import Ledger,POLICY,BudgetExceeded

VERSION='nine-workload-placement-CTS-proof-resume-v1'
CHECKPOINTS=('1_2_yosys.v','1_2_yosys.sdc','1_synth.odb','1_synth.sdc','3_place.odb','3_place.sdc',
             '4_before_rsz_lec.v','4_after_rsz_lec.v')


def admit(root,task_id,batch,proof):
    _,parent=verify_parent(root);task=next(t for t in parent['tasks'] if t['id']==task_id)
    folder=root/'capacity'/batch;source=root/'runs'/task_id;m=read(source/'manifest.json')
    if folder.exists() or m['status']!='failed' or m.get('failure_code')!='timeout':
        raise ValueError('fresh placement resume requires a settled retained timeout')
    result=source/'results'/SUFFIX
    verify_proof(proof,result/'4_before_rsz_lec.v',result/'4_after_rsz_lec.v')
    checkpoints={n:sha(result/n) for n in CHECKPOINTS}
    for n,h in checkpoints.items():
        if m['evidence_sha256'].get(str(Path('results')/SUFFIX/n))!=h:raise ValueError('changed placement recovery checkpoint')
    usage=Ledger().summary();limits=read(POLICY)['resources']
    if (usage['grt']+1>limits['max_global_route_calls']
            or usage['walltime_s']+3840>limits['max_global_walltime_h']*3600
            or usage['CPU_time_s']+4*3840>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('finite CTS continuation envelope unfunded')
    folder.mkdir(parents=True);sources={}
    for name in ('workload_resume.py','workload_capacity.py','workload_cec.py','model_m2_cec_resume.py'):
        p=Path(__file__).with_name(name);dest=folder/name;shutil.copy2(p,dest);sources[name]=sha(p)
    t=dict(task,source=str(source),source_manifest_sha256=sha(source/'manifest.json'),checkpoints=checkpoints,
           proof=str(proof.resolve()),proof_sha256=sha(proof))
    a=dict(version=VERSION,id=parent['id']+'-'+batch,tasks=[t],sources=sources,
           created_at=datetime.now(timezone.utc).isoformat(),parent_admission_sha256=sha(root/'admission.json'),
           grt_timeout_s=3600,threads=4,memory_limit_MiB=8192,call_caps=dict(synth=0,grt=1,support=2),
           automatic_retries=0,application_PPA_feedback=False,
           scope='reuse synthesis and placement; replay identical CTS repair with exact-pair CEC, then global route; no cold-runtime claim')
    write(folder/'admission.json',a);write(folder/'progress.json',dict(status='admitted',completed=[],errors=[],active=[]));return a


def verify(root,folder):
    verify_parent(root);a=read(folder/'admission.json')
    if a['version']!=VERSION or sha(root/'admission.json')!=a['parent_admission_sha256']:raise ValueError('resume admission changed')
    for n,h in a['sources'].items():
        if sha(Path(__file__).with_name(n))!=h or sha(folder/n)!=h:raise ValueError('resume producer changed')
    return a


class ResumeLedger(Ledger):
    def __init__(self,root,folder):super().__init__();self.root,self.folder=root,folder
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.root,self.folder);entries=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        if threads!=4 or purpose!='final_evaluation':raise ValueError('unregistered CTS continuation resources')
        if stage=='grt':
            if timeout_s!=3600 or any(e['stage']=='grt' for e in entries):raise ValueError('one CTS/grt continuation only')
        elif stage is not None or timeout_s!=120 or sum(e['stage'] is None for e in entries)>=2:
            raise ValueError('CTS continuation support limit exhausted')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)


def run(root,batch):
    folder=root/'capacity'/batch;a=verify(root,folder);t=a['tasks'][0];source=Path(t['source'])
    if sha(source/'manifest.json')!=t['source_manifest_sha256'] or sha(t['proof'])!=t['proof_sha256']:
        raise ValueError('resume source/proof changed')
    old=read(source/'manifest.json');out=folder/'runs'/t['id']
    if out.exists():raise ValueError('resume already attempted')
    for n,h in old['files_sha256'].items():
        if sha(n)!=h:raise ValueError('physical/source asset changed before continuation: '+n)
    for lib in old['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('resume library changed')
    for tool in old['tools'].values():
        if sha(tool['path'])!=tool['sha256']:raise ValueError('resume physical binary changed')
    out.mkdir(parents=True)
    for n,h in t['checkpoints'].items():
        p=source/'results'/SUFFIX/n
        if sha(p)!=h:raise ValueError('resume checkpoint changed')
        dest=out/'results'/SUFFIX/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for n in ('input.sv','liberty_cells.json'):shutil.copy2(source/n,out/n)
    shutil.copytree(source/'flow-scripts',out/'flow-scripts',symlinks=True)
    config=out/'config.mk';config.write_text((source/'config.mk').read_text().replace(str(source),str(out)))
    wrapper=out/'verify-workload-cec.py';wrapper.write_text(
        'import sys\nfrom pathlib import Path\nsys.path.insert(0,'+repr(str(ROOT))+')\n'
        'from experiments.arithmetic_dse.workload_cec import verify_proof\nverify_proof(*map(Path,sys.argv[1:]))\n')
    cts=out/'flow-scripts/cts.tcl';original=cts.read_text();cts.unlink()
    cts.write_text(render_cts(original,Path(t['proof']),wrapper,False))
    base=next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/grt.log'))
    base=[s.replace(str(source),str(out)) for s in base if not s.startswith('--assume-old=')]
    result,reports,logs=(out/n/SUFFIX for n in ('results','reports','logs'))
    assume=['--assume-old='+str(result/n) for n in CHECKPOINTS[:6]]
    m=dict(old,status='running',commands=[],metrics=[x for x in old['metrics'] if x['stage']=='synth'],
           admission_id=a['id'],capacity_admission_sha256=sha(folder/'admission.json'),source_attempt=str(source),
           source_manifest_sha256=t['source_manifest_sha256'],started_at=datetime.now(timezone.utc).isoformat(),
           checkpoint_reuse=dict(mode=a['scope'],checkpoints=t['checkpoints'],proof=t['proof'],proof_sha256=t['proof_sha256']),
           continuation_sources={str(p):sha(p) for p in (Path(__file__),cts,config,wrapper)})
    for k in ('failure_reason','failure_code','failure_stage','finished_at','evidence_sha256'):m.pop(k,None)
    ledger=ResumeLedger(root,folder);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=t['id'])
    env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen')
    progress=dict(status='running',completed=[],errors=[],active=[t['id']]);write(folder/'progress.json',progress)
    def execute(args,stem,timeout,stage):
        verify(root,folder);m['active_stage']=stage or stem;write(out/'manifest.json',m)
        command=base+(assume if stage=='grt' else [])+args
        reservation=ledger.reserve(stage,timeout,4,'final_evaluation',command,out/stem,context=ctx)
        rec=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,rec);rec['budget_reservation_id']=reservation['id'];m['commands'].append(rec)
        write(out/'manifest.json',m)
        if rec['exit_code']:raise BackendCommandError(stem,'timeout' if rec['timed_out'] else 'command_failed')
    with ExitStack() as stack:
        deadline=time.monotonic()+1800
        while True:
            try:stack.enter_context(ledger.job(ctx));break
            except BudgetExceeded as error:
                if str(error)!='all backend job slots occupied' or time.monotonic()>=deadline:raise
                time.sleep(2)
        try:
            m['budget_job_id']=ledger.job_id
            execute(['grt'],'grt',3600,'grt')
            p=profile('asap7');ports=rtl_ports((out/'input.sv').read_text(),'Workload')
            m['sdc_contracts']['grt']=verify_sdc((result/'5_1_grt.sdc').read_text(),p,t['period_ps'],ports,serialization_stage='grt')
            execute(['run',f'RUN_SCRIPT={ASSETS}/snapshot.tcl','RUN_LOG_NAME_STEM=vulsim_grt',
                     'VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],
                    'grt-snapshot',120,None)
            metric=stage_metrics(reports,'grt',read(out/'liberty_cells.json')['cells'],t['period_ps'],selected=p)
            metric['wire_RC_readback']=verify_wire_readback(reports/'vulsim_grt_layer_rc.tsv',p)
            native=read(logs/'5_1_grt.json')['globalroute__design__instance__area__stdcell']
            metric['orfs_area_crosscheck']=verify_orfs_area(metric['cell_area_um2'],native);m['metrics'].append(metric)
            if not metric['timing_coverage_complete']:raise ValueError('incomplete resumed timing coverage')
            clock(out,t,execute,m);m['status']='completed';progress['completed'].append(t['id'])
        except Exception as e:
            m.update(status='failed',failure_reason=str(e),failure_stage=m.get('active_stage'),
                     failure_code=e.code if isinstance(e,BackendCommandError) else 'evidence_rejected')
            progress['errors'].append(dict(task=t['id'],reason=str(e)))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(f.relative_to(out)):sha(f) for n in ('logs','reports','results','clock-readout')
                                  for f in (out/n).rglob('*') if f.is_file()}
            write(out/'manifest.json',m);write(out/'metrics.json',m['metrics'])
            progress.update(status='batch_settled',active=[]);write(folder/'progress.json',progress)
    return progress


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True)
    p.add_argument('--task');p.add_argument('--proof',type=Path);a=p.parse_args();root=a.root.resolve()
    print(admit(root,a.task,a.batch,a.proof) if a.action=='admit' else run(root,a.batch))
