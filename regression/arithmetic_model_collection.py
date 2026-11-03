"""Execute generated isolated sample RTL against independent integer results."""
import json
import random
import subprocess
import tempfile
import unittest
from pathlib import Path

from experiments.arithmetic_dse.model_collection import bundle_source,expression


def reference(op,w,a,b,c):
    mask=(1<<w)-1
    values={'mul':a*b,'mul_low':a*b,'add':a+b,'sub':a-b,'addcarry':a+b+c,
            'and':a&b,'or':a|b,'xor':a^b,'compare_eq':int(a==b),'compare_rel':int(a<b),
            'eq_zero':int(a==0),'not':~a,'neg':-a,'reduce_or':int(a!=0),
            'reduce_and':int(a==mask),'reduce_xor':a.bit_count()%2,
            'mux':a if c else b,'mux_zero':a if c else 0,'mux_one':a if c else 1,
            'mux_ones':a if c else mask,'shl':a<<b if b<w else 0,'shr':a>>b,
            'div':a//(b if b else 1),'mod':a%(b if b else 1)}
    out=expression(op,w)[2]
    return values[op]&((1<<out)-1)


class Collection(unittest.TestCase):
    def test_actual_RTL_all_registered_expressions_and_fanout(self):
        ops=['mul','mul_low','add','sub','addcarry','and','or','xor','compare_eq','compare_rel','eq_zero','not','neg','reduce_or','reduce_and','reduce_xor','mux','mux_zero','mux_one','mux_ones','shl','shr','div','mod']
        specs=[(op,w) for op in ops for w in (2,4,8,16,32)]
        rng=random.Random(20261102);checks=0
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            for fan in (1,2,3,4,5,6):
                source,labels=bundle_source(specs,fan)
                bench='module Bench;reg clk=0,rstn=0,iv=1;wire ov;\n';connections=['.clk(clk)', '.rstn(rstn)', '.iv(iv)', '.ov(ov)']
                for i,(_,w) in enumerate(specs):
                    rhs=labels[i]['rhs_width'];out=labels[i]['result_width'];bench+=f'reg [{w-1}:0] a{i};reg [{max(rhs,1)-1}:0] b{i};reg c{i};wire [{fan*out-1}:0] y{i};\n'
                    connections.extend(f'.{k}{i}({k}{i})' for k in ('a','b','c','y'))
                bench+='ModelBundle dut('+','.join(connections)+');\ninitial begin\n'
                for iteration in range(16):
                    values=[]
                    for i,(op,w) in enumerate(specs):
                        rhs=labels[i]['rhs_width'];a=rng.getrandbits(w);b=rng.getrandbits(max(rhs,1));c=rng.getrandbits(1)
                        if iteration==0:a=b=0
                        if iteration==1:a=(1<<w)-1;b=(1<<max(rhs,1))-1
                        bench+=f'a{i}={w}\'h{a:x};b{i}={max(rhs,1)}\'h{b:x};c{i}={c};\n';values.append(reference(op,w,a,b,c))
                    bench+='rstn=1;#5;clk=1;#5;clk=0;#5;clk=1;#5;clk=0;#1;\n'
                    for i,value in enumerate(values):
                        width=labels[i]['result_width'];packed=sum(value<<(k*width) for k in range(fan));checks+=fan
                        bench+=f'if(y{i} !== {fan*width}\'h{packed:x}) $fatal(1,"sample {i} fanout {fan} iteration {iteration}");\n'
                bench+='$display("COLLECTION_FUNCTIONAL_PASS");$finish;end endmodule\n'
                (root/'samples.sv').write_text(source+'\n'+bench)
                subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(root/'sim'),str(root/'samples.sv')],check=True,capture_output=True)
                run=subprocess.run(['vvp',str(root/'sim')],check=True,capture_output=True,text=True)
                self.assertIn('COLLECTION_FUNCTIONAL_PASS',run.stdout)
        print(json.dumps({'generated_RTL_sample_output_checks':checks,'widths':[2,4,8,16,32],'fanouts':[1,2,3,4,5,6],'seed':20261102}))


if __name__=='__main__':unittest.main()
