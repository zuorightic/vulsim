"""Separate frozen-selection admission and one-time general-state test evaluation."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
import fcntl
import inspect
import json
from pathlib import Path
import shutil

from .budget import Ledger,POLICY,usage
from .model_collection import sha,write
from . import model_general_state_collection as collection
from . import model_general_state_collection_v2 as successor
from .model_general_state_fit import CONFIG,EXECUTION,OWNERS,verify_fit,reparse,owner_features,owner_rows
from .model_general_state_samples_v2 import specifications,source
from .model_reference_audit import ReferenceAudit
from .model_m2_state_fit import quality

ROOT=collection.ROOT


def read(path):return json.loads(Path(path).read_text())


def prepare(folder,parent,fit):
    if folder.exists():raise ValueError('preserve independent state attempts')
    a=successor.verify(parent);f=verify_fit(fit);cfg=read(CONFIG);candidate=read(fit/'candidate.json')
    if (f['status']!='frozen_awaiting_independent_test' or candidate['quality_status']!='awaiting_independent_test'
        or f['admission_sha256']!=sha(parent/'admission.json') or f['required_independent_tasks']!=54):
        raise ValueError('validation-ready frozen general-state candidate required')
    dataset=read(f['dataset_path']);tasks=[dict(t) for t in a['tasks'] if t['split']=='test']
    if (len(tasks)!=54 or dataset['test_labels_read'] or not dataset['test_collection_locked']
        or dataset['audit']['physical_runs']!=162 or any((parent/'runs'/t['id']).exists() for t in tasks)):
        raise ValueError('new independent role/source separation not established')
    current=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];later=cfg['later_work_reserved']
    wall=len(tasks)*cfg['resources']['per_task_walltime_envelope_s']+3600
    if (current['walltime_s']+wall+later['walltime_s']>limits['max_global_walltime_h']*3600
        or current['CPU_time_s']+4*wall+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600
        or current['synth']+len(tasks)+later['synth']>limits['max_synthesis_calls']
        or current['grt']+len(tasks)+later['grt']>limits['max_global_route_calls']
        or shutil.disk_usage(folder.parent).free<len(tasks)*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']):
        raise ValueError('independent state and later work not funded')
    folder.mkdir(parents=True);sources={}
    paths={ROOT/name for name in a['sources']}|{ROOT/name for name in f['sources']}
    paths |= {Path(__file__),Path(__file__).with_name('model_reference_audit.py'),Path(__file__).with_name('model_m2_state_replay.py')}
    for path in sorted(paths):
        name=str(path.relative_to(ROOT));dest=folder/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);sources[name]=sha(path)
    pilots=[cfg['independent_capacity_pilot_source']+f'-t{i}' for i in cfg['capacity_pilot_clock_indices']]
    admission={'version':'asap7-general-state-independent-admission-v1','id':folder.name,'sources':sources,'tasks':tasks,
        'protocol_sha256':sha(CONFIG),'execution_sha256':sha(EXECUTION),'policy_sha256':sha(POLICY),
        'fitting_admission':str(parent/'admission.json'),'fitting_admission_sha256':sha(parent/'admission.json'),
        'selection_freeze':str(fit/'selection-freeze.json'),'selection_freeze_sha256':sha(fit/'selection-freeze.json'),
        'candidate':str(fit/'candidate.json'),'candidate_sha256':sha(fit/'candidate.json'),
        'dataset':f['dataset_path'],'dataset_sha256':f['dataset_sha256'],
        'measurement_static_identity_sha256':a['measurement_static_identity_sha256'],
        'pin_table':a['pin_table'],'pin_table_sha256':a['pin_table_sha256'],'capacity_pilots':pilots,
        'evaluation':{'area_gate':'original median20%/P95 50% separately per owned state class and stage',
            'exact_clock_area_breakdown':'report, not a new post-test gate',
            'boundary_gate':'each exact clock/non-birth path class independent H+delay maximum <= frozen overhead',
            'reserve_adaptation':False,'deployable_stage_if_passed':'grt','test_labels_for_fitting_or_selection':False},
        'resource_plan':{'tasks':54,'synth':54,'grt':54,'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,
            'storage_bytes':len(tasks)*cfg['resources']['storage_per_task_bytes'],'later_work_reserved':later},
        'automatic_retries':0,'automatic_fit_evaluate_or_publish':False,'full_D_ready':False}
    write(folder/'admission.json',admission)
    collection.progress_write(folder,{'phase':'independent_admitted','active':[],'completed':[],'waiting':[t['id'] for t in tasks],
        'errors':[],'capacity_qualified':False,'test_locked':False})
    verify(folder);print(json.dumps({'status':'independent_admitted','tasks':54,'capacity_pilots':pilots,
        'walltime_envelope_s':wall,'CPU_envelope_s':4*wall,'automatic_evaluation':False}),flush=True)


def verify(folder):
    a=read(folder/'admission.json')
    if (a['version']!='asap7-general-state-independent-admission-v1' or sha(CONFIG)!=a['protocol_sha256']
        or sha(EXECUTION)!=a['execution_sha256'] or sha(POLICY)!=a['policy_sha256']
        or sha(a['fitting_admission'])!=a['fitting_admission_sha256']
        or sha(a['selection_freeze'])!=a['selection_freeze_sha256'] or sha(a['candidate'])!=a['candidate_sha256']
        or sha(a['dataset'])!=a['dataset_sha256'] or sha(a['pin_table'])!=a['pin_table_sha256']):
        raise ValueError('general-state independent frozen identity changed')
    f=verify_fit(Path(a['selection_freeze']).parent)
    if f['status']!='frozen_awaiting_independent_test' or f['test_observed']:raise ValueError('independent state selection not frozen')
    expected=[t for t in read(a['fitting_admission'])['tasks'] if t['split']=='test']
    if a['tasks']!=expected or len(a['tasks'])!=54:raise ValueError('independent task/source roles changed')
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('independent producer changed: '+name)
    for t in a['tasks']:
        if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['contract'])!=t['contract_sha256']:raise ValueError('independent RTL source changed')
    return a


class IndependentLedger(Ledger):
    def __init__(self,folder,task):super().__init__();self.folder=folder;self.task=task
    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a=verify(self.folder)
        if self.task not in a['tasks'] or self.task['split']!='test' or threads!=4:
            raise ValueError('unregistered or wrong-role general-state independent command')
        if self.task['id'] not in a['capacity_pilots']:
            proof=read(self.folder/'capacity-proof.json')
            if (proof['status']!='passed' or proof['admission_sha256']!=sha(self.folder/'admission.json')
                or {r['id'] for r in proof['runs']}!=set(a['capacity_pilots'])):raise ValueError('independent capacity gate missing')
            for r in proof['runs']:
                if sha(self.folder/'runs'/r['id']/'manifest.json')!=r['manifest_sha256']:raise ValueError('independent capacity pilot changed')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context={**(context or {}),
            'target_platform':'asap7','admission_id':a['id'],'task_id':self.task['id'],
            'admission_sha256':sha(self.folder/'admission.json'),'selection_freeze_sha256':a['selection_freeze_sha256'],
            'model_version':'asap7-general-state-independent-v1'})


def run_task(folder,t):
    text=inspect.getsource(collection.run_task)
    old="if t['split']=='test':raise ValueError('independent general-state tests locked until a separate frozen-selection admission')"
    if text.count(old)!=1:raise ValueError('unsupported independent role gate')
    text=text.replace(old,"if t['split']!='test':raise ValueError('independent source role required')")
    old='from .sdc import verify_sdc,rtl_ports'
    if text.count(old)!=1:raise ValueError('unsupported independent SDC reader point')
    text=text.replace(old,'from .sdc_storage_v3 import verify_sdc\n    from .sdc import rtl_ports')
    old="data_role=t['split'])"
    if text.count(old)!=1:raise ValueError('unsupported independent manifest selection binding')
    text=text.replace(old,"data_role=t['split'],selection_freeze_sha256=a['selection_freeze_sha256'])")
    namespace=dict(collection.run_task.__globals__);namespace.update(CONFIG=CONFIG,verify=verify,GeneralLedger=IndependentLedger)
    exec(compile(text,str(Path(__file__).resolve())+'::independent_worker','exec'),namespace)
    return namespace['run_task'](folder,t)


def run(folder):
    from . import backend
    from .sdc_storage_v3 import verify_sdc,VERSION
    verify(folder);backend.verify_sdc=verify_sdc;backend.SDC_CONTRACT_VERSION=VERSION
    a=read(folder/'admission.json');indexed={t['id']:t for t in a['tasks']}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/key).exists() for key in indexed):raise ValueError('preserve independent attempts; explicit continuation required')
        waiting=list(indexed);active={};completed=[];errors=[];capacity=False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_pilots'])<=set(completed):
                    rows=[]
                    for key in a['capacity_pilots']:
                        path=folder/'runs'/key/'manifest.json';m=read(path)
                        rows.append({'id':key,'manifest_sha256':sha(path),
                            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
                    collection.exclusive(folder/'capacity-proof.json',{'status':'passed','admission_sha256':sha(folder/'admission.json'),
                        'scope':'registered six independent S sources and nine exact periods only','runs':rows});capacity=True
                while waiting and len(active)<4 and not errors:
                    ready=next((key for key in waiting if capacity or key in a['capacity_pilots']),None)
                    if ready is None:break
                    waiting.remove(ready);active[pool.submit(run_task,folder,indexed[ready])]=ready
                collection.progress_write(folder,{'phase':'independent_collecting','active':list(active.values()),'completed':completed,
                    'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
                if not active:break
                done,_=wait(active,timeout=1,return_when=FIRST_COMPLETED)
                for future in done:
                    key=active.pop(future)
                    try:completed.append(future.result())
                    except Exception as error:errors.append({'task_id':key,'reason':str(error)})
        collection.progress_write(folder,{'phase':'stopped_on_error' if errors else 'independent_collection_complete','active':[],
            'completed':completed,'waiting':waiting,'errors':errors,'capacity_qualified':capacity,'test_locked':False})
        if errors:raise RuntimeError(str(errors))


def extract(folder,out):
    if out.exists():raise ValueError('preserve general-state independent extraction')
    a=verify(folder);p=read(folder/'progress.json');cfg=read(CONFIG)
    if (p['phase']!='independent_collection_complete' or p['active'] or p['waiting'] or p['errors']
        or set(p['completed'])!={t['id'] for t in a['tasks']}):raise ValueError('complete independent S collection required')
    specs={s['id']:s for s in specifications(cfg)};audit=ReferenceAudit(read(Ledger().path)['entries']);rows=[];runs=[]
    pins=read(a['pin_table'])
    for t in a['tasks']:
        d=folder/'runs'/t['id'];s=specs[t['source_group']]
        if t['split']!='test' or source(s)!=(d/'input.sv').read_text():raise ValueError('independent source/role mismatch')
        audit.ancestry(d);m,metrics,identity=reparse(d,t,pins)
        if (identity!=a['measurement_static_identity_sha256'] or m['selection_freeze_sha256']!=a['selection_freeze_sha256']
            or m['general_state_admission_sha256']!=sha(folder/'admission.json')):raise ValueError('independent selection/physical identity differs')
        for g in metrics:
            rows.append({'id':t['id']+'/'+g['stage'],'task_id':t['id'],'source_group':t['source_group'],'split':'test',
                'stage':g['stage'],'period_ps':t['period_ps'],'owner_features':{o:owner_features(s,t['period_ps'],o) for o in OWNERS},
                'owner_area_um2':g['general_state_owner_area_um2'],'owner_FF_bits':g['general_state_owner_FF_bits'],
                'boundary_paths':g['general_state_paths'],'whole_setup_slack_ps':g['setup_worst_slack_ps'],
                'whole_hold_slack_ps':g['hold_worst_slack_ps'],'source_sha256':t['rtl_sha256'],'manifest_sha256':sha(d/'manifest.json')})
        runs.append({'task_id':t['id'],'directory':str(d),'manifest_sha256':sha(d/'manifest.json')})
    if len(rows)!=108 or len({r['source_group'] for r in rows})!=6:raise ValueError('independent S full row/source count differs')
    write(out,{'version':'asap7-general-state-independent-dataset-v1','admission_path':str(folder/'admission.json'),
        'admission_sha256':sha(folder/'admission.json'),'selection_freeze_sha256':a['selection_freeze_sha256'],
        'candidate_sha256':a['candidate_sha256'],'rows':rows,'runs':runs,'audit':{'status':'passed','physical_runs':54,
            'stage_rows':108,'path_labels':972,'paid_leaf_commands':len(audit.commands),'paid_leaf_ids':sorted(audit.commands),
            'raw_file_hashes_checked':len(audit.hashed),'PPA_calls':0}})
    print(json.dumps({'status':'passed','physical_runs':54,'stage_rows':108,'path_labels':972,'PPA_calls':0}),flush=True)


def verdict(candidate,dataset):
    cfg=read(CONFIG);stages={}
    for stage in ('synth','grt'):
        rows=[r for r in dataset['rows'] if r['stage']==stage];frozen=candidate['stages'][stage]
        areas={o:quality(frozen['area_models'][o],owner_rows(rows,o),cfg) for o in OWNERS};bounds=[]
        for period in cfg['SDC_ps']:
            for name,b in frozen['boundary_model']['by_exact_SDC'][str(period)].items():
                paths=[p|{'row_id':r['id']} for r in rows if r['period_ps']==period for p in r['boundary_paths'] if p['id']==name]
                worst=max(paths,key=lambda p:(p['H_ps']+p['delay_ps'],p['row_id']))
                required=worst['H_ps']+worst['delay_ps'];margin=b['overhead_ps']-required
                bounds.append({'period_ps':period,'path_class':name,'required_ps':required,'frozen_overhead_ps':b['overhead_ps'],
                    'margin_ps':margin,'covered':margin>=-1e-6,'witness':worst})
        passed=all(q['status']=='passed' for q in areas.values()) and all(b['covered'] for b in bounds)
        stages[stage]={'status':'passed' if passed else 'failed','owner_area_quality':areas,'boundary_coverage':bounds,
            'minimum_boundary_margin_ps':min(b['margin_ps'] for b in bounds)}
    return {'version':'asap7-general-state-independent-verdict-v1','status':stages['grt']['status'],'stages':stages,
        'parameters_domain_or_reserve_changed':False,'test_labels_consumed':True,
        'test_labels_permanently_excluded_from_future_fitting':True,'eligible_deployable_stages':['grt'] if stages['grt']['status']=='passed' else [],
        'production_price_binding_qualified':False,'full_D_ready':False,'PPA_calls':0}


def evaluate(folder,dataset,out):
    a=verify(folder);d=read(dataset)
    if (d['audit']['status']!='passed' or d['admission_sha256']!=sha(folder/'admission.json')
        or d['selection_freeze_sha256']!=a['selection_freeze_sha256'] or d['candidate_sha256']!=a['candidate_sha256']
        or len(d['rows'])!=108 or any(r['split']!='test' for r in d['rows'])):raise ValueError('audited frozen independent S dataset required')
    if out.exists():raise ValueError('preserve one-time S independent verdict')
    marker=folder/'test-consumed.json'
    with (folder/'evaluation.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if marker.exists():raise ValueError('independent S test already consumed; verify existing result without reselecting')
        out.mkdir(parents=True);collection.exclusive(marker,{'dataset_sha256':sha(dataset),
            'selection_freeze_sha256':a['selection_freeze_sha256'],'candidate_sha256':a['candidate_sha256'],
            'out':str(out),'parameters_or_margins_may_change':False})
        result=verdict(read(a['candidate']),d);write(out/'verdict.json',result)
        write(out/'identity.json',{'admission_sha256':sha(folder/'admission.json'),'dataset_path':str(dataset),
            'dataset_sha256':sha(dataset),'candidate_sha256':a['candidate_sha256'],'verdict_sha256':sha(out/'verdict.json')})
    print(json.dumps({'status':result['status'],'eligible_deployable_stages':result['eligible_deployable_stages'],
        'test_consumed':True,'parameters_changed':False,'PPA_calls':0}),flush=True)


def status(folder):
    a=read(folder/'admission.json');p=read(folder/'progress.json');counts=Counter()
    print(datetime.now().astimezone().isoformat(timespec='seconds'));print('一般状态独立测试：'+p['phase'])
    for t in a['tasks']:
        path=folder/'runs'/t['id']/'manifest.json';m=read(path) if path.exists() else {};counts[m.get('status','not_started')]+=1
        if m.get('status')=='running':print('任务：',t['id'],'阶段：',m.get('active_stage'))
    print('完成'+str(counts['completed'])+'/54；'+str(dict(counts))+'；容量准入：'+str(p['capacity_qualified']))
    print('最多4任务×4线程／8GiB；参数／域／裕量已冻结；采完停止，不自动评价／拟合／发布。');print('错误：',p['errors'])


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify','run','status','extract','evaluate'))
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--fit',type=Path)
    p.add_argument('--out',type=Path);p.add_argument('--dataset',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':prepare(folder,a.parent.resolve(),a.fit.resolve())
    elif a.action=='verify':verify(folder);print('frozen general-state independent admission verified')
    elif a.action=='run':run(folder)
    elif a.action=='status':status(folder)
    elif a.action=='extract':extract(folder,a.out.resolve())
    else:evaluate(folder,a.dataset.resolve(),a.out.resolve())
