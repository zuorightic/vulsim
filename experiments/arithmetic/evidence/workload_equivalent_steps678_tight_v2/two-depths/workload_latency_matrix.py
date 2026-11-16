"""Two declared pipeline depths per workload; finite software-only selection.

The original depths keep their frozen selections. The shallower depths get
fresh native graphs/schedules, joint body budgets and equivalent-T queries.
Dot16 uses its requested L4/L5 successor instead of the padded L8 experiment.
All model parameters remain frozen. Applications never provide price labels.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
from unittest.mock import patch

from .sampling_time_contract import ROOT,canonical
from .workload_abcd import read,write,sha,static_node,static_score
from .workload_contracts import load
from .workload_demand import Graph
from .workload_final_software import export,record,simulate,balanced,BINARY
from .workload_final_selection import metadata,export_selected,BASE
from .workload_final_prices import CachedPrices
from .workload_tight_equivalent import optimize
from .workload_equivalent import score_key
from .workload_diagnostic import evaluate
from .workload_equivalent_run import compressed,compact_prediction
from .workload_dot16_latency import frozen,depth_schedule,active_stages
from .workload_tight_run import DEFAULT as PARENT
from .workload_nine_runtime import DEFAULT

SOURCE=Path(__file__).resolve()
VERSION='nine-workloads-two-pipeline-depths-v1'
DEPTHS=dict(mac32=[2,3],add512=[2,4],mul128=[2,4],dot16=[4,5],
    horner64=[4,8],barrett64=[4,8],karatsuba256=[4,8],montgomery256=[16,32],ntt8x64=[8,16])
DOT=ROOT.parent/'vulsim-artifacts/workload-equivalent-dot16-L45-v1'


def target_pair(A,L):
    values=[math.ceil(f*A/L/50)*50 for f in (1.25,1.5)]
    values[1]=max(values[1],values[0]+50)
    if not all(0<T<A for T in values):
        raise ValueError('derived target does not improve on A')
    return values


def initialize(root=DEFAULT):
    root=Path(root).resolve(); root.mkdir(parents=True,exist_ok=True)
    doc=dict(version=VERSION,depths=DEPTHS,required_groups=37,required_main_records=148,
        required_attribution_records=37,MAC32_original_targets_ps=[500,750,1000],
        shallow_clock_rule='ceil50(factor * frozen measured A / L); factors 1.25,1.5',
        MAC32_reference='existing unsplit A at the largest original request (1000ps); fixed selection rule',
        Dot16='L4/L5 only in the new matrix; L8 records retained as historical evidence',
        sources_and_models_unchanged=True,model_refitted=False,application_PPA_for_selection=False,
        original_selection_reused=True,original_measurement_threads_reported=True,
        new_physical_parallel_jobs=9,new_threads_per_tool=2,
        source_sha256=sha(SOURCE),compiler_sha256=sha(BINARY),
        model_sha256=sha(BASE/'diagnostic-model.json'),
        common_contract_sha256=sha(PARENT/'software/characterization-contract.json'),
        new_MAC32_grammar=[[0,0],[4,0],[8,0],[16,0],[12,0]],
        structure_cap=16,additional_stage_counts_per_case=1,
        no_post_PPA_selection_or_clock_relaxation=True,qualification='diagnostic_only')
    frozen(root/'protocol.json',doc)
    rows=[]
    for cid,depths in DEPTHS.items():
        for L in depths:
            path=root/'targets'/f'{cid}-L{L}.json'
            if cid=='dot16':
                old=read(DOT/f'L{L}/targets/dot16.json')
                value=dict(old,role='existing_Dot16_L4_L5_frozen_targets')
            elif cid=='mac32' and L==3:
                value=dict(case=cid,L=L,targets_ps=[500,750,1000],role='original_confirmed_requests')
            elif cid=='montgomery256':
                # A successful capacity successor will freeze both depths.
                if not path.exists():
                    rows.append(dict(case=cid,L=L,status='awaiting_measured_A_reference')); continue
                value=read(path)
            else:
                original_L=next(c for c in load()['cases'] if c['id']==cid)['formal_targets'][0]['L']
                if L==original_L:
                    value=dict(read(PARENT/'targets'/(cid+'.json')),role='original_frozen_targets')
                else:
                    if cid=='mac32':
                        selection=read(PARENT/'final-mac32-methods.json')
                        record_a=max(selection['records'],key=lambda r:r['target']['T_ps'])
                        method=record_a['methods']['A']
                        p=PARENT/'final-mac32/runs'/method['task_id']/'clock-readout/result.json'
                        A=read(p)['full_setup_minimum_period_ps']
                    else:
                        p=PARENT/'A-reference/runs'/(cid+'-A-reference')/'clock-readout/result.json'
                        A=read(p)['full_setup_minimum_period_ps']
                    value=dict(case=cid,L=L,targets_ps=target_pair(A,L),A_reference_Tmin_ps=A,
                        reference_readout=str(p),clock_readout_sha256=sha(p),factors=[1.25,1.5],quantum_ps=50,
                        role='shallower_depth_clock_calibration_only',application_PPA_for_model=False)
            frozen(path,value); rows.append(dict(value,status='frozen'))
    write(root/'target-matrix.json',dict(version=VERSION,rows=rows,required_groups=37,
        frozen_groups=sum(len(r.get('targets_ps',[])) for r in rows),
        required_main_records=148,exactly_two_depths_per_case=True))
    return doc


def freeze_montgomery(root,run):
    readout=run/'clock-readout/result.json'; proof=run/'verification-receipt.json'
    if not readout.exists() or not proof.exists() or read(proof)['status']!='proven':
        return False
    A=read(readout)['full_setup_minimum_period_ps']
    for L in DEPTHS['montgomery256']:
        value=dict(case='montgomery256',L=L,targets_ps=target_pair(A,L),A_reference_Tmin_ps=A,
            reference_readout=str(readout),clock_readout_sha256=sha(readout),
            verification_receipt_sha256=sha(proof),factors=[1.25,1.5],quantum_ps=50,
            role='A_clock_calibration_only',predecessor_failures_retained=True,application_PPA_for_model=False)
        frozen(root/'targets'/f'montgomery256-L{L}.json',value)
    initialize(root); return True


def variant_root(root,cid,L):
    return DOT/f'L{L}' if cid=='dot16' else root/'variants'/cid/f'L{L}'


def original_selection(cid,L):
    if cid=='dot16':
        return None
    original_L=next(c for c in load()['cases'] if c['id']==cid)['formal_targets'][0]['L']
    p=PARENT/'software'/cid/'final-selections.json'
    return p if L==original_L and p.exists() else None


def ready_selection(root,cid,L):
    old=original_selection(cid,L)
    if old:
        return old
    variant=variant_root(root,cid,L)
    receipt=variant/'matrix-software-ready.json'
    if receipt.exists() and read(receipt)['status']=='passed':
        return variant/'software'/cid/'final-selections.json'
    return None


def prepare(root,cid,L):
    target=read(root/'targets'/f'{cid}-L{L}.json'); variant=variant_root(root,cid,L)
    soft=variant/'software'; soft.mkdir(parents=True,exist_ok=True)
    for name in ('bindings.json','characterization-contract.json'):
        src=PARENT/'software'/name; dest=soft/name
        if dest.exists() and sha(dest)!=sha(src):
            raise ValueError('copied common input changed')
        if not dest.exists():
            shutil.copyfile(src,dest)
    frozen(soft/'protocol.json',dict(read(root/'protocol.json'),case=cid,L=L,target=target))
    dest=soft/cid/'source'
    if not dest.exists():
        shutil.copytree(PARENT/'software'/cid/'source',dest)
    pool=soft/cid/'static-pool.json'
    if pool.exists():
        return soft
    case=next(c for c in load()['cases'] if c['id']==cid)
    grammar=(read(root/'protocol.json')['new_MAC32_grammar'] if cid=='mac32'
             else read(PARENT/'software'/cid/'static-pool.json')['grammar'])
    if not 1<=len(grammar)<=16 or grammar[0]!=[0,0]:
        raise ValueError('finite shared grammar with original structure first required')
    T=target['targets_ps'][0]; rows=[]
    for number,(block,limb) in enumerate(grammar):
        native=export(soft,case,block,limb,T,L); raw=read(native/'graph.json'); graph=Graph(raw)
        weights={n['id']:static_node(graph,n) for n in graph.nodes}
        for view in read(native/'inventory.json')['views']:
            rows.append(record(native,view,number,L,'new_depth_native_beam'))
        placements=balanced(raw,read(native/'scheduling-units.json')['units'],L,weights)
        # Add an explicit dependency-depth schedule when the atomic graph can
        # support it. A single original Add/Mul in B cannot be split to fill L.
        try:
            p=depth_schedule(raw,read(native/'scheduling-units.json')['units'],L,weights)
        except ValueError as error:
            if 'depth cannot fill' not in str(error):
                raise
        else:
            if p not in placements:
                placements.append(p)
        dest=export(soft,case,block,limb,T,L,placements,tag='balanced-new-depth')
        for view in read(dest/'inventory.json')['views']:
            rows.append(record(dest,view,number,L,'balanced_static'))
        print(f'NEW_DEPTH_POOL {cid} L{L} {number+1}/{len(grammar)}',flush=True)
        Graph.origins.cache_clear(); Graph.roots.cache_clear()
    a_path=export(soft,case,0,0,T,1,tag='A')
    a=record(a_path,read(a_path/'inventory.json')['views'][0],0,1,'original_no_pipeline')
    b=min((r for r in rows if r['structure']==0),key=static_score); c=min(rows,key=static_score)
    for row in (a,b,c):
        simulate(soft,case,row)
    write(pool,dict(case=cid,grammar=grammar,candidates=rows,A=a,B=b,C=c,
        pipeline_L=L,candidate_PPA_calls=0,atomic_B_unchanged=True))
    return soft


def select_new(root,cid,L):
    soft=prepare(root,cid,L); complete=soft/cid/'final-selections.json'
    if complete.exists():
        return soft
    from .workload_final_software import ENV
    import os
    sentinel=soft/'no-eda-bin'; sentinel.mkdir(exist_ok=True)
    for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
        p=sentinel/name; p.write_text('#!/bin/sh\nexit 97\n'); p.chmod(0o755)
    ENV['PATH']=str(sentinel)+os.pathsep+os.environ['PATH']
    pool=read(soft/cid/'static-pool.json'); case=next(c for c in load()['cases'] if c['id']==cid)
    contract=read(soft/'characterization-contract.json'); prices=CachedPrices(read(BASE/'diagnostic-model.json'))
    targets=read(root/'targets'/f'{cid}-L{L}.json')['targets_ps']; records=[]
    for T in targets:
        candidates=[]; seen=set()
        def add(row):
            if row['rtl_sha256'] not in seen:
                candidates.append(row); seen.add(row['rtl_sha256'])
        for number,(block,limb) in enumerate(pool['grammar']):
            rows=[r for r in pool['candidates'] if r['structure']==number]
            chosen=[min(rows,key=static_score),min(rows,key=lambda r:(r['static']['saved_bits'],static_score(r))),
                min((r for r in rows if r['origin']=='balanced_static'),key=static_score)]
            for row in chosen:
                add(row)
            graph,view,state,owners=metadata(chosen[0],T); prediction=evaluate(graph,view,state,owners,prices)
            groups={r['root']:r['members'] for r in owners['G_regions']}; weights={}
            for owner in prediction['owners']:
                ns=groups.get(owner['node'],[owner['node']])
                for n in ns:
                    weights[n]=owner['delay_ps']/len(ns)
            native=export(soft,case,block,limb,T,L)
            placements=balanced(read(native/'graph.json'),read(native/'scheduling-units.json')['units'],L,weights)[:2]
            pressure=export(soft,case,block,limb,T,L,placements,'pressure')
            for view in read(pressure/'inventory.json')['views']:
                add(record(pressure,view,number,L,'model_pressure_balanced'))
            Graph.origins.cache_clear(); Graph.roots.cache_clear()
        for row in (pool['B'],pool['C']):
            add(row)
        scored=[]; out=soft/cid/f'scores-T{T}'; out.mkdir(exist_ok=True)
        for index,row in enumerate(candidates):
            ident=hashlib.sha256(canonical(dict(rtl=row['rtl_sha256'],T=T))).hexdigest()
            trace=out/(ident+'.json.gz')
            if trace.exists():
                item=json.loads(gzip.decompress(trace.read_bytes()))
            else:
                graph,view,state,owners=metadata(row,T)
                result=optimize(graph,view,state,owners,prices,contract)
                item=dict(id=ident,row=row,model=result['prediction'],result=result,
                    static=evaluate(graph,view,state,owners,prices,static_cal=True),old_global=result['baseline'])
                compressed(trace,item)
            light={k:v for k,v in item.items() if k!='result'}
            light.update(trace_path=str(trace),complete_variants=item['result']['complete_variants'])
            scored.append(light); del item
            print(f'NEW_DEPTH_SCORE {cid} L{L} T{T} {index+1}/{len(candidates)}',flush=True)
            Graph.origins.cache_clear(); Graph.roots.cache_clear()
            if len(prices.cache)>25000:
                prices.cache.clear()
        valid=[r for r in scored if r['model'] is not None]
        if not valid:
            raise ValueError('no complete equivalent-period candidate')
        winner=min(valid,key=lambda r:score_key(r['model'])+(r['id'],))
        control=min(scored,key=lambda r:score_key(r['static'])+(r['id'],))
        methods={}
        for name in ('A','B','C'):
            row=pool[name]; graph,view,state,owners=metadata(row,T)
            methods[name]=export_selected(soft,case,row,T,name,prediction=evaluate(graph,view,state,owners,prices))
        result=json.loads(gzip.decompress(Path(winner['trace_path']).read_bytes()))['result']
        methods['D']=export_selected(soft,case,winner['row'],T,'D',result,winner['model'])
        methods['same_policy_static']=export_selected(soft,case,control['row'],T,'same_policy_static',prediction=control['static'])
        summary=[dict(id=r['id'],rtl_sha256=r['row']['rtl_sha256'],origin=r['row']['origin'],
            model=compact_prediction(r['model']) if r['model'] else None,static=compact_prediction(r['static']),
            complete_variants=r['complete_variants']) for r in scored]
        compressed(out/'pool-summary.json.gz',summary)
        records.append(dict(case=cid,target=dict(T_ps=T,L=L),methods=methods,
            search=dict(candidates=len(scored),complete=len(valid),selected_id=winner['id'],
                static_control_id=control['id'],same_pool_same_search_credit=True,candidate_PPA_calls=0,
                pool_summary_sha256=sha(out/'pool-summary.json.gz'))))
        print(f'NEW_DEPTH_SELECTED {cid} L{L} T{T} {methods["D"]["grammar"]}',flush=True)
    write(complete,dict(version=VERSION,case=cid,targets_ps=targets,records=records,
        application_PPA_for_selection=False,qualified=False,selector_source_sha256=sha(SOURCE)))
    return soft


def occupancy(soft,cid):
    rows=[]
    for group in read(soft/cid/'final-selections.json')['records']:
        for name,m in group['methods'].items():
            folder=Path(m['rtl']).parent; raw=read(folder/'graph.json'); graph=Graph(raw)
            weights={n['id']:static_node(graph,n) for n in graph.nodes}
            counts=Counter(m['placement'][n['id']] for n in graph.nodes if weights[n['id']]>0)
            active=active_stages(raw,m['placement'],weights)
            rows.append(dict(method=name,T_ps=m['T_clk_ps'],L=m['L'],active_arithmetic_stages=active,
                arithmetic_empty_stages=[s for s in range(m['L']) if s not in active],
                arithmetic_nodes_per_stage=[counts[s] for s in range(m['L'])],
                predicted_stage_periods_ps=[s['required_ps'] for s in m['prediction']['stages']],
                rtl_sha256=m['rtl_sha256']))
            Graph.origins.cache_clear(); Graph.roots.cache_clear()
    write(soft/'matrix-stage-occupancy.json',dict(rows=rows,
        B_atomic_depth_limitation_retained=True,empty_stages_are_reported_not_called_balanced=True))


def software(root,cid,L):
    root=Path(root).resolve(); initialize(root)
    if ready_selection(root,cid,L):
        return ready_selection(root,cid,L)
    if cid=='dot16':
        from .workload_dot16_latency import select
        soft=select(DOT,L)
    else:
        soft=select_new(root,cid,L)
    from .workload_final_replay import replay
    from .workload_final_audit import audit
    replayed=replay(soft); audited=audit(soft); occupancy(soft,cid)
    if replayed['targets']!=2 or audited['records']!=10:
        raise ValueError('new-depth software audit incomplete')
    variant=variant_root(root,cid,L)
    frozen(variant/'matrix-software-ready.json',dict(status='passed',case=cid,L=L,targets=2,
        functional_implementations=10,selected_replay_sha256=sha(soft/'selected-replay.json'),
        owner_audit_sha256=sha(soft/'all-selected-owner-audit.json'),
        selection_sha256=sha(soft/cid/'final-selections.json'),occupancy_sha256=sha(soft/'matrix-stage-occupancy.json'),
        EDA_calls=0,model_refitted=False,source_sha256=sha(SOURCE)))
    return soft/cid/'final-selections.json'


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=('initialize','software'))
    p.add_argument('--root',type=Path,default=DEFAULT); p.add_argument('--case'); p.add_argument('--L',type=int)
    args=p.parse_args(); print(initialize(args.root) if args.action=='initialize' else software(args.root,args.case,args.L))
