"""Bounded steps 1--3 software work, through existing shared leaf accounting."""
import argparse
from copy import deepcopy
import gzip
import json
import os
from pathlib import Path
import random
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import model_sampling_v2 as samples
from experiments.arithmetic_dse.model_context_samples import layout,evaluate


def prepare(out,cohort_manifest=None):
    from regression.arithmetic_target_round1 import cohort,capacity_sources
    out.mkdir(parents=True,exist_ok=False);inventory=read(ROOT/'experiments/arithmetic/evidence/step7_fast_loads_v1/loads.json')
    rows=read(cohort_manifest)['sources'] if cohort_manifest else cohort(inventory)+capacity_sources();modules=[];declarations=[];assigns=[];checks=[];initial=[];cycles=128
    for i,row in enumerate(rows):
        f=row['features'];g=layout(f);n,r=g['input_bits'],g['output_bits'];banks=len(g['captures']);name='Observe'+str(i);w=n+r+3
        modules.append(samples.source(f,name));rng=random.Random(int(row['source_group'][:16],16));old=0;valid=0;vectors=[]
        for cycle in range(cycles):
            value=rng.getrandbits(n);rstn=int(cycle not in (0,1,57,58));iv=int(cycle%5 not in (1,3));word=value
            for v,bits in ((rstn,1),(iv,1),(evaluate(f,old),r),(0 if not rstn else valid,1)):word=(word<<bits)|v
            vectors.append(format(word,'x'))
            if not rstn:old=0;valid=0
            else:
                valid=iv
                if iv:old=value
        path=out/(row['id']+'.hex');path.write_text('\n'.join(vectors)+'\n')
        declarations.append(f'reg [{w-1}:0] v{i}[0:127];reg [{n-1}:0] data{i};reg rst{i},iv{i};wire [{banks-1}:0] y{i};wire ov{i};{name} dut{i}(.clk(clk),.rstn(rst{i}),.iv(iv{i}),.data(data{i}),.y(y{i}),.ov(ov{i}));')
        assigns.append(f'{{data{i},rst{i},iv{i}}}=v{i}[j][{w-1}:{r+1}];');checks.append(f'if(ov{i}!==v{i}[j][0])$fatal(1,"valid source{i} row%0d",j);if(j>0&&dut{i}.observed!==v{i}[j][{r}:1])$fatal(1,"capture source{i} row%0d",j);')
        offset=0
        for b,bank in enumerate(g['captures']):
            width=len(bank['tokens']);checks.append(f'if(j>0&&y{i}[{b}]!==( ^v{i}[j][{offset+width}: {offset+1}]))$fatal(1,"observer source{i} bank{b} row%0d",j);');offset+=width
        initial.append(f'$readmemh("{path}",v{i});')
    (out/'kernels.sv').write_text('\n'.join(modules));(out/'tb.sv').write_text('module ObserveTb;reg clk=0;integer j;\n'+'\n'.join(declarations)+'\ninitial begin\n'+'\n'.join(initial)+'\nfor(j=0;j<128;j=j+1)begin clk=0;\n'+'\n'.join(assigns)+'\n#5;clk=1;#1;\n'+'\n'.join(checks)+f'\n#4;end $display("INDEPENDENT_OBSERVERS_PASS sources={len(rows)} cycles=128");$finish;end endmodule\n')
    for row in rows:
        d=out/'sources'/row['id'];d.mkdir(parents=True);(d/'input.sv').write_text(samples.source(row['features']));write(d/'contract.json',samples.geometry_contract(row['features']))
    write(out/'sources.json',dict(rows=rows,source_role='software_only_no_physical_test_labels',schema=samples.VERSION,source_sha256=sha(Path(samples.__file__))))
    print('prepared '+str(len(rows))+' successor shells, each bank independently observable',flush=True)


def execute(out,name,command,timeout=180,cwd=None):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);ctx=dict(target_platform='asap7',admission_id='steps123-20261110-'+out.name,task_id=name)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',VUL_REGRESSION_CIRCT='0')
    # Preserve every changed producer used by this concrete attempt.
    paths=[p for folder in ('experiments/arithmetic_dse','regression') for p in (ROOT/folder).glob('*.py') if p.name in ('model_sampling_v2.py','arithmetic_steps123.py')]
    for p in paths:
        dest=out/'source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    try:
        with ledger.job(ctx):
            r=ledger.reserve(None,timeout,4,'steps123_software_preparation',command,out/name,context=ctx)
            if cwd:os.chdir(cwd)
            record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record);write(out/'commands.json',[dict(**record,budget_reservation_id=r['id'])])
    finally:
        after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries'])))
    print(Path(record['log']).read_text()[-2200:],flush=True)
    if record['exit_code']:raise RuntimeError('paid leaf failed; preserved '+str(out))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','leaf'));p.add_argument('--out',type=Path,required=True);p.add_argument('--name',default='support');p.add_argument('--timeout',type=int,default=180);p.add_argument('--cwd',type=Path);p.add_argument('--cohort',type=Path);a,cmd=p.parse_known_args()
    if a.action=='prepare':prepare(a.out.resolve(),a.cohort.resolve() if a.cohort else None)
    else:execute(a.out.resolve(),a.name,cmd[1:] if cmd[:1]==['--'] else cmd,a.timeout,a.cwd)
