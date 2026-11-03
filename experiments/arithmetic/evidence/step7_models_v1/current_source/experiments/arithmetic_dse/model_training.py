"""Offline fit/validation/export. Test metrics never choose an algorithm.

Only the new collection admission's isolated microbenchmarks are accepted.
Portable files contain fitted numbers/trees and no executable Python objects.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

from .model_collection import PROTOCOL, sha, write
from .model_features import FEATURES, VERSION, features, infer


def dataset(out):
    a=json.loads((out/'admission.json').read_text())
    if a['purpose']!='arithmetic_model_collection' or a['protocol_sha256']!=sha(PROTOCOL):raise ValueError('unregistered model data')
    rows=[];failures=[];contexts={}
    for task in a['tasks']:
        directory=Path(task['reuse_directory']) if task.get('reuse_directory') else out/'runs'/task['id'];manifest=directory/'manifest.json'
        if not manifest.exists():failures.append({'task':task['id'],'status':'not_run'});continue
        m=json.loads(manifest.read_text())
        if task.get('reuse_directory') and sha(manifest)!=task['reuse_manifest_sha256']:raise ValueError('changed inherited label measurement')
        if m['status']!='completed':failures.append({'task':task['id'],'status':'failed','reason':m.get('failure_reason')});continue
        contexts[m['mapping_context_sha256']]=m['mapping_context']
        contract=directory/'sample-contract.json'
        if sha(contract)!=task['sample_contract_sha256'] or sha(directory/'input.sv')!=task['rtl_sha256']:raise ValueError('changed characterization inputs')
        specs={x['id']:x for x in json.loads(contract.read_text())['labels']}
        cells=json.loads((directory/'liberty_cells.json').read_text())['cells']
        for metrics in m['metrics']:
            stage=metrics['stage'];prefix=directory/f'reports/{task["platform"]}/arithmetic_probe/base/vulsim_{stage}'
            # Read every consumed raw instance list, retain identity, and sum
            # nonsequential masters once. Boundary/physical/clock are separate.
            instances=[]
            path=Path(str(prefix)+'_instances.tsv')
            if sha(path)!=m['evidence_sha256'][str(path.relative_to(directory))]:raise ValueError('changed model instance evidence')
            for line in path.read_text().splitlines():
                name,master,*_=line.split('\t');instances.append((name,master))
            for label in metrics['model_labels']:
                spec=specs[label['id']];scope=spec['instance_scope'];area=0.;seq=0.;destinations=0;masters={}
                for name,master in instances:
                    if not name.startswith(scope):continue
                    c=cells.get(master)
                    if c is None:continue # physical-only cells are not a node label
                    masters[master]=masters.get(master,0)+1
                    if c['sequential']:
                        seq+=c['area_um2']
                        if name.startswith(scope+'y') or name.startswith(scope+'dst'):destinations+=1
                    elif name.startswith(spec['arithmetic_scope']):area+=c['area_um2']
                # Duplicate destinations may be merged; such a graph cannot
                # support the nominal fanout feature or independent split.
                expected=spec['fanout']*spec['result_width']
                if destinations!=expected:raise ValueError(f'{task["id"]}/{spec["id"]}: capture fanout mismatch {destinations} != {expected}')
                if area<=0:raise ValueError('missing positive arithmetic area')
                f=features(spec['lhs_width'],spec['rhs_width'],spec['result_width'],spec['fanout'],task['abc_target_ps'],task['period_ps'])
                row={'id':task['id']+'/'+label['id']+'/'+stage,'platform':task['platform'],'stage':stage,'operation':spec['operation'],
                     'result_shape':spec['result_shape'],'split':task['split'],'source_group':task['source_group'],
                     'source_sha256':task['rtl_sha256'],'manifest_sha256':sha(manifest),'contract_sha256':sha(contract),
                     'mapping_context_sha256':m['mapping_context_sha256'],'profile_sha256':task['profile_sha256'],
                     'features':f,'delay_ps':label['data_delay_ps'],'comb_area_um2':area,'sequential_boundary_area_um2':seq,
                     'scope_masters':masters,'instance_list_sha256':sha(path),'path_points_sha256':label['points_sha256'],
                     'boundary_timing':{k:label[k] for k in ('slack_ps','setup_margin_ps','clock_skew_ps','expanded_path_report_sha256') if k in label},
                     'actual_capture_DFFs':destinations,'status':'measured_exact','target_condition':'fixed_ABC_reference__SDC_reference',
                     'label_definition':label['label_definition']}
                rows.append(row)
    if not rows:raise ValueError('no usable measured labels')
    groups={}
    for row in rows:
        key=(row['platform'],row['source_sha256']);split=row['split']
        if key in groups and groups[key]!=split:raise ValueError('same source graph crosses data partitions')
        groups[key]=split
    return {'version':'arithmetic-model-dataset-v1','admission_sha256':sha(out/'admission.json'),
            'protocol_sha256':sha(PROTOCOL),'rows':rows,'failures':failures,'measurement_contexts':contexts,
            'data_role':'isolated registered microbenchmarks; no evaluation/capacity PPA',
            'split_rule':'entire source bundles and all target/stage variants stay together'}


def metric(actual,predicted,floor):
    if len(actual)!=len(predicted) or not actual or not math.isfinite(floor) or floor<=0:raise ValueError('nonempty aligned metrics with positive finite floor required')
    if any(isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) for v in list(actual)+list(predicted)):raise ValueError('finite numeric metric values required')
    errors=[abs(a-b) for a,b in zip(actual,predicted)];relative=sorted(e/max(abs(a),floor) for e,a in zip(errors,actual))
    def quantile(q):
        x=(len(relative)-1)*q;i=int(x);return relative[i]+(relative[min(i+1,len(relative)-1)]-relative[i])*(x-i)
    return {'n':len(actual),'MAE':sum(errors)/len(errors),'median_relative_error':quantile(.5),
            'p95_relative_error':quantile(.95),'max_relative_error':max(relative),
            'relative_error_floor':floor}


def algorithms(train,key,floor):
    import numpy as np
    from sklearn.linear_model import LinearRegression,Ridge
    from sklearn.tree import DecisionTreeRegressor
    y=np.asarray([r[key] for r in train]);result=[]
    names=list(FEATURES)
    def linear_export(model,selected,mean=None,scale=None):
        coefficients=model.coef_ if scale is None else model.coef_/scale
        intercept=float(model.intercept_) if mean is None else float(model.intercept_-np.dot(coefficients,mean))
        return {'kind':'linear','features':selected,'intercept':intercept,'coefficients':[float(v) for v in coefficients]}
    result.append(('constant_per_operation',{'kind':'linear','features':[],'coefficients':[],'intercept':float(np.mean(y))}))
    selected=['lhs_width','rhs_width','result_width','width_product','fanout','width_result_product','retained_product_terms']
    x=np.asarray([[r['features'][k] for k in selected] for r in train]);simple=LinearRegression().fit(x,y)
    result.append(('linear_per_operation',linear_export(simple,selected)))
    x=np.asarray([[r['features'][k] for k in names] for r in train]);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    for alpha in (.01,.1,1.,10.):
        model=Ridge(alpha=alpha).fit((x-mean)/scale,y);result.append((f'ridge_{alpha}',linear_export(model,names,mean,scale)))
    weights=1/np.maximum(np.abs(y),floor)**2;weights*=len(weights)/np.sum(weights)
    model=LinearRegression().fit((x-mean)/scale,y,sample_weight=weights)
    result.append(('relative_weighted_linear',linear_export(model,names,mean,scale)))
    for alpha in (.000001,.0001,.01,.1,1.):
        model=Ridge(alpha=alpha).fit((x-mean)/scale,y,sample_weight=weights);result.append((f'relative_weighted_ridge_{alpha}',linear_export(model,names,mean,scale)))
    for depth in (2,3,4):
        model=DecisionTreeRegressor(max_depth=depth,min_samples_leaf=2,random_state=20261102).fit(x,y);tree=model.tree_;nodes=[]
        for i in range(tree.node_count):
            nodes.append({'value':float(tree.value[i][0][0])} if tree.children_left[i]<0 else
                         {'feature':int(tree.feature[i]),'threshold':float(tree.threshold[i]),'left':int(tree.children_left[i]),'right':int(tree.children_right[i])})
        result.append((f'decision_tree_{depth}',{'kind':'tree','features':names,'nodes':nodes}))
    return result


def fit(rows,key,floor):
    import numpy as np
    train=[r for r in rows if r['split']=='train'];validation=[r for r in rows if r['split']=='validation']
    if not train or not validation:raise ValueError('separate training/validation required')
    candidates=[]
    gates=json.loads(PROTOCOL.read_text())['quality_gates_frozen_before_test'];label='delay' if key=='delay_ps' else 'area'
    for name,predictor in algorithms(train,key,floor):
        values=[infer(predictor,r['features']) for r in validation];m=metric([r[key] for r in validation],values,floor)
        violation=max(m['median_relative_error']/gates[label+'_median_relative_error_max'],m['p95_relative_error']/gates[label+'_p95_relative_error_max'])
        candidates.append({'algorithm':name,'predictor':predictor,'validation':m,
                           'validation_ready':violation<=1,
                           'key':(violation>1,0 if violation<=1 else violation,m['MAE']/max(floor,float(np.mean([r[key] for r in validation]))),m['p95_relative_error'],len(json.dumps(predictor)))})
    chosen=min(candidates,key=lambda c:c['key']);p=chosen['predictor']
    residual=[max(0,r[key]-infer(p,r['features'])) for r in validation]
    margin=float(np.quantile(residual,.95))+floor if key=='delay_ps' else 0.
    return p,margin,{'selected_algorithm':chosen['algorithm'],'candidates':[{k:v for k,v in c.items() if k not in ('predictor','key')} for c in candidates],
                     'validation':chosen['validation'],'validation_ready':chosen['validation_ready'],'margin':margin,'selection_uses_test':False}


def train(data,out):
    """Freeze chosen estimators/margins before the separate test command."""
    out.mkdir(parents=True,exist_ok=False);protocol=json.loads(PROTOCOL.read_text())
    document=json.loads(data.read_text());rows=document['rows'];index=[]
    for platform in sorted({r['platform'] for r in rows}):
        selected=[r for r in rows if r['platform']==platform];ref=protocol['reference_abc_ps'][platform];stages={};reports={}
        for stage in ('synth','grt'):
            subset=[r for r in selected if r['stage']==stage];models={};stage_reports={}
            for operation in sorted({r['operation'] for r in subset}):
                group=[r for r in subset if r['operation']==operation];floor=max(1,ref*.001)
                delay,margin,delay_report=fit(group,'delay_ps',floor);area,_,area_report=fit(group,'comb_area_um2',1e-4)
                conditions=[]
                for r in group:
                    if r['split']=='test':continue
                    f=r['features'];condition={'lhs_min':f['lhs_width'],'lhs_max':f['lhs_width'],'rhs_min':f['rhs_width'],'rhs_max':f['rhs_width'],
                    'result_shape':r['result_shape'],'fanout_max':6,'abc_target_ps':ref,'sdc_min_ps':ref,'sdc_max_ps':ref}
                    if condition not in conditions:conditions.append(condition)
                ready=delay_report['validation_ready'] and area_report['validation_ready']
                models[operation]={'quality_status':'awaiting_independent_test' if ready else 'failed_validation','validation_ready':ready,'delay':delay,'delay_margin_ps':margin,'area':area,'domain':{'conditions':conditions,'known_zero_policy':'none','constant_operand_policy':'dynamic_only'}}
                stage_reports[operation]={'delay':delay_report,'area':area_report,'counts':{s:sum(r['split']==s for r in group) for s in ('train','validation','test')}}
            stages[stage]={'operations':models};reports[stage]=stage_reports
        bundle={'version':'arithmetic-backend-model-v1','id':platform+'-isolated-mul-local-v2','target_platform':platform,
                'platform_profile_sha256':selected[0]['profile_sha256'],'feature_schema':VERSION,'mapping_abc_target_ps':ref,
                'quality_status':'awaiting_independent_test','stages':stages,'dataset_sha256':sha(data),'protocol_sha256':sha(PROTOCOL),
                'measurement_domain':{
                    'complete_contexts_in_dataset_sha256':sha(data),
                    'context_sha256':sorted({r['mapping_context_sha256'] for r in selected}),
                    'identities':[{k:v for k,v in context.items() if k in ('libraries_sha256','tool_binaries_sha256','executed_synth_script_sha256','executed_util_script_sha256','abc_driver_cell','abc_load_fF','corner','VT','liberty_model','tool_thread_controls','io_delay_policy','io_delay_max_ps')}
                                  for context in [document['measurement_contexts'][selected[0]['mapping_context_sha256']]]]},
                'fitting':'independent per-platform fitted coefficients/trees, validation-only algorithm and margin selection',
                'support_status':'isolated node models only; no state/stage-context calibration yet; compiler D not ready'}
        write(out/(platform+'.candidate.json'),bundle);write(out/(platform+'.validation.json'),reports)
        index.append({'platform':platform,'candidate_sha256':sha(out/(platform+'.candidate.json')),'validation_sha256':sha(out/(platform+'.validation.json'))})
    write(out/'selection-freeze.json',{'version':'offline-model-selection-v1','dataset_sha256':sha(data),'protocol_sha256':sha(PROTOCOL),'models':index,
                                      'independent_test_admission_sha256':document.get('independent_test_admission_sha256'),
                                      'test_policy':'exactly one test evaluation for these frozen choices; no tuning from test'})


def test(data,out):
    result_path=out/'independent-test.json'
    if result_path.exists():raise ValueError('test already evaluated; preserve it, never tune/retest in place')
    frozen=json.loads((out/'selection-freeze.json').read_text());d=json.loads(data.read_text());protocol=json.loads(PROTOCOL.read_text())
    same_dataset=frozen['dataset_sha256']==sha(data)
    deferred=(d.get('fitting_dataset_sha256')==frozen['dataset_sha256'] and d.get('admission_sha256')==frozen.get('independent_test_admission_sha256'))
    if not (same_dataset or deferred) or frozen['protocol_sha256']!=sha(PROTOCOL):raise ValueError('changed test or predeclared gates')
    reports=[];gates=protocol['quality_gates_frozen_before_test']
    for item in frozen['models']:
        p=out/(item['platform']+'.candidate.json')
        if sha(p)!=item['candidate_sha256']:raise ValueError('chosen model changed before independent test')
        b=json.loads(p.read_text());platform_ready=True
        for stage,stage_model in b['stages'].items():
            for op,model in stage_model['operations'].items():
                rows=[r for r in d['rows'] if r['platform']==item['platform'] and r['stage']==stage and r['operation']==op and r['split']=='test']
                if not model.get('validation_ready',True):
                    reports.append({'platform':item['platform'],'stage':stage,'operation':op,'status':'failed_validation','independent_test_evaluated':False});platform_ready=False;continue
                metrics={};passed=True
                for name,key,unit in [('delay','delay_ps','ps'),('area','comb_area_um2','um2')]:
                    floor=max(1,b['mapping_abc_target_ps']*.001) if name=='delay' else 1e-4
                    m=metric([r[key] for r in rows],[infer(model[name],r['features']) for r in rows],floor);m['unit']=unit;metrics[name]=m
                    passed &= m['median_relative_error']<=gates[name+'_median_relative_error_max'] and m['p95_relative_error']<=gates[name+'_p95_relative_error_max']
                model['quality_status']='passed' if passed else 'failed';platform_ready &= passed
                reports.append({'platform':item['platform'],'stage':stage,'operation':op,'status':model['quality_status'],'metrics':metrics,
                                'conservative_delay_underpredictions':sum(infer(model['delay'],r['features'])+model['delay_margin_ps']<r['delay_ps'] for r in rows),
                                'coverage_denominator':len(rows)})
        # Even good isolated errors cannot grant unmeasured stage/state coverage.
        b['quality_status']='isolated_labels_passed' if platform_ready else 'failed'
        write(out/(item['platform']+'.tested.json'),b)
    write(result_path,{'version':'offline-model-independent-test-v1','selection_freeze_sha256':sha(out/'selection-freeze.json'),'reports':reports,
                      'full_D_ready':False,'remaining':['state/reset/enable/clock fixtures','independent synthetic stage validation','D functional/placement/native parity']})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['extract','train','test']);ap.add_argument('--data',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
    if args.action=='extract':write(args.out,dataset(args.data))
    elif args.action=='train':train(args.data,args.out)
    else:test(args.data,args.out)


if __name__=='__main__':main()
