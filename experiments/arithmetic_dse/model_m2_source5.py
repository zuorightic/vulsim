"""Extend the frozen four-bank shell with a real fifth kept capture bank."""
import re
from .model_m2_samples import source as four_bank_source


def once(text,before,after):
    if text.count(before)!=1:raise ValueError('unsupported fixed sampling shell')
    return text.replace(before,after,1)


def source(family,width,cfg,fp_core):
    text,labels=four_bank_source(family,width,4,cfg,fp_core)
    for index,label in enumerate(labels):
        sid=label['id'];result=label['result_width']
        pattern=rf'module Cell_{sid}\(.*?endmodule\n'
        match=re.search(pattern,text,re.S)
        if not match:raise ValueError('missing registered Cell module')
        block=once(match[0],'output wire y3);','output wire y3,output wire y4);')
        bank=f'(* keep,dont_touch *) reg [{result-1}:0] dst4;(* keep *) always @(posedge clk)dst4<=value;assign y4=^dst4;\n'
        block=once(block,'endmodule\n',bank+'endmodule\n')
        text=text[:match.start()]+block+text[match.end():]
        text=once(text,f'output wire y{index}_b3',f'output wire y{index}_b3,\noutput wire y{index}_b4')
        text=once(text,f'.y3(y{index}_b3));',f'.y3(y{index}_b3),.y4(y{index}_b4));')
        label['fanout']=5
        label['capture_banks'].append({'id':sid+'_bank4','target_cells':[sid+'/dst4*']+([sid+'/y4*'] if result==1 else []),'static_bit_capacity':result})
    return text,labels
