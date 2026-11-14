"""Validate logical cover semantics, ownership and structural invariants."""
from copy import deepcopy
import itertools
import math
import random
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.prospective_logic import Circuit
from experiments.arithmetic_dse.prospective_cell_cover import cover, AREA
from experiments.arithmetic_dse import branch_load_features_v5 as features
from experiments.arithmetic_dse import wide_arithmetic as arithmetic
from experiments.arithmetic_dse import wide_operator_query as query


def cell_value(name, inputs):
    if name == 'not':
        return 1 - inputs[0]
    if name in ('ao21', 'aoi21', 'oa21', 'oai21'):
        a, b, c = inputs
        value = (a & b) | c if name.startswith('ao') else (a | b) & c
        return 1 - value if 'i' in name else value
    op = name.rstrip('2345')
    if op == 'xor':
        return inputs[0] ^ inputs[1]
    value = int(all(inputs)) if op in ('and', 'nand') else int(any(inputs))
    return 1 - value if op in ('nand', 'nor') else value


class BranchLoadTests(unittest.TestCase):
    def check_cover(self, circuit, outputs):
        result = cover(circuit, outputs, witnesses=True)
        owned = [n for cut in result['cuts'] for n in cut['members']]
        self.assertEqual(len(owned), len(set(owned)))
        self.assertAlmostEqual(result['area'], math.fsum(AREA[c['cell']] for c in result['cuts']))
        for cut in result['cuts']:
            leaves = list(dict.fromkeys(cut['inputs']))
            self.assertLessEqual(len(leaves), 5)
            for values in itertools.product((0, 1), repeat=len(leaves)):
                env = dict(zip(leaves, values))
                for node in cut['members']:
                    kind, a, b = circuit.nodes[node]
                    env[node] = cell_value('not' if kind == 'not' else kind + '2',
                                           [env[a]] if kind == 'not' else [env[a], env[b]])
                self.assertEqual(env[cut['root']], cell_value(cut['cell'], [env[n] for n in cut['inputs']]))
        return result

    def test_all_cell_templates_and_random_DAGs(self):
        seen = set()
        for op in ('and', 'or'):
            for count in range(2, 6):
                c = Circuit()
                bits = [c.leaf(i) for i in range(count)]
                root = bits[0]
                for bit in bits[1:]:
                    root = c.gate(op, root, bit)
                seen.update(x['cell'] for x in self.check_cover(c, [root])['cuts'])
            for inverted in (False, True):
                c = Circuit()
                a, b, d = [c.leaf(i) for i in range(3)]
                root = c.gate(op, c.gate('or' if op == 'and' else 'and', a, b), d)
                if inverted:
                    root = c.gate('not', root)
                seen.update(x['cell'] for x in self.check_cover(c, [root])['cuts'])
        rng = random.Random(51819)
        for _ in range(80):
            c = Circuit()
            signals = [0, 1] + [c.leaf(i) for i in range(8)]
            for _ in range(60):
                signals.append(c.gate(rng.choice(('and', 'or', 'xor', 'not')),
                                      rng.choice(signals), rng.choice(signals)))
            self.check_cover(c, signals[-8:])
        self.assertTrue({'and5', 'or5', 'ao21', 'oa21', 'aoi21', 'oai21'} <= seen)

    def test_external_fanout_is_not_absorbed(self):
        c = Circuit()
        a, b, d = [c.leaf(i) for i in range(3)]
        shared = c.gate('and', a, b)
        root = c.gate('or', shared, d)
        result = self.check_cover(c, [shared, root])
        self.assertFalse(any(shared in x['members'] and x['root'] != shared for x in result['cuts']))
        self.assertEqual(result['cells'], 2)

    def test_arithmetic_and_shared_outputs(self):
        for width in (1, 3, 9, 17, 32):
            c = Circuit()
            a = [c.leaf(('a', i)) for i in range(width)]
            b = [c.leaf(('b', i)) for i in range(width)]
            sums, carry = c.prefix(a, b)
            self.check_cover(c, sums + [carry[-1]])
        for serial in (False, True):
            q = dict(output_bits=73, target_ps=1373, terms=[[[j, i, i + lo] for i in range(hi - lo)]
                                           for j, (lo, hi) in enumerate(((0, 27), (25, 50), (48, 73)))])
            c, out, _ = features.previous.reduction_circuit(q, serial=serial)
            self.check_cover(c, out)

    def test_source_renaming_and_exchange_without_backend(self):
        with patch('subprocess.Popen', side_effect=AssertionError('unexpected backend')):
            q = dict(output_bits=73, target_ps=1373, terms=[[[j, i, i + lo] for i in range(hi - lo)]
                      for j, (lo, hi) in enumerate(((0, 27), (25, 50), (48, 73)))])
            renamed = deepcopy(q)
            for term in renamed['terms']:
                for bit in term:
                    bit[0] += 123
            self.assertEqual(features.reduction_features(q), features.reduction_features(renamed))
            spec = arithmetic.spec('add', 27, 17, 9)
            c, out = features.previous.operator_circuit(spec)
            swapped = deepcopy(spec)
            for key in ('width', 'zero_hex', 'one_hex'):
                swapped['lhs_' + key], swapped['rhs_' + key] = spec['rhs_' + key], spec['lhs_' + key]
            d, other = features.previous.operator_circuit(swapped)
            self.assertEqual(cover(c, out), cover(d, other))

    def test_input_valid_uses_service_capture_context(self):
        state = dict(input_widths=[8, 8], stage_words=[[64, 64], [64]], external_bits=64,
                     service_mode=0, target_ps=1373, input_sink_inputs=[[i] for i in range(16)],
                     stage_reset_one_bits=[0, 8], input_reset_one_bits=0)
        controls = features.state_controls(state)
        iv = next(p['features'] for p in controls if p['path_class'] == 'input_valid')
        self.assertEqual(iv['log2_context_capture'], math.log2(17))
        self.assertEqual(iv['log2_capture_bank_bits'], math.log2(129))


if __name__ == '__main__':
    unittest.main()
