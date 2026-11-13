"""Cycle/reset/hold validation of parameterized larger S qualification banks."""
import argparse
from pathlib import Path
import random
import subprocess

from experiments.arithmetic_dse import block_pipeline_state_samples as samples
from experiments.arithmetic_dse.model_fast_preflight import write


def run(out):
    out.mkdir(parents=True,exist_ok=False)
    specs=[samples.specification([16]*32,reset_seed=1),
           samples.specification([16]*96,reset_seed=2),
           samples.specification([72]*24,reset_seed=3),
           samples.specification([48]*64,lifetimes=[(1,1) if i%2==0 else (2,2) for i in range(64)],reset_seed=4)]
    evidence=[];total_checks=0
    for index,s in enumerate(specs):
        d=out/s['id'];d.mkdir();write(d/'specification.json',s);(d/'source.sv').write_text(samples.source(s))
        widths={f'launch.data_{j}':r['width'] for j,r in enumerate(s['roots'])}
        widths.update({'launch.valid':1,'external.valid':1})
        widths.update({f'native.valid_{k}':1 for k in range(1,s['depth']+1)})
        widths.update({'native.'+x['name']:x['variable_bits'] for x in s['slots']})
        widths.update({f'external.data_{j}':s['words'][j]['variable_bits'] for j in s['external_words']})
        old=dict.fromkeys(widths,0);rng=random.Random(20261112+index);bench=['module TB;reg clk=0,rstn,iv,we_iv;wire y,ov;']
        ports=['.clk(clk)','.rstn(rstn)','.iv(iv)','.we_iv(we_iv)','.y(y)','.ov(ov)']
        for j,r in enumerate(s['roots']):
            bench.append(f'reg [{r["width"]-1}:0] in{j};reg we{j};');ports += [f'.in{j}(in{j})',f'.we{j}(we{j})']
        bench += ['ModelBundle dut('+','.join(ports)+');','initial begin']
        for cycle in range(64):
            reset=cycle in (0,1,23,44);inputs=dict(iv=int(cycle%5 not in (1,3)),we_iv=int(cycle%7!=2))
            for j,r in enumerate(s['roots']):inputs.update({f'in{j}':rng.getrandbits(r['width']),f'we{j}':int((cycle+j)%6!=2)})
            new=samples.step(s,old,inputs,reset)
            bench.append('clk=0;rstn='+str(int(not reset))+';'+''.join(f'{name}={max(1,value.bit_length())}\'h{value:x};' for name,value in inputs.items())+'#5;clk=1;#1;')
            for name,width in widths.items():
                bench.append(f'if(dut.{name}!=={width}\'h{new[name]:x})$fatal(1,"bank{index} cycle{cycle} {name}");')
                total_checks+=1
            bench.append('#4;');old=new
        bench += ['$display("COMMON_STATE_RTL_PASS");$finish;end endmodule']
        (d/'tb.sv').write_text('\n'.join(bench)+'\n')
        with (d/'simulation.log').open('w') as stream:
            subprocess.run(['iverilog','-g2012','-s','TB','-o','sim.vvp','source.sv','tb.sv'],cwd=d,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=60)
            subprocess.run(['vvp','sim.vvp'],cwd=d,stdout=stream,stderr=subprocess.STDOUT,check=True,timeout=60)
        evidence.append(dict(id=s['id'],native_data_bits=s['features']['native_data_bits'],
                             words=len(s['words']),max_variable_width=max(s['word_widths']) if 'word_widths' in s else max(w['variable_bits'] for w in s['words']),
                             total_FF_bits=sum(s['expected_FF_bits'].values()),cycles=64))
    rejected=0
    for f in (lambda:samples.specification([8]*97),lambda:samples.specification([97]),
              lambda:samples.specification([64]*64),lambda:samples.specification([16]*2,root_widths=(96,96)),
              lambda:samples.specification([16]*2,depth=3),lambda:samples.specification([16]*2,lifetimes=[(0,2),(1,2)]),
              lambda:samples.specification([96]*3,external_words=[0,1,2])):
        try:f()
        except ValueError:rejected+=1
        else:raise ValueError('invalid state bank accepted')
    write(out/'acceptance.json',dict(status='passed',banks=evidence,registered_state_comparisons=total_checks,
                                   rejected_invalid_specs=rejected,physical_preservation_qualified=False,price_qualification=False))
    print('COMMON_STATE_SOFTWARE_PASS banks='+str(len(specs))+' comparisons='+str(total_checks)+' negatives='+str(rejected),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);a=p.parse_args();run(a.out.resolve())
