"""Continue the paid serial synth snapshot after scalar-alias qualification.

The failed v1 admission/receipts stay intact.  Exactly one new synthesis and
two global routes remain; the first synthesis is inherited, never rerun.
"""
import argparse
from pathlib import Path
import os
import shutil
from types import FunctionType,SimpleNamespace

from . import stage67_physical_probe_v1 as parent,stage67_mapped_state_v2 as mapped
from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage


def admit(root,previous):
    if root.exists():raise ValueError('preserve continuation attempt')
    a=read(previous/'admission.json');progress=read(previous/'progress.json')
    if progress['phase']!='stopped_on_error' or len(progress['errors'])!=1:raise ValueError('one audited alias stop required')
    first=previous/'runs'/a['tasks'][0]['id'];m=read(first/'manifest.json')
    if m['status']!='completed' or [x['stage'] for x in m['metrics']]!=['synth']:raise ValueError('only completed synth checkpoint may continue')
    proof=read(previous/'mapped-state-recovery.json')
    if proof['status']!='passed_variable_bit_FF_census' or not proof['expected_mask_never_used_to_fill_absent_alias']:raise ValueError('independent alias recovery missing')
    for n,h in m['evidence_sha256'].items():
        if sha(first/n)!=h:raise ValueError('paid synth checkpoint changed')
    root.mkdir(parents=True);sources=dict(a['sources'])
    for p in (Path(__file__),Path(mapped.__file__)):
        sources[str(p.relative_to(parent.ROOT))]=sha(p)
    for n,h in sources.items():
        if sha(parent.ROOT/n)!=h:raise ValueError('physical source drift')
        dest=root/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(parent.ROOT/n,dest)
    # All original source roles, clocks, RTL and baseline prices are inherited.
    b=dict(a,id=root.name+'-serial-pilot-continuation',version='stage67-two-serial-pilot-v2',sources=sources,
        synth_max=1,grt_max=2,parent_admission_sha256=sha(previous/'admission.json'),parent=str(previous),
        parent_stop_retained=True,alias_recovery_sha256=sha(previous/'mapped-state-recovery.json'),
        inherit_synth=dict(directory=str(first),manifest_sha256=sha(first/'manifest.json'),files_sha256=m['evidence_sha256']),
        no_repeat_synthesis_for=a['tasks'][0]['id'])
    write(root/'admission.json',b);write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=None))
    print('STAGE67_ALIAS_CONTINUATION_ADMITTED new_synth_max=1 new_grt_max=2 inherited_synth=1',flush=True)


class ContinuationLedger(parent.PilotLedger):
    def reserve(self,stage,*args,**kwargs):
        a=read(self.root/'admission.json')
        if stage=='synth' and self.task['id']==a['no_repeat_synthesis_for']:raise ValueError('paid synth cannot repeat')
        return super().reserve(stage,*args,**kwargs)


def inherited_point(root,task):
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .processes import run_command
    a=read(root/'admission.json');out=Path(a['inherit_synth']['directory']);m=read(out/'manifest.json')
    if sha(out/'manifest.json')!=a['inherit_synth']['manifest_sha256']:raise ValueError('inherited manifest drift')
    for n,h in a['inherit_synth']['files_sha256'].items():
        if sha(out/n)!=h:raise ValueError('inherited snapshot drift')
    result=root/'runs'/task['id'];result.mkdir(parents=True)
    write(result/'physical-directory.json',dict(path=str(out),synth_inherited=True))
    state=mapped.verify(read(out/'mapped.json'),read(out/'liberty-pins.json'),read(task['endpoint_contract']),read(Path(task['input_directory'])/'source.json'),(out/'input.sv').read_text());write(result/'mapped-state.json',state)
    ledger=ContinuationLedger(root,task);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=task['id'])
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'));commands=[]
    with ledger.job(ctx):
        def execute(command,name,timeout=120,stage=None):
            r=ledger.reserve(stage,timeout,4,'stage67_alias_continuation',command,result/name,context=ctx)
            rec=run_command(command,result,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,rec);commands.append(dict(**rec,budget_reservation_id=r['id']));write(result/'commands.json',commands)
            if rec['exit_code']:raise ValueError('continuation leaf failed '+rec['log'])
        wrapper=result/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(parent.ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
        request=result/'live-cec-request.json';write(request,dict(libraries=m['libraries'],admission_sha256=sha(root/'admission.json'),collection_plan_sha256=sha(root/'admission.json')))
        cts=out/'flow-scripts/cts.tcl';shutil.copy2(cts,result/'parent-cts.tcl');cts.unlink();cts.write_text(render_cts((parent.ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/parent.SUFFIX/'structural_cec'))
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            if stage=='grt':
                execute(base+['grt'],'grt',1200,'grt')
                execute(base+['run','RUN_SCRIPT='+str(parent.backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=pilot_grt',
                    'VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'pilot-grt-snapshot')
            census=result/('census-'+stage+'.tcl');prefix=result/('census-'+stage)
            census.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\nset ownership_prefix {'+str(prefix)+'}\nsource {'+str(parent.ROOT/'experiments/arithmetic_dse/reference_assets/ownership_census_v1.tcl')+'}\n')
            execute(base+['run','RUN_SCRIPT='+str(census),'RUN_LOG_NAME_STEM=continuation_census_'+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'census-'+stage)
        verify_proof(out/'logs'/parent.SUFFIX/'structural_cec/proof.json',out/'results'/parent.SUFFIX/'4_before_rsz_lec.v',out/'results'/parent.SUFFIX/'4_after_rsz_lec.v')
        for n,h in a['inherit_synth']['files_sha256'].items():
            if n.startswith('results/') and sha(out/n)!=h:raise ValueError('paid synthesis result mutated')
    write(result/'pilot-status.json',dict(status='physical_snapshots_collected',synth_inherited=True,CEC=True,S_G_qualified=False,full_D_ready=False))
    print('STAGE67_INHERITED_PILOT_COMPLETE '+task['id'],flush=True)


def run(root):
    a=read(root/'admission.json');p=read(root/'progress.json')
    if p['errors']:raise ValueError('continuation stopped; preserve and diagnose')
    for task in a['tasks']:
        if task['id'] in p['completed']:continue
        p.update(phase='running',active=task['id']);write(root/'progress.json',p)
        try:
            if task['id']==a['no_repeat_synthesis_for']:inherited_point(root,task)
            else:
                def verify(d,pins,c,s):return mapped.verify(d,pins,c,s,Path(task['rtl']).read_text())
                namespace=dict(parent.point.__globals__);namespace.update(mapped=SimpleNamespace(verify=verify),PilotLedger=ContinuationLedger)
                FunctionType(parent.point.__code__,namespace)(root,task)
        except Exception as e:
            p['errors'].append(dict(task=task['id'],reason=str(e)));p.update(phase='stopped_on_error',active=None);write(root/'progress.json',p);raise
        p['completed'].append(task['id']);p.update(phase='point_settled',active=None);write(root/'progress.json',p)
    p['phase']='physical_pilot_complete';write(root/'progress.json',p)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('admit','run'));parser.add_argument('--root',type=Path,required=True);parser.add_argument('--previous',type=Path)
    args=parser.parse_args()
    if args.action=='admit':admit(args.root.resolve(),args.previous.resolve())
    else:run(args.root.resolve())
