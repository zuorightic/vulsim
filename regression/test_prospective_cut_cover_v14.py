import copy
import random
import unittest

from experiments.arithmetic_dse import prospective_cut_cover_v14 as mapper
from experiments.arithmetic_dse.prospective_logic import Circuit


def library():
    definitions = [('INV', ['A'], '!A', .05), ('AND2', ['A', 'B'], 'A*B', .1),
        ('OR2', ['A', 'B'], 'A+B', .1), ('XOR2', ['A', 'B'], 'A^B', .16),
        ('AO21', ['A', 'B', 'C'], '(A*B)+C', .11),
        ('AND4', ['A', 'B', 'C', 'D'], 'A*B*C*D', .14)]
    return [dict(cell=name, inputs=inputs, truth=mapper.expression(function,
        {pin: mapper.variable(i, len(inputs)) for i, pin in enumerate(inputs)},
        (1 << (1 << len(inputs))) - 1), area_um2=area)
        for name, inputs, function, area in definitions]


def mapped_value(circuit, outputs, mapped, values):
    by_name = {c['cell']: c for c in library()}
    signals = {0: 0, 1: 1, **{node: values[key] for key, node in circuit.leaves.items()}}
    for cut in mapped['cuts']:
        if cut['cell'] == 'wire':
            value = signals[cut['leaves'][0]]
        else:
            assignment = sum(signals[cut['leaves'][j]] << i for i, j in enumerate(cut['permutation']))
            value = ((by_name[cut['cell']]['truth'] >> assignment) & 1) ^ cut['invert']
        signals[cut['root']] = value
    return sum(signals[n] << i for i, n in enumerate(outputs))


class CutCoverTests(unittest.TestCase):
    def setUp(self):
        self.table = mapper.library_table(library())

    def test_shared_interior_can_be_absorbed_and_remain_an_output(self):
        c = Circuit()
        a, b, d = [c.leaf(n) for n in ('a', 'b', 'd')]
        shared = c.gate('and', a, b)
        outputs = [shared, c.gate('or', shared, d)]
        mapped = mapper.cover(c, outputs, self.table, witnesses=True)
        mapper.verify(c, outputs, mapped, self.table)
        self.assertAlmostEqual(mapped['area'], .21)
        self.assertEqual(mapped['overlapping_interior_gates'], 1)
        for bits in range(8):
            values = {n: bits >> i & 1 for i, n in enumerate(('a', 'b', 'd'))}
            self.assertEqual(c.evaluate(outputs, values), mapped_value(c, outputs, mapped, values))

    def test_pin_permutation_and_explicit_output_inversion(self):
        c = Circuit()
        a, b, d = [c.leaf(n) for n in range(3)]
        outputs = [c.gate('not', c.gate('or', a, c.gate('and', b, d)))]
        mapped = mapper.cover(c, outputs, self.table, witnesses=True)
        match = self.table[3, mapper.cut_truth(c, outputs[0], (a, b, d))]
        self.assertTrue(match['invert'])
        self.assertTrue(any(cut['invert'] or cut['cell'] == 'INV' for cut in mapped['cuts']))
        self.assertAlmostEqual(mapped['area'], .16)
        for bits in range(8):
            values = {n: bits >> n & 1 for n in range(3)}
            self.assertEqual(c.evaluate(outputs, values), mapped_value(c, outputs, mapped, values))

    def test_random_reconvergent_multioutput_DAGs_exhaustively(self):
        rng = random.Random(1401)
        for _ in range(30):
            c = Circuit()
            pool = [c.leaf(i) for i in range(5)] + [0, 1]
            for _ in range(26):
                pool.append(c.gate(rng.choice(('and', 'or', 'xor', 'not')), rng.choice(pool), rng.choice(pool)))
            outputs = [rng.choice(pool) for _ in range(6)]
            mapped = mapper.cover(c, outputs, self.table, witnesses=True)
            mapper.verify(c, outputs, mapped, self.table)
            for assignment in range(32):
                values = {n: assignment >> n & 1 for n in range(5)}
                self.assertEqual(c.evaluate(outputs, values), mapped_value(c, outputs, mapped, values))

    def test_carry_and_sparse_tail_with_repeated_outputs(self):
        rng = random.Random(1402)
        for width in (1, 3, 8, 17):
            c = Circuit()
            a = [c.leaf(('a', i)) for i in range(width)]
            b = [c.leaf(('b', i)) if i < 3 else 0 for i in range(width)]
            outputs, carries = c.prefix(a, b, c.leaf('cin'))
            outputs += [carries[-1], outputs[0]]
            mapped = mapper.cover(c, outputs, self.table, witnesses=True)
            mapper.verify(c, outputs, mapped, self.table)
            for _ in range(100):
                values = {n: rng.randrange(2) for n in c.leaves}
                self.assertEqual(c.evaluate(outputs, values), mapped_value(c, outputs, mapped, values))

    def test_truth_area_boundary_and_missing_cut_mutations_rejected(self):
        c = Circuit()
        a, b = c.leaf('a'), c.leaf('b')
        outputs = [c.gate('xor', a, b)]
        mapped = mapper.cover(c, outputs, self.table, witnesses=True)
        for mutation in ('truth', 'area', 'outputs', 'missing'):
            bad = copy.deepcopy(mapped)
            if mutation == 'truth':
                bad['cuts'][0]['truth'] ^= 1
            elif mutation == 'area':
                bad['area'] += 1
            elif mutation == 'outputs':
                bad['outputs'] = [a]
            else:
                bad['cuts'] = []
            with self.assertRaises(ValueError):
                mapper.verify(c, outputs, bad, self.table)

    def test_non_boolean_grammar_is_rejected(self):
        for source in ('A and B', '__import__("os")', 'A << B', '2'):
            with self.assertRaises(ValueError):
                mapper.expression(source, {'A': 2, 'B': 1}, 3)


if __name__ == '__main__':
    unittest.main()
