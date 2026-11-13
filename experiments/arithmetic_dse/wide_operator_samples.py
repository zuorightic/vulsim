"""Retained local shells for wide finite-bit operators and explicit demands."""
from copy import deepcopy
from types import FunctionType
import inspect
from . import wide_arithmetic as arithmetic,model_context_samples as parent,model_mapped_contract as mapped

VERSION='wide-family-retained-consumer-shell-v1'


def check_map(mapping,width,result):
    if type(width) is not int or not 1<=width<=arithmetic.MAX_WIDTH or len(mapping)!=width:raise ValueError('incomplete wide bit map')
    for bit in mapping:
        if type(bit) is int:
            if not 0<=bit<result:raise ValueError('mapped wide producer bit outside demand')
        elif type(bit) is not str or bit not in ('0','1','external','undemanded'):raise ValueError('unknown wide bit origin')


def validate(f):
    if set(f)!={'producer','consumers','captures'}:raise ValueError('explicit wide local context required')
    arithmetic.validate(f['producer'])
    if not f['consumers'] and not f['captures']:raise ValueError('unobserved wide producer')
    if len(f['consumers'])>1:raise ValueError('first wide scope has at most one real consumer')
    for c in f['consumers']:
        if set(c)!={'spec','bindings','other_dynamic_inputs'} or c['other_dynamic_inputs']!='independent_launch; source correlations require G validation':raise ValueError('unregistered wide consumer semantics')
        arithmetic.validate(c['spec']);seen=set()
        for b in c['bindings']:
            index=b['operand_index']
            if set(b)!={'operand_index','result_bit_map'} or type(index) is not int or index not in (0,1) or index in seen:raise ValueError('invalid wide consumer binding')
            seen.add(index);check_map(b['result_bit_map'],c['spec'][('lhs','rhs')[index]+'_width'],f['producer']['result_width'])
        if not seen or not any(type(v) is int for b in c['bindings'] for v in b['result_bit_map']):raise ValueError('consumer does not use producer')
    for cap in f['captures']:
        if set(cap)!={'banks','declared_width','result_bit_map'} or type(cap['banks']) is not int or not 1<=cap['banks']<=4:raise ValueError('capture bank bound')
        check_map(cap['result_bit_map'],cap['declared_width'],f['producer']['result_width'])
    return f


def input_demand(s,prefix):
    alias=arithmetic.aliases(s)
    if alias is not None:return {v[1] for v in alias if isinstance(v,list) and v[0]==prefix}
    if s['operation']=='mux':return set(range(s['result_lo'],s['result_lo']+s['value_width']))
    if s['operation'] in ('ult','ule','eq'):return set(range(s[prefix+'_width']))
    high=s['arithmetic_width'] if s['status']!='none' else s['result_lo']+s['value_width']
    return set(range(min(s[prefix+'_width'],high)))


def layout(f):
    validate(f);inputs=[];nodes=[];captures=[];pzero,pone=arithmetic.known_result(f['producer'])
    def allocate(label):inputs.append(label);return ('input',len(inputs)-1)
    def token(bit):
        if type(bit) is int:return '0' if pzero>>bit&1 else '1' if pone>>bit&1 else ('producer',bit)
        return allocate('capture_external') if bit=='external' else '0' if bit=='undemanded' else bit
    def operands(s,bindings,label):
        result=[]
        for index,prefix in enumerate(('lhs','rhs')):
            needed=input_demand(s,prefix);row=[]
            for i in range(s[prefix+'_width']):
                choices=arithmetic.bit_values(s,prefix,i)
                if i not in needed:value='0'
                elif len(choices)==1:
                    value=str(choices[0])
                    if index in bindings and bindings[index][i] not in (value,'external','undemanded') and token(bindings[index][i])!=value:raise ValueError('wide binding contradicts known bit')
                elif index in bindings:value=token(bindings[index][i])
                else:value=allocate(label+'/'+prefix+'/'+str(i))
                row.append(value)
            result.append(row)
        result.append([allocate(label+'/control') if s['carry']=='dynamic' else '1' if s['carry']=='one' else '0']);return result
    nodes.append(operands(f['producer'],{},'producer'))
    for i,c in enumerate(f['consumers']):
        nodes.append(operands(c['spec'],{b['operand_index']:b['result_bit_map'] for b in c['bindings']},'consumer'+str(i)));z,o=arithmetic.known_result(c['spec']);captures.append(dict(id='consumer'+str(i),tokens=['0' if z>>j&1 else '1' if o>>j&1 else ('consumer'+str(i),j) for j in range(c['spec']['result_width'])]))
    for i,c in enumerate(f['captures']):
        mapped_bits=[token(b) for b in c['result_bit_map']]
        for bank in range(c['banks']):captures.append(dict(id='direct'+str(i)+'bank'+str(bank),tokens=mapped_bits))
    for c in captures:c['live_tokens']=list(dict.fromkeys(v for v in c['tokens'] if isinstance(v,tuple)))
    if not inputs or not any(c['live_tokens'] for c in captures):raise ValueError('fully constant wide context has no measured arithmetic')
    return dict(inputs=inputs,node_inputs=nodes,captures=captures,input_bits=len(inputs),output_bits=sum(len(c['tokens']) for c in captures),undemanded_policy='operation-specific dependency proof; high-product lower carries retained',independent_consumer_inputs=True)


def evaluate(f,word):
    g=layout(f);values={}
    def bit(t):return int(t) if isinstance(t,str) else (word if t[0]=='input' else values[t[0]])>>t[1]&1
    def vector(tokens):return sum(bit(t)<<i for i,t in enumerate(tokens))
    for i,(s,operands) in enumerate(zip([f['producer']]+[c['spec'] for c in f['consumers']],g['node_inputs'])):
        a,b,c=[vector(v) for v in operands];values['producer' if i==0 else 'consumer'+str(i-1)]=arithmetic.evaluate(s,a,b,c)
    result=offset=0
    for c in g['captures']:result|=vector(c['tokens'])<<offset;offset+=len(c['tokens'])
    return result


def source(f,name='ModelBundle'):
    ns=dict(parent.source.__globals__);ns.update(layout=layout,arithmetic=arithmetic)
    text=FunctionType(parent.source.__code__,ns)(f,name);banks=len(layout(f)['captures'])
    text=text.replace('always @(posedge clk)','(* keep *) always @(posedge clk)').replace('output wire y,ov',f'output wire [{banks-1}:0] y,output wire ov').replace('output wire y)',f'output wire [{banks-1}:0] y)')
    if text.count('assign y=^data;')!=1:raise ValueError('wide observer contract drift')
    offset=0;assign=[]
    for i,c in enumerate(layout(f)['captures']):width=len(c['tokens']);assign.append(f'assign y[{i}]=^data[{offset}+:{width}];');offset+=width
    return text.replace('assign y=^data;',''.join(assign))


def geometry_contract(f):
    g=layout(f)
    return dict(version=VERSION,features=f,input_bits=g['input_bits'],output_bits=g['output_bits'],launch_FF_bits=g['input_bits']+1,capture_FF_bits=sum(len(c['live_tokens']) for c in g['captures'])+1,banks=[dict(index=i,id=c['id'],logical_width=len(c['tokens']),FF_bits=len(c['live_tokens'])) for i,c in enumerate(g['captures'])],operator_boundary_policy=arithmetic.POLICY,mapped_qualified=False)


def _adapt(function):
    text=inspect.getsource(function).replace('from .model_sampling_v2 import geometry_contract','from .wide_operator_samples import geometry_contract').replace('from .model_context_samples import layout','from .wide_operator_samples import layout')
    ns=dict(function.__globals__);exec(compile(text,__file__,'exec'),ns);return ns[function.__name__]


mapped_contract=_adapt(mapped.mapped_contract)
render_query_contract=_adapt(mapped.render_query_contract)
operator_port_contract=mapped.operator_port_contract
