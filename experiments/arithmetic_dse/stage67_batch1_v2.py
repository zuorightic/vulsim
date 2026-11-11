"""Explicit CEC-reader successor; resume saved post-repair state, no EDA retry.

One failed parent grt is retained. Exactly three new synth and four grt leaves
are admitted; the saved first synth/CTS/repair are never executed again.
"""
import argparse
from datetime import datetime,timezone
import inspect
import os
from pathlib import Path
import shutil
from types import FunctionType,SimpleNamespace

from . import stage67_batch1_v1 as parent,model_m2_live_cec_v4 as cec
from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage

RECOVERY=Path('/home/zyrv/vulsim-artifacts/stage67-batch1-cec-recovery-20261111-v1')


def admit(root,previous):
    if root.exists():raise ValueError('preserve continuation admission')
    a=read(previous/'admission.json');p=read(previous/'progress.json');task=a['tasks'][0]
    if p['phase']!='stopped_on_error' or len(p['errors'])!=1 or p['errors'][0]['task']!=task['id']:raise ValueError('one audited CEC failure required')
    original=previous/'runs'/task['id'];results=original/'results'/parent.physical.SUFFIX
    cec.verify_proof(RECOVERY/'proof.json',results/'4_before_rsz_lec.v',results/'4_after_rsz_lec.v')
    saved=['4_1_post_repair_pre_lec.odb','4_1_post_repair_pre_lec.sdc','4_before_rsz_lec.v','4_after_rsz_lec.v','1_synth.odb','1_synth.sdc','1_2_yosys.v']
    fixed={name:sha(results/name) for name in saved};m=read(original/'manifest.json')
    if [x['stage'] for x in m['metrics']]!=['synth']:raise ValueError('unexpected parent state')
    root.mkdir(parents=True);hashes=dict(a['sources'])
    hashes.update({str(x.relative_to(parent.ROOT)):sha(x) for x in (Path(__file__),Path(cec.__file__))})
    for n,h in hashes.items():
        if sha(parent.ROOT/n)!=h:raise ValueError('producer drift '+n)
        dest=root/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(parent.ROOT/n,dest)
    shutil.copytree(previous/'inputs',root/'inputs');tasks=[]
    for item in a['tasks']:
        t=dict(item)
        for key in ('rtl','endpoint_contract','input_directory'):t[key]=t[key].replace(str(previous),str(root))
        tasks.append(t)
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=a['later_work_reserved'];wall=3*300+4*1200+128*120
    if used['synth']+3+later['synth']>limits['max_synthesis_calls'] or used['grt']+4+later['grt']>limits['max_global_route_calls'] or used['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:raise ValueError('continuation not funded')
    if shutil.disk_usage(root).free<later['storage_bytes']+4*1024**3:raise ValueError('continuation storage not funded')
    successor=dict(a,version='stage67-combination-validation-batch1-v2',id=root.name,tasks=tasks,sources=hashes,synth_max=3,grt_max=4,
        parent=str(previous),original_software_parent=a['parent'],parent_admission_sha256=sha(previous/'admission.json'),
        created_at=datetime.now(timezone.utc).isoformat(),inherit_post_repair=dict(directory=str(original),files_sha256=fixed,
            recovery_proof=str(RECOVERY/'proof.json'),recovery_proof_sha256=sha(RECOVERY/'proof.json'),task_id=task['id']),
        no_repeat_synth_CTS_or_repair_for=task['id'],parent_failure_retained=True,batch_budget=dict(a['batch_budget'],synth=3,grt=4,walltime_s=wall,CPU_time_s=4*wall))
    write(root/'admission.json',successor);write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=None));shutil.copy2(previous/'demand-audit.json',root/'demand-audit.json')
    print('BATCH1_CEC_SUCCESSOR_ADMITTED synth=3 grt=4 inherit_post_repair=1',flush=True)


class SuccessorLedger(parent.BatchLedger):
    def reserve(self,stage,*args,**kwargs):
        a=read(self.root/'admission.json')
        if stage=='synth' and self.task['id']==a['no_repeat_synth_CTS_or_repair_for']:raise ValueError('cannot repeat inherited synthesis')
        return super().reserve(stage,*args,**kwargs)


def inherited(root,task):
    from .processes import run_command
    a=read(root/'admission.json');old=Path(a['inherit_post_repair']['directory']);out=root/'runs'/task['id'];oldresults=old/'results'/parent.physical.SUFFIX
    for n,h in a['inherit_post_repair']['files_sha256'].items():
        if sha(oldresults/n)!=h:raise ValueError('parent snapshot changed')
    shutil.copytree(old,out,symlinks=True);(out/'config.mk').write_text((out/'config.mk').read_text().replace(str(old),str(out)))
    logs=out/'logs'/parent.physical.SUFFIX;(logs/'structural_cec').rename(logs/'structural_cec-v3-failed');shutil.copytree(RECOVERY,logs/'structural_cec')
    cts=out/'flow-scripts/cts.tcl'
    if cts.is_symlink():cts.unlink()
    cts.write_text('utl::set_metrics_stage "cts__{}"\nsource $::env(SCRIPTS_DIR)/load.tcl\nsource $::env(SCRIPTS_DIR)/lec_check.tcl\n'+
        'erase_non_stage_variables cts\nload_design 4_1_post_repair_pre_lec.odb 4_1_post_repair_pre_lec.sdc\n'+
        'puts "Resuming exact saved post-repair design after separately verified structural CEC"\n'+
        'set result [catch { log_cmd detailed_placement } msg]\nif {$result != 0} {error "resumed detailed placement failed: $msg"}\n'+
        'check_placement -verbose\nlog_cmd estimate_parasitics -placement\nreport_metrics 4 "cts final"\nsource_step_tcl POST CTS\n'+
        'orfs_write_db $::env(RESULTS_DIR)/4_1_cts.odb\norfs_write_sdc $::env(RESULTS_DIR)/4_cts.sdc\n')
    m=read(old/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'));base=[x.replace(str(old),str(out)) for x in base]
    ledger=SuccessorLedger(root,task);ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=task['id']);records=[]
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen')
    with ledger.job(ctx):
        def execute(command,name,timeout=120,stage=None):
            reservation=ledger.reserve(stage,timeout,4,'stage67_post_repair_continuation',command,out/name,context=ctx)
            record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
            records.append(dict(**record,budget_reservation_id=reservation['id']));write(out/'continuation-commands.json',records)
            if record['exit_code']:raise ValueError('post-repair continuation failed '+record['log'])
        execute(base+['grt'],'continuation-grt',1200,'grt')
        execute(base+['run','RUN_SCRIPT='+str(parent.physical.backend.ASSETS/'snapshot.tcl'),'RUN_LOG_NAME_STEM=pilot_grt','VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'continuation-grt-snapshot')
        census=out/'census-grt.tcl';prefix=out/'census-grt';census.write_text('source $::env(SCRIPTS_DIR)/load.tcl\nload_design $::env(VULSIM_EVAL_DB) $::env(VULSIM_EVAL_SDC)\nset ownership_prefix {'+str(prefix)+'}\nsource {'+str(parent.ROOT/'experiments/arithmetic_dse/reference_assets/ownership_census_v1.tcl')+'}\n')
        execute(base+['run','RUN_SCRIPT='+str(census),'RUN_LOG_NAME_STEM=census_grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'continuation-census-grt')
    results=out/'results'/parent.physical.SUFFIX
    for n,h in a['inherit_post_repair']['files_sha256'].items():
        if sha(results/n)!=h:raise ValueError('inherited design mutated '+n)
    cec.verify_proof(logs/'structural_cec/proof.json',results/'4_before_rsz_lec.v',results/'4_after_rsz_lec.v')
    cells=read(out/'liberty_cells.json')['cells'];metric=parent.physical.backend.stage_metrics(out/'reports'/parent.physical.SUFFIX,'grt',cells,1500,selected=parent.physical.profile('asap7'))
    # Stored SDC, RC and area are cross-checked for every stage again by the
    # final analyzer, for inherited and fresh tasks alike.
    write(out/'pilot-metrics.json',m['metrics']+[metric]);write(out/'pilot-status.json',dict(status='physical_snapshots_collected',synth_CTS_repair_inherited=True,
        mapped_state_FF_census=True,CEC=True,source_role=task['source_role'],full_D_ready=False))
    print('BATCH1_POST_REPAIR_CONTINUED '+task['id'],flush=True)


def fresh(root,task):
    source=inspect.getsource(parent.physical.point)
    if source.count('model_m2_live_cec_v3')!=2:raise ValueError('unexpected frozen physical CEC callsites')
    source=source.replace('model_m2_live_cec_v3','model_m2_live_cec_v4')
    def verify(d,pins,c,s):return parent.mapped.verify(d,pins,c,s,Path(task['rtl']).read_text())
    namespace=dict(parent.physical.point.__globals__);namespace.update(mapped=SimpleNamespace(verify=verify),PilotLedger=SuccessorLedger)
    exec(compile(source,__file__,'exec'),namespace);namespace['point'](root,task)


def run(root):
    a=read(root/'admission.json');p=read(root/'progress.json')
    if p['errors']:raise ValueError('successor stopped; no automatic retry')
    for task in a['tasks']:
        if task['id'] in p['completed']:continue
        if (root/'runs'/task['id']).exists():raise ValueError('preserve prior continuation attempt')
        p.update(phase='running',active=task['id']);write(root/'progress.json',p)
        try:
            if task['id']==a['no_repeat_synth_CTS_or_repair_for']:inherited(root,task)
            else:fresh(root,task)
        except Exception as error:
            p['errors'].append(dict(task=task['id'],reason=str(error)));p.update(phase='stopped_on_error',active=None);write(root/'progress.json',p);raise
        p['completed'].append(task['id']);p.update(phase='point_settled',active=None);write(root/'progress.json',p)
    p['phase']='physical_batch_complete';write(root/'progress.json',p)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--previous',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.previous.resolve())
    else:run(a.root.resolve())
