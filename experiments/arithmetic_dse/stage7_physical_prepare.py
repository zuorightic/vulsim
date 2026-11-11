"""Real stage-validation structures and measurement preregistration; no EDA.

The former six toy DAGs remain software evidence. This successor compiles fresh
sources, materializes native placements and uses the existing real S provider.
It never changes a node-model feature, parameter, support rule or test role.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import random
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.operator_condition_model import query
from regression.arithmetic_steps123 import execute

VERSION='stage7-physical-preparation-v1'
OWNERS=['operators','input_service','native_state','external_state','shared_clock','shared_physical','root_repair']


def specs():
    rows=[]
    for name in ('serial','parallel','shared','wide_reduction','bypass','cross_stage_saved_value'):
        rows.append(dict(id=name,kind=name,w=8,v=16,role='combination_validation'))
    for name in ('serial','cross_stage_saved_value'):
        rows.append(dict(id=name+'_heldout',kind=name,w=12,v=12,role='locked_joint_test'))
    for r in rows:
        w,v=r['w'],r['v'];kind=r['kind'];r['inputs']=[dict(name='a',width=w),dict(name='b',width=w)]
        r['outputs']=[dict(name='y',width=64)]
        prefix=f'Int<{2*w}> p=Int<{2*w}>(a*b);'
        if kind in ('parallel','wide_reduction'):
            r['inputs'] += [dict(name='d',width=v),dict(name='e',width=v)]
            prefix+=f'Int<{2*v}> q=Int<{2*v}>(d*e);'
            if kind=='parallel':expr='Int<64>(p)+Int<64>(q)'
            else:
                prefix+=f'Int<64> sp{{}},sq{{}};sp.at<{40+2*w-1},40>()=p;sq.at<{32+2*v-1},32>()=q;';expr='sp+sq'
        elif kind=='shared':
            prefix+=f'Int<64> sp{{}};sp.at<{9+2*w-1},9>()=p;';expr='Int<64>(p)+sp';r['outputs'].append(dict(name='product',width=2*w))
        else:
            r['inputs'].append(dict(name='c',width=64))
            if kind=='serial':
                r['inputs'].append(dict(name='d',width=32));prefix+='Int<64> q=Int<64>(p)+Int<64>(d);';expr='q+c'
            elif kind=='cross_stage_saved_value':prefix+='Int<64> q=Int<64>(p)+c;';expr='q+Int<64>(p)'
            else:
                expr='Int<64>(p)+c';r['inputs'].append(dict(name='bypass_in',width=29));r['outputs'] += [dict(name='product',width=2*w),dict(name='bypass_out',width=29)]
        declarations=[]
        for direction in ('input','output'):
            for p in r[direction+'s']:
                declarations.append(f'#pragma {direction}_port {p["name"]}\nInt<{p["width"]}> {p["name"]};')
            valid='iv' if direction=='input' else 'ov';declarations.append(f'#pragma {direction}_port {valid}\nbool {valid};')
        extras='product=p;' if kind in ('shared','bypass') else ''
        if kind=='bypass':extras+='bypass_out=bypass_in;'
        r['source_text']='#include <fixint.hpp>\n#include <arithmetic.hpp>\n'+'\n'.join(declarations)+f'\nvoid stage7_top(){{{prefix} y={expr};{extras}}}\n'
    return rows


def reference(r,values):
    p=values['a']*values['b'];kind=r['kind'];mask=(1<<64)-1
    if kind=='serial':y=p+values['d']+values['c']
    elif kind=='parallel':y=p+values['d']*values['e']
    elif kind=='wide_reduction':y=(p<<40)+((values['d']*values['e'])<<32)
    elif kind=='shared':y=p+(p<<9)
    elif kind=='cross_stage_saved_value':y=p+values['c']+p
    else:y=p+values['c']
    out=dict(y=y&mask)
    if kind in ('shared','bypass'):out['product']=p
    if kind=='bypass':out['bypass_out']=values['bypass_in']
    return out


def init(out,model,binding):
    if out.exists():raise ValueError('preserve previous preparation')
    out.mkdir(parents=True)
    rows=specs()
    for r in rows:
        d=out/'sources'/r['id'];d.mkdir(parents=True);p=d/'source.cpp';p.write_text(r.pop('source_text'))
        r.update(source=str(p),source_sha256=sha(p));write(d/'request.json',r)
    write(out/'sources.json',dict(version=VERSION,sources=rows))
    write(out/'dependencies.json',dict(model=dict(path=str(model),sha256=sha(model)),S_binding=dict(path=str(binding),sha256=sha(binding)),
        preparation_sources={str(p.relative_to(ROOT)):sha(p) for p in (Path(__file__),ROOT/'rtlzz/testv2/arithmetic_stage7_export.cpp',ROOT/'experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl')},
        backend_calls=0,full_D_ready=False))


def export(out,tool):
    deps=read(out/'dependencies.json')
    for p in deps['preparation_sources']:
        if sha(ROOT/p)!=deps['preparation_sources'][p]:raise ValueError('preparation implementation changed')
    for r in read(out/'sources.json')['sources']:
        d=out/'sources'/r['id'];execute(out/'receipts'/(out.name+'-export-'+r['id']),'export',[
            str(tool),str(ROOT),str(d/'request.json'),deps['model']['path'],deps['S_binding']['path'],str(d/'native')],120)


def wrapper(r,v,d):
    """Same S protocol: independent writes/held iv, unconditional output capture.

    Native registers are exclusively those emitted by materializeSchedule.
    Renaming the module here only allows all sixteen cores in one simulator.
    """
    tag=r['id']+'_'+v['id'].replace('-','_');core=tag+'_core';top='Stage7_'+tag
    rtl=(d/v['rtl_file']).read_text().replace('stage7_top',core)
    declarations=['input wire clk','input wire rstn','input wire iv_data','input wire iv_wen']
    declarations += [f'input wire [{p["width"]-1}:0] {p["name"]}_data, input wire {p["name"]}_wen' for p in r['inputs']]
    declarations += [f'output wire [{p["width"]-1}:0] {p["name"]}' for p in r['outputs']]+['output wire ov']
    launch=['input wire clk','input wire rstn','input wire iv_data','input wire iv_wen','output reg iv']
    launch += [f'input wire [{p["width"]-1}:0] {p["name"]}_data, input wire {p["name"]}_wen, output reg [{p["width"]-1}:0] {p["name"]}' for p in r['inputs']]
    reset='iv<=0;'+''.join(p['name']+'<=0;' for p in r['inputs'])
    update='if(iv_wen)iv<=iv_data;'+''.join(f'if({p["name"]}_wen){p["name"]}<={p["name"]}_data;' for p in r['inputs'])
    launch_rtl=f'(* keep_hierarchy=1 *) module {tag}_Launch('+','.join(launch)+f');always @(posedge clk)if(!rstn)begin {reset}end else begin {update}end endmodule\n'
    ext=['input wire clk','input wire rstn','input wire iv','output reg ov']
    ext += [f'input wire [{p["width"]-1}:0] {p["name"]}_d, output reg [{p["width"]-1}:0] {p["name"]}' for p in r['outputs']]
    reset='ov<=0;'+''.join(p['name']+'<=0;' for p in r['outputs']);update='ov<=iv;'+''.join(f'{p["name"]}<={p["name"]}_d;' for p in r['outputs'])
    ext_rtl=f'(* keep_hierarchy=1 *) module {tag}_Capture('+','.join(ext)+f');always @(posedge clk)if(!rstn)begin {reset}end else begin {update}end endmodule\n'
    body=['wire liv,cov;']+[f'wire [{p["width"]-1}:0] l_{p["name"]};' for p in r['inputs']]+[f'wire [{p["width"]-1}:0] c_{p["name"]};' for p in r['outputs']]
    common=['.clk(clk)','.rstn(rstn)'];lc=common+['.iv_data(iv_data)','.iv_wen(iv_wen)','.iv(liv)']
    for p in r['inputs']:
        n=p['name'];lc += [f'.{n}_data({n}_data)',f'.{n}_wen({n}_wen)',f'.{n}(l_{n})']
    body += [f'(* keep_hierarchy=1 *) {tag}_Launch launch('+','.join(lc)+');']
    cc=common+['.iv(liv)','.ov(cov)']+[f'.{p["name"]}(l_{p["name"]})' for p in r['inputs']]+[f'.{p["name"]}(c_{p["name"]})' for p in r['outputs']]
    body += [f'(* keep_hierarchy=1 *) {core} core('+','.join(cc)+');']
    ec=common+['.iv(cov)','.ov(ov)']
    for p in r['outputs']:
        n=p['name'];ec += [f'.{n}_d(c_{n})',f'.{n}({n})']
    body += [f'(* keep_hierarchy=1 *) {tag}_Capture external_capture('+','.join(ec)+');']
    return top,rtl+launch_rtl+ext_rtl+f'\nmodule {top}('+','.join(declarations)+');\n'+'\n'.join(body)+'\nendmodule\n'


def endpoint_contract(r,v,e):
    nodes={n['id']:n for n in e['graph']['nodes']};slots=v['state']['slots']
    # Logical identities are frozen now. Mapped pin names must be resolved from
    # net connectivity, not guessed from these names or hierarchy prefixes.
    return dict(version='stage7-logical-endpoint-contract-v1',cuts=v['cuts'],
        native_registers=v['registers'],state_slots=slots,
        input_service=[dict(port=p['name'],width=p['width'],scope='launch',data_enable=p['name']+'_wen',reset=0) for p in r['inputs']],
        valid_service=dict(scope='launch',write_enable='iv_wen',held=True,reset=0),
        external_capture=dict(scope='external_capture',policy='unconditional',ports=r['outputs'],valid='ov',reset=0),
        operator_scopes=[dict(node=n,scope='core/rtlzz_arith_'+str(n),width=nodes[n]['width']) for n in e['arithmetic_nodes']],
        path_classes=['input_data','input_enable','input_valid','native_data','native_enable','native_valid','external_data','external_valid','bypass','arithmetic_through','whole_shell'],
        required_readout=['all dynamic capture D bits, all relevant launch Q bits and input data/control ports',
            'worst setup slack per capture bank/class/stage; no empty path silently accepted',
            'whole-shell worst, arithmetic-through worst and independent node maxima with separate witnesses',
            'every cell step verifies Liberty direction and actual timing arc; wire endpoints/net connectivity checked',
            'native origin, stage, enable, reset and variable mask matched to actual mapped FF/constant census',
            'node max input-to-output delay/area and on-path node segments separately; no Q-to-D relabeling'],
        mapped_resolution='pending_physical_qualification',per_instance_owner_required=True,
        unowned_cell_policy='reject; root multi-input repair is not a buffer or free G residual')


def diagnose(r,v,e,model):
    rows=[]
    for target in v['targets']:
        prices=[dict(node=q['trace']['node'],**query(model,q['descriptor'],allow_candidate=True)) for q in target['queries']]
        rows.append(dict(target_ps=target['target_ps'],prices=prices,S_covered=target['real_S_candidate']['covered'],
            S_reason=target['real_S_candidate']['reason'],joint_qualified=False,zero_G=compose(e,v,target,prices)))
    return dict(source=r['id'],placement=v['id'],role=r['role'],rows=rows,diagnostic_only=True)


def compose(e,v,target,prices):
    """Same stage-local recurrence as D, retaining signed capture slacks."""
    quote=target['real_S_candidate'];bad=[p for p in prices if p['status']!='covered']
    if bad or not quote['covered']:return dict(status='cost_uncovered',uncovered_nodes=[p['node'] for p in bad],S_reason=quote['reason'])
    costs={p['node']:p for p in prices}
    if len(costs)!=len(prices) or set(costs)!=set(e['arithmetic_nodes']):raise ValueError('duplicate/missing node price')
    if set(quote['owners_um2'])!=set(OWNERS)-{'operators'}:raise ValueError('missing/overlapping non-node owner')
    nodes={n['id']:n for n in e['graph']['nodes']};stages=[]
    for cut,b in zip(v['cuts'],quote['stages'],strict=True):
        if cut['sha256']!=b['cut_sha256']:raise ValueError('stale stage boundary')
        launch={x['node']:x['ps'] for x in b['launches']};required={x['node']:x['ps'] for x in b['captures']};wires={(x['from'],x['to']):x['ps'] for x in b['wires']}
        if set(launch)!=set(cut['launches']) or set(required)!={x['node'] for x in cut['captures']} or set(wires)!={tuple(x) for x in cut['edges']}:raise ValueError('incomplete launch/capture/wire ownership')
        values={};visiting=set()
        def arrival(n):
            if nodes[n]['constant']:return 0.
            if n in launch:return launch[n]
            if n in values:return values[n]
            if n not in cut['members'] or n in visiting:raise ValueError('unpriced launch or cycle')
            visiting.add(n)
            a=max((arrival(p)+wires[p,n] for p in nodes[n]['parents'] if not nodes[p]['constant']),default=0.)
            if n in costs:a+=costs[n]['conservative_operator_delay_ps']
            visiting.remove(n);values[n]=a;return a
        endpoints=[dict(node=n,arrival_ps=arrival(n),required_ps=t,slack_ps=t-arrival(n)) for n,t in required.items()]
        stages.append(dict(stage=cut['stage'],captures=endpoints,violation_ps=max([0.,b['other_timing_violation_ps']]+[-x['slack_ps'] for x in endpoints])))
    owners=dict(quote['owners_um2'],operators=sum(p['comb_area_um2'] for p in prices))
    return dict(status='diagnostic_covered',stages=stages,owners_um2=owners,total_area_um2=sum(owners.values()),
        violation_ps=max(s['violation_ps'] for s in stages),G_area_um2=0,G_delay_ps=0,joint_qualified=False)


def prepare_products(out):
    deps=read(out/'dependencies.json');model=read(Path(deps['model']['path']));sv=[];decl=[];setups=[];drivers=[];checks=[];prechecks=[];rows=[];endpoints=[];diagnostics=[]
    cycles=192
    for r in read(out/'sources.json')['sources']:
        d=out/'sources'/r['id']/'native';e=read(d/'export.json')
        if len(e['arithmetic_nodes'])!=(2 if r['kind'] in ('shared','bypass') else 3):raise ValueError('optimized graph lost required combination '+r['id'])
        for v in e['variants']:
            top,rtl=wrapper(r,v,d);sv.append(rtl);i=len(rows);stem=r['id']+'/'+v['id'];rng=random.Random(int(hashlib.sha256(stem.encode()).hexdigest()[:16],16))
            widths=[p['width'] for p in r['inputs']];total_in=sum(widths)+len(widths)+3;total_out=sum(p['width'] for p in r['outputs'])+1;bits=total_in+total_out
            held=dict.fromkeys((p['name'] for p in r['inputs']),0);iv=0;core=reference(r,held);core_valid=0;vectors=[]
            for cycle in range(cycles):
                rst=int(cycle not in (0,1,71,72,131));iv_data=int(cycle%7 not in (1,2,5));iv_wen=int(cycle%11!=4)
                data={p['name']:rng.getrandbits(p['width']) for p in r['inputs']};wen={p['name']:int((cycle+j)%9!=3) for j,p in enumerate(r['inputs'])}
                if cycle in (5,6,7):data={p['name']:(1<<p['width'])-1 for p in r['inputs']}
                expected=core if rst else dict.fromkeys(core,0);ov=core_valid if rst else 0
                word=0
                for value,width in [(rst,1),(iv_data,1),(iv_wen,1)]+[(data[p['name']],p['width']) for p in r['inputs']]+[(wen[p['name']],1) for p in r['inputs']]+[(expected[p['name']],p['width']) for p in r['outputs']]+[(ov,1)]:word=(word<<width)|value
                vectors.append(format(word,'x'))
                if not rst:held=dict.fromkeys(held,0);iv=0;core=dict.fromkeys(core,0);core_valid=0
                else:
                    if iv:core=reference(r,held)
                    core_valid=iv
                    held.update({n:data[n] for n in held if wen[n]})
                    if iv_wen:iv=iv_data
            vp=out/'vectors'/f'vectors-{i}.hex';vp.parent.mkdir(exist_ok=True);vp.write_text('\n'.join(vectors)+'\n')
            decl += [f'reg [{bits-1}:0] vec{i}[0:{cycles-1}];reg rst{i},ivd{i},ivw{i};wire ov{i};']
            decl += [f'reg [{p["width"]-1}:0] in{i}_{p["name"]};reg wen{i}_{p["name"]};' for p in r['inputs']]
            decl += [f'wire [{p["width"]-1}:0] out{i}_{p["name"]};' for p in r['outputs']]
            conn=['.clk(clk)',f'.rstn(rst{i})',f'.iv_data(ivd{i})',f'.iv_wen(ivw{i})',f'.ov(ov{i})']
            conn += [f'.{p["name"]}_data(in{i}_{p["name"]}),.{p["name"]}_wen(wen{i}_{p["name"]})' for p in r['inputs']]
            conn += [f'.{p["name"]}(out{i}_{p["name"]})' for p in r['outputs']]
            decl += [f'{top} dut{i}('+','.join(conn)+');'];setups.append(f'$readmemh("{vp}",vec{i});')
            inputs=[f'rst{i}',f'ivd{i}',f'ivw{i}']+[f'in{i}_{p["name"]}' for p in r['inputs']]+[f'wen{i}_{p["name"]}' for p in r['inputs']]
            drivers.append('{'+','.join(inputs)+f'}}=vec{i}[j][{bits-1}:{total_out}];')
            results=[f'out{i}_{p["name"]}' for p in r['outputs']]+[f'ov{i}']
            checks.append('if({'+','.join(results)+f'}}!==vec{i}[j][{total_out-1}:0])$fatal(1,"output {stem} cycle%0d got%h expected%h",j,{{'+','.join(results)+f'}},vec{i}[j][{total_out-1}:0]);')
            # Check actual native gates/reset on every register in addition to
            # independent end-to-end arithmetic/cycle comparisons.
            for k,reg in enumerate(v['registers']):
                path=f'dut{i}.core.{reg["name"]}';old=f'old{i}_{k}';en=f'en{i}_{k}'
                decl.append(f'reg [{reg["width"]-1}:0] {old};reg {en};');prechecks.append(f'{old}={path};')
                if reg['enable_name']:prechecks.append(f'{en}=dut{i}.core.{reg["enable_name"]};')
                checks.append(f'if(!rst{i}&&{path}!==0)$fatal(1,"native reset {stem}/{reg["name"]}");')
                if reg['enable_name']:checks.append(f'if(rst{i}&&!{en}&&{path}!=={old})$fatal(1,"native enable {stem}/{reg["name"]}");')
            contract=endpoint_contract(r,v,e);cp=d/(v['id']+'-endpoints.json');write(cp,contract);endpoints.append(str(cp.relative_to(out)))
            rtlp=d/(v['id']+'-measurement.sv');rtlp.write_text(rtl)
            rows.append(dict(id=stem,source=r['id'],role=r['role'],placement=v['id'],L=2,II=1,service_latency=1,
                source_sha256=r['source_sha256'],rtl=str(rtlp.relative_to(out)),rtl_sha256=sha(rtlp),endpoint_contract=str(cp.relative_to(out)),endpoint_sha256=sha(cp),
                graph_sha256=e['graph']['sha256'],layout_sha256=v['state']['layout_sha256'],arithmetic_nodes=e['arithmetic_nodes']))
            diagnostics.append(diagnose(r,v,e,model))
    (out/'all-measurement.sv').write_text('\n'.join(sv));(out/'tb.sv').write_text('module Stage7Tb;reg clk=0;integer j;\n'+'\n'.join(decl)+'\ninitial begin\n'+'\n'.join(setups)+f'\nfor(j=0;j<{cycles};j=j+1)begin clk=0;\n'+'\n'.join(drivers)+'\n#4;\n'+'\n'.join(prechecks)+'\n#1;clk=1;#1;\n'+'\n'.join(checks)+'\n#4;end $display("STAGE7_REAL_RTL_PASS cores='+str(len(rows))+' cycles='+str(cycles)+'");$finish;end endmodule\n')
    write(out/'structures.json',dict(version=VERSION,rows=rows,endpoint_files=endpoints,cycles=cycles,backend_calls=0))
    write(out/'coverage-diagnostic.json',dict(version=VERSION,model_sha256=deps['model']['sha256'],rows=diagnostics,
        summary=dict(Counter(p['status'] for d in diagnostics for t in d['rows'] for p in t['prices'])),
        full_D_ready=False,physical_admission_allowed=False))
    write(out/'protocol.json',protocol(rows,deps))


def protocol(rows,deps):
    return dict(version='stage7-physical-validation-preregistration-v1',zero_G_first=True,dependencies=deps,
        source_roles='all targets/stages/placements of one source keep its role; no arithmetic training or old test reuse',
        clocks_ps=[500,1500,3000],reserved_exact_T_ps=1000,
        primary_matrix=[dict(structure=r['id'],role=r['role'],target_ps=t) for r in rows for t in (500,1500,3000)],
        matrix_is_capacity_envelope_not_admission=True,
        pilot=dict(requested=[r['id'] for r in rows if r['source'] in ('serial','cross_stage_saved_value')],target_ps=1500,max_synth=4,max_grt=4,automatic_retry=False,
            prerequisite='new exact funded admission after node independent pass, complete query coverage and same real service contract'),
        resources=dict(threads_per_tool=4,max_concurrent_tasks=2,timeout_synth_s=300,timeout_grt_s=1200,memory_limit_mib=8192,
            preserve_future_synth=688,preserve_future_grt=688,preserve_future_wall_s=86400,preserve_future_cpu_s=172800,preserve_future_storage_gib=30),
        hard_gates=['cycle arithmetic/valid/reset/II contract','mapped source-stage-enable-reset-variable-bit retention',
            'no undeclared owner or duplicated cell; owner sum equals physical area',
            'all dynamic endpoints covered with exact connectivity and Liberty arcs',
            'model/S/flow/RTL/layout/cut/target identities bound before measuring',
            'all source/role/target/placements kept in denominator, including uncovered and failures'],
        area_owners=OWNERS,wire_owner='existing S edge estimate charged once per DAG edge; measured inter-node wire once; residual never re-adds S wire',
        timing_checks=dict(full_stage_relative_error_median_max=.15,full_stage_relative_error_p95_max=.35,
            per_class_p95_max=.50,delay_denominator_floor_ps=10,area_denominator_floor_um2=.01,
            false_feasible_max=0,setup_pass_ps=0,setup_near_zero_review_ps=5,hold='reported, not setup qualification',
            conservative_rejection='report all counts/fractions and ps excess separately; do not hide using absolute error',
            ranking='same source/T/L/II pair: feasible before unmet; min total area among feasible; else min worst violation then area; all non-tied pairs must agree',
            rank_tie_area_relative=.05,rank_tie_violation_ps=5),
        error_partition=['base predicted vs measured independent node maxima and exclusive area',
            'DAG of measured independent maxima vs actual on-path segments: conservatism, not node fit error',
            'measured wire and launch/capture/clock/IO boundary vs each distinct owner',
            'unique state/shared/repair area and duplicate/missing charges',
            'remaining stable selection-relevant residual only after preceding gates'],
        locked_joint_test='two complete new parameter sources; collect only after node/S/G parameters, support, reserves, selector and stage validation decision freeze',
        frozen_node_model='candidate frozen, independent result required before formal physical admission; failure is retained and blocks release',
        physical_admission_allowed=False,full_D_ready=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('init','export','products'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--model',type=Path);p.add_argument('--binding',type=Path);p.add_argument('--tool',type=Path);a=p.parse_args();out=a.out.resolve()
    if a.action=='init':init(out,a.model.resolve(),a.binding.resolve())
    elif a.action=='export':export(out,a.tool.resolve())
    else:prepare_products(out)


if __name__=='__main__':main()
