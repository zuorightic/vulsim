"""One-shot F5 audit using frozen v4 predictors and five-bank witnesses."""
import argparse
import copy
import fcntl
from itertools import combinations
import json
from pathlib import Path
import shutil

from .budget import Ledger
from .model_collection import sha,write
from .model_features import features
from .model_m2_evaluate import measurement_identity,verify_paid_ancestry
from .model_m2_fit import CONFIG as GATES
from .model_m2_fit_v4 import verify_fit,predict,quality
from .model_m2_f5_resume import verify as verify_admission
from .model_m2_labels5 import read_labels,verify_capture_banks
from .model_training import metric

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')
DATA_VERSION='asap7-m2-F5-independent-dataset-v1'
RESULT_VERSION='asap7-m2-F5-independent-result-v1'


def read(path):return json.loads(Path(path).read_text())


def exclusive(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def initial_observation_owner(directory,m):
    snapshots=m.get('initial_synth_observation_sha256',{})
    if not snapshots:return None
    if all((directory/name).is_file() for name in snapshots):return directory
    reuse=m.get('checkpoint_reuse',{})
    if reuse.get('mode')!='exact_t0_mapping_fresh_SDC_ODB':raise ValueError('missing initial F5 synthesis observation')
    # The first F5 producer copied this optional t0 provenance field into later
    # target manifests. It never copied the pre-label observation directory.
    # Resolve only an exact annotation inherited from the hash-bound t0, without
    # replacing any current synth/grt labels or pretending this was a new run.
    source=Path(reuse['source_run']);old=read(source/'manifest.json')
    if (sha(source/'manifest.json')!=reuse['source_manifest_sha256'] or snapshots!=old.get('initial_synth_observation_sha256')
        or m.get('initial_unlabeled_synth_metrics')!=old.get('initial_unlabeled_synth_metrics')):
        raise ValueError('changed inherited initial synthesis observation')
    return initial_observation_owner(source,old)


def admission_chain(path):
    result={};seen=set()
    while path:
        path=Path(path)
        if str(path) in seen:raise ValueError('cyclic F5 admission ancestry')
        seen.add(str(path));a=read(path)
        for name,h in a['sources'].items():
            if sha(path.parent/'source'/name)!=h:raise ValueError('changed archived F5 producer')
        if a['id'] in result:raise ValueError('duplicate F5 admission id')
        result[a['id']]={'path':str(path),'sha256':sha(path)}
        parent=a.get('predecessor')
        if parent and sha(parent['path'])!=parent['sha256']:raise ValueError('changed F5 admission ancestor')
        path=parent['path'] if parent else None
    return result


def verify_measurement(directory,m,t,cells):
    from .backend import stage_metrics
    from .platforms import verify_wire_readback
    from .sdc import verify_sdc,rtl_ports
    if (m['status']!='completed' or m.get('budget_purpose')!='characterization' or m['task_id']!=t['id']
        or m['target_platform']!=t['platform'] or m['platform_profile']['profile_sha256']!=t['profile_sha256']
        or m['period_ps']!=t['period_ps'] or m['abc_target_ps']!=1500 or m['io_delay_max_ps'] is not None
        or m['threads_per_tool']!=4):raise ValueError('F5 measured identity differs from registered task')
    if {v['stage'] for v in m['metrics']}!={'synth','grt'} or len(m['metrics'])!=2:raise ValueError('incomplete F5 stage coverage')
    for name,h in m['evidence_sha256'].items():
        if sha(directory/name)!=h:raise ValueError('changed F5 raw evidence: '+name)
    observation=initial_observation_owner(directory,m)
    for name,h in m.get('initial_synth_observation_sha256',{}).items():
        if sha(observation/name)!=h:raise ValueError('changed initial F5 synthesis observation')
    if len({c['log'] for c in m['commands']})!=len(m['commands']):raise ValueError('F5 leaf log overwritten')
    for archived in m['metrics']:
        stage=archived['stage'];reports=directory/'reports'/SUFFIX;prefix=reports/('vulsim_'+stage)
        parsed=stage_metrics(reports,stage,cells,m['period_ps'],selected=m['platform_profile'])
        if any(v!=archived[k] for k,v in parsed.items() if k!='raw_reports_prefix'):raise ValueError('F5 raw stage metrics differ')
        labels=read_labels(prefix,directory/'sample-contract.json',parsed['raw_report_units']['time']['to_ps'])
        banks=verify_capture_banks(prefix,directory/'sample-contract.json',cells)
        if labels!=archived['model_labels'] or banks!=archived['model_capture_banks']:raise ValueError('F5 QD or bank evidence differs')
        if any(v['declared_capture_fanout']!=5 or len(v['capture_bank_counts'])!=5 for v in banks.values()):
            raise ValueError('F5 physical banks missing')
        if 'wire_RC_readback' in archived and verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'),m['platform_profile'])!=archived['wire_RC_readback']:
            raise ValueError('F5 wire RC differs')
        sdc=directory/'results'/SUFFIX/({'synth':'1_synth','grt':'5_1_grt'}[stage]+'.sdc')
        verify_sdc(sdc.read_text(),m['platform_profile'],t['period_ps'],rtl_ports((directory/'input.sv').read_text(),t['top']))


def check_proof(directory,admission_sha256,selection_sha256):
    from .model_m2_live_cec import verify_proof as old_verify
    from .model_m2_live_cec_v3 import verify_proof as state_verify
    path=directory/'logs'/SUFFIX/'structural_cec/proof.json';p=read(path)
    verifier=state_verify if p['version']=='m2-live-structural-cec-v3' else old_verify
    verifier(path,directory/'results'/SUFFIX/'4_before_rsz_lec.v',directory/'results'/SUFFIX/'4_after_rsz_lec.v')
    request=read(p['request_path'])
    if request['admission_sha256']!=admission_sha256 or request['selection_sha256']!=selection_sha256:raise ValueError('F5 CEC request not bound to measurement')
    for lib in request['libraries']:
        if sha(lib['path'])!=lib['sha256']:raise ValueError('F5 CEC Liberty changed')
    if any(c['exit_code'] for c in p['commands']):raise ValueError('failed F5 proof command')
    return sha(path)


def validate_cohort(admission,plan):
    tasks=admission['tasks'];old={t['id']:t for t in plan['tasks'] if t['split']=='test'}
    if len(tasks)!=56 or len({t['id'] for t in tasks})!=56:raise ValueError('F5 requires all56 preregistered tasks')
    expected={tid.replace('F4','F5') for tid in old}
    if {t['id'] for t in tasks}!=expected:raise ValueError('changed F5 source/target cohort')
    for t in tasks:
        ref=old[t['id'].replace('F5','F4')]
        for key in ('platform','profile_sha256','family','width','period_ps','abc_target_ps','top','samples'):
            if t[key]!=ref[key]:raise ValueError('changed registered F5 target/semantics: '+key)
        if t['split']!='test' or t['capture_fanout']!=5 or t['rtl_sha256'] in {v['rtl_sha256'] for v in plan['tasks']}:
            raise ValueError('F5 source not independent of earlier partitions')
        if sha(t['rtl'])!=t['rtl_sha256'] or sha(t['sample_contract'])!=t['sample_contract_sha256']:
            raise ValueError('changed registered F5 source or contract')
    return {t['id']:t for t in tasks}


def extract(folder,out):
    from .model_m2_collection import verify_plan,run_directory
    a=verify_admission(folder);p=verify_plan(Path(a['plan_path']));f=verify_fit(Path(a['selection_path']))
    tasks=validate_cohort(a,p);progress=read(folder/'progress.json')
    if (progress['phase']!='test_collection_complete' or set(progress['completed'])!=set(tasks)
        or len(progress['completed'])!=56 or progress['waiting'] or progress['errors']):raise ValueError('F5 collection incomplete')
    admissions=admission_chain(folder/'admission.json');entries={e['id']:e for e in read(Ledger().path)['entries']}
    ref=next(t for t in p['tasks'] if t['split']=='train');identity=measurement_identity(read(run_directory(Path(a['plan_path']).parent,ref)/'manifest.json'))
    rows=[];runs=[];ancestors=set()
    for tid,t in tasks.items():
        binding=t.get('inherited_run');d=Path(binding['directory']) if binding else folder/'runs'/tid;m=read(d/'manifest.json')
        if binding and sha(d/'manifest.json')!=binding['manifest_sha256']:raise ValueError('changed inherited F5 result')
        if sha(d/'input.sv')!=t['rtl_sha256'] or sha(d/'sample-contract.json')!=t['sample_contract_sha256']:raise ValueError('F5 measured source changed')
        if m['selection_freeze_sha256']!=a['selection_sha256'] or m['test_admission_sha256']!=admissions[m['admission_id']]['sha256']:
            raise ValueError('F5 measurement not bound to frozen choices')
        if measurement_identity(m)!=identity:raise ValueError('F5 physical context differs from fitting')
        ancestors.update(verify_paid_ancestry(d,admissions,entries))
        if any(c['exit_code'] for c in m['commands']):raise ValueError('current F5 stage contains failed command')
        cells=read(d/'liberty_cells.json')['cells'];contract=read(d/'sample-contract.json')
        if contract['version']!='arithmetic-model-labels-v2':raise ValueError('F5 label protocol changed')
        verify_measurement(d,m,t,cells)
        proof_hash=check_proof(d,admissions[m['admission_id']]['sha256'],a['selection_sha256'])
        for stage in m['metrics']:
            prefix=d/'reports'/SUFFIX/('vulsim_'+stage['stage']);instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
            labels={v['id']:v for v in stage['model_labels']}
            for s in contract['labels']:
                core=sum(cells[master]['area_um2'] for name,master in instances if master in cells and not cells[master]['sequential'] and name.startswith(s['arithmetic_scope']))
                if core<=0:raise ValueError('F5 arithmetic core missing')
                label=labels[s['id']]
                rows.append({'id':tid+'/'+s['id']+'/'+stage['stage'],'task_id':tid,'split':'test','family':t['family'],'stage':stage['stage'],
                    'operation':s['operation'],'rtl_operation':s['rtl_operation'],'spec':s,
                    'features':features(s['lhs_width'],s['rhs_width'],s['result_width'],5,1500,t['period_ps']),
                    'delay_ps':label['data_delay_ps'],'comb_area_um2':core,'period_ps':t['period_ps'],
                    'observed_H_ps':t['period_ps']-label['data_delay_ps']-label['slack_ps'],'path_slack_ps':label['slack_ps'],
                    'whole_setup_slack_ps':stage['setup_worst_slack_ps'],'whole_hold_slack_ps':stage['hold_worst_slack_ps'],
                    'manifest_sha256':sha(d/'manifest.json'),'source_sha256':t['rtl_sha256'],'bank_counts':stage['model_capture_banks'][s['id']]})
        runs.append({'task_id':tid,'directory':str(d),'manifest_sha256':sha(d/'manifest.json'),'admission_id':m['admission_id'],
            'proof_sha256':proof_hash,'proof_version':read(d/'logs'/SUFFIX/'structural_cec/proof.json')['version'],
            'initial_observation_owner':str(initial_observation_owner(d,m)) if m.get('initial_synth_observation_sha256') else None,
            'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
    data={'version':DATA_VERSION,'mode':'test','cohort':'F5','admission_path':str((folder/'admission.json').resolve()),'admission_sha256':sha(folder/'admission.json'),
        'selection_path':a['selection_path'],'selection_sha256':a['selection_sha256'],'candidate_sha256':a['candidate_sha256'],'plan_sha256':a['plan_sha256'],
        'measurement_static_identity_sha256':identity,'expected_task_ids':sorted(tasks),'rows':sorted(rows,key=lambda r:r['id']),
        'runs':sorted(runs,key=lambda r:r['task_id']),'physical_ancestry':sorted(ancestors),'admission_ancestry':admissions,'failures':[],'old_test_labels_used':False}
    validate_dataset(data,read(Path(a['selection_path']).parent/'candidate.json'),a,p)
    train=read(f['dataset_path'])
    if {r['source_sha256'] for r in train['rows']}&{r['source_sha256'] for r in rows}:raise ValueError('F5 source crosses fitting boundary')
    exclusive(out,data);print(json.dumps({'status':'extracted','tasks':len(runs),'rows':len(rows)}),flush=True)


def validate_dataset(data,candidate,admission,plan):
    if data.get('version')!=DATA_VERSION or data.get('cohort')!='F5' or data.get('mode')!='test' or data['failures'] or data['old_test_labels_used']:
        raise ValueError('wrong F5 independent data role')
    tasks=validate_cohort(admission,plan);specs={tid:{s['id']:s for s in read(t['sample_contract'])['labels']} for tid,t in tasks.items()}
    expected={tid+'/'+sid+'/'+stage for tid,values in specs.items() for sid in values for stage in ('synth','grt')}
    if (set(data['expected_task_ids'])!=set(tasks) or {r['id'] for r in data['rows']}!=expected or len(data['rows'])!=len(expected)
        or len(data['rows'])!=488 or {r['task_id'] for r in data['runs']}!=set(tasks) or len(data['runs'])!=56):raise ValueError('F5 sample/stage coverage incomplete')
    for r in data['rows']:
        t=tasks[r['task_id']];s=specs[t['id']][r['spec']['id']]
        if r['split']!='test' or r['source_sha256']!=t['rtl_sha256'] or r['period_ps']!=t['period_ps'] or s['fanout']!=5:raise ValueError('F5 row crossed source/target/partition')
        if (r['spec']!=s or r['features']!=features(s['lhs_width'],s['rhs_width'],s['result_width'],5,1500,t['period_ps'])
            or r['operation']!=s['operation'] or r['rtl_operation']!=s['rtl_operation'] or r['id']!=t['id']+'/'+s['id']+'/'+r['stage']):raise ValueError('F5 semantics or features changed')
    if {r['operation'] for r in data['rows']}!=set(candidate['stages']['grt']['operations']):raise ValueError('F5 operation coverage incomplete')


def report(rows,candidate):
    stages={};ratios=read(GATES)['feasibility_ratios']
    for stage,value in candidate['stages'].items():
        subset=[r for r in rows if r['stage']==stage];details={};all_pred={}
        for op,model in value['operations'].items():
            group=[r for r in subset if r['operation']==op]
            if not group:raise ValueError('missing F5 mandatory operation')
            delay=quality(group,model['delay'],'delay');area=quality(group,model['area'],'area')
            pred=[{'id':r['id'],'delay_ps':predict(model['delay'],r,'delay'),'comb_area_um2':predict(model['area'],r,'area')} for r in group]
            all_pred.update({p['id']:p for p in pred})
            details[op]={'status':'passed' if delay['status']==area['status']=='passed' else 'failed','delay':delay,'area':area,'predictions':pred,
                'synthetic_conservative_rejections':sum(r['delay_ps']<=r['delay_ps']*k<p['delay_ps'] for r,p in zip(group,pred) for k in ratios),
                'actual_target_conservative_rejections':sum(r['delay_ps']<=r['period_ps']-r['observed_H_ps']<p['delay_ps'] for r,p in zip(group,pred)),
                'whole_setup_failed':sum(r['whole_setup_slack_ps']<0 for r in group),'local_pass_whole_setup_fail':sum(r['path_slack_ps']>=0 and r['whole_setup_slack_ps']<0 for r in group),
                'source_task_count':len({r['task_id'] for r in group})}
        ranking=[];groups={}
        for r in subset:groups.setdefault((r['operation'],r['rtl_operation'],r['spec']['lhs_width'],r['spec']['result_width']),[]).append(r)
        for key,group in sorted(groups.items()):
            for a,b in combinations(sorted(group,key=lambda r:r['period_ps']),2):
                for field in ('delay_ps','comb_area_um2'):
                    observed=(a[field]>b[field])-(a[field]<b[field]);pa=all_pred[a['id']][field];pb=all_pred[b['id']][field];predicted=(pa>pb)-(pa<pb)
                    ranking.append({'operation':key[0],'rtl_operation':key[1],'width':key[2],'result_width':key[3],'label':field,
                        'task_a':a['task_id'],'task_b':b['task_id'],'observed_order':observed,'predicted_order':predicted,'matches':observed==predicted})
        stages[stage]={'status':'passed' if all(d['status']=='passed' for d in details.values()) else 'failed',
            'passing_operations':sum(d['status']=='passed' for d in details.values()),'operation_count':len(details),'operations':details,
            'delay':metric([r['delay_ps'] for r in subset],[all_pred[r['id']]['delay_ps'] for r in subset],1.5),
            'area':metric([r['comb_area_um2'] for r in subset],[all_pred[r['id']]['comb_area_um2'] for r in subset],1e-4),
            'false_feasible':sum(d['delay']['false_feasible'] for d in details.values()),'denominator':sum(d['delay']['denominator'] for d in details.values()),
            'actual_target_false_feasible':sum(d['delay']['actual_target_false_feasible'] for d in details.values()),'actual_target_denominator':len(subset),
            'ranking':{'scope':'same primitive/shape/width/F5 at different registered SDCs; diagnostic only, no whole-candidate ranking claim',
                'matching_pairs':sum(x['matches'] for x in ranking),'denominator':len(ranking),'records':ranking}}
    return stages


def evaluate(data_path,selection,out):
    from .model_m2_collection import verify_plan
    f=verify_fit(selection);data=read(data_path);candidate=read(selection.parent/'candidate.json');a=verify_admission(Path(data['admission_path']).parent)
    if data['selection_sha256']!=sha(selection) or data['candidate_sha256']!=f['candidate_sha256'] or data['admission_sha256']!=sha(data['admission_path']):
        raise ValueError('F5 evaluation not bound to frozen choices')
    validate_dataset(data,candidate,a,verify_plan(Path(f['plan_path'])))
    with (selection.parent/'independent-F5-evaluation.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():raise ValueError('preserve existing F5 result')
        exclusive(selection.parent/'independent-F5-evaluation-consumption.json',{'dataset_sha256':sha(data_path),'selection_sha256':sha(selection),'result_path':str((out/'result.json').resolve())})
        out.mkdir(parents=True);stages=report(data['rows'],candidate)
        paths=[Path(__file__),Path(__file__).with_name('model_m2_evaluate.py'),GATES]
        paths+=[ROOT/name for name in f['sources']]
        sources={}
        for path in paths:
            name=str(path.relative_to(ROOT));dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
        r={'version':RESULT_VERSION,'cohort':'F5','dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),'selection_path':str(selection.resolve()),
            'selection_sha256':sha(selection),'candidate_sha256':f['candidate_sha256'],'stages':stages,'quality_status':stages['grt']['status'],
            'sources':sources,'full_D_ready':False,'parameters_changed_after_test':False,'quality_gates_changed':False}
        write(out/'result.json',r);print(json.dumps({'quality_status':r['quality_status'],'stages':{s:{k:v for k,v in r.items() if k not in ('operations','ranking')} for s,r in stages.items()}}),flush=True)


def verify_result(path):
    from .model_m2_collection import verify_plan
    r=read(path);selection=Path(r['selection_path']);f=verify_fit(selection)
    if r['version']!=RESULT_VERSION or sha(selection)!=r['selection_sha256'] or sha(r['dataset_path'])!=r['dataset_sha256'] or f['candidate_sha256']!=r['candidate_sha256']:
        raise ValueError('changed F5 result inputs')
    for name,h in r['sources'].items():
        if sha(ROOT/name)!=h or sha(path.parent/'source'/name)!=h:raise ValueError('changed F5 numerical evaluator')
    data=read(r['dataset_path']);candidate=read(selection.parent/'candidate.json');a=verify_admission(Path(data['admission_path']).parent)
    validate_dataset(data,candidate,a,verify_plan(Path(f['plan_path'])))
    actual=report(data['rows'],candidate)
    if actual!=r['stages'] or actual['grt']['status']!=r['quality_status']:raise ValueError('F5 independent result does not recompute')
    receipt=read(selection.parent/'independent-F5-evaluation-consumption.json')
    if receipt!={'dataset_sha256':r['dataset_sha256'],'selection_sha256':r['selection_sha256'],'result_path':str(path.resolve())}:raise ValueError('wrong F5 one-shot evaluation owner')
    return r


def publish(result_path,out):
    r=verify_result(result_path);out.mkdir(parents=True,exist_ok=False);published=[]
    if r['quality_status']=='passed':
        model=read(Path(r['selection_path']).parent/'candidate.json');model.update(version='asap7-m2-primitives-qualified-v2',quality_status='passed',full_D_ready=False,
            independent_result_sha256=sha(result_path),native_consumer_ready=False)
        model['stages']={'grt':model['stages']['grt']}
        for m in model['stages']['grt']['operations'].values():m['quality_status']='passed'
        write(out/'asap7-primitives.json',model);published=[{'file':'asap7-primitives.json','sha256':sha(out/'asap7-primitives.json')}]
    write(out/'publication.json',{'version':'asap7-m2-F5-publication-v1','result_sha256':sha(result_path),'quality_status':r['quality_status'],'published':published,
        'full_D_ready':False,'scope':'primitive/atomic labels at registered exact widths/shapes/ABC-SDC points; production one capture bank; F5 new-load qualification only',
        'remaining':['native primitive adapter','qualified multiplier intervals','state and composition qualification','formal targets and whole D closure']})
    print(json.dumps({'quality_status':r['quality_status'],'published':published}),flush=True)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['extract','evaluate','verify','publish'])
    for name in ('folder','out','data','selection','result'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='extract':extract(a.folder.resolve(),a.out.resolve())
    elif a.action=='evaluate':evaluate(a.data.resolve(),a.selection.resolve(),a.out.resolve())
    elif a.action=='publish':publish(a.result.resolve(),a.out.resolve())
    else:print(json.dumps({'status':'verified','quality_status':verify_result(a.result.resolve())['quality_status']}))


if __name__=='__main__':main()
