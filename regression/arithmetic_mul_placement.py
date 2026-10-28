#!/usr/bin/env python3
"""Same-graph placement acceptance, no PPA and no CIRCT dependency.

Only the frozen production placement is emitted and functionally simulated.
Alternative placements are analyzed as models, not new C/D candidates.
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
from experiments.arithmetic_dse.placement_analysis import analyze


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build'/('step5-placement-'+uuid.uuid4().hex[:12]))
    parser.add_argument('--rtlzz-build',type=Path,default=ROOT/'build/step4-rtlzz')
    parser.add_argument('--skip-build',action='store_true')
    args=parser.parse_args();out=args.output.resolve();build=args.rtlzz_build.resolve()
    if out.exists():parser.error('use a new directory to preserve evidence')
    out.mkdir(parents=True)
    study=ROOT/'experiments/arithmetic_dse/configs/step5_placement_v1.json'
    config=json.loads(study.read_text())
    parent=config['parent_freeze']
    if sha256(ROOT/parent['path'])!=parent['sha256']:raise ValueError('parent freeze changed')
    ledger=Ledger();before=ledger.summary();commands=[]
    def run(command,stem):
        reservation=ledger.reserve(None,300,2,'step5_placement_acceptance',command,out/stem)
        record=run_command(command,out,stem,300,os.environ.copy(),cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record);record['budget_reservation_id']=reservation['id'];commands.append(record)
        write_json(out/'commands.json',commands)
        if record['exit_code']:raise RuntimeError(f'{stem}: see {record["log"]}')
        return Path(record['log']).read_text()
    if not args.skip_build:
        run(['cmake','-S',ROOT/'rtlzz','-B',build],'configure')
        run(['cmake','--build',build,'--target','mul-placement-test','-j2'],'build')
    (out/config['source_name']).write_text(config['source'])
    run([build/'testv2/mul-placement-test',ROOT/'vullib',out/config['source_name'],out],'generation')
    graph=json.loads((out/'graph.json').read_text())
    analysis=analyze(graph,config)
    # This comparison preserves the connection to the earlier function/PPA run.
    historical=ROOT/'experiments/arithmetic/evidence/step5/mul32_split16.sv'
    if (out/'mul32_split16.sv').read_bytes()!=historical.read_bytes():raise ValueError('production RTL changed')
    write_json(out/'analysis.json',analysis)
    # Meaningful negative checks: changed costs, reported paths and register chains.
    import copy
    rejected=[]
    for name,mutate in [('materialized_width',lambda g:g['registers'][0].update(width=1)),
                        ('cost',lambda g:g['nodes'][14].update(cpp_delay=0)),
                        ('reported_stage_delay',lambda g:g['report'].update(stage_delays=[0,0]))]:
        tampered=copy.deepcopy(graph);mutate(tampered)
        try:analyze(tampered,config)
        except ValueError:rejected.append(name)
        else:raise ValueError(f'negative check accepted {name}')
    run(['verilator','--cc','--exe','--build','-j','2','--top-module','mul32_split16','--Mdir',out/'obj',
         out/'mul32_split16.sv',ROOT/'regression/arithmetic_mul_placement/rtl_driver.cpp'],'verilator')
    rng=random.Random(config['functional']['seed'])
    edges=[0,1,2,3,0x7fff,0x8000,0xffff,0x10000,0x10001,0x7fffffff,0x80000000,0xfffffffe,0xffffffff]
    pairs=[(a,b) for a in edges for b in edges]+[(1<<a,1<<b) for a in range(32) for b in range(32)]
    pairs += [(rng.getrandbits(32),rng.getrandbits(32)) for _ in range(config['functional']['random_vectors'])]
    rows=[(a,b,int(i<1193 or i%7 not in (1,2)),int(i not in config['functional']['reset_indices'])) for i,(a,b) in enumerate(pairs)]
    rows += [(0,0,0,1)]*4
    (out/'vectors.txt').write_text(''.join(f'{a:x} {b:x} {iv:x} {rst:x}\n' for a,b,iv,rst in rows))
    observed=run([out/'obj/Vmul32_split16',out/'vectors.txt'],'rtl').splitlines()
    if len(observed)!=len(rows):raise ValueError('incomplete RTL output')
    history=[];last=0;products=bubbles=resets=0
    for cycle,((a,b,iv,rst),line) in enumerate(zip(rows,observed)):
        if not rst:
            history=[];valid=0;last=0;resets+=1
        else:
            history.append((iv,a*b));valid=int(len(history)>=3 and history[-3][0])
            if valid:last=history[-3][1];products+=1
            else:bubbles+=1
        if [int(v,16) for v in line.split()]!=[last,valid]:raise ValueError(f'RTL mismatch at cycle {cycle}')
    files=['graph.json','analysis.json','schedule.txt','mul32_split16.sv',config['source_name'],'vectors.txt']
    report={'version':'step5-placement-regression-v1','status':'passed','study_sha256':sha256(study),
            'cycles':len(rows),'valid_checks':len(rows),'valid_product_checks':products,
            'bubble_hold_checks':bubbles,'reset_checks':resets,'negative_checks_rejected':rejected,
            'evidence_type':analysis['evidence_type'],'preference_selection_demonstrated':False,
            'production_RTL_equals_frozen_step5':True,'new_PPA_calls':{'synth':0,'grt':0,'final':0},
            'CIRCT':'outside native acceptance; no tool check or invocation',
            'commands':commands,'usage_before':before,'usage_after':ledger.summary(),
            'artifacts_sha256':{name:sha256(out/name) for name in files}}
    write_json(out/'regression.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ['commands','artifacts_sha256']},ensure_ascii=False,indent=2))

if __name__=='__main__':main()
