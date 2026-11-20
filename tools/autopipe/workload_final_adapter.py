"""Frozen v10 runtime functions; extracted without numerical edits from workload_final_adapter.py."""
from dataclasses import replace

from unittest.mock import patch

from .sampling_time_contract import canonical, sha

from .equivalent_period import InversionConfig, invert_window

from . import workload_equivalent as equivalent

from .workload_diagnostic import functional_circuit

from .prospective_cell_cover import cover

class Adapter:
    def __init__(self,graph,owners,prices,contract,inversion=InversionConfig()):
        if contract['operator_response_refitted'] or contract['application_PPA_used'] or contract['profile_sha256']!=prices.bundle['profile_sha256']:
            raise ValueError('frozen compatible response and train boundary required')
        self.rows={r['node']:('operator',r['query']) for r in owners['operators']}
        self.rows.update({r['root']:('G',r['query']) for r in owners['G_regions']})
        self.prices=prices;self.contract=contract;self.inversion=inversion;self.cache={};self.consumers={}
        self.consumer_delays = {}
        for i,(kind,q) in self.rows.items():
            consumers=[]
            for index,c in enumerate(q['local_context']['consumers'] if kind=='operator' else q.get('consumers',[])):
                if c.get('spec') is not None:
                    consumers.append(dict(kind='operator',query=equivalent.virtual_operator(q,c['spec']),index=index,
                        context='immediate_sampling_consumer'))
                elif c.get('operation')=='reduction':
                    matches=[g for g in owners['G_regions'] if any(s==i for term in g['terms'] for s,_,_ in term)]
                    if not matches:raise ValueError('unbound G consumer')
                    consumers.extend(dict(kind='G',query=g['query'],node=g['root'],index=index,
                        context='actual_region_as_diagnostic_sampling_consumer') for g in matches)
                elif c.get('operation')=='functional':
                    matches=[]
                    for n in owners['functional_logic']:
                        node=graph.nodes[n]
                        def binding_matches(binding):
                            index=binding['operand_index'];expected=binding['result_bit_map']
                            if index>=len(node['operands']):return False
                            if node['operands'][index]['width']!=len(expected):return False
                            actual=(graph.operand(node['operands'][index])+('0',)*len(expected))[:len(expected)]
                            return all((not isinstance(value,tuple) or value[0]!=i) if bit=='external'
                                else value==((i,bit) if type(bit) is int else bit) for value,bit in zip(actual,expected))
                        uses=any(any(isinstance(b,tuple) and b[0]==i for b in graph.operand(a)) for a in node['operands'])
                        if uses and all(binding_matches(b) for b in c['bindings']):
                            circuit,outputs=functional_circuit(graph,n);cov=cover(circuit,outputs)
                            matches.append(dict(kind='functional',node=n,index=index,query=dict(
                                delay_ps=cov['depth']*prices.bundle['numerical_floors']['gate_delay_ps'],
                                operation=graph.nodes[n]['operation'],cover=cov),context='actual immediate Boolean-cover owner'))
                    if not matches:raise ValueError('unbound functional consumer')
                    consumers.extend(matches)
                else:raise ValueError('uncovered immediate characterization consumer')
            if kind=='operator' and not consumers and not q['local_context']['captures']:
                raise ValueError('operator lacks capture/consumer endpoint')
            self.consumers[i]=consumers

    def price(self,kind,q):
        if kind=='functional':return dict(delay_ps=q['delay_ps'])
        return self.prices.operator_price(q) if kind=='operator' else self.prices.reduction_price(q)

    def consumer_delay(self, consumer, period):
        kind, query = consumer['kind'], consumer['query']
        if kind == 'functional':
            return query['delay_ps']
        # Consumer queries are retained for this adapter's lifetime. Multiple
        # owners and budget proposals can sample the same consumer and period.
        identity = kind, id(query), period
        if identity not in self.consumer_delays:
            self.consumer_delays[identity] = self.price(kind, equivalent.request_at(query, period))['delay_ps']
        return self.consumer_delays[identity]

    def convert(self,node,budget):
        key=(node,budget)
        if key in self.cache:return self.cache[key]
        kind,q=self.rows[node];op=q['local_context']['producer']['operation'] if kind=='operator' else 'G'
        family={'mul':'Mul','add':'Add','adc':'Add','sub':'Sub','ult':'Compare','ule':'Compare','eq':'Compare','mux':'Mux','G':'G'}.get(op)
        if family is None:raise ValueError('uncovered family '+op)
        shell=self.contract['families'][family];h=shell['H_char_ps'];alpha=shell['alpha'];consumers=self.consumers[node]
        def window(t):
            values=[alpha*t-h] if kind=='G' or q['local_context']['captures'] else []
            values.extend(alpha*t-h-self.consumer_delay(c,t) for c in consumers)
            return values
        result=invert_window(budget,window,self.inversion,direct=(alpha,h) if not consumers else None)
        extended=result['status']!='converted'
        if extended:result=invert_window(budget,window,replace(self.inversion,max_period_ps=100000.),direct=(alpha,h) if not consumers else None)
        result.update(node=node,kind=kind,family=family,H_char_ps=h,alpha=alpha,
            characterization_contract_sha256=sha(canonical(self.contract)),other_arithmetic=consumers,
            conversion_qualified=False,boundary_extrapolated=family in ('Sub','Compare'),extended_interval_used=extended)
        for root in result['roots']:
            query=equivalent.request_at(q,root['tau_ps']);price=self.price(kind,query)
            root.update(query=query,query_sha256=sha(canonical(query)),price=price,
                local_request_met=price['delay_ps']<=budget,local_shortfall_ps=max(0.,price['delay_ps']-budget),
                D_other_char_ps=[self.consumer_delay(c,root['tau_ps']) for c in consumers])
        self.cache[key]=result;return result


def optimize(graph,view,state,owners,prices,contract,**kwargs):
    with patch.object(equivalent,'CharacterizationAdapter',lambda *a,**k:Adapter(graph,*a,**k)):
        return equivalent.optimize(graph,view,state,owners,prices,contract,**kwargs)
