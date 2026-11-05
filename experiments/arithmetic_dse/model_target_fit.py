"""Baseline-first fitting, validation reserves, immutable test and bounded release."""
import argparse
import copy
import hashlib
from importlib.metadata import version
import json
import math
import os
from pathlib import Path
import shutil
import sys

from .model_target_collection import CONFIG, ROOT, read, exclusive, extract, verify_plan, selected_tasks
from .model_collection import sha, write
from .model_target_features import BASE_FEATURES, FEATURES, infer, features
from .model_training import metric


def expected_samples(plan,mode):
    result=set()
    for t in selected_tasks(plan,mode):
        if sha(t['sample_contract'])!=t['sample_contract_sha256']:raise ValueError('changed declared sample contract')
        for spec in read(t['sample_contract'])['labels']:
            for stage in ('synth','grt'):
                identity=t['id']+'/'+spec['id']+'/'+stage
                if identity in result:raise ValueError('duplicate declared sample/stage identity')
                result.add(identity)
    return result


def measurement_identity(data):
    from .model_target_collection import run_directory,measurement_context
    folder=Path(data['plan_path']).parent;identities=set()
    indexed={t['id']:t for t in read(data['plan_path'])['tasks']}
    for tid in {r['task_id'] for r in data['rows']}:
        manifest=read(run_directory(folder,indexed[tid])/'manifest.json')
        identity=measurement_context(manifest,indexed[tid])
        identities.add(hashlib.sha256(json.dumps(identity,sort_keys=True,separators=(',',':')).encode()).hexdigest())
    if len(identities)!=1:raise ValueError('mixed tool/library/flow contexts in target/load data')
    return next(iter(identities))


def validate_data(path, selection=None):
    data=read(path);plan_path=Path(data['plan_path']);plan=verify_plan(plan_path)
    if plan.get('not_training'):raise ValueError('diagnostic plan cannot enter fitting or independent test')
    if (data['version']!='arithmetic-target-load-dataset-v1' or data['plan_sha256']!=sha(plan_path)
            or data['protocol_sha256']!=sha(CONFIG) or data['failures'] or not data['rows']
            or data['old_failed_test_labels_read'] is not False):raise ValueError('incomplete or changed target/load data')
    actual=extract(plan_path.parent,data['mode'],selection)
    if actual!=data:raise ValueError('dataset does not replay from actual measured target/load labels')
    ids=[r['id'] for r in data['rows']]
    if len(ids)!=len(set(ids)) or set(ids)!=expected_samples(plan,data['mode']):raise ValueError('duplicate or incomplete target/load sample/stage coverage')
    expected=[t['id'] for t in selected_tasks(plan,data['mode'])]
    if data['expected_task_ids']!=expected or {r['task_id'] for r in data['rows']}!=set(expected):
        raise ValueError('incomplete declared acquisition phase')
    measurement_identity(data)
    return data,plan


def algorithm_definitions(conditional):
    added=['tightness','width_tightness','load_tightness','width_squared_tightness'] if conditional else []
    definitions=[('constant',[],None),
                 ('linear-width-load',['width','capture_fanout','width_fanout']+added,None),
                 ('linear-log-width-load',['log_width','capture_fanout','log_width_fanout']+added,None),
                 ('quadratic-width-load',['width','width_squared','capture_fanout','width_fanout']+added,None)]
    names=list(FEATURES if conditional else BASE_FEATURES)
    definitions += [(name,names,alpha) for name,alpha in [('ridge-relative-1e-6',1e-6),('ridge-relative-1e-4',1e-4),('ridge-relative-1e-2',1e-2)]]
    definitions.append(('tree-depth-2',names,'tree'))
    return definitions


def train_predictor(rows, field, definition, floor):
    import numpy as np
    from sklearn.linear_model import LinearRegression,Ridge
    from sklearn.tree import DecisionTreeRegressor
    name,names,parameter=definition
    y=np.asarray([r[field] for r in rows]);weights=1/np.maximum(abs(y),floor)**2
    if not names:return {'kind':'linear','features':[],'intercept':float(y.mean()),'coefficients':[]}
    x=np.asarray([[r['features'][n] for n in names] for r in rows])
    if parameter=='tree':
        fitted=DecisionTreeRegressor(max_depth=2,min_samples_leaf=2,random_state=20261103).fit(x,y,sample_weight=weights)
        tree=fitted.tree_;nodes=[]
        for i in range(tree.node_count):
            nodes.append({'value':float(tree.value[i][0][0])} if tree.children_left[i]<0 else
                         {'feature':int(tree.feature[i]),'threshold':float(tree.threshold[i]),
                          'left':int(tree.children_left[i]),'right':int(tree.children_right[i])})
        return {'kind':'tree','features':names,'nodes':nodes}
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    model=LinearRegression() if parameter is None else Ridge(alpha=parameter)
    model.fit((x-mean)/scale,y,sample_weight=weights)
    coefficients=model.coef_/scale
    return {'kind':'linear','features':names,'intercept':float(model.intercept_-np.dot(coefficients,mean)),
            'coefficients':[float(v) for v in coefficients]}


def quantity_quality(actual, predicted, quantity, floor):
    cfg=read(CONFIG);g=cfg['quality_gates'];m=metric(actual,predicted,floor)
    false=sum(p<=y*ratio<y for y,p in zip(actual,predicted) for ratio in cfg['feasibility_ratios']) if quantity=='delay' else 0
    denominator=len(actual)*len(cfg['feasibility_ratios']) if quantity=='delay' else 0
    violation=max(m[k+'_relative_error']/g[quantity+'_'+k+'_relative_error_max'] for k in ('median','p95'))
    if quantity=='delay':violation=max(violation,false/denominator/g['false_feasible_fraction_max'])
    return {'status':'passed' if violation<=1 else 'failed','metrics':m,'false_feasible':false,
            'denominator':denominator,'gate_violation_ratio':violation}


def choose(train, validation, field, quantity, allow_conditional):
    floor=1.5 if quantity=='delay' else 1e-4
    candidates=[]
    for conditional in (False,True) if allow_conditional else (False,):
        fit_rows=train if conditional else [r for r in train if 'absolute-2250' in r['target_roles']]
        if {r['features']['width'] for r in fit_rows}!={8,16,32}:raise ValueError('incomplete fitting width anchors')
        fold_train=[r for r in fit_rows if r['features']['width'] in (8,32)]
        fold_test=[r for r in fit_rows if r['features']['width']==16]
        for definition in algorithm_definitions(conditional):
            predictor=train_predictor(fit_rows,field,definition,floor)
            raw=[infer(predictor,r['features']) for r in validation]
            scale=1.;fold_metrics=None
            if quantity=='delay':
                fold=train_predictor(fold_train,field,definition,floor)
                folded=[infer(fold,r['features']) for r in fold_test]
                scale=max([1.]+[r[field]/max(1e-9,p) for r,p in zip(validation,raw)]
                          +[r[field]/max(1e-9,p) for r,p in zip(fold_test,folded)])*1.05
                fold_metrics=metric([r[field] for r in fold_test],folded,floor)
                fold_metrics.update(scope='new-context coefficient cross-fit; pre-existing training-only reference remains frozen',
                                    withheld_new_context_width=16,unseen_width_claim=False)
            predicted=[p*scale for p in raw]
            q=quantity_quality([r[field] for r in validation],predicted,quantity,floor)
            normalized=q['metrics']['MAE']/max(floor,sum(r[field] for r in validation)/len(validation))
            score=(q['status']!='passed',q['gate_violation_ratio'] if q['status']!='passed' else 0,
                   int(conditional) if q['status']=='passed' else 0, normalized,len(json.dumps(predictor)))
            candidates.append({'score':score,'family':'conditional' if conditional else 'baseline','algorithm':definition[0],
                               'predictor':predictor,'reserve':scale,'validation':q,'crossfit':fold_metrics})
    selected=min(candidates,key=lambda c:c['score'])
    return selected,[{k:v for k,v in c.items() if k not in ('score','predictor')} for c in candidates]


def predictions(entry,row):
    return {'delay_ps':infer(entry['delay'],row['features'])*entry['validation_delay_scale'],
            'comb_area_um2':infer(entry['area'],row['features'])}


def quality(entry, rows):
    pred=[predictions(entry,r) for r in rows]
    d=quantity_quality([r['delay_ps'] for r in rows],[p['delay_ps'] for p in pred],'delay',1.5)
    a=quantity_quality([r['comb_area_um2'] for r in rows],[p['comb_area_um2'] for p in pred],'area',1e-4)
    ratios=read(CONFIG)['feasibility_ratios']
    conservative=sum(r['delay_ps']<=r['delay_ps']*k<p['delay_ps'] for r,p in zip(rows,pred) for k in ratios)
    actual_false=sum(p['delay_ps']<=r['period_ps']-r['observed_H_ps']<r['delay_ps'] for r,p in zip(rows,pred))
    return {'status':'passed' if d['status']==a['status']=='passed' else 'failed','delay':d,'area':a,
            'conservative_rejections':conservative,'actual_target_false_feasible':actual_false,
            'actual_target_denominator':len(rows),'actual_target_scope':'local QD budget using observed H for evaluation only',
            'local_pass_whole_setup_fail':sum(r['path_slack_ps']>=0 and r['whole_setup_slack_ps']<0 for r in rows),
            'predictions':[{'id':r['id'],**p} for r,p in zip(rows,pred)]}


def support_domain(rows):
    groups={}
    for r in rows:groups.setdefault((r['features']['width'],r['features']['capture_fanout']),[]).append(r)
    # A group observed at one loose target does not establish the lower edge of
    # the target axis. The axis is qualified by actual varying-target validation.
    ranges=[min(r['features']['pressure'] for r in values) for values in groups.values()
            if len({r['period_ps'] for r in values})>1]
    if not ranges:raise ValueError('no actual multi-target fitting/validation evidence')
    return {'min_width':8,'max_width':32,'width_multiple':4,'production_capture_fanout':1,
            'reference_pressure_min':max(ranges),'period_max_ps':2250,
            'shape':'equal unsigned native full/low half/quarter complete contiguous legal groups',
            'basis':'width/load training anchors plus complete varying-target validation and preregistered independent load/target test',
            'limitation':'empirical local interval approximation; no complete pipeline or arbitrary stage topology claim'}


def training_sources():
    from .model_target_collection import sources
    return list(dict.fromkeys(sources()+[Path(__file__),Path(__file__).with_name('model_training.py')]))


def fit(data_path,out):
    data,plan=validate_data(data_path)
    if data['mode'] not in ('fitting-baseline','fitting-full') or any(r['split']=='test' for r in data['rows']):
        raise ValueError('fit requires eligible training/validation only')
    out.mkdir(parents=True,exist_ok=False);reference=read(plan['reference_path']);rows=data['rows']
    report={'version':'arithmetic-target-load-fit-report-v1','mode':data['mode'],'stages':{}}
    candidate={'version':read(CONFIG)['model_schema'],'id':'asap7-native-target-load-v1','target_platform':'asap7',
               'platform_profile_sha256':rows[0]['profile_sha256'],'abc_target_ps':1500,'io_policy':'proportional_0.2T',
               'quality_status':'awaiting_independent_test','reference':reference,'stages':{},'max_operations':64,'max_result_bits':4096}
    for stage in ('synth','grt'):
        entries={};details={}
        for name in sorted(reference['intervals']):
            subset=[r for r in rows if r['stage']==stage and r['interval_key']==name]
            train=[r for r in subset if r['split']=='train'];validation=[r for r in subset if r['split']=='validation']
            if {r['features']['width'] for r in validation}!={12,24}:raise ValueError('incomplete validation widths')
            delay,ds=choose(train,validation,'delay_ps','delay',data['mode']=='fitting-full')
            area,ars=choose(train,validation,'comb_area_um2','area',data['mode']=='fitting-full')
            entry={'delay':delay['predictor'],'area':area['predictor'],'validation_delay_scale':delay['reserve'],
                   'delay_family':delay['family'],'area_family':area['family'],'quality_status':'awaiting_independent_test',
                   'domain':support_domain(subset)}
            q=quality(entry,validation);entry['validation_ready']=q['status']=='passed'
            entries[name]=entry;details[name]={'quality':q,'delay_candidates':ds,'area_candidates':ars,
                                            'selected_delay':delay['algorithm'],'selected_area':area['algorithm']}
        ready=all(e['validation_ready'] for e in entries.values())
        candidate['stages'][stage]={'intervals':entries,'quality_status':'awaiting_independent_test','validation_ready':ready}
        report['stages'][stage]={'validation_ready':ready,'intervals':details,
                               'passing_intervals':sum(e['validation_ready'] for e in entries.values()),'interval_count':len(entries)}
    report['all_grt_validation_passed']=candidate['stages']['grt']['validation_ready']
    hashes={}
    for path in training_sources():
        name=path.relative_to(ROOT);target=out/'training-source'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,target);hashes[str(name)]=sha(target)
    environment={'python':sys.version,'numpy':version('numpy'),'sklearn':version('scikit-learn'),'seed':20261103,
                 'threads':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}}
    report['training_environment']=environment
    candidate['measurement_static_identity_sha256']=measurement_identity(data)
    report['measurement_static_identity_sha256']=candidate['measurement_static_identity_sha256']
    write(out/'candidate.json',candidate);write(out/'fit-report.json',report)
    frozen={'version':'arithmetic-target-load-fit-freeze-v1','mode':data['mode'],'plan_path':data['plan_path'],'plan_sha256':data['plan_sha256'],
            'protocol_sha256':sha(CONFIG),'dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),
            'candidate_sha256':sha(out/'candidate.json'),'fit_report_sha256':sha(out/'fit-report.json'),'training_sources':hashes,
            'grt_validation_ready':report['all_grt_validation_passed'],'test_consumed':False}
    write(out/'fit-freeze.json',frozen)
    if report['all_grt_validation_passed']:
        write(out/'selection-freeze.json',{**frozen,'version':'arithmetic-target-load-selection-v1'})
    print(json.dumps({'mode':data['mode'],'stages':{s:{k:v for k,v in q.items() if k!='intervals'} for s,q in report['stages'].items()},
                      'independent_test_released':report['all_grt_validation_passed']},indent=2))


def frozen_fit(path,plan_path):
    if path is None:raise ValueError('frozen fitting decision required')
    path=Path(path);f=read(path);plan=verify_plan(plan_path)
    if f['plan_sha256']!=sha(plan_path) or f['protocol_sha256']!=sha(CONFIG) or f['test_consumed'] is not False:
        raise ValueError('frozen decision does not bind current protocol/plan')
    for name,h in f['training_sources'].items():
        if sha(ROOT/name)!=h or sha(path.parent/'training-source'/name)!=h:raise ValueError('changed frozen fitting source: '+name)
    if (sha(f['dataset_path'])!=f['dataset_sha256'] or sha(path.parent/'candidate.json')!=f['candidate_sha256']
            or sha(path.parent/'fit-report.json')!=f['fit_report_sha256']):raise ValueError('changed frozen data/predictor/validation')
    data=read(f['dataset_path']);candidate=read(path.parent/'candidate.json');report=read(path.parent/'fit-report.json')
    if data['failures'] or data['mode'] not in ('fitting-baseline','fitting-full') or any(r['split']=='test' for r in data['rows']):
        raise ValueError('invalid frozen fitting data role')
    expected=[t['id'] for t in selected_tasks(plan,data['mode'])]
    if expected!=data['expected_task_ids'] or {r['task_id'] for r in data['rows']}!=set(expected):raise ValueError('incomplete frozen fitting phase')
    if {r['id'] for r in data['rows']}!=expected_samples(plan,data['mode']) or len({r['id'] for r in data['rows']})!=len(data['rows']):
        raise ValueError('frozen fitting sample/stage coverage incomplete')
    for stage in ('synth','grt'):
        for name,entry in candidate['stages'][stage]['intervals'].items():
            val=[r for r in data['rows'] if r['stage']==stage and r['interval_key']==name and r['split']=='validation']
            q=quality(entry,val)
            if q!=report['stages'][stage]['intervals'][name]['quality'] or entry['validation_ready']!=(q['status']=='passed'):
                raise ValueError('frozen validation does not recompute')
    return f,candidate,report


def verify_selection(path,plan_path):
    f,candidate,report=frozen_fit(path,plan_path)
    if (f['version']!='arithmetic-target-load-selection-v1' or not f['grt_validation_ready']
            or not report['all_grt_validation_passed'] or len(candidate['stages']['grt']['intervals'])!=42
            or any(not e['validation_ready'] for e in candidate['stages']['grt']['intervals'].values())):
        raise ValueError('all 42 grt intervals must pass frozen validation before test')
    return sha(path)


def verify_screening(path,plan_path):
    f,_,report=frozen_fit(path,plan_path)
    if f['mode']!='fitting-baseline' or report['all_grt_validation_passed']:
        raise ValueError('conditional acquisition requires an insufficient frozen baseline screen')
    return sha(path)


def test_report(data,candidate):
    stages={}
    for stage in ('synth','grt'):
        intervals={}
        for name,entry in candidate['stages'][stage]['intervals'].items():
            rows=[r for r in data['rows'] if r['stage']==stage and r['interval_key']==name]
            if {r['features']['width'] for r in rows}!={20,28} or {r['features']['capture_fanout'] for r in rows}!={2,4}:
                raise ValueError('incomplete new independent width/load coverage')
            intervals[name]=quality(entry,rows)
        all_rows=[r for r in data['rows'] if r['stage']==stage]
        predicted=[predictions(candidate['stages'][stage]['intervals'][r['interval_key']],r) for r in all_rows]
        stages[stage]={'status':'passed' if all(q['status']=='passed' for q in intervals.values()) else 'failed',
                       'passing_intervals':sum(q['status']=='passed' for q in intervals.values()),'intervals':intervals,
                       'delay':metric([r['delay_ps'] for r in all_rows],[p['delay_ps'] for p in predicted],1.5),
                       'area':metric([r['comb_area_um2'] for r in all_rows],[p['comb_area_um2'] for p in predicted],1e-4),
                       'false_feasible':sum(q['delay']['false_feasible'] for q in intervals.values()),
                       'denominator':sum(q['delay']['denominator'] for q in intervals.values()),
                       'actual_target_false_feasible':sum(q['actual_target_false_feasible'] for q in intervals.values()),
                       'actual_target_denominator':len(all_rows)}
        pairs={};rankings=[]
        for r in all_rows:
            spec=r['spec']
            if spec['first']==0 and spec['last']==spec['groups']-1 and any(role.startswith('absolute-') for role in r['target_roles']):
                pairs.setdefault((spec['width'],spec['fanout'],spec['result_shape'],r['period_ps']),{})[spec['configuration']]=r
        for identity,pair in sorted(pairs.items()):
            if set(pair)!={'half','quarter'}:raise ValueError('missing equivalent full-template absolute-target ranking pair')
            a,b=pair['half'],pair['quarter'];pa=predictions(candidate['stages'][stage]['intervals'][a['interval_key']],a);pb=predictions(candidate['stages'][stage]['intervals'][b['interval_key']],b)
            for label in ('delay_ps','comb_area_um2'):
                observed=(a[label]>b[label])-(a[label]<b[label]);predicted=(pa[label]>pb[label])-(pa[label]<pb[label])
                rankings.append({'width':identity[0],'fanout':identity[1],'shape':identity[2],'period_ps':identity[3],'label':label,
                                 'observed_order':observed,'predicted_order':predicted,'matches':observed==predicted})
        stages[stage]['ranking']={'scope':'equivalent complete half/quarter at identical absolute targets and loads; no pipeline state claim',
                                  'matching_pairs':sum(r['matches'] for r in rankings),'denominator':len(rankings),'records':rankings}
    return stages


def evaluate(data_path,selection,out):
    f=read(selection);plan_path=Path(f['plan_path']);verify_selection(selection,plan_path)
    marker=selection.parent/'independent-test-consumption.json'
    if marker.exists() or out.exists():raise ValueError('test already consumed or output exists; use read-only verification')
    exclusive(marker,{'status':'started','selection_sha256':sha(selection),'data_sha256':sha(data_path),'output':str(out.resolve())})
    out.mkdir(parents=True)
    try:
        data,_=validate_data(data_path,selection)
        if data['mode']!='test':raise ValueError('independent test data required')
        candidate=read(selection.parent/'candidate.json');stages=test_report(data,candidate)
        if measurement_identity(data)!=candidate['measurement_static_identity_sha256']:raise ValueError('independent test changed static measurement context')
        result={'version':'arithmetic-target-load-independent-test-v1','selection_path':str(selection.resolve()),'selection_sha256':sha(selection),
                'dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),'stages':stages,
                'quality_status':stages['grt']['status'],'old_failed_test_labels_used':False,
                'independence_claim':read(CONFIG)['independence_claim']}
        write(out/'independent-test.json',result)
        write(marker,{'status':'completed','selection_sha256':sha(selection),'data_sha256':sha(data_path),
                      'result_sha256':sha(out/'independent-test.json'),'output':str(out.resolve())})
        print(json.dumps({'quality_status':result['quality_status'],'stages':{s:{k:v for k,v in r.items() if k!='intervals'} for s,r in stages.items()}}))
    except Exception as error:
        write(marker,{'status':'failed_after_claim','selection_sha256':sha(selection),'error':str(error),'output':str(out.resolve())})
        raise


def verify_test(result_path):
    result=read(result_path);selection=Path(result['selection_path']);f=read(selection)
    verify_selection(selection,Path(f['plan_path']))
    if sha(selection)!=result['selection_sha256'] or sha(result['dataset_path'])!=result['dataset_sha256']:raise ValueError('changed independent inputs')
    data,_=validate_data(Path(result['dataset_path']),selection)
    if measurement_identity(data)!=read(selection.parent/'candidate.json')['measurement_static_identity_sha256']:raise ValueError('changed independent measurement context')
    actual=test_report(data,read(selection.parent/'candidate.json'))
    if actual!=result['stages'] or result['quality_status']!=actual['grt']['status']:raise ValueError('independent quality does not recompute')
    marker=read(selection.parent/'independent-test-consumption.json')
    if marker.get('status')!='completed' or marker['result_sha256']!=sha(result_path):raise ValueError('unbound independent result')
    return result


def publish(result_path,out):
    result=verify_test(result_path);selection=Path(result['selection_path']);out.mkdir(parents=True,exist_ok=False)
    published=[]
    if result['quality_status']=='passed':
        model=read(selection.parent/'candidate.json');model['quality_status']='passed'
        model['stages']={'grt':model['stages']['grt']};model['stages']['grt']['quality_status']='passed'
        for e in model['stages']['grt']['intervals'].values():e['quality_status']='passed'
        model['independent_test_sha256']=sha(result_path);model['full_step7_complete']=False
        model['release_scope']='local native interval costs only; ordinary/state/overhead joint target coverage and full D remain separate'
        write(out/'asap7-interval-target-load.json',model);published.append({'file':'asap7-interval-target-load.json','sha256':sha(out/'asap7-interval-target-load.json')})
    write(out/'release.json',{'version':'arithmetic-target-load-release-v1','independent_test_sha256':sha(result_path),'published':published,'full_step7_complete':False})
    print(json.dumps({'published':published,'full_step7_complete':False}))


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['fit','test','verify','publish','reproduce'])
    parser.add_argument('--data',type=Path);parser.add_argument('--selection',type=Path);parser.add_argument('--result',type=Path);parser.add_argument('--out',type=Path)
    args=parser.parse_args()
    if args.action=='fit':fit(args.data,args.out)
    elif args.action=='test':evaluate(args.data,args.selection,args.out)
    elif args.action=='verify':print(json.dumps({'status':'verified','quality_status':verify_test(args.result)['quality_status']}))
    elif args.action=='publish':publish(args.result,args.out)
    else:
        f=read(args.selection);fit(Path(f['dataset_path']),args.out)
        for name in ('candidate.json','fit-report.json'):
            if (args.out/name).read_bytes()!=(args.selection.parent/name).read_bytes():raise ValueError('refit bytes differ: '+name)
        print('Reproduced identical candidate and fit report using fitting data only')


if __name__=='__main__':main()
