"""Isolated primitive/atomic-region sampling shells for the ASAP7 M2 scope."""
from .model_collection import expression


def family_specs(family,width,cfg):
    return [op for op in cfg['families'][family]['operations']
            if not (op.startswith('mul') and width>cfg['families'][family].get('multiply_max_width',width))]


def sample_expression(op,width):
    if op=='add_wide':return "{1'b0,a} + {1'b0,b}",width,width+1,'carry'
    if op=='fp32':return None,32,37,'fp37'
    return expression(op,width)


def source(family,width,fanout,cfg,fp_core):
    if not 1<=fanout<=4:raise ValueError('bounded capture-bank count required')
    modules=[];ports=['input wire clk,rstn,iv','output reg ov'];instances=[];labels=[]
    for index,op in enumerate(family_specs(family,width,cfg)):
        sid=f's{index:03d}';expr,rhs,result,shape=sample_expression(op,width)
        core=f'(* keep_hierarchy=1 *) module Core_{sid}(input wire [{width-1}:0] a,input wire [{max(rhs,1)-1}:0] b,input wire cin,output wire [{result-1}:0] value);\n'
        core+=('AtomicFp fp(.a(a),.b(b),.value(value));\n' if op=='fp32' else 'assign value='+expr+';\n')
        modules.append(core+'endmodule\n')
        module=f'(* keep_hierarchy=1 *) module Cell_{sid}(input wire clk,rstn,iv,input wire [{width-1}:0] in_a,input wire [{max(rhs,1)-1}:0] in_b,input wire in_c,'
        module+=','.join(f'output wire y{bank}' for bank in range(fanout))+');\n'
        divisor=op in ('div','mod')
        module+=f'(* keep *) reg [{width-1}:0] src_a;(* keep *) reg [{max(rhs,1)-1}:0] src_b;(* keep *) reg src_c;\n'
        safe='(in_b==0 ? 1 : in_b)' if divisor else 'in_b'
        module+=f'always @(posedge clk)if(!rstn)begin src_a<=0;src_b<={1 if divisor else 0};src_c<=0;end else if(iv)begin src_a<=in_a;src_b<={safe};src_c<=in_c;end\n'
        module+=f'wire [{result-1}:0] value;Core_{sid} core(.a(src_a),.b(src_b),.cin(src_c),.value(value));\n'
        for bank in range(fanout):
            module+=f'(* keep,dont_touch *) reg [{result-1}:0] dst{bank};(* keep *) always @(posedge clk)dst{bank}<=value;assign y{bank}=^dst{bank};\n'
        modules.append(module+'endmodule\n')
        def declaration(bits,name):return f'input wire '+(f'[{bits-1}:0] ' if bits>1 else '')+name
        ports += [declaration(width,f'a{index}'),declaration(max(rhs,1),f'b{index}'),f'input wire c{index}']
        connections=['.clk(clk)','.rstn(rstn)','.iv(iv)',f'.in_a(a{index})',f'.in_b(b{index})',f'.in_c(c{index})']
        for bank in range(fanout):
            ports.append(f'output wire y{index}_b{bank}');connections.append(f'.y{bank}(y{index}_b{bank})')
        instances.append(f'Cell_{sid} {sid}('+','.join(connections)+');')
        semantic_op='mul' if op=='mul_low' else 'add' if op=='add_wide' else op
        label={'id':sid,'operation':semantic_op,'rtl_operation':op,'lhs_width':width,'rhs_width':0 if op.startswith('mux') else rhs,
               'input_widths':[width,max(rhs,1),1],'result_width':result,'capture_width':result,
               'result_shape':shape,'fanout':fanout,'source_cells':sid+'/src*',
               'target_cells':[sid+'/dst*']+([sid+'/y*'] if result==1 else []),'instance_scope':sid+'/','arithmetic_scope':sid+'/core/',
               'role':'isolated_atomic_region' if op=='fp32' else 'isolated_primitive',
               'boundary':'reset/enable before launch Q; unconditional real capture banks; no external arithmetic in this sample'}
        if fanout>1:
            label['capture_banks']=[{'id':sid+f'_bank{k}','target_cells':[sid+f'/dst{k}*']+([sid+f'/y{k}*'] if result==1 else []),'static_bit_capacity':result} for k in range(fanout)]
        labels.append(label)
    if family=='binary32':modules.insert(0,fp_core)
    text='\n'.join(modules)+'module ModelBundle('+',\n'.join(ports)+');\nalways @(posedge clk)if(!rstn)ov<=0;else ov<=iv;\n'+'\n'.join(instances)+'\nendmodule\n'
    return text,labels
