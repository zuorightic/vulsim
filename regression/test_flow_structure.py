"""Arithmetic and structural invariants of the prospective flow model.

Run from the repository root with python3 -B -m unittest discover
-s regression -p test_flow_structure.py. No EDA installation is required.
"""
from copy import deepcopy
import random
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import wide_arithmetic as arithmetic
from experiments.arithmetic_dse import flow_structure_features as structure
from experiments.arithmetic_dse import flow_structure_features_v3 as polarity
from experiments.arithmetic_dse.prospective_logic import Circuit


def reduction(width, ranges):
    return dict(output_bits=width, target_ps=1373,
                terms=[[[source, column - lo, column] for column in range(lo, hi)]
                       for source, (lo, hi) in enumerate(ranges)])


class FlowStructureTests(unittest.TestCase):
    def test_prefix_sum_and_carry_exhaustive(self):
        for width in range(1, 6):
            c = Circuit()
            a = [c.leaf(('a', i)) for i in range(width)]
            b = [c.leaf(('b', i)) for i in range(width)]
            outputs, carry = c.prefix(a, b, c.leaf(('cin', 0)))
            for av in range(1 << width):
                for bv in range(1 << width):
                    for cin in (0, 1):
                        values = {(name, i): (av if name == 'a' else bv if name == 'b' else cin) >> i & 1
                                  for name, i in c.leaves}
                        actual = c.evaluate(outputs + [carry[-1]], values)
                        self.assertEqual(actual, av + bv + cin)

    def test_width_masks_slices_and_arithmetic_flags(self):
        rng = random.Random(71829)
        for width in (1, 2, 3, 5, 8, 17, 31, 64, 73, 128, 513):
            for op in ('add', 'adc', 'sub', 'sbb', 'mux'):
                status = 'carry' if op == 'adc' else 'borrow' if op == 'sbb' else 'none'
                control = 'dynamic' if op in ('adc', 'sbb', 'mux') else 'zero'
                zero = rng.getrandbits(width)
                one = rng.getrandbits(width) & ~zero
                spec = arithmetic.spec(op, width, width, width, lo=width // 3,
                                       status=status, control=control, za=zero, oa=one)
                c, outputs = structure.operator_circuit(spec)
                for _ in range(8):
                    a, b, cin = rng.getrandbits(width), rng.getrandbits(width), rng.randrange(2)
                    values = {(name, bit): (a if name == 'lhs' else b if name == 'rhs' else cin) >> bit & 1
                              for name, bit in c.leaves}
                    self.assertEqual(c.evaluate(outputs, values), arithmetic.evaluate(spec, a, b, cin))

    def test_fused_and_serial_reductions_match_integer_sum(self):
        rng = random.Random(7813)
        cases = [reduction(73, [(0, 27), (25, 50), (48, 73)]),
                 reduction(24, [(0, 24), (0, 6), (12, 18)]),
                 reduction(40, [(0, 6)] * 2 + [(14, 20)] * 2 + [(28, 34)] * 2),
                 reduction(32, [(0, 32)] * 9)]
        for query in cases:
            for serial in (False, True):
                c, outputs, _ = structure.reduction_circuit(query, serial=serial)
                for _ in range(16):
                    values = {(rank, col): rng.randrange(2)
                              for rank, term in enumerate(query['terms']) for _, _, col in term}
                    truth = sum(value << col for (rank, col), value in values.items())
                    self.assertEqual(c.evaluate(outputs, values), truth & ((1 << query['output_bits']) - 1))

    def test_source_names_do_not_change_features(self):
        query = reduction(73, [(0, 27), (25, 50), (48, 73)])
        renamed = deepcopy(query)
        for term in renamed['terms']:
            for bit in term:
                bit[0] += 1000
        with patch('subprocess.Popen', side_effect=AssertionError('unexpected backend launch')):
            self.assertEqual(polarity.reduction_features(query), polarity.reduction_features(renamed))

    def test_intermediate_precision_is_distinct_from_output_width(self):
        query = reduction(73, [(0, 27), (25, 50), (48, 73)])
        f = polarity.reduction_features(query)['intensive']
        self.assertEqual(f['initial_sum_precision'], 51.)
        self.assertEqual(f['effective_sum_precision'], 73.)
        self.assertGreater(f['log2_boundary_logic_depth'], f['log2_ks_depth'])
        dense = polarity.reduction_features(reduction(24, [(0, 24), (0, 6), (12, 18)]))['intensive']
        self.assertEqual(dense['log2_boundary_logic_depth'], dense['log2_ks_depth'])

    def test_state_reset_loads_follow_capture_stage(self):
        state = dict(input_widths=[8, 8], stage_words=[[8, 8], [8]], external_bits=8,
                     service_mode=0, target_ps=1373, input_sink_inputs=[[i] for i in range(16)],
                     stage_reset_one_bits=[0, 8], input_reset_one_bits=0)
        controls = polarity.state_controls(state)
        service = next(q['features'] for q in controls if q['path_class'] == 'native_valid' and q['stage'] == 0)
        native = next(q['features'] for q in controls if q['path_class'] == 'native_valid' and q['stage'] == 1)
        self.assertEqual(service['log2_reset_one_sinks'], 0.)
        self.assertGreater(native['log2_reset_one_sinks'], 0.)
        self.assertEqual(service['native_reset_one_load'], 0.)
        self.assertEqual(native['native_reset_one_load'], native['log2_reset_one_sinks'])


if __name__ == '__main__':
    unittest.main()
