"""Same parameters/support, symmetric numerical boundary tolerance.

Only floating roundoff at support boundaries is covered (1e-10 relative).
Empirical extrapolation remains refused. Original frozen failure is preserved.
"""
import argparse
import math
from pathlib import Path
from types import FunctionType
from . import stage67_shared_model_v1 as parent
from .model_fast_preflight import read,write,sha


def linear(model,features):
    if model['kind']!='nonnegative_linear' or len(model['features'])!=len(model['coefficients']):raise ValueError('invalid simple shared/state model')
    value=0.
    for n,c in zip(model['features'],model['coefficients'],strict=True):
        if not math.isfinite(c) or c<0:raise ValueError('invalid nonnegative coefficient')
        if 'numeric_support' in model:
            low,high=model['numeric_support'][n];epsilon=1e-10*max(1.,abs(low),abs(high))
            if not low-epsilon<=features[n]<=high+epsilon:raise ValueError('shared area outside frozen semantic feature support')
        value+=c*features[n]
    return value


def predict(policy,f,t):
    ns=dict(parent.predict.__globals__);ns['linear']=linear
    return FunctionType(parent.predict.__code__,ns)(policy,f,t)


def freeze(root):
    old=root/'fit-v1/freeze.json';p=read(old)
    for n,h in p['files'].items():
        if sha(n)!=h:raise ValueError('old frozen fit changed '+n)
    files=[Path(__file__),Path(__file__).with_name('stage67_shared_extract_v3.py'),Path(__file__).with_name('stage67_state_semantics_v2.py')]
    files += [parent.ROOT/'rtlzz/src/backend'/('arithmetic_shared_function_v2.'+ext) for ext in ('cpp','hpp')]
    files += [parent.ROOT/'rtlzz/testv2'/('arithmetic_shared_function_'+name+'_v2.cpp') for name in ('consumer','mac32')]
    files += [parent.ROOT/'build/step4-rtlzz/testv2'/('arithmetic-shared-function-'+name+'-v2') for name in ('consumer','mac32')]
    p.update(version='shared-function-freeze-v2',parent_freeze_sha256=sha(old),numerical_boundary_tolerance_relative=1e-10,
        parameters_changed=False,empirical_numeric_support_changed=False,validation_labels_read=False,
        files={**p['files'],**{str(n):sha(n) for n in files}})
    target=root/'fit-v1/freeze-v2.json'
    if target.exists():raise ValueError('preserve successor freeze')
    write(target,p);print('SHARED_IMPLEMENTATION_SUCCESSOR_FROZEN unchanged_parameters=1 unchanged_support=1',flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('freeze','parity','validate'));p.add_argument('--root',type=Path)
    for n in ('native','policy','data','freeze','out'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='freeze':freeze(a.root.resolve());return
    ns=dict(parent.parity.__globals__);ns.update(linear=linear,predict=predict)
    if a.action=='parity':FunctionType(parent.parity.__code__,ns)(a.native.resolve(),a.policy.resolve(),a.out.resolve())
    else:FunctionType(parent.validate.__code__,ns)(a.data.resolve(),a.freeze.resolve(),a.out.resolve())


if __name__=='__main__':main()
