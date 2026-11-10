"""Native OperatorQuery/explicit-placement software acceptance, accounted leaves."""
import argparse
from copy import deepcopy
import gzip
import json
import math
import os
from pathlib import Path
import random
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse import operator_query as query

GRAPH_SOURCE=ROOT/'experiments/arithmetic/evidence/step7_fast_loads_v1/static-graphs.json.gz'
SOURCE_LIST=ROOT/'build/step7-d-requirements-20261105/audit-v3/cases.json'


def prepare(out):
    out.mkdir(parents=True,exist_ok=False);graphs=json.loads(gzip.decompress(GRAPH_SOURCE.read_bytes()))
    if len({g['case'] for g in graphs})!=1:raise ValueError('one explicit pilot source required')
    name=graphs[0]['case'];source=deepcopy(next(c for c in read(SOURCE_LIST)['cases'] if c['name']==name))
    if sha(source['source'])!=source['generated_source_sha256']:raise ValueError('public source hash differs')
    shutil.copy2(source['source'],out/'source.cpp');source['source']=str(out/'source.cpp')
    manifest=dict(mode='TEST_ONLY',source=source,candidates=graphs,targets_ps=[50,150,1500],
                  physical_labels_read=False,production_binding_implemented=False,full_D_ready=False)
    write(out/'request.json',manifest)
    print('prepared actual-source/typed-graphs and three TEST_ONLY target contexts',flush=True)


def score(export,view,queries,target):
    nodes={n['id']:n for n in export['nodes']};placement=view['placement'];costs={};area=0
    for row in queries:
        price=query.fixture_predict(row['descriptor']);costs[row['trace']['node']]=price['delay_ps'];area+=price['comb_area_um2']
    arrivals={}
    def arrival(at):
        if at not in arrivals:
            n=nodes[at]
            arrivals[at]=0 if n['constant'] or n['operation']=='input' else max((arrival(a['node']) for a in n['operands'] if a['kind']=='symbol' and placement[a['node']]==placement[at]),default=0)+costs.get(at,0)
        return arrivals[at]
    stages=[];maximum=violation=0
    for cut in view['stages']:
        delay=max((arrival(c['value']) for c in cut['captures']),default=0);io=.2*target if cut['index']==0 else 0
        slack=target-io-40-delay;violation=max(violation,-slack);maximum=max(maximum,delay+40)
        stages.append(dict(index=cut['index'],comb_delay_ps=delay,fixture_boundary_ps=40,fixture_IO_ps=io,slack_ps=slack))
    q=view['state']['query'];slots=q['slots']
    native=[s for s in slots if not s['external_capture']];external=[s for s in slots if s['external_capture']]
    nb=sum(s['variable_bits'] for s in native);eb=sum(s['variable_bits'] for s in external)
    owners=dict(operators=area,input_service=.2*q['input_variable_bits'],native_state=.2*nb+.03*len(native),
                external_state=.18*eb+.02*len(external),shared_clock_physical_repair=.4+.005*(nb+eb))
    return dict(total_area_um2=sum(owners.values()),timing_violation_ps=max(0,violation),maximum_fixture_delay_ps=maximum,
                owner_area_um2=owners,stages=stages)


def compare(a,b,label):
    if isinstance(a,dict):
        if set(a)!=set(b):raise ValueError(label+' keys differ: '+str(set(a)^set(b)))
        for k,v in a.items():compare(v,b[k],label+'/'+k)
    elif isinstance(a,list):
        if len(a)!=len(b):raise ValueError(label+' length differs')
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,label+'/'+str(i))
    elif type(a) in (float,int) and type(b) in (float,int):
        if not math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-9):raise ValueError(label+' numerical mismatch '+str((a,b)))
    elif a!=b:raise ValueError(label+' value mismatch '+str((a,b)))


def verify(out):
    requested=read(out/'input/request.json');native=read(out/'native/queries.json');by_candidate={g['candidate']:g for g in requested['candidates']};total=0;all_scores={t:[] for t in requested['targets_ps']};nfeatures=set()
    for variant in native['variants']:
        graph=by_candidate[variant['candidate']];view=next(v for v in graph['views'] if v['placement']==variant['placement'])
        state=variant['materialized_state_query'];old=view['state']['query']
        if state['layout_sha256']!=old['layout_sha256'] or not state['materialized_checked']:raise ValueError('actual materialized state layout differs')
        if sha(out/'native'/variant['rtl_file'])!=variant['rtl_sha256']:raise ValueError('emitted RTL identity mismatch')
        for target in variant['target_rows']:
            t=target['target_ps'];first=target['queries'][0]['descriptor']['flow_context'];rows=query.queries(graph,view,t,first['profile_sha256'],first['boundary_policy'])
            compare(rows,target['queries'],'native_vs_Python_queries');total+=len(rows)
            for row in rows:
                nfeatures.update(row['features'])
                if query.fixture_predict(row['descriptor'],production=True)['status']!='cost_uncovered':raise ValueError('test fixture entered production')
            predicted=score(graph,view,rows,t)
            for key,value in predicted.items():compare(value,target['score'][key],'DAG_state_'+key)
            all_scores[t].append((predicted,target['score']['register_bits'],variant['id']))
    for selected in native['selections']:
        t=selected['target_ps'];scores=all_scores[t];feasible=any(v[0]['timing_violation_ps']==0 for v in scores)
        def ranking(item):
            index,(s,reg,name)=item
            return (0 if feasible and s['timing_violation_ps']==0 else 1 if feasible else s['timing_violation_ps'],s['total_area_um2'],s['maximum_fixture_delay_ps'],reg,index)
        chosen=min(enumerate(scores),key=ranking)[0]
        if chosen!=selected['selected_view']:raise ValueError('native finite selection differs from independent Python ranking')
        if selected['formal_D_selection'] or not selected['selection_status'].startswith('TEST_ONLY'):raise ValueError('fixture selection falsely production-qualified')
    if len(native['variants'])!=44 or total!=native['query_count']:raise ValueError('incomplete pilot view/query count')
    if not any(s['selection_status']=='TEST_ONLY_target_unmet' for s in native['selections']):raise ValueError('fallback path unexercised')
    if not any(s['selection_status']=='TEST_ONLY_predicted_feasible_selected' for s in native['selections']):raise ValueError('feasible path unexercised')
    example=deepcopy(native['variants'][0]['target_rows'][0]['queries'][0]['descriptor']);rejected=[]
    changes=[('posterior_input',lambda q:q.update(data_setup_slack_ps=0)),('unknown_semantics',lambda q:q.update(semantics='signed')),
        ('bad_target_relation',lambda q:q['flow_context'].update(abc_target_ps=123)),('unknown_boundary',lambda q:q['flow_context'].update(boundary_policy='')),
        ('bad_result_demand',lambda q:q.update(required_result_bits=[])),('conflicting_mask',lambda q:q['local_context']['producer'].update(lhs_zero_hex='1',lhs_one_hex='1'))]
    for name,change in changes:
        item=deepcopy(example);change(item)
        try:query.features(item)
        except ValueError:rejected.append(name)
        else:raise ValueError('invalid query accepted '+name)
    if native['negative_query_rejections']!=rejected:raise ValueError('native and Python invalid-query rejection differs')
    write(out/'query-proof.json',dict(status='passed',native_Python_query_count=total,feature_count=len(nfeatures),views=44,targets=requested['targets_ps'],
        true_native_source_recompiled=True,actual_register_maps_materialized=44,negative_queries=rejected,native_invalid_map_rejections=native['invalid_map_rejections'],
        selections=[dict(target=s['target_ps'],view=s['selected_view'],status=s['selection_status']) for s in native['selections']],
        physical_qualification=False,full_D_ready=False,candidate_PPA_calls=0))
    print(json.dumps(read(out/'query-proof.json')),flush=True)


def cycle_prepare(out):
    data=read(out/'native/queries.json');parts=[];decl=[];assign=[];checks=[];inits=[];rng=random.Random(20261110);cycles=160
    for i,variant in enumerate(data['variants']):
        raw=(out/'native'/variant['rtl_file']).read_text();match=re.search(r'\bmodule\s+([A-Za-z_][A-Za-z_0-9]*)',raw)
        if not match:raise ValueError('native kernel missing')
        names=re.findall(r'\bmodule\s+([A-Za-z_][A-Za-z_0-9]*)',raw)
        renamed={name:('QueryView'+str(i) if j==0 else 'QueryView'+str(i)+'__child'+str(j)) for j,name in enumerate(names)}
        if len(renamed)!=len(names):raise ValueError('duplicate module definition')
        raw=re.sub(r'\b(?:'+'|'.join(re.escape(name) for name in sorted(names,key=len,reverse=True))+r')\b',lambda m:renamed[m[0]],raw);parts.append(raw)
        decl.append(f'wire [63:0] y{i};wire ov{i};QueryView{i} d{i}(.clk(clk),.rstn(rstn),.__vul_port_a(a),.__vul_port_b(b),.__vul_port_c(c),.__vul_port_iv(iv),.__vul_port_ov(ov{i}),.__vul_port_y(y{i}));')
        # One internal boundary, no service state inside this direct kernel TB.
        checks.append(f'if(ov{i}!==expected_valid)$fatal(1,"valid view{i} row%0d",j);if(expected_valid && y{i}!==expected)$fatal(1,"data view{i} row%0d",j);')
    # Python computes arithmetic values independently; SV scoreboard handles
    # N=1 validity and asynchronous observation of native nonblocking updates.
    vectors=[]
    for i in range(cycles):
        a,b=rng.getrandbits(32),rng.getrandbits(32);c=rng.getrandbits(64);rst=int(i not in (0,1,70,71));iv=int(i%5 not in (1,3));want=(a*b+c)&((1<<64)-1)
        word=a
        for v,w in ((b,32),(c,64),(rst,1),(iv,1),(want,64)):word=(word<<w)|v
        vectors.append(format(word,'x'))
    (out/'cycles.hex').write_text('\n'.join(vectors)+'\n');(out/'cycles.sv').write_text('\n'.join(parts))
    # For N=1 the transaction present before a rising edge appears after that
    # edge. Reset flushes valid; outputs on invalid cycles are not compared.
    tb='module QueryTb;reg clk=0,rstn,iv;reg [31:0] a,b;reg [63:0] c,expected;reg expected_valid;integer j;reg [193:0] rows[0:159];\n'+'\n'.join(decl)
    tb+='\ninitial begin $readmemh("'+str(out/'cycles.hex')+'",rows);for(j=0;j<160;j=j+1)begin clk=0;{a,b,c,rstn,iv,expected}=rows[j];expected_valid=rstn&&iv;#5;clk=1;#1;\n'+'\n'.join(checks)+'\n#4;end $display("QUERY_ALL_VIEWS_RTL_PASS views=44 cycles=160");$finish;end endmodule\n'
    (out/'cycles-tb.sv').write_text(tb)
    print('prepared actual materialized 44-view RTL comparison',flush=True)


def run(out,build):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);records=[];ctx=dict(target_platform='asap7',admission_id=out.name,task_id='operator-query-software')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
    source_paths=[Path(__file__),Path(query.__file__),ROOT/'rtlzz/src/backend/pipeline.cpp',ROOT/'rtlzz/src/backend/pipeline.hpp',
                  ROOT/'rtlzz/src/backend/arithmetic_operator_query.cpp',ROOT/'rtlzz/src/backend/arithmetic_operator_query.hpp',ROOT/'rtlzz/testv2/arithmetic_operator_query_export.cpp',
                  ROOT/'rtlzz/src/backend/rtlgen.cpp',ROOT/'rtlzz/src/backend/rtlgen.hpp']
    for p in source_paths:
        dest=out/'source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    write(out/'source-freeze.json',{str(p.relative_to(ROOT)):sha(p) for p in source_paths})
    try:
        with ledger.job(ctx):
            def leaf(command,name,timeout):
                r=ledger.reserve(None,timeout,4,'operator_query_software',command,out/name,context=ctx)
                record=run_command(command,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record);records.append(dict(**record,budget_reservation_id=r['id']));write(out/'commands.json',records)
                print(name+': '+Path(record['log']).read_text()[-1800:],flush=True)
                if record['exit_code']:raise RuntimeError('paid leaf failed, evidence preserved: '+record['log'])
            leaf([sys.executable,'-B',str(Path(__file__)),'prepare','--out',str(out/'input')],'prepare',120)
            leaf(['cmake','-S',str(ROOT/'rtlzz'),'-B',str(build)],'configure',180)
            leaf(['cmake','--build',str(build),'--target','arithmetic-operator-query-export','-j4'],'native-build',900)
            leaf([str(build/'testv2/arithmetic-operator-query-export'),str(ROOT),str(out/'input/request.json'),str(out/'native'),'--preserve-arithmetic-boundaries'],'native',300)
            leaf([sys.executable,'-B',str(Path(__file__)),'verify','--out',str(out)],'parity',180)
            leaf([sys.executable,'-B',str(Path(__file__)),'cycle-prepare','--out',str(out)],'cycle-prepare',120)
            leaf(['verilator','--binary','--timing','--top-module','QueryTb','--Mdir',str(out/'obj'),'-j','4',str(out/'cycles.sv'),str(out/'cycles-tb.sv')],'verilator',600)
            leaf([str(out/'obj/VQueryTb')],'simulate',120)
    finally:
        after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','prepare','verify','cycle-prepare'));p.add_argument('--out',type=Path,required=True);p.add_argument('--build',type=Path,default=ROOT/'build/step4-rtlzz');args=p.parse_args()
    if args.action=='run':run(args.out.resolve(),args.build.resolve())
    elif args.action=='cycle-prepare':cycle_prepare(args.out.resolve())
    else:globals()[args.action](args.out.resolve())
