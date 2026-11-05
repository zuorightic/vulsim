"""Audit and evaluate the frozen M2 F4 cohort once; never refit from tests."""
import argparse
from collections import Counter
import copy
import fcntl
import hashlib
from itertools import combinations
import json
from pathlib import Path
import shutil

from .budget import Ledger
from .model_collection import sha,write
from .model_features import features
from .model_m2_fit import CONFIG as BASE_CONFIG
from .model_m2_fit_v2 import verify_fit,predict,quality
from .model_m2_tests import verify as verify_admission
from .model_training import metric

ROOT=Path(__file__).resolve().parents[2]
SUFFIX=Path('asap7/arithmetic_probe/base')


def read(path):return json.loads(Path(path).read_text())


def exclusive(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def admission_chain(path):
    result={};seen=set()
    while path:
        path=Path(path)
        if str(path) in seen:raise ValueError('cyclic test admission ancestry')
        seen.add(str(path));a=read(path)
        for name,h in a['sources'].items():
            if sha(path.parent/'source'/name)!=h:raise ValueError('changed archived test producer')
        if a['id'] in result:raise ValueError('duplicate admission id')
        result[a['id']]={'path':str(path),'sha256':sha(path)}
        parent=a.get('predecessor')
        if parent:
            if sha(parent['admission_path'])!=parent['admission_sha256']:raise ValueError('changed archived test admission')
            path=parent['admission_path']
        else:path=None
    return result


def measurement_identity(manifest):
    # SDC and its proportional IO are registered axes. The generic synth-only
    # prefix records evaluation_stage=synth even when its continuation obtains
    # grt; actual stage identity is reparsed independently for every metric.
    c={k:v for k,v in manifest['mapping_context'].items() if k not in ('sdc_period_ps','io_delay_max_ps','evaluation_stage')}
    return hashlib.sha256(json.dumps(c,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def verify_paid_ancestry(directory,admissions,entries,seen=None):
    directory=Path(directory);seen=set() if seen is None else seen
    if str(directory) in seen:raise ValueError('cyclic physical ancestry')
    seen.add(str(directory));m=read(directory/'manifest.json')
    owner=admissions.get(m['admission_id'])
    if owner is None:raise ValueError('physical task has no test admission')
    for c in m['commands']:
        e=entries[c['budget_reservation_id']]
        expected_status='completed' if c['exit_code']==0 else 'failed'
        if (e['status']!=expected_status or e.get('admission_sha256')!=owner['sha256'] or e['command']!=c['command']
            or e.get('selection_freeze_sha256')!=m['selection_freeze_sha256'] or e.get('task_id')!=m['task_id']
            or c['cleanup']['remaining_live_pids']):raise ValueError('unpaid or unbound test command')
    reuse=m.get('checkpoint_reuse')
    if reuse:
        source=Path(reuse['source_run'])
        if sha(source/'manifest.json')!=reuse['source_manifest_sha256']:raise ValueError('changed physical ancestor')
        old=read(source/'manifest.json')
        if sha(source/'input.sv')!=sha(directory/'input.sv') or sha(source/'sample-contract.json')!=sha(directory/'sample-contract.json'):
            raise ValueError('physical ancestry changed the source')
        if reuse['mode'] in ('exact_postrepair_ODB_parser_continuation',):
            actual=copy.deepcopy(next(v for v in m['metrics'] if v['stage']=='synth'))
            inherited=copy.deepcopy(next(v for v in old['metrics'] if v['stage']=='synth'))
            actual.pop('raw_reports_prefix',None);inherited.pop('raw_reports_prefix',None)
            if actual!=inherited:raise ValueError('inherited synthesis metric changed')
        verify_paid_ancestry(source,admissions,entries,seen)
    return seen


def extract(folder,out):
    from .model_m2_collection import verify_plan,run_directory
    from .model_mul_interval_fit import verify_measurement
    from .model_samples import verify_capture_banks
    from .model_m2_live_cec import verify_proof
    a=verify_admission(folder);progress=read(folder/'progress.json')
    ids={t['id'] for t in a['tasks']}
    if (progress['phase']!='test_collection_complete' or set(progress['completed'])!=ids or progress['waiting'] or progress['errors']):
        raise ValueError('all56 independent tasks must complete before evaluation extraction')
    p=verify_plan(Path(a['plan_path']));f=verify_fit(Path(a['selection_path']))
    parent_data=read(f['dataset_path']);admissions=admission_chain(folder/'admission.json')
    ledger=read(Ledger().path);entries={e['id']:e for e in ledger['entries']}
    ref_task=next(t for t in p['tasks'] if t['split']=='train')
    ref=read(run_directory(Path(a['plan_path']).parent,ref_task)/'manifest.json');identity=measurement_identity(ref)
    rows=[];runs=[];physical_ancestors=set()
    for t in a['tasks']:
        binding=t.get('inherited_run');d=Path(binding['directory']) if binding else folder/'runs'/t['id'];m=read(d/'manifest.json')
        if binding and (sha(d/'manifest.json')!=binding['manifest_sha256'] or sha(binding['admission_path'])!=binding['admission_sha256']):
            raise ValueError('changed inherited independent measurement')
        if (m['status']!='completed' or t['split']!='test' or m['threads_per_tool']!=4 or m['selection_freeze_sha256']!=a['selection_sha256']
            or sha(d/'input.sv')!=t['rtl_sha256'] or sha(d/'sample-contract.json')!=t['sample_contract_sha256']):raise ValueError('incomplete independent source or selection')
        if measurement_identity(m)!=identity:raise ValueError('test physical context differs from fitting')
        if m['test_admission_sha256']!=admissions[m['admission_id']]['sha256']:raise ValueError('test manifest admission mismatch')
        physical_ancestors.update(verify_paid_ancestry(d,admissions,entries))
        cells=read(d/'liberty_cells.json')['cells'];specs=read(d/'sample-contract.json')['labels']
        verify_measurement(d,m,t,{'id':m['admission_id']},cells)
        proof=d/'logs'/SUFFIX/'structural_cec/proof.json'
        verify_proof(proof,d/'results'/SUFFIX/'4_before_rsz_lec.v',d/'results'/SUFFIX/'4_after_rsz_lec.v')
        if {v['stage'] for v in m['metrics']}!={'synth','grt'} or len(m['metrics'])!=2:raise ValueError('independent stage coverage incomplete')
        for stage in m['metrics']:
            prefix=d/'reports'/SUFFIX/('vulsim_'+stage['stage']);banks=verify_capture_banks(prefix,d/'sample-contract.json',cells)
            if banks!=stage.get('model_capture_banks',{}):raise ValueError('independent capture structure changed')
            instances=[line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
            labels={v['id']:v for v in stage['model_labels']}
            for s in specs:
                core=sum(cells[master]['area_um2'] for name,master in instances if master in cells and not cells[master]['sequential'] and name.startswith(s['arithmetic_scope']))
                if core<=0:raise ValueError('missing independent core area')
                label=labels[s['id']]
                rows.append({'id':t['id']+'/'+s['id']+'/'+stage['stage'],'task_id':t['id'],'split':'test','family':t['family'],
                    'stage':stage['stage'],'operation':s['operation'],'rtl_operation':s['rtl_operation'],'spec':s,
                    'features':features(s['lhs_width'],s['rhs_width'],s['result_width'],s['fanout'],1500,t['period_ps']),
                    'delay_ps':label['data_delay_ps'],'comb_area_um2':core,'period_ps':t['period_ps'],
                    'observed_H_ps':t['period_ps']-label['data_delay_ps']-label['slack_ps'],'path_slack_ps':label['slack_ps'],
                    'whole_setup_slack_ps':stage['setup_worst_slack_ps'],'whole_hold_slack_ps':stage['hold_worst_slack_ps'],
                    'manifest_sha256':sha(d/'manifest.json'),'source_sha256':t['rtl_sha256'],'bank_counts':banks.get(s['id'])})
        runs.append({'task_id':t['id'],'directory':str(d),'manifest_sha256':sha(d/'manifest.json'),'admission_id':m['admission_id'],
                     'proof_sha256':sha(proof),'peak_RSS_MiB':max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
    expected={t['id']+'/'+s['id']+'/'+stage for t in a['tasks'] for s in read(t['sample_contract'])['labels'] for stage in ('synth','grt')}
    if {r['id'] for r in rows}!=expected or len(rows)!=len(expected):raise ValueError('independent label coverage incomplete')
    if {r['source_sha256'] for r in rows}&{r['source_sha256'] for r in parent_data['rows']}:raise ValueError('independent source crossed fitting boundary')
    data={'version':'asap7-m2-independent-dataset-v1','mode':'test','admission_path':str((folder/'admission.json').resolve()),
        'admission_sha256':sha(folder/'admission.json'),'selection_path':a['selection_path'],'selection_sha256':a['selection_sha256'],
        'candidate_sha256':a['candidate_sha256'],'measurement_static_identity_sha256':identity,'plan_sha256':a['plan_sha256'],
        'rows':sorted(rows,key=lambda r:r['id']),'runs':sorted(runs,key=lambda r:r['task_id']),'expected_task_ids':sorted(ids),
        'physical_ancestry':sorted(physical_ancestors),'admission_ancestry':admissions,'failures':[],'old_test_labels_used':False}
    exclusive(out,data);print(json.dumps({'status':'extracted','tasks':len(runs),'rows':len(rows)}),flush=True)


def validate_dataset(data,candidate,plan):
    if data.get('version')!='asap7-m2-independent-dataset-v1' or data.get('mode')!='test' or data['failures'] or data['old_test_labels_used']:
        raise ValueError('wrong independent data role')
    tasks={t['id']:t for t in plan['tasks'] if t['split']=='test'}
    specs={tid:{s['id']:s for s in read(t['sample_contract'])['labels']} for tid,t in tasks.items()}
    expected={t['id']+'/'+s['id']+'/'+stage for t in tasks.values() for s in specs[t['id']].values() for stage in ('synth','grt')}
    if set(data['expected_task_ids'])!=set(tasks) or {r['id'] for r in data['rows']}!=expected or len(data['rows'])!=len(expected):raise ValueError('incomplete independent cohort')
    for r in data['rows']:
        t=tasks[r['task_id']]
        if r['split']!='test' or r['source_sha256']!=t['rtl_sha256'] or r['period_ps']!=t['period_ps'] or r['spec']['fanout']!=4:
            raise ValueError('independent row crossed source/split/target')
        s=specs[t['id']][r['spec']['id']]
        if (r['spec']!=s or r['features']!=features(s['lhs_width'],s['rhs_width'],s['result_width'],4,1500,t['period_ps'])
            or r['operation']!=s['operation'] or r['rtl_operation']!=s['rtl_operation']
            or r['id']!=t['id']+'/'+s['id']+'/'+r['stage']):raise ValueError('independent semantic feature or label mismatch')
    if {r['operation'] for r in data['rows']}!=set(candidate['stages']['grt']['operations']):raise ValueError('independent operation coverage incomplete')


def report(rows,candidate):
    stages={};ratios=read(BASE_CONFIG)['feasibility_ratios']
    for stage,value in candidate['stages'].items():
        details={};all_pred=[];subset=[r for r in rows if r['stage']==stage]
        for op,model in value['operations'].items():
            group=[r for r in subset if r['operation']==op]
            if not group:raise ValueError('missing independent operation')
            delay=quality(group,model['delay'],'delay');area=quality(group,model['area'],'area')
            pred=[{'id':r['id'],'delay_ps':predict(model['delay'],r,'delay'),'comb_area_um2':predict(model['area'],r,'area')} for r in group]
            all_pred.extend(pred)
            passed=delay['status']==area['status']=='passed'
            details[op]={'status':'passed' if passed else 'failed','delay':delay,'area':area,'predictions':pred,
                'synthetic_conservative_rejections':sum(r['delay_ps']<=r['delay_ps']*k<p['delay_ps'] for r,p in zip(group,pred) for k in ratios),
                'actual_target_conservative_rejections':sum(r['delay_ps']<=r['period_ps']-r['observed_H_ps']<p['delay_ps'] for r,p in zip(group,pred)),
                'whole_setup_failed':sum(r['whole_setup_slack_ps']<0 for r in group),'local_pass_whole_setup_fail':sum(r['path_slack_ps']>=0 and r['whole_setup_slack_ps']<0 for r in group),
                'source_task_count':len({r['task_id'] for r in group})}
        indexed={v['id']:v for v in all_pred}
        ranking=[];groups={}
        for r in subset:groups.setdefault((r['operation'],r['rtl_operation'],r['spec']['lhs_width'],r['spec']['result_width']),[]).append(r)
        for key,group in sorted(groups.items()):
            for a,b in combinations(sorted(group,key=lambda r:r['period_ps']),2):
                for field in ('delay_ps','comb_area_um2'):
                    observed=(a[field]>b[field])-(a[field]<b[field]);pa=indexed[a['id']][field];pb=indexed[b['id']][field];predicted=(pa>pb)-(pa<pb)
                    ranking.append({'operation':key[0],'rtl_operation':key[1],'width':key[2],'result_width':key[3],'label':field,
                        'task_a':a['task_id'],'task_b':b['task_id'],'observed_order':observed,'predicted_order':predicted,'matches':observed==predicted})
        stages[stage]={'status':'passed' if all(d['status']=='passed' for d in details.values()) else 'failed',
            'passing_operations':sum(v['status']=='passed' for v in details.values()),'operation_count':len(details),'operations':details,
            'delay':metric([r['delay_ps'] for r in subset],[indexed[r['id']]['delay_ps'] for r in subset],1.5),
            'area':metric([r['comb_area_um2'] for r in subset],[indexed[r['id']]['comb_area_um2'] for r in subset],1e-4),
            'false_feasible':sum(d['delay']['false_feasible'] for d in details.values()),'denominator':sum(d['delay']['denominator'] for d in details.values()),
            'actual_target_false_feasible':sum(d['delay']['actual_target_false_feasible'] for d in details.values()),'actual_target_denominator':len(subset),
            'ranking':{'scope':'same primitive/shape/width/F4 at different registered SDCs; diagnostic only, no whole-candidate ranking claim',
                       'matching_pairs':sum(v['matches'] for v in ranking),'denominator':len(ranking),'records':ranking}}
    return stages


def evaluate(data_path,selection,out):
    from .model_m2_collection import verify_plan
    f=verify_fit(selection);data=read(data_path);candidate=read(selection.parent/'candidate.json');plan=verify_plan(Path(f['plan_path']))
    if data['selection_sha256']!=sha(selection) or data['candidate_sha256']!=f['candidate_sha256'] or sha(data['admission_path'])!=data['admission_sha256']:
        raise ValueError('independent dataset changed frozen selection')
    validate_dataset(data,candidate,plan)
    with (selection.parent/'independent-evaluation.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        if out.exists():raise ValueError('preserve previous independent result')
        exclusive(selection.parent/'independent-evaluation-consumption.json',{'dataset_sha256':sha(data_path),'selection_sha256':sha(selection),'result_path':str((out/'result.json').resolve())})
        out.mkdir(parents=True)
        stages=report(data['rows'],candidate)
        paths=[Path(__file__),Path(__file__).with_name('model_m2_fit_v2.py'),Path(__file__).with_name('model_m2_fit.py'),
               Path(__file__).with_name('model_features.py'),Path(__file__).with_name('model_training.py'),BASE_CONFIG]
        sources={}
        for path in paths:
            name=str(path.relative_to(ROOT));dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
        result={'version':'asap7-m2-independent-result-v1','dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),
            'selection_path':str(selection.resolve()),'selection_sha256':sha(selection),'candidate_sha256':f['candidate_sha256'],
            'stages':stages,'quality_status':stages['grt']['status'],'sources':sources,'full_D_ready':False,'parameters_changed_after_test':False}
        write(out/'result.json',result)
        print(json.dumps({'quality_status':result['quality_status'],'stages':{s:{k:v for k,v in r.items() if k not in ('operations','ranking')} for s,r in stages.items()}}),flush=True)


def verify_result(path):
    r=read(path);selection=Path(r['selection_path']);f=verify_fit(selection)
    if sha(selection)!=r['selection_sha256'] or sha(r['dataset_path'])!=r['dataset_sha256'] or f['candidate_sha256']!=r['candidate_sha256']:
        raise ValueError('changed independent result inputs')
    for name,h in r['sources'].items():
        if sha(ROOT/name)!=h or sha(path.parent/'source'/name)!=h:raise ValueError('changed independent evaluator')
    data=read(r['dataset_path']);candidate=read(selection.parent/'candidate.json')
    from .model_m2_collection import verify_plan
    validate_dataset(data,candidate,verify_plan(Path(f['plan_path'])))
    actual=report(data['rows'],candidate)
    if actual!=r['stages'] or actual['grt']['status']!=r['quality_status']:raise ValueError('independent result does not recompute')
    consume=read(selection.parent/'independent-evaluation-consumption.json')
    if consume!={'dataset_sha256':r['dataset_sha256'],'selection_sha256':r['selection_sha256'],'result_path':str(path.resolve())}:raise ValueError('wrong independent consumption owner')
    return r


def publish(result_path,out):
    r=verify_result(result_path);out.mkdir(parents=True,exist_ok=False);published=[]
    if r['quality_status']=='passed':
        model=read(Path(r['selection_path']).parent/'candidate.json');model.update(version='asap7-m2-primitives-qualified-v1',quality_status='passed',full_D_ready=False,
            independent_result_sha256=sha(result_path),native_consumer_ready=False)
        model['stages']={'grt':model['stages']['grt']}
        for value in model['stages']['grt']['operations'].values():value['quality_status']='passed'
        write(out/'asap7-primitives.json',model);published=[{'file':'asap7-primitives.json','sha256':sha(out/'asap7-primitives.json')}]
    write(out/'publication.json',{'version':'asap7-m2-primitives-publication-v1','result_sha256':sha(result_path),'quality_status':r['quality_status'],
        'published':published,'full_D_ready':False,'scope':'primitive/atomic labels at registered widths/shapes/ABC-SDC points and single capture bank only',
        'remaining':['native primitive adapter','qualified multiplier intervals','state and composition qualification','formal target and whole D closure']})
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
