"""Diagnostic operator successor with disjoint, nonnegative compare work.

The ordered/equality algorithms have separate numerical workload columns;
there are no source, shape, width-category or exact-period price keys.
"""
from copy import deepcopy
from . import wide_function_model as parent, conditional_function_support_v2 as support

VERSION='common-wide-operator-functions-v3-compare-work'
FEATURE_VERSION='wide-function-features-v3-disjoint-compare-work'


def features(descriptor):
    f=parent.features(descriptor)
    f['compare_order_work']=(1.-f['predicate_eq'])*f['operand_live_max']
    return f


def predict(model,descriptor,*,diagnostic=False):
    try:
        if model['version']!=VERSION or model['feature_version']!=FEATURE_VERSION:
            raise ValueError('operator successor feature identity mismatch')
        if model['quality_status']!='passed_independent' and not diagnostic:
            raise ValueError('operator successor lacks independent qualification')
        # Project the new linear basis algebraically into the original basis.
        # This also reuses all existing semantic, profile and support checks.
        adapted=deepcopy(model);adapted['version']=parent.VERSION
        for function in adapted['functions'].values():
            for key in ('delay_ps','area_um2'):
                m=function[key];terms={}
                for name,co in zip(m['features'],m['coefficients'],strict=True):
                    for n,c in ([('operand_live_max',co),('compare_eq_work',-co)]
                                if name=='compare_order_work' else [(name,co)]):
                        terms[n]=terms.get(n,0.)+c
                m['features']=list(terms);m['coefficients']=list(terms.values())
        result=parent.predict(adapted,descriptor,diagnostic=diagnostic)
        if result['status'] in ('covered','diagnostic_estimate'):
            result['features']=features(descriptor)
        return result
    except (KeyError,ValueError,TypeError,OverflowError) as error:
        return dict(status='cost_uncovered',reason=str(error))
