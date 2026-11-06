"""Actual RTL preflight for native state lifetime/enable/mask protocol."""
import argparse
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.model_m2_cec import leaf
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.model_native_state_collection import CONFIG
from experiments.arithmetic_dse.model_native_state_samples import specifications,source,step,features
from experiments.arithmetic_dse.model_native_state_labels import labels,REQUESTS


def worker(out,native_audit):
    out.mkdir(parents=True,exist_ok=False);cfg=json.loads(CONFIG.read_text());specs=specifications(cfg)
    audit=json.loads(native_audit.read_text())
    if audit['status']!='passed' or len(audit['cases'])!=12 or audit['PPA_calls']:
        raise ValueError('real native projection/materialization/RTL audit required')
    text_seen=set()
    for s in specs:
        text=source(s)
        if text in text_seen or s['features']!=features(s,1500):raise ValueError('duplicate native bank or inconsistent features')
        text_seen.add(text)
    selected=('native-state-train-small-w1','native-state-train-small-w5','native-state-train-large-w37',
              'native-state-train-large-w65','native-state-validation-w32','native-state-test-w5')
    checks=0;primary_old_disagreements=0
    for name in selected:
        spec=next(s for s in specs if s['id']==name);d=out/name;d.mkdir()
        (d/'bank.sv').write_text(source(spec));rng=random.Random(20261105+sum(map(ord,name)))
        declarations=['reg clk=0,rstn=0,iv=0;wire y,ov;']
        declarations += [f'reg [{w["variable_mask"].bit_count()-1}:0] in{j}=0;' for j,w in enumerate(spec['words'])]
        conns=['.clk(clk)','.rstn(rstn)','.iv(iv)','.y(y)','.ov(ov)']+[f'.in{j}(in{j})' for j in range(len(spec['words']))]
        bench=['module tb;',*declarations,'ModelBundle dut('+','.join(conns)+');','initial begin']
        state={s['name']:0 for s in spec['slots']};state.update({f'valid_q{i}':0 for i in range(1,spec['stages']+1)})
        widths={s['name']:s['variable_bits'] for s in spec['slots']}
        for cycle in range(80):
            inputs={f'in{j}':rng.getrandbits(w['variable_mask'].bit_count()) for j,w in enumerate(spec['words'])}
            inputs['iv']=int(cycle%7 not in (1,2,5));reset=cycle in (0,1,27,54)
            primary_old_disagreements+=int(not reset and inputs['iv']!=state['valid_q1'])
            state=step(spec,state,inputs,reset)
            bench.append('clk=0;rstn='+str(int(not reset))+';'+''.join(f'{k}=65\'h{v:x};' for k,v in inputs.items())+'#4;clk=1;#1;')
            for key,value in state.items():
                bench.append(f'if(dut.bank.{key} !== {widths.get(key,1)}\'h{value:x})$fatal(1,"{name} cycle{cycle} {key}");');checks+=1
            parity=0
            for j,w in enumerate(spec['words']):parity^=state[f'dst{w["end"]}_{j}'].bit_count()%2
            bench.append(f'if(y !== 1\'b{parity} || ov !== 1\'b{state["valid_q"+str(spec["stages"])]})$fatal(1,"terminal observation cycle{cycle}");#1;clk=0;#4;')
        bench += ['$display("NATIVE_STATE_BANK_PASS");$finish;end','endmodule'];(d/'tb.sv').write_text('\n'.join(bench)+'\n')
        for cmd,name in [(['iverilog','-g2012','-s','tb','-o',str(d/'sim.out'),str(d/'bank.sv'),str(d/'tb.sv')],'compile'),(['vvp',str(d/'sim.out')],'simulate')]:
            p=subprocess.run(cmd,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=60);(d/(name+'.log')).write_text(p.stdout)
            if p.returncode:raise ValueError('native bank RTL failed: '+p.stdout[-2000:])
    if primary_old_disagreements==0:raise ValueError('primary versus old-valid semantics not tested')
    fixture=out/'label-reader';fixture.mkdir();prefix=fixture/'vulsim_synth'
    rows=['id\tkind\tstart\tend\tstart_arrival\tend_arrival\tdelay\tpoints\tslack']
    for name,kind,src,dst in REQUESTS:
        start='iv' if kind=='port' else 'bank/valid_q1/Q' if name!='state_data' else 'bank/dst1_0/Q'
        end='bank/valid_q2/D' if name=='state_valid' else 'bank/dst1_0/D'
        a,b,slack=(300,345,1150) if kind=='port' else (20,60,1370)
        rows.append(f'{name}\t{kind}\t{start}\t{end}\t{a}\t{b}\t{b-a}\t2\t{slack}')
        Path(str(prefix)+'_native_'+name+'_points.tsv').write_text(f'{start}\t{a}\n{end}\t{b}\n')
        Path(str(prefix)+'_native_'+name+'.rpt').write_text('static reader fixture, no measured timing label\n')
    table=Path(str(prefix)+'_native_state_paths.tsv');table.write_text('\n'.join(rows)+'\n')
    result=labels(prefix,1500,1)
    if next(r for r in result if r['kind']=='port')['H_ps']!=5:raise ValueError('native input delay charged more than once')
    table.write_text(('\n'.join(rows)+'\n').replace('300\t345\t45','300\t345\t46'))
    try:labels(prefix,1500,1)
    except ValueError:pass
    else:raise ValueError('wrong native input arrival difference accepted')
    proof={'status':'passed','protocol_sha256':sha(CONFIG),
        'generator_sha256':sha(ROOT/'experiments/arithmetic_dse/model_native_state_samples.py'),
        'native_audit_path':str(native_audit),'native_audit_sha256':sha(native_audit),'source_groups':48,
        'RTL_banks':6,'cycles_per_bank':80,'full_state_checks':checks,
        'primary_and_old_valid_differing_cycles':primary_old_disagreements,
        'native_primary_and_previous_valid_enables':True,'mixed_lifetimes_and_known_zero_masks':True,
        'port_vs_register_label_reader_and_negative':True,'PPA_calls':0}
    proof['native_binding_sources']={name:sha(ROOT/name) for name in (
        'rtlzz/src/backend/arithmetic_state.hpp','rtlzz/src/backend/arithmetic_state.cpp',
        'rtlzz/testv2/arithmetic_native_state_test.cpp','regression/arithmetic_native_state.py')}
    proof['native_queries_sha256']=sha(native_audit.parent/'native/queries.json')
    write(out/'result.json',proof);print(json.dumps(proof),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','worker'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--native-audit',type=Path,required=True);a=p.parse_args();out=a.out.resolve()
    if a.action=='worker':worker(out,a.native_audit.resolve());return
    out.mkdir(parents=True,exist_ok=False);l=Ledger();ctx={'target_platform':'asap7','admission_id':out.name,'task_id':'native-bank-RTL-and-label-preflight'}
    with l.job(ctx):leaf([sys.executable,'-B',str(Path(__file__).resolve()),'worker','--out',str(out/'RTL'),'--native-audit',str(a.native_audit.resolve())],out,'software',600,l,ctx)
    print((out/'software.log').read_text(),flush=True)


if __name__=='__main__':main()
