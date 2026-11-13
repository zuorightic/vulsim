"""Shared numerical operator functions over the versioned wide Query.

Source names, exact shape keys and period categories never enter inference.
The public query requires independent qualification; diagnostics explicitly
opt in to the same arithmetic with an unqualified candidate.
"""
import math
from . import wide_operator_query as query,wide_arithmetic as arithmetic
from . import conditional_function_support_v2 as support
from . import wide_alu_geometry as alu

VERSION='common-wide-operator-functions-v2'
FEATURE_VERSION='wide-function-numerical-features-v2-demand-prefix'


def family(spec):
    op=spec['operation']
    return 'add' if op in ('add','adc') else 'sub' if op in ('sub','sbb') else 'compare' if op in ('ult','ule','eq') else op


def features(descriptor):
    f=query.features(descriptor);spec=descriptor['local_context']['producer']
    if arithmetic.aliases(spec) is not None:raise ValueError('exact alias lowering required before arithmetic pricing')
    graph=alu.geometry(spec);f.update(graph['features']);pressure=f['clock_pressure']
    used=graph['used']
    if arithmetic.permutation(spec)==[1,0]:used=dict(lhs=used['rhs'],rhs=used['lhs'])
    for name,bits in used.items():
        f[name+'_live_bits']=float(len(bits));f['log2_'+name+'_live_bits']=math.log2(len(bits)+1.)
        f[name+'_low_position']=float(min(bits,default=0));f[name+'_high_position']=float(max(bits,default=-1)+1)
    f['active_overlap']=float(len(set(graph['used']['lhs'])&set(graph['used']['rhs'])))
    if not graph['mul']:
        f['dynamic_result_bits']=float(len(graph['dynamic_outputs']));f['known_result_bits']=spec['result_width']-f['dynamic_result_bits']
    z,o=arithmetic.known_result(spec)
    dynamic={i for i in range(spec['result_width']) if not ((z|o)>>i&1)} if graph['mul'] else set(graph['dynamic_outputs'])
    uses=positions=0.
    for c in descriptor['local_context']['consumers']:
        for binding in c['bindings']:
            for i,bit in enumerate(binding['result_bit_map']):
                if type(bit) is int and bit in dynamic:uses+=1;positions+=i/max(1,c['spec']['arithmetic_width']-1)
    f['consumer_operand_pin_uses']=uses;f['consumer_mapping_position_mean']=positions/max(1.,uses)
    a=f['lhs_live_bits'];b=f['rhs_live_bits'];w=f['arithmetic_width']
    f.update(live_input_sum=a+b,log2_live_input_sum=math.log2(a+b+1.),
        operand_live_min=min(a,b),operand_live_max=max(a,b),
        log2_retained_work=math.log2(f['retained_product_terms']+1.),
        log2_value_width=math.log2(f['value_width']+1.),
        result_high_fraction=f['result_lo']/w,
        pressure_live_sum=(a+b)*pressure,
        pressure_consumer_uses=f['consumer_operand_pin_uses']*pressure,
        compare_eq_work=f['predicate_eq']*max(a,b),compare_le_work=f['predicate_le']*max(a,b),
        log2_alu_work=math.log2(f['alu_work']+1.),pressure_alu_work=f['alu_work']*pressure)
    f['log2_operand_live_min']=math.log2(min(a,b)+1.)
    f['log2_demand_hi']=math.log2(spec['result_lo']+spec['value_width']+1.)
    f['consumer_conditioning_proxy']=math.log2(f['consumer_arithmetic_width']+1.)*(1-f['consumer_mapping_position_mean'])
    f['consumer_load_work']=f['consumer_operand_pin_uses']*f['consumer_conditioning_proxy']
    if any(not math.isfinite(v) for v in f.values()):raise ValueError('nonfinite numerical function feature')
    return f


def semantic_scope(descriptor):
    local=descriptor['local_context'];p=local['producer'];op=p['operation'];w=p['arithmetic_width'];r=p['result_width']
    if descriptor['topology']['same_stage_remaining_depth']!=1:raise ValueError('unqualified remaining-stage context')
    if any(int(p[name+'_one_hex'],16) for name in ('lhs','rhs')):raise ValueError('known-one operands need a qualified successor')
    for name in ('lhs','rhs'):
        bits=[i for i in range(p[name+'_width']) if len(arithmetic.bit_values(p,name,i))==2]
        if bits and bits!=list(range(min(bits),max(bits)+1)):raise ValueError('multiple live operand intervals need qualification')
    if op=='mul' and (w!=p['lhs_width']+p['rhs_width'] or int(p['lhs_zero_hex'],16) or int(p['rhs_zero_hex'],16)):raise ValueError('canonical full-product precision and unmasked operands required')
    if op in ('add','adc','sub','sbb','mux') and p['result_lo']!=0:raise ValueError('unqualified nonzero arithmetic slice')
    if op in ('sub','sbb') and (w!=max(p['lhs_width'],p['rhs_width']) or int(p['lhs_zero_hex'],16) or int(p['rhs_zero_hex'],16)):raise ValueError('unqualified subtract padding/known-bit context')
    if op=='mux' and (p['carry']!='dynamic' or w!=p['value_width']):raise ValueError('canonical dynamic whole-result Mux required')
    if local['consumers']:
        if family(p) not in ('add','mul'):raise ValueError('consumer context for this family needs qualification')
        if local['captures'] or len(local['consumers'])!=1:raise ValueError('mixed consumer/capture context needs qualification')
        c=local['consumers'][0];s=c['spec'];bindings=c['bindings']
        if len(bindings)!=1 or s['operation']!='add' or s['carry']!='zero' or s['status']!='none' or s['result_lo'] or s['value_width']!=s['arithmetic_width'] or s['lhs_width']!=s['arithmetic_width'] or s['rhs_width']!=s['arithmetic_width']:raise ValueError('unqualified consumer algorithm/demand')
        mapping=bindings[0]['result_bit_map'];shift=next((i for i,b in enumerate(mapping) if type(b) is int),-1);cw=s['arithmetic_width']
        if shift<0 or mapping!=['0']*shift+list(range(r))+['0']*(cw-shift-r):raise ValueError('unqualified result connection')
        bound=('lhs','rhs')[bindings[0]['operand_index']];other='rhs' if bound=='lhs' else 'lhs';outside=((1<<cw)-1)^(((1<<r)-1)<<shift)
        if int(s[bound+'_zero_hex'],16)!=outside or any(int(s[name],16) for name in (bound+'_one_hex',other+'_one_hex',other+'_zero_hex')):raise ValueError('consumer mask/connection mismatch')
    else:
        caps=local['captures']
        if len(caps)!=1 or caps[0]['banks']>2 or caps[0]['declared_width']!=r or caps[0]['result_bit_map']!=list(range(r)):raise ValueError('unqualified capture bit demand')


def linear(model,f):
    names=model['features'];coeff=model['coefficients']
    if len(names)!=len(coeff) or len(set(names))!=len(names):raise ValueError('function parameter mismatch')
    value=model.get('intercept',0.)+sum(f[n]*c for n,c in zip(names,coeff,strict=True))
    if not math.isfinite(value):raise ValueError('nonfinite function price')
    return max(0.,value)


def predict(model,descriptor,*,diagnostic=False):
    try:
        if model['version']!=VERSION or (model['quality_status']!='passed_independent' and not diagnostic):raise ValueError('operator functions lack independent qualification')
        ctx=descriptor['flow_context']
        if ctx['profile_sha256']!=model['profile_sha256'] or ctx['boundary_policy']!=arithmetic.POLICY:raise ValueError('function/measurement policy mismatch')
        local=descriptor['local_context'];spec=local['producer'];name=family(spec)
        semantic_scope(descriptor)
        if descriptor['topology']['operand_shared_input_roots']!=0:raise ValueError('correlated operator operands require qualified composition')
        if arithmetic.aliases(spec) is not None:raise ValueError('exact alias lowering required before arithmetic pricing')
        f=features(descriptor);domain=model['support'][name];verdict=support.check(domain,f,ctx['target_period_ps'])
        if (name!='mul' and f['alu_work']==0) or f['dynamic_result_bits']==0:raise ValueError('constant/wire lowering required before arithmetic pricing')
        if verdict['status']!='structurally_supported':return verdict
        m=model['functions'][name]
        d=linear(m['delay_ps'],f);a=linear(m['area_um2'],f)
        if d<=0 or a<=0:raise ValueError('nonpositive arithmetic price')
        return dict(status='diagnostic_estimate' if diagnostic else 'covered',operator_delay_ps=d,comb_area_um2=a,
                    train_LOSO_delay_reserve_ps=m['delay_reserve_ps'],reserve_charged_in_price=False,features=f,qualified_for_public_D=not diagnostic)
    except (KeyError,ValueError,TypeError,OverflowError) as e:return dict(status='cost_uncovered',reason=str(e))
