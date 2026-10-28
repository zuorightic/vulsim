#!/usr/bin/env python3
"""Step5 native RTL vs independent integer products, including cycle protocol.

This regression makes no PPA calls. Generation, builds and RTL execution are
support leaf commands in the shared ledger. CIRCT is outside this native test.
"""
import argparse
import json
import os
from pathlib import Path
import random
import sys
import uuid

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.backend import sha256,write_json
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.processes import run_command
from experiments.arithmetic_dse.simple_cost import candidate_score

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build'/('step5-mul-split-'+uuid.uuid4().hex[:12]),
                        help='new output directory; default creates a unique build directory for regression.sh')
    parser.add_argument('--rtlzz-build',type=Path,default=ROOT/'build/step4-rtlzz')
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args();out=args.output.resolve();build=args.rtlzz_build.resolve()
    if out.exists():parser.error('use a new output directory to preserve evidence')
    out.mkdir(parents=True);ledger=Ledger();before=ledger.summary();commands=[]
    def run(command,stem,timeout=300):
        reservation=ledger.reserve(None,timeout,2,'step5_functional',command,out/stem)
        record=run_command(command,out,stem,timeout,os.environ.copy(),cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record);record['budget_reservation_id']=reservation['id'];commands.append(record)
        write_json(out/'commands.json',commands)
        if record['exit_code']:raise RuntimeError(f'{stem}: see {record["log"]}')
        return Path(record['log']).read_text()
    if not args.skip_build:
        run(['cmake','-S',ROOT/'rtlzz','-B',build],'configure')
        run(['cmake','--build',build,'--target','mul-split-test','-j2'],'build')
    structure=run([build/'testv2/mul-split-test',ROOT/'vullib',out],'generation')
    assert 'PASS automatic mul split' in structure
    wrapper='''`timescale 1ns/1ps
module MulSplitRegression(input logic clk,rstn,iv,input logic [31:0] a,b,
output logic [63:0] y0,y1,output logic ov0,ov1);
original u0(.clk(clk),.rstn(rstn),.a(a),.b(b),.iv(iv),.y(y0),.ov(ov0));
mul32_split16 u1(.clk(clk),.rstn(rstn),.a(a),.b(b),.iv(iv),.y(y1),.ov(ov1));
endmodule
'''
    (out/'wrapper.sv').write_text(wrapper)
    run(['verilator','--cc','--exe','--build','-j','2','--top-module','MulSplitRegression','--Mdir',out/'obj',
         out/'wrapper.sv',out/'original.sv',out/'mul32_split16.sv',ROOT/'regression/arithmetic_mul_split/rtl_driver.cpp'],'verilator')
    seed=20261028;rng=random.Random(seed)
    edges=[0,1,2,3,0x7fff,0x8000,0xffff,0x10000,0x10001,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    pairs=[(a,b) for a in edges for b in edges]
    # Exercise each one-hot partial-product cross term, and all carry boundaries.
    pairs += [(1<<a,1<<b) for a in range(32) for b in range(32)]
    pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(20000)]
    rows=[(a,b,int(i<1193 or i%7 not in (1,2)),int(i not in (0,400,401,1000,8000,16000))) for i,(a,b) in enumerate(pairs)]
    rows += [(0,0,0,1)]*4
    (out/'vectors.txt').write_text(''.join(f'{a:x} {b:x} {iv:x} {rst:x}\n' for a,b,iv,rst in rows))
    observed=run([out/'obj/VMulSplitRegression',out/'vectors.txt'],'rtl').splitlines()
    assert len(observed)==len(rows)
    history=[];last=0;valid_checks=data_checks=bubble_checks=reset_checks=0
    for cycle,(row,line) in enumerate(zip(rows,observed)):
        a,b,iv,rst=row;values=[int(v,16) for v in line.split()];assert len(values)==4
        if not rst:
            history=[];expected_valid=0;last=0;reset_checks+=2
        else:
            history.append((iv,a*b))
            expected_valid=len(history)>=3 and history[-3][0]
            if expected_valid:last=history[-3][1];data_checks+=2
            else:bubble_checks+=2
        for index in (0,2):
            assert values[index+1]==expected_valid,(cycle,'valid',index,values,expected_valid)
            assert values[index]==last,(cycle,'product/hold/reset',index,values,last)
            valid_checks+=1
    candidates=json.loads((out/'candidates.json').read_text())
    chosen=min(candidates,key=lambda c:candidate_score(c['delay'],c['combinational_cost'],c['register_bits'],c['register_count'],c['id']))
    assert chosen['id']=='mul32_split16'
    assert candidates[1]['internal_region_registers']>0
    artifacts=['original.sv','mul32_split16.sv','mul_kernel.logic.cpp','schedule.txt','candidates.json','wrapper.sv']
    report={'version':'step5-mul-split-regression-v1','status':'passed','seed':seed,'cycles':len(rows),
            'cases':'directed unsigned boundaries, all one-hot pairs, 20000 random products, continuous inputs, bubbles, six reset cycles and drain',
            'valid_checks':valid_checks,'valid_product_checks':data_checks,'bubble_hold_checks':bubble_checks,'reset_checks':reset_checks,
            'candidates':candidates,'simple_cost_version':'simple-cost-v1.1/effective-width-v2',
            'C_choice_before_PPA':chosen['id'],'L':2,'II':1,'latency_scope':'input Q to output Q, N=L-1; external transaction sampled at tick t appears at t+2',
            'emitter':'native','CIRCT':'outside this native regression; existing CIRCT policy unchanged',
            'commands':commands,'usage_before':before,'usage_after':ledger.summary(),
            'new_PPA_calls':{'synth':0,'grt':0,'final':0},'artifacts_sha256':{p:sha256(out/p) for p in artifacts}}
    write_json(out/'regression.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('commands','artifacts_sha256')},ensure_ascii=False,indent=2))
    return 0
if __name__=='__main__':raise SystemExit(main())
