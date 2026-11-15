"""Complete diagnostic D selection on the frozen common finite candidates.

All nineteen targets freeze together before the physical runner can start.
The compiler's owned RTL is reused verbatim, with exact functional receipts.
"""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
from unittest.mock import patch

from .workload_abcd import ROOT,read,write,sha
from .workload_demand import Graph
from .workload_diagnostic import VERSION,DiagnosticPrices,make_bundle,evaluate,select
from .workload_software_validation import run


def compact(prediction):
    return {k:v for k,v in prediction.items() if k not in ('owners','S')}


def score_target(root,case,target,rows,prices,*,static_cal=False):
    suffix='static-cal' if static_cal else 'model'
    result_dir=root/'diagnostic-scores'/case/f"T{target['T_ps']}-L{target['L']}"/suffix
    result_dir.mkdir(parents=True,exist_ok=False)
    predictions=[];graphs={};inventories={}
    try:
        for row in rows:
            folder=Path(row['folder']);directory=folder.parent
            if directory not in graphs:
                # Scope the cached graph/origin objects to one structure.
                for g in graphs.values():g.origins.cache_clear();g.roots.cache_clear()
                graphs={directory:Graph(read(directory/'graph.json'))}
                inventories={directory:read(directory/'inventory.json')}
            graph=graphs[directory];inv=inventories[directory]
            view=next(v for v in inv['views'] if v['directory']==row['view'])
            if sha(folder/'workload.sv')!=row['rtl_sha256']:
                raise ValueError('candidate implementation changed since baseline scoring')
            state=read(folder/'state.json');owners=read(folder/'owners.json')
            with patch('subprocess.Popen',side_effect=AssertionError('EDA/process forbidden during model selection')):
                pred=evaluate(graph,view,state,owners,prices,static_cal=static_cal)
            path=result_dir/f"structure-{row['structure']}-view-{row['view']}.json.gz"
            path.write_bytes(gzip.compress(json.dumps(pred,separators=(',',':')).encode(),mtime=0))
            predictions.append(dict(row,prediction=compact(pred),prediction_path=str(path),prediction_sha256=sha(path)))
        selection=select(predictions)
        write(result_dir/'selection.json',dict(version=VERSION,case=case,target=target,cost_mode=suffix,
              selection=selection,candidates=predictions,bounded_candidates_unchanged=True,
              static_fallback=False,candidate_PPA_calls=0,qualification='diagnostic_only_not_W6_qualified'))
        chosen=next(r for r in predictions if (r['structure'],r['view'])==(
                    selection['selected']['structure'],selection['selected']['view']))
        print(json.dumps(dict(case=case,target=target,mode=suffix,selection=selection)),flush=True)
        return chosen,selection,result_dir/'selection.json'
    finally:
        for g in graphs.values():g.origins.cache_clear();g.roots.cache_clear()


def materialize(root,chosen,method,case,target,simulations):
    original=Path(chosen['folder']);digest=chosen['rtl_sha256']
    dest=root/'diagnostic-inputs'/digest
    if not dest.exists():
        dest.mkdir(parents=True)
        for name in ('workload.sv','state.json','owners.json','tb.sv','simulation.log'):
            shutil.copy2(original/name,dest/name)
        shutil.copy2(original.parent/'graph.json',dest/'graph.json')
    if sha(dest/'workload.sv')!=digest:
        raise ValueError('selected RTL differs from scored and emitted implementation')
    if digest not in simulations:
        env=dict(os.environ,OMP_NUM_THREADS='1')
        run(['iverilog','-g2012','-s','tb','-o',dest/'sim.out',dest/'workload.sv',dest/'tb.sv'],dest/'iverilog-fresh.log',env,300)
        output=run(['vvp',dest/'sim.out'],dest/'simulation-fresh.log',env,300)
        if 'PASS' not in output:raise ValueError('selected D functional check failed')
        simulations.add(digest)
    return dict(rtl=str(dest/'workload.sv'),rtl_sha256=digest,L=target['L'],II=1,
                input_service_additional_cycles=1,simulation_status='passed',
                simulation_receipt=str(dest/'simulation-fresh.log'),
                structure=chosen['structure'],view=chosen['view'],
                prediction=chosen['prediction'],prediction_path=chosen['prediction_path'],
                prediction_sha256=chosen['prediction_sha256'],
                qualification='diagnostic_only_not_W6_qualified')


def prepare(root):
    root=Path(root).resolve()
    if (root/'diagnostic-model.json').exists():raise ValueError('preserve model/selection attempt; use explicit continuation')
    model=make_bundle();write(root/'diagnostic-model.json',model)
    # The fixed feature/fit implementation and source roles freeze before any
    # application prediction. There is one fit and no validation-driven search.
    source_paths=[ROOT/'experiments/arithmetic_dse'/n for n in
                  ('workload_diagnostic.py','workload_diagnostic_run.py','workload_abcd.py',
                   'workload_demand.py','workload_software_validation.py','centered_response.py')]
    write(root/'diagnostic-contract.json',dict(version=VERSION,model_sha256=sha(root/'diagnostic-model.json'),
          user_authorization='先完成诊断版',qualification='diagnostic_only_not_W6_qualified',
          candidate_set='unchanged nineteen-target W2/W678 finite views used by C',
          selector='complete feasible: minimum total area; otherwise minimum maximum complete violation then area; stable candidate order',
          source_sha256={str(p):sha(p) for p in source_paths},
          static_cal_targets=[dict(case='mac32',T_ps=750),dict(case='dot16',T_ps=1000)],
          application_PPA_seen=False,application_PPA_feedback=False,independent_operator_sources_read=False))
    return score(root)


def score(root):
    root=Path(root).resolve();model=read(root/'diagnostic-model.json');contract=read(root/'diagnostic-contract.json')
    if sha(root/'diagnostic-model.json')!=contract['model_sha256']:raise ValueError('diagnostic model changed')
    for p,h in contract['source_sha256'].items():
        if sha(p)!=h:raise ValueError('selector changed after prediction began: '+p)
    baselines=read(root/'baseline-methods.json');prices=DiagnosticPrices(model)
    simulations=set();records=[];files={}
    for old in baselines['records']:
        case,target=old['case'],old['target'];target_id=f"T{target['T_ps']}-L{target['L']}"
        baseline=read(root/case/(target_id+'.json'));rows=baseline['candidates']
        methods=dict(old['methods']);prediction_path=root/'diagnostic-scores'/case/target_id/'model/selection.json'
        if prediction_path.exists():
            previous=read(prediction_path);selection=previous['selection']
            chosen=next(r for r in previous['candidates'] if (r['structure'],r['view'])==(
                        selection['selected']['structure'],selection['selected']['view']))
        else:chosen,selection,prediction_path=score_target(root,case,target,rows,prices)
        # An interrupted software run may reuse an already completed *identical*
        # selected-RTL simulation, never a physical observation.
        fresh=root/'diagnostic-inputs'/chosen['rtl_sha256']/'simulation-fresh.log'
        if fresh.exists() and 'PASS' in fresh.read_text():simulations.add(chosen['rtl_sha256'])
        methods['D']=materialize(root,chosen,'D',case,target,simulations)
        files[str(prediction_path)]=sha(prediction_path)
        if dict(case=case,T_ps=target['T_ps']) in contract['static_cal_targets']:
            path=root/'diagnostic-scores'/case/target_id/'static-cal/selection.json'
            if path.exists():
                previous=read(path);s=previous['selection'];cal=next(r for r in previous['candidates']
                     if (r['structure'],r['view'])==(s['selected']['structure'],s['selected']['view']))
            else:cal,s,path=score_target(root,case,target,rows,prices,static_cal=True)
            fresh=root/'diagnostic-inputs'/cal['rtl_sha256']/'simulation-fresh.log'
            if fresh.exists() and 'PASS' in fresh.read_text():simulations.add(cal['rtl_sha256'])
            methods['D_static_cal']=materialize(root,cal,'D_static_cal',case,target,simulations)
            files[str(path)]=sha(path)
        records.append(dict(case=case,target=target,methods=methods))
        write(root/'diagnostic-progress.json',dict(completed_targets=len(records),total_targets=19,unique_D_simulations=len(simulations),candidate_PPA_calls=0))
    methods=dict(version='nine-workload-diagnostic-ABCD-v1',records=records,
                 qualification='diagnostic_only_not_W6_qualified',model_sha256=sha(root/'diagnostic-model.json'),
                 candidate_PPA_calls=0,unique_D_simulations=len(simulations),new_D_cycles=96*len(simulations))
    write(root/'methods.json',methods)
    for name in ('methods.json','diagnostic-model.json','diagnostic-contract.json','baseline-methods.json','baselines-freeze.json'):
        files[str(root/name)]=sha(root/name)
    for row in records:
        for method,data in row['methods'].items():
            p=Path(data['rtl']);files[str(p)]=sha(p)
            receipt=Path(data['simulation_receipt']) if 'simulation_receipt' in data else p.with_name('simulation.log')
            files[str(receipt)]=sha(receipt)
            if 'prediction_path' in data:files[data['prediction_path']]=data['prediction_sha256']
    files.update(contract['source_sha256'])
    write(root/'selection-freeze.json',dict(version='nine-workload-selection-freeze-v1',files=files,
          methods_complete=True,application_PPA_seen=False,application_PPA_feedback=False,
          qualification='diagnostic_only_not_W6_qualified',cases=9,targets=19,candidate_PPA_calls=0))
    print('NINE_DIAGNOSTIC_ABCD_FROZEN targets=19 methods=78 candidates_PPA_calls=0',flush=True)
    return methods


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','continue'))
    p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    prepare(a.root) if a.action=='prepare' else score(a.root)
