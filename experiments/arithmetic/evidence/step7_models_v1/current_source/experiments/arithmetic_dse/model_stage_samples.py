"""Versioned, single-output synthetic graph definitions for stage training.

The generator returns an explicit operand graph. The RTL test uses a separate
integer evaluator of this graph, including every intermediate truncation.
"""
import json
from .model_calibration import CALIBRATION


def specs(split):
    cfg=json.loads(CALIBRATION.read_text());s=cfg['splits'][split];result=[]
    for w in cfg['state_widths']:
        result.append({'role':'state','topology':'state','lhs_width':w,'result_width':w,'input_widths':[w],'graph_nodes':[]})
    for operation in cfg['primitive_operations']:
        for w in s['primitive_widths']:
            width=2*w if operation=='mul' else w+1 if operation=='addcarry' else w
            inputs=[w,w]+([1] if operation=='addcarry' else [])
            node={'operation':'mul' if operation=='mul_low' else operation,'lhs_width':w,'rhs_width':w,'result_width':width,
                  'inputs':[],'operand_sources':[{'input':i} for i in range(len(inputs))]}
            result.append({'role':'synthetic_context','topology':'primitive_'+operation,'lhs_width':w,'result_width':width,'input_widths':inputs,'graph_nodes':[node]})
    for w in s['context_widths']:
        for products in range(1 if split=='train' else 2,5):
            inputs=[];nodes=[];width=2*w
            def external(bits):
                inputs.append(bits);return {'input':len(inputs)-1}
            def op(kind,a,b,lhs=width,rhs=width):
                sources=[a,b];nodes.append({'operation':kind,'lhs_width':lhs,'rhs_width':rhs,'result_width':width,
                    'inputs':[v['node'] for v in sources if 'node' in v], 'operand_sources':sources})
                return {'node':len(nodes)-1}
            values=[op('mul',external(w),external(w),w,w) for _ in range(products)]
            if split=='train':
                value=values[0]
                for other in values[1:]:value=op('add',value,other)
                for _ in range(2):value=op('add',value,external(width))
            else:
                # Distinct branch depths/topologies across validation and test;
                # neither reproduces a registered formal MAC/DOT2 graph.
                for k in range(products):
                    depth=1 if split=='validation' else (2 if k==0 else 1 if k==products-1 else 0)
                    for _ in range(depth):values[k]=op('add',values[k],external(width))
                while len(values)>1:
                    values=[op('add',values[k],values[k+1]) if k+1<len(values) else values[k] for k in range(0,len(values),2)]
                value=values[0]
            assert value=={'node':len(nodes)-1}
            result.append({'role':'synthetic_context','topology':f'{split}_products_{products}','lhs_width':w,'result_width':width,
                           'input_widths':inputs,'graph_nodes':nodes})
    return result


def source(split,fanout_override=None):
    cfg=json.loads(CALIBRATION.read_text());fan=cfg['splits'][split]['fanout'] if fanout_override is None else fanout_override;modules=[]
    if type(fan) is not int or fan<1:raise ValueError('positive integer capture fanout required')
    ports=['input wire clk,rstn,iv','output reg ov'];instances=[];labels=[]
    def port_range(w):return f'[{w-1}:0] ' if w>1 else ''
    for i,spec in enumerate(specs(split)):
        name=f's{i:03d}';width=spec['result_width'];inputs=spec['input_widths'];nodes=spec['graph_nodes']
        coreports=[f'input wire {port_range(w)}x{k}' for k,w in enumerate(inputs)]
        expr=''
        for k,node in enumerate(nodes):
            operands=['v'+str(v['node']) if 'node' in v else 'x'+str(v['input']) for v in node['operand_sources']]
            if node['operation']=='mul':value=' * '.join(operands)
            elif node['operation']=='add':value=' + '.join(operands)
            elif node['operation']=='addcarry':value="{1'b0,"+operands[0]+"} + {1'b0,"+operands[1]+'} + '+operands[2]
            else:raise ValueError('unregistered stage operation')
            expr+=f'wire [{node["result_width"]-1}:0] v{k}={value};\n'
        if nodes:
            modules.append(f'(* keep_hierarchy=1 *) module Core_{name}('+','.join(coreports)+f',output wire [{width-1}:0] value);\n'+expr+f'assign value=v{len(nodes)-1};\nendmodule\n')
        args=[f'input wire {port_range(w)}in{k}' for k,w in enumerate(inputs)]
        module=f'(* keep_hierarchy=1 *) module Cell_{name}(input wire clk,rstn,iv,'+','.join(args)+f',output wire [{fan*width-1}:0] y);\n'
        for k,w in enumerate(inputs):module+=f'(* keep *) reg [{w-1}:0] src{k};always @(posedge clk)if(!rstn)src{k}<=0;else if(iv)src{k}<=in{k};\n'
        value='src0'
        if nodes:
            module+=f'wire [{width-1}:0] value;Core_{name} core('+','.join(f'.x{k}(src{k})' for k in range(len(inputs)))+',.value(value));\n';value='value'
        for b in range(fan):
            control='if(!rstn)dst'+str(b)+'<=0;else if(iv)' if not nodes else ''
            module+=f'(* keep *) reg [{width-1}:0] dst{b};(* keep *) always @(posedge clk){control}dst{b}<={value};assign y[{b*width} +: {width}]=dst{b};\n'
        modules.append(module+'endmodule\n');connections=['.clk(clk)','.rstn(rstn)','.iv(iv)']
        for k,w in enumerate(inputs):ports.append(f'input wire {port_range(w)}x{i}_{k}');connections.append(f'.in{k}(x{i}_{k})')
        if cfg.get('observer'):
            ports.append(f'output wire y{i}');connections.append(f'.y(captured_{i})')
            instances.append(f'wire [{fan*width-1}:0] captured_{i};assign y{i}=^captured_{i};')
        else:ports.append(f'output wire [{fan*width-1}:0] y{i}');connections.append(f'.y(y{i})')
        instances.append(f'Cell_{name} {name}('+','.join(connections)+');')
        labels.append({**spec,'id':name,'source_cells':name+'/src*','target_cells':[name+'/y*',name+'/dst*'],'instance_scope':name+'/',
                       'arithmetic_scope':name+'/core/','fanout':fan,'observer':bool(cfg.get('observer')),
                       'no_formal_or_holdout_case_replication':True,'state_reset':'synchronous_zero','state_enable':True})
    text='\n'.join(modules)+'\nmodule ModelBundle('+',\n'.join(ports)+');\nalways @(posedge clk)if(!rstn)ov<=0;else ov<=iv;\n'+'\n'.join(instances)+'\nendmodule\n'
    return text,labels
