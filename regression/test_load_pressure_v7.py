"""Contracts for the one-way context and paired source isolation."""
from copy import deepcopy
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import load_pressure_model_v7 as model
from experiments.arithmetic_dse.load_pressure_replay_v7 import verify_context_lineage
from experiments.arithmetic_dse.common_centered_replay_v1 import load, close

ROOT = Path(__file__).resolve().parents[1] / 'experiments/arithmetic/evidence/common_load_pressure_v7'


class LoadPressureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = load(ROOT / 'runtime-bundle.json.gz')
        cls.cases = load(ROOT / 'consumption-cases.json.gz')['cases']
        cls.state = next(c['queries'][0] for c in cls.cases if c['kind'] == 'S')

    def test_prediction_uses_no_files_or_processes(self):
        functions = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
        with patch('subprocess.Popen', side_effect=AssertionError('online process')):
            with patch('builtins.open', side_effect=AssertionError('online file')):
                with patch('pathlib.Path.open', side_effect=AssertionError('online path')):
                    for case in self.cases:
                        close(functions[case['kind']](self.bundle, case['queries'][0], diagnostic=True),
                              case['expected'][0])

    def test_context_cannot_drift_from_enable_price(self):
        bundle = deepcopy(self.bundle)
        bundle['context_function']['intercept'] += 1
        result = model.predict_state(bundle, self.state, diagnostic=True)
        self.assertEqual(result['status'], 'cost_uncovered')
        self.assertIn('dependency differs', result['reason'])

    def test_dropping_a_class_from_both_model_and_support_is_rejected(self):
        bundle = deepcopy(self.bundle)
        bundle['models']['S'].pop('external_valid')
        bundle['state_support'].pop('external_valid')
        result = model.predict_state(bundle, self.state, diagnostic=True)
        self.assertEqual(result['status'], 'cost_uncovered')
        self.assertIn('incomplete state', result['reason'])

    def test_crossfit_rejects_training_a_held_out_pair_member(self):
        train = load(ROOT / 'train-data.json.gz')
        crossfit = load(ROOT / 'context-crossfit.json.gz')
        pair = train['paired_folds'][0]
        crossfit['contexts'][pair['group']]['training_sources'].append(pair['new'])
        with self.assertRaisesRegex(ValueError, 'held-out context training leaked'):
            verify_context_lineage(train, crossfit, load(ROOT / 'train-predictions.json.gz'), self.bundle)

    def test_diagnostic_coverage_does_not_grant_public_price(self):
        for case in self.cases:
            if case['kind'] != 'S':
                continue
            self.assertTrue(all(r['status'] == 'diagnostic_estimate' for r in case['expected']))
            for query in case['queries']:
                self.assertEqual(model.predict_state(self.bundle, query)['status'], 'cost_uncovered')

    def test_extra_stage_is_rejected_by_depth_even_with_in_range_ff_load(self):
        case = load(ROOT / 'depth-rejection-cases.json.gz')['cases'][0]
        result = model.predict_state(self.bundle, case['query'], diagnostic=True)
        self.assertEqual(result['status'], 'cost_uncovered')
        self.assertIn('log2_state_depth', result['reason'])


if __name__ == '__main__':
    unittest.main()
