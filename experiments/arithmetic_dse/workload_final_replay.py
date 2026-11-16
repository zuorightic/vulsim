"""Independent selected-budget replay with online files and EDA disabled."""
import argparse
from collections import Counter
import gzip
from pathlib import Path
from unittest.mock import patch

from .sampling_time_contract import ROOT
from .workload_abcd import read,write,sha
from .workload_final_adapter import Adapter,extend_contract
from .workload_final_selection import BASE
from .workload_diagnostic import DiagnosticPrices,evaluate
from .workload_equivalent import timing_problem,score_key
from .workload_equivalent_run import compact_prediction
from .workload_demand import Graph


def close(a,b):
    if isinstance(a,(int,float)) and not isinstance(a,bool) and isinstance(b,(int,float)):
        return abs(a-b)<1e-7*max(1.,abs(a),abs(b))
    if isinstance(a,dict):return isinstance(b,dict) and set(a)==set(b) and all(close(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    return a==b


def replay(root):
    root=Path(root).resolve();contract=read(root/'characterization-contract.json');model=read(BASE/'diagnostic-model.json')
    if contract!=extend_contract(read(BASE/'characterization-contract.json')):raise ValueError('common boundary derivation differs')
    rows=[]
    for p in sorted((root/'selected').glob('*/T*/D/selection.json')):
        m=read(p);folder=p.parent;raw=read(folder/'graph.json');state=read(folder/'state.json');owners=read(folder/'owners.json')
        trace=read_gzip(folder/'complete-budget-trace.json.gz');index=int(trace['best_variant_id'].split(':')[0]);entry=trace['trace'][index]
        selected=next(v for v in entry['variants'] if v['id']==trace['best_variant_id']);queries={int(i):q for i,q in selected['actual_queries'].items()}
        budgets={int(i):b for i,b in entry['budgets_ps'].items()};g=Graph(raw);v=dict(placement=m['placement']);prices=DiagnosticPrices(model)
        native_audit=None
        if m['case']!='mac32':
            from .workload_owned import verify_plan
            from .workload_v10 import binding,Prices
            block,limb=m['grammar'];native=root/m['case']/f"final-D-b{block}-w{limb}-T{m['T_clk_ps']}-L{m['L']}"
            inventory=read(native/'inventory.json');binding_doc=binding();native_prices=Prices(binding_doc)
            if sha(native/'graph.json')!=sha(folder/'graph.json') or sha(native/'0/workload.sv')!=sha(folder/'workload.sv'):
                raise ValueError('native semantic audit input differs from selected implementation')
            native_audit=dict(verify_plan(native,inventory['views'][0],g,binding_doc,
                predictor=lambda owner,ops,regions,diag:native_prices.owner(owner,ops,regions,diag)))
        with patch('builtins.open',side_effect=AssertionError('online file read')),patch('io.open',side_effect=AssertionError('online pathlib read')),patch('subprocess.Popen',side_effect=AssertionError('EDA or online subprocess')):
            baseline=evaluate(g,v,state,owners,prices);problem=timing_problem(g,v,state,owners,baseline,model)
            requested_check=problem.inspect(budgets)
            if not requested_check['feasible']:
                if trace.get('requested_budget_window_feasible') is not False:raise ValueError('selected path budgets violate conservation')
                from copy import deepcopy
                alloc=deepcopy(owners);alloc['target_ps']=trace['allocation_envelope_ps']
                if not timing_problem(g,v,state,alloc,baseline,model).inspect(budgets)['feasible']:
                    raise ValueError('unreachable-clock allocation also violates its declared envelope')
            adapter=Adapter(g,owners,prices,contract);families=Counter();taus=[];extrapolated=0;residuals=[]
            for i,b in budgets.items():
                result=adapter.convert(i,b);families[result['family']]+=1;extrapolated+=result['boundary_extrapolated']
                q=queries[i];tau=q['flow_context']['target_period_ps'] if 'flow_context' in q else q['target_ps'];taus.append(tau)
                root_row=next((r for r in result['roots'] if abs(r['tau_ps']-tau)<1e-7),None)
                if root_row is None:raise ValueError('recorded actual tau is not a reproduced compatible root')
                if root_row['query']!=q:raise ValueError('query changed outside numerical T')
                residuals.append(abs(root_row['residual_ps']))
            prediction=evaluate(g,v,state,owners,prices,owner_queries=queries)
            if not close(compact_prediction(prediction),m['prediction']):raise ValueError('full selected prediction differs')
        row=dict(case=m['case'],T_clk_ps=m['T_clk_ps'],status='passed',
            native_owner_checks=native_audit or 'step5 original owner checks retained',
            requested_deadline_feasible=requested_check['feasible'],allocation_envelope_ps=trace.get('allocation_envelope_ps'),
            owners=len(adapter.rows),budget_variables=len(budgets),families=dict(families),
            boundary_extrapolated_owners=extrapolated,budget_range_ps=[min(budgets.values()),max(budgets.values())],
            tau_range_ps=[min(taus),max(taus)],maximum_window_residual_ps=max(residuals),
            full_prediction=compact_prediction(prediction),rtl_sha256=sha(folder/'workload.sv'),
            actual_global_T_retained=owners['target_ps']==m['T_clk_ps']==state['features']['sdc_period_ps'])
        rows.append(row);Graph.origins.cache_clear();Graph.roots.cache_clear()
    result=dict(status='passed',targets=len(rows),required_targets=19,rows=rows,online_file_reads=False,
        EDA_calls=0,response_refitted=False,qualified=False,source_sha256=sha(__file__))
    write(root/'selected-replay.json',result);return result


def read_gzip(path):
    import json
    return json.loads(gzip.decompress(path.read_bytes()))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);a=p.parse_args();print(replay(a.root))
