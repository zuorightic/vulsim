"""Carry semantics and the frozen diagnostic consumer's data boundaries."""
import random
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.arithmetic_dse.rebuffer_context_features_v6 import RippleCircuit
from experiments.arithmetic_dse import rebuffer_context_model_v6 as model
from experiments.arithmetic_dse.common_centered_replay_v1 import load, close

ROOT = Path(__file__).resolve().parents[1] / 'experiments/arithmetic/evidence/common_rebuffer_context_v6'


class RebufferContextTests(unittest.TestCase):
    def test_ripple_carry_crosses_wide_boundaries(self):
        rng = random.Random(2026111406)
        for width in (1, 17, 64, 129):
            circuit = RippleCircuit()
            a = [circuit.leaf(('a', i)) for i in range(width)]
            b = [circuit.leaf(('b', i)) for i in range(width)]
            cin = circuit.leaf(('cin', 0))
            sums, carries = circuit.prefix(a, b, cin)
            pairs = [(0, 0), ((1 << width) - 1, 1), ((1 << width) - 1, (1 << width) - 1)]
            pairs += [(rng.getrandbits(width), rng.getrandbits(width)) for _ in range(32)]
            for x, y in pairs:
                for carry in (0, 1):
                    values = {('a', i): (x >> i) & 1 for i in range(width)}
                    values.update({('b', i): (y >> i) & 1 for i in range(width)})
                    values['cin', 0] = carry
                    self.assertEqual(circuit.evaluate(sums + [carries[-1]], values), x + y + carry)

    def test_sparse_compression_keeps_high_carry(self):
        rng = random.Random(73132)
        width = 132
        circuit = RippleCircuit()
        columns = [[] for _ in range(width)]
        for term, (offset, bits) in enumerate(((0, 64), (1, 64), (63, 64), (0, 128), (3, 97))):
            for bit in range(bits):
                columns[offset + bit].append(circuit.leaf((term, offset + bit)))
        outputs, _ = circuit.compress(columns)
        for _ in range(64):
            values = {key: rng.getrandbits(1) for key in circuit.leaves}
            truth = sum(value << key[1] for key, value in values.items()) % (1 << width)
            self.assertEqual(circuit.evaluate(outputs, values), truth)

    def test_inference_needs_no_files_or_processes(self):
        bundle = load(ROOT / 'runtime-bundle.json.gz')
        cases = load(ROOT / 'consumption-cases.json.gz')['cases']
        functions = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
        with patch('subprocess.Popen', side_effect=AssertionError('online process')):
            with patch('builtins.open', side_effect=AssertionError('online file')):
                with patch('pathlib.Path.open', side_effect=AssertionError('online path')):
                    for case in cases:
                        close(functions[case['kind']](bundle, case['queries'][0], diagnostic=True), case['expected'][0])

    def test_paired_sources_stay_in_one_fold_and_keep_diagnostic_status(self):
        train = load(ROOT / 'train-data.json.gz')
        rows = train['data']['S']
        for pair in train['paired_folds']:
            matching = [r for r in rows if r['source'] in (pair['old'], pair['new'])]
            self.assertEqual({r['fold'] for r in matching}, {pair['group']})
            self.assertEqual(len({r['source'] for r in matching}), 2)
            self.assertEqual({r['role'] for r in matching}, {'train'})
        report = load(ROOT / 'evaluation--report.json.gz')
        self.assertFalse(report['fresh_validation'])
        self.assertFalse(report['independent_labels_read'])
        self.assertFalse(report['public_D_changed'])


if __name__ == '__main__':
    unittest.main()
