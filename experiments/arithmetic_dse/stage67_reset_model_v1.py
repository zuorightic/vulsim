"""A common train-only reset timing function with a separate upper guard.

Only numerical FF/reset counts and requested T enter predict(). Source names
balance train loss and split roles; neither inference nor support uses them.
"""
import argparse
import math
from pathlib import Path
from .model_fast_preflight import read,write,sha
from .stage67_reset_v1 import TRAIN_FEATURES
from .stage67_shared_model_v1 import fit_models
from .stage67_batch1_analyze_v1 import stats

ROOT=Path(__file__).resolve().parents[2]


def features(ff,ones,t):
    if any(isinstance(x,bool) or not isinstance(x,(float,int)) or not math.isfinite(x) for x in (ff,ones,t)):raise ValueError('nonfinite or nonnumeric reset input')
    if ff<=0 or ones<0 or ones>ff or ff!=int(ff) or ones!=int(ones) or t<=0:raise ValueError('invalid reset state counts or target')
    return dict(one=1.,sqrt_total_FF_bits=math.sqrt(ff),sqrt_reset_one_bits=math.sqrt(ones),clock_pressure=1500/t,total_FF_bits=ff,reset_one_bits=ones)


def predict(model,ff,ones,t,native_depth=1):
    f=features(ff,ones,t)
    if native_depth!=1:raise ValueError('reset native depth outside qualified domain')
    if not model['target_interval_ps'][0]<=t<=model['target_interval_ps'][1]:raise ValueError('reset target outside numerical interval')
    for n,(lo,hi) in model['numeric_support'].items():
        if not lo<=f[n]<=hi:raise ValueError('reset numerical feature outside support: '+n)
    point=math.fsum(c*f[n] for c,n in zip(model['coefficients'],model['features']));guard=point+model['upper_guard_ps']
    return dict(point_intrinsic_ps=point,guard_intrinsic_ps=guard,required_period_ps=guard/.8,violates=guard>.8*t,features=f)


def evaluate(model,data):
    rows=[];refused=[];false=0
    for r in data['rows']:
        try:p=predict(model,r['features']['total_FF_bits'],r['features']['reset_one_bits'],r['target_ps'])
        except ValueError as e:refused.append(dict(source=r['source'],target_ps=r['target_ps'],reason=str(e)));continue
        y=r['reset_required_ps'];error=abs(p['point_intrinsic_ps']-y)/max(1.,abs(y));wrong=not p['violates'] and r['worst_slack_ps']<0;false+=wrong
        rows.append(dict(source=r['source'],target_ps=r['target_ps'],actual_intrinsic_ps=y,worst_slack_ps=r['worst_slack_ps'],relative_point_error=error,
            **p,false_feasible=wrong,guard_underestimation_ps=max(0.,y-p['guard_intrinsic_ps'])))
    errors=stats([r['relative_point_error'] for r in rows]);failures=[]
    if errors['median']>.15 or errors['P95']>.35:failures.append('point_error')
    if false:failures.append('false_feasible')
    if refused:failures.append('support_refusal')
    return dict(rows=rows,refused=refused,errors=errors,false_feasible=false,failures=failures,endpoint_checks=data['endpoint_checks'],full_D_ready=False)


def fit(data,admission,out,native_source=None,native_binary=None):
    if out.exists():raise ValueError('preserve reset candidate')
    d=read(data);a=read(admission)
    if a['role']!='train' or len(d['rows'])!=24 or d['role']!='train' or d['admission_sha256']!=sha(admission):raise ValueError('complete frozen train role required')
    if a['features']!=TRAIN_FEATURES:raise ValueError('prospective reset feature drift')
    rows=[dict(r,labels=dict(reset=r['reset_required_ps'])) for r in d['rows']]
    m=fit_models(rows,dict(reset=TRAIN_FEATURES))['reset']
    residual=max(r['reset_required_ps']-math.fsum(c*r['features'][n] for c,n in zip(m['coefficients'],TRAIN_FEATURES)) for r in rows)
    m.update(version='common-reset-timing-function-v1',upper_guard_ps=max(0.,residual)+25.,fixed_engineering_margin_ps=25.,maximum_positive_train_residual_ps=max(0.,residual),
        target_interval_ps=[500.,3000.],native_depth=1,numeric_support={n:[min(r['features'][n] for r in rows),max(r['features'][n] for r in rows)] for n in ('total_FF_bits','reset_one_bits')},
        guard_convention='reset port max arrival 0.2*T; compare intrinsic guard with 0.8*T; report guard/0.8 as required period',
        training_dataset_sha256=sha(data),protocol_sha256=sha(admission),validation_read=False,independent_tests_unlocked=False,quality_status='frozen_train_candidate',full_D_ready=False)
    diag=evaluate(m,d);out.mkdir(parents=True);write(out/'candidate.json',m);write(out/'training.json',diag)
    files=[out/'candidate.json',data,admission,Path(__file__),ROOT/'experiments/arithmetic_dse/stage67_reset_v1.py',ROOT/'experiments/arithmetic_dse/stage67_reset_v3.py',ROOT/'experiments/arithmetic_dse/stage67_shared_model_v1.py',ROOT/'experiments/arithmetic_dse/stage67_batch1_analyze_v1.py']
    if native_source:
        files.append(native_source)
        files += [ROOT/'rtlzz/src/backend/arithmetic_reset_function.hpp',ROOT/'rtlzz/testv2/arithmetic_reset_function_consumer.cpp']
    if native_binary:files.append(native_binary)
    write(out/'freeze.json',dict(version='reset-timing-candidate-freeze-v1',files={str(p):sha(p) for p in files},features_parameters_support_and_guard_frozen=True,validation_read=False,full_D_ready=False))
    print(dict(status='reset_candidate_frozen',coefficients=m['coefficients'],guard=m['upper_guard_ps'],training_errors=diag['errors'],failures=diag['failures']),flush=True)


def validate(data,freeze,out):
    if out.exists():raise ValueError('preserve one-time reset validation')
    f=read(freeze)
    for n,h in f['files'].items():
        if sha(n)!=h:raise ValueError('reset candidate drift '+n)
    m=read(freeze.parent/'candidate.json');d=read(data)
    if d['role']!='validation' or any(r['role']!='validation' for r in d['rows']):raise ValueError('validation role required')
    train=read(next(n for n in f['files'] if n.endswith('dataset.json')))
    if {r['source'] for r in train['rows']}&{r['source'] for r in d['rows']}:raise ValueError('source role overlap')
    result=evaluate(m,d);result.update(status='failed_reset_validation' if result['failures'] else 'passed_reset_validation_not_independent',freeze_sha256=sha(freeze),parameters_changed=False)
    write(out,result);print(dict(status=result['status'],errors=result['errors'],false_feasible=result['false_feasible'],refused=len(result['refused']),failures=result['failures']),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('fit','validate'))
    for n in ('data','admission','out','freeze','native-source','native-binary'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='fit':fit(a.data.resolve(),a.admission.resolve(),a.out.resolve(),a.native_source.resolve() if a.native_source else None,a.native_binary.resolve() if a.native_binary else None)
    else:validate(a.data.resolve(),a.freeze.resolve(),a.out.resolve())
