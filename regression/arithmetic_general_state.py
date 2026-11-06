"""Full-state RTL and unmapped geometry preflight for prospective S banks."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.model_general_state_samples import specifications,source,step,features
from experiments.arithmetic_dse.model_general_state_labels import labels,REQUESTS

CONFIG=ROOT/'experiments/arithmetic_dse/configs/model_asap7_general_state_v1.json'
ENVIRONMENT=ROOT/'build/step7-reference-20261106/collection-v3/runs/add_u64'


def execute(command,log):
    with log.open('x') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=120)
    if p.returncode:raise ValueError('general-state preflight command failed: '+str(log))


def worker(out):
    out.mkdir(parents=True,exist_ok=False);cfg=json.loads(CONFIG.read_text())
    for name in ('requirements','targets','parent_model'):
        if sha(ROOT/cfg[name])!=cfg[name+'_sha256']:raise ValueError('general-state predecessor changed: '+name)
    targets=json.loads((ROOT/cfg['targets']).read_text())
    if cfg['SDC_ps']!=targets['exact_SDC_ps']:raise ValueError('general-state target grid differs from frozen numerical targets')
    specs=specifications(cfg);manifest=json.loads((ENVIRONMENT/'manifest.json').read_text());rtl_hashes={}
    checks=held_valid=unconditional=general_resets=0;coverage={}
    for split in ('train','validation','test'):
        selected=[s for s in specs if s['split']==split]
        observed={w['declared_width'] for s in selected for w in s['words']}
        if observed!=set(cfg['word_widths']):raise ValueError('general-state required widths missing in '+split+': '+str(set(cfg['word_widths'])-observed))
        coverage[split]={'sources':len(selected),'widths':sorted(observed),
            'no_full_chain_sources':sum(not s['features']['has_full_native_chain'] for s in selected),
            'eighteen_channel_sources':sum(len(s['words'])==18 for s in selected)}
    for s in specs:
        d=out/s['id'];d.mkdir();rtl=d/'input.sv';rtl.write_text(source(s));rtl_hashes[s['id']]=sha(rtl)
        if s['features']!=features(s,1500):raise ValueError('general-state features inconsistent')
        declarations=['reg clk=0,rstn=0,iv=0,we_iv=0;wire y,ov;']
        declarations += [f'reg [{r["width"]-1}:0] in{j}=0;reg we{j}=0;' for j,r in enumerate(s['roots'])]
        conns=['.clk(clk)','.rstn(rstn)','.iv(iv)','.we_iv(we_iv)','.y(y)','.ov(ov)']
        conns += [f'.in{j}(in{j}),.we{j}(we{j})' for j in range(len(s['roots']))]
        declarations += ['wire probe_ov;']
        for j in s['external_words']:
            w=s['words'][j]['variable_bits'];declarations.append(f'reg [{w-1}:0] probe_in{j}=0;wire [{w-1}:0] probe_out{j};')
        probe=['.clk(clk)','.rstn(rstn)',".iv(1'b0)",'.valid(probe_ov)']
        probe += [f'.word{j}(probe_in{j}),.data_{j}(probe_out{j})' for j in s['external_words']]
        bench=['module tb;',*declarations,'ModelBundle dut('+','.join(conns)+');',
            'GeneralExternal invalid_data_probe('+','.join(probe)+');','initial begin']
        widths={f'launch.data_{j}':r['width'] for j,r in enumerate(s['roots'])}
        widths.update({'launch.valid':1,'external.valid':1})
        widths.update({f'native.valid_{k}':1 for k in range(1,s['depth']+1)})
        widths.update({'native.'+x['name']:x['variable_bits'] for x in s['slots']})
        widths.update({f'external.data_{j}':s['words'][j]['variable_bits'] for j in s['external_words']})
        state={k:0 for k in widths};rng=random.Random(20261106+sum(map(ord,s['id'])))
        for w in s['words']:
            v=w['variable_bits'];patterns={0,(1<<v)-1,sum(1<<k for k in range(v) if k%2==0),sum(1<<k for k in range(v) if k%3==0)}
            general_resets+=int(w['reset'] not in patterns)
        for cycle in range(128):
            reset=cycle in (0,1,31,68,97);inputs={'iv':int(cycle%7 not in (1,2,5)),'we_iv':int(cycle%5 not in (1,2))}
            inputs.update({f'in{j}':rng.getrandbits(r['width']) for j,r in enumerate(s['roots'])})
            inputs.update({f'we{j}':int((cycle+j)%4!=1) for j in range(len(s['roots']))})
            new=step(s,state,inputs,reset)
            held_valid+=int(not reset and s['service_mode']!=2 and not inputs['we_iv'] and state['launch.valid']!=inputs['iv'])
            probe_values={j:rng.getrandbits(s['words'][j]['variable_bits']) for j in s['external_words']}
            unconditional+=int(not reset)*len(probe_values)
            bench.append('clk=0;rstn='+str(int(not reset))+';'+''.join(f'{key}=130\'h{value:x};' for key,value in inputs.items())+
                ''.join(f'probe_in{j}=64\'h{value:x};' for j,value in probe_values.items())+'#4;clk=1;#1;')
            for name,value in new.items():
                bench.append(f'if(dut.{name} !== {widths[name]}\'h{value:x})$fatal(1,"{s["id"]} cycle{cycle} {name}");');checks+=1
            # A separate real instance receives changing data with valid held
            # low; aligned native words alone can hide an accidental output
            # enable because their data also holds during a bubble.
            for j,value in probe_values.items():
                w=s['words'][j];expected=w['reset'] if reset else value
                bench.append(f'if(probe_out{j} !== {w["variable_bits"]}\'h{expected:x})$fatal(1,"unconditional external capture cycle{cycle}");');checks+=1
            parity=0
            for j,w in enumerate(s['words']):
                value=new[f'external.data_{j}'] if j in s['external_words'] else new[f'native.data_{j}_s{w["end"]}']
                parity^=value.bit_count()%2
            bench.append(f'if(y !== 1\'b{parity} || ov !== 1\'b{new["external.valid"]})$fatal(1,"terminal observation cycle{cycle}");#1;clk=0;#4;')
            state=new
        bench += ['$display("GENERAL_STATE_RTL_PASS");$finish;end','endmodule'];(d/'tb.sv').write_text('\n'.join(bench)+'\n')
        execute(['iverilog','-g2012','-s','tb','-o',str(d/'sim.out'),str(rtl),str(d/'tb.sv')],d/'compile.log')
        execute(['vvp',str(d/'sim.out')],d/'simulate.log')
        if s is specs[0]:
            text=rtl.read_text()
            if text.count('else data_')!=len(s['external_words']):raise ValueError('external negative mutation point changed')
            mutated=d/'incorrect-gated-external.sv';mutated.write_text(text.replace('else data_','else if(iv)data_'))
            execute(['iverilog','-g2012','-s','tb','-o',str(d/'negative.out'),str(mutated),str(d/'tb.sv')],d/'negative-compile.log')
            negative=subprocess.run(['vvp',str(d/'negative.out')],capture_output=True,text=True,timeout=120)
            (d/'negative-simulate.log').write_text(negative.stdout+negative.stderr)
            if negative.returncode==0 or 'unconditional external capture' not in negative.stdout:
                raise ValueError('accidental valid-gated external capture not detected')
        script=d/'generic.ys';script.write_text('read_verilog -sv "'+str(rtl)+'"\nhierarchy -check -top ModelBundle\nproc\nopt\ncheck -assert\nwrite_json "'+str(d/'generic.json')+'"\n')
        execute([manifest['tools']['yosys']['path'],'-T','-s',str(script)],d/'generic.log')
        modules=json.loads((d/'generic.json').read_text())['modules'];actual={}
        for name,owner in [('GeneralLaunch','input_service'),('GeneralNative','native_state'),('GeneralExternal','external_state')]:
            actual[owner]=sum(len(c['connections']['Q']) for c in modules[name]['cells'].values() if 'dff' in c['type'].lower())
        if actual!=s['expected_FF_bits']:raise ValueError('general-state unmapped FF geometry differs: '+s['id']+' '+str((actual,s['expected_FF_bits'])))
        write(d/'generic-proof.json',{'status':'passed','actual':actual,'expected':s['expected_FF_bits'],'technology_mapping_used':False})
    if not all((held_valid,unconditional,general_resets)):raise ValueError('general-state protocol/reset discrimination missing')
    public={}
    for name in targets['policy']['cases']:
        candidates=[ROOT/'build/step6-integration-20261031'/part/name/'sim/top.sv' for part in ('public-final','public-remaining')]
        present=[p for p in candidates if p.exists()]
        if len(present)!=1:raise ValueError('one exact public protocol witness required: '+name)
        p=present[0];text=p.read_text()
        for token in ('assign wen_iv = push__vld;','if (wen_iv__)','__vul_pipeline_q_iv <= wdata_iv__;','__vul_pipeline_q_ov <= __vul_pipeline_d_ov;'):
            if token not in text:raise ValueError('public service protocol witness changed: '+name+'/'+token)
        public[str(p)]=sha(p)
    # Synthetic path fixtures exercise the new reader, not measured labels.
    fixture=out/'reader-fixture';fixture.mkdir();prefix=fixture/'raw'
    ff={'sequential':True,'data_pins':['D'],'pins':{'D':{'direction':'input'},'Q':{'direction':'output'}}}
    cells={'FF':ff};instances={};rows=['id\tkind\tstart\tend\tstart_arrival\tend_arrival\tdelay\tpoints\tslack\tsetup_margin_s\tclk_skew_s']
    for name,kind,src,dst in REQUESTS:
        start=src[0].replace('*','0')+('/Q' if kind=='register' else '')
        end=dst[0].replace('*','0')+'/D';instances[end.rsplit('/',1)[0]]='FF'
        if kind=='register':instances[start.rsplit('/',1)[0]]='FF'
        a,b,slack=(300,345,1150) if kind=='port' else (20,60,1370)
        rows.append(f'{name}\t{kind}\t{start}\t{end}\t{a}\t{b}\t{b-a}\t2\t{slack}\t1e-11\t2e-11')
        Path(str(prefix)+'_reference_'+name+'_points.tsv').write_text(f'{start}\t{a}\n{end}\t{b}\n')
        Path(str(prefix)+'_reference_'+name+'.rpt').write_text('synthetic reader fixture; not measured\n')
    table=Path(str(prefix)+'_reference_paths.tsv');table.write_text('\n'.join(rows)+'\n')
    parsed=labels(prefix,1500,1,cells,instances)
    if any(r['H_ps']!=5 for r in parsed if r['kind']=='port'):raise ValueError('input IO subtracted incorrectly')
    table.write_text(('\n'.join(rows)+'\n').replace('300\t345\t45','300\t345\t46'))
    try:labels(prefix,1500,1,cells,instances)
    except ValueError:pass
    else:raise ValueError('general-state wrong port delta accepted')
    proof={'version':'general-state-software-preflight-v1','status':'passed','protocol_sha256':sha(CONFIG),
        'source_groups':len(specs),'RTL_sources':rtl_hashes,'cycles_per_source':128,'full_state_checks':checks,
        'service_valid_hold_distinguishing_cycles':held_valid,'external_unconditional_distinguishing_words':unconditional,
        'incorrect_valid_gated_external_RTL_rejected':True,
        'general_reset_words':general_resets,'split_coverage':coverage,'generic_state_geometry_checked':True,
        'input_IO_once_and_wrong_delta_refused':True,'public_service_protocol_witnesses':public,
        'producer_sha256':{str(p.relative_to(ROOT)):sha(p) for p in [CONFIG,Path(__file__).resolve(),
            ROOT/'experiments/arithmetic_dse/model_general_state_samples.py',ROOT/'experiments/arithmetic_dse/model_general_state_labels.py']},
        'environment_manifest':str(ENVIRONMENT/'manifest.json'),'environment_manifest_sha256':sha(ENVIRONMENT/'manifest.json'),
        'independent_physical_labels_read':False,'PPA_calls':0}
    write(out/'proof.json',proof);print(json.dumps(proof),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();worker(a.out.resolve())
