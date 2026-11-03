"""Actual qualified models through source, scheduling and cycle scoreboards."""
import json
import random
import subprocess
import sys
import tempfile
from pathlib import Path
from experiments.arithmetic_dse.model_analysis import verify_report,verify_selection


def run(models,directory):
    count=cycles=0;rng=random.Random(20261102)
    vectors=[(rng.randrange(256),rng.randrange(256),rng.randrange(2),int(i%9 not in (2,3,4)),int(i not in (0,1,60,61,150))) for i in range(256)]
    vectors[2:6]=[(255,255,1,1,1),(255,0,1,1,1),(0,0,0,1,1),(128,128,1,1,1)]
    vectors += [(0,0,0,0,1)]*4
    for platform in ('asap7','nangate45','sky130hd','gf180'):
        bundle=json.loads((models/(platform+'.json')).read_text());reports=[]
        for context in (0,1):
            stem=platform+'.carry.context'+str(context);report=json.loads((directory/(stem+'.json')).read_text());rtl=(directory/(stem+'.sv')).read_text()
            cost=verify_report(report,bundle,rtl);verify_selection(report,bundle)
            if report['selection']['formal_D_selection'] is not True or report['selection']['evaluated_structures']!=1:raise ValueError('unexpected formal single-structure selection')
            reports.append(report);count+=1
            for mode in ('','C.'):
                source=directory/(stem+'.'+mode+'sv')
                bench='''module Bench;
reg clk=0,rstn=0,iv=0,carry=0;reg [7:0] a=0,b=0;wire [8:0] y;wire ov;
reg [8:0] observed=0;reg valid_observed=0;
carryTop dut(.clk(clk),.rstn(rstn),.a(a),.b(b),.carry(carry),.iv(iv),.ov(ov),.y(y));
always @(posedge clk)if(!rstn)begin observed<=0;valid_observed<=0;end else begin valid_observed<=ov;if(ov)observed<=y;end
initial begin
'''
                history=[];held=0
                for i,(a,b,c,iv,rst) in enumerate(vectors):
                    if not rst:history=[];held=0;valid=0
                    else:
                        history.append((a,b,c,iv));valid=int(len(history)>=3 and history[-3][3])
                        if valid:held=sum(history[-3][:3])
                    bench+=f'a=8\'d{a};b=8\'d{b};carry={c};iv={iv};rstn={rst};#5;clk=1;#1;\n'
                    bench+=f'if(valid_observed !== 1\'b{valid} || observed !== 9\'d{held})$fatal(1,"entry cycle {stem}/{mode}/{i}");\n#4;clk=0;\n';cycles+=2
                bench+='$display("QUALIFIED_ENTRY_CYCLES_PASS");$finish;end endmodule\n'
                with tempfile.TemporaryDirectory() as tmp:
                    p=Path(tmp);(p/'bench.sv').write_text(bench)
                    subprocess.run(['iverilog','-g2012','-s','Bench','-o',str(p/'sim'),str(source),str(p/'bench.sv')],check=True,capture_output=True)
                    result=subprocess.run(['vvp',str(p/'sim')],check=True,capture_output=True,text=True)
                    if 'QUALIFIED_ENTRY_CYCLES_PASS' not in result.stdout:raise ValueError('missing qualified entry cycle marker')
        a,b=reports
        if b['request']['target_period_ps']!=1.5*a['request']['target_period_ps'] or b['pipeline']['input_data_budget_ps']==a['pipeline']['input_data_budget_ps']:raise ValueError('second target did not reach actual schedule budget')
        def semantics(r):return [{k:n[k] for k in ('id','kind','opcode','width','dims','operands','hi','lo','bit','times')} for n in r['graph']['nodes']]
        if semantics(a)!=semantics(b):raise ValueError('fixed-structure context experiment changed semantics graph')
        count+=1
    result={'status':'passed','qualified_source_context_checks':count,'RTL_cycle_checks':cycles,'contexts_per_platform':2,'L':3,'II':1,
            'case':'independent dynamic AddCarry8; one structure, model/physical budget placement',
            'scope':'does not establish multiplication internal candidate coverage or global placement optimality'}
    print(json.dumps(result));return result


if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]))
