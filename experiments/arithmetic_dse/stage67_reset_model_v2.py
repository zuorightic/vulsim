"""Train-only reset successor with numerical clock relaxation.

The sign-correct feature 1-500/T expresses relaxation under larger requested
periods while retaining a common nonnegative coefficient vector.
"""
import argparse
from copy import deepcopy
import inspect
from pathlib import Path
from types import FunctionType
from . import stage67_reset_model_v1 as parent
from .model_fast_preflight import read,write,sha

TRAIN_FEATURES=['one','sqrt_total_FF_bits','sqrt_reset_one_bits','clock_relaxation']


def features(ff,ones,t):
    f=parent.features(ff,ones,t);f['clock_relaxation']=1-500/t;return f


def predict(model,ff,ones,t,native_depth=1):
    ns=dict(parent.predict.__globals__);ns['features']=features
    return FunctionType(parent.predict.__code__,ns)(model,ff,ones,t,native_depth)


def evaluate(model,data):
    ns=dict(parent.evaluate.__globals__);ns['predict']=predict
    return FunctionType(parent.evaluate.__code__,ns)(model,data)


def register(data,admission,out):
    if out.exists():raise ValueError('preserve reset successor protocol')
    d=read(data);a=read(admission)
    if d['admission_sha256']!=sha(admission) or a['role']!='train':raise ValueError('only existing frozen train labels')
    a=deepcopy(a);a.update(version='compatible-reset-fit-protocol-v2',features=TRAIN_FEATURES,predecessor_admission_sha256=sha(admission),source_dataset_sha256=sha(data),
        reason='train-only v1 error gate failed; 500ps reset implementations faster than relaxed targets',clock_relaxation='1 - 500 / numerical target_ps',
        additional_budget=dict(synth=0,grt=0,support=12,per_leaf_timeout_s=300),validation_read=False)
    write(out/'admission.json',a);d=deepcopy(d);d.update(version='reset-compatible-dataset-v2',admission_sha256=sha(out/'admission.json'),predecessor_dataset_sha256=sha(data))
    for r in d['rows']:r['features']=features(r['features']['total_FF_bits'],r['features']['reset_one_bits'],r['target_ps'])
    write(out/'dataset.json',d);print('RESET_SUCCESSOR_REGISTERED same_24_train_labels numerical_clock_relaxation',flush=True)


def fit(data,admission,out,native_source,native_binary):
    text=inspect.getsource(parent.fit).replace("version='common-reset-timing-function-v1'","version='common-reset-timing-function-v2'")
    old="if native_binary:files.append(native_binary)"
    new="files += [Path(parent.__file__),ROOT/'rtlzz/src/backend/arithmetic_reset_function_v2.cpp']\n    "+old
    if text.count(old)!=1:raise ValueError('reset freeze callsite drift')
    ns=dict(parent.fit.__globals__);ns.update(__file__=__file__,parent=parent,TRAIN_FEATURES=TRAIN_FEATURES,evaluate=evaluate)
    exec(compile(text.replace(old,new),__file__,'exec'),ns);ns['fit'](data,admission,out,native_source,native_binary)


def validate(data,freeze,out):
    ns=dict(parent.validate.__globals__);ns['evaluate']=evaluate
    FunctionType(parent.validate.__code__,ns)(data,freeze,out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('register','fit','validate'))
    for n in ('data','admission','out','freeze','native-source','native-binary'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='register':register(a.data.resolve(),a.admission.resolve(),a.out.resolve())
    elif a.action=='fit':fit(a.data.resolve(),a.admission.resolve(),a.out.resolve(),a.native_source.resolve(),a.native_binary.resolve())
    else:validate(a.data.resolve(),a.freeze.resolve(),a.out.resolve())
