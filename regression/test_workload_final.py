"""Independent invariants for the final nine-case diagnostic workflow."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_final_software import balanced
from experiments.arithmetic_dse.workload_final_adapter import Adapter,extend_contract
from experiments.arithmetic_dse.workload_abcd import read,write,sha
from experiments.arithmetic_dse.workload_equivalent import CharacterizationAdapter
from experiments.arithmetic_dse.workload_diagnostic import DiagnosticPrices
from experiments.arithmetic_dse.workload_v10_replay import old_structure
from experiments.arithmetic_dse.workload_demand import Graph
from experiments.arithmetic_dse.sampling_time_contract import ROOT

BASE=ROOT/'experiments/arithmetic/evidence/workload_equivalent_mac32_v1'


class BalancedScheduling(unittest.TestCase):
    def test_deep_chain_is_distributed_and_constant_output_is_fixed(self):
        raw=dict(nodes=[dict(id=i,operation='input' if i==0 else 'wire' if i>=9 else 'add',
            constant=i==10,operands=[] if i in (0,10) else [dict(node=i-1)]) for i in range(11)])
        units=[dict(members=[i],fixed=i in (0,9,10),constant=i==10) for i in range(11)]
        for p in balanced(raw,units,4,{i:1. for i in range(1,9)}):
            self.assertEqual(p[0],0);self.assertEqual(p[9:], [3,3])
            self.assertTrue(all(0<=s<4 for s in p))
            self.assertTrue(all(p[i]>=p[i-1] for i in range(1,10)))
        p=balanced(raw,units,4,{i:1. for i in range(1,9)})[0]
        self.assertEqual([sum(p[i]==s for i in range(1,9)) for s in range(4)],[2,2,2,2])

    def test_parallel_nodes_do_not_consume_serial_budget(self):
        raw=dict(nodes=[dict(operation='input',operands=[]),*[dict(operation='mul',operands=[dict(node=0)]) for _ in range(12)],
            dict(operation='wire',operands=[dict(node=12)])])
        units=[dict(members=[i],fixed=i in (0,13),constant=False) for i in range(14)]
        p=balanced(raw,units,4,{i:10. for i in range(1,13)})[0]
        self.assertEqual(p[1:13],[0]*12)


class ShellCoverage(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=read(BASE/'characterization-contract.json');cls.contract=extend_contract(cls.base)
        cls.prices=DiagnosticPrices(read(BASE/'diagnostic-model.json'))

    def test_existing_MAC_numerical_response_is_preserved(self):
        import json
        m=old_structure('mac32',2);owners=json.loads(m['0/owners.json']);g=Graph(json.loads(m['graph.json']))
        old=CharacterizationAdapter(owners,self.prices,self.base);new=Adapter(g,owners,self.prices,self.contract)
        for node in old.rows:
            a,b=old.convert(node,250.),new.convert(node,250.)
            self.assertEqual(a['status'],b['status'])
            self.assertEqual(a['roots'],b['roots'])

    def test_Sub_compare_and_functional_consumers_are_explicit(self):
        import json
        m=old_structure('montgomery256',3);o=json.loads(m['0/owners.json']);g=Graph(json.loads(m['graph.json']))
        adapter=Adapter(g,o,self.prices,self.contract)
        functional=[c for cs in adapter.consumers.values() for c in cs if c['kind']=='functional']
        self.assertTrue(functional)
        for c in functional:self.assertIn(c['node'],o['functional_logic'])
        found=set()
        for node,(kind,q) in adapter.rows.items():
            if kind!='operator':continue
            op=q['local_context']['producer']['operation']
            if op not in ('sub','ult'):continue
            result=adapter.convert(node,1200.);found.add(op)
            self.assertEqual(result['status'],'converted');self.assertTrue(result['boundary_extrapolated'])
            self.assertFalse(result['conversion_qualified'])
        self.assertEqual(found,{'sub','ult'})

    def test_large_budget_extends_interval_without_clipping(self):
        import json
        m=old_structure('mac32',0);o=json.loads(m['0/owners.json']);g=Graph(json.loads(m['graph.json']))
        adapter=Adapter(g,o,self.prices,self.contract)
        result=adapter.convert(next(iter(adapter.rows)),10000.)
        self.assertEqual(result['status'],'converted');self.assertTrue(result['extended_interval_used'])
        self.assertGreater(result['roots'][0]['tau_ps'],10000.)
        self.assertLess(abs(result['roots'][0]['residual_ps']),.05)

    def test_split_functional_external_bits_match_actual_operand_width(self):
        import json
        m=old_structure('karatsuba256',1);o=json.loads(m['0/owners.json']);g=Graph(json.loads(m['graph.json']))
        adapter=Adapter(g,o,self.prices,self.contract)
        checked=0
        for i,cs in adapter.consumers.items():
            for c in cs:
                if c['kind']!='functional':continue
                original=adapter.rows[i][1]['local_context']['consumers'][c['index']]
                for binding in original['bindings']:
                    self.assertEqual(g.nodes[c['node']]['operands'][binding['operand_index']]['width'],len(binding['result_bit_map']))
                checked+=1
        self.assertGreater(checked,0)


class FreezeIntegrity(unittest.TestCase):
    def test_backend_rejects_changed_simulation_and_RTL(self):
        from experiments.arithmetic_dse.workload_final_backend import verify_freeze,VERSION
        with tempfile.TemporaryDirectory() as d:
            r=Path(d);rtl=r/'a.sv';receipt=r/'pass.json';rtl.write_text('module a; endmodule');receipt.write_text('{}')
            write(r/'freeze.json',dict(version=VERSION,application_PPA_for_selection=False,files={str(p):sha(p) for p in (rtl,receipt)}))
            verify_freeze(r)
            receipt.write_text('{"status":"changed"}')
            with self.assertRaises(ValueError):verify_freeze(r)


class ExactPriceCache(unittest.TestCase):
    def test_cover_cache_rebuilds_target_interactions_exactly(self):
        import json
        from experiments.arithmetic_dse.workload_final_prices import CachedPrices
        from experiments.arithmetic_dse.workload_equivalent import request_at
        bundle=read(BASE/'diagnostic-model.json');cached=CachedPrices(bundle);original=DiagnosticPrices(bundle)
        for cid,number in [('mac32',2),('ntt8x64',3)]:
            members=old_structure(cid,number);owners=json.loads(members['0/owners.json'])
            shapes={r['query']['local_context']['producer']['operation']:r['query'] for r in owners['operators']}
            for q in shapes.values():
                for T in (250.,750.,1500.,10000.):
                    query=request_at(q,T)
                    self.assertEqual(cached.operator_price(query),original.operator_price(query))
        self.assertGreater(cached.cover_hits,0)


class UnreachableClock(unittest.TestCase):
    def test_closest_goal_keeps_actual_T_and_labels_infeasible_budgets(self):
        import json
        from experiments.arithmetic_dse.workload_tight_equivalent import optimize
        from experiments.arithmetic_dse.workload_v10_replay import retarget
        from experiments.arithmetic_dse.workload_equivalent import SearchConfig
        members=old_structure('mac32',2);owners=retarget(json.loads(members['0/owners.json']),200.)
        state=json.loads(members['0/state.json']);state['features']['sdc_period_ps']=200.
        view=json.loads(members['inventory.json'])['views'][0];graph=Graph(json.loads(members['graph.json']))
        prices=DiagnosticPrices(read(BASE/'diagnostic-model.json'));contract=extend_contract(read(BASE/'characterization-contract.json'))
        result=optimize(graph,view,state,owners,prices,contract,search=SearchConfig(rounds=1,proposals_per_round=1,root_vectors_per_budget=1))
        self.assertEqual(result['status'],'diagnostic_complete');self.assertEqual(result['target_ps'],200.)
        self.assertEqual(result['prediction']['target_ps'],200.);self.assertFalse(result['prediction']['target_met'])
        self.assertFalse(result['requested_budget_window_feasible']);self.assertFalse(result['requested_deadline_check']['feasible'])
        self.assertGreater(result['allocation_envelope_ps'],200.)
        self.assertTrue(result['actual_global_T_retained']);self.assertGreater(result['complete_variants'],0)


if __name__=='__main__':unittest.main()
