"""Independent actual-state S reuse checks and fresh state-bank RTL checks."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import random
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.conditional_boundary_binding_v2 import new_specs


def close(a,b):
    if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8):raise ValueError('native/Python state price mismatch '+str((a,b)))


def word(values):return sum(int(v,16)<<(64*i) for i,v in enumerate(values))


def projection(graph,state,source):
    nodes={n['id']:n for n in graph['nodes']};owners={o:dict(data_bits=0,data_signals=0,valid_bits=0,enable_domains=0,reset_one_bits=0) for o in ('input_service','native_state','external_state')}
    incoming=owners['input_service']
    for port in graph['ports']:
        if port['direction']!='input' or port['name']==source['iv']:continue
        for at in port.get('nodes',port.get('element_nodes',[])):
            n=nodes[at];width=n['width'];known=word(n['known_zero_hex'])|word(n['known_one_hex']);mask=((1<<width)-1)^known;bits=mask.bit_count()
            if bits:incoming['data_bits']+=bits;incoming['data_signals']+=1;incoming['reset_one_bits']+=(word(source['reset'][port['name']])&mask).bit_count()
    incoming['valid_bits']=1;incoming['enable_domains']=incoming['data_signals']+1
    enables=set();stages=defaultdict(lambda:[0,0])
    for slot in state['slots']:
        f=owners['external_state' if slot['external_capture'] else 'native_state']
        if slot['valid']:f['valid_bits']+=1;continue
        if slot['variable_bits']:
            f['data_bits']+=slot['variable_bits'];f['data_signals']+=1;f['reset_one_bits']+=(word(slot['reset_hex'])&word(slot['variable_mask_hex'])).bit_count()
            if not slot['external_capture']:enables.add(slot['enable_stage']);stages[slot['stage']][0]+=slot['variable_bits'];stages[slot['stage']][1]+=1
    owners['native_state']['enable_domains']=len(enables);largest=max((v[0] for v in stages.values()),default=0);words=max((v[1] for v in stages.values()),default=0)
    control=dict(one=1,native_enable_bits_max=largest,native_enable_bits_sqrt=math.sqrt(largest),native_enable_bits_log2=math.log2(1+largest),
        native_enable_words_max=words,native_valid_targets_max=largest+2,native_data_bits=owners['native_state']['data_bits'],
        native_reset_one_bits=owners['native_state']['reset_one_bits'],input_data_bits=incoming['data_bits'],external_data_bits=owners['external_state']['data_bits'])
    return owners,control


def verify(run,binding,source_request):
    b=read(binding);s=read(binding.parent/b['state_model']['path']);data=read(run/'real-boundary.json');request=read(source_request);graphs={g['candidate']:g for g in request['candidates']}
    selected=[];rows=0
    for result in data['runs']:
        target=result['target_period_ps'];scores=[]
        for row in result['candidates']:
            graph=graphs[row['candidate']];view=next(v for v in graph['views'] if v['placement']==row['placement']);owners,control=projection(graph,row['state_query'],request['source']);diagnostic=row['boundary_diagnostics']
            for owner,f in owners.items():
                if f!=diagnostic['owner_features'][owner]:raise ValueError('actual owner features differ '+owner+' '+str((f,diagnostic['owner_features'][owner])))
                model=s['stages']['grt']['area_models'][owner];area=sum(c*f[n] for n,c in zip(model['features'],model['coefficients'],strict=True));close(area,row['owner_area_um2'][owner])
            for k,v in control.items():close(v,diagnostic['control_features'][k])
            ff=sum(f['data_bits']+f['valid_bits'] for f in owners.values());close(ff,diagnostic['total_FF_bits']);close(ff*b['shared']['clock_area_per_FF_um2'],row['owner_area_um2']['shared_clock'])
            nonphysical=sum(v for k,v in row['owner_area_um2'].items() if k in ('input_service','native_state','external_state','operators'))
            close(nonphysical*b['shared']['physical_area_per_functional_um2'],row['owner_area_um2']['shared_physical']);close(b['shared']['root_repair_area_um2'],row['owner_area_um2']['root_repair'])
            close(sum(row['owner_area_um2'].values()),row['total_area_um2'])
            upper={}
            for path,m in b['control_models'].items():
                values=[]
                for t in b['control_exact_clocks']:
                    f={**control,**{'exact_SDC_'+str(k):int(k==t) for k in b['control_exact_clocks']}}
                    values.append(sum(c*f[n] for n,c in zip(m['regression']['features'],m['regression']['coefficients'],strict=True))+m['train_upper_correction_ps']+m['reserve_ps'])
                upper[path]=max(values)
            max_other=0
            for check in diagnostic['nonarithmetic_checks']:
                path=check['path_class'];budget=.8*target if path.startswith('input_') or path.startswith('output_') else target
                name={'output_data':'external_data','output_valid':'external_valid','external_bypass':'external_data','native_forward_or_bypass':'native_data'}.get(path,path)
                needed=upper[name] if name in upper else b['six_path_upper_ps'][name];close(needed,check['upper_ps']);close(budget,check['budget_ps']);close(max(0,needed-budget),check['violation_ps']);max_other=max(max_other,check['violation_ps'])
            nodes={n['id']:n for n in graph['nodes']};delay={n['node']:n['operator_delay_ps']+n['delay_reserve_ps'] for n in row['node_prices']};violation=max_other
            for cut,actual in zip(view['stages'],row['stages'],strict=True):
                inside=set(cut['semantic_members']);cache={}
                def arrive(at):
                    n=nodes[at]
                    if n['constant'] or at not in inside:return 0.
                    if at not in cache:cache[at]=max((arrive(a['node'])+b['shared']['wire_per_edge_ps'] for a in n['operands'] if a['kind']=='symbol' and not nodes[a['node']]['constant']),default=0)+delay.get(at,0.)
                    return cache[at]
                required=target-b['six_path_upper_ps']['external_data' if cut['index']==request['source']['N'] else 'native_data']
                for capture,endpoint in zip(cut['captures'],actual['captures'],strict=True):
                    value=arrive(capture['value']);close(value,endpoint['arrival_ps']);close(required,endpoint['required_ps']);close(required-value,endpoint['slack_ps']);violation=max(violation,value-required)
            close(violation,row['timing_violation_ps']);scores.append((max(0,violation),row['total_area_um2'],row['view']));rows+=1
        feasible=any(v==0 for v,_,_ in scores);best=min((0 if feasible and v==0 else math.inf if feasible else v,a,name) for v,a,name in scores)
        if best[2]!=result['selected_view'] or result['formal_D_selection']:raise ValueError('actual S candidate selection mismatch')
        if sha(run/result['rtl_file'])!=result['rtl_sha256']:raise ValueError('actual S selected RTL changed')
        selected.append(dict(target_ps=target,view=best[2],area_um2=best[1],violation_ps=best[0]))
    proof=dict(status='passed',actual_views=rows,candidate_targets=len(data['runs']),negative_checks=len(data['negative_checks']),
        S_sha256=sha(binding.parent/b['state_model']['path']),binding_sha256=sha(binding),S_coefficients_unchanged=True,
        actual_state_masks_resets_enables_and_shared_terms_recomputed=True,nonarith_and_DAG_recomputed=True,selections=selected,
        old_test_labels_read=False,operator_physical_labels_read=False,production_qualified=False,full_D_ready=False)
    write(run/'state-boundary-proof.json',proof);print(proof,flush=True)


def probe_software(folder,out):
    from experiments.arithmetic_dse.model_general_state_samples_v2 import source,step
    out.mkdir(parents=True,exist_ok=False);checks=0;specs=new_specs()
    for s in specs:
        d=out/s['id'];d.mkdir();rtl=folder/'sources'/s['id']/'input.sv'
        if rtl.read_text()!=source(s):raise ValueError('proposed state RTL changed')
        widths={f'launch.data_{j}':r['width'] for j,r in enumerate(s['roots'])};widths.update({'launch.valid':1,'external.valid':1})
        widths.update({f'native.valid_{j}':1 for j in range(1,s['depth']+1)});widths.update({'native.'+x['name']:x['variable_bits'] for x in s['slots']});widths.update({f'external.data_{j}':s['words'][j]['variable_bits'] for j in s['external_words']})
        lines=['module tb;reg clk=0,rstn=0,iv=0,we_iv=0;wire y,ov;']+[f'reg [{r["width"]-1}:0] in{j}=0;reg we{j}=0;' for j,r in enumerate(s['roots'])]
        conns=['.clk(clk)','.rstn(rstn)','.iv(iv)','.we_iv(we_iv)','.y(y)','.ov(ov)']+[f'.in{j}(in{j}),.we{j}(we{j})' for j in range(len(s['roots']))]
        lines+=['ModelBundle dut('+','.join(conns)+');initial begin'];state={k:0 for k in widths};rng=random.Random(20261110+s['depth'])
        for cycle in range(128):
            reset=cycle in (0,1,45,87);inputs={'iv':int(cycle%5!=1),'we_iv':int(cycle%4!=2)};inputs.update({f'in{j}':rng.getrandbits(r['width']) for j,r in enumerate(s['roots'])});inputs.update({f'we{j}':int((cycle+j)%3!=1) for j in range(len(s['roots']))})
            new=step(s,state,inputs,reset);lines+=['clk=0;rstn='+str(int(not reset))+';'+''.join(f'{k}=128\'h{v:x};' for k,v in inputs.items())+'#4;clk=1;#1;']
            for name,value in new.items():lines.append(f'if(dut.{name}!=={widths[name]}\'h{value:x})$fatal(1,"state {name} cycle{cycle}");');checks+=1
            lines+=['#4;clk=0;#1;'];state=new
        lines+=['$display("NEW_STATE_BINDING_BANK_PASS");$finish;end endmodule'];(d/'tb.sv').write_text('\n'.join(lines)+'\n')
        for name,cmd in [('compile',['iverilog','-g2012','-s','tb','-o',str(d/'sim'),str(rtl),str(d/'tb.sv')]),('simulate',['vvp',str(d/'sim')])]:
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=120);(d/(name+'.log')).write_text(result.stdout+result.stderr)
            if result.returncode:raise ValueError('new state-bank '+name+' failed')
    proof=dict(status='passed',new_sources=len(specs),cycles_per_source=128,actual_state_checks=checks,proposal_sha256=sha(folder/'proposal.json'),
        binding_sha256=sha(folder/'binding-candidate.json'),old_independent_labels_read=False,operator_labels_read=False)
    write(out/'software-proof.json',proof);print(proof,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('verify','probe-software'));p.add_argument('--run',type=Path);p.add_argument('--binding',type=Path);p.add_argument('--request',type=Path);p.add_argument('--folder',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='verify':verify(a.run.resolve(),a.binding.resolve(),a.request.resolve())
    else:probe_software(a.folder.resolve(),a.out.resolve())
