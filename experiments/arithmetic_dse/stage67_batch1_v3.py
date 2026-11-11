"""Explicit same-lifetime FF-alias continuation; no completed EDA repeats."""
import argparse
from datetime import datetime,timezone
import inspect
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from . import stage67_batch1_v1 as base,stage67_batch1_v2 as previous,stage67_mapped_state_v3 as mapped
from . import model_m2_live_cec_v4 as cec
from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage


def admit(root,parent):
    if root.exists():raise ValueError('preserve FF-alias continuation')
    a=read(parent/'admission.json');p=read(parent/'progress.json')
    if p['phase']!='stopped_on_error' or len(p['errors'])!=1 or p['errors'][0]['task']!='bypass-placement-0-T1500':raise ValueError('one audited bypass alias stop required')
    proof_path=Path('/home/zyrv/vulsim-artifacts/stage67-bypass-alias-proof-20261111-v1/proof.json')
    census=read(parent/'bypass-alias-census-candidate.json');proof=read(proof_path)
    if census['unique_physical_FF_bits']!=330 or proof['status']!='passed_exact_Boolean_state_functions' or proof['checked_FF_bits']!=census['logical_FF_bit_references']:raise ValueError('actual alias proof missing')
    # 330 is a snapshot audit here, never a model key or accepted FF count for
    # other designs; the general reader computes its own complete census.
    root.mkdir(parents=True);hashes=dict(a['sources'])
    for file in (Path(__file__),Path(mapped.__file__)):hashes[str(file.relative_to(base.ROOT))]=sha(file)
    for n,h in hashes.items():
        if sha(base.ROOT/n)!=h:raise ValueError('frozen producer drift '+n)
        path=root/'source'/n;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base.ROOT/n,path)
    shutil.copytree(parent/'inputs',root/'inputs');tasks=[];inherited_files={}
    for value in a['tasks']:
        t=dict(value)
        for key in ('rtl','endpoint_contract','input_directory'):t[key]=t[key].replace(str(parent),str(root))
        tasks.append(t)
        old=parent/'runs'/t['id']
        if old.exists():
            shutil.copytree(old,root/'runs'/t['id'],symlinks=True)
            inherited_files[t['id']]={str(f.relative_to(old)):sha(f) for f in old.rglob('*') if f.is_file() and (f.is_relative_to(old/'results') or f.name in ('mapped.json','liberty-pins.json','input.sv'))}
    u=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=a['later_work_reserved'];wall=300+2*1200+128*120
    if u['synth']+1+later['synth']>limits['max_synthesis_calls'] or u['grt']+2+later['grt']>limits['max_global_route_calls'] or u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(root).free<later['storage_bytes']+4*1024**3:raise ValueError('alias continuation not funded')
    successor=dict(a,version='stage67-combination-validation-batch1-v3',id=root.name,parent=str(parent),tasks=tasks,sources=hashes,
        synth_max=1,grt_max=2,parent_admission_sha256=sha(parent/'admission.json'),parent_failure_retained=True,
        inherited_files=inherited_files,inherit_synth_task='bypass-placement-0-T1500',inherit_completed=p['completed'],
        alias_census_sha256=sha(parent/'bypass-alias-census-candidate.json'),alias_Boolean_proof_path=str(proof_path),alias_Boolean_proof_sha256=sha(proof_path),
        created_at=datetime.now(timezone.utc).isoformat(),batch_budget=dict(a['batch_budget'],synth=1,grt=2,walltime_s=wall,CPU_time_s=4*wall))
    write(root/'admission.json',successor);write(root/'progress.json',dict(phase='admitted',completed=list(p['completed']),errors=[],active=None));shutil.copy2(parent/'demand-audit.json',root/'demand-audit.json')
    print('BATCH1_FF_ALIAS_CONTINUATION_ADMITTED new_synth=1 new_grt=2 inherited_complete=2 inherited_synth=1',flush=True)


class AliasLedger(base.BatchLedger):
    def reserve(self,stage,*args,**kwargs):
        a=read(self.root/'admission.json')
        if stage=='synth' and (self.task['id'] in a['inherit_completed'] or self.task['id']==a['inherit_synth_task']):raise ValueError('inherited synthesis cannot repeat')
        return super().reserve(stage,*args,**kwargs)


def inherit_synth(root,task):
    from .model_m2_mux_collection import render_cts
    from .processes import run_command
    a=read(root/'admission.json');old=Path(a['parent'])/'runs'/task['id'];out=root/'runs'/task['id']
    (out/'config.mk').write_text((out/'config.mk').read_text().replace(str(old),str(out)))
    state=mapped.verify(read(out/'mapped.json'),read(out/'liberty-pins.json'),read(task['endpoint_contract']),read(Path(task['input_directory'])/'source.json'),(out/'input.sv').read_text());write(out/'mapped-state.json',state)
    wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(base.ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v4 import main\nmain()\n')
    m=read(out/'manifest.json');request=out/'live-cec-request.json';write(request,dict(libraries=m['libraries'],admission_sha256=sha(root/'admission.json'),collection_plan_sha256=sha(root/'admission.json')))
    cts=out/'flow-scripts/cts.tcl'
    if cts.is_symlink():cts.unlink()
    cts.write_text(render_cts((base.physical.ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/base.physical.SUFFIX/'structural_cec'))
    commands=[];ledger=AliasLedger(root,task);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=task['id'])
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    original=read(old/'manifest.json');base_cmd=next(c['command'][:-1] for c in original['commands'] if c['log'].endswith('/synth.log'));base_cmd=[x.replace(str(old),str(out)) for x in base_cmd]
    with ledger.job(ctx):
        def execute(command,name,timeout=120,stage=None):
            r=ledger.reserve(stage,timeout,4,'stage67_alias_synth_continuation',command,out/name,context=ctx);record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'alias-continuation-commands.json',commands)
            if record['exit_code']:raise ValueError('alias synth continuation failed '+record['log'])
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            if stage=='grt':execute(base_cmd+['grt'],'alias-grt',1200,'grt')
            execute(base_cmd+['run','RUN_SCRIPT='+str(base.physical.backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=alias_'+stage,'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'alias-'+stage+'-snapshot')
            script=out/('census-'+stage+'.tcl');prefix=out/('census-'+stage);script.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\nset ownership_prefix {'+str(prefix)+'}\nsource {'+str(base.ROOT/'experiments/arithmetic_dse/reference_assets/ownership_census_v1.tcl')+'}\n')
            execute(base_cmd+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=alias_census_'+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],'alias-census-'+stage)
    cec.verify_proof(out/'logs'/base.physical.SUFFIX/'structural_cec/proof.json',out/'results'/base.physical.SUFFIX/'4_before_rsz_lec.v',out/'results'/base.physical.SUFFIX/'4_after_rsz_lec.v')
    write(out/'pilot-status.json',dict(status='physical_snapshots_collected',synth_inherited=True,CEC=True,source_role=task['source_role'],full_D_ready=False));print('BATCH1_ALIAS_INHERITED_SYNTH_COMPLETE '+task['id'],flush=True)


def fresh(root,task):
    text=inspect.getsource(base.physical.point)
    if text.count('model_m2_live_cec_v3')!=2:raise ValueError('physical CEC callsite changed')
    def verify(d,pins,c,s):return mapped.verify(d,pins,c,s,Path(task['rtl']).read_text())
    ns=dict(base.physical.point.__globals__);ns.update(mapped=SimpleNamespace(verify=verify),PilotLedger=AliasLedger)
    exec(compile(text.replace('model_m2_live_cec_v3','model_m2_live_cec_v4'),__file__,'exec'),ns);ns['point'](root,task)


def run(root):
    a=read(root/'admission.json');p=read(root/'progress.json')
    if p['errors']:raise ValueError('preserve alias continuation failure')
    for task in a['tasks']:
        if task['id'] in p['completed']:continue
        p.update(phase='running',active=task['id']);write(root/'progress.json',p)
        try:
            if task['id']==a['inherit_synth_task']:inherit_synth(root,task)
            else:
                if (root/'runs'/task['id']).exists():raise ValueError('physical attempt cannot repeat')
                fresh(root,task)
        except Exception as error:
            p['errors'].append(dict(task=task['id'],reason=str(error)));p.update(phase='stopped_on_error',active=None);write(root/'progress.json',p);raise
        p['completed'].append(task['id']);p.update(phase='point_settled',active=None);write(root/'progress.json',p)
    p['phase']='physical_batch_complete';write(root/'progress.json',p)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.parent.resolve())
    else:run(a.root.resolve())
