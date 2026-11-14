import copy
import random
import unittest

from experiments.arithmetic_dse import phase_cut_cover_v15 as phase
from experiments.arithmetic_dse import prospective_cut_cover_v14 as base
from experiments.arithmetic_dse.prospective_logic import Circuit
from regression.test_prospective_cut_cover_v14 import library


def evaluate(circuit, outputs, mapped, values, cells):
    lookup = {c['cell']: c for c in cells}
    signals = {(0, 0): 0, (1, 0): 1}
    signals.update({(node, 0): values[key] for key, node in circuit.leaves.items()})
    pending = {(c['root'], c['phase']): c for c in mapped['cuts']}
    while pending:
        progress = False
        for key, cut in list(pending.items()):
            deps = [(n, (cut['input_phases'] >> i) & 1) for i, n in enumerate(cut['leaves'])]
            if any(n not in signals for n in deps):
                continue
            assignment = sum(signals[deps[j]] << i for i, j in enumerate(cut['permutation']))
            value = signals[deps[0]] if cut['cell'] == 'wire' else (lookup[cut['cell']]['truth'] >> assignment) & 1
            signals[key] = value ^ cut['invert']
            del pending[key]
            progress = True
        if not progress:
            raise AssertionError('cyclic or incomplete mapped graph')
    return sum(signals[n, 0] << i for i, n in enumerate(outputs))


class PhaseCoverTests(unittest.TestCase):
    def setUp(self):
        self.cells = library() + [dict(cell='NAND2', inputs=['A', 'B'], truth=7, area_um2=.06),
                                  dict(cell='XNOR2', inputs=['A', 'B'], truth=9, area_um2=.16)]
        self.table = base.library_table(self.cells)

    def test_negative_internal_signal_removes_forced_inversion(self):
        c = Circuit()
        a, b, d, e = [c.leaf(i) for i in range(4)]
        internal = c.gate('and', a, b)
        outputs = [c.gate('xor', internal, d), c.gate('xor', internal, e)]
        mapped = phase.cover(c, outputs, self.table, witnesses=True)
        phase.verify(c, outputs, mapped, self.table)
        self.assertTrue(mapped['negative_phase_roots'])
        self.assertLess(mapped['area'], base.cover(c, outputs, self.table)['area'])
        for bits in range(16):
            values = {n: bits >> n & 1 for n in range(4)}
            self.assertEqual(c.evaluate(outputs, values), evaluate(c, outputs, mapped, values, self.cells))

    def test_random_reconvergent_graphs_all_assignments(self):
        rng = random.Random(1501)
        for _ in range(40):
            c = Circuit()
            pool = [c.leaf(i) for i in range(5)] + [0, 1]
            for _ in range(30):
                pool.append(c.gate(rng.choice(('and', 'or', 'xor', 'not')), rng.choice(pool), rng.choice(pool)))
            outputs = [rng.choice(pool) for _ in range(7)]
            mapped = phase.cover(c, outputs, self.table, witnesses=True)
            phase.verify(c, outputs, mapped, self.table)
            for bits in range(32):
                values = {n: bits >> n & 1 for n in range(5)}
                self.assertEqual(c.evaluate(outputs, values), evaluate(c, outputs, mapped, values, self.cells))

    def test_sparse_carry_status_and_repeated_boundary(self):
        rng = random.Random(1502)
        for width in (1, 7, 17, 33):
            c = Circuit()
            a = [c.leaf(('a', i)) for i in range(width)]
            b = [c.leaf(('b', i)) if i < 3 else 0 for i in range(width)]
            outputs, carry = c.prefix(a, b, c.leaf('cin'))
            outputs += [carry[-1], outputs[0]]
            mapped = phase.cover(c, outputs, self.table, witnesses=True)
            phase.verify(c, outputs, mapped, self.table)
            for _ in range(60):
                values = {n: rng.randrange(2) for n in c.leaves}
                self.assertEqual(c.evaluate(outputs, values), evaluate(c, outputs, mapped, values, self.cells))

    def test_phase_truth_permutation_and_mutations(self):
        for count in range(1, 5):
            for mask in range(1 << count):
                for p in (0, 1):
                    truth = (1 << (1 << count)) - 3
                    value = phase.phase_truth(count, truth, mask, p)
                    for assignment in range(1 << count):
                        self.assertEqual(value >> assignment & 1, (truth >> (assignment ^ mask) & 1) ^ p)
        c = Circuit()
        a, b = c.leaf('a'), c.leaf('b')
        outputs = [c.gate('xor', a, b)]
        mapped = phase.cover(c, outputs, self.table, witnesses=True)
        for kind in ('truth', 'phase', 'area', 'missing', 'self_cycle', 'phase_range'):
            bad = copy.deepcopy(mapped)
            if kind == 'truth': bad['cuts'][0]['truth'] ^= 1
            elif kind == 'phase': bad['cuts'][0]['phase'] ^= 1
            elif kind == 'area': bad['area'] += 1
            elif kind == 'missing': bad['cuts'] = []
            elif kind == 'phase_range': bad['cuts'][0]['input_phases'] = 1 << len(bad['cuts'][0]['leaves'])
            else:
                root = bad['cuts'][0]['root']
                bad['cuts'] = [dict(root=root, phase=0, leaves=[root], input_phases=0,
                                   truth=2, **self.table[1, 2])]
                bad['area'] = 0.
            with self.assertRaises(ValueError):
                phase.verify(c, outputs, bad, self.table)


if __name__ == '__main__':
    unittest.main()
