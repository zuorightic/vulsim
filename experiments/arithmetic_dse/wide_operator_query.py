"""Versioned wide Query and numerical features, independently of price tables."""
from copy import deepcopy
from . import wide_arithmetic as arithmetic,wide_operator_samples as samples

VERSION='arithmetic-wide-query-v1'


def descriptor(local,target,profile_sha256):
    samples.validate(local);r=local['producer']['result_width']
    return dict(version=VERSION,semantics=arithmetic.VERSION,declared_result_width=r,required_result_bits=list(range(r)),local_context=deepcopy(local),
                flow_context=dict(target_platform='asap7',evaluation_stage='grt',target_period_ps=target,abc_target_ps=target,profile_sha256=profile_sha256,boundary_policy=arithmetic.POLICY),
                topology=dict(operand_shared_input_roots=0,same_stage_remaining_depth=1))


def features(q):
    if set(q)!={'version','semantics','declared_result_width','required_result_bits','local_context','flow_context','topology'} or q['version']!=VERSION or q['semantics']!=arithmetic.VERSION:raise ValueError('unknown wide Query schema')
    ctx=q['flow_context'];local=q['local_context'];samples.validate(local);p=local['producer'];r=p['result_width']
    if set(ctx)!={'target_platform','evaluation_stage','target_period_ps','abc_target_ps','profile_sha256','boundary_policy'} or ctx['target_platform']!='asap7' or ctx['evaluation_stage']!='grt' or ctx['boundary_policy']!=arithmetic.POLICY or not ctx['profile_sha256'] or ctx['target_period_ps']!=ctx['abc_target_ps']:raise ValueError('wide Query flow identity mismatch')
    if type(q['declared_result_width']) is not int or not r<=q['declared_result_width']<=arithmetic.MAX_WIDTH:raise ValueError('wide result declaration mismatch')
    demand=q['required_result_bits']
    if any(type(b) is not int for b in demand) or demand!=list(range(r)):raise ValueError('demand must match explicit finite result slice')
    if set(q['topology'])!={'operand_shared_input_roots','same_stage_remaining_depth'} or any(type(v) is not int or not 0<=v<=1000000 for v in q['topology'].values()):raise ValueError('invalid wide topology')
    f=arithmetic.features(p,ctx['target_period_ps']);f.update(capture_banks=0.,capture_bits=0.,consumer_count=float(len(local['consumers'])),consumer_arithmetic_width=0.,consumer_operand_pin_uses=0.,consumer_mapping_position_mean=0.)
    uses=position=0.
    for cap in local['captures']:f['capture_banks']+=cap['banks'];f['capture_bits']+=cap['banks']*cap['declared_width']
    for c in local['consumers']:
        f['consumer_arithmetic_width']=max(f['consumer_arithmetic_width'],c['spec']['arithmetic_width'])
        for b in c['bindings']:
            for i,t in enumerate(b['result_bit_map']):
                if type(t) is int:uses+=1;position+=i/max(1,c['spec']['arithmetic_width']-1)
    f['consumer_operand_pin_uses']=uses;f['consumer_mapping_position_mean']=position/max(1.,uses)
    return f
