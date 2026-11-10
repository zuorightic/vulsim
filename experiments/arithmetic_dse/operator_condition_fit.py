"""Train/validation-only condition fitting, immutable selection, one test eval."""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
from importlib.metadata import version
import json
import math
from pathlib import Path
from statistics import median
import sys

from .model_fast_preflight import read,write,sha,key
from . import operator_collection as collect
from . import operator_condition_model as model
from . import model_three_region_scan as scan

ROOT=Path(__file__).resolve().parents[2]
CONFIG=ROOT/'experiments/arithmetic_dse/configs/operator_condition_fit_v1.json'
FEATURE_CONFIG=ROOT/'experiments/arithmetic_dse/configs/operator_condition_features_v1.json'


def extract(root,out,mode='fitting',selection=None):
    from regression.arithmetic_physical_label_contract import packet
    from . import model_qualification_labels as labels
    from .model_mapped_contract import mapped_contract,operator_port_contract
    from .model_m2_live_cec_v3 import verify_proof
    corpus=root/'corpus';m=read(corpus/'manifest.json');roles=('train','validation') if mode=='fitting' else ('locked_test',)
    if mode!='fitting':
        if selection is None:raise ValueError('selection freeze required before test extract')
        freeze=read(selection)
        if freeze['source_manifest_sha256']!=sha(corpus/'manifest.json') or not freeze['validation_passed']:raise ValueError('wrong independent selection freeze')
    rows=[];coverage=[];failures=[];contexts={}
    for source in m['sources']:
        if source['role'] not in roles:continue
        state=root/'raw'/source['id'];history=read(state/'history.json') if (state/'history.json').exists() else []
        decision=collect.next_request(corpus,source['id'],history,selection)['decision']
        if decision['next_request'] is not None:raise ValueError('source bounded scan incomplete '+source['id'])
        coverage.append(dict(source_id=source['id'],role=source['role'],operation=source['features']['producer']['operation'],
            lhs_width=source['features']['producer']['lhs_width'],rhs_width=source['features']['producer']['rhs_width'],result_width=source['features']['producer']['result_width'],
            consumer_count=len(source['features']['consumers']),regions=decision['regions'],stop_reason=decision['stop_reason'],coverage_shortfall=decision['coverage_shortfall']))
        for point in history:
            if point.get('source_id')!=source['id'] or point.get('role')!=source['role']:
                raise ValueError('history source/role mismatch')
            if point['status']=='failed':failures.append(dict(point,source_id=source['id']));continue
            folder=state/('target-'+str(point['SDC_ps']))/'runs'/(source['id']+'-T'+str(point['SDC_ps']))
            if sha(folder/'grt-labels.json')!=point['implementation_id']:raise ValueError('completed measurement label changed')
            pins=read(folder/'liberty-pins.json');design=read(folder/'mapped.json')
            if mapped_contract(design,source['features'],pins)!=read(folder/'mapped-contract.json'):raise ValueError('mapped FF/bank proof differs')
            if operator_port_contract(design,source['features'],pins)!=read(folder/'operator-port-contract.json'):raise ValueError('mapped ports differ')
            suffix=Path('asap7/arithmetic_probe/base');verify_proof(folder/'logs'/suffix/'structural_cec/proof.json',folder/'results'/suffix/'4_before_rsz_lec.v',folder/'results'/suffix/'4_after_rsz_lec.v')
            manifest=read(folder/'manifest.json');context={k:manifest.get(k) for k in ('tools','libraries','platform_profile_sha256','platform')};contexts[key(context)]=context
            for stage in ('synth','grt'):
                raw,c=packet(folder,stage);actual=labels.extract(raw,c['nodes'],c['banks']);saved=read(folder/(stage+'-labels.json'))
                if any(saved[k]!=v for k,v in actual.items() if k!='physical_training_label_eligible'):raise ValueError('actual physical labels differ')
                if saved['source_role']!=source['role'] or not saved['physical_training_label_eligible']:raise ValueError('physical row role mismatch')
                descriptor=collect.descriptor(source,point['SDC_ps']);f=model.features(descriptor)
                rows.append(dict(id=source['id']+'/T'+str(point['SDC_ps'])+'/'+stage,source_id=source['id'],source_group=source['source_group'],role=source['role'],
                    operation=source['features']['producer']['operation'],stage=stage,target_ps=point['SDC_ps'],features=f,descriptor=descriptor,
                    operator_delay_ps=actual['operator_delay_ps'],comb_area_um2=actual['comb_area_um2'],data_setup_slack_ps=actual['data_setup_slack_ps'],
                    label_sha256=sha(folder/(stage+'-labels.json')),measurement_path=str(folder),immutable_role_verified=True))
    result=dict(version='operator-conditional-dataset-v1',mode=mode,collection_root=str(root),source_manifest_sha256=sha(corpus/'manifest.json'),
        protocol_sha256=sha(corpus/'protocol.json'),fit_protocol_sha256=sha(CONFIG),feature_protocol_sha256=sha(FEATURE_CONFIG),
        feature_producer_sha256=sha(Path(model.__file__)),rows=rows,coverage=coverage,failures=failures,measurement_contexts=contexts,
        data_role='formal complete-source grouping; diagnostics/old consumed test excluded',raw_labels_replayed=True,independent_labels_read=mode!='fitting')
    write(out,result);print(json.dumps(dict(status='extracted',rows=len(rows),sources=len(coverage),failures=len(failures),mode=mode)),flush=True)
    return result


def validate_snapshot(data,mode):
    """Bind fit/test rows back to immutable roles and saved qualified labels."""
    root=Path(data['collection_root']);corpus=root/'corpus';manifest=read(corpus/'manifest.json');sources={r['id']:r for r in manifest['sources']}
    if (data['mode']!=mode or data['source_manifest_sha256']!=sha(corpus/'manifest.json')
            or data['protocol_sha256']!=sha(corpus/'protocol.json') or data['feature_producer_sha256']!=sha(Path(model.__file__))):
        raise ValueError('dataset snapshot identity mismatch')
    roles=('train','validation') if mode=='fitting' else ('locked_test',);seen=set();expected=set()
    declared={r['id'] for r in manifest['sources'] if r['role'] in roles}
    if len(data['coverage'])!=len(declared) or {r['source_id'] for r in data['coverage']}!=declared:
        raise ValueError('dataset declared source coverage differs')
    for source in manifest['sources']:
        if source['role'] not in roles:continue
        history=read(root/'raw'/source['id']/'history.json')
        for point in history:
            if point['status']=='completed':
                for stage in ('synth','grt'):expected.add(source['id']+'/T'+str(point['SDC_ps'])+'/'+stage)
    for row in data['rows']:
        source=sources[row['source_id']]
        if row['id'] in seen or row['role'] not in roles or source['role']!=row['role'] or source['source_group']!=row['source_group']:raise ValueError('dataset source-role leak or duplicate')
        seen.add(row['id']);label_path=Path(row['measurement_path'])/(row['stage']+'-labels.json');label=read(label_path)
        if sha(label_path)!=row['label_sha256'] or not label['physical_training_label_eligible'] or label['source_role']!=row['role']:raise ValueError('dataset physical label mismatch')
        for key in ('operator_delay_ps','comb_area_um2','data_setup_slack_ps'):
            if row[key]!=label[key]:raise ValueError('dataset numerical label tampered')
        descriptor=collect.descriptor(source,row['target_ps'])
        if descriptor!=row['descriptor'] or model.features(descriptor)!=row['features']:raise ValueError('dataset feature/descriptor mismatch')
    if seen!=expected:raise ValueError('dataset complete measured source/target/stage coverage differs')


def weights(rows,field,floor):
    import numpy as np
    counts=Counter(r['source_id'] for r in rows);y=np.asarray([r[field] for r in rows]);base=np.asarray([1/counts[r['source_id']] for r in rows])
    w=base/np.maximum(abs(y),floor)**2;return w*len(counts)/sum(w)


def ridge(rows,field,names,alpha,floor):
    import numpy as np
    from sklearn.linear_model import Ridge
    y=np.asarray([r[field] for r in rows]);w=weights(rows,field,floor)
    if not names:
        counts=Counter(r['source_id'] for r in rows);base=np.asarray([1/counts[r['source_id']] for r in rows])
        return dict(kind='linear',features=[],coefficients=[],intercept=float(np.average(y,weights=base)))
    x=np.asarray([[r['features'][n] for n in names] for r in rows]);mean=np.average(x,axis=0,weights=w);scale=np.sqrt(np.average((x-mean)**2,axis=0,weights=w));scale[scale==0]=1
    fitted=Ridge(alpha=alpha).fit((x-mean)/scale,y,sample_weight=w);c=fitted.coef_/scale
    return dict(kind='linear',features=names,coefficients=[float(v) for v in c],intercept=float(fitted.intercept_-np.dot(c,mean)))


def candidates(rows,field,names,floor):
    from sklearn.tree import DecisionTreeRegressor
    import numpy as np
    protocol=read(CONFIG);result=[('constant',ridge(rows,field,[],1,floor))]
    for alpha in protocol['ridge_alpha']:result.append(('ridge-'+str(alpha),ridge(rows,field,names,alpha,floor)))
    coordinates=sorted(r['features']['log2_target_ps'] for r in rows)
    for count in protocol['piecewise_ridge']['knots']:
        knots=sorted(set(coordinates[max(0,math.ceil(len(coordinates)*j/(count+1))-1)] for j in range(1,count+1)))
        bins=[[r for r in rows if sum(r['features']['log2_target_ps']>k for k in knots)==i] for i in range(len(knots)+1)]
        if any(len({r['source_id'] for r in b})<3 for b in bins):continue
        for alpha in protocol['ridge_alpha']:result.append(('segmented-'+str(count)+'-'+str(alpha),dict(kind='segmented',knots=knots,segments=[ridge(b,field,names,alpha,floor) for b in bins])))
    x=np.asarray([[r['features'][n] for n in names] for r in rows]);y=np.asarray([r[field] for r in rows]);w=weights(rows,field,floor)
    for depth in protocol['shallow_tree']['depth']:
        estimator=DecisionTreeRegressor(max_depth=depth,min_samples_leaf=3,random_state=20261109).fit(x,y,sample_weight=w);tree=estimator.tree_;nodes=[]
        def visit(at,indices):
            here=len(nodes);nodes.append({});left=tree.children_left[at]
            if left<0:nodes[here]=dict(value=float(tree.value[at][0][0]));return here
            feature=tree.feature[at];threshold=float(tree.threshold[at]);a=[i for i in indices if x[i,feature]<=threshold];b=[i for i in indices if x[i,feature]>threshold]
            if min(len({rows[i]['source_id'] for i in child}) for child in (a,b))<3:
                nodes[here]=dict(value=float(np.average(y[indices],weights=w[indices])));return here
            li=visit(left,a);ri=visit(tree.children_right[at],b);nodes[here]=dict(feature=names[feature],threshold=threshold,left=li,right=ri);return here
        visit(0,list(range(len(rows))));result.append(('tree-'+str(depth),dict(kind='tree',features=names,nodes=nodes)))
    return result


def metrics(rows,predictor,field,floor):
    by_source=defaultdict(list);absolute=[]
    for row in rows:
        predicted=model.infer(predictor,row['features']);error=abs(predicted-row[field]);by_source[row['source_id']].append(error/max(abs(row[field]),floor));absolute.append(error)
    medians=sorted(median(v) for v in by_source.values())
    if not medians:
        return dict(sources=0,rows=0,source_macro_median=None,source_macro_P95=None,
            source_macro_normalized_absolute_error=None,raw_MAE=None,passed=False)
    q=lambda p:medians[max(0,math.ceil(len(medians)*p)-1)]
    macro_median,p95=q(.5),q(.95)
    return dict(sources=len(medians),rows=len(rows),source_macro_median=macro_median,source_macro_P95=p95,
        source_macro_normalized_absolute_error=sum(sum(v)/len(v) for v in by_source.values())/len(by_source),
        raw_MAE=sum(absolute)/len(absolute),passed=macro_median<=.15 and p95<=.35 and p95<=.5)


def choose(train,validation,field,names,floor):
    trials=[]
    for index,(name,predictor) in enumerate(candidates(train,field,names,floor)):
        quality=metrics(validation,predictor,field,floor);complexity=len(json.dumps(predictor));
        score=(not quality['passed'],quality['source_macro_normalized_absolute_error'],complexity,index)
        trials.append(dict(name=name,predictor=predictor,quality=quality,score=score))
    selected=min(trials,key=lambda r:r['score'])
    # Optional preregistered width groups remain parameter functions. Try them
    # only when the shared function fails, with independent source-count gates.
    if not selected['quality']['passed']:
        groups={};valid=True
        for group,small in [('small',True),('large',False)]:
            tr=[r for r in train if (max(r['features']['lhs_width'],r['features']['rhs_width'])<=16)==small]
            va=[r for r in validation if (max(r['features']['lhs_width'],r['features']['rhs_width'])<=16)==small]
            if len({r['source_id'] for r in tr})<3 or len({r['source_id'] for r in va})<2:valid=False;break
            best=[]
            for index,(name,predictor) in enumerate(candidates(tr,field,names,floor)):
                q=metrics(va,predictor,field,floor);best.append((not q['passed'],q['source_macro_normalized_absolute_error'],len(json.dumps(predictor)),index,predictor))
            groups[group]=min(best,key=lambda item:item[:4])[-1]
        if valid:
            predictor=dict(kind='width_grouped',split=16,groups=groups);q=metrics(validation,predictor,field,floor)
            item=dict(name='validated-width-groups-16',predictor=predictor,quality=q,score=(not q['passed'],q['source_macro_normalized_absolute_error'],len(json.dumps(predictor)),len(trials)))
            trials.append(item);selected=min(trials,key=lambda r:r['score'])
    return selected,[{k:v for k,v in r.items() if k!='score'} for r in trials]


def fit(data_path,out):
    data=read(data_path)
    if data['mode']!='fitting' or data['fit_protocol_sha256']!=sha(CONFIG) or data['feature_protocol_sha256']!=sha(FEATURE_CONFIG) or data['independent_labels_read']:raise ValueError('fit data role/protocol mismatch')
    validate_snapshot(data,'fitting')
    out.mkdir(parents=True,exist_ok=False);root=Path(data['collection_root']);protocol=read(root/'corpus/protocol.json');rows=[r for r in data['rows'] if r['stage']=='grt']
    excluded=set(protocol['feature_schema']['excluded_from_operator_predictor']);ops={};report={};schema=sorted(set(rows[0]['features'])-excluded)
    for op in sorted({r['operation'] for r in rows}):
        group=[r for r in rows if r['operation']==op];train=[r for r in group if r['role']=='train'];valid=[r for r in group if r['role']=='validation']
        if len({r['source_id'] for r in train})<3 or len({r['source_id'] for r in valid})<2:raise ValueError('insufficient source groups '+op)
        names=[n for n in schema if len({r['features'][n] for r in train})>1]
        d,ds=choose(train,valid,'operator_delay_ps',names,10);a,ars=choose(train,valid,'comb_area_um2',names,.01)
        ready=d['quality']['passed'] and a['quality']['passed']
        # Intrinsic numeric interpolation is bounded by training. The local
        # consumer family is selected/checked on validation as permitted by
        # the frozen protocol, rather than turning an unseen wiring ID into
        # an automatic rejection. It allows the preregistered one-bit pad.
        support_names=['lhs_width','rhs_width','result_width','target_period_ps','lhs_zero_count','rhs_zero_count']
        domain={n:[min(r['features'][n] for r in train),max(r['features'][n] for r in train)] for n in support_names}
        domain['target_period_ps']=[min(r['features']['target_period_ps'] for r in group),max(r['features']['target_period_ps'] for r in group)]
        outside=[r['id'] for r in valid if any(not bounds[0]<=r['features'][n]<=bounds[1] for n,bounds in domain.items())]
        ready=ready and not outside
        ops[op]=dict(status='awaiting_independent' if ready else 'failed_validation',delay=d['predictor'],area=a['predictor'],
            delay_reserve_ps=max([0.]+[r['operator_delay_ps']-model.infer(d['predictor'],r['features']) for r in valid]),
            domain=dict(numeric_support=domain,local_load_family='direct capture or one Add consumer no wider than demanded result plus one bit; at most two capture banks',
                load_family_validation_source_count=len({r['source_id'] for r in valid if r['features']['consumer_count']}),
                semantics='unsigned-modulo-v1; dynamic/known-zero inputs; zero carry; no exact-shape whitelist'),validation_ready=ready)
        # Joint width/shape/load/clock support prevents the independent numeric
        # min/max checks from granting an unmeasured Cartesian product.
        distance_names=['lhs_width','rhs_width','result_width','lhs_zero_count','rhs_zero_count','consumer_count','capture_banks']
        scales=[max(1.,max(r['features'][n] for r in train)-min(r['features'][n] for r in train)) for n in distance_names]
        anchors=[]
        training_vectors=[]
        for sid in sorted({r['source_id'] for r in group}):
            local=[r for r in group if r['source_id']==sid];f=local[0]['features'];reference=dict(f);reference.update(target_period_ps=1500.,abc_target_ps=1500.,log2_target_ps=math.log2(1500.))
            ref=max(10.,model.infer(d['predictor'],reference));pressures=[r['target_ps']/ref for r in local]
            anchors.append(dict(vector=[f[n] for n in distance_names],clock_ratio_min=min(pressures),clock_ratio_max=max(pressures)))
            if local[0]['role']=='train':training_vectors.append(anchors[-1]['vector'])
        k=min(3,len(training_vectors));radius=0.
        for r in valid:
            distances=sorted(math.sqrt(sum(((r['features'][n]-v)/scale)**2 for n,v,scale in zip(distance_names,vector,scales,strict=True))) for vector in training_vectors)
            radius=max(radius,distances[k-1])
        joint=dict(features=distance_names,scales=scales,k=k,radius=radius,reference_target_ps=1500.,reference_floor_ps=10.,anchors=anchors,
            basis='fit/validation semantic and requested-clock support witnesses; training-only coefficients; validation-to-train neighborhood radius; anchors contain no measured delay/area prices or source-ID lookup')
        ops[op]['domain']['joint_support']=joint
        joint_missing=[r['id'] for r in valid if not model.joint_covered(ops[op],r['features'])]
        if joint_missing:ops[op].update(status='failed_validation',validation_ready=False)
        report[op]=dict(delay=d['quality'],area=a['quality'],selected_delay=d['name'],selected_area=a['name'],delay_candidates=ds,area_candidates=ars,
            source_counts=dict(train=len({r['source_id'] for r in train}),validation=len({r['source_id'] for r in valid})),
            validation_outside_train_support=outside)
        report[op]['validation_outside_joint_support']=joint_missing
    candidate=dict(version=model.VERSION,profile_sha256=read(root/'corpus/manifest.json')['profile_sha256'],operator_boundary_policy='unsigned-op-hierarchy-v1',
        quality_status='awaiting_independent' if all(v['validation_ready'] for v in ops.values()) else 'failed_validation',operations=ops,
        fit_dataset_sha256=sha(data_path),fit_protocol_sha256=sha(CONFIG),feature_protocol_sha256=sha(FEATURE_CONFIG),source_manifest_sha256=data['source_manifest_sha256'],full_D_ready=False)
    # Mandatory attribution calibration is global over operations, train only.
    fixed=read(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json');train=[r for r in rows if r['role']=='train'];counts=Counter(r['source_id'] for r in train)
    def proxy(row,field):
        if row['operation']=='add':return 1.
        width=max(row['features']['lhs_width'],row['features']['rhs_width']);bucket=next(b for b in fixed['width_buckets'] if b>=width)
        return float(fixed['operations']['Mul']['delay_weight' if field=='operator_delay_ps' else 'comb_weight'][str(bucket)])
    alpha={}
    for field in ('operator_delay_ps','comb_area_um2'):
        numerator=sum(proxy(r,field)*r[field]/counts[r['source_id']] for r in train);denominator=sum(proxy(r,field)**2/counts[r['source_id']] for r in train)
        alpha[field]=max(0,numerator/denominator)
    write(out/'candidate.json',candidate);write(out/'validation.json',dict(status='passed' if candidate['quality_status']=='awaiting_independent' else 'failed',
        model_sha256=sha(out/'candidate.json'),source_manifest_sha256=data['source_manifest_sha256'],operations=report))
    write(out/'static-unit-bridge.json',dict(version='fixed-cost-global-unit-bridge-v1',train_only=True,source_equal=True,
        fixed_table_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/fixed_op_width_v1.json'),alpha=alpha,fit_dataset_sha256=sha(data_path)))
    frozen=dict(version='operator-condition-selection-freeze-v1',validation_passed=candidate['quality_status']=='awaiting_independent',
        source_manifest_sha256=data['source_manifest_sha256'],model_path='candidate.json',model_sha256=sha(out/'candidate.json'),validation_path='validation.json',
        validation_sha256=sha(out/'validation.json'),fit_dataset_sha256=sha(data_path),fit_protocol_sha256=sha(CONFIG),test_consumed=False,
        implementation_sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),Path(model.__file__),CONFIG,FEATURE_CONFIG,
            ROOT/'rtlzz/src/backend/arithmetic_condition.cpp',ROOT/'rtlzz/src/backend/arithmetic_condition.hpp',
            ROOT/'rtlzz/src/backend/arithmetic_operator_query.cpp',ROOT/'rtlzz/src/backend/arithmetic_operator_query.hpp',
            Path(collect.operator_query.__file__),ROOT/'rtlzz/testv2/operator_condition_infer.cpp',ROOT/'regression/arithmetic_condition_model.py')})
    write(out/'selection-freeze.json',frozen);print(json.dumps(dict(status=candidate['quality_status'],operations={op:{k:v for k,v in r.items() if k in ('delay','area','selected_delay','selected_area','source_counts')} for op,r in report.items()})),flush=True)


def test(data_path,selection,out):
    freeze=read(selection);folder=selection.parent;data=read(data_path)
    root=Path(data['collection_root']);consumed=root/'independent-evaluation-consumed.json'
    if consumed.exists() or (out/'test-consumed.json').exists():raise ValueError('test already consumed')
    if (not freeze['validation_passed'] or sha(folder/'candidate.json')!=freeze['model_sha256']
            or sha(folder/'validation.json')!=freeze['validation_sha256'] or data['mode']!='independent'
            or sha(root/'fit-data.json')!=freeze['fit_dataset_sha256']):raise ValueError('independent selection mismatch')
    validate_snapshot(data,'independent')
    for name,h in freeze['implementation_sources'].items():
        if sha(ROOT/name)!=h:raise ValueError('frozen fitting/inference implementation drift')
    out.mkdir(parents=True,exist_ok=False)
    candidate=read(folder/'candidate.json');rows=[r for r in data['rows'] if r['stage']=='grt'];report={}
    for op,entry in candidate['operations'].items():
        group=[r for r in rows if r['operation']==op]
        d=metrics(group,entry['delay'],'operator_delay_ps',10);a=metrics(group,entry['area'],'comb_area_um2',.01)
        missing=[r['id'] for r in group if model.query(candidate,r['descriptor'],True)['status']!='covered']
        fit=read(Path(data['collection_root'])/'fit-data.json');fit_targets={r['target_ps'] for r in fit['rows'] if r['operation']==op}
        train_targets=[r['target_ps'] for r in fit['rows'] if r['operation']==op and r['role']=='train']
        new_targets=[r['target_ps'] for r in group if r['target_ps'] not in fit_targets and min(train_targets)<=r['target_ps']<=max(train_targets)]
        expected_sources={r['source_id'] for r in data['coverage'] if r['operation']==op}
        acquisition_failed=any(failure['source_id'] in expected_sources for failure in data['failures'])
        passed=(d['passed'] and a['passed'] and len({r['source_id'] for r in group})>=2 and bool(new_targets) and not missing
            and not acquisition_failed and {r['source_id'] for r in group}==expected_sources)
        report[op]=dict(status='passed' if passed else 'failed',delay=d,area=a,uncovered=missing,unseen_exact_in_range_targets=sorted(set(new_targets)),
            reserved_underpredictions=sum(model.infer(entry['delay'],r['features'])+entry['delay_reserve_ps']<r['operator_delay_ps'] for r in group))
        entry['status']='passed_independent' if passed else 'failed_independent'
    candidate['quality_status']='isolated_functions_passed' if all(r['status']=='passed' for r in report.values()) else 'failed_independent'
    write(out/'tested-model.json',candidate);write(out/'independent-test.json',dict(status=candidate['quality_status'],operations=report,model_sha256=freeze['model_sha256'],full_D_ready=False))
    write(out/'test-consumed.json',dict(version='operator-condition-test-consumed-v1',selection_sha256=sha(selection),dataset_sha256=sha(data_path),
        label_rows=len(rows),permanently_excluded_from_future_fitting_or_selection=True))
    # Create the collection-level single-consumption marker only after all
    # validation and report writes succeed. A second output directory cannot
    # bypass this frozen independent-evaluation contract.
    with consumed.open('x') as stream:
        json.dump(dict(selection_sha256=sha(selection),dataset_sha256=sha(data_path),output=str(out),
            permanently_excluded_from_future_fitting_or_selection=True),stream,indent=2)
        stream.write('\n')
    print(json.dumps(read(out/'independent-test.json')),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('extract','fit','test'));p.add_argument('--root',type=Path);p.add_argument('--data',type=Path);p.add_argument('--out',type=Path,required=True)
    p.add_argument('--mode',choices=('fitting','independent'),default='fitting');p.add_argument('--selection',type=Path);a=p.parse_args()
    if a.action=='extract':extract(a.root.resolve(),a.out.resolve(),a.mode,a.selection.resolve() if a.selection else None)
    elif a.action=='fit':fit(a.data.resolve(),a.out.resolve())
    else:test(a.data.resolve(),a.selection.resolve(),a.out.resolve())
