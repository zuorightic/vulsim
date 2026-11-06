"""Prospective general-state fitting collection; exact targets and tests locked."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import shutil
import tempfile
from types import SimpleNamespace

from .budget import Ledger,POLICY,usage
from .model_collection import sha,write
from .model_general_state_samples import specifications,source,features,VERSION
from .model_general_state_labels import partition,labels,render_requests

ROOT=Path(__file__).resolve().parents[2]
CONFIG=Path(__file__).with_name('configs')/'model_asap7_general_state_v1.json'
ORFS=Path('/home/zyrv/OpenROAD-flow-scripts')
SUFFIX=Path('asap7/arithmetic_probe/base')
ASSET=Path(__file__).with_name('reference_assets')/'snapshot.tcl'
PIN_TABLE=ROOT/'build/step7-reference-20261106/preflight-v4/software/liberty-pin-classes.json'


def read(path):return json.loads(Path(path).read_text())
def exclusive(path,value):
    with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def progress_write(folder,value):
    with tempfile.NamedTemporaryFile('w',dir=folder,delete=False,prefix='.general-progress-') as f:
        json.dump(value,f,indent=2);f.write('\n');name=f.name
    os.replace(name,folder/'progress.json')


def prepare(folder,proof_path):
    from .platforms import profile
    from .model_m2_evaluate import measurement_identity
    cfg=read(CONFIG);proof=read(proof_path)
    if (proof['status']!='passed' or proof['protocol_sha256']!=sha(CONFIG) or proof['source_groups']!=24
        or not proof['generic_state_geometry_checked'] or not proof['incorrect_valid_gated_external_RTL_rejected']
        or proof['independent_physical_labels_read']):raise ValueError('complete general-state software proof required')
    for name,h in proof['producer_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('general-state software producer changed')
    for name,h in proof['public_service_protocol_witnesses'].items():
        if sha(name)!=h:raise ValueError('general-state public protocol witness changed')
    for name in ('requirements','targets','parent_model'):
        if sha(ROOT/cfg[name])!=cfg[name+'_sha256']:raise ValueError('general-state frozen predecessor changed')
    env=Path(proof['environment_manifest'])
    if sha(env)!=proof['environment_manifest_sha256']:raise ValueError('general-state environment seed changed')
    parent=read(env);p=profile('asap7')
    for asset in [*parent['tools'].values(),*parent['libraries']]:
        if sha(asset['path'])!=asset['sha256']:raise ValueError('general-state tool/Liberty changed')
    current=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=cfg['later_work_reserved']
    count=sum(v['tasks'] for v in cfg['splits'].values());wall=count*cfg['resources']['per_task_walltime_envelope_s']+cfg['support_walltime_envelope_s']
    if (current['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
        or current['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
        or current['synth']+count+later['synth']>limits['max_synthesis_calls']
        or current['grt']+count+later['grt']>limits['max_global_route_calls']
        or shutil.disk_usage(folder.parent).free<count*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']):
        raise ValueError('full general-state cohort and later work not funded')
    folder.mkdir(parents=True,exist_ok=False);tasks=[]
    for s in specifications(cfg):
        d=folder/'sources'/s['id'];d.mkdir(parents=True);rtl=d/'input.sv';rtl.write_text(source(s))
        if sha(rtl)!=proof['RTL_sources'][s['id']]:raise ValueError('general-state RTL differs from preflight')
        contract=d/'contract.json';write(contract,{'version':VERSION,'spec':s,'protocol_sha256':sha(CONFIG),
            'source_role':s['split'],'formal_graph_copied':False,'all_clock_variants_same_split':True})
        for index,period in enumerate(cfg['SDC_ps']):
            tasks.append({'id':s['id']+f'-t{index}','source_group':s['id'],'split':s['split'],
                'semantic_signature':s['semantic_signature'],'platform':'asap7','top':'ModelBundle',
                'period_ps':period,'abc_target_ps':1500,'features':features(s,period),
                'rtl':str(rtl),'rtl_sha256':sha(rtl),'contract':str(contract),'contract_sha256':sha(contract),
                'profile_sha256':p['profile_sha256']})
    if Counter(t['split'] for t in tasks)!={k:v['tasks'] for k,v in cfg['splits'].items()}:
        raise ValueError('general-state task/split counts differ')
    paths=[CONFIG,POLICY,ASSET,ROOT/cfg['requirements'],ROOT/cfg['targets'],ROOT/cfg['parent_model'],
        ROOT/'regression/arithmetic_general_state.py',Path(__file__).with_name('configs')/'platforms/asap7.json']
    paths += [Path(__file__).with_name(n) for n in ('model_general_state_collection.py','model_general_state_samples.py',
        'model_general_state_labels.py','model_reference_labels.py','model_reference_labels_v2.py','model_reference_samples.py',
        'backend.py','platforms.py','processes.py','budget.py','sdc.py','model_collection.py','model_samples.py',
        'characterization.py','model_m2_mux_collection.py','model_m2_evaluate.py',
        'model_m2_live_cec_v3.py','model_m2_cec.py','model_m2_aig.py','model_m2_state.py')]
    paths += sorted(p for p in Path(__file__).with_name('backend').iterdir() if p.is_file())
    hashes={}
    for path in paths:
        name=str(path.relative_to(ROOT));dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);hashes[name]=sha(path)
    pilots=[s+f'-t{i}' for s in cfg['capacity_pilot_sources'] for i in cfg['capacity_pilot_clock_indices']]
    exclusive(folder/'admission.json',{'version':'asap7-general-state-fitting-admission-v1','id':folder.name,
        'sources':hashes,'protocol_sha256':sha(CONFIG),'policy_sha256':sha(POLICY),'tasks':tasks,
        'software_proof':str(proof_path),'software_proof_sha256':sha(proof_path),
        'environment_manifest':str(env),'environment_manifest_sha256':sha(env),
        'measurement_static_identity_sha256':measurement_identity(parent),
        'physical_tools':parent['tools'],'libraries':parent['libraries'],
        'pin_table':str(PIN_TABLE),'pin_table_sha256':sha(PIN_TABLE),'capacity_pilots':pilots,
        'resource_plan':{'whole_cohort_tasks':count,'new_synth':count,'new_grt':count,
            'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,
            'storage_bytes':count*cfg['resources']['storage_per_task_bytes'],'later_work_reserved':later},
        'test_locked':True,'automatic_retries':0,'formal_or_consumed_independent_PPA_read':False,
        'fit_test_or_publication_automatic':False,'full_D_ready':False})
    progress_write(folder,{'phase':'admitted','active':[],'completed':[],'errors':[],
        'waiting':[t['id'] for t in tasks if t['split']!='test'],'capacity_qualified':False,'test_locked':True})
    print(json.dumps({'status':'admitted','tasks':dict(Counter(t['split'] for t in tasks)),
        'capacity_pilots':pilots,'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,'independent_test_locked':True}),flush=True)


def verify(folder):
    a=read(folder/'admission.json');cfg=read(CONFIG)
    if (a['version']!='asap7-general-state-fitting-admission-v1' or a['protocol_sha256']!=sha(CONFIG)
        or a['policy_sha256']!=sha(POLICY) or not a['test_locked']
        or sha(a['software_proof'])!=a['software_proof_sha256']
        or sha(a['environment_manifest'])!=a['environment_manifest_sha256']
        or sha(a['pin_table'])!=a['pin_table_sha256']):raise ValueError('general-state admission dependencies changed')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('general-state frozen producer changed: '+name)
    specs={s['id']:s for s in specifications(cfg)};seen=set()
    for t in a['tasks']:
        s=specs[t['source_group']]
        if (t['id'] in seen or t['split']!=s['split'] or t['period_ps'] not in cfg['SDC_ps']
            or t['id']!=s['id']+'-t'+str(cfg['SDC_ps'].index(t['period_ps']))
            or t['features']!=features(s,t['period_ps']) or t['semantic_signature']!=s['semantic_signature']
            or t['abc_target_ps']!=1500 or t['platform']!='asap7' or t['top']!='ModelBundle'
            or sha(t['rtl'])!=t['rtl_sha256'] or sha(t['contract'])!=t['contract_sha256']):
            raise ValueError('general-state task/role/target/source differs')
        seen.add(t['id'])
    if Counter(t['split'] for t in a['tasks'])!={k:v['tasks'] for k,v in cfg['splits'].items()}:
        raise ValueError('general-state full task counts differ')
    return a


class GeneralLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder)
        if self.task not in a['tasks'] or self.task['split']=='test' or threads!=4:
            raise ValueError('general-state unregistered or locked physical request')
        if self.task['id'] not in a['capacity_pilots']:
            proof=read(self.folder/'capacity-proof.json')
            if (proof['status']!='passed' or proof['admission_sha256']!=sha(self.folder/'admission.json')
                or {r['id'] for r in proof['runs']}!=set(a['capacity_pilots'])):raise ValueError('general-state capacity gate missing')
            for row in proof['runs']:
                if sha(self.folder/'runs'/row['id']/'manifest.json')!=row['manifest_sha256']:
                    raise ValueError('general-state capacity source changed')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':self.task['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'model_version':'asap7-general-state-successor-v1'})


def run_task(folder,t):
    from .backend import _evaluate,stage_metrics,verify_orfs_area
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .platforms import profile,verify_wire_readback
    from .processes import run_command
    from .sdc import verify_sdc,rtl_ports
    a=verify(folder);cfg=read(CONFIG);out=folder/'runs'/t['id']
    if t['split']=='test':raise ValueError('independent general-state tests locked until a separate frozen-selection admission')
    if out.exists():raise ValueError('preserve general-state attempts; no automatic retry')
    ledger=GeneralLedger(folder,t);ctx={'target_platform':'asap7','admission_id':a['id'],'task_id':t['id']}
    env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',
        PYTHONDONTWRITEBYTECODE='1',QT_QPA_PLATFORM='offscreen',VULSIM_REFERENCE_REQUESTS=str(out/'requests.tcl'))
    with ledger.job(ctx):
        args=SimpleNamespace(out=out,platform='asap7',threads=4,stage='synth',memory_limit_mib=8192,
            period_ps=t['period_ps'],period_role='resource_trial',abc_target_ps=1500,io_delay_max_ps=None,
            budget_purpose='characterization',admission_id=a['id'],task_id=t['id'],sample_contract=None,
            admission=None,resume_synth_from=None,orfs=ORFS,rtl=Path(t['rtl']),top='ModelBundle',
            synth_timeout_s=cfg['resources']['synth_timeout_s'],route_timeout_s=cfg['resources']['grt_timeout_s'],selection_freeze=None)
        _evaluate(args,ledger);m=read(out/'manifest.json')
        if m['status']!='completed':raise RuntimeError('general-state synthesis failed: '+str(m.get('failure_reason')))
        base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        m.update(status='running',stages_requested='grt',general_state_admission_sha256=sha(folder/'admission.json'),data_role=t['split'])
        def save():write(out/'manifest.json',m)
        def execute(command,name,timeout,stage=None):
            m['active_stage']=name;r=ledger.reserve(stage,timeout,4,'general_state_characterization',command,out/name,context=ctx)
            m['active_reservation']=r['id'];save();c=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s'])
            ledger.finish(r,c);c['budget_reservation_id']=r['id'];m['commands'].append(c);save()
            if c['exit_code']:raise RuntimeError(name+' failed; timeout='+str(c['timed_out']))
        try:
            shutil.copy2(t['contract'],out/'general-state-contract.json');s=read(t['contract'])['spec']
            (out/'requests.tcl').write_text(render_requests())
            snapshot=out/'general-state-snapshot.tcl';text=(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl').read_text()
            text=text.replace('source [file join [file dirname [info script]] rc_readback.tcl]','source {'+str(ROOT/'experiments/arithmetic_dse/backend/rc_readback.tcl')+'}')
            text=text.replace('source [file join [file dirname [info script]] model_labels.tcl]','source {'+str(ASSET)+'}')
            snapshot.write_text(text)
            wrapper=out/'live-cec.py';wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request=out/'live-cec-request.json';write(request,{'libraries':m['libraries'],'admission_sha256':sha(folder/'admission.json'),'collection_plan_sha256':sha(folder/'admission.json')})
            cts=out/'flow-scripts/cts.tcl';cts.unlink();cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(),wrapper,request,out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(p):sha(p) for p in [snapshot,wrapper,request,cts,out/'requests.tcl',out/'general-state-contract.json',ASSET]})
            if measurement_identity(m)!=a['measurement_static_identity_sha256']:raise ValueError('general-state physical identity differs')
            for asset in [*m['tools'].values(),*m['libraries']]:
                if sha(asset['path'])!=asset['sha256']:raise ValueError('general-state tool/library changed')
            p=profile('asap7');cells=read(out/'liberty_cells.json')['cells'];pins=read(a['pin_table']);m['metrics']=[]
            for stage,stem in [('synth','1_synth'),('grt','5_1_grt')]:
                if stage=='grt':execute(base+['grt'],'grt',cfg['resources']['grt_timeout_s'],'grt')
                execute(base+['run','RUN_SCRIPT='+str(snapshot),'RUN_LOG_NAME_STEM=general_'+stage,
                    'VULSIM_EVAL_STAGE='+stage,'VULSIM_EVAL_DB='+stem+'.odb','VULSIM_EVAL_SDC='+stem+'.sdc'],
                    'general-'+stage+'-snapshot',cfg['resources']['snapshot_timeout_s'])
                reports=out/'reports'/SUFFIX;prefix=reports/('vulsim_'+stage)
                g=stage_metrics(reports,stage,cells,t['period_ps'],selected=p)
                ownership,instances,_=partition(prefix,pins,p,s);write(out/('general-'+stage+'-ownership.json'),ownership)
                if abs(g['cell_area_um2']-ownership['total_area_um2'])>1e-6:raise ValueError('general-state exhaustive area differs')
                g.update(general_state_paths=labels(prefix,t['period_ps'],g['raw_report_units']['time']['to_ps'],pins,instances),
                    general_state_owner_area_um2=ownership['owner_area_um2'],general_state_owner_FF_bits=ownership['owner_FF_bits'],
                    general_state_ownership_sha256=sha(out/('general-'+stage+'-ownership.json')))
                rc=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),p)
                if rc is not None:g['wire_RC_readback']=rc
                m['sdc_contracts'][stage]=verify_sdc((out/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,t['period_ps'],rtl_ports((out/'input.sv').read_text(),'ModelBundle'))
                native=read(out/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
                g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native)
                if not g['timing_coverage_complete']:raise ValueError('general-state unconstrained paths')
                m['metrics'].append(g);save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',out/'results'/SUFFIX/'4_before_rsz_lec.v',out/'results'/SUFFIX/'4_after_rsz_lec.v')
            m['status']='completed';write(out/'metrics.json',m['metrics'])
        except Exception as error:m.update(status='failed',failure_stage=m.get('active_stage','general_preflight'),failure_reason=str(error))
        finally:
            m['finished_at']=datetime.now(timezone.utc).isoformat()
            m['evidence_sha256']={str(path.relative_to(out)):sha(path) for name in ('logs','reports','results') for path in (out/name).rglob('*') if path.is_file()};save()
        print(json.dumps({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')}),flush=True)
        if m['status']!='completed':raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def run(folder):
    a=verify(folder);indexed={t['id']:t for t in a['tasks'] if t['split']!='test'}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/key).exists() for key in indexed):raise ValueError('preserve attempts; explicit successor required')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_pilots'])<=set(completed):
                    rows=[]
                    for key in a['capacity_pilots']:
                        path=folder/'runs'/key/'manifest.json';m=read(path)
                        rows.append({'id':key,'manifest_sha256':sha(path),
                            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
                    exclusive(folder/'capacity-proof.json',{'status':'passed','admission_sha256':sha(folder/'admission.json'),
                        'scope':'explicit24 general-state sources and nine clocks only; no arithmetic stage qualification','runs':rows});capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((key for key in waiting if capacity or key in a['capacity_pilots']),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                progress_write(folder,{'phase':'fitting_collecting','active':list(active.values()),'completed':completed,
                    'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':True})
                if not active:break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    key=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':key,'reason':str(error)})
        progress_write(folder,{'phase':'stopped_on_error' if errors else 'fitting_collection_complete','active':[],
            'completed':completed,'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':True})
        if errors:raise RuntimeError(str(errors))


def status(folder):
    a=read(folder/'admission.json');progress=read(folder/'progress.json')
    print(datetime.now().astimezone().isoformat(timespec='seconds'));print('一般状态采集：'+progress['phase'])
    for split in ('train','validation','test'):
        counts=Counter()
        for t in a['tasks']:
            if t['split']!=split:continue
            path=folder/'runs'/t['id']/'manifest.json';m=read(path) if path.exists() else {};counts[m.get('status','not_started')]+=1
            if m.get('status')=='running':print('任务：',t['id'],'阶段：',m.get('active_stage'))
        print(split+': '+str(dict(counts)))
    print('最多4任务×4线程／8GiB；独立54项锁定；采完停止，不自动拟合／测试／发布。')
    print('容量准入：',progress['capacity_qualified'],'错误：',progress['errors'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify','run','status'))
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--proof',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':prepare(folder,a.proof.resolve())
    elif a.action=='run':run(folder)
    elif a.action=='status':status(folder)
    else:verify(folder);print('general-state admission verified')
