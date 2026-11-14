"""Semantic fanout invariants and the information retained by S queries."""
from copy import deepcopy
import math
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import semantic_fanout_features_v8 as features, semantic_fanout_model_v8 as model
from experiments.arithmetic_dse.prospective_logic import Circuit
from experiments.arithmetic_dse.common_centered_replay_v1 import load, close
from experiments.arithmetic_dse import common_mechanism_features_v1 as state
from experiments.arithmetic_dse.semantic_fanout_replay_v8 import verify_context_lineage

ROOT = Path(__file__).resolve().parents[1] / 'experiments/arithmetic/evidence/common_semantic_fanout_v8'


class SemanticFanoutTests(unittest.TestCase):
    def test_shared_gate_and_output_observation_loads(self):
        circuit = Circuit()
        a, b, c = [circuit.leaf(name) for name in 'abc']
        shared = circuit.gate('xor', a, b)
        outputs = [circuit.gate('and', shared, c), circuit.gate('or', shared, c)]
        circuit.gate('or', a, b)  # This dead node must not contribute loads.
        actual = features.graph_loads(circuit, outputs)
        for group in ('root', 'internal'):
            self.assertAlmostEqual(actual[group + '_log2_mass'], math.log2(5))
            self.assertAlmostEqual(actual[group + '_log2_concentration'], math.log2(2.5))
            self.assertAlmostEqual(actual[group + '_log2_effective_drivers'], math.log2(1 + 16 / 6))
            self.assertEqual(actual[group + '_log2_repair_excess'], 0.)

    def test_constants_do_not_create_driver_load(self):
        circuit = Circuit()
        value = circuit.leaf('a')
        circuit.gate('and', value, 0)
        stats = features.graph_loads(circuit, [0, 1, value])
        self.assertEqual(stats['root_log2_mass'], 1.)
        self.assertEqual(stats['internal_log2_mass'], 0.)

    def test_root_renaming_and_pair_order_preserve_features(self):
        bundle = load(ROOT / 'runtime-bundle.json.gz')
        case = next(c for c in load(ROOT / 'consumption-cases.json.gz')['cases'] if c['kind'] == 'S')
        query = deepcopy(case['queries'][0])
        renamed = deepcopy(query)
        total = sum(query['input_widths'])
        renamed['input_sink_inputs'] = [list(reversed([total - 1 - n for n in sink])) for sink in query['input_sink_inputs']]
        close(features.state_controls(query, bundle['context_function']),
              features.state_controls(renamed, bundle['context_function']))

    def test_inference_reads_no_files_and_starts_no_process(self):
        bundle = load(ROOT / 'runtime-bundle.json.gz')
        cases = load(ROOT / 'consumption-cases.json.gz')['cases']
        functions = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
        with patch('subprocess.Popen', side_effect=AssertionError('online process')):
            with patch('builtins.open', side_effect=AssertionError('online file')):
                with patch('pathlib.Path.open', side_effect=AssertionError('online path')):
                    for case in cases:
                        close(functions[case['kind']](bundle, case['queries'][0], diagnostic=True), case['expected'][0])

    def test_reused_context_still_excludes_paired_sources(self):
        bundle = load(ROOT / 'runtime-bundle.json.gz')
        train = load(ROOT / 'train-data.json.gz')
        contexts = load(ROOT / 'context-crossfit.json.gz')
        pair = train['paired_folds'][0]
        contexts['contexts'][pair['group']]['training_sources'].append(pair['new'])
        with self.assertRaisesRegex(ValueError, 'held-out context training leaked'):
            verify_context_lineage(train, contexts, load(ROOT / 'train-predictions.json.gz'), bundle)

    def test_reset_bit_reordering_aliases_the_current_query(self):
        package = load(ROOT / 'S-alias--sources.json.gz')
        bundle = load(ROOT / 'runtime-bundle.json.gz')
        for pair in package['pairs']:
            before, after = pair['old_spec'], pair['new_spec']
            self.assertNotEqual(before['semantic_signature'], after['semantic_signature'])
            for target in (500, 1500, 3000):
                q1, q2 = state.state_structure(before, target), state.state_structure(after, target)
                self.assertEqual(q1, q2)
                close(features.state_controls(q1, bundle['context_function']),
                      features.state_controls(q2, bundle['context_function']))
            self.assertFalse(pair['feeds_frozen_v8_fit'])


if __name__ == '__main__':
    unittest.main()
