"""Shared finite software selector and target-specific final RTL receipts.

Physical reports are not imported here. The caller supplies independently
frozen targets. Static and model attribution use the exact same finite pool.
The MAC pool reuses step5's complete immutable numerical receipts, whose
original four shell families are unchanged by the common diagnostic extension.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

from .sampling_time_contract import ROOT,canonical
from .workload_abcd import read,write,sha,static_score
from .workload_equivalent_run import compact_prediction,compressed
from .workload_final_software import export,balanced,record,simulate,VERSION,ENV
from .workload_tight_equivalent import optimize
from .workload_equivalent import score_key,SearchConfig
from .workload_diagnostic import evaluate
from .workload_final_prices import CachedPrices as DiagnosticPrices
from .workload_demand import Graph
from .workload_contracts import load
from .workload_v10_replay import retarget

BASE=ROOT/'experiments/arithmetic/evidence/workload_equivalent_mac32_v1'
PREVIOUS=ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps45_v1'


def key(r,mode):return score_key(r[mode])+(r['id'],)


def metadata(row,T):
    f=Path(row['folder']);state=read(f/'state.json');state['features']['sdc_period_ps']=T
    return Graph(read(row['graph'])),dict(placement=row['placement']),state,retarget(read(f/'owners.json'),T)


def export_selected(root,case,row,T,method,result=None,prediction=None):
    pool=read(root/case['id']/'static-pool.json');block,limb=pool['grammar'][row['structure']]
    L=row['L'];out=root/'selected'/case['id']/f'T{T}-L{L}'/method;out.mkdir(parents=True,exist_ok=True)
    native=export(root,case,block,limb,T,L,[row['placement']],tag='final-'+method)
    v=read(native/'inventory.json')['views'][0];r=record(native,v,row['structure'],L,'final_'+method)
    if r['rtl_sha256']!=row['rtl_sha256']:raise ValueError('selected native RTL differs from scored input')
    simulate(root,case,r)
    for n in ('workload.sv','owners.json','state.json','tb.sv','simulation.log','functional-receipt.json'):
        shutil.copyfile(Path(r['folder'])/n,out/n)
    shutil.copyfile(native/'graph.json',out/'graph.json')
    receipt=dict(case=case['id'],T_clk_ps=T,L=L,II=1,additional_input_service_cycles=1,
        method=method,structure=row['structure'],grammar=[block,limb],placement=row['placement'],
        rtl_sha256=row['rtl_sha256'],source_selection=row,simulation_status='passed',
        rtl=str(out/'workload.sv'),simulation_receipt=str(out/'functional-receipt.json'),
        model_sha256=sha(BASE/'diagnostic-model.json'),contract_sha256=sha(root/'characterization-contract.json'),
        qualification='diagnostic_only',prediction=compact_prediction(prediction) if prediction else None)
    if result:
        compressed(out/'complete-budget-trace.json.gz',result)
        if result.get('allocation_envelope_ps') is not None:
            receipt.update(allocation_envelope_ps=result['allocation_envelope_ps'],
                requested_budget_window_feasible=False)
        e=result['trace'][int(result['best_variant_id'].split(':')[0])]
        v=next(v for v in e['variants'] if v['id']==result['best_variant_id'])
        write(out/'equivalent-requests.json',dict(T_clk_ps=T,budgets_ps=e['budgets_ps'],actual_queries=v['actual_queries'],
            model_sha256=receipt['model_sha256'],common_contract_sha256=receipt['contract_sha256']))
        receipt.update(budget_trace_sha256=sha(out/'complete-budget-trace.json.gz'),queries_sha256=sha(out/'equivalent-requests.json'))
    write(out/'selection.json',receipt);return receipt


def select_case(root,cid,targets):
    root=Path(root).resolve();case=next(c for c in load()['cases'] if c['id']==cid)
    complete=root/cid/'final-selections.json'
    if complete.exists():
        r=read(complete)
        if r['targets_ps']!=targets:raise ValueError('targets changed after selection')
        return r
    sentinel=root/'no-eda-bin';sentinel.mkdir(exist_ok=True)
    for name in ('yosys','abc','yosys-abc','openroad','opensta','sta'):
        executable=sentinel/name
        executable.write_text('#!/bin/sh\nexit 97\n');executable.chmod(0o755)
    ENV['PATH']=str(sentinel)+os.pathsep+os.environ['PATH']
    pool=read(root/cid/'static-pool.json');prices=DiagnosticPrices(read(BASE/'diagnostic-model.json'))
    contract=read(root/'characterization-contract.json');records=[];counts=[]
    for T in targets:
        scored=[];candidates=[];out=root/cid/f'scores-T{T}';out.mkdir(exist_ok=True)
        if cid=='mac32':
            from .workload_steps45_package import replay_data
            data,input_sha=replay_data(PREVIOUS)
            for old in data['rows']:
                if old['target_ps']!=T:continue
                folder=ROOT.parent/'vulsim-artifacts/workload-equivalent-steps45-v1'/old['path']
                v=old['view'];s=old['structure']
                row=dict(id=old['id'],folder=str(folder/v['directory']),graph=str(folder/'graph.json'),
                    placement=v['placement'],artifact=v['artifact'],structure=s,L=3,view=v['directory'],
                    grammar=old['grammar'],rtl_sha256=old['rtl_sha256'],origin=old['origin'])
                scored.append(dict(id=old['id'],row=row,model=old['model'],static=old['static'],result=old['result'],
                    old_global=old['result']['baseline'],numerical_reuse='original four shells unchanged; step5 full pool'))
        else:
            # Three seeds per structure, chosen before model prices: best
            # abstract critical path, least state, best balanced placement.
            # Same scope and credits for the two numerical price functions.
            for number,grammar in enumerate(pool['grammar']):
                rs=[r for r in pool['candidates'] if r['structure']==number]
                chosen=[min(rs,key=static_score),min(rs,key=lambda r:(r['static']['saved_bits'],static_score(r))),
                    min((r for r in rs if r['origin']=='balanced_static'),key=static_score)]
                seen=set()
                for r in chosen:
                    if r['rtl_sha256'] not in seen:candidates.append(r);seen.add(r['rtl_sha256'])
                # Full model pressure generates additional globally balanced
                # placements on the same legal structural grammar. Native
                # materialization rebuilds all state and G ownership.
                parent=chosen[0];g,v,s,o=metadata(parent,T);p=evaluate(g,v,s,o,prices)
                members={r['root']:r['members'] for r in o['G_regions']};weights={}
                for owner in p['owners']:
                    ns=members.get(owner['node'],[owner['node']])
                    for n in ns:weights[n]=owner['delay_ps']/len(ns)
                block,limb=grammar;native=export(root,case,block,limb,T,parent['L'])
                placements=balanced(read(native/'graph.json'),read(native/'scheduling-units.json')['units'],parent['L'],weights)[:2]
                new=export(root,case,block,limb,T,parent['L'],placements,'pressure')
                for view in read(new/'inventory.json')['views']:
                    row=record(new,view,number,parent['L'],'model_pressure_balanced')
                    if row['rtl_sha256'] not in seen:candidates.append(row);seen.add(row['rtl_sha256'])
                Graph.origins.cache_clear();Graph.roots.cache_clear()
            # Baseline finalists are always included in the common pool.
            for r in (pool['B'],pool['C']):
                if not any(x['rtl_sha256']==r['rtl_sha256'] for x in candidates):candidates.append(r)
            for index,row in enumerate(candidates):
                identity=hashlib.sha256(canonical(dict(rtl=row['rtl_sha256'],T=T))).hexdigest();dest=out/(identity+'.json.gz')
                if dest.exists():item=json.loads(gzip.decompress(dest.read_bytes()))
                else:
                    g,v,s,o=metadata(row,T);result=optimize(g,v,s,o,prices,contract)
                    item=dict(id=identity,row=row,model=result['prediction'],static=evaluate(g,v,s,o,prices,static_cal=True),
                        result=result,old_global=result['baseline'])
                    compressed(dest,item);Graph.origins.cache_clear();Graph.roots.cache_clear()
                    del result
                # Complete traces remain byte-bound on disk; retaining every
                # wide candidate trace in RAM can exceed a backend job's
                # memory use. Selection needs only complete final prices.
                light={k:v for k,v in item.items() if k!='result'}
                light.update(trace_path=str(dest),result_info={k:item['result'][k] for k in ('stop_reason','complete_variants')})
                scored.append(light)
                print(f'SCORE {cid} T{T} {index+1}/{len(candidates)} '+str(item['model']['critical_required_ps'] if item['model'] else item['result']['stop_reason']),flush=True)
                del item
                if len(prices.cache)>25000:prices.cache.clear()
        valid=[r for r in scored if r['model'] is not None]
        if not valid:raise ValueError('all declared candidates lack complete equivalent-T prices: '+cid)
        d=min(valid,key=lambda r:key(r,'model'));control=min(scored,key=lambda r:key(r,'static'))
        methods={}
        for method in ('A','B','C'):
            row=pool[method];g,v,s,o=metadata(row,T);pred=evaluate(g,v,s,o,prices)
            methods[method]=export_selected(root,case,row,T,method,prediction=pred)
        if cid=='mac32':
            # MAC new block widths12 etc are outside the old four-structure
            # index. Copy the exact step5 artifacts, bound by their recorded
            # RTL/state/owners and fresh functional receipts.
            def mac_export(item,method):
                row=item['row'];folder=Path(row['folder']);out=root/'selected'/cid/f'T{T}-L3'/method;out.mkdir(parents=True,exist_ok=True)
                for n in ('workload.sv','state.json','owners.json','tb.sv'):
                    shutil.copyfile(folder/n,out/n)
                write(out/'graph.json',next(old['graph'] for old in data['rows'] if old['id']==item['id']))
                sr=dict(row,folder=str(out));simulate(root,case,sr)
                pred=item['model'] if method=='D' else item['static'];result=item['result'] if method=='D' else None
                receipt=dict(case=cid,T_clk_ps=T,L=3,II=1,additional_input_service_cycles=1,method=method,
                    grammar=row['grammar'],structure=row['structure'],placement=row['placement'],rtl_sha256=sha(out/'workload.sv'),
                    rtl=str(out/'workload.sv'),simulation_receipt=str(out/'functional-receipt.json'),simulation_status='passed',
                    prediction=compact_prediction(pred),qualification='diagnostic_only',candidate_id=item['id'],
                    numerical_reuse=item['numerical_reuse'],common_contract_sha256=sha(root/'characterization-contract.json'))
                if result:
                    compressed(out/'complete-budget-trace.json.gz',result);e=result['trace'][int(result['best_variant_id'].split(':')[0])]
                    v=next(v for v in e['variants'] if v['id']==result['best_variant_id'])
                    write(out/'equivalent-requests.json',dict(T_clk_ps=T,budgets_ps=e['budgets_ps'],actual_queries=v['actual_queries']))
                write(out/'selection.json',receipt);return receipt
            methods['D']=mac_export(d,'D');methods['same_policy_static']=mac_export(control,'same_policy_static')
        else:
            selected_trace=json.loads(gzip.decompress(Path(d['trace_path']).read_bytes()))['result']
            methods['D']=export_selected(root,case,d['row'],T,'D',selected_trace,d['model'])
            methods['same_policy_static']=export_selected(root,case,control['row'],T,'same_policy_static',prediction=control['static'])
        summaries=[dict(id=r['id'],rtl_sha256=r['row']['rtl_sha256'],origin=r['row']['origin'],
            model=compact_prediction(r['model']) if r['model'] else None,static=compact_prediction(r['static']),
            global_T=compact_prediction(r['old_global']),stop=r.get('result_info',r.get('result'))['stop_reason'],
            variants=r.get('result_info',r.get('result'))['complete_variants']) for r in scored]
        compressed(out/'pool-summary.json.gz',summaries)
        count=dict(T_ps=T,candidates=len(scored),complete=len(valid),uncovered=len(scored)-len(valid),
            complete_variants=sum(r.get('result_info',r.get('result'))['complete_variants'] for r in scored),
            selected_id=d['id'],static_control_id=control['id'],pool_summary_sha256=sha(out/'pool-summary.json.gz'),
            same_pool_same_search_credit=True,candidate_PPA_calls=0)
        counts.append(count);records.append(dict(case=cid,target=dict(T_ps=T,L=pool['B']['L']),methods=methods,search=count))
        print('SELECTED '+cid+' '+str(T)+' '+str(methods['D']['grammar']),flush=True)
    result=dict(version=VERSION,case=cid,targets_ps=targets,records=records,search=counts,
        application_PPA_for_selection=False,qualified=False,common_model_sha256=sha(BASE/'diagnostic-model.json'),
        common_contract_sha256=sha(root/'characterization-contract.json'),selector_source_sha256=sha(__file__))
    write(complete,result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--case',required=True);p.add_argument('--targets',nargs='+',type=int,required=True)
    a=p.parse_args();select_case(a.root,a.case,a.targets)
