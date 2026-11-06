"""Raw native-state replay, preregistered area selection and boundary freeze."""
import argparse
from collections import Counter
from contextlib import redirect_stdout
import copy
from importlib.metadata import version as package_version
import io
import json
import math
import os
from pathlib import Path
import shutil
import sys

from .budget import Ledger
from .model_collection import sha,write
from .model_native_state_collection import CONFIG,ROOT,SUFFIX,verify as verify_collection,read
from .model_native_state_samples import specifications,source,features
from .model_native_state_labels import labels,witness
from .model_m2_state_replay import RawAudit
from .model_m2_state_fit import nnls,quality


def reparse(directory,task):
    from .backend import stage_metrics,verify_orfs_area
    from .model_m2_evaluate import measurement_identity
    from .model_m2_live_cec_v3 import verify_proof
    from .platforms import profile,verify_wire_readback
    from .sdc import verify_sdc,rtl_ports
    m=read(directory/'manifest.json');p=profile('asap7');cells=read(directory/'liberty_cells.json')['cells']
    if (m['status']!='completed' or m['threads_per_tool']!=4 or m['task_id']!=task['id']
        or sha(directory/'input.sv')!=task['rtl_sha256'] or sha(directory/'native-state-contract.json')!=task['contract_sha256']
        or m['period_ps']!=task['period_ps'] or len(m['metrics'])!=2 or {v['stage'] for v in m['metrics']}!={'synth','grt'}):
        raise ValueError('native-state measurement incomplete or mismatched')
    metrics=[]
    for stage in ('synth','grt'):
        reports=directory/'reports'/SUFFIX;g=stage_metrics(reports,stage,cells,task['period_ps'],selected=p)
        g['native_state_paths']=labels(reports/('vulsim_'+stage),task['period_ps'],g['raw_report_units']['time']['to_ps'])
        g['native_state_witness']=witness(directory,stage,cells)
        rc=verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),p)
        if rc is not None:g['wire_RC_readback']=rc
        stem={'synth':'1_synth','grt':'5_1_grt'}[stage]
        sdc=directory/'results'/SUFFIX/(stem+'.sdc')
        contract=verify_sdc(sdc.read_text(),p,task['period_ps'],rtl_ports((directory/'input.sv').read_text(),'ModelBundle'))
        if contract!=m['sdc_contracts'][stage]:raise ValueError('native-state SDC replay differs')
        native=read(directory/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell']
        g['orfs_area_crosscheck']=verify_orfs_area(g['cell_area_um2'],native)
        old=next(v for v in m['metrics'] if v['stage']==stage)
        for key,value in g.items():
            if key!='raw_reports_prefix' and old.get(key)!=value:raise ValueError('native-state replay differs: '+task['id']+'/'+stage+'/'+key)
        if not g['timing_coverage_complete']:raise ValueError('native-state incomplete timing coverage')
        metrics.append(g)
    with redirect_stdout(io.StringIO()):
        verify_proof(directory/'logs'/SUFFIX/'structural_cec/proof.json',
            directory/'results'/SUFFIX/'4_before_rsz_lec.v',directory/'results'/SUFFIX/'4_after_rsz_lec.v')
    return m,metrics,measurement_identity(m)


def rows_for_task(task,metrics,manifest_hash):
    result=[]
    for g in metrics:
        w=g['native_state_witness'];area=g['cell_area_um2']-w['excluded_observer_area_um2']
        unassigned=area-w['functional_state_control_area_um2']
        if area<=0 or unassigned < -1e-6 or g['sequential_cells']!=task['features']['state_bits']:
            raise ValueError('native state area/register decomposition invalid')
        result.append({'id':task['id']+'/'+g['stage'],'task_id':task['id'],'source_group':task['source_group'],
            'split':task['split'],'stage':g['stage'],'period_ps':task['period_ps'],'features':task['features'],
            'state_area_um2':area,'functional_state_control_area_um2':w['functional_state_control_area_um2'],
            'unassigned_clock_physical_port_area_um2':max(0.,unassigned),'excluded_observer_area_um2':w['excluded_observer_area_um2'],
            'boundary_paths':g['native_state_paths'],'whole_setup_slack_ps':g['setup_worst_slack_ps'],
            'whole_hold_slack_ps':g['hold_worst_slack_ps'],'source_sha256':task['rtl_sha256'],'manifest_sha256':manifest_hash})
    return result


def extract(folder,out):
    a=verify_collection(folder);cfg=read(CONFIG);p=read(folder/'progress.json')
    ids={t['id'] for t in a['tasks'] if t['split']!='test'}
    if (p['phase']!='fitting_collection_complete' or p['active'] or p['errors'] or p['waiting']
        or set(p['completed'])!=ids or not p['test_locked']):raise ValueError('complete native fitting and locked tests required')
    specs={s['id']:s for s in specifications(cfg)};audit=RawAudit(read(Ledger().path)['entries'])
    rows=[];runs=[];groups={}
    for t in a['tasks']:
        d=folder/'runs'/t['id']
        if t['split']=='test':
            if d.exists():raise ValueError('native independent state test observed before freeze')
            continue
        spec=specs[t['source_group']];c=read(d/'native-state-contract.json')
        if (source(spec)!=(d/'input.sv').read_text() or c['spec']!=spec or c['protocol_sha256']!=sha(CONFIG)
            or t['features']!=features(spec,t['period_ps'])):raise ValueError('native state source/geometry/features differ')
        audit.ancestry(d);m,metrics,identity=reparse(d,t)
        if (identity!=a['measurement_static_identity_sha256'] or m['native_state_admission_sha256']!=sha(folder/'admission.json')):
            raise ValueError('native state physical context/admission differs')
        if groups.setdefault(t['rtl_sha256'],t['split'])!=t['split']:raise ValueError('native source crossed splits')
        rows.extend(rows_for_task(t,metrics,sha(d/'manifest.json')))
        runs.append({'task_id':t['id'],'directory':str(d),'manifest_sha256':sha(d/'manifest.json'),
            'CTS_proof_sha256':sha(d/'logs'/SUFFIX/'structural_cec/proof.json')})
    if len(rows)!=216 or Counter(r['split'] for r in rows)!={'train':144,'validation':72}:
        raise ValueError('native-state raw row count differs')
    if audit.support_sidecar_reconciliations:raise ValueError('native cohort unexpectedly contains legacy sidecar damage')
    result={'version':'asap7-native-state-fitting-dataset-v1','admission_path':str(folder/'admission.json'),
        'admission_sha256':sha(folder/'admission.json'),'protocol_sha256':sha(CONFIG),
        'parent_model_sha256':cfg['parent_model_sha256'],'parent_primitives_sha256':cfg['parent_primitives_sha256'],
        'measurement_static_identity_sha256':a['measurement_static_identity_sha256'],
        'test_labels_read':False,'test_collection_locked':True,'rows':sorted(rows,key=lambda r:r['id']),
        'runs':runs,'audit':{'status':'passed','source_groups':len(groups),'physical_runs':108,'stage_rows':216,
            'path_labels':sum(len(r['boundary_paths']) for r in rows),'paid_leaf_commands':len(audit.commands),
            'paid_leaf_ids':sorted(audit.commands),'raw_file_hashes_checked':len(audit.hashed),
            'raw_ancestor_manifests':{str(k):v for k,v in audit.directories.items()},'PPA_calls':0}}
    if out.exists():raise ValueError('preserve native-state raw extraction')
    write(out,result)
    print(json.dumps(result['audit']|{'paid_leaf_ids':'in dataset','raw_ancestor_manifests':'in dataset'}),flush=True)


def boundary(rows,cfg):
    registered=[p|{'row_id':r['id']} for r in rows for p in r['boundary_paths'] if p['kind']=='register']
    primary=[p|{'row_id':r['id']} for r in rows for p in r['boundary_paths'] if p['kind']=='port']
    if len(registered)!=3*len(rows) or len(primary)!=len(rows):raise ValueError('native boundary labels incomplete')
    def maximum(values,key):return max(values,key=lambda v:(v[key],v['row_id'],v['id']))
    rh,rd=maximum(registered,'H_ps'),maximum(registered,'delay_ps')
    ih,pd=maximum(primary,'H_ps'),maximum(primary,'delay_ps')
    reserve=cfg['boundary']['engineering_reserve_ps']
    reg=max(0.,rh['H_ps'])+max(0.,rd['delay_ps'])+reserve
    primary_value=max(0.,ih['H_ps'])+max(0.,pd['delay_ps'])+reserve
    return {'io_delay_fraction':.2,'register_overhead_ps':reg,'input_overhead_ps':max(reg,primary_value),
        'registered_H_max_ps':max(0.,rh['H_ps']),'registered_control_QD_max_ps':max(0.,rd['delay_ps']),
        'input_H_max_ps':max(0.,ih['H_ps']),'input_enable_PD_max_ps':max(0.,pd['delay_ps']),
        'engineering_clock_reserve_ps':reserve,'registered_H_witness':rh,'registered_QD_witness':rd,
        'input_H_witness':ih,'input_PD_witness':pd,'fit_splits':['train','validation'],
        'scope':cfg['boundary']['scope'],'input_IO_delay_subtracted_once':True}


def fit(dataset,out):
    cfg,d=read(CONFIG),read(dataset)
    if (d['version']!='asap7-native-state-fitting-dataset-v1' or d['protocol_sha256']!=sha(CONFIG)
        or d['audit']['status']!='passed' or d['test_labels_read'] or not d['test_collection_locked']
        or any(r['split'] not in ('train','validation') for r in d['rows'])):
        raise ValueError('audited fitting-only native dataset required')
    a=verify_collection(Path(d['admission_path']).parent)
    if sha(d['admission_path'])!=d['admission_sha256']:raise ValueError('native fitting admission changed')
    baseline=read(ROOT/cfg['parent_model'])
    if sha(ROOT/cfg['parent_model'])!=cfg['parent_model_sha256']:raise ValueError('immutable released state baseline changed')
    out.mkdir(parents=True,exist_ok=False);stages={};reports={}
    for stage in ('synth','grt'):
        rows=[r for r in d['rows'] if r['stage']==stage]
        train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
        if len(train)!=72 or len(val)!=36:raise ValueError('complete native state stage data required')
        candidates=[];unavailable=[]
        for name in cfg['area_candidates']:
            if name=='immutable_released_state_v1':
                if stage not in baseline['stages']:
                    unavailable.append({'name':name,'reason':'parent published no '+stage+' coefficients'});continue
                # Copy only coefficients; old independent values do not select
                # algorithms or reserves and never enter this dataset.
                model=copy.deepcopy(baseline['stages'][stage]['area_model'])
            elif name=='NNLS_bits_signals':model=nnls(train,['state_bits','state_signals'])
            elif name=='NNLS_typed_state_and_controls':model=nnls(train,cfg['typed_features'])
            elif name=='exact_SDC_NNLS_typed_state_and_controls':
                model={'kind':'exact_SDC_nonnegative_linear','slices':{str(t):nnls([r for r in train if r['period_ps']==t],cfg['typed_features']) for t in cfg['SDC_ps']}}
            else:raise ValueError('unregistered native state predictor')
            q=quality(model,val,cfg)
            candidates.append({'name':name,'model':model,'validation':q,
                'by_exact_SDC':{str(t):quality(model,[r for r in val if r['period_ps']==t],cfg) for t in cfg['SDC_ps']},
                'serialized_bytes':len(json.dumps(model,sort_keys=True,separators=(',',':')).encode())})
        best=min(candidates,key=lambda c:(c['validation']['status']!='passed',c['validation']['normalized_MAE'],c['serialized_bytes'],c['name']))
        stages[stage]={'quality_status':'awaiting_independent_test' if best['validation']['status']=='passed' else 'failed_validation',
            'algorithm':best['name'],'area_model':best['model'],'boundary_model':boundary(rows,cfg)}
        reports[stage]={'selected_algorithm':best['name'],'selected_validation':best['validation'],
            'candidates':candidates,'unavailable_candidates':unavailable}
    ready=stages['grt']['quality_status']=='awaiting_independent_test'
    candidate={'version':'arithmetic-native-state-candidate-v1','id':'asap7-native-state-successor-v1',
        'quality_status':'awaiting_independent_test' if ready else 'failed_validation','target_platform':'asap7',
        'platform_profile_sha256':a['tasks'][0]['profile_sha256'],'ABC_ps':1500,'exact_SDC_ps':cfg['SDC_ps'],'IO':'0.2T',
        'feature_schema':cfg['feature_schema'],'feature_names':cfg['features'],'stages':stages,
        'native_enable_policy':cfg['native_protocol'],'domain':{'word_widths':cfg['word_widths'],
            **{k:cfg[k] for k in ('max_capture_stage','max_parallel_words','max_input_bits','max_capture_bits','max_state_bits','max_state_signals')},
            'known_bits':cfg['known_bits'],'topology':cfg['geometry'],'clock_reset':'single clock, synchronous active-low reset',
            'input_service_wrapper_state_included':False,'joint_arithmetic_or_formal_boundary_qualified':False,
            'continuous_SDC_qualified':False,'native_actual_bank_coverage_still_required':True},
        'parent_model_sha256':cfg['parent_model_sha256'],'parent_primitives_sha256':cfg['parent_primitives_sha256'],
        'measurement_static_identity_sha256':d['measurement_static_identity_sha256'],
        'dataset_sha256':sha(dataset),'protocol_sha256':sha(CONFIG),'test_observed':False,
        'production_price_binding_qualified':False,'full_D_ready':False}
    write(out/'candidate.json',candidate);write(out/'validation.json',reports)
    sources={}
    for path in [Path(__file__),CONFIG,Path(__file__).with_name('model_m2_state_fit.py'),Path(__file__).with_name('model_m2_state_replay.py'),Path(__file__).with_name('model_training.py')]:
        name=str(path.relative_to(ROOT));dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
    write(out/'selection-freeze.json',{'version':'asap7-native-state-selection-freeze-v1',
        'status':'frozen_awaiting_independent_test' if ready else 'failed_validation','dataset_path':str(dataset),
        'dataset_sha256':sha(dataset),'admission_path':d['admission_path'],'admission_sha256':d['admission_sha256'],
        'protocol_sha256':sha(CONFIG),'candidate_sha256':sha(out/'candidate.json'),'validation_sha256':sha(out/'validation.json'),
        'sources':sources,'test_observed':False,'production_price_binding_qualified':False,
        'parent_model_sha256':cfg['parent_model_sha256'],'required_independent_tasks':36,
        'environment':{'python':sys.version,'numpy':package_version('numpy'),'scipy':package_version('scipy'),
            'threads':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS')}}})
    print(json.dumps({'status':'validation_passed' if ready else 'validation_failed','PPA_calls':0,'test_observed':False,
        'stages':{st:{'algorithm':r['selected_algorithm'],'median_relative_error':r['selected_validation']['median_relative_error'],
            'p95_relative_error':r['selected_validation']['p95_relative_error'],
            'input_overhead_ps':stages[st]['boundary_model']['input_overhead_ps'],
            'register_overhead_ps':stages[st]['boundary_model']['register_overhead_ps']} for st,r in reports.items()}}),flush=True)


def verify_fit(folder):
    f=read(folder/'selection-freeze.json')
    if (f['version']!='asap7-native-state-selection-freeze-v1' or f['test_observed']
        or sha(CONFIG)!=f['protocol_sha256'] or sha(f['dataset_path'])!=f['dataset_sha256']
        or sha(f['admission_path'])!=f['admission_sha256'] or sha(folder/'candidate.json')!=f['candidate_sha256']
        or sha(folder/'validation.json')!=f['validation_sha256']):raise ValueError('native-state frozen fit differs')
    for name,h in f['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('native state frozen producer changed')
    return f


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('extract','fit','verify'))
    p.add_argument('--out',type=Path,required=True);p.add_argument('--folder',type=Path);p.add_argument('--dataset',type=Path)
    args=p.parse_args()
    if args.action=='extract':
        if args.folder is None:p.error('extract requires folder')
        extract(args.folder.resolve(),args.out.resolve())
    elif args.action=='fit':
        if args.dataset is None:p.error('fit requires dataset')
        fit(args.dataset.resolve(),args.out.resolve())
    else:verify_fit(args.out.resolve());print('verified frozen native-state fit')


if __name__=='__main__':main()
