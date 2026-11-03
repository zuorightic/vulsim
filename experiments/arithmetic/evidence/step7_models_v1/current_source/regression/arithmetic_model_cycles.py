"""Cycle scoreboard for the actual RTL selected by the native model test.

An explicit output capture makes the public L=3 transaction boundary visible.
The expected values use Python integer multiplication, never BEIR evaluation.
"""
import hashlib
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path


def run(directory):
    rng=random.Random(20261102);vectors=[];checks=valids=bubbles=resets=0;identities=[]
    for i in range(256):vectors.append((rng.randrange(256),rng.randrange(256),int(i<32 or i%7 not in (1,2,3)),int(i not in (0,1,65,66,150))))
    vectors += [(0,0,0,1)]*4
    for platform in ('asap7','nangate45','sky130hd','gf180'):
        for mode in ('','C.'):
            rtl=directory/(platform+'.'+mode+'sv');report=json.loads((directory/(platform+'.'+mode+'report.json')).read_text())
            actual=hashlib.sha256(rtl.read_bytes()).hexdigest()
            if actual!=report['rtl_sha256']:raise ValueError('RTL/report identity changed before cycle test')
            bench='''module Bench;
reg clk=0,rstn=0,iv=0;reg [7:0] a=0,b=0;wire [15:0] y;wire ov;
reg [15:0] observed=0;reg valid_observed=0;
top dut(.clk(clk),.rstn(rstn),.a(a),.b(b),.iv(iv),.ov(ov),.y(y));
always @(posedge clk)if(!rstn)begin observed<=0;valid_observed<=0;end else begin valid_observed<=ov;if(ov)observed<=y;end
initial begin
'''
            history=[];held=0
            for i,(a,b,iv,rst) in enumerate(vectors):
                if not rst:history=[];held=0;valid=0;resets+=1
                else:
                    history.append((a,b,iv));valid=int(len(history)>=3 and history[-3][2])
                    if valid:held=history[-3][0]*history[-3][1];valids+=1
                    else:bubbles+=1
                bench+=f'a=8\'d{a};b=8\'d{b};iv={iv};rstn={rst};#5;clk=1;#1;\n'
                bench+=f'if(valid_observed !== 1\'b{valid} || observed !== 16\'d{held})$fatal(1,"model cycle {platform}/{mode}/{i}");\n#4;clk=0;\n';checks+=2
            bench+='$display("MODEL_RTL_CYCLES_PASS");$finish;end endmodule\n'
            with tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);(p/'bench.sv').write_text(bench)
                subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(p/'sim'),str(rtl),str(p/'bench.sv')],check=True,capture_output=True)
                result=subprocess.run(['vvp',str(p/'sim')],check=True,capture_output=True,text=True)
                if 'MODEL_RTL_CYCLES_PASS' not in result.stdout:raise ValueError('missing cycle pass marker')
            identities.append({'platform':platform,'mode':'C' if mode else 'D_mechanism','rtl_sha256':actual})
    result={'status':'passed','checks':checks,'valid_transactions':valids,'bubble_hold_checks':bubbles,'reset_cycles':resets,
            'L':3,'II':1,'seed':20261102,'tested_RTL':identities,'quality_claim':'RTL correctness of selected implementation only; no fitted stage quality or candidate coverage assertion'}
    print(json.dumps(result));return result


if __name__=='__main__':run(Path(sys.argv[1]))
