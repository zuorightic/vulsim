import builtins
from copy import deepcopy
import io
import json
import os
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_v10 as trial
from experiments.arithmetic_dse import workload_v10_replay as portable


class WorkloadV10Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bindings = trial.binding()
        archive = trial.REPO / 'experiments/arithmetic/evidence/workload_owners_v2/structures/mac32-0.tar.gz'
        with tarfile.open(archive) as tar:
            cls.plan = json.load(tar.extractfile('0/owners.json'))
        cls.operators = {r['node']: r for r in cls.plan['operators']}
        cls.query = next(r['predecessor_projection'] for r in cls.plan['operators']
                         if r['query']['local_context']['producer']['operation'] == 'add')

    def test_runtime_content_and_profile_are_bound(self):
        changed = dict(self.bindings, transition_model_json=self.bindings['transition_model_json'] + ' ')
        with self.assertRaisesRegex(ValueError, 'binding mismatch'):
            trial.Prices(changed)
        with self.assertRaisesRegex(ValueError, 'profile mismatch'):
            trial.Prices(dict(self.bindings, profile_sha256='wrong'))

    def test_public_cannot_consume_diagnostic_price(self):
        prices = trial.Prices(self.bindings)
        self.assertEqual(prices.price('operator', self.query, False)['status'], 'cost_uncovered')
        self.assertEqual(prices.price('operator', self.query, True)['status'], 'diagnostic_estimate')

    def test_add_consumes_v10_area(self):
        prices = trial.Prices(self.bindings)
        new = prices.price('operator', self.query, True)
        old = trial.inherited_operator.predict(prices.inherited, self.query, diagnostic=True)
        self.assertNotAlmostEqual(new['comb_area_um2'], old['comb_area_um2'])
        self.assertFalse(new['qualified_for_public_D'])

    def test_v10_rejection_never_retries_predecessor(self):
        prices = trial.Prices(self.bindings)
        with patch.object(trial.transition, 'predict_operator', return_value=dict(status='cost_uncovered', reason='unsupported observation')):
            with patch.object(trial.inherited_operator, 'predict', side_effect=AssertionError('silent fallback')):
                self.assertEqual(prices.price('operator', self.query, True)['status'], 'cost_uncovered')

    def test_pure_online_consumption_and_unchanged_query(self):
        prices = trial.Prices(self.bindings); query = deepcopy(self.query); expected = deepcopy(query)
        with patch.object(builtins, 'open', side_effect=AssertionError('online file read')):
            with patch.object(io, 'open', side_effect=AssertionError('online pathlib read')):
                with patch.object(subprocess, 'Popen', side_effect=AssertionError('online process')):
                    self.assertEqual(prices.price('operator', query, True)['status'], 'diagnostic_estimate')
        self.assertEqual(query, expected)

    def test_model_support_is_not_extended_for_trials(self):
        prices = trial.Prices(self.bindings); query = deepcopy(self.query)
        query['flow_context']['target_period_ps'] = 1
        query['flow_context']['abc_target_ps'] = 1
        self.assertEqual(prices.price('operator', query, True)['status'], 'cost_uncovered')
        query = deepcopy(self.query); query['topology']['operand_shared_input_roots'] = 1
        self.assertEqual(prices.price('operator', query, True)['status'], 'cost_uncovered')

    def test_missing_stage_has_no_target_met_or_winner(self):
        answer = trial.selection([dict(stage_status='cost_uncovered', partial_comb_area_um2=0)])
        self.assertIsNone(answer['selected']); self.assertIsNone(answer['target_met'])
        self.assertEqual(answer['complete_candidates'], 0)
        self.assertFalse(answer['incomplete_candidates_competed'])

    def test_partial_price_cannot_become_full_stage_by_status_edit(self):
        with self.assertRaisesRegex(ValueError, 'separately frozen selector'):
            trial.selection([dict(stage_status='diagnostic_estimate', partial_comb_area_um2=5)])

    def test_receipt_json_integral_float_representation(self):
        self.assertEqual(portable.digest(dict(clock_pressure=3)), portable.digest(dict(clock_pressure=3.0)))

    def test_receipt_does_not_round_real_numerical_differences(self):
        self.assertNotEqual(portable.digest(dict(clock_pressure=3)), portable.digest(dict(clock_pressure=3.0000000000000004)))

    def test_numerical_retarget_preserves_connections_and_source(self):
        original = deepcopy(self.plan)
        changed = portable.retarget(original, 750)
        self.assertEqual(original, self.plan)
        restored = portable.retarget(changed, self.plan['target_ps'])
        self.assertEqual(portable.digest(restored), portable.digest(self.plan))


@unittest.skipUnless(os.environ.get('VULSIM_WORKLOAD_V10_BINARY'), 'set VULSIM_WORKLOAD_V10_BINARY for native binding guards')
class NativeBindingTests(unittest.TestCase):
    def reject_binding(self, mutate, reason):
        with tempfile.TemporaryDirectory(prefix='v10-native-') as directory:
            root = trial.Path(directory)
            trial.sources.prepare_case(root / 'source', 'mac32')
            binding = trial.binding(); mutate(binding); trial.write(root / 'binding.json', binding)
            result = subprocess.run([os.environ['VULSIM_WORKLOAD_V10_BINARY'], str(trial.REPO),
                    str(root / 'source/request.json'), '3', '0', '8', '100000', str(root / 'export'),
                    '0', '500', 'owned', str(root / 'binding.json')], text=True, capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(reason, result.stderr)
            self.assertFalse(list((root / 'export').glob('*/costs-*.json')))

    def test_native_runtime_content_binding(self):
        self.reject_binding(lambda b: b.update(transition_model_json=b['transition_model_json'] + ' '),
                            'frozen v10 runtime SHA mismatch')

    def test_native_profile_binding(self):
        self.reject_binding(lambda b: b.update(profile_sha256='wrong'), 'version/profile mismatch')

    def test_native_version_binding(self):
        self.reject_binding(lambda b: b.update(version='workload-transition-v10-pretend-qualified'), 'version/profile mismatch')


if __name__ == '__main__':
    unittest.main()
