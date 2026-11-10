"""Cross-language local condition inference and guarded model contract tests."""
import argparse
from copy import deepcopy
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import operator_collection as collect
from experiments.arithmetic_dse import operator_condition_model as inference


def fixture_predictors():
    linear=dict(kind='linear',features=['lhs_width','width_product','width_result_product','target_period_ps'],coefficients=[2.,.1,.01,-.001],intercept=12.)
    return [linear,dict(kind='segmented',knots=[math.log2(500),math.log2(1500)],segments=[linear,{**linear,'intercept':22.},{**linear,'intercept':35.}]),
        dict(kind='tree',features=['lhs_width','target_period_ps'],nodes=[dict(feature='lhs_width',threshold=20.,left=1,right=2),dict(value=25.),dict(feature='target_period_ps',threshold=1000.,left=3,right=4),dict(value=90.),dict(value=110.)]),
        dict(kind='width_grouped',split=16,groups=dict(small=linear,large=dict(kind='segmented',knots=[math.log2(500)],segments=[linear,{**linear,'intercept':22.}])))]


def prepare(root,out,candidate=None,data=None):
    out.mkdir(parents=True,exist_ok=False);m=read(root/'corpus/manifest.json');queries=[]
    if candidate:
        bundle=read(candidate)
        for row in read(data)['rows']:
            if row['stage']=='grt':queries.append(dict(descriptor=row['descriptor'],allow_candidate=True))
        bundles=[bundle]
    else:
        bundle=dict(version=inference.VERSION,profile_sha256=m['profile_sha256'],operator_boundary_policy='unsigned-op-hierarchy-v1',operations={})
        for op in ('add','mul'):
            bundle['operations'][op]=dict(status='awaiting_independent',delay_reserve_ps=15.,domain=dict(numeric_support={'lhs_width':[1,67],'rhs_width':[1,67],'result_width':[1,65],'target_period_ps':[25,12000]}))
        bundles=[]
        for predictor in fixture_predictors():
            b=deepcopy(bundle)
            for entry in b['operations'].values():entry.update(delay=predictor,area=predictor)
            bundles.append(b)
        for row in m['sources']:
            for target in (250,500,1373,1500,2000):queries.append(dict(descriptor=collect.descriptor(row,target),allow_candidate=True))
        # A bounded joint support fixture exercises neighborhood distance,
        # stable equal-distance ordering and the inferred reference-clock
        # ratio. No physical labels or per-source prices enter this fixture.
        b=deepcopy(bundles[0])
        for op,entry in b['operations'].items():
            names=['lhs_width','rhs_width','result_width','consumer_count','capture_banks']
            anchors=[]
            for row in m['sources']:
                if row['features']['producer']['operation']!=op:continue
                f=inference.features(collect.descriptor(row,1500))
                anchors.append(dict(vector=[f[n] for n in names],clock_ratio_min=1.,clock_ratio_max=10.))
            entry['domain']['joint_support']=dict(features=names,scales=[32.,32.,64.,1.,2.],k=3,radius=.75,
                reference_target_ps=1500.,reference_floor_ps=10.,anchors=anchors)
        bundles.append(b)
    negative=[]
    base=deepcopy(queries[0]);base['allow_candidate']=False;negative.append(base)
    base=deepcopy(queries[0]);base['descriptor']['flow_context']['target_period_ps']=0;negative.append(base)
    base=deepcopy(queries[0]);base['descriptor']['flow_context']['boundary_policy']='incompatible';negative.append(base)
    base=deepcopy(queries[0]);base['descriptor']['slack_ps']=1;negative.append(base)
    base=deepcopy(queries[0]);base['descriptor']['local_context']['producer']['operation']='div';negative.append(base)
    base=deepcopy(queries[0]);base['descriptor']['flow_context']['abc_target_ps']+=1;negative.append(base)
    base=deepcopy(queries[0]);p=base['descriptor']['local_context']['producer'];p['lhs_zero_hex']='0x4';p['lhs_one_hex']='0x0';negative.append(base)
    for index,b in enumerate(bundles):write(out/('input-'+str(index)+'.json'),dict(model=b,queries=queries+negative))
    write(out/'manifest.json',dict(inputs=len(bundles),queries_per_input=len(queries)+len(negative),negative_controls=len(negative),
        actual_candidate=bool(candidate),producer_sha256=sha(Path(inference.__file__))))
    print(read(out/'manifest.json'),flush=True)


def verify(folder,out):
    m=read(folder/'manifest.json');total=covered=0
    for index in range(m['inputs']):
        inputs=read(folder/('input-'+str(index)+'.json'));native=read(folder/('output-'+str(index)+'.json'))
        if len(native)!=len(inputs['queries']):raise ValueError('incomplete native inference')
        for query,answer in zip(inputs['queries'],native,strict=True):
            python=inference.query(inputs['model'],query['descriptor'],query['allow_candidate']);total+=1
            if answer['status']!=python['status']:raise ValueError('native/Python coverage mismatch')
            if python['status']=='covered':
                covered+=1
                for key in ('operator_delay_ps','delay_reserve_ps','conservative_operator_delay_ps','comb_area_um2'):
                    if not math.isclose(answer[key],python[key],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('native/Python numerical mismatch '+key)
        if any(v['status']!='cost_uncovered' for v in native[-m['negative_controls']:]):raise ValueError('negative condition query accepted')
    out.mkdir(parents=True,exist_ok=False);write(out/'proof.json',dict(status='passed',queries=total,covered=covered,negative_controls=m['negative_controls']*m['inputs'],
        actual_frozen_candidate=m['actual_candidate'],new_EDA_calls=0,full_D_ready=False))
    print(read(out/'proof.json'),flush=True)


def fit_preflight(out):
    """Check source-macro statistics against explicit, unbalanced examples."""
    from experiments.arithmetic_dse.operator_condition_fit import metrics,weights,candidates
    predictor=dict(kind='linear',features=[],coefficients=[],intercept=100.)
    rows=[]
    # Unequal targets per source must not let source A dominate the report.
    for sid, labels in [('A',[100.]*13),('B',[80.,100.]),('C',[50.])]:
        rows += [dict(source_id=sid,features={},operator_delay_ps=v) for v in labels]
    result=metrics(rows,predictor,'operator_delay_ps',10.)
    if result['sources']!=3 or not math.isclose(result['source_macro_median'],.125) or result['source_macro_P95']!=1. or result['passed']:
        raise ValueError('source-macro median/P95 does not match hand calculation')
    if not math.isclose(result['source_macro_normalized_absolute_error'],.375):
        raise ValueError('source-equal score does not match hand calculation')
    w=weights(rows,'operator_delay_ps',10.)
    if not math.isclose(float(sum(w)),3.) or any(not math.isfinite(float(v)) or v<=0 for v in w):
        raise ValueError('invalid source-normalized fitting weights')
    # A new-width/new-clock analytical fixture checks fit/export, without any
    # real training or held-out physical label. The supplied formula is known
    # independently of the estimator and must survive coefficient export.
    def example(sid,width,target):
        return dict(source_id=sid,features=dict(lhs_width=width,target_period_ps=target,log2_target_ps=math.log2(target)),
            operator_delay_ps=5.+2.*width+.001*target)
    train=[example('train'+str(w),w,t) for w in (8,12,16,20,24,28) for t in (300,900,1500)]
    valid=[example('valid'+str(w),w,t) for w in (10,22) for t in (600,1200)]
    fitted=candidates(train,'operator_delay_ps',['lhs_width','target_period_ps','log2_target_ps'],10.)
    linear=next(predictor for name,predictor in fitted if name=='ridge-0.01')
    errors=[abs(inference.infer(linear,r['features'])-r['operator_delay_ps'])/r['operator_delay_ps'] for r in valid]
    if max(errors)>.01 or {p['kind'] for _,p in fitted}!={'linear','segmented','tree'}:
        raise ValueError('analytical fit/export fixture failed')
    if any(not math.isfinite(inference.infer(p,r['features'])) for _,p in fitted for r in valid):
        raise ValueError('nonfinite exported candidate')
    write(out,dict(status='passed',source_macro_expected=dict(median=.125,P95=1.,score=.375),actual=result,
        analytical_export_candidates=len(fitted),analytical_new_width_clock_max_relative_error=max(errors),
        formal_labels_read=False,independent_labels_read=False))
    print('CONDITION_FIT_SOURCE_MACRO_PREFLIGHT_PASS',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','verify','fit-preflight'));p.add_argument('--root',type=Path);p.add_argument('--folder',type=Path);p.add_argument('--out',type=Path);p.add_argument('--candidate',type=Path);p.add_argument('--data',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.root,a.folder,a.candidate,a.data)
    elif a.action=='verify':verify(a.folder,a.out)
    else:fit_preflight(a.out)
