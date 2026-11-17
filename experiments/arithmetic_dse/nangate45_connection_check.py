"""Finite RTL functional validation, charged as one shared support leaf."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

from . import budget
from . import workload_nine_runtime as runtime
from .nangate45_connection import ROOT, TASKS, read, write, sha, verify
from .nangate45_migration import SCOPE, software_root
from .processes import run_command
from .workload_software_validation import bench


def checks(root):
    root = Path(root).resolve()
    verify(root/'connection')
    destination = root/'functional'
    destination.mkdir(exist_ok=False)
    rows=[]
    def simulate(rtl, tb, name):
        work=destination/name;work.mkdir()
        (work/'tb.sv').write_text(tb)
        for command,log in [(['iverilog','-g2012','-s','tb','-o',str(work/'sim'),str(rtl),str(work/'tb.sv')], 'compile.log'),
                            (['vvp',str(work/'sim')], 'simulation.log')]:
            with (work/log).open('w') as output:
                subprocess.run(command,check=True,stdout=output,stderr=subprocess.STDOUT,timeout=120)
        if 'PASS' not in (work/'simulation.log').read_text():
            raise ValueError('RTL functional simulation did not pass')
        return dict(name=name,rtl_sha256=sha(rtl),testbench_sha256=sha(work/'tb.sv'),
            log_sha256=sha(work/'simulation.log'),status='passed')
    for name in TASKS:
        result=33 if name=='add32' else 16 if name=='mac8' else 64
        width=8 if name=='mac8' else 32
        expression='pa + pb' if name=='add32' else 'pa * pb + pc' if name=='mac8' else 'pa * pb'
        ports=', .c(c)' if name=='mac8' else ''
        tb=f'''module tb;
reg clk=0; always #5 clk=~clk;
reg rstn=0;
reg [{width-1}:0] a=0,b=0; reg [15:0] c=0;
wire [{result-1}:0] y;
reg [63:0] pa=0,pb=0,pc=0;reg [{result-1}:0] expected;
integer i;
Probe dut(.clk(clk),.rstn(rstn),.a(a),.b(b){ports},.y(y));
initial begin
for(i=0;i<256;i=i+1)begin
 @(negedge clk);rstn=(i>1 && i%37!=0);
 a=(i==2)?0:(i==3)?'1:$urandom;
 b=(i==2)?'1:(i==3)?'1:$urandom;c=$urandom;
 expected=rstn?({expression}):0;
 @(posedge clk);#1;
 if(y!==expected) $fatal(1,"mismatch i=%d got=%h expected=%h",i,y,expected);
 pa=rstn?a:0;pb=rstn?b:0;pc=rstn?c:0;
end
$display("PASS 256 vectors including directed overflow and reset");$finish;
end
endmodule
'''
        row=simulate(root/'connection/rtl'/(name+'.sv'),tb,name)
        row.update(integer_vectors=256,reset_checked=True)
        rows.append(row)
    for case,depths in SCOPE.items():
        for depth in depths:
            path=root/'software-check/native'/f'{case}-L{depth}'
            inv=read(path/'inventory.json');view=inv['views'][0]
            spec=read(software_root(case,depth)/case/'source/semantics.json')
            tb,counts=bench(spec,view['artifact'],depth,cycles=192)
            row=simulate(path/view['directory']/'workload.sv',tb,f'{case}-L{depth}')
            row.update(cycles=192,integer_cycle_checks=counts,reset_stall_protocol_checked=True)
            rows.append(row)
    receipt=dict(status='passed',rows=rows,new_synthesis_calls=0,new_physical_calls=0,
        source_sha256=sha(__file__),RTL_only=True)
    write(destination/'receipt.json',receipt)
    return receipt


def run(root):
    root=Path(root).resolve()
    if not (root/'software-check/software-check.json').exists():
        raise ValueError('software platform export checks must complete first')
    folder=root/'functional-accounting';folder.mkdir(exist_ok=False)
    context=dict(target_platform='nangate45',admission_id='matrix-nangate45-n12-validation-v1',
                 task_id='nine-RTL-functional-checks')
    command=[sys.executable,'-B','-m','experiments.arithmetic_dse.nangate45_connection_check',
             '--root',str(root),'--checks']
    write(folder/'admission.json',dict(version='nangate45-N12-support-validation-v1',
        context=context,commands=command,timeout_s=300,threads=2,memory_limit_MiB=2048,
        automatic_retries=0,source_sha256=sha(__file__),global_ledger=str(budget.LEDGER),
        same_nine_slots=True,unit_tests_not_model_samples=True))
    ledger=runtime.NineLedger()
    with ledger.job(context):
        reservation=ledger.reserve(None,300,2,'nangate45_N12_functional_validation',command,folder/'validation',context=context)
        record=run_command(command,folder,'validation',300,dict(os.environ,PYTHONPATH=str(ROOT),OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1'),
            memory_limit_mib=2048,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record)
        write(folder/'settlement.json',dict(reservation_id=reservation['id'],record=record))
        if record['exit_code']:
            raise RuntimeError('functional validation failed; retain attempt, no automatic retry')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,required=True);p.add_argument('--checks',action='store_true')
    a=p.parse_args()
    if a.checks:checks(a.root)
    else:run(a.root)
