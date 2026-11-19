"""Frozen v10 runtime functions; extracted without numerical edits from workload_equivalent.py."""
from copy import deepcopy

from dataclasses import asdict, dataclass

import math

from .equivalent_period import InversionConfig, invert_window

from .local_budget import TimingDAG

from .sampling_time_contract import canonical, sha

from . import workload_diagnostic as diagnostic

VERSION='workload-equivalent-body-budget-diagnostic-v1'


@dataclass(frozen=True)
class SearchConfig:
    rounds: int = 3
    proposals_per_round: int = 3
    transfer_fraction: float = .125
    root_vectors_per_budget: int = 3
    floor_ps: float = .001

    def __post_init__(self):
        if not (self.rounds>=1 and self.proposals_per_round>=1 and self.root_vectors_per_budget>=1
                and 0<self.transfer_fraction<1 and math.isfinite(self.floor_ps) and self.floor_ps>0):
            raise ValueError('invalid bounded feedback policy')


def request_at(query, target):
    q=deepcopy(query)
    if 'flow_context' in q:
        q['flow_context']['target_period_ps']=target
        q['flow_context']['abc_target_ps']=target
    else:q['target_ps']=target
    return q


def virtual_operator(parent, spec):
    """The sampling shell captures its immediate consumer, not its successors."""
    q=deepcopy(parent);q['declared_result_width']=spec['result_width']
    q['required_result_bits']=list(range(spec['result_width']))
    q['local_context']=dict(producer=deepcopy(spec),consumers=[],captures=[dict(
        banks=1,declared_width=spec['result_width'],result_bit_map=list(range(spec['result_width'])))])
    q['topology']=dict(operand_shared_input_roots=0,same_stage_remaining_depth=1)
    return q


class CharacterizationAdapter:
    def __init__(self,owners,prices,contract,inversion=InversionConfig()):
        if contract['operator_response_refitted'] or contract['application_PPA_used']:
            raise ValueError('equivalent-T requires frozen responses and train-only boundary')
        if contract['profile_sha256']!=prices.bundle['profile_sha256']:
            raise ValueError('sampling boundary/response profile differs')
        self.owners=owners;self.prices=prices;self.contract=contract;self.inversion=inversion
        self.rows={r['node']:('operator',r['query']) for r in owners['operators']}
        self.rows.update({r['root']:('G',r['query']) for r in owners['G_regions']})
        self.consumers={};self.cache={}
        for i,(kind,q) in self.rows.items():
            consumers=[]
            if kind=='operator':
                for index,c in enumerate(q['local_context']['consumers']):
                    if c.get('spec') is not None:
                        consumers.append(dict(kind='operator',query=virtual_operator(q,c['spec']),
                                              context='immediate_sampling_consumer',index=index))
                    elif c.get('operation')=='reduction':
                        matching=[g for g in owners['G_regions'] if
                                  any(source==i for term in g['terms'] for source,_,_ in term)]
                        if not matching:
                            raise ValueError('G consumer has no actual owner/term binding')
                        # v2 may combine several sink bindings in one G consumer.
                        # Keep all real matching endpoints; min window governs.
                        for g in matching:
                            consumers.append(dict(kind='G',query=g['query'],node=g['root'],
                                context='diagnostic_virtual_G_consumer',index=index))
                    else:raise ValueError('unpriced characterization consumer')
                if not consumers and not q['local_context']['captures']:
                    raise ValueError('operator has no characterization capture endpoint')
            elif q.get('consumers'):
                raise ValueError('G consumer shell requires explicit characterization contract')
            self.consumers[i]=consumers

    def price(self,kind,q):
        return self.prices.operator_price(q) if kind=='operator' else self.prices.reduction_price(q)

    def convert(self,node,budget):
        key=(node,budget)
        if key in self.cache:return self.cache[key]
        kind,q=self.rows[node]
        op=q['local_context']['producer']['operation'] if kind=='operator' else 'G'
        family={'mul':'Mul','add':'Add','adc':'Add','mux':'Mux','G':'G'}.get(op)
        if family is None:raise ValueError('uncovered characterization family '+op)
        shell=self.contract['families'][family];h=shell['H_char_ps'];alpha=shell['alpha']
        consumers=self.consumers[node]
        def window(t):
            values=[]
            if kind=='G' or q['local_context']['captures']:
                values.append(alpha*t-h)
            values.extend(alpha*t-h-self.price(c['kind'],request_at(c['query'],t))['delay_ps'] for c in consumers)
            return values
        result=invert_window(budget,window,self.inversion,direct=(alpha,h) if not consumers else None)
        result.update(node=node,kind=kind,family=family,H_char_ps=h,alpha=alpha,
            characterization_contract_sha256=sha(canonical(self.contract)),
            other_arithmetic=[dict(c,query_sha256=sha(canonical(c['query']))) for c in consumers],
            conversion_qualified=False)
        for root in result['roots']:
            query=request_at(q,root['tau_ps']);price=self.price(kind,query)
            root.update(query=query,query_sha256=sha(canonical(query)),price=price,
                        local_request_met=price['delay_ps']<=budget,
                        local_shortfall_ps=max(0.,price['delay_ps']-budget),
                        D_other_char_ps=[self.price(c['kind'],request_at(c['query'],root['tau_ps']))['delay_ps'] for c in consumers])
        self.cache[key]=result;return result


def timing_problem(graph,view,state,owners,baseline,bundle):
    placement=view['placement'];L=state['internal_stages']+1
    prices={r['node']:r for r in baseline['owners']}
    dynamic={i for i,p in prices.items() if p['kind'] in ('operator','G') and p['delay_ps']+p['area_um2']>0}
    regions={g['root']:g for g in owners['G_regions']};children={}
    for i,n in enumerate(graph.nodes):
        sources=({s for term in regions[i]['terms'] for s,_,_ in term} if i in regions else
                 {a['node'] for a in n['operands'] if a['node'] is not None})
        children[i]=[(j,bundle['inter_owner_wire_ps'] if j in prices and i in prices else 0.)
                     for j in sorted(sources) if placement[i]==placement[j]]
    fixed={i:p['delay_ps'] for i,p in prices.items() if i not in dynamic}
    groups=dict(enumerate(placement));endpoints=[];reserve=baseline['S']['reserve_ps']
    boundaries=bundle['S']['data_boundary_ps'];target=owners['target_ps']
    for slot in state['slots']:
        if slot['valid'] or not slot['variable_bits']:continue
        stage=slot['stage']-1;i=slot['origin']
        if placement[i]!=stage:
            i=-1-len(endpoints);children[i]=[];groups[i]=stage
        boundary=(boundaries['native_state->external_state'] if stage==L-1 else
                  boundaries['input_service->native_state'] if stage==0 else boundaries['native_state->native_state'])
        endpoints.append(dict(node=i,stage=stage,origin=slot['origin'],slot=slot['name'],
                              deadline_ps=target-boundary-reserve,boundary_ps=boundary,reserve_ps=reserve))
    problem=TimingDAG(children,endpoints,dynamic,fixed=fixed,groups=groups)
    check=problem.inspect({i:prices[i]['delay_ps'] for i in dynamic})
    for stage in baseline['stages']:
        arrival=max((r['arrival_ps'] for r in check['endpoints'] if r['stage']==stage['stage']),default=0.)
        if abs(arrival-stage['comb_delay_ps'])>1e-7:
            raise ValueError('budget DAG differs from full scorer')
    return problem


def score_key(p):
    return (0.,p['total_area_um2']) if p['target_met'] else (1.,p['violation_ps'],p['total_area_um2'])


def optimize(graph,view,state,owners,prices,contract,*,search=SearchConfig(),inversion=InversionConfig()):
    baseline=diagnostic.evaluate(graph,view,state,owners,prices)
    problem=timing_problem(graph,view,state,owners,baseline,prices.bundle)
    adapter=CharacterizationAdapter(owners,prices,contract,inversion)
    weights={r['node']:r['delay_ps'] for r in baseline['owners'] if r['node'] in problem.variables}
    initial=problem.allocate(weights,floor_ps=search.floor_ps)
    trace=[];seen=set();best=None;best_id=None;stop='round_limit';frontier=[]
    if initial['status']=='allocated':frontier=[('initial',initial['budgets_ps'])]
    else:stop='no_positive_joint_window'
    for round_index in range(search.rounds+1):
        changed=False
        for reason,budgets in frontier:
            identity=sha(canonical({str(i):v for i,v in sorted(budgets.items())}))
            if identity in seen:
                trace.append(dict(round=round_index,proposal=reason,status='repeated_budget',budget_sha256=identity))
                continue
            seen.add(identity);check=problem.inspect(budgets)
            if not check['feasible']:raise ValueError('feedback broke joint budget conservation')
            converted={i:adapter.convert(i,budgets[i]) for i in sorted(budgets)}
            entry=dict(round=round_index,proposal=reason,budget_sha256=identity,
                       budgets_ps=budgets,budget_check=check,conversions=converted,variants=[])
            trace.append(entry)
            if any(c['status']!='converted' for c in converted.values()):
                entry['status']='conversion_uncovered';continue
            counts=[len(c['roots']) for c in converted.values()]
            # Keep more than one compatible root without an exponential search.
            # Diagonal root vectors are explicit; mixed root combinations are
            # NOT claimed to have been exhausted.
            vectors=min(search.root_vectors_per_budget,max(counts,default=1));seen_vectors=set()
            entry.update(status='fully_scored',root_vectors_policy='bounded_diagonal',
                         possible_root_combinations=math.prod(counts),root_vectors_scored=0)
            for rank in range(vectors):
                vector={i:min(rank,len(c['roots'])-1) for i,c in converted.items()}
                if tuple(vector.values()) in seen_vectors:continue
                seen_vectors.add(tuple(vector.values()))
                roots={i:c['roots'][vector[i]] for i,c in converted.items()}
                queries={i:roots[i]['query'] if i in roots else request_at(q,owners['target_ps'])
                         for i,(_,q) in adapter.rows.items()}
                prediction=diagnostic.evaluate(graph,view,state,owners,prices,owner_queries=queries)
                variant_id=f'{len(trace)-1}:{rank}'
                snapshot=dict(id=variant_id,root_indices=vector,actual_queries=queries,
                    prediction=prediction,owner_queries_sha256=sha(canonical(queries)),
                    local_requests_unmet=sum(not r['local_request_met'] for r in roots.values()))
                entry['variants'].append(snapshot);entry['root_vectors_scored']+=1
                if best is None or score_key(prediction)<score_key(best['prediction']):
                    best=snapshot;best_id=variant_id;changed=True
                    snapshot['accepted_as_best']=True
                else:snapshot['accepted_as_best']=False
            entry['root_combinations_omitted']=entry['possible_root_combinations']-entry['root_vectors_scored']
        if best is None:
            stop='conversion_uncovered' if frontier else stop;break
        if round_index==search.rounds:break
        if round_index>0 and not changed:
            stop='no_improvement';break
        best_entry=trace[int(best_id.split(':')[0])]
        predicted={r['node']:r['delay_ps'] for r in best['prediction']['owners'] if r['node'] in problem.variables}
        frontier=problem.proposals(best_entry['budgets_ps'],predicted,
            limit=search.proposals_per_round,fraction=search.transfer_fraction)
        if not frontier:
            stop='fixed_point';break
    return dict(version=VERSION,status='diagnostic_complete' if best else 'cost_uncovered',qualified=False,
        target_ps=owners['target_ps'],L=state['internal_stages']+1,baseline=baseline,
        initial_allocation=initial,trace=trace,best_variant_id=best_id,
        prediction=best['prediction'] if best else None,stop_reason=stop,
        search=asdict(search),inversion=asdict(inversion),
        complete_variants=sum(len(e.get('variants',[])) for e in trace),
        candidate_PPA_calls=0,RTL_changed=False,model_response_refitted=False,
        actual_global_T_retained=True,physical_reuse_validation_pending=True,
        global_optimum_claimed=False)
