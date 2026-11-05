"""Frozen independent-test admission and observational proof integration."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.model_m2_tests import prepare,render_cts,physical_base
from experiments.arithmetic_dse.model_m2_live_cec import check_result


class IndependentTestGate(unittest.TestCase):
    def test_mapping_reuse_after_inherited_synthesis(self):
        m={'commands':[{'log':'/run/grt.log','command':['make','CONFIG=same','--assume-old=cts','grt']}]}
        self.assertEqual(physical_base(m),['make','CONFIG=same','--assume-old=cts'])
        with self.assertRaisesRegex(ValueError,'physical make'):physical_base({'commands':[]})
    def test_both_complete_ABC_equivalence_forms(self):
        check_result('Networks are equivalent.  Time = 0.8 sec',True)
        check_result('Networks are equivalent after structural hashing.  Time = 0.0 sec',True)
        for text in ('Networks are equivalent after assumptions.', 'Networks are NOT EQUIVALENT',
                     'Networks are equivalent after structural hashing.\nError: incomplete'):
            with self.subTest(text=text),self.assertRaises(ValueError):check_result(text,True)
    def test_unready_model_rejected_before_folder_or_launch(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'test'
            with patch('experiments.arithmetic_dse.model_m2_tests.verify_fit',return_value={'grt_validation_ready':False}), \
                 patch('experiments.arithmetic_dse.model_m2_collection.verify_plan',return_value={}):
                with self.assertRaisesRegex(ValueError,'validated selection'):prepare(Path('/plan'),Path('/selection'),out)
            self.assertFalse(out.exists())

    def test_wrong_selection_plan_rejected_before_collection(self):
        with tempfile.TemporaryDirectory() as td:
            plan=Path(td)/'plan';plan.write_text('{}');out=Path(td)/'test'
            with patch('experiments.arithmetic_dse.model_m2_tests.verify_fit',return_value={'grt_validation_ready':True,'plan_sha256':'changed'}), \
                 patch('experiments.arithmetic_dse.model_m2_collection.verify_plan',return_value={}):
                with self.assertRaisesRegex(ValueError,'validated selection'):prepare(plan,Path('/selection'),out)
            self.assertFalse(out.exists())

    def test_cts_keeps_timing_operations_and_saves_recovery_checkpoint(self):
        marker='    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v'
        original='repair_timing_helper\n'+marker+'\nlog_cmd detailed_placement'
        rendered=render_cts(original,Path('/wrapper'),Path('/request'),Path('/proof'))
        self.assertTrue(rendered.startswith('repair_timing_helper\n'));self.assertTrue(rendered.endswith('\nlog_cmd detailed_placement'))
        self.assertIn('4_1_post_repair_pre_lec.odb',rendered)
        self.assertIn('--before $::env(RESULTS_DIR)/4_before_rsz_lec.v',rendered)
        self.assertIn('--after $::env(RESULTS_DIR)/4_after_rsz_lec.v',rendered)
        self.assertNotIn('run_lec_test',rendered)
        with self.assertRaises(ValueError):render_cts(original+marker,Path('/wrapper'),Path('/request'),Path('/proof'))


if __name__=='__main__':unittest.main()
