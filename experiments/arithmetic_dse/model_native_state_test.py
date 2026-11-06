"""Prospective native-state independent collection; frozen one-shot verdict.

The physical worker is copied from the admitted fitting collector. Independent
role and immutable selection checks are enforced before each paid leaf.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from .budget import Ledger,POLICY,usage
from .model_collection import sha,write
from .model_native_state_collection import ROOT,CONFIG,SUFFIX,ASSETS,read,verify as verify_collection
from .model_native_state_fit import verify_fit,reparse,rows_for_task
from .model_native_state_samples import specifications,source,features
from .model_native_state_labels import labels,witness,render_requests
from .model_m2_state_fit import quality
from .model_m2_state_replay import RawAudit
from . import model_m2_state_collection as legacy

VERSION='asap7-native-state-independent-admission-v1'


def verify(folder):
    a=read(folder/'admission.json');f=verify_fit(Path(a['selection_path']).parent);cfg=read(CONFIG)
    if (a['version']!=VERSION or a['test_locked'] or sha(a['selection_path'])!=a['selection_sha256']
        or f['status']!='frozen_awaiting_independent_test' or f['test_observed']
        or sha(CONFIG)!=a['protocol_sha256'] or sha(POLICY)!=a['policy_sha256']
        or sha(a['fitting_admission_path'])!=a['fitting_admission_sha256']):
        raise ValueError('native independent frozen admission changed')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('native independent producer changed: '+name)
    original=read(a['fitting_admission_path'])
    expected=[t for t in original['tasks'] if t['split']=='test']
    if a['tasks']!=expected or len(expected)!=36:raise ValueError('native test role/target/source registration differs')
    return a


def prepare(folder,fitting,selection,reproduced):
    parent=verify_collection(fitting);f=verify_fit(selection.parent);cfg=read(CONFIG)
    if (f['status']!='frozen_awaiting_independent_test' or f['test_observed']
        or f['admission_sha256']!=sha(fitting/'admission.json')):raise ValueError('native-state fit not ready')
    for name in ('candidate.json','validation.json','selection-freeze.json'):
        if (selection.parent/name).read_bytes()!=(reproduced/name).read_bytes():raise ValueError('native-state fit not byte reproduced')
    tasks=[t for t in parent['tasks'] if t['split']=='test']
    if len(tasks)!=36 or any((fitting/'runs'/t['id']).exists() for t in tasks):raise ValueError('native tests already observed')
    u=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=cfg['later_work_reserved']
    wall=36*cfg['resources']['per_task_walltime_envelope_s']+600
    storage=36*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']
    if (u['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
        or u['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
        or u['synth']+36+later['synth']>limits['max_synthesis_calls']
        or u['grt']+36+later['grt']>limits['max_global_route_calls'] or shutil.disk_usage(folder.parent).free<storage):
        raise ValueError('native independent cohort/later reserve not funded')
    folder.mkdir(parents=True,exist_ok=False);sources=dict(parent['sources'])
    for path in [Path(__file__),Path(__file__).with_name('model_native_state_fit.py'),
                 Path(__file__).with_name('model_m2_state_fit.py'),Path(__file__).with_name('model_m2_state_replay.py'),Path(__file__).with_name('model_training.py')]:
        sources[str(path.relative_to(ROOT))]=sha(path)
    for name in sources:
        dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst)
    legacy.exclusive(folder/'admission.json',{'version':VERSION,'id':folder.name,'sources':sources,'tasks':tasks,
        'test_locked':False,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
        'selection_path':str(selection),'selection_sha256':sha(selection),'candidate_sha256':f['candidate_sha256'],
        'fitting_admission_path':str(fitting/'admission.json'),'fitting_admission_sha256':sha(fitting/'admission.json'),
        'measurement_static_identity_sha256':parent['measurement_static_identity_sha256'],
        'capacity_pilot':cfg['independent_capacity_pilot'],'automatic_retries':0,
        'resource_plan':{'tasks':36,'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,'storage_reserved_bytes':storage,'later_reserved':later},
        'evaluation_rule':'unchanged per-stage state-area gates; at every exact SDC frozen register and input overheads cover independent maxima; no refit/reserve/domain change',
        'full_D_ready':False})
    write(folder/'progress.json',{'phase':'independent_admitted','active':[],'completed':[],
        'waiting':[t['id'] for t in tasks],'errors':[],'capacity_qualified':False,'test_locked':False})
    verify(folder)
    print(json.dumps({'status':'independent_admitted','tasks':36,'selection_sha256':sha(selection),
        'capacity_pilot':cfg['independent_capacity_pilot'],'walltime_envelope_s':wall}),flush=True)


class TestLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder);t=next(x for x in a['tasks'] if x['id']==self.task['id'])
        if (t!=self.task or t['split']!='test' or threads!=4
            or sha(t['rtl'])!=t['rtl_sha256'] or sha(t['contract'])!=t['contract_sha256']):
            raise ValueError('native independent unregistered tool call')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':t['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'selection_freeze_sha256':a['selection_sha256'],
            'model_version':'asap7-native-state-independent-v1'})


def run_task(folder,t):
    from .backend import _evaluate,stage_metrics,verify_orfs_area
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .platforms import profile,verify_wire_readback,resolve_environment,validate_environment
    from .processes import run_command
    from .sdc import verify_sdc,rtl_ports
    a=verify(folder)
    if t not in a['tasks'] or t['split']!='test':raise ValueError('only registered native independent tests may execute')
    out=folder/'runs'/t['id']
    if out.exists():raise ValueError('preserve native-state attempt; no automatic retry')
    ledger=TestLedger(folder,t);ctx={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',
        PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen',VULSIM_NATIVE_STATE_REQUESTS=str(out/'native-requests.tcl'))
    with ledger.job(ctx):
        if t['mapping_source_task']:
            m,base=legacy.seed_mapping(folder,t,out)
        else:
            args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,
                period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,
                budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=None,
                admission=None,resume_synth_from=None,orfs=legacy.ORFS,rtl=Path(t['rtl']),top='ModelBundle',
                synth_timeout_s=300,route_timeout_s=1200,selection_freeze=None)
            _evaluate(args,ledger);m=read(out/'manifest.json')
            if m['status']!='completed':raise RuntimeError('native-state initial synthesis failed: '+str(m.get('failure_reason')))
            base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        m.update(status='running',stages_requested='grt',budget_job_id=ledger.job_id,
            native_state_admission_sha256=sha(folder/'admission.json'),native_state_collection_version=a['version'],selection_freeze_sha256=a['selection_sha256'],candidate_sha256=a['candidate_sha256'])
        def save():write(out/'manifest.json',m)
        def execute(command,name,timeout,stage=None):
            m['active_stage']=name;r=ledger.reserve(stage,timeout,4,'native_state_characterization',command,out/name,context=ctx)
            m['active_reservation']=r['id'];save()
            c=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,c)
            c['budget_reservation_id']=r['id'];m['commands'].append(c);save()
            if c['exit_code']:raise RuntimeError(name+': failed; timeout='+str(c['timed_out']))
        try:
            for name in ('native-state-contract.json','sample-contract.json'):shutil.copy2(t['contract'],out/name)
            (out/'label_requests.tcl').write_text('set vulsim_label_requests {}\n')
            (out/'native-requests.tcl').write_text(render_requests())
            script=out/'native-snapshot.tcl'
            snapshot=(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl').read_text()
            snapshot=snapshot.replace('source [file join [file dirname [info script]] rc_readback.tcl]',
                'source {'+str(ROOT/'experiments/arithmetic_dse/backend/rc_readback.tcl')+'}')
            snapshot=snapshot.replace('source [file join [file dirname [info script]] model_labels.tcl]',
                'source {'+str(ASSETS/'labels.tcl')+'}')
            script.write_text(snapshot)
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,{'libraries':m['libraries'],
                'admission_sha256':sha(folder/'admission.json'),'collection_plan_sha256':sha(folder/'admission.json')})
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((legacy.ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            added=[script,wrapper,request,cts,out/'native-requests.tcl',out/'native-state-contract.json',out/'sample-contract.json',out/'label_requests.tcl',out/'config.mk',ASSETS/'labels.tcl']
            m['files_sha256'].update({str(p):sha(p) for p in added})
            for name in ('model_native_state_test.py','model_native_state_fit.py','model_native_state_collection.py','model_native_state_samples.py','model_native_state_labels.py'):
                p=Path(__file__).with_name(name);d=out/'source'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d);m['source_sha256'][str(p.relative_to(ROOT))]=sha(p)
            for asset in [*m['tools'].values(),*m['libraries']]:
                if sha(asset['path'])!=asset['sha256']:raise ValueError('native-state physical tool or Liberty changed')
            if t['mapping_source_task']:
                execute(base+['vulsim-environment','VULSIM_ENV_FILE='+str(out/'effective-environment.txt')],'environment',60)
                raw=dict(line.strip().split('=',1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
                effective,origins=resolve_environment(raw);validate_environment(effective,profile('asap7'))
                for key in ('LIB_FILES','TECH_LEF','SC_LEF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','YOSYS_MAX_THREADS'):
                    if effective.get(key)!=m['effective_environment'].get(key):raise ValueError('native mapping environment differs')
                m.update(raw_make_environment=raw,effective_environment=effective,asset_resolution=origins)
                execute(base+['synth'],'synth',300,'synth')
            if measurement_identity(m)!=a['measurement_static_identity_sha256']:raise ValueError('native physical identity differs from released parent')
            p=profile('asap7');cells=read(out/'liberty_cells.json')['cells'];m['metrics']=[]
            for stage in ('synth','grt'):
                if stage=='grt':execute(base+['grt'],'grt',1200,'grt')
                stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
                execute(base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=vulsim_'+stage,
                    'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],stage+'-native-snapshot',120)
                reports=out/'reports'/SUFFIX;g=stage_metrics(reports,stage,cells,t['period_ps'],selected=p)
                g['native_state_paths']=labels(reports/('vulsim_'+stage),t['period_ps'],g['raw_report_units']['time']['to_ps'])
                g['native_state_witness']=witness(out,stage,cells)
                rc=verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),p)
                if rc is not None:g['wire_RC_readback']=rc
                actual_sdc=out/'results'/SUFFIX/(stem+'.sdc')
                m['sdc_contracts'][stage]=verify_sdc(actual_sdc.read_text(),p,t['period_ps'],rtl_ports((out/'input.sv').read_text(),'ModelBundle'))
                native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native)
                if not g['timing_coverage_complete']:raise ValueError('native-state timing coverage incomplete')
                m['metrics'].append(g);save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
            m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_stage=m.get('active_stage','native_state_preflight'),failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(p.relative_to(out)):sha(p) for name in ('logs','reports','results') for p in (out/name).rglob('*') if p.is_file()};save()
        print(json.dumps({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')}),flush=True)
        if m['status']!='completed':raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/tid).exists() for tid in indexed):raise ValueError('preserve independent attempts; no automatic retry')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and a['capacity_pilot'] in completed:
                    d=folder/'runs'/a['capacity_pilot'];m=read(d/'manifest.json')
                    legacy.exclusive(folder/'capacity-proof.json',{'status':'passed','task_id':a['capacity_pilot'],
                        'manifest_sha256':sha(d/'manifest.json'),'actual_state':m['metrics'][-1]['native_state_witness'],
                        'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024,
                        'scope':'registered native independent banks only; no whole-stage or full D qualification'})
                    capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((tid for tid in waiting if (capacity or tid==a['capacity_pilot']) and
                        (not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed)),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                write(folder/'progress.json',{'phase':'independent_collecting','active':list(active.values()),'completed':completed,
                    'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
                if not active:
                    if waiting and not errors:raise ValueError('native independent mapping/capacity deadlock')
                    break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    tid=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':tid,'reason':str(error)})
        write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'test_collection_complete','active':[],
            'waiting':waiting,'completed':completed,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
        if errors:raise RuntimeError(str(errors))


def report(candidate,rows,cfg):
    result={}
    for stage in ('synth','grt'):
        group=[r for r in rows if r['stage']==stage];model=candidate['stages'][stage]
        area=quality(model['area_model'],group,cfg);b=model['boundary_model'];coverage={}
        for period in cfg['SDC_ps']:
            paths=[p for r in group if r['period_ps']==period for p in r['boundary_paths']]
            reg=[p for p in paths if p['kind']=='register'];primary=[p for p in paths if p['kind']=='port']
            reg_required=max(0.,max(p['H_ps'] for p in reg))+max(0.,max(p['delay_ps'] for p in reg))
            primary_required=max(0.,max(p['H_ps'] for p in primary))+max(0.,max(p['delay_ps'] for p in primary))
            required_input=max(reg_required,primary_required)
            rm=b['register_overhead_ps']-reg_required;im=b['input_overhead_ps']-required_input
            coverage[str(period)]={'status':'passed' if rm>=0 and im>=0 else 'failed',
                'registered_H_plus_QD_ps':reg_required,'primary_H_plus_PD_ps':primary_required,
                'frozen_register_ps':b['register_overhead_ps'],'frozen_input_ps':b['input_overhead_ps'],
                'register_margin_ps':rm,'input_margin_ps':im}
        passed=area['status']=='passed' and all(c['status']=='passed' for c in coverage.values())
        result[stage]={'status':'passed' if passed else 'failed','state_area':area,'boundary_coverage':coverage,
            'state_area_by_exact_SDC':{str(t):quality(model['area_model'],[r for r in group if r['period_ps']==t],cfg) for t in cfg['SDC_ps']},
            'whole_setup_failed':sum(r['whole_setup_slack_ps']<0 for r in group),'whole_hold_negative':sum(r['whole_hold_slack_ps']<0 for r in group)}
    return result


def evaluate(folder,out):
    a=verify(folder);progress=read(folder/'progress.json')
    if (progress['phase']!='test_collection_complete' or set(progress['completed'])!={t['id'] for t in a['tasks']}
        or progress['active'] or progress['errors'] or progress['waiting']):raise ValueError('all36 native independent tests must complete')
    out.mkdir(parents=True,exist_ok=False)
    legacy.exclusive(folder/'evaluation-claim.json',{'selection_sha256':a['selection_sha256'],
        'admission_sha256':sha(folder/'admission.json'),'output':str(out),'refit_or_reserve_change':False})
    fit=verify_fit(Path(a['selection_path']).parent);dataset=read(fit['dataset_path'])
    fitting_sources={r['source_sha256'] for r in dataset['rows']};cfg=read(CONFIG)
    specs={s['id']:s for s in specifications(cfg)};audit=RawAudit(read(Ledger().path)['entries']);rows=[]
    for t in a['tasks']:
        d=folder/'runs'/t['id'];spec=specs[t['source_group']]
        if t['rtl_sha256'] in fitting_sources or source(spec)!=(d/'input.sv').read_text() or t['features']!=features(spec,t['period_ps']):
            raise ValueError('native independent source/feature/partition differs')
        audit.ancestry(d);m,metrics,identity=reparse(d,t)
        if (identity!=a['measurement_static_identity_sha256'] or m['selection_freeze_sha256']!=a['selection_sha256']
            or m['candidate_sha256']!=a['candidate_sha256'] or m['native_state_admission_sha256']!=sha(folder/'admission.json')):
            raise ValueError('native test selection/physical binding differs')
        for c in m['commands']:
            if audit.entries[c['budget_reservation_id']].get('selection_freeze_sha256')!=a['selection_sha256']:
                raise ValueError('native independent paid leaf missing immutable selection')
        rows.extend(rows_for_task(t,metrics,sha(d/'manifest.json')))
    if len(rows)!=72 or any(r['split']!='test' for r in rows):raise ValueError('native independent stage coverage incomplete')
    candidate=read(Path(a['selection_path']).parent/'candidate.json');result=report(candidate,rows,cfg)
    write(out/'test-dataset.json',{'version':'asap7-native-state-independent-dataset-v1','rows':rows,
        'selection_sha256':a['selection_sha256'],'admission_sha256':sha(folder/'admission.json'),
        'audit':{'status':'passed','physical_runs':36,'stage_rows':72,'path_labels':288,'paid_leaves':len(audit.commands),
            'raw_files_checked':len(audit.hashed),'PPA_calls':0}})
    write(out/'verdict.json',{'version':'asap7-native-state-independent-verdict-v1','status':result['grt']['status'],
        'stages':result,'selection_sha256':a['selection_sha256'],'candidate_sha256':a['candidate_sha256'],
        'admission_sha256':sha(folder/'admission.json'),'test_dataset_sha256':sha(out/'test-dataset.json'),
        'parameters_or_reserve_or_domain_changed':False,'independent_labels_consumed':True,
        'PPA_calls_during_evaluation':0,'production_price_binding_qualified':False,'full_D_ready':False})
    print(json.dumps({'status':result['grt']['status'],'stages':{s:{'status':r['status'],
        'area_median_relative_error':r['state_area']['median_relative_error'],'area_p95_relative_error':r['state_area']['p95_relative_error'],
        'boundary':r['boundary_coverage']} for s,r in result.items()}}),flush=True)


def status(folder):
    a,p=read(folder/'admission.json'),read(folder/'progress.json');counts=Counter()
    print(datetime.now().astimezone().isoformat(timespec='seconds'));print('原生状态协议独立测试：'+p['phase'])
    for t in a['tasks']:
        f=folder/'runs'/t['id']/'manifest.json';m=read(f) if f.exists() else {};counts[m.get('status','not_started')]+=1
        if m.get('status')=='running':print('任务：',t['id'],'阶段：',m.get('active_stage'))
    print(f'完成{counts["completed"]}/36；{dict(counts)}；容量准入：{p["capacity_qualified"]}')
    print('最多4任务×4线程／8GiB；只采集，采完停止，不自动评价／拟合或发布。');print('错误：',p['errors'])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run','verify','status','evaluate'))
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--fitting',type=Path);p.add_argument('--selection',type=Path)
    p.add_argument('--reproduced',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':
        if None in (a.fitting,a.selection,a.reproduced):p.error('prepare requires fitting/selection/reproduced')
        prepare(folder,a.fitting.resolve(),a.selection.resolve(),a.reproduced.resolve())
    elif a.action=='run':run(folder)
    elif a.action=='status':status(folder)
    elif a.action=='evaluate':
        if a.out is None:p.error('evaluate requires out')
        evaluate(folder,a.out.resolve())
    else:verify(folder);print('verified native independent admission')


if __name__=='__main__':main()
