"""Raw S replay and prospective per-owner NNLS/clock-boundary selection."""
import argparse
from collections import Counter
from contextlib import redirect_stdout
from importlib.metadata import version as package_version
import io
import json
import os
from pathlib import Path
import shutil
import sys

from .budget import Ledger,cpu_seconds
from .model_collection import sha,write
from .model_general_state_collection import ROOT,SUFFIX,read
from .model_general_state_collection_v2 import CONFIG,verify as verify_collection
from .model_general_state_samples_v2 import specifications,source,features
from .model_general_state_labels import labels,partition
from .model_reference_labels import liberty
from .model_reference_audit import ReferenceAudit
from .model_m2_state_fit import nnls,predict,quality
from .model_training import metric

EXECUTION=Path(__file__).with_name('configs')/'model_asap7_general_state_fit_v1.json'
OWNERS=('input_service','native_state','external_state')


def owner_features(s,period,owner):
    f=features(s,period)
    if owner=='input_service':
        bits,signals,valid,ones=f['input_data_bits'],f['input_signals'],1,f['input_reset_one_bits']
        enables=1 if s['service_mode']==1 else len(s['roots'])+int(s['service_mode']!=2)
    elif owner=='native_state':
        bits,signals,valid,ones=f['native_data_bits'],f['native_data_signals'],s['depth'],f['native_reset_one_bits']
        enables=len({x['stage'] for x in s['slots']})
    elif owner=='external_state':
        bits,signals,valid,ones=f['external_data_bits'],f['external_data_signals'],1,f['external_reset_one_bits'];enables=0
    else:raise ValueError('unknown general-state area owner')
    return dict(state_bits=bits+valid,state_signals=signals+valid,data_bits=bits,data_signals=signals,
        valid_bits=valid,enable_domains=enables,reset_one_bits=ones,sdc_period_ps=period)


def reparse(directory,task,pins):
    from .backend import stage_metrics,verify_orfs_area
    from .model_m2_evaluate import measurement_identity
    from .model_m2_live_cec_v3 import verify_proof
    from .platforms import profile,verify_wire_readback
    from .sdc import rtl_ports
    from .sdc_storage_v3 import verify_sdc
    m=read(directory/'manifest.json');p=profile('asap7');cells=read(directory/'liberty_cells.json')['cells']
    s=read(directory/'general-state-contract.json')['spec']
    if (m['status']!='completed' or m['task_id']!=task['id'] or m['data_role']!=task['split']
        or m['threads_per_tool']!=4 or m['memory_limit_MiB']!=8192
        or m['period_ps']!=task['period_ps'] or m['abc_target_ps']!=1500
        or sha(directory/'input.sv')!=task['rtl_sha256'] or sha(directory/'general-state-contract.json')!=task['contract_sha256']
        or [g['stage'] for g in m['metrics']]!=['synth','grt']):raise ValueError('general-state source/role/context differs')
    result=[]
    for stage,stem in [('synth','1_synth'),('grt','5_1_grt')]:
        reports=directory/'reports'/SUFFIX;prefix=reports/('vulsim_'+stage)
        g=stage_metrics(reports,stage,cells,task['period_ps'],selected=p)
        ownership,instances,_=partition(prefix,pins,p,s);owner_path=directory/('general-'+stage+'-ownership.json')
        if ownership!=read(owner_path) or abs(g['cell_area_um2']-ownership['total_area_um2'])>1e-6:
            raise ValueError('general-state unique ownership does not reproduce')
        g.update(general_state_paths=labels(prefix,task['period_ps'],g['raw_report_units']['time']['to_ps'],pins,instances),
            general_state_owner_area_um2=ownership['owner_area_um2'],general_state_owner_FF_bits=ownership['owner_FF_bits'],
            general_state_ownership_sha256=sha(owner_path))
        rc=verify_wire_readback(Path(str(prefix)+'_layer_rc.tsv'),p)
        if rc is not None:g['wire_RC_readback']=rc
        actual=verify_sdc((directory/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,task['period_ps'],rtl_ports((directory/'input.sv').read_text(),'ModelBundle'))
        if actual!=m['sdc_contracts'][stage]:raise ValueError('general-state actual SDC differs')
        native=read(directory/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
        g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native)
        old=next(v for v in m['metrics'] if v['stage']==stage)
        for key,value in g.items():
            if key!='raw_reports_prefix' and old.get(key)!=value:raise ValueError('general-state raw replay differs: '+task['id']+'/'+stage+'/'+key)
        if not g['timing_coverage_complete']:raise ValueError('general-state timing coverage incomplete')
        result.append(g)
    if read(directory/'metrics.json')!=m['metrics']:raise ValueError('general-state metric sidecar differs')
    with redirect_stdout(io.StringIO()):
        verify_proof(directory/'logs'/SUFFIX/'structural_cec/proof.json',directory/'results'/SUFFIX/'4_before_rsz_lec.v',directory/'results'/SUFFIX/'4_after_rsz_lec.v')
    return m,result,measurement_identity(m)


def failed_predecessors(a,audit):
    original=Path(a['predecessor_admission']).parent;result=[]
    for key,h in a['predecessor_runs'].items():
        d=original/'runs'/key;m=read(d/'manifest.json')
        if sha(d/'manifest.json')!=h or m['status']!='failed':raise ValueError('general-state failed probe changed')
        commands=[]
        for c in m['commands']:
            e=audit.entries[c['budget_reservation_id']]
            if (e['status']!=('failed' if c['exit_code'] else 'completed') or e['command']!=c['command']
                or e.get('admission_sha256')!=a['predecessor_admission_sha256']
                or e['task_id']!=key or c['cleanup']['remaining_live_pids']
                or abs(e['CPU_time_s']-cpu_seconds(c['gnu_time']))>1e-8):raise ValueError('failed probe fee ancestry differs')
            commands.append(e['id'])
        for name,value in m.get('evidence_sha256',{}).items():
            if audit.digest(d/name)!=value:raise ValueError('failed probe raw artifact changed')
        result.append({'task_id':key,'manifest_sha256':h,'paid_leaf_ids':commands,'numeric_labels_inherited':False})
    return result


def extract(folder,out):
    if out.exists():raise ValueError('preserve previous general-state extraction')
    a=verify_collection(folder);cfg=read(CONFIG);p=read(folder/'progress.json')
    ids={t['id'] for t in a['tasks'] if t['split']!='test'}
    if (p['phase']!='fitting_collection_complete' or p['active'] or p['waiting'] or p['errors']
        or set(p['completed'])!=ids or not p['test_locked']):raise ValueError('complete fitting collection and locked test required')
    audit=ReferenceAudit(read(Ledger().path)['entries']);specs={s['id']:s for s in specifications(cfg)}
    first=read(folder/'runs'/next(iter(a['capacity_pilots']))/'manifest.json')
    cells=read(folder/'runs'/next(iter(a['capacity_pilots']))/'liberty_cells.json')['cells']
    pins=read(a['pin_table'])
    if liberty(first['libraries'],cells)!=pins:raise ValueError('actual Liberty pin/function/FF table differs')
    rows=[];runs=[];groups={}
    for t in a['tasks']:
        d=folder/'runs'/t['id']
        if t['split']=='test':
            if d.exists():raise ValueError('general-state independent test observed before freeze')
            continue
        s=specs[t['source_group']];contract=read(d/'general-state-contract.json')
        if source(s)!=(d/'input.sv').read_text() or contract['spec']!=s or t['features']!=features(s,t['period_ps']):
            raise ValueError('general-state source/semantic features differ')
        if groups.setdefault(s['semantic_signature'],t['split'])!=t['split']:raise ValueError('semantic source crossed splits')
        audit.ancestry(d);m,metrics,identity=reparse(d,t,pins)
        if identity!=a['measurement_static_identity_sha256'] or m['general_state_admission_sha256']!=sha(folder/'admission.json'):
            raise ValueError('general-state measurement/admission identity differs')
        for g in metrics:
            owners=g['general_state_owner_area_um2']
            if any(owners.get(owner,0)<=0 for owner in OWNERS):raise ValueError('missing positive state owner area')
            rows.append({'id':t['id']+'/'+g['stage'],'task_id':t['id'],'source_group':t['source_group'],
                'source_semantic_signature':s['semantic_signature'],'split':t['split'],'stage':g['stage'],'period_ps':t['period_ps'],
                'owner_features':{owner:owner_features(s,t['period_ps'],owner) for owner in OWNERS},
                'owner_area_um2':owners,'owner_FF_bits':g['general_state_owner_FF_bits'],
                'boundary_paths':g['general_state_paths'],'whole_setup_slack_ps':g['setup_worst_slack_ps'],
                'whole_hold_slack_ps':g['hold_worst_slack_ps'],'source_sha256':t['rtl_sha256'],'manifest_sha256':sha(d/'manifest.json')})
        runs.append({'task_id':t['id'],'directory':str(d),'manifest_sha256':sha(d/'manifest.json'),
            'CTS_proof_sha256':sha(d/'logs'/SUFFIX/'structural_cec/proof.json')})
    if len(rows)!=324 or Counter(r['split'] for r in rows)!={'train':216,'validation':108}:
        raise ValueError('general-state full fitting row counts differ')
    failures=failed_predecessors(a,audit)
    result={'version':'asap7-general-state-fitting-dataset-v1','admission_path':str(folder/'admission.json'),
        'admission_sha256':sha(folder/'admission.json'),'protocol_sha256':sha(CONFIG),
        'measurement_static_identity_sha256':a['measurement_static_identity_sha256'],
        'test_labels_read':False,'test_collection_locked':True,'rows':sorted(rows,key=lambda r:r['id']),'runs':runs,
        'retained_failed_predecessors':failures,'audit':{'status':'passed','source_groups':len(groups),'physical_runs':162,
            'stage_rows':324,'path_labels':sum(len(r['boundary_paths']) for r in rows),'paid_leaf_commands':len(audit.commands),
            'paid_leaf_ids':sorted(audit.commands),'raw_file_hashes_checked':len(audit.hashed),
            'raw_manifests':{str(k):v for k,v in audit.directories.items()},'PPA_calls':0}}
    write(out,result);print(json.dumps({k:v for k,v in result['audit'].items() if k not in ('paid_leaf_ids','raw_manifests')}),flush=True)


def owner_rows(rows,owner):
    return [{'id':r['id']+'/'+owner,'period_ps':r['period_ps'],'features':r['owner_features'][owner],
             'state_area_um2':r['owner_area_um2'][owner]} for r in rows]


def boundary(rows,cfg):
    result={};reserve=cfg['boundary']['engineering_reserve_ps']
    for period in cfg['SDC_ps']:
        classes={}
        for name in cfg['timing_labels']:
            if name=='birth_data':continue
            points=[p|{'row_id':r['id']} for r in rows if r['period_ps']==period for p in r['boundary_paths'] if p['id']==name]
            if len(points)!=18:raise ValueError('general-state boundary context incomplete')
            h=max(points,key=lambda p:(p['H_ps'],p['row_id']));d=max(points,key=lambda p:(p['delay_ps'],p['row_id']))
            classes[name]={'kind':h['kind'],'H_max_ps':max(0.,h['H_ps']),'delay_max_ps':d['delay_ps'],
                'overhead_ps':max(0.,h['H_ps'])+d['delay_ps']+reserve,'reserve_ps':reserve,
                'H_witness':h,'delay_witness':d,'input_IO_subtracted_once':h['kind']=='port'}
        result[str(period)]=classes
    return {'kind':'exact_SDC_path_class_boundary','by_exact_SDC':result,'birth_data_diagnostic_only':True,
        'arbitrary_joint_arithmetic_boundary_qualified':False}


def fit(dataset,out):
    cfg,d,execution=read(CONFIG),read(dataset),read(EXECUTION)
    if (d['version']!='asap7-general-state-fitting-dataset-v1' or d['protocol_sha256']!=sha(CONFIG)
        or execution['collection_protocol_sha256']!=sha(CONFIG) or d['audit']['status']!='passed'
        or d['test_labels_read'] or not d['test_collection_locked'] or any(r['split'] not in ('train','validation') for r in d['rows'])):
        raise ValueError('audited general-state fitting-only dataset required')
    a=verify_collection(Path(d['admission_path']).parent)
    if sha(d['admission_path'])!=d['admission_sha256']:raise ValueError('general-state fit admission changed')
    out.mkdir(parents=True,exist_ok=False);stages={};reports={}
    for stage in ('synth','grt'):
        rows=[r for r in d['rows'] if r['stage']==stage];train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
        if len(train)!=108 or len(val)!=54:raise ValueError('complete general-state stage fitting data required')
        candidates=[]
        for name in execution['candidate_order']:
            models={};qualities={};clock_breakdown={}
            for owner in OWNERS:
                tr,vr=owner_rows(train,owner),owner_rows(val,owner)
                names=execution['bits_signals_features'] if name=='per_owner_NNLS_bits_signals' else execution['typed_features']
                if name=='per_owner_exact_SDC_NNLS_typed_state':
                    model={'kind':'exact_SDC_nonnegative_linear','slices':{str(t):nnls([r for r in tr if r['period_ps']==t],names) for t in cfg['SDC_ps']}}
                else:model=nnls(tr,names)
                models[owner]=model;qualities[owner]=quality(model,vr,cfg)
                clock_breakdown[owner]={str(t):quality(model,[r for r in vr if r['period_ps']==t],cfg) for t in cfg['SDC_ps']}
            total_actual=[sum(r['owner_area_um2'][o] for o in OWNERS) for r in val]
            total_predicted=[sum(predict(models[o],owner_rows([r],o)[0]) for o in OWNERS) for r in val]
            abs_sum=sum(sum(abs(predict(models[o],owner_rows([r],o)[0])-r['owner_area_um2'][o]) for o in OWNERS) for r in val)
            candidates.append({'name':name,'models':models,'validation':qualities,'by_exact_SDC':clock_breakdown,
                'status':'passed' if all(q['status']=='passed' for q in qualities.values()) else 'failed',
                'normalized_MAE':abs_sum/sum(total_actual),'total_owned_area':metric(total_actual,total_predicted,1e-4),
                'serialized_bytes':len(json.dumps(models,sort_keys=True,separators=(',',':')).encode())})
        best=min(candidates,key=lambda c:(c['status']!='passed',c['normalized_MAE'],c['serialized_bytes'],c['name']))
        stages[stage]={'quality_status':'awaiting_independent_test' if best['status']=='passed' else 'failed_validation',
            'algorithm':best['name'],'area_models':best['models'],'boundary_model':boundary(rows,cfg)}
        reports[stage]={'selected_algorithm':best['name'],'selected_validation':best['validation'],
            'selected_total_owned_area':best['total_owned_area'],'status':best['status'],'candidates':candidates}
    baseline=read(ROOT/cfg['parent_model'])
    if sha(ROOT/cfg['parent_model'])!=cfg['parent_model_sha256']:raise ValueError('immutable native baseline changed')
    old=baseline['stages']['grt']['area_model'];diagnostic=[]
    for r in d['rows']:
        if r['stage']!='grt':continue
        f={k:sum(r['owner_features'][o][k] for o in OWNERS) for k in ('state_bits','state_signals')}
        actual=sum(v for o,v in r['owner_area_um2'].items() if o not in ('source_adapter','observer','excluded_filler'))
        diagnostic.append({'id':r['id'],'actual_standalone_bank_area_um2':actual,
            'immutable_total_baseline_um2':predict(old,{'period_ps':r['period_ps'],'features':f})})
    ready=stages['grt']['quality_status']=='awaiting_independent_test'
    candidate={'version':'arithmetic-general-state-candidate-v1','quality_status':'awaiting_independent_test' if ready else 'failed_validation',
        'target_platform':'asap7','platform_profile_sha256':a['tasks'][0]['profile_sha256'],'ABC_ps':1500,'exact_SDC_ps':cfg['SDC_ps'],'IO':'0.2T',
        'owners':list(OWNERS),'stages':stages,'execution_definition':execution,'dataset_sha256':sha(dataset),
        'protocol_sha256':sha(CONFIG),'execution_sha256':sha(EXECUTION),'parent_model_sha256':cfg['parent_model_sha256'],
        'measurement_static_identity_sha256':d['measurement_static_identity_sha256'],
        'domain':{k:cfg[k] for k in ('word_widths','max_variable_word_bits','max_parallel_words','max_input_data_bits',
            'max_native_data_bits','max_external_data_bits','native_depths','reset','source_relations','relation_limit','lifetime','known_bits','service_protocols','external_protocol','observation')},
        'shared_clock_physical_repair_prices_included':False,'arbitrary_arithmetic_source_correlation_qualified':False,
        'production_price_binding_qualified':False,'test_observed':False,'full_D_ready':False}
    write(out/'candidate.json',candidate);write(out/'validation.json',reports)
    write(out/'immutable-baseline-diagnostic.json',{'source_sha256':cfg['parent_model_sha256'],'coefficients_unchanged':True,
        'eligible_for_selection':False,'outside_original_domain_diagnostic_only':True,'rows':diagnostic})
    sources={}
    for path in [Path(__file__),CONFIG,EXECUTION,Path(__file__).with_name('model_m2_state_fit.py'),Path(__file__).with_name('model_training.py'),
        Path(__file__).with_name('model_general_state_samples_v2.py'),Path(__file__).with_name('model_general_state_samples.py'),Path(__file__).with_name('model_general_state_labels.py')]:
        name=str(path.relative_to(ROOT));dest=out/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);sources[name]=sha(path)
    write(out/'selection-freeze.json',{'version':'asap7-general-state-selection-freeze-v1','status':'frozen_awaiting_independent_test' if ready else 'failed_validation',
        'dataset_path':str(dataset),'dataset_sha256':sha(dataset),'admission_path':d['admission_path'],'admission_sha256':d['admission_sha256'],
        'protocol_sha256':sha(CONFIG),'execution_sha256':sha(EXECUTION),'candidate_sha256':sha(out/'candidate.json'),
        'validation_sha256':sha(out/'validation.json'),'baseline_diagnostic_sha256':sha(out/'immutable-baseline-diagnostic.json'),
        'sources':sources,'test_observed':False,'required_independent_tasks':54,'deployable_stage_if_independent_passes':'grt',
        'production_price_binding_qualified':False,'environment':{'python':sys.version,'numpy':package_version('numpy'),
            'scipy':package_version('scipy'),'threads':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}}})
    print(json.dumps({'status':'validation_passed' if ready else 'validation_failed','stages':{st:{'algorithm':r['selected_algorithm'],
        'owners':{o:{k:v for k,v in q.items() if k in ('status','median_relative_error','p95_relative_error','normalized_MAE')} for o,q in r['selected_validation'].items()}} for st,r in reports.items()},
        'PPA_calls':0,'test_observed':False}),flush=True)


def verify_fit(folder):
    f=read(folder/'selection-freeze.json')
    if (f['version']!='asap7-general-state-selection-freeze-v1' or f['test_observed']
        or sha(CONFIG)!=f['protocol_sha256'] or sha(EXECUTION)!=f['execution_sha256']
        or sha(f['dataset_path'])!=f['dataset_sha256'] or sha(f['admission_path'])!=f['admission_sha256']):
        raise ValueError('general-state frozen fit inputs changed')
    for key,name in [('candidate_sha256','candidate.json'),('validation_sha256','validation.json'),('baseline_diagnostic_sha256','immutable-baseline-diagnostic.json')]:
        if sha(folder/name)!=f[key]:raise ValueError('general-state selected artifact changed')
    for name,h in f['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('general-state fitting producer changed')
    return f


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('extract','fit','verify'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--folder',type=Path);p.add_argument('--dataset',type=Path);a=p.parse_args()
    if a.action=='extract':extract(a.folder.resolve(),a.out.resolve())
    elif a.action=='fit':fit(a.dataset.resolve(),a.out.resolve())
    else:verify_fit(a.out.resolve());print('general-state frozen fit verified')
