"""Portable inference ABI shared by data collection and native cost queries."""
import math

VERSION='arithmetic-physical-features-v2'
FEATURES=('lhs_width','rhs_width','result_width','log_width','width_product','fanout',
          'lhs_zero_bits','rhs_zero_bits','abc_target_ps','sdc_period_ps',
          'width_result_product','retained_product_terms')

def features(lhs_width,rhs_width,result_width,fanout,abc_target_ps,sdc_period_ps,lhs_zero_bits=0,rhs_zero_bits=0,*,literal_operands=False,known_one_operands=False,constant_carry=False,correlated_operands=False):
    if any(type(v) is not bool for v in (literal_operands,known_one_operands,constant_carry,correlated_operands)):raise ValueError('operand metadata must be boolean')
    if any(isinstance(x,bool) or not isinstance(x,int) for x in (lhs_width,rhs_width,result_width,fanout,lhs_zero_bits,rhs_zero_bits)):
        raise ValueError('integer widths, fanout and bit counts required')
    values=(lhs_width,rhs_width,result_width,math.log2(max(lhs_width,rhs_width,1)),
            lhs_width*max(rhs_width,1),fanout,lhs_zero_bits,rhs_zero_bits,abc_target_ps,sdc_period_ps,
            max(lhs_width,rhs_width)*result_width,
            sum(max(0,min(rhs_width,result_width-i)) for i in range(lhs_width)))
    if any(isinstance(x,bool) or not isinstance(x,(int,float)) or not math.isfinite(x) for x in values):raise ValueError('finite numeric model features required')
    if min(lhs_width,result_width,fanout,abc_target_ps,sdc_period_ps)<=0 or min(rhs_width,lhs_zero_bits,rhs_zero_bits)<0 or lhs_zero_bits>lhs_width or rhs_zero_bits>rhs_width:raise ValueError('invalid model feature domain')
    return {**dict(zip(FEATURES,values)),'literal_operands':literal_operands,'known_one_operands':known_one_operands,
            'constant_carry':constant_carry,'correlated_operands':correlated_operands}

def infer(predictor,values):
    def numeric(value):
        if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):raise ValueError('finite model number required')
        return float(value)
    names=predictor['features']
    if not isinstance(names,list) or len(set(names))!=len(names) or any(k not in FEATURES for k in names):raise ValueError('invalid predictor feature names')
    x=[numeric(values[k]) for k in predictor['features']]
    if predictor['kind']=='linear':
        result=numeric(predictor['intercept'])
        # Match the native double accumulation order, including intercept.
        for a,b in zip(predictor['coefficients'],x,strict=True):result+=numeric(a)*b
    elif predictor['kind']=='tree':
        at=0;nodes=predictor['nodes'];seen=set()
        if not isinstance(nodes,list) or not nodes:raise ValueError('nonempty portable tree required')
        while 'value' not in nodes[at]:
            if at in seen:raise ValueError('cyclic portable tree')
            seen.add(at);node=nodes[at]
            index=node['feature']
            if isinstance(index,bool) or not isinstance(index,int) or not 0<=index<len(x):raise ValueError('invalid tree feature index')
            at=node['left'] if x[index]<=numeric(node['threshold']) else node['right']
            if not isinstance(at,int) or isinstance(at,bool) or not 0<=at<len(nodes):raise ValueError('invalid portable tree child')
        result=numeric(nodes[at]['value'])
    else:raise ValueError('unknown portable predictor')
    if not math.isfinite(result):raise ValueError('nonfinite model prediction')
    return max(0.0,result)

def validate_query(bundle,operation,values,*,platform,profile_sha256,stage):
    if (bundle.get('version')!='arithmetic-backend-model-v1' or bundle['target_platform']!=platform
            or bundle['platform_profile_sha256']!=profile_sha256 or bundle['feature_schema']!=VERSION
            or bundle.get('quality_status')!='passed'):
        return {'status':'uncovered','reason':'model_platform_profile_or_schema_mismatch'}
    scope=bundle.get('stages',{}).get(stage,{}).get('operations',{}).get(operation)
    if not scope:return {'status':'uncovered','reason':'unsupported_operation_or_stage'}
    if scope.get('quality_status')!='passed':return {'status':'uncovered','reason':'model_quality_not_ready'}
    # v2 samples use equal-width dynamic operands. Independent min/max bounds
    # never authorize an unmeasured rectangular width domain.
    if operation in ('mul','add','addcarry') and values['lhs_width']!=values['rhs_width']:
        return {'status':'uncovered','reason':'unvalidated_asymmetric_operand_widths'}
    domain=scope['domain']
    if domain.get('known_zero_policy','none')!='none' or domain.get('constant_operand_policy','dynamic_only')!='dynamic_only':
        return {'status':'uncovered','reason':'unsupported_operand_domain_policy'}
    if values.get('literal_operands',False) and domain.get('constant_operand_policy','dynamic_only')=='dynamic_only':
        return {'status':'uncovered','reason':'unvalidated_literal_operand'}
    if values.get('known_one_operands',False):return {'status':'uncovered','reason':'unvalidated_known_one_operand_pattern'}
    if values.get('constant_carry',False):return {'status':'uncovered','reason':'unvalidated_constant_carry'}
    if values.get('correlated_operands',False):return {'status':'uncovered','reason':'unvalidated_correlated_operands'}
    if (values['lhs_zero_bits'] or values['rhs_zero_bits']) and domain.get('known_zero_policy','none')=='none':
        return {'status':'uncovered','reason':'unvalidated_known_zero_operand_pattern'}
    # Width/result shapes and ABC/SDC pairs are a single declared relationship.
    conditions=domain['conditions']
    if not any(c['lhs_min']<=values['lhs_width']<=c['lhs_max'] and c['rhs_min']<=values['rhs_width']<=c['rhs_max']
               and values['fanout']<=c['fanout_max'] and values['abc_target_ps']==c['abc_target_ps']
               and c['sdc_min_ps']<=values['sdc_period_ps']<=c['sdc_max_ps']
               and (c['result_shape']=='full_mul' and values['result_width']==values['lhs_width']+values['rhs_width']
                    or c['result_shape']=='low_mul' and values['result_width']==max(values['lhs_width'],values['rhs_width'])
                    or c['result_shape']=='same_width' and values['result_width']==values['lhs_width']
                    or c['result_shape']=='boolean' and values['result_width']==1
                    or c['result_shape']=='carry' and values['result_width']==max(values['lhs_width'],values['rhs_width'])+1
                    or c['result_shape']=='fp37' and values['lhs_width']==32 and values['rhs_width']==32 and values['result_width']==37)
               for c in conditions):return {'status':'uncovered','reason':'outside_joint_shape_width_target_domain'}
    if isinstance(scope['delay_margin_ps'],bool) or not isinstance(scope['delay_margin_ps'],(int,float)) or not math.isfinite(scope['delay_margin_ps']) or scope['delay_margin_ps']<0:
        raise ValueError('finite nonnegative physical delay margin required')
    return {'status':'predicted_in_domain','delay_ps':infer(scope['delay'],values)+scope['delay_margin_ps'],
            'comb_area_um2':infer(scope['area'],values),'model_id':bundle['id'],'source':'fitted_microbenchmark_model'}
