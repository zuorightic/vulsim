"""Numerical consumption of frozen G parameters in an explicitly diagnostic scope."""
from . import reduction_wide_features as geometry,wide_function_model as linear
from . import conditional_function_support_v2 as support

VERSION='wide-prefix-reuse-diagnostic-v1'


def predict(model,query,*,diagnostic=False,extrapolate=False):
    try:
        if model['version']!=VERSION or model['feature_version']!=geometry.VERSION:
            raise ValueError('wide G model identity mismatch')
        if not diagnostic:raise ValueError('wide G successor has no independent qualification')
        if query.get('launch_type','register')!='register' or query.get('capture_banks',1)!=1 or query.get('consumer_count',0)!=0:
            raise ValueError('unqualified wide G boundary')
        T=query['target_ps'];f=geometry.features(query['output_bits'],query['terms'],T)
        verdict=support.check(model['support'],f['area'],T)
        inside=verdict['status']=='structurally_supported'
        if not inside and (not extrapolate or not 500<=T<=3000):return verdict
        delay=linear.linear(model['delay'],f['delay']);area=linear.linear(model['area'],f['area'])
        if delay<=0 or area<=0:raise ValueError('invalid G intrinsic price')
        return dict(status='diagnostic_estimate' if inside else 'unqualified_extrapolation',
                    operator_delay_ps=delay,comb_area_um2=area,
                    support_reason='' if inside else verdict.get('reason','outside support'),qualified_for_public_D=False)
    except (KeyError,ValueError,TypeError,OverflowError) as e:return dict(status='cost_uncovered',reason=str(e))
