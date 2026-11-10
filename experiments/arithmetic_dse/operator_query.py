"""OperatorQuery ABI, reconstructed from native typed graphs before measurement.

No exact shape/case whitelist, no physical labels and no EDA. A valid query is
not itself a qualified price. The native counterpart lives in RTLzz backend.
"""
from copy import deepcopy
import math

from .model_fast_preflight import bits, demanded_bits, operator_shape
from .model_fast_samples import from_shape
from .model_fast_loads import bit_origins

VERSION = 'arithmetic-operator-query-v1'


def _integer(value, label, low=0, high=1000000):
    if type(value) is not int or not low <= value <= high:
        raise ValueError('bounded integer required: '+label)
    return value


def _number(value):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError('finite number required')
    return float(value)


def _mask(spec, prefix, which, width):
    value=int(spec[prefix+'_'+which+'_hex'],16)
    if value < 0 or value >> width:
        raise ValueError('known mask out of range')
    return [bool(value >> i & 1) for i in range(width)]


def features(descriptor):
    if set(descriptor) != {'version','semantics','declared_result_width','required_result_bits','local_context','flow_context','topology'}:
        raise ValueError('unknown or missing operator descriptor field')
    if descriptor['version']!=VERSION or descriptor['semantics']!='unsigned-modulo-v1':
        raise ValueError('unknown query schema/semantics')
    ctx=descriptor['flow_context']
    if set(ctx)!={'target_platform','evaluation_stage','target_period_ps','abc_target_ps','profile_sha256','boundary_policy'}:
        raise ValueError('unknown flow context field')
    t=_number(ctx['target_period_ps'])
    if (t<=0 or _number(ctx['abc_target_ps'])!=t or ctx['target_platform']!='asap7' or ctx['evaluation_stage']!='grt'
            or not isinstance(ctx['profile_sha256'],str) or not ctx['profile_sha256'] or not isinstance(ctx['boundary_policy'],str) or not ctx['boundary_policy']):
        raise ValueError('incompatible query context')
    local=descriptor['local_context']
    if set(local)!={'producer','consumers','captures'}:raise ValueError('unknown local context')
    p=local['producer'];op=p['operation']
    if set(p)!={'operation','lhs_width','rhs_width','result_width','lhs_zero_hex','lhs_one_hex','rhs_zero_hex','rhs_one_hex','carry','capture_banks'}:
        raise ValueError('unknown or missing producer field')
    if op not in ('mul','add','addcarry'):raise ValueError('unsupported operation')
    wa=_integer(p['lhs_width'],'lhs',1,257);wb=_integer(p['rhs_width'],'rhs',1,257);r=_integer(p['result_width'],'result',1,257)
    declared=_integer(descriptor['declared_result_width'],'declared',r,257)
    required=descriptor['required_result_bits']
    if not isinstance(required,list) or not required or any(type(v) is not int or not 0<=v<r for v in required) or sorted(set(required))!=required or max(required)+1!=r:
        raise ValueError('invalid required result bits')
    carry=p['carry']
    if carry not in ('zero','one','dynamic'):raise ValueError('invalid carry')
    topo=descriptor['topology']
    if set(topo)!={'operand_shared_input_roots','same_stage_remaining_depth'}:raise ValueError('unknown topology feature')
    f=dict(lhs_width=wa,rhs_width=wb,result_width=r,declared_result_width=declared,target_period_ps=t,abc_target_ps=t,log2_target_ps=math.log2(t))
    for name in ('mul','add','addcarry'):f['operation_'+name]=int(op==name)
    f.update(carry_dynamic=int(carry=='dynamic'),carry_one=int(carry=='one'),full_product=int(op=='mul' and r==wa+wb),
             low_result=int(r<(wa+wb if op=='mul' else max(wa,wb)+1)),required_result_bits=len(required),width_product=wa*wb,
             operand_shared_input_roots=_integer(topo['operand_shared_input_roots'],'overlap'),
             same_stage_remaining_depth=_integer(topo['same_stage_remaining_depth'],'depth'))
    for prefix,w in (('lhs',wa),('rhs',wb)):
        zero=_mask(p,prefix,'zero',w);one=_mask(p,prefix,'one',w)
        if any(a and b for a,b in zip(zero,one)):raise ValueError('conflicting known bits')
        for which,row in (('zero',zero),('one',one)):
            current=runs=longest=0;previous=False
            for v in row:
                current=current+1 if v else 0
                if v and not previous:runs+=1
                longest=max(current,longest);previous=v
            def streak(seq):
                n=0
                for v in seq:
                    if not v:break
                    n+=1
                return n
            base=prefix+'_'+which
            f.update({base+'_count':sum(row),base+'_runs':runs,base+'_longest_run':longest,
                      base+'_lsb_run':streak(row),base+'_msb_run':streak(reversed(row))})
            for b in range(4):f[base+'_bin'+str(b)]=sum(v for i,v in enumerate(row) if min(3,4*i//w)==b)
    fields=('consumer_count','consumer_mul','consumer_add','consumer_addcarry','consumer_lhs_max','consumer_rhs_max','consumer_result_max',
            'operand0_bindings','operand1_bindings','capture_banks','capture_declared_bits','mapped_dynamic_bits','mapped_unique_bits',
            'mapped_repeated_bits','mapped_zero_bits','mapped_one_bits','mapped_external_bits','mapped_undemanded_bits','mapped_origin_span',
            'mapping_runs','mapping_shift_min','mapping_shift_max')
    f.update(dict.fromkeys(fields,0));used=set();shifts=[]
    def mapping(row):
        previous=-2
        for i,bit in enumerate(row):
            if type(bit) is int:
                if not 0<=bit<r:raise ValueError('mapped producer bit out of range')
                f['mapped_dynamic_bits']+=1;used.add(bit)
                if bit!=previous+1:f['mapping_runs']+=1
                previous=bit;shifts.append(i-bit)
            elif type(bit) is str and bit in ('0','1','external','undemanded'):
                key={'0':'zero','1':'one','external':'external','undemanded':'undemanded'}[bit]
                f['mapped_'+key+'_bits']+=1;previous=-2
            else:raise ValueError('unknown bit-map token')
    for consumer in local['consumers']:
        spec=consumer['spec'];name=spec['operation']
        if name not in ('mul','add','addcarry'):raise ValueError('unsupported consumer operation')
        f['consumer_count']+=1;f['consumer_'+name]+=1
        for k in ('lhs','rhs','result'):f['consumer_'+k+'_max']=max(f['consumer_'+k+'_max'],_integer(spec[k+'_width'],k,1,257))
        seen=set()
        for binding in consumer['bindings']:
            index=_integer(binding['operand_index'],'operand index',0,1)
            if index in seen:raise ValueError('duplicate consumer operand')
            seen.add(index);f['operand'+str(index)+'_bindings']+=1
            if len(binding['result_bit_map'])!=spec[('lhs','rhs')[index]+'_width']:raise ValueError('consumer map width differs')
            mapping(binding['result_bit_map'])
    for capture in local['captures']:
        n=_integer(capture['banks'],'capture banks',1,4);w=_integer(capture['declared_width'],'capture width',1,257)
        if len(capture['result_bit_map'])!=w:raise ValueError('capture map width differs')
        f['capture_banks']+=n;f['capture_declared_bits']+=n*w
        for _ in range(n):mapping(capture['result_bit_map'])
    f.update(mapped_unique_bits=len(used),mapped_repeated_bits=f['mapped_dynamic_bits']-len(used),
             mapped_origin_span=max(used)-min(used)+1 if used else 0,
             mapping_shift_min=min(shifts) if shifts else 0,mapping_shift_max=max(shifts) if shifts else 0)
    return f


def queries(export,view,target,profile,boundary):
    """Independent extraction from full typed graph and actual logical cuts."""
    nodes={n['id']:n for n in export['nodes']};demand=demanded_bits(nodes,export['ports'])
    specs={at:from_shape(operator_shape(n,nodes,demand)) for at,n in nodes.items()
           if n['operation'] in ('mul','add','addcarry') and not n['constant'] and demand[at]}
    maps={};root_cache={}
    def origins(at):
        if at not in maps:maps[at]=bit_origins(nodes,at)
        return maps[at]
    def operand(a):
        if a['kind']=='symbol':return origins(a['node'])
        if a['kind']=='literal':return [str(bits(a['limbs_hex'])>>i&1) for i in range(a['width'])]
        raise ValueError('unknown operand origin')
    def roots(at):
        if at not in root_cache:
            n=nodes[at];root_cache[at]={at} if n['operation']=='input' else set().union(*(roots(a['node']) for a in n['operands'] if a['kind']=='symbol'))
        return root_cache[at]
    rows=[]
    for stage in view['stages']:
        paid=set(stage['semantic_members'])&specs.keys();children={at:set() for at in paid}
        for child in paid:
            for arg in nodes[child]['operands']:
                for bit in operand(arg):
                    if isinstance(bit,tuple) and bit[0] in paid and bit[0]!=child:children[bit[0]].add(child)
        depths={}
        def depth(at):
            if at not in depths:depths[at]=1+max((depth(c) for c in children[at]),default=0)
            return depths[at]
        for at in sorted(paid):
            def project(row):return [bit[1] if isinstance(bit,tuple) and bit[0]==at else bit if isinstance(bit,str) else 'external' for bit in row]
            consumers=[];captures=[]
            for child in sorted(paid-{at}):
                bindings=[]
                for index,arg in enumerate(nodes[child]['operands'][:2]):
                    row=project(operand(arg)[:specs[child][('lhs','rhs')[index]+'_width']])
                    row=[v if i<specs[child]['result_width'] else 'undemanded' for i,v in enumerate(row)]
                    if any(type(bit) is int for bit in row):bindings.append(dict(operand_index=index,result_bit_map=row))
                if bindings:consumers.append(dict(spec=specs[child],bindings=bindings,other_dynamic_inputs='independent_launch; source correlations require G validation'))
            for cap in stage['captures']:
                row=[bit if demand[cap['value']]>>i&1 else 'undemanded' for i,bit in enumerate(project(origins(cap['value'])))]
                if any(type(bit) is int for bit in row):captures.append(dict(banks=cap['banks'],declared_width=cap['declared_width'],result_bit_map=row))
            n=nodes[at];args=n['operands'];mask=demand[at]
            descriptor=dict(version=VERSION,semantics='unsigned-modulo-v1',declared_result_width=n['width'],
                required_result_bits=[i for i in range(n['width']) if mask>>i&1],
                local_context=dict(producer=specs[at],consumers=consumers,captures=captures),
                topology=dict(operand_shared_input_roots=len(roots(args[0]['node'])&roots(args[1]['node'])),same_stage_remaining_depth=depth(at)),
                flow_context=dict(target_platform='asap7',evaluation_stage='grt',target_period_ps=target,abc_target_ps=target,profile_sha256=profile,boundary_policy=boundary))
            rows.append(dict(trace=dict(node=at,stage=stage['index']),descriptor=deepcopy(descriptor),features=features(descriptor),qualified_price=False))
    return rows


def fixture_predict(query,*,production=False):
    """Nonconstant software fixture. Never a fitted or production model."""
    if production:return dict(status='cost_uncovered',reason='TEST_ONLY_model_not_production_qualified')
    f=features(query);mul=f['operation_mul']
    # Every coefficient is synthetic, deliberately simple for native parity.
    delay=(12+0.12*f['width_product'] if mul else 7+0.3*max(f['lhs_width'],f['rhs_width']))
    delay+=0.04*f['mapped_dynamic_bits']+0.02*f['consumer_result_max']+0.001*f['target_period_ps']
    area=(0.05*f['width_product'] if mul else 0.08*f['result_width'])+0.01*f['mapped_unique_bits']
    return dict(status='TEST_ONLY',delay_ps=delay,comb_area_um2=area,margin_ps=0.0,model_version='TEST_ONLY-operator-query-fixture-v1')
