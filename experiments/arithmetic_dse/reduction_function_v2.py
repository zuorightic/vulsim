"""G numerical feature successor: balanced compressor levels, same RTL policy.

The sampling-v1 column sweep remains a work diagnostic. Its sweep count can
include a carry walking across columns, so it is not a compressor layer count.
This version derives balanced levels from maximum live column height instead.
"""
import math
from .reduction_function import POLICY,VERSION,features as original_features

FEATURE_VERSION='bit-column-features-v2-balanced-levels'


def features(width,terms,target):
    f=original_features(width,terms,target);rows=int(f['max_column_height']);levels=0
    while rows>2:
        rows=2*(rows//3)+rows%3;levels+=1
    return dict(f,compression_levels=float(levels))


def predict(model,width,terms,target):
    if model['version']!=VERSION or model['feature_version']!=FEATURE_VERSION or model['policy']!=POLICY or model['quality_status']!='passed_independent':
        raise ValueError('G reduction model is not independently qualified')
    f=features(width,terms,target)
    if not model['target_interval_ps'][0]<=target<=model['target_interval_ps'][1]:raise ValueError('G target outside frozen interval')
    for name,(lo,hi) in model['numeric_support'].items():
        eps=1e-10*max(1,abs(lo),abs(hi))
        if name not in f or not lo-eps<=f[name]<=hi+eps:raise ValueError('G feature outside frozen support: '+name)
    out={}
    for name in ('delay_ps','area_um2'):
        m=model[name];names=m['features'];co=m['coefficients']
        if m['kind']!='nonnegative_linear' or len(names)!=len(co) or len(set(names))!=len(names) or any(n not in f for n in names) or any(not math.isfinite(c) or c<0 for c in co):raise ValueError('invalid G function features/coefficients')
        out[name]=sum(f[k]*c for k,c in zip(names,co))
        if not math.isfinite(out[name]) or out[name]<=0:raise ValueError('invalid G prediction')
    return dict(**out,features=f,residual_G_delay_ps=0.,residual_G_area_um2=0.)
