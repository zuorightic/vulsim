"""Independent post-repair recovery, sharing four slots with the frozen collector."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
from datetime import datetime, timezone
import copy
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger,POLICY,usage
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.model_m2_phase_resume import validate_lec,validate_replayed_pair
from experiments.arithmetic_dse.processes import run_command

CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_postrepair_resume_v1.json'
SUFFIX=Path('asap7/arithmetic_probe/base')
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')


def read(path):return json.loads(Path(path).read_text())


def exclusive(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')


def available_slots(jobs,dispatched):
    live=[j for j in jobs if j['status'] in ('active','unsettled')]
    claiming=set(dispatched)-{j['task_id'] for j in live}
    return max(0,4-len(live)-len(claiming))


def render_tail(original,folder):
    marker='    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
    if original.count(marker)!=1:raise ValueError('unsupported CTS tail')
    start=original.index('\n  set result [catch { log_cmd detailed_placement } msg]',original.index(marker))
    prefix='''utl::set_metrics_stage "cts__{}"
source $::env(SCRIPTS_DIR)/load.tcl
source $::env(SCRIPTS_DIR)/lec_check.tcl
erase_non_stage_variables cts
load_design 4_1_post_repair_pre_lec.odb 4_1_post_repair_pre_lec.sdc
proc save_progress { stage } {
  orfs_write_db $::env(RESULTS_DIR)/$stage.odb
  orfs_write_sdc $::env(RESULTS_DIR)/$stage.sdc
}
set_dont_use $::env(DONT_USE_CELLS)
set_placement_padding -global -left $::env(CELL_PAD_IN_SITES_DETAIL_PLACEMENT) -right $::env(CELL_PAD_IN_SITES_DETAIL_PLACEMENT)
write_lec_verilog 4_after_resume_load.v
'''
    proof=folder/'run/logs'/SUFFIX/'lec_resume/proof.json'
    prefix+=f'exec {{{sys.executable}}} -B {{{Path(__file__).resolve()}}} verify-pair --proof {{{proof}}} --before $::env(RESULTS_DIR)/4_before_rsz_lec.v --after $::env(RESULTS_DIR)/4_after_resume_load.v\n'
    return prefix+'if {1} {\n'+original[start:]


def prepare(folder):
    from experiments.arithmetic_dse import model_m2_collection as c
    cfg=read(CONFIG);parent=ROOT/cfg['parent_plan'];p=c.verify_plan(parent)
    t=next(t for t in p['tasks'] if t['id']==cfg['task_id']);source=c.run_directory(parent.parent,t);m=read(source/'manifest.json')
    if (m['status']!='failed' or m.get('failure_code')!='timeout' or m['period_ps']!=cfg['period_ps'] or m['abc_target_ps']!=cfg['abc_target_ps']):
        raise ValueError('not the named settled F3 timeout')
    command=next(x for x in m['commands'] if x['log'].endswith('/grt.log'))
    if not command['timed_out'] or command['cleanup']['remaining_live_pids']:raise ValueError('unsettled F3 failure')
    files={}
    names=('4_1_post_repair_pre_lec.odb','4_1_post_repair_pre_lec.sdc','4_before_rsz_lec.v','4_after_rsz_lec.v','1_synth.sdc','1_synth.odb','1_2_yosys.v')
    for name in names:
        path=source/'results'/SUFFIX/name;h=sha(path)
        if m['evidence_sha256'].get(str(path.relative_to(source)))!=h:raise ValueError('changed post-repair checkpoint')
        files[str(path.relative_to(source))]=h
    folder.mkdir(parents=True,exist_ok=False)
    script=folder/'postrepair-resume.tcl';script.write_text(render_tail((ORFS/'flow/scripts/cts.tcl').read_text(),folder))
    source_names=set(p['sources'])|{str(Path(__file__).relative_to(ROOT)),str(CONFIG.relative_to(ROOT))}
    hashes={}
    for name in source_names:
        dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst);hashes[name]=sha(dst)
    for tid in cfg['tail_task_ids']:
        task=next(x for x in p['tasks'] if x['id']==tid)
        if task['split']!='validation' or c.run_directory(parent.parent,task).exists():raise ValueError('tail task already started or wrong split')
    wall=cfg['lec_timeout_s']+cfg['post_CTS_timeout_s']+cfg['route_timeout_s']+1800
    u=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];future=c.read(c.CONFIG)['later_work_reserved']
    if u['walltime_s']+wall+4*1800+future['walltime_s']>limits['max_global_walltime_h']*3600 or u['CPU_time_s']+4*(wall+4*1800)+future['CPU_time_s']>limits['max_tool_CPU_time_h']*3600:
        raise ValueError('F3 recovery and tail resource envelope not funded')
    if u['grt']+6+future['grt']>limits['max_global_route_calls'] or u['synth']+4+future['synth']>limits['max_synthesis_calls']:raise ValueError('F3 recovery calls not funded')
    if shutil.disk_usage(folder).free<15*1024**3:raise ValueError('F3 recovery storage reserve insufficient')
    wave=parent.parent/'waves/validation-tail-001.json'
    exclusive(wave,{'version':'asap7-m2-primitives-wave-v1','id':p['id']+'-wave-'+wave.stem,'purpose':c.PURPOSE,
        'plan_path':str(parent.resolve()),'plan_sha256':sha(parent),'protocol_sha256':sha(c.CONFIG),'policy_sha256':sha(POLICY),
        'mode':'validation','task_ids':cfg['tail_task_ids'],'funding':c.funding(4,parent.parent,set(cfg['tail_task_ids'])),
        'automatic_retries':0,'call_caps':{'synth':4,'grt':4,'final':0},
        'supplemental_dispatch_reason':'original frozen scheduler drained after F3 failure; new coordinator owns only these four never-started validation tasks'})
    a={'version':'asap7-m2-postrepair-resume-admission-v1','id':folder.name,'task':t,'source_run':str(source.resolve()),
       'source_manifest_sha256':sha(source/'manifest.json'),'checkpoint_sha256':files,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
       'parent_plan':str(parent.resolve()),'parent_plan_sha256':sha(parent),'sources':hashes,'source_snapshot':str((folder/'source').resolve()),
       'script_sha256':sha(script),'tail_wave':str(wave.resolve()),'tail_wave_sha256':sha(wave),
       'lec_executable':str(ORFS/'tools/install/kepler-formal/bin/kepler-formal'),
       'lec_executable_sha256':sha(ORFS/'tools/install/kepler-formal/bin/kepler-formal'),
       'resource_envelope':{'walltime_s':wall+4*1800,'CPU_time_s':4*(wall+4*1800),'future_reserve':future},
       'automatic_retries':0,'test_locked':True}
    exclusive(folder/'admission.json',a)
    (parent.parent/'PAUSE').write_text('F3 failure is handled by the registered supplemental coordinator; existing jobs drain unchanged.\n')
    print(json.dumps({'admission':str(folder/'admission.json'),'recovery':t['id'],'tail_tasks':len(cfg['tail_task_ids']),'existing_jobs_not_interrupted':True}))


def verify(folder):
    a=read(folder/'admission.json')
    if a['protocol_sha256']!=sha(CONFIG) or a['policy_sha256']!=sha(POLICY) or sha(a['parent_plan'])!=a['parent_plan_sha256']:raise ValueError('changed postrepair admission')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(Path(a['source_snapshot'])/name)!=h:raise ValueError('changed supplemental producer: '+name)
    if sha(Path(a['source_run'])/'manifest.json')!=a['source_manifest_sha256'] or sha(folder/'postrepair-resume.tcl')!=a['script_sha256']:
        raise ValueError('changed postrepair source/script')
    if sha(a['tail_wave'])!=a['tail_wave_sha256']:raise ValueError('changed tail admission')
    return a


def task(folder):
    from experiments.arithmetic_dse.backend import stage_metrics,verify_orfs_area
    from experiments.arithmetic_dse.model_samples import read_labels,verify_capture_banks
    from experiments.arithmetic_dse.sdc import verify_sdc,rtl_ports
    a=verify(folder);cfg=read(CONFIG);t=a['task'];source=Path(a['source_run']);old=read(source/'manifest.json');out=folder/'run'
    ledger=Ledger();context={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    with ledger.job(context):
        if out.exists():raise ValueError('preserve existing postrepair attempt; no automatic retry')
        out.mkdir();m=copy.deepcopy(old)
        m.update(status='running',started_at=datetime.now(timezone.utc).isoformat(),commands=[],metrics=[],admission_id=a['id'],
                 budget_job_id=ledger.job_id,source_manifest_sha256=a['source_manifest_sha256'],postrepair_resume=True,
                 source_run=a['source_run'],active_stage='preflight',source_sha256=a['sources'])
        for name in ('finished_at','failure_stage','failure_code','failure_reason','active_reservation'):m.pop(name,None)
        def save():write(out/'manifest.json',m)
        def execute(command,stem,timeout,stage=None):
            reservation=ledger.reserve(stage,timeout,4,'characterization',command,out/stem,context={**context,'admission_sha256':sha(folder/'admission.json')})
            m['active_reservation']=reservation['id'];save()
            record=run_command(command,out,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
            record['budget_reservation_id']=reservation['id'];m['commands'].append(record);save()
            if record['exit_code']:raise RuntimeError(stem+(': timeout' if record['timed_out'] else ': command failed'))
            return record
        env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
        try:
            save();results=out/'results'/SUFFIX;results.mkdir(parents=True)
            for name,h in a['checkpoint_sha256'].items():
                path=source/name
                if sha(path)!=h:raise ValueError('changed bound checkpoint')
                dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
            for name in ('input.sv','sample-contract.json','label_requests.tcl','liberty_cells.json'):
                shutil.copy2(source/name,out/name)
            for lib in old['libraries']:
                if sha(lib['path'])!=lib['sha256']:raise ValueError('changed physical library')
            for tool in old['tools'].values():
                if sha(tool['path'])!=tool['sha256']:raise ValueError('changed physical tool')
            for name,h in old['files_sha256'].items():
                path=Path(name)
                if path.is_relative_to(ORFS) or path.is_relative_to(ROOT/'experiments/arithmetic_dse/backend'):
                    if sha(path)!=h:raise ValueError('changed physical asset')
            for name,h in old['evidence_sha256'].items():
                if name.startswith('reports/'+str(SUFFIX)+'/vulsim_synth'):
                    path=source/name
                    if sha(path)!=h:raise ValueError('changed inherited synth evidence')
                    dst=out/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst)
            scripts=out/'flow-scripts';scripts.mkdir()
            for path in (source/'flow-scripts').iterdir():
                if path.is_symlink():(scripts/path.name).symlink_to(path.resolve())
                elif path.is_file():shutil.copy2(path,scripts/path.name)
            config=out/'config.mk';config.write_text((source/'config.mk').read_text().replace(str(source),str(out)))
            env['VULSIM_LABEL_REQUESTS']=str(out/'label_requests.tcl')
            base=next(c['command'][:-1] for c in old['commands'] if c['log'].endswith('/grt.log'))
            base=[x.replace(str(source),str(out)) for x in base if not x.startswith('--assume-old=')]
            logdir=out/'logs'/SUFFIX/'lec_resume';logdir.mkdir(parents=True)
            log=logdir/'solver.log';request=logdir/'request.yml';before=results/'4_before_rsz_lec.v';after=results/'4_after_rsz_lec.v'
            request.write_text(json.dumps({'format':'verilog','verification':'lec','input_paths':[str(before),str(after)],
                 'liberty_files':[lib['path'] for lib in old['libraries']],'solver':cfg['lec_solver'],'log_file':str(log)},indent=2)+'\n')
            if sha(a['lec_executable'])!=a['lec_executable_sha256']:raise ValueError('changed LEC executable')
            m['active_stage']='lec_resume';record=execute([a['lec_executable'],'--config',str(request)],'lec-resume',cfg['lec_timeout_s'])
            boundary=cfg['expected_boundary'];validate_lec(log.read_text(),boundary['primary_inputs'],boundary['primary_outputs'])
            proof=logdir/'proof.json';proof.write_text(json.dumps({'status':'passed','command_exit_code':record['exit_code'],
                 'reservation_id':record['budget_reservation_id'],'log_path':str(log),'log_sha256':sha(log),'before_sha256':sha(before),
                 'after_sha256':sha(after),'boundary':boundary,'executable':a['lec_executable'],'executable_sha256':a['lec_executable_sha256'],
                 'libraries':old['libraries']},indent=2)+'\n')
            m['active_stage']='CTS_post_LEC';execute(base+['run','RUN_SCRIPT='+str(folder/'postrepair-resume.tcl'),'RUN_LOG_NAME_STEM=4_1_cts_resume'],'cts-post-lec',cfg['post_CTS_timeout_s'],'grt')
            shutil.copy2(results/'4_1_cts.odb',results/'4_cts.odb')
            m['active_stage']='grt';assume=['--assume-old='+str(results/n) for n in ('4_1_cts.odb','4_cts.odb','4_cts.sdc')]
            execute(base+assume+['grt'],'grt',cfg['route_timeout_s'],'grt')
            m['active_stage']='grt_snapshot';execute(base+['run','RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),
                'RUN_LOG_NAME_STEM=vulsim_grt','VULSIM_EVAL_STAGE=grt','VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc'],'grt-snapshot',120)
            cells=read(out/'liberty_cells.json')['cells'];reports=out/'reports'/SUFFIX
            g=stage_metrics(reports,'grt',cells,t['period_ps'],selected=old['platform_profile'])
            g['model_labels']=read_labels(reports/'vulsim_grt',out/'sample-contract.json',g['raw_report_units']['time']['to_ps'])
            g['model_capture_banks']=verify_capture_banks(reports/'vulsim_grt',out/'sample-contract.json',cells)
            g.update(abc_target_ps=1500,mapping_context_sha256=old['mapping_context_sha256'],target_dependent_measurement=True)
            native=read(out/'logs'/SUFFIX/'5_1_grt.json')['globalroute__design__instance__area__stdcell']
            g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native);g['orfs_stdcell_area_um2']=native
            verify_sdc((results/'5_1_grt.sdc').read_text(),old['platform_profile'],t['period_ps'],rtl_ports((out/'input.sv').read_text(),t['top']))
            if not g['timing_coverage_complete']:raise ValueError('incomplete resumed timing coverage')
            synth=copy.deepcopy(next(x for x in old['metrics'] if x['stage']=='synth'));synth['raw_reports_prefix']=str(reports/'vulsim_synth')
            m.update(status='completed',metrics=[synth,g],inherited_synth_manifest_sha256=a['source_manifest_sha256'],
                checkpoint_reuse={'mode':'exact_postrepair_ODB_after_complete_LEC','source_manifest_sha256':a['source_manifest_sha256'],
                                 'proof_path':str(proof),'proof_sha256':sha(proof),'no_CTS_repair_replay':True,'cold_runtime_claimed':False})
            m['files_sha256'].update({str(path):sha(path) for path in (config,proof,request,folder/'postrepair-resume.tcl')})
            write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_stage=m['active_stage'],failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(path.relative_to(out)):sha(path) for name in ('logs','reports','results') for path in (out/name).rglob('*') if path.is_file()}
            save()
        print(json.dumps({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')}),flush=True)
        if m['status']!='completed':raise RuntimeError('F3 postrepair continuation failed')


def run(folder):
    from experiments.arithmetic_dse import model_m2_collection as c
    a=verify(folder);cfg=read(CONFIG);wave=Path(a['tail_wave']);w=read(wave);p=c.verify_plan(a['parent_plan']);indexed={t['id']:t for t in p['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('supplemental coordinator already active')
        waiting=[cfg['task_id'],*cfg['tail_task_ids']];active={};outcomes=[];errors=[]
        def launch(tid):
            if tid==cfg['task_id']:task(folder);return {'task_id':tid,'kind':'postrepair_resume'}
            return c.run_task(Path(a['parent_plan']).parent,wave,w,indexed[tid])
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                jobs=read(Ledger().path)['jobs'];slots=available_slots(jobs,{tid for tid in active.values()})
                while waiting and slots and not errors:
                    tid=next((tid for tid in waiting if tid==cfg['task_id'] or ready(indexed[tid],indexed,Path(a['parent_plan']).parent)),None)
                    if tid is None:break
                    waiting.remove(tid);active[pool.submit(launch,tid)]=tid;slots-=1
                write(folder/'progress.json',{'phase':'collecting' if active or waiting else 'supplemental_complete',
                     'updated_at':datetime.now(timezone.utc).isoformat(),'active':list(active.values()),'waiting':waiting,'completed':outcomes,'errors':errors})
                if not active:
                    if errors:break
                    if waiting:time.sleep(1);continue
                    break
                completed,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in completed:
                    tid=active.pop(future)
                    try:outcomes.append(future.result())
                    except Exception as error:errors.append({'task_id':tid,'reason':str(error)})
            write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'supplemental_complete','updated_at':datetime.now(timezone.utc).isoformat(),'completed':outcomes,'errors':errors,'waiting':waiting})
        if errors:raise RuntimeError(str(errors))


def ready(task,indexed,folder):
    from experiments.arithmetic_dse.model_m2_collection import run_directory
    if not task['mapping_source_task']:return True
    path=run_directory(folder,indexed[task['mapping_source_task']])/'manifest.json'
    return path.exists() and read(path).get('status')=='completed'


def bootstrap(folder):
    ledger=Ledger();context={'target_platform':'asap7','admission_id':folder.name+'-setup','task_id':'postrepair-resume-preparation'}
    folder.parent.mkdir(parents=True,exist_ok=True);logs=folder.parent/(folder.name+'-setup');logs.mkdir(exist_ok=False)
    with ledger.job(context):
        env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
        for stem,command,timeout in [('tests',[sys.executable,'-B','-m','unittest','regression.arithmetic_postrepair_resume'],120),
                 ('prepare',[sys.executable,'-B','-m','experiments.arithmetic_dse.model_m2_postrepair_resume','prepare','--folder',str(folder)],180)]:
            reservation=ledger.reserve(None,timeout,4,'postrepair_resume_setup',command,logs/stem,context=context)
            record=run_command(command,logs,stem,timeout,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
            print((logs/(stem+'.log')).read_text()[-4000:])
            if record['exit_code']:raise RuntimeError('setup '+stem+' failed')


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['prepare','run','bootstrap','verify-pair'])
    ap.add_argument('--folder',type=Path);ap.add_argument('--proof',type=Path);ap.add_argument('--before',type=Path);ap.add_argument('--after',type=Path);a=ap.parse_args()
    if a.action=='verify-pair':validate_replayed_pair(a.proof,a.before,a.after)
    else:{'prepare':prepare,'run':run,'bootstrap':bootstrap}[a.action](a.folder.resolve())


if __name__=='__main__':main()
