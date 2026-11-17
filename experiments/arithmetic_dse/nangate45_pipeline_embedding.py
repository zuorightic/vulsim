"""Evaluate actual local-budget/equivalent-tau prices on frozen compositions.

The existing physical labels remain unchanged. This is an additional comparison
on already consumed holdouts, not fresh independent data or model selection.
Physical implementation still uses global ABC T. No parameters are adjusted.
"""
from collections import defaultdict
from pathlib import Path
from .nangate45_samples import read, write, sha
from . import nangate45_pipeline_samples as samples
from . import nangate45_pipeline_fit as fitting
from . import nangate45_pipeline_runtime as runtime
from .nangate45_pipeline_check import numerical_guard
from .workload_demand import Graph


def evaluate(root):
    root = Path(root)
    output = root/'equivalent-embedding.json'
    if output.exists():
        raise ValueError('preserve frozen equivalent-embedding evaluation')
    admission = samples.verify(root)
    seal = read(root/'model-freeze.json')
    for path,expected in seal['files'].items():
        if sha(path)!=expected:
            raise ValueError('equivalent-embedding model drift')
    baseline = read(root/'evaluation.json')
    rt = runtime.load_package(root/'package/package.json')
    rows = []
    panels = defaultdict(list)
    for task in admission['tasks']:
        if task['role']=='train':
            continue
        source = next(s for s in admission['sources'] if s['id']==task['source'])
        old = next(r for r in baseline['rows'] if r['task']==task['id'])
        graph,view,state,owners = fitting.metadata(source,task['period_ps'])
        with numerical_guard():
            result = rt.optimize(graph,view,state,owners)
            prediction = result['prediction']
            if prediction is None:
                raise ValueError('equivalent composition cost uncovered: '+task['id'])
            trace = result['trace'][int(result['best_variant_id'].split(':')[0])]
            best = next(v for v in trace['variants'] if v['id']==result['best_variant_id'])
            replay = rt.evaluate(graph,view,state,owners,owner_queries=best['actual_queries'])
            if replay!=prediction:
                raise ValueError('equivalent composition numerical replay differs')
            bindings = []
            for node,conversion in trace['conversions'].items():
                root_choice = conversion['roots'][best['root_indices'][node]]
                bindings.append(dict(node=node,body_budget_ps=trace['budgets_ps'][node],tau_ps=root_choice['tau_ps'],
                    H_char_ps=conversion['H_char_ps'],D_other_char_ps=root_choice['D_other_char_ps'],
                    query=root_choice['query'],query_sha256=root_choice['query_sha256'],price=root_choice['price'],
                    local_request_met=root_choice['local_request_met']))
        timing = abs(prediction['critical_required_ps']/old['actual_required_ps']-1)
        area = abs(prediction['total_area_um2']/old['actual_area_um2']-1)
        panels[(task['role'],'complete_timing')].append(dict(source=source['source_group'],APE=timing))
        panels[(task['role'],'total_area')].append(dict(source=source['source_group'],APE=area))
        rows.append(dict(task=task['id'],source=source['source_group'],role=task['role'],target_ps=task['period_ps'],
            baseline_global_T_prediction_ps=old['predicted_required_ps'],
            equivalent_prediction_ps=prediction['critical_required_ps'],actual_required_ps=old['actual_required_ps'],
            predicted_area_um2=prediction['total_area_um2'],actual_area_um2=old['actual_area_um2'],
            timing_APE=timing,area_APE=area,bindings=bindings,complete_variants=result['complete_variants'],
            local_requests_unmet=sum(not b['local_request_met'] for b in bindings),
            requested_budget_window_feasible=result.get('requested_budget_window_feasible',True),
            complete_score_replay_equal=True,candidate_PPA_calls=0))
        Graph.origins.cache_clear()
        Graph.roots.cache_clear()
    for path,expected in seal['files'].items():
        if sha(path)!=expected:
            raise ValueError('equivalent-embedding modified a frozen model')
    metrics = {role:{metric:fitting.stats(values) for (r,metric),values in panels.items() if r==role}
               for role in ('validation','test')}
    result = dict(rows=rows,metrics=metrics,parameters_changed=False,candidate_PPA_calls=0,
        inference_IO_disabled=True,physical_ABC='global T unchanged',
        holdout_status='additional fixed-algorithm evaluation on already consumed holdouts; no new independence claim',
        model_freeze_sha256=sha(root/'model-freeze.json'))
    write(output,result)
    return metrics


if __name__=='__main__':
    import argparse,json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    print(json.dumps(evaluate(parser.parse_args().root.resolve()),indent=2))
