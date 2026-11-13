"""Per-source numerical S features; no mapped fanout or source price keys."""
import math
from .state_control_queries import bank_queries,materialized_queries

VERSION='per-source-control-response-features-v1'


def features(control_query):
    f=dict(control_query['features'])
    f['sqrt_logical_sinks']=math.sqrt(f['total_logical_sinks'])
    f['pressure_logical_sinks']=f['log2_logical_sinks']*f['clock_pressure']
    return f


def aggregate(models,control_queries,path_class):
    """Worst registered source; a source's measured price is never an input."""
    if path_class not in models:raise ValueError('unqualified control path family')
    model=models[path_class];queries=[q for q in control_queries if q['path_class']==path_class]
    if not queries:raise ValueError('missing prospective control source')
    predictions=[]
    for query in queries:
        f=features(query);m=model['function']
        y=max(0.,m.get('intercept',0.)+sum(f[n]*v for n,v in zip(m['features'],m['coefficients'],strict=True)))
        predictions.append(dict(stage=query['stage'],required_ps=y,guarded_required_ps=y+model['reserve_ps']))
    return dict(required_ps=max(p['required_ps'] for p in predictions),guarded_required_ps=max(p['guarded_required_ps'] for p in predictions),sources=predictions,price_qualification_granted=False)
