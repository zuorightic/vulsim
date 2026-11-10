"""Independent conditional-consumer software checks; no physical label reads."""
import argparse
from copy import deepcopy
import gzip
import json
import math
from pathlib import Path
import random
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import operator_condition_model as model
from experiments.arithmetic_dse import operator_query


def prepare(out):
    out.mkdir(parents=True,exist_ok=False)
    old=ROOT/'build/step7-operator-query-20261110/query-hierarchy-20261110-v4/input/request.json'
    request=read(old);source=Path(request['source']['source'])
    if sha(source)!=request['source']['generated_source_sha256']:raise ValueError('public source changed')
    shutil.copy2(source,out/'source.cpp');request['source']['source']=str(out/'source.cpp');write(out/'request.json',request)
    bundle=dict(version=model.VERSION,profile_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json'),
        operator_boundary_policy='unsigned-op-hierarchy-v1',quality_status='awaiting_independent',test_only=True,full_D_ready=False,operations={})
    for op in ('add','mul'):
        delay=dict(kind='linear',features=['width_product' if op=='mul' else 'result_width','mapped_dynamic_bits','consumer_result_max','target_period_ps'],
            coefficients=[.12 if op=='mul' else .3,.04,.02,.001],intercept=12. if op=='mul' else 7.)
        area=dict(kind='linear',features=['width_product' if op=='mul' else 'result_width','mapped_unique_bits'],coefficients=[.05 if op=='mul' else .08,.01],intercept=0.)
        bundle['operations'][op]=dict(status='awaiting_independent',delay=delay,area=area,delay_reserve_ps=2.,
            domain=dict(numeric_support=dict(lhs_width=[1,67],rhs_width=[1,67],result_width=[1,65],target_period_ps=[25,12000])))
    write(out/'fixture.json',bundle)
    print('CONDITIONAL_FIXTURE_PREPARED; no physical prices or test labels',flush=True)


def close(a,b):
    if not math.isclose(a,b,rel_tol=1e-10,abs_tol=1e-8):raise ValueError('independent numeric mismatch '+str((a,b)))


def score(graph,view,rows,target,state):
    nodes={n['id']:n for n in graph['nodes']};placement=view['placement'];delays={};area=0
    for row in rows:
        price=model.query(CANDIDATE,row['descriptor'],True)
        if price['status']!='covered':raise ValueError('analytical fixture unexpectedly uncovered')
        for name in ('operator_delay_ps','delay_reserve_ps','comb_area_um2'):close(price[name],row[name])
        origin=row['node']
        if origin in delays:raise ValueError('shared operator charged twice')
        delays[origin]=price['conservative_operator_delay_ps'];area+=price['comb_area_um2']
    stages=[];worst=0
    for cut in view['stages']:
        inside=set(cut['semantic_members']) if 'semantic_members' in cut else set(cut['members']);cache={}
        def arrival(at):
            node=nodes[at]
            if node['constant']:return 0.
            if at not in inside:return 20.+(.2*target if cut['index']==0 else 0.)
            if at not in cache:
                previous=[arrival(a['node'])+.5 for a in node['operands'] if a['kind']=='symbol' and not nodes[a['node']]['constant']]
                cache[at]=max(previous,default=0.)+delays.get(at,0.)
            return cache[at]
        endpoints=[];violation=0
        for capture in cut['captures']:
            at=capture['value'];value=arrival(at);required=target-20.;slack=required-value;violation=max(violation,-slack)
            endpoints.append(dict(node=at,arrival_ps=value,required_ps=required,slack_ps=slack))
        stages.append(dict(index=cut['index'],timing_violation_ps=violation,captures=endpoints));worst=max(worst,violation)
    slots=state['slots'];native=[s for s in slots if not s['external_capture']];external=[s for s in slots if s['external_capture']]
    nb=sum(s['variable_bits'] for s in native);eb=sum(s['variable_bits'] for s in external)
    owners=dict(operators=area,input_service=.2*state['input_variable_bits'],native_state=.2*nb+.03*len(native),
        external_state=.18*eb+.02*len(external),shared_clock=.3+.005*(nb+eb),shared_physical=.1,root_repair=.05)
    return sum(owners.values()),worst,owners,stages


def verify(out,input_folder=None):
    global CANDIDATE
    inputs=input_folder or out/'input'
    CANDIDATE=read(inputs/'fixture.json');request=read(inputs/'request.json');data=read(out/'native/consumer.json')
    graphs={g['candidate']:g for g in request['candidates']};total=0;selected=[]
    for run in data['runs']:
        target=run['target_period_ps'];prices=[]
        if run['formal_D_selection'] or not run['coverage_complete'] or run['candidate_PPA_calls']:raise ValueError('wrong qualification')
        for row in run['candidates']:
            graph=graphs[row['candidate']];view=next(v for v in graph['views'] if v['placement']==row['placement'])
            expected=operator_query.queries(graph,view,target,CANDIDATE['profile_sha256'],CANDIDATE['operator_boundary_policy'])
            if {q['trace']['node']:q['descriptor'] for q in expected}!={q['node']:q['descriptor'] for q in row['node_prices']}:
                raise ValueError('native model consumed a different real Query')
            total+=len(row['node_prices'])
            state=row['state_query']
            if not state['materialized_checked'] or state['layout_sha256']!=view['state']['query']['layout_sha256']:raise ValueError('wrong actual state projection')
            area,violation,owners,stages=score(graph,view,row['node_prices'],target,state)
            close(area,row['total_area_um2']);close(violation,row['timing_violation_ps'])
            for k,v in owners.items():close(v,row['owner_area_um2'][k])
            for a,b in zip(stages,row['stages'],strict=True):
                if a['index']!=b['index']:raise ValueError('stage mismatch')
                close(a['timing_violation_ps'],b['timing_violation_ps'])
                for x,y in zip(a['captures'],b['captures'],strict=True):
                    if x['node']!=y['node']:raise ValueError('capture mismatch')
                    for k in ('arrival_ps','required_ps','slack_ps'):close(x[k],y[k])
            prices.append((row['view'],area,violation))
        feasible=any(v==0 for _,_,v in prices)
        winner=min((0 if feasible and v==0 else math.inf if feasible else v,a,name) for name,a,v in prices)
        if winner[2]!=run['selected_view']:raise ValueError('finite view selection differs')
        if sha(out/'native'/run['rtl_file'])!=run['rtl_sha256']:raise ValueError('selected RTL differs')
        selected.append(dict(target_ps=target,view=winner[2],area_um2=winner[1],violation_ps=winner[0],status=run['selection_status']))
    statuses={r['status'] for r in selected}
    if not {'TEST_ONLY_predicted_feasible_selected','TEST_ONLY_target_unmet'}<=statuses:raise ValueError('feasible/fallback paths missing')
    if total!=data['query_count'] or data['views']!=44:raise ValueError('query/view inventory incomplete')
    partial=read(out/'native/partial-coverage.json')
    if partial['coverage_complete'] or 'selected_view' in partial:raise ValueError('partial coverage produced selection')
    write(out/'proof.json',dict(status='passed',mode='TEST_ONLY',views=data['views'],targets=len(data['runs']),query_count=total,
        selections=selected,negative_checks=data['negative_checks'],actual_state_and_node_Query_checked=True,
        independent_Python_DAG_ownership_and_selection_checked=True,physical_labels_read=False,new_EDA_calls=0,full_D_ready=False))
    print(read(out/'proof.json'),flush=True)


def cycles(out):
    data=read(out/'native/consumer.json');parts=[];decl=[];checks=[]
    for i,run in enumerate(data['runs']):
        raw=(out/'native'/run['rtl_file']).read_text();names=re.findall(r'\bmodule\s+([A-Za-z_][A-Za-z_0-9]*)',raw)
        rename={name:'ConditionView'+str(i)+('' if j==0 else '__child'+str(j)) for j,name in enumerate(names)}
        raw=re.sub(r'\b(?:'+'|'.join(re.escape(n) for n in sorted(names,key=len,reverse=True))+r')\b',lambda m:rename[m[0]],raw);parts.append(raw)
        decl.append(f'wire [63:0] y{i};wire ov{i};ConditionView{i} d{i}(.clk(clk),.rstn(rstn),.__vul_port_a(a),.__vul_port_b(b),.__vul_port_c(c),.__vul_port_iv(iv),.__vul_port_ov(ov{i}),.__vul_port_y(y{i}));')
        checks.append(f'if(ov{i}!==expected_valid)$fatal(1,"valid selection{i} row%0d",j);if(expected_valid&&y{i}!==expected)$fatal(1,"data selection{i} row%0d",j);')
    rng=random.Random(20261110);vectors=[]
    for i in range(160):
        a,b=rng.getrandbits(32),rng.getrandbits(32);c=rng.getrandbits(64);word=a
        for v,w in ((b,32),(c,64),(int(i not in (0,1,70,71)),1),(int(i%5 not in (1,3)),1),((a*b+c)&((1<<64)-1),64)):word=(word<<w)|v
        vectors.append(format(word,'x'))
    (out/'cycles.hex').write_text('\n'.join(vectors)+'\n');(out/'cycles.sv').write_text('\n'.join(parts))
    tb='module ConditionTb;reg clk=0,rstn,iv;reg [31:0] a,b;reg [63:0] c,expected;reg expected_valid;integer j;reg [193:0] rows[0:159];\n'+'\n'.join(decl)
    tb+='\ninitial begin $readmemh("'+str(out/'cycles.hex')+'",rows);for(j=0;j<160;j=j+1)begin clk=0;{a,b,c,rstn,iv,expected}=rows[j];expected_valid=rstn&&iv;#5;clk=1;#1;\n'+'\n'.join(checks)+'\n#4;end $display("CONDITIONAL_SELECTED_RTL_PASS selections=3 cycles=160");$finish;end endmodule\n'
    (out/'cycles-tb.sv').write_text(tb);print('selected RTL vectors prepared',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','verify','cycles'));p.add_argument('--out',type=Path,required=True);p.add_argument('--input',type=Path);a=p.parse_args()
    if a.action=='verify':verify(a.out.resolve(),a.input.resolve() if a.input else None)
    else:{'prepare':prepare,'cycles':cycles}[a.action](a.out.resolve())
