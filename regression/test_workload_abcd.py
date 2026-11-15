"""Selection invariants independent of the nine application results."""
import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch

from experiments.arithmetic_dse.workload_abcd import dag_timing, static_cost, static_node, static_score, write, sha
from experiments.arithmetic_dse.workload_demand import Graph
from experiments.arithmetic_dse.workload_backend import verify_freeze, admit, measurement_sources


def node(i, op, args=(), width=16):
    return dict(id=i, operation=op, width=width, constant=False,
                known_zero_hex='0', known_one_hex='0', lo=0, hi=width-1, bit=0,
                operands=[dict(node=j, width=width, signed=False, literal_hex=None) for j in args])


def graph():
    # Two parallel branches share one input and reconverge in an addition.
    nodes = [node(0, 'input'), node(1, 'input'), node(2, 'mul', (0, 1)),
             node(3, 'add', (0, 1)), node(4, 'add', (2, 3))]
    return Graph(dict(version='prospective-workload-graph-v1', nodes=nodes,
                      ports=[dict(input=True, name='a', nodes=[0], width=16),
                             dict(input=True, name='b', nodes=[1], width=16),
                             dict(input=False, name='y', nodes=[4], width=16)]))


def state(slots, bits=16):
    return dict(slots=[dict(origin=n, stage=s, valid=False, variable_bits=16) for n, s in slots],
                features=dict(state_bits=bits, state_signals=len(slots)))


class WorkloadBaselines(unittest.TestCase):
    def tearDown(self):
        Graph.origins.cache_clear(); Graph.roots.cache_clear()

    def test_serial_sum_parallel_max(self):
        self.assertEqual(dag_timing(graph(), [0]*5, {2: 20, 3: 5, 4: 7}, state([(4, 1)]), 1), [27])

    def test_register_cut_and_forwarding(self):
        # Mul/Add results captured before the final add; no combinational
        # delay can leak across the saved-value boundary or its forward bank.
        self.assertEqual(dag_timing(graph(), [0, 0, 0, 0, 1], {2: 20, 3: 5, 4: 7},
                         state([(2, 1), (3, 1), (4, 2), (4, 3)]), 3), [20, 7, 0])

    def test_area_owns_shared_nodes_once(self):
        g = graph(); result = static_cost(g, dict(placement=[0]*5), state([(4, 1)]), 1)
        self.assertEqual(result['comb_weight'], 10)  # 16-bit Mul=8, two Adds=2

    def test_mul_bucket_successor_is_generic(self):
        for width, expected in ((1, 1), (3, 2), (128, 64), (129, 128), (256, 128), (4096, 2048)):
            g = graph()
            for n in g.nodes:
                n['width'] = width
                for a in n['operands']: a['width'] = width
            self.assertEqual(static_node(g, g.nodes[2]), expected)

    def test_stable_score_ignores_target_and_path(self):
        a = dict(structure=1, view='2', static=dict(maximum_stage_abstract_delay=5,
                 comb_weight_plus_saved_bits=30, saved_bits=20, saved_signals=3))
        b = dict(a, folder='/unrelated', target_ps=999, structure=2)
        self.assertLess(static_score(a), static_score(b))


class FrozenComparison(unittest.TestCase):
    def test_changed_implementation_rejected_before_measurement(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); rtl = root/'input.sv'; rtl.write_text('frozen implementation')
            freeze = root/'freeze.json'
            write(freeze, dict(version='nine-workload-selection-freeze-v1', application_PPA_seen=False,
                              methods_complete=True, files={str(rtl):sha(rtl)}))
            verify_freeze(freeze)
            rtl.write_text('different implementation')
            with self.assertRaisesRegex(ValueError, 'changed'): verify_freeze(freeze)

    def test_incomplete_or_post_observation_freeze_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'freeze.json'
            good = dict(version='nine-workload-selection-freeze-v1',application_PPA_seen=False,
                        methods_complete=True,files={})
            for change in (dict(methods_complete=False),dict(application_PPA_seen=True)):
                write(p, dict(good, **change))
                with self.assertRaises(ValueError): verify_freeze(p)

    def test_missing_D_cannot_reserve_physical_work(self):
        from experiments.arithmetic_dse.workload_contracts import load
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            write(root/'selection-freeze.json',dict(version='nine-workload-selection-freeze-v1',
                  application_PPA_seen=False,methods_complete=True,files={}))
            rows = [dict(case=c['id'],target=t,methods=dict(A={},B={},C={}))
                    for c in load()['cases'] for t in c['formal_targets']]
            write(root/'methods.json',dict(records=rows))
            with patch('experiments.arithmetic_dse.workload_backend.Ledger',side_effect=AssertionError('backend account must not open')):
                with self.assertRaisesRegex(ValueError,'ABCD implementation missing'): admit(root)

    def test_measurement_source_closure_exists(self):
        for p in measurement_sources(): self.assertTrue(p.is_file(), str(p))


if __name__ == '__main__': unittest.main()
