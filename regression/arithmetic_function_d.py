"""Independent numerical selection, real RTL cycles and D rejection checks."""
import argparse
from collections import defaultdict
from copy import deepcopy
import inspect
import json
import math
from pathlib import Path
import random
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.stage8_d_output_v1 import verify,command
from experiments.arithmetic_dse.operator_condition_model import query
from experiments.arithmetic_dse.stage67_shared_model_v2 import linear,predict
from experiments.arithmetic_dse import stage67_factored_timing_v1 as timing


def close(a,b):
    if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8):raise ValueError('D numerical difference '+str((a,b)))


def projection(row,source):
    owners={n:dict(data_bits=0,data_signals=0,valid_bits=0,enable_domains=0,reset_one_bits=0) for n in ('input_service','native_state','external_state')}
    nodes={n['id']:n for n in row['graph']['nodes']};input_owner=owners['input_service']
    for p in row['ports']:
        if not p['input'] or p['name']==source['iv']:continue
        if len(p['nodes'])!=1:raise ValueError('scalar projection required')
        n=nodes[p['nodes'][0]];mask=((1<<n['width'])-1)^sum(1<<i for i in set(n['known_zero'])|set(n['known_one']))
        if mask:
            input_owner['data_bits']+=mask.bit_count();input_owner['data_signals']+=1
            reset=sum(int(v,16)<<(64*i) for i,v in enumerate(source['reset'].get(p['name'],[])));input_owner['reset_one_bits']+=(mask&reset).bit_count()
    input_owner['valid_bits']=1;input_owner['enable_domains']=input_owner['data_signals']+1;enables=set();bits=defaultdict(int);words=defaultdict(int)
    for slot in row['state_query']['slots']:
        owner=owners['external_state' if slot['external_capture'] else 'native_state']
        if slot['valid']:owner['valid_bits']+=1
        elif slot['variable_bits']:
            owner['data_bits']+=slot['variable_bits'];owner['data_signals']+=1
            mask=sum(int(v,16)<<(64*i) for i,v in enumerate(slot['variable_mask_hex']));reset=sum(int(v,16)<<(64*i) for i,v in enumerate(slot['reset_hex']));owner['reset_one_bits']+=(mask&reset).bit_count()
            if not slot['external_capture']:enables.add(slot['enable_stage']);bits[slot['stage']]+=slot['variable_bits'];words[slot['stage']]+=1
    owners['native_state']['enable_domains']=len(enables);largest=max(bits.values(),default=0)
    control=dict(one=1.,native_enable_bits_max=largest,native_enable_bits_sqrt=math.sqrt(largest),native_enable_bits_log2=math.log2(1+largest),native_enable_words_max=max(words.values(),default=0),native_valid_targets_max=largest+2,
        native_data_bits=owners['native_state']['data_bits'],native_reset_one_bits=owners['native_state']['reset_one_bits'],input_data_bits=input_owner['data_bits'],external_data_bits=owners['external_state']['data_bits'])
    return owners,control


def nonarithmetic(row,source,binding,control,t):
    six=binding['six_path_upper_ps'];clocks=binding['control_exact_clocks'];worst=0.
    for name in ('input_data','input_enable','input_valid','external_data','external_valid'):worst=max(worst,six[name]-.8*t)
    def upper(name):
        m=binding['control_models'][name];values=[]
        for clock in clocks:
            f=dict(control);f.update({'exact_SDC_'+str(c):int(c==clock) for c in clocks});values.append(linear(m['regression'],f)+m['train_upper_correction_ps']+m['reserve_ps'])
        return max(values)
    for stage in range(row['state_query']['internal_stages']):
        if any(not s['valid'] and not s['external_capture'] and s['stage']==stage+1 and s['variable_bits'] for s in row['state_query']['slots']):worst=max(worst,upper('native_enable')-t)
        worst=max(worst,upper('native_valid')-t)
    nodes={n['id']:n for n in row['graph']['nodes']};placement=row['placement']
    def arithmetic_here(n,stage,seen):
        if n in seen or placement[n]!=stage or nodes[n]['kind']=='constant':return False
        seen.add(n)
        if nodes[n]['kind'] in ('add','addcarry','mul'):return True
        return any(arithmetic_here(a['node'],stage,seen) for a in nodes[n]['operands'] if a['kind']=='symbol')
    for slot in row['state_query']['slots']:
        if not slot['valid'] and slot['variable_bits'] and not arithmetic_here(slot['origin'],slot['stage']-1,set()):worst=max(worst,six['external_data' if slot['external_capture'] else 'native_data']-t)
    return max(0.,worst)


def parity(out):
    a=verify(out);policy=read(a['dependencies']['composition']['path']);node=read(a['dependencies']['node']['path']);binding=read(a['dependencies']['S_binding']['path']);S=read(Path(a['dependencies']['S_binding']['path']).parent/'reused-S.json');source=read(out/'source-request.json')['source']
    text=inspect.getsource(timing.estimate).replace("policy['version']!='factored-state-shared-v1'","policy['version']!='factored-state-shared-v2'");ns=dict(timing.estimate.__globals__);ns['area']=lambda *args:{};exec(compile(text,__file__,'exec'),ns)
    cases=[];query_checks=0;arc_checks=0
    for target in a['targets_ps']:
        directory=out/'outputs'/('T'+str(target));report=read(directory/'selection.json');scores=[]
        if report['output_scope']!=a['output_scope'] or not report['coverage_complete'] or report['formal_D_selection'] or report['reset_timing_checked'] or not report['prototype_D_selection'] or report['candidate_PPA_calls']:raise ValueError('D scope/coverage changed')
        for row in report['candidates']:
            if row['status']!='covered':raise ValueError('uncovered candidate emitted RTL')
            actual=row['estimate'];owners,control=projection(row,source);areas={n:linear(S['stages']['grt']['area_models'][n],f) for n,f in owners.items()};prices={}
            for q in row['queries']:
                p=query(node,q['descriptor']);query_checks+=1
                if p['status']!='covered' or q['trace']['node'] in prices:raise ValueError('missing or duplicate arithmetic charge')
                prices[q['trace']['node']]=p
            for q in actual['node_prices']:
                p=prices[q['node']]
                for lhs,rhs in [('delay_ps','operator_delay_ps'),('reserve_ps','delay_reserve_ps'),('area_um2','comb_area_um2')]:close(q[lhs],p[rhs])
            areas['operators']=sum(p['comb_area_um2'] for p in prices.values());ff=sum(f['data_bits']+f['valid_bits'] for f in owners.values())
            features=dict(one=1.,total_FF_bits=ff,sqrt_FF_bits=math.sqrt(ff),predicted_functional_area_um2=sum(areas.values()),reset_one_bits=sum(f['reset_one_bits'] for f in owners.values()),input_data_bits=owners['input_service']['data_bits'],input_ports=owners['input_service']['data_signals'],clock_pressure=1500/target)
            areas.update(predict(policy,features,target))
            if set(areas)!=set(actual['owner_area_um2']):raise ValueError('D owner inventory differs')
            for n,v in areas.items():close(v,actual['owner_area_um2'][n])
            for n,v in features.items():close(v,actual['shared_features'][n])
            close(sum(areas.values()),row['total_area_um2'])
            v=dict(state=row['state_query'],cuts=row['cuts']);predicted=ns['estimate'](row['graph'],v,dict(target_ps=target,queries=row['queries']),policy,node,S)
            for left,right in zip(predicted['stages'],actual['stages'],strict=True):
                connections=[e|dict(wire_point_ps=policy['inter_arithmetic_wire_point_ps'] if e['owner']=='inter_arithmetic' else 0.) for e in left['connections']]
                if connections!=right['connections']:raise ValueError('D normalized bit arcs differ')
                arc_checks+=len(connections)
                for x,y in zip(left['captures'],right['captures'],strict=True):
                    if x.keys()!=y.keys():raise ValueError('D capture record differs')
                    for k in x:close(x[k],y[k])
            violation=max(predicted['decision_arithmetic_violation_ps'],nonarithmetic(row,source,binding,control,target));close(violation,row['timing_violation_ps']);scores.append((violation,sum(areas.values()),row['view']))
        feasible=any(v==0 for v,_,_ in scores);best=min((0. if feasible else v,area,name) for v,area,name in scores if not feasible or v==0)
        if best[2]!=report['selected_view'] or report['selection_status']!=('predicted_feasible_selected' if feasible else 'target_unmet'):raise ValueError('D selected another objective result')
        close(best[1],report['selected_area_um2']);close(best[0],report['selected_timing_violation_ps'])
        if sha(directory/'D.sv')!=report['artifact']['rtl_sha256'] or sha(directory/'D_core.sv')!=report['artifact']['core_sha256']:raise ValueError('selected RTL identity differs')
        cases.append(dict(target_ps=target,view=best[2],candidate=report['selected_candidate'],area_um2=best[1],violation_ps=best[0],status=report['selection_status'],rtl=str(directory/'D.sv'),rtl_sha256=sha(directory/'D.sv')))
    result=dict(status='passed_real_function_D_selection_parity',cases=cases,query_checks=query_checks,arc_checks=arc_checks,reset_timing_checked=False,candidate_PPA_calls=0,full_D_ready=False)
    write(out/'parity.json',result);print(result,flush=True)


def negative(out,binary):
    root=out/'negative';root.mkdir(exist_ok=False);records=[]
    bad=read(out/'source-request.json');bad['source']['generated_source_sha256']='0'*64;write(root/'bad-source.json',bad)
    for name,target,limit,request in [('outside_T',499,None,None),('truncated_inventory',1500,1,None),('source_identity',1500,None,root/'bad-source.json')]:
        dest=root/name;cmd=command(out,binary,target,dest,limit,request);p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
        (root/(name+'.stdout')).write_text(p.stdout);(root/(name+'.stderr')).write_text(p.stderr)
        if p.returncode!=2 or (dest/'D.sv').exists() or (dest/'D_core.sv').exists():raise ValueError('invalid D request emitted RTL '+name)
        report=read(dest/'selection.json')
        if report['selection_status']!='cost_uncovered' or report['prototype_D_selection']:raise ValueError('invalid D request selected '+name)
        records.append(dict(name=name,exit_code=p.returncode,reason=report.get('reason',report.get('enumeration_reason'))))
    # Existing output directories are never overwritten, even on an error.
    dest=root/'already-exists';dest.mkdir();(dest/'marker').write_text('preserve\n');before={p.name:sha(p) for p in dest.iterdir()};p=subprocess.run(command(out,binary,1500,dest),capture_output=True,text=True,timeout=120)
    if p.returncode!=2 or before!={p.name:sha(p) for p in dest.iterdir()}:raise ValueError('D clobbered existing output')
    records.append(dict(name='existing_directory',exit_code=p.returncode,preserved=True));write(out/'negative.json',dict(status='passed_D_refusal_checks',checks=records,full_D_ready=False));print('D_REFUSALS_PASS checks='+str(len(records)),flush=True)


def partial(out,binary):
    a=verify(out);folder=out/'partial-domain-negative-v2';folder.mkdir(exist_ok=False)
    model=read(a['dependencies']['node']['path']);model['operations']['mul']['domain']['numeric_support']['lhs_width']=[8,16];write(folder/'partial-node-fixture.json',model)
    policy=read(a['dependencies']['composition']['path']);policy['operator_model_sha256']=sha(folder/'partial-node-fixture.json');write(folder/'partial-policy-fixture.json',policy)
    dest=folder/'output';cmd=command(out,binary,1500,dest);cmd[cmd.index('--node-model')+1]=str(folder/'partial-node-fixture.json');cmd[cmd.index('--composition-policy')+1]=str(folder/'partial-policy-fixture.json')
    run=subprocess.run(cmd,capture_output=True,text=True,timeout=120);(folder/'stdout.log').write_text(run.stdout);(folder/'stderr.log').write_text(run.stderr);report=read(dest/'selection.json');covered=sum(r['status']=='covered' for r in report['candidates'])
    if run.returncode!=2 or not 0<covered<len(report['candidates']) or report['coverage_complete'] or report['prototype_D_selection'] or (dest/'D.sv').exists():raise ValueError('partial function coverage silently selected a subset')
    verify(out);write(folder/'proof.json',dict(status='passed_partial_function_domain_refusal',covered=covered,uncovered=len(report['candidates'])-covered,RTL_emitted=False,fixture_only=True,published_models_changed=False,full_D_ready=False));print('D_PARTIAL_DOMAIN_REFUSED covered='+str(covered)+' uncovered='+str(len(report['candidates'])-covered),flush=True)


def cycles(out):
    a=verify(out);source=read(out/'source-request.json')['source'];folder=out/'simulation';folder.mkdir(exist_ok=False);reports=[read(out/'outputs'/('T'+str(t))/'selection.json') for t in a['targets_ps']]
    ports=reports[0]['artifact']['ports'];inputs=[p for p in ports if p['direction']=='input'];outputs=[p for p in ports if p['direction']=='output']
    by_suffix={p['name'].rsplit('_',1)[-1]:p for p in inputs}
    if set(by_suffix)!=set('abc') or len(outputs)!=1 or outputs[0]['width']!=64 or a['latency']!=2:raise ValueError('MAC cycle regression expects a,b,c -> 64-bit y and L=2')
    def reference(x):return (x[by_suffix['a']['name']]*x[by_suffix['b']['name']]+x[by_suffix['c']['name']])&((1<<64)-1)
    def reset_value(p):return int(p['reset_literal'].split("'h")[1],16)&((1<<p['width'])-1)
    held={p['name']:reset_value(p) for p in inputs};core=reference(held);iv=cv=0;rng=random.Random(20261111);vectors=[];valid_checks=0;cycles_count=256
    if core!=reset_value(outputs[0]):raise ValueError('independent reset arithmetic differs from output capture reset')
    ni=sum(p['width'] for p in inputs);bits=3+ni+len(inputs)+65
    for i in range(cycles_count):
        rst=int(i not in (0,1,53,54,129,201));ivd=int(i%9 not in (2,3,6));ivw=int(i%7!=4)
        data={p['name']:rng.getrandbits(p['width']) for p in inputs};wen={p['name']:int((i+j)%6!=2) for j,p in enumerate(inputs)}
        if i in (4,5,6,7):data={p['name']:(1<<p['width'])-1 for p in inputs}
        expected=core if rst else reset_value(outputs[0]);ov=cv if rst else 0;valid_checks+=ov;word=0
        for value,width in [(rst,1),(ivd,1),(ivw,1)]+[(data[p['name']],p['width']) for p in inputs]+[(wen[p['name']],1) for p in inputs]+[(expected,64),(ov,1)]:word=(word<<width)|value
        vectors.append(format(word,'x'))
        if not rst:held={p['name']:reset_value(p) for p in inputs};iv=cv=0;core=reference(held)
        else:
            if iv:core=reference(held)
            cv=iv;held.update({n:data[n] for n in held if wen[n]})
            if ivw:iv=ivd
    (folder/'vectors.hex').write_text('\n'.join(vectors)+'\n');rtl=[];decl=[];checks=[];pre=[];native_checks=0
    for i,(target,report) in enumerate(zip(a['targets_ps'],reports)):
        raw=(out/'outputs'/('T'+str(target))/'D.sv').read_text();names=re.findall(r'\bmodule\s+(\w+)\s*\(',raw);rename={n:'Case'+str(i)+'_'+n for n in names}
        raw=re.sub(r'\b(?:'+'|'.join(re.escape(n) for n in sorted(names,key=len,reverse=True))+r')\b',lambda m:rename[m[0]],raw);rtl.append(raw)
        decl.append(f'wire ov{i};wire [63:0] y{i};');conn=['.clk(clk)','.rstn(rstn)','.iv_data(ivd)','.iv_wen(ivw)',f'.ov(ov{i})',f'.{outputs[0]["name"]}(y{i})']
        conn += [f'.{p["name"]}_data(in{j}),.{p["name"]}_wen(wen{j})' for j,p in enumerate(inputs)];decl.append('Case'+str(i)+'_D dut'+str(i)+'('+','.join(conn)+');')
        checks += [f'if(ov{i}!==expected_valid)$fatal(1,"D valid T{target} cycle%0d",cycle);',f'if((expected_valid||!rstn)&&y{i}!==expected)$fatal(1,"D data T{target} cycle%0d got%h expected%h",cycle,y{i},expected);']
        state=report['artifact']['state_query'];valids={s['stage']:s['name'] for s in state['slots'] if s['valid'] and not s['external_capture']}
        for j,slot in enumerate(s for s in state['slots'] if not s['external_capture']):
            name=slot['name'];path=f'dut{i}.core.{name}';old=f'old{i}_{j}';en=f'en{i}_{j}';width=slot['declared_width'];reset=sum(int(v,16)<<(64*k) for k,v in enumerate(slot['reset_hex']));decl.append(f'reg [{width-1}:0] {old};reg {en};');pre.append(old+'='+path+';')
            checks.append(f'if(!rstn&&{path}!=={width}\'h{reset:x})$fatal(1,"D native reset T{target}/{name}");');native_checks+=1
            if not slot['valid']:
                enable=source['iv'] if slot['enable_stage']==0 else valids[slot['enable_stage']];pre.append(f'{en}=dut{i}.core.{enable};');checks.append(f'if(rstn&&!{en}&&{path}!=={old})$fatal(1,"D native hold T{target}/{name}");')
    (folder/'all.sv').write_text('\n'.join(rtl));globaldecl=['module DTb;reg clk=0,rstn,ivd,ivw;reg [63:0] expected;reg expected_valid;integer cycle;']
    globaldecl += [f'reg [{p["width"]-1}:0] in{j};reg wen{j};' for j,p in enumerate(inputs)];globaldecl+=decl+[f'reg [{bits-1}:0] vectors[0:{cycles_count-1}];']
    drive='{'+','.join(['rstn','ivd','ivw']+[f'in{j}' for j in range(len(inputs))]+[f'wen{j}' for j in range(len(inputs))]+['expected','expected_valid'])+'}=vectors[cycle];'
    tb='\n'.join(globaldecl)+'\ninitial begin $readmemh("'+str(folder/'vectors.hex')+'",vectors);\n'+f'for(cycle=0;cycle<{cycles_count};cycle=cycle+1)begin clk=0;'+drive+'\n#4;\n'+'\n'.join(pre)+'\n#1;clk=1;#1;\n'+'\n'.join(checks)+'\n#4;end $display("FUNCTION_D_RTL_PASS targets='+str(len(reports))+' cycles='+str(cycles_count)+'");$finish;end endmodule\n'
    (folder/'tb.sv').write_text(tb);write(folder/'contract.json',dict(cases=len(reports),cycles_per_case=cycles_count,valid_data_checks=valid_checks*len(reports),native_words_checked_per_cycle=native_checks,
        behaviors=['independent source write enables','held valid','bubbles','back-to-back data','unsigned overflow','nonzero functional reset','in-flight reset','native FF hold'],reset_timing_checked=False,full_D_ready=False));print('D_RTL_CYCLES_PREPARED cases='+str(len(reports))+' valid_checks='+str(valid_checks*len(reports)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('parity','negative','partial','cycles'));p.add_argument('--out',type=Path,required=True);p.add_argument('--binary',type=Path);a=p.parse_args()
    if a.action=='negative':negative(a.out.resolve(),a.binary.resolve())
    elif a.action=='partial':partial(a.out.resolve(),a.binary.resolve())
    else:{'parity':parity,'cycles':cycles}[a.action](a.out.resolve())
