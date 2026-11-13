"""Opt-in Add Query/feature/RTL contract with explicit operand permutation.

The external operand wires retain their widths, masks and identities. Only
their deterministic binding to the two internal arithmetic operands changes.
No physical label or qualified price is inferred from this software contract.
"""
from copy import deepcopy
from .operator_interval_features import features as interval_features, variable_positions

VERSION = 'canonical-add-query-v1'
BOUNDARY_POLICY = 'unsigned-add-normalized-operands-v1'


def operand_key(spec, prefix):
    positions = variable_positions(spec,prefix,spec['result_width'])
    # Effective geometry leads the order; declaration and mask tie breakers
    # make the emitted operand bindings deterministic as well.
    return (len(positions),max(positions,default=-1)+1,min(positions,default=0),
            spec[prefix+'_width'],int(spec[prefix+'_zero_hex'],16),
            int(spec[prefix+'_one_hex'],16))


def normalize(query):
    interval_features(query)  # Validate the existing Query ABI first.
    q=deepcopy(query);p=q['local_context']['producer']
    if p['operation']!='add' or p['carry']!='zero':
        raise ValueError('canonical Add scope requires unsigned zero-carry Add')
    if any(int(p[n+'_one_hex'],16) for n in ('lhs','rhs')):
        raise ValueError('canonical Add first scope excludes known-one operands')
    for prefix in ('lhs','rhs'):
        for kind in ('zero','one'):p[prefix+'_'+kind+'_hex']=hex(int(p[prefix+'_'+kind+'_hex'],16))
    swap=operand_key(p,'rhs')>operand_key(p,'lhs')
    if swap:
        for field in ('width','zero_hex','one_hex'):
            p['lhs_'+field],p['rhs_'+field]=p['rhs_'+field],p['lhs_'+field]
    q['flow_context']['boundary_policy']=BOUNDARY_POLICY
    return dict(version=VERSION,descriptor=q,operand_permutation=[1,0] if swap else [0,1],
                boundary_policy=BOUNDARY_POLICY,consumer_result_connections_preserved=True,
                physical_mapping_equivalence_qualified=False,price_qualification_granted=False)


def features(query):
    return interval_features(normalize(query)['descriptor'])


def core_source(query,name):
    if not name.isidentifier():raise ValueError('safe core identifier required')
    contract=normalize(query);spec=query['local_context']['producer'];r=spec['result_width']
    def masked(prefix,value):
        w=spec[prefix+'_width'];zero=int(spec[prefix+'_zero_hex'],16);one=int(spec[prefix+'_one_hex'],16)
        return f"(({value} & {w}'h{(((1<<w)-1)&~(zero|one)):x}) | {w}'h{one:x})"
    names=['masked_a','masked_b'];a,b=(names[i] for i in contract['operand_permutation'])
    return (f'// {BOUNDARY_POLICY}\n'
            f'(* keep_hierarchy=1 *) module {name}(input wire [{spec["lhs_width"]-1}:0] a,input wire [{spec["rhs_width"]-1}:0] b,input wire cin,output wire [{r-1}:0] value);\n'
            f'wire [{spec["lhs_width"]-1}:0] masked_a={masked("lhs","a")};\n'
            f'wire [{spec["rhs_width"]-1}:0] masked_b={masked("rhs","b")};\n'
            f"wire [{r-1}:0] canonical_lhs={r}'({a});\n"
            f"wire [{r-1}:0] canonical_rhs={r}'({b});\n"
            'assign value=canonical_lhs+canonical_rhs;\nendmodule\n'),contract


def sampling_source(features,query,name='ModelBundle'):
    from . import model_sampling_v2,model_fast_samples
    if features['producer']!=query['local_context']['producer']:
        raise ValueError('sampling spec and original Query producer differ')
    text=model_sampling_v2.source(features,name);child=name+'Producer'
    marker='(* keep_hierarchy=1 *) module '+child+'('
    original=model_fast_samples.source(features['producer'],child).split(marker)[0]
    replacement,contract=core_source(query,child+'Core')
    if text.count(original)!=1:raise ValueError('sampling producer definition not unique')
    return text.replace(original,replacement),contract
