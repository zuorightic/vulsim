"""Admitted four-thread native-state fitting collection; independent tests locked."""
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
from .model_native_state_samples import specifications,source,features
from .model_native_state_labels import labels,witness,render_requests
from . import model_m2_state_collection as legacy

ROOT=legacy.ROOT
CONFIG=Path(__file__).with_name('configs')/'model_asap7_native_state_v1.json'
SUFFIX=legacy.SUFFIX
ASSETS=Path(__file__).with_name('native_state_assets')


def read(path):return json.loads(Path(path).read_text())


def prepare(folder,software_proof):
    from .platforms import profile
    cfg,proof=read(CONFIG),read(software_proof)
    if (proof['status']!='passed' or proof['protocol_sha256']!=sha(CONFIG)
        or proof['generator_sha256']!=sha(Path(__file__).with_name('model_native_state_samples.py'))
        or not proof['native_primary_and_previous_valid_enables']):
        raise ValueError('current native-state software proof required')
    for name,h in proof['native_binding_sources'].items():
        if sha(ROOT/name)!=h:raise ValueError('native state binding source changed after proof')
    if (sha(proof['native_audit_path'])!=proof['native_audit_sha256']
        or sha(Path(proof['native_audit_path']).parent/'native/queries.json')!=proof['native_queries_sha256']):
        raise ValueError('native state audit changed after software proof')
    for key in ('parent_model','parent_primitives'):
        if sha(ROOT/cfg[key])!=cfg[key+'_sha256'] or read(ROOT/cfg[key])['quality_status']!='passed':
            raise ValueError('native-state unchanged published parent required')
    total=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=cfg['later_work_reserved']
    tasks_count=sum(v['tasks'] for v in cfg['splits'].values())
    wall=tasks_count*cfg['resources']['per_task_walltime_envelope_s']+cfg['support_walltime_envelope_s']
    storage=tasks_count*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']
    if (total['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
        or total['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
        or total['synth']+tasks_count+later['synth']>limits['max_synthesis_calls']
        or total['grt']+tasks_count+later['grt']>limits['max_global_route_calls']
        or shutil.disk_usage(folder.parent).free<storage):
        raise ValueError('native-state complete cohort and later work not funded')
    folder.mkdir(parents=True,exist_ok=False);p=profile('asap7');tasks=[];seen={}
    for spec in specifications(cfg):
        d=folder/'sources'/spec['id'];d.mkdir(parents=True)
        (d/'input.sv').write_text(source(spec));h=sha(d/'input.sv')
        if h in seen:raise ValueError('native-state source collision across groups')
        seen[h]=spec['split']
        write(d/'contract.json',{'version':'native-state-bank-contract-v1','spec':spec,'protocol_sha256':sha(CONFIG)})
        for i,t in enumerate(cfg['SDC_ps']):
            tasks.append({'id':spec['id']+f'-t{i}','source_group':spec['id'],'split':spec['split'],
                'rtl':str(d/'input.sv'),'rtl_sha256':h,'contract':str(d/'contract.json'),'contract_sha256':sha(d/'contract.json'),
                'features':features(spec,t),'period_ps':t,'abc_target_ps':1500,'platform':'asap7','top':'ModelBundle',
                'profile_sha256':p['profile_sha256'],'mapping_source_task':spec['id']+'-t0' if i else None})
    if dict(Counter(t['split'] for t in tasks))!={k:v['tasks'] for k,v in cfg['splits'].items()}:
        raise ValueError('native-state registered task counts differ')
    producer=[Path(__file__),CONFIG,POLICY,*sorted(ASSETS.iterdir())]
    producer += [Path(__file__).with_name(n) for n in ('model_native_state_samples.py','model_native_state_labels.py',
        'model_m2_state_samples.py','model_m2_state_collection.py','model_m2_mux_collection.py','model_m2_evaluate.py',
        'model_m2_live_cec_v3.py','model_m2_cec.py','model_m2_aig.py','model_m2_state.py',
        'backend.py','platforms.py','processes.py','budget.py','sdc.py','model_collection.py','model_samples.py')]
    producer += sorted(p for p in Path(__file__).with_name('backend').iterdir() if p.is_file())
    producer += [ROOT/name for name in proof['native_binding_sources']]
    producer += [ROOT/'regression/arithmetic_native_state_bank.py']
    hashes={}
    for path in producer:
        name=str(path.relative_to(ROOT));dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);hashes[name]=sha(path)
    legacy.exclusive(folder/'admission.json',{'version':'asap7-native-state-fitting-admission-v1','id':folder.name,
        'sources':hashes,'tasks':tasks,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),
        'parent_model_path':str(ROOT/cfg['parent_model']),'parent_model_sha256':cfg['parent_model_sha256'],
        'parent_primitives_path':str(ROOT/cfg['parent_primitives']),'parent_primitives_sha256':cfg['parent_primitives_sha256'],
        'measurement_static_identity_sha256':read(ROOT/cfg['parent_model'])['measurement_static_identity_sha256'],
        'software_proof_path':str(software_proof),'software_proof_sha256':sha(software_proof),
        'resource_plan':{'whole_cohort_tasks':tasks_count,'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,
                         'storage_reserved_bytes':storage,'later_work_reserved':later},
        'test_locked':True,'automatic_retries':0,'formal_PPA_read':False})
    write(folder/'progress.json',{'phase':'admitted','active':[],'completed':[],'waiting':[t['id'] for t in tasks if t['split']!='test'],
        'errors':[],'capacity_qualified':False,'test_locked':True})
    print(json.dumps({'status':'admitted','counts':dict(Counter(t['split'] for t in tasks)),'walltime_envelope_s':wall,
        'storage_reserved_bytes':storage,'test_locked':True}),flush=True)


def verify(folder):
    a=read(folder/'admission.json')
    cfg=read(CONFIG)
    if (a['version']!='asap7-native-state-fitting-admission-v1' or a['protocol_sha256']!=sha(CONFIG)
        or a['policy_sha256']!=sha(POLICY) or not a['test_locked']
        or sha(a['parent_model_path'])!=a['parent_model_sha256']
        or sha(a['parent_primitives_path'])!=a['parent_primitives_sha256']
        or sha(a['software_proof_path'])!=a['software_proof_sha256']):
        raise ValueError('native-state admission or parent changed')
    if (a['parent_model_sha256']!=cfg['parent_model_sha256']
        or a['parent_primitives_sha256']!=cfg['parent_primitives_sha256']
        or dict(Counter(t['split'] for t in a['tasks']))!={k:v['tasks'] for k,v in cfg['splits'].items()}):
        raise ValueError('native-state parent or source roles differ from registration')
    specs={s['id']:s for s in specifications(cfg)}
    ids=set()
    for t in a['tasks']:
        spec=specs[t['source_group']]
        if (t['id'] in ids or t['split']!=spec['split'] or t['period_ps'] not in cfg['SDC_ps']
            or t['id']!=t['source_group']+'-t'+str(cfg['SDC_ps'].index(t['period_ps']))
            or t['features']!=features(spec,t['period_ps']) or t['abc_target_ps']!=1500
            or t['platform']!='asap7' or t['top']!='ModelBundle'):
            raise ValueError('native-state task/target/features differ from registration')
        ids.add(t['id'])
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('native-state producer changed: '+name)
    return a


class NativeLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder);t=next(x for x in a['tasks'] if x['id']==self.task['id'])
        if (t!=self.task or t['split'] not in ('train','validation') or threads!=4
            or sha(t['rtl'])!=t['rtl_sha256'] or sha(t['contract'])!=t['contract_sha256']):
            raise ValueError('native-state locked/unregistered physical request')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':t['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'model_version':'asap7-native-state-successor-v1'})


def run_task(folder,t):
    from .backend import _evaluate,stage_metrics,verify_orfs_area
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .platforms import profile,verify_wire_readback,resolve_environment,validate_environment
    from .processes import run_command
    from .sdc import verify_sdc,rtl_ports
    a=verify(folder)
    if t['split']=='test':raise ValueError('native independent tests locked before validation/freeze')
    out=folder/'runs'/t['id']
    if out.exists():raise ValueError('preserve native-state attempt; no automatic retry')
    ledger=NativeLedger(folder,t);ctx={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
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
            native_state_admission_sha256=sha(folder/'admission.json'),native_state_collection_version=a['version'])
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
            for name in ('model_native_state_collection.py','model_native_state_samples.py','model_native_state_labels.py'):
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
    a=verify(folder);cfg=read(CONFIG);indexed={t['id']:t for t in a['tasks'] if t['split']!='test'}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/tid).exists() for tid in indexed):raise ValueError('preserve native-state attempts; explicit successor required')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(cfg['capacity_pilots'])<=set(completed):
                    rows=[]
                    for tid in cfg['capacity_pilots']:
                        m=read(folder/'runs'/tid/'manifest.json')
                        rows.append({'task_id':tid,'manifest_sha256':sha(folder/'runs'/tid/'manifest.json'),
                            'actual_state':m['metrics'][-1]['native_state_witness'],
                            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
                    legacy.exclusive(folder/'capacity-proof.json',{'status':'passed','runs':rows,'scope':'registered native-state fitting geometries only'})
                    capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((tid for tid in waiting if (capacity or tid in cfg['capacity_pilots']) and
                        (not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed)),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                write(folder/'progress.json',{'phase':'fitting_collecting','active':list(active.values()),'completed':completed,
                    'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':True})
                if not active:
                    if waiting and not errors:raise ValueError('native-state dependency deadlock')
                    break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    tid=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':tid,'reason':str(error)})
        write(folder/'progress.json',{'phase':'stopped_on_error' if errors else 'fitting_collection_complete','active':[],
            'completed':completed,'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':True})
        if errors:raise RuntimeError(str(errors))


def status(folder):
    a,p=read(folder/'admission.json'),read(folder/'progress.json')
    print(datetime.now().astimezone().isoformat(timespec='seconds'));print('原生状态协议后继：'+p['phase'])
    for split in ('train','validation','test'):
        counts=Counter()
        for t in a['tasks']:
            if t['split']!=split:continue
            f=folder/'runs'/t['id']/'manifest.json';m=read(f) if f.exists() else {};counts[m.get('status','not_started')]+=1
            if m.get('status')=='running':print('任务：',t['id'],'阶段：',m.get('active_stage'))
        print(f'{split}: {counts["completed"]}/{sum(counts.values())}；{dict(counts)}')
    print('容量准入：',p['capacity_qualified'],'；独立test锁定：',p['test_locked'],'；最多4任务×4线程／8GiB')
    print('错误：',p['errors']);print('只采108项拟合侧任务，采完停止；不自动拟合、独立测试或发布。')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run','verify','status'))
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--software-proof',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':
        if a.software_proof is None:p.error('prepare requires software-proof')
        prepare(folder,a.software_proof.resolve())
    elif a.action=='run':run(folder)
    elif a.action=='status':status(folder)
    else:verify(folder);print('verified native-state admission')


if __name__=='__main__':main()
