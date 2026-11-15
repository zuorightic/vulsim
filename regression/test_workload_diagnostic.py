"""Diagnostic semantics, ownership, timing and deterministic selection guards."""
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_diagnostic import (
    DiagnosticPrices, base_features, functional_circuit, state_projection, select)
from experiments.arithmetic_dse.workload_demand import Graph
from experiments.arithmetic_dse import wide_arithmetic as arithmetic
from regression.test_workload_abcd import node


class DiagnosticSemantics(unittest.TestCase):
    def tearDown(self):
        Graph.origins.cache_clear();Graph.roots.cache_clear()

    def test_functional_logic_uses_actual_aliases(self):
        nodes=[node(0,'input',width=4),node(1,'xor',(0,0),width=4)]
        g=Graph(dict(version='prospective-workload-graph-v1',nodes=nodes,
             ports=[dict(input=True,name='x',nodes=[0],width=4),dict(input=False,name='y',nodes=[1],width=4)]))
        c,outputs=functional_circuit(g,1)
        self.assertEqual(outputs,[0]*4)
        self.assertFalse(c.work(outputs)['work'])

    def test_functional_dynamic_shift_truth(self):
        nodes=[node(0,'input',width=4),node(1,'input',width=4),node(2,'shl',(0,1),width=4)]
        g=Graph(dict(version='prospective-workload-graph-v1',nodes=nodes,
             ports=[dict(input=True,name='a',nodes=[0],width=4),dict(input=True,name='s',nodes=[1],width=4),
                    dict(input=False,name='y',nodes=[2],width=4)]))
        c,outputs=functional_circuit(g,2)
        for a in range(16):
            for s in range(16):
                values={(n,b):((a if n==0 else s)>>b)&1 for n,b in c.leaves}
                self.assertEqual(c.evaluate(outputs,values),(a<<s)&15)

    def test_v2_carry_and_G_consumer_pins_are_kept(self):
        spec=arithmetic.spec('add',8,8,9)
        local=dict(producer=spec,captures=[dict(banks=1,declared_width=1,result_bit_map=[8])],
                   consumers=[dict(spec=None,bindings=[dict(role='carry',operand_index=2,result_bit_map=[8])]),
                              dict(spec=None,bindings=[dict(role='selector',operand_index=0,result_bit_map=[0])])])
        f=base_features(spec,750,local)
        self.assertEqual(f['capture_bits'],1)
        self.assertEqual(f['consumer_operand_pin_uses'],2)
        self.assertEqual(f['consumer_count'],2)

    def test_state_projection_retains_native_valid_capture_and_service(self):
        nodes=[node(0,'input',width=4),node(1,'input',width=1),node(2,'wire',(0,),width=4)]
        g=Graph(dict(version='prospective-workload-graph-v1',nodes=nodes,
             ports=[dict(input=True,name='a',nodes=[0],width=4),dict(input=True,name='iv',nodes=[1],width=1),
                    dict(input=False,name='y',nodes=[2],width=4)]))
        slots=[dict(valid=False,external_capture=False,variable_bits=4,variable_mask_hex=['f'],reset_hex=['5'],stage=1),
               dict(valid=True,external_capture=False,variable_bits=1,stage=1),
               dict(valid=False,external_capture=True,variable_bits=4,variable_mask_hex=['f'],reset_hex=['0'],stage=2),
               dict(valid=True,external_capture=True,variable_bits=1,stage=2)]
        p=state_projection(g,dict(valid_input_rtl_name='iv',slots=slots),2,1000)
        self.assertEqual(p['total_FF_bits'],15)
        self.assertEqual(p['owners']['native_state']['reset_one_bits'],2)
        self.assertEqual(p['owners']['external_state']['valid_bits'],1)
        self.assertEqual(p['stage_words'],[[4],[4]])


def candidate(i,area,required,target=100):
    return dict(structure=i,view='0',prediction=dict(status='diagnostic_complete',total_area_um2=area,
                critical_required_ps=required,target_met=required<=target,violation_ps=max(0,required-target)))


class DiagnosticSelection(unittest.TestCase):
    def test_feasible_minimum_area(self):
        r=select([candidate(0,10,150),candidate(1,30,80),candidate(2,20,90)])
        self.assertEqual(r['selected']['structure'],2)

    def test_all_unmet_minimum_violation_then_area(self):
        r=select([candidate(0,1,200),candidate(1,30,120),candidate(2,20,120)])
        self.assertEqual(r['selected']['structure'],2)
        self.assertFalse(r['target_met'])

    def test_stable_tie_and_no_processes(self):
        with patch('subprocess.Popen',side_effect=AssertionError('online tool')):
            r=select([candidate(2,20,90),candidate(1,20,90)])
        self.assertEqual(r['selected']['structure'],1)

    def test_incomplete_candidate_cannot_disappear(self):
        bad=candidate(0,1,1);bad['prediction']['status']='cost_uncovered'
        with self.assertRaises(ValueError):select([bad,candidate(1,2,3)])


if __name__=='__main__':unittest.main()
