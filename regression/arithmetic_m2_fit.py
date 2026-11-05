"""Independent data roles, conservative gates and frozen fitting checks."""
import copy
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_fit import quality, choose, verify_fit
from experiments.arithmetic_dse.model_collection import write, sha


def constant(value):
    return {'kind': 'linear', 'features': [], 'coefficients': [], 'intercept': value}


class M2Fitting(unittest.TestCase):
    def row(self, split='validation', delay=100):
        return {'split': split, 'features': {}, 'delay_ps': delay, 'comb_area_um2': 10,
                'period_ps': 100, 'observed_H_ps': 10}

    def test_margin_is_included_in_error_gate(self):
        rows = [self.row()]
        self.assertEqual(quality(rows, constant(100), 'delay_ps')['status'], 'passed')
        self.assertEqual(quality(rows, constant(100), 'delay_ps', 40)['status'], 'failed')

    def test_false_feasible_uses_actual_target_and_synthetic_budgets(self):
        q = quality([self.row()], constant(80), 'delay_ps')
        self.assertEqual(q['actual_target_false_feasible'], 1)
        self.assertGreater(q['false_feasible'], 0)
        self.assertEqual(q['status'], 'failed')

    def test_no_false_feasible_when_conservative(self):
        q = quality([self.row()], constant(105), 'delay_ps')
        self.assertEqual(q['actual_target_false_feasible'], 0)
        self.assertEqual(q['false_feasible'], 0)
        self.assertEqual(q['status'], 'passed')

    def test_choose_cannot_fit_or_select_using_test_rows(self):
        rows = [self.row('train'), self.row()]
        def predictors(train, field, floor):
            self.assertTrue(all(r['split'] == 'train' for r in train))
            return [('a', constant(100)), ('b', constant(200))]
        with patch('experiments.arithmetic_dse.model_m2_fit.algorithms', predictors):
            selected = choose(rows, 'delay_ps')
            changed = choose(rows+[self.row('test', 999999)], 'delay_ps')
        self.assertEqual(selected, changed)

    def test_validation_ready_precedes_fit_error(self):
        with patch('experiments.arithmetic_dse.model_m2_fit.algorithms', return_value=[('false_feasible', constant(80)), ('safe', constant(105))]):
            chosen = choose([self.row('train'), self.row()], 'delay_ps')
        self.assertEqual(chosen['quality']['status'], 'passed')

    def test_changed_protocol_rejects_freeze(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'freeze.json'
            write(p, {'version': 'asap7-m2-primitives-fit-freeze-v1', 'test_consumed': False, 'protocol_sha256': 'changed'})
            with self.assertRaisesRegex(ValueError, 'changed fitting data/protocol'): verify_fit(p)


if __name__ == '__main__': unittest.main()
