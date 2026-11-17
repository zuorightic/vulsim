"""Offline shared N4 functions, with a pure numerical inference interface.

No query identity, measured-clock index, source, workload or nearest-neighbour
label enters the response. Numerical clock is a continuous feature. S/shared
and characterization boundaries are intentionally left for N5/N6.
"""
from copy import deepcopy
import math

from . import workload_diagnostic as old
from . import centered_response as response

VERSION='nangate45-shared-operator-functions-v1'
FEATURES={
 'Mul':['log_old','log_width','log_work','log_clock','log_load'],
 'Add':['log_old','log_width','log_work','log_clock','log_load','carry_dynamic','known_fraction'],
 'G':['log_old','log_width','log_work','log_clock','log_terms']}


def native_query(query,platform,profile_sha256,target):
    q=deepcopy(query)
    if 'local_context' in q:
        q['version']='arithmetic-workload-query-v2'
        q['flow_context'].update(target_platform=platform,profile_sha256=profile_sha256,
                                 target_period_ps=target,abc_target_ps=target)
    else:q['target_ps']=target
    return q


def basis(family,query,target,metric,old_prices,time_scale=1.):
    oldq=native_query(query,'asap7',old_prices.bundle['profile_sha256'],target/time_scale)
    p=old_prices.reduction_price(oldq) if family=='G' else old_prices.operator_price(oldq)
    reference=p[metric]
    if reference<=0:raise ValueError('nonpositive old response needs a separate alias certificate')
    if family=='G':
        terms=query['terms'];width=query['output_bits'];work=sum(len(t) for t in terms)
        load=1.;extra=dict(log_terms=math.log1p(len(terms)))
    else:
        local=query['local_context'];s=local['producer'];f=old.base_features(s,target,local)
        width=max(s['lhs_width'],s['rhs_width']);work=f['retained_product_terms'] if family=='Mul' else f['alu_work']
        load=1.+f['capture_banks']+f['consumer_operand_pin_uses']/max(1.,f['dynamic_result_bits'])
        known=sum((int(s[p+'_zero_hex'],16)|int(s[p+'_one_hex'],16)).bit_count() for p in ('lhs','rhs'))
        extra=dict(carry_dynamic=float(s['carry']=='dynamic'),known_fraction=known/max(1,s['lhs_width']+s['rhs_width']))
    f=dict(log_old=math.log(reference),log_width=math.log1p(width),log_work=math.log1p(work),
           log_clock=math.log(target/1500.),log_load=math.log(load),**extra)
    return reference,f


class OperatorFunctions:
    def __init__(self,model):
        if model['version']!=VERSION or model['target_platform']!='nangate45':raise ValueError('N4 function/platform identity')
        self.model=model;self.old_prices=old.DiagnosticPrices(model['ASAP7_response'])

    def predict(self,family,query):
        if family not in FEATURES:raise ValueError('unsupported arithmetic family')
        if 'flow_context' in query:
            flow=query['flow_context'];target=flow['target_period_ps']
            if flow['target_platform']!='nangate45' or flow['profile_sha256']!=self.model['profile_sha256'] or flow['abc_target_ps']!=target:
                raise ValueError('query/profile/clock identity mismatch')
        else:
            target=query['target_ps']
            if query.get('target_platform')!='nangate45' or query.get('profile_sha256')!=self.model['profile_sha256']:
                raise ValueError('G query requires explicit platform identity')
        if not math.isfinite(target) or target<=0:raise ValueError('positive numerical request required')
        values={}
        for metric in ('delay_ps','area_um2'):
            m=self.model['functions'][family][metric]
            ref,f=basis(family,query,target,metric,self.old_prices,m['time_scale'])
            if m['form'] in ('global_scale','family_scale'):v=m['scale']*ref
            elif m['form']=='family_affine':v=max(1e-9,m['scale']*ref+m['intercept'])
            elif m['form']=='shared_log_feature_ridge':v=ref*response.predict(m['response'],f)
            else:raise ValueError('unregistered response form')
            if not math.isfinite(v) or v<=0:raise ValueError('invalid response')
            values[metric]=v
        return dict(**values,qualified=False,full_D_ready=False,
                    within_clock_support=self.model['clock_support_ps'][0]<=target<=self.model['clock_support_ps'][1],
                    source='offline shared arithmetic functions; no S/shared/G-embedding qualification')
