"""Actual reference RTL, generic state proof, raw ownership and STA API preflight."""
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_collection import sha,write
from experiments.arithmetic_dse.model_reference_samples import spec,source,evaluate,render_requests
from experiments.arithmetic_dse.model_reference_labels import liberty,partition,labels

CONFIG=ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_reference_v1.json'
ENVIRONMENT=ROOT/'build/step7-native-state-20261105/collection-v1/runs/native-state-train-small-w5-t0'
ATOM=ROOT/'build/step7-m2-models-20261104/atomic-fp/AtomicFp.sv'


def read(path):return json.loads(Path(path).read_text())
def execute(command,log,timeout=120):
    with log.open('x') as f:p=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
    if p.returncode:raise ValueError('reference preflight command failed: '+str(log))


def worker(out):
    out.mkdir(parents=True,exist_ok=False);cfg=read(CONFIG);requirements=ROOT/'experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json'
    if sha(requirements)!=cfg['requirements_sha256'] or cfg['labels']!=read(requirements)['target_reference']['required_labels']:
        raise ValueError('reference key list changed')
    atom=ATOM.read_text();(out/'AtomicFp.sv').write_text(atom)
    m=read(ENVIRONMENT/'manifest.json');base=read(ENVIRONMENT/'liberty_cells.json')['cells']
    cells=liberty(m['libraries'],base);write(out/'liberty-pin-classes.json',cells)
    checks=0;rtl_hashes={};even_divisors=0;protocol_differences=0
    for key in cfg['labels']:
        s=spec(key);d=out/'sources'/key;d.mkdir(parents=True);rtl=d/'input.sv';rtl.write_text(source(s,atom));rtl_hashes[key]=sha(rtl)
        write(d/'contract.json',{'version':'reference-shell-contract-v1','spec':s,'protocol_sha256':sha(CONFIG),
            'source_role':'microbenchmark_reference_only','model_fit_allowed':False,
            'native_capture_mode':'previous_launch_valid','external_capture_mode':'unconditional'})
        (d/'requests.tcl').write_text(render_requests(s))
        conns=['.clk(clk)','.rstn(rstn)','.iv(iv)','.y(y)','.ov(ov)']+['.'+n+'('+n+')' for n in s['inputs']]+['.we_'+n+'(we_'+n+')' for n in s['inputs']]
        bench=['module tb;reg clk=0,rstn=0,iv=0;wire y,ov;']
        for n,w in s['inputs'].items():bench.append(f'reg [{w-1}:0] {n}=0;reg we_{n}=0;')
        bench += ['ModelBundle dut('+','.join(conns)+');','initial begin']
        rng=random.Random(20261106+sum(map(ord,key)));launch=dict(s['reset']);cap=external=evaluate(s,launch);lv=cv=ev=0
        for cycle in range(144):
            reset=cycle in (0,1,39,77,111);iv=int(cycle%7 not in (1,2,5));values={n:rng.getrandbits(w) for n,w in s['inputs'].items()}
            if cycle%11==0:values['a']=0
            elif cycle%11==1:values['a']=(1<<s['width'])-1
            if s['operation'] in ('div','mod'):values['b']=(0,1,2,4,(1<<s['width'])-1)[cycle%5]
            if s['operation']=='fp32':
                edge=[0,0x80000000,0x7f800000,0xff800000,0x7fc00001,0x7f812345,1,0x7f7fffff,0x3f800000]
                if cycle<len(edge)**2:values['a']=edge[cycle%len(edge)];values['b']=edge[cycle//len(edge)]
            enable={n:int((cycle+i)%5 not in (1,3)) for i,n in enumerate(s['inputs'])}
            protocol_differences+=int(not reset and (iv!=lv or cv==0 and cap!=external))
            new_launch=dict(s['reset']) if reset else {n:(max(values[n],1) if s['operation'] in ('div','mod') and n=='b' else values[n]) if enable[n] else launch[n] for n in launch}
            new_cap=evaluate(s,s['reset']) if reset else evaluate(s,launch) if lv else cap
            new_external=evaluate(s,s['reset']) if reset else cap
            new_lv,new_cv,new_ev=(0,0,0) if reset else (iv,lv,cv)
            if s['operation'] in ('div','mod') and new_launch['b'] and new_launch['b']%2==0:even_divisors+=1
            bench.append('clk=0;rstn='+str(int(not reset))+';iv='+str(iv)+';'+''.join(f'{n}={s["inputs"][n]}\'h{v:x};we_{n}={enable[n]};' for n,v in values.items())+'#4;clk=1;#1;')
            for n,value in new_launch.items():bench.append(f'if(dut.launch.data_{n} !== {s["inputs"][n]}\'h{value:x})$fatal(1,"{key} launch {cycle} {n}");');checks+=1
            for signal,width,value in [('launch_valid',1,new_lv),('capture_valid',1,new_cv),('ov',1,new_ev),('captured',s['result_width'],new_cap),('external_value',s['result_width'],new_external),('y',1,new_external.bit_count()%2)]:
                bench.append(f'if(dut.{signal} !== {width}\'h{value:x})$fatal(1,"{key} {signal} cycle{cycle}");');checks+=1
            bench.append('#1;clk=0;#4;');launch,cap,external,lv,cv,ev=new_launch,new_cap,new_external,new_lv,new_cv,new_ev
        bench += ['$display("REFERENCE_RTL_PASS");$finish;end','endmodule'];(d/'tb.sv').write_text('\n'.join(bench)+'\n')
        execute(['iverilog','-g2012','-s','tb','-o',str(d/'sim.out'),str(rtl),str(d/'tb.sv')],d/'compile.log')
        execute(['vvp',str(d/'sim.out')],d/'simulate.log')
        ys=d/'generic.ys';ys.write_text('read_verilog -sv "'+str(rtl)+'"\nhierarchy -check -top ModelBundle\nproc\nopt\ncheck -assert\nwrite_json "'+str(d/'generic.json')+'"\n')
        execute([m['tools']['yosys']['path'],'-T','-s',str(ys)],d/'generic.log')
        design=read(d/'generic.json')['modules'];actual={}
        for module,owner in [('RefLaunch','input_service'),('RefCapture','native_state'),('RefExternal','external_state')]:
            actual[owner]=sum(len(c['connections']['Q']) for c in design[module]['cells'].values() if 'dff' in c['type'].lower())
        expected={name:s[name+'_bits'] for name in ('input_service','native_state','external_state')}
        if actual!=expected:raise ValueError('reference unmapped state differs: '+key+' '+str((actual,expected)))
        write(d/'generic-state-proof.json',{'status':'passed','actual_bits':actual,'expected_static_bits':expected,
            'mapped_technology_or_PPA_used':False,'generic_netlist_sha256':sha(d/'generic.json')})
    if not even_divisors or not protocol_differences or len(set(rtl_hashes.values()))!=17:raise ValueError('reference RTL contexts not exercised')
    from experiments.arithmetic_dse.platforms import profile
    p=profile('asap7');probe=out/'STA-api';probe.mkdir();prefix=probe/'raw'
    request=probe/'requests.tcl';request.write_text('set vulsim_reference_requests {{api_data register {bank/dst*} {bank/dst*}}}\n')
    script=probe/'probe.tcl';text=[]
    for lib in m['libraries']:text.append('read_liberty {'+lib['path']+'}')
    text += ['read_db {'+str(ENVIRONMENT/'results/asap7/arithmetic_probe/base/1_synth.odb')+'}',
        'read_sdc {'+str(ENVIRONMENT/'results/asap7/arithmetic_probe/base/1_synth.sdc')+'}',
        'set prefix {'+str(prefix)+'}', 'set ::env(VULSIM_REFERENCE_REQUESTS) {'+str(request)+'}',
        'source {'+str(ROOT/'experiments/arithmetic_dse/reference_assets/snapshot.tcl')+'}']
    script.write_text('\n'.join(text)+'\n');execute([m['tools']['openroad']['path'],'-no_init','-threads','4','-exit',str(script)],probe/'probe.log')
    # Raw cell/instance reports and the read-only connection export describe
    # the same old TRAIN database. This is API/ownership preflight only.
    for suffix in ('_instances.tsv','_cells.tsv'):
        (Path(str(prefix)+suffix)).write_bytes((ENVIRONMENT/'reports/asap7/arithmetic_probe/base'/('vulsim_synth'+suffix)).read_bytes())
    ownership,instances,connections=partition(prefix,cells,p,scopes={'bank/':'native_state'})
    if not ownership['all_cells_accounted_once']:raise ValueError('real database ownership incomplete')
    write(probe/'ownership-api-proof.json',{'status':'passed','scope':'old TRAIN database API/partition preflight, not a new reference or model label',
        'parent_manifest_sha256':sha(ENVIRONMENT/'manifest.json'),'partition':ownership})
    table=list(csv.DictReader(Path(str(prefix)+'_reference_paths.tsv').read_text().splitlines(),delimiter='\t'))
    if len(table)!=1 or table[0]['id']!='api_data':raise ValueError('actual OpenSTA API probe missing')
    proof={'version':'reference-software-preflight-v1','status':'passed','protocol_sha256':sha(CONFIG),'requirements_sha256':sha(requirements),
        'reference_keys':cfg['labels'],'RTL_sources':rtl_hashes,'cycles_per_source':144,'full_state_checks':checks,
        'even_divisor_cycles':even_divisors,'different_enable_protocol_cycles':protocol_differences,
        'native_and_unconditional_external_captures_separate':True,'unmapped_state_geometry_checked':True,
        'read_only_STA_API_and_raw_ownership_checked':True,'reference_numeric_labels_collected':False,
        'joint_boundary_model_qualified':False,'atom_path':str(ATOM),'atom_sha256':sha(ATOM),
        'environment_manifest':str(ENVIRONMENT/'manifest.json'),'environment_manifest_sha256':sha(ENVIRONMENT/'manifest.json'),
        'producer_sha256':{str(path.relative_to(ROOT)):sha(path) for path in [CONFIG,ROOT/'experiments/arithmetic_dse/model_reference_samples.py',
            ROOT/'experiments/arithmetic_dse/model_reference_labels.py',ROOT/'experiments/arithmetic_dse/reference_assets/snapshot.tcl',Path(__file__).resolve()]},
        'PPA_calls':0,'read_only_support_OpenSTA_calls':1}
    write(out/'proof.json',proof);print(json.dumps(proof),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','worker'));p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.action=='worker':worker(a.out.resolve())
    else:
        from experiments.arithmetic_dse.budget import Ledger
        from experiments.arithmetic_dse.model_m2_cec import leaf
        out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);ledger=Ledger();ctx={'target_platform':'asap7','admission_id':out.name,'task_id':'reference-RTL-ownership-preflight'}
        with ledger.job(ctx):leaf([sys.executable,'-B',str(Path(__file__).resolve()),'worker','--out',str(out/'software')],out,'preflight',900,ledger,ctx)
        print((out/'preflight.log').read_text()[-5000:])
