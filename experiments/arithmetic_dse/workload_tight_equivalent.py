"""Unreachable-clock continuation without changing the requested global T.

If even positive infinitesimal bodies cannot fit the requested data windows,
the ordinary allocator correctly refuses them. A finite, explicitly labelled
allocation envelope then permits complete prices for a closest-to-goal result.
Only budget deadlines change in this branch: S, control, actual queries and
the scoring objective retain the requested T. No feasible-budget claim is
made for the original deadlines.
"""
from copy import deepcopy
from unittest.mock import patch

from . import workload_equivalent as equivalent
from .workload_final_adapter import optimize as ordinary


def optimize(graph,view,state,owners,prices,contract,**kwargs):
    first=ordinary(graph,view,state,owners,prices,contract,**kwargs)
    if first['initial_allocation']['status']!='no_positive_joint_window':return first
    target=owners['target_ps'];original=equivalent.timing_problem
    problem=original(graph,view,state,owners,first['baseline'],prices.bundle)
    floor=kwargs.get('search',equivalent.SearchConfig()).floor_ps
    check=problem.inspect({i:floor for i in problem.variables})
    minimum=target+check['violation_ps']+1.
    envelopes=sorted({max(target*f,minimum+target*extra) for f,extra in ((1.25,0.),(1.5,.25),(2.,.5))})
    candidates=[];branches=[];branch_traces=[]
    for envelope in envelopes:
        def allocation_problem(g,v,s,o,b,bundle):
            allocation=deepcopy(o);allocation['target_ps']=envelope
            return original(g,v,s,allocation,b,bundle)
        with patch.object(equivalent,'timing_problem',allocation_problem):
            result=ordinary(graph,view,state,owners,prices,contract,**kwargs)
        branches.append(dict(allocation_envelope_ps=envelope,status=result['status'],
            complete_variants=result['complete_variants'],prediction=result['prediction']))
        branch_traces.append(dict(allocation_envelope_ps=envelope,initial_allocation=result['initial_allocation'],
            trace=result['trace'],best_variant_id=result['best_variant_id'],stop_reason=result['stop_reason']))
        if result['prediction'] is not None:
            result['allocation_envelope_ps']=envelope;candidates.append(result)
    if not candidates:
        first.update(unreachable_goal_continuation=branches,requested_budget_window_feasible=False)
        return first
    best=min(candidates,key=lambda r:equivalent.score_key(r['prediction'])+(r['allocation_envelope_ps'],))
    entry=best['trace'][int(best['best_variant_id'].split(':')[0])]
    requested_check=problem.inspect(entry['budgets_ps'])
    best.update(requested_budget_window_feasible=False,requested_deadline_check=requested_check,
        unreachable_goal_continuation=branches,original_initial_allocation=first['initial_allocation'],
        allocation_continuation_traces=branch_traces,
        allocation_envelope_scope='diagnostic complete-price fallback only; actual requested T and S/control unchanged',
        all_branch_complete_variants=sum(b['complete_variants'] for b in branches))
    if best['prediction']['target_met']:raise ValueError('unreachable original window reported as feasible')
    return best
