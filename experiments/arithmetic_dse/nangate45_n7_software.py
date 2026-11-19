"""Finite frozen-D search at A-derived clocks using the N56 function package."""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile

from . import nangate45_n7 as app
from .nangate45_pipeline_runtime import load_package
from .nangate45_pipeline_check import numerical_guard
from .workload_demand import Graph
from .workload_abcd import static_score
from .workload_contracts import load
from .workload_final_software import record, balanced, BINARY
from .workload_software_validation import bench
from .workload_equivalent import score_key
from .workload_equivalent_run import compact_prediction
from .workload_platform_entry import native_export
from .workload_dot16_latency import depth_schedule


def compressed(path,value):
    app.write(Path(path).with_suffix('.pending.json'),dict(status='writing_trace'))
    Path(path).write_bytes(gzip.compress(json.dumps(value,separators=(',',':')).encode(),mtime=0))
    Path(path).with_suffix('.pending.json').unlink()


def copy_selected(root,case,L,T,method,row,prediction,result=None):
    root=Path(root);out=root/'selected'/case/f'T{T}-L{L}'/method
    if (out/'selection.json').exists():return app.read(out/'selection.json')
    out.mkdir(parents=True,exist_ok=True)
    src=Path(row['folder']);g,v,state,owners=app.metadata(row,T)
    shutil.copyfile(src/'workload.sv',out/'workload.sv')
    app.write(out/'graph.json',app.read(row['graph']));app.write(out/'state.json',state);app.write(out/'owners.json',owners)
    app.write(out/'view.json',dict(placement=row['placement'],artifact=row['artifact']))
    protocol=root/'protocol.json'
    if protocol.exists():source=Path(app.read(protocol)['pools'][f'{case}-L{app.SCOPE[case][0]}']['source'])
    else:source=app.software_root(case,app.SCOPE[case][0])/case/'source'
    text,checks=bench(app.read(source/'semantics.json'),row['artifact'],L,cycles=192)
    (out/'tb.sv').write_text(text)
    with tempfile.TemporaryDirectory(prefix='nangate45-N7-sim-') as tmp:
        sim=Path(tmp)/'sim'
        for command,name in [(['iverilog','-g2012','-s','tb','-o',str(sim),str(out/'workload.sv'),str(out/'tb.sv')],'iverilog.log'),(['vvp',str(sim)],'simulation.log')]:
            with (out/name).open('w') as log:subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
    assert 'PASS' in (out/'simulation.log').read_text()
    receipt=dict(status='passed',rtl_sha256=app.sha(out/'workload.sv'),testbench_sha256=app.sha(out/'tb.sv'),
        log_sha256=app.sha(out/'simulation.log'),cycles=192,integer_cycle_checks=checks,L=L,II=1,additional_input_service_cycles=1)
    app.write(out/'functional-receipt.json',receipt)
    selected=dict(case=case,L=L,T_clk_ps=T,II=1,method=method,rtl=str(out/'workload.sv'),rtl_sha256=receipt['rtl_sha256'],
        simulation_status='passed',simulation_receipt=str(out/'functional-receipt.json'),selection_file=str(out/'selection.json'),
        placement=row['placement'],grammar=row.get('grammar'),source_implementation=row,
        platform='nangate45',profile_sha256=app.profile('nangate45')['profile_sha256'],model_package_sha256=app.sha(app.PACKAGE),
        prediction=compact_prediction(prediction) if prediction else None,qualification='diagnostic_only',
        application_PPA_for_selection=False,reused_ASAP7_RTL=method in 'ABC',
        active_arithmetic_stages=sorted({row['placement'][r['node']] for r in (prediction or {}).get('owners',[]) if r['delay_ps']>0 or r['area_um2']>0}))
    if result:
        compressed(out/'complete-budget-trace.json.gz',result)
        entry=result['trace'][int(result['best_variant_id'].split(':')[0])]
        best=next(r for r in entry['variants'] if r['id']==result['best_variant_id'])
        app.write(out/'equivalent-requests.json',dict(T_clk_ps=T,budgets_ps=entry['budgets_ps'],actual_queries=best['actual_queries'],
            model_package_sha256=selected['model_package_sha256'],requested_budget_window_feasible=result.get('requested_budget_window_feasible',True)))
        selected.update(budget_trace_sha256=app.sha(out/'complete-budget-trace.json.gz'),queries_sha256=app.sha(out/'equivalent-requests.json'))
    app.write(out/'selection.json',selected)
    Graph.origins.cache_clear();Graph.roots.cache_clear()
    return selected


def candidate_pool(root,case,L,T,rt,pool):
    root=Path(root);work=root/'software'/f'{case}-L{L}'/f'T{T}'
    work.mkdir(parents=True,exist_ok=True)
    candidates=[];seen=set();grammar=[list(r) for r in pool['grammar']]
    def add(row):
        if row['rtl_sha256'] not in seen:
            candidates.append(row);seen.add(row['rtl_sha256'])
    rows=list(pool['candidates'])
    if case=='mac32' and L==3:
        extra=app.ROOT.parent/'vulsim-artifacts/workload-equivalent-steps45-v1/search/native'
        for path in sorted(extra.glob('*/inventory.json')):
            inv=app.read(path)
            if inv['L']!=L:continue
            pair=[inv['mul_block_width'],0]
            if pair not in grammar:grammar.append(pair)
            number=grammar.index(pair)
            for view in inv['views']:
                r=record(path.parent,view,number,L,'frozen_MAC_L3_prospective_view');r['grammar']=pair;rows.append(r)
    source=Path(app.read(root/'protocol.json')['pools'][f'{case}-L{L}']['source'])/'request.json'
    for number,(block,limb) in enumerate(grammar):
        available=[r for r in rows if r['structure']==number]
        if not available:raise ValueError('registered grammar lacks a prospective view')
        # The same static seeds and two pressure-balanced placements as the
        # frozen selector. MAC L3 also keeps its pre-existing finite views.
        static_balanced=[r for r in available if r['origin']=='balanced_static']
        chosen=[min(available,key=static_score),min(available,key=lambda r:(r['static']['saved_bits'],static_score(r))),
            min(static_balanced or available,key=static_score)]
        for r in (available if case=='mac32' and L==3 else chosen):add(r)
        g,v,s,o=app.metadata(chosen[0],T)
        with numerical_guard():p=rt.evaluate(g,v,s,o)
        members={r['root']:r['members'] for r in o['G_regions']};weights={}
        for owner in p['owners']:
            nodes=members.get(owner['node'],[owner['node']])
            for n in nodes:weights[n]=owner['delay_ps']/len(nodes)
        native=work/f'beam-b{block}-w{limb}'
        if not (native/'inventory.json').exists():native_export(BINARY,source,native,platform='nangate45',L=L,limb=limb,block=block,target_ps=T)
        raw=app.read(native/'graph.json');units=app.read(native/'scheduling-units.json')['units']
        placements=balanced(raw,units,L,weights)[:2]
        pressure=work/f'pressure-b{block}-w{limb}'
        if not (pressure/'inventory.json').exists():
            request=work/f'placements-b{block}-w{limb}.json'
            app.write(request,dict(version='workload-explicit-schedules-v1',L=L,T_clk_ps=T,graph_export_sha256=app.sha(native/'graph.json'),placements=placements))
            native_export(BINARY,source,pressure,platform='nangate45',L=L,limb=limb,block=block,target_ps=T,placements=request)
        for view in app.read(pressure/'inventory.json')['views']:
            r=record(pressure,view,number,L,'model_pressure_balanced');r['grammar']=[block,limb];add(r)
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    for method in ('B','C'):add(pool[method])
    app.frozen(work/'candidate-pool.json',dict(case=case,L=L,T_ps=T,candidates=candidates,grammar=grammar,
        candidate_PPA_calls=0,same_pool_for_D_and_static_attribution=True,model_package_sha256=app.sha(app.PACKAGE)))
    return work,candidates


def select(root,case,L):
    root=Path(root);doc=app.verify(root);out=root/'software'/f'{case}-L{L}';out.mkdir(parents=True,exist_ok=True)
    target=app.read(root/'targets'/f'{case}-L{L}.json');pool=app.read(doc['pools'][f'{case}-L{L}']['path'])
    rt=load_package(app.PACKAGE);records=[]
    app.write(out/'software-status.json',dict(status='running',started_at=app.now(),targets_ps=target['targets_ps']))
    for T in target['targets_ps']:
        # Reused B/C can enter the backend before the D search completes.
        bc=[]
        for method in ('B','C'):
            row=pool[method];g,v,s,o=app.metadata(row,T)
            with numerical_guard():prediction=rt.evaluate(g,v,s,o)
            bc.append(copy_selected(root,case,L,T,method,row,prediction))
        app.admit(root,case,L,T,bc)
        work,candidates=candidate_pool(root,case,L,T,rt,pool)
        scored=[]
        for index,row in enumerate(candidates):
            ident=hashlib.sha256(json.dumps(dict(rtl=row['rtl_sha256'],T=T,model=doc['package_sha256']),sort_keys=True).encode()).hexdigest()
            trace=work/(ident+'.json.gz')
            if trace.exists():item=json.loads(gzip.decompress(trace.read_bytes()))
            else:
                g,v,s,o=app.metadata(row,T)
                with numerical_guard():
                    result=rt.optimize(g,v,s,o)
                    static=rt.evaluate(g,v,s,o,static_cal=True)
                item=dict(id=ident,row=row,model=result['prediction'],static=static,result=result)
                compressed(trace,item)
            scored.append(dict(id=ident,row=row,model=item['model'],static=item['static'],trace=str(trace),
                complete_variants=item['result']['complete_variants']))
            app.write(out/'software-status.json',dict(status='running',L=L,T_ps=T,candidate=index+1,candidates=len(candidates),at=app.now()))
            print(f'N7_SCORE {case} L{L} T{T} {index+1}/{len(candidates)}',flush=True)
            del item
            Graph.origins.cache_clear();Graph.roots.cache_clear()
        valid=[r for r in scored if r['model'] is not None]
        if not valid:raise ValueError('all candidates lack a complete Nangate45 price')
        winner=min(valid,key=lambda r:score_key(r['model'])+(r['id'],))
        control=min(scored,key=lambda r:score_key(r['static'])+(r['id'],))
        result=json.loads(gzip.decompress(Path(winner['trace']).read_bytes()))['result']
        d=copy_selected(root,case,L,T,'D',winner['row'],winner['model'],result)
        static=copy_selected(root,case,L,T,'same_policy_static',control['row'],control['static'])
        app.admit(root,case,L,T,[d])
        compressed(work/'pool-summary.json.gz',[dict(id=r['id'],rtl_sha256=r['row']['rtl_sha256'],model=compact_prediction(r['model']) if r['model'] else None,
            static=compact_prediction(r['static']),complete_variants=r['complete_variants']) for r in scored])
        records.append(dict(case=case,L=L,T_ps=T,methods={**{s['method']:s for s in bc},'D':d,'same_policy_static':static},
            candidates=len(candidates),complete=len(valid),selected_id=winner['id'],static_id=control['id'],candidate_PPA_calls=0))
        app.write(out/'selections.json',dict(records=records,model_package_sha256=doc['package_sha256'],candidate_PPA_calls=0))
    app.write(out/'software-status.json',dict(status='ready',finished_at=app.now(),targets_ps=target['targets_ps'],records=records))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=app.DEFAULT);p.add_argument('--case',required=True);p.add_argument('--L',type=int,required=True);a=p.parse_args()
    try:select(a.root,a.case,a.L)
    except Exception as error:
        app.write(a.root/'software'/f'{a.case}-L{a.L}'/'software-status.json',dict(status='error',reason=str(error),at=app.now()))
        raise
