"""Successor consumer shells: independently observable banks and kept FF processes.

The old round-one source generator and evidence stay byte-identical. This fixes
observation/state preservation only; operator semantics and exact bit maps reuse
the same validated parameterized implementation.
"""
from . import model_context_samples as parent

VERSION='arithmetic-consumer-sampling-v2-independent-bank-observers'


def source(features,name='ModelBundle'):
    geometry=parent.layout(features);banks=len(geometry['captures']);text=parent.source(features,name)
    # Keep attributes on the sequential processes propagate to lowered FFs.
    text=text.replace('always @(posedge clk)','(* keep *) always @(posedge clk)')
    text=text.replace('output wire y,ov','output wire ['+str(banks-1)+':0] y,output wire ov')
    text=text.replace('output wire y)','output wire ['+str(banks-1)+':0] y)')
    old='assign y=^data;'
    if text.count(old)!=1:raise ValueError('unsupported parent observer')
    offset=0;assign=[]
    for i,bank in enumerate(geometry['captures']):
        width=len(bank['tokens']);assign.append(f'assign y[{i}]=^data[{offset}+:{width}];');offset+=width
    return text.replace(old,''.join(assign))


def geometry_contract(features):
    g=parent.layout(features)
    return dict(version=VERSION,features=features,input_bits=g['input_bits'],output_bits=g['output_bits'],
                launch_FF_bits=g['input_bits']+1,capture_FF_bits=sum(len(c['live_tokens']) for c in g['captures'])+1,
                banks=[dict(index=i,id=b['id'],logical_width=len(b['tokens']),FF_bits=len(b['live_tokens']),
                            live_positions=[b['tokens'].index(t) for t in b['live_tokens']]) for i,b in enumerate(g['captures'])],
                operator_boundary_policy='unsigned-op-hierarchy-v1',mapped_qualified=False)
