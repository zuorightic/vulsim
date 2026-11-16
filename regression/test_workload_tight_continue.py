"""Successor cannot replace a failed reference with an invented clock."""
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.workload_abcd import read, write
from experiments.arithmetic_dse.workload_tight_continue import freeze_reference_target


class SuccessorReferenceTargets(unittest.TestCase):
    def test_complete_proven_reference_uses_same_A_over_L_rule(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'A-reference-repair-v1/runs/reference'
            (out/'clock-readout').mkdir(parents=True);(root/'targets').mkdir()
            write(out/'clock-readout/result.json',dict(full_setup_minimum_period_ps=30001.0))
            write(out/'verification-receipt.json',dict(status='proven'))
            admission=dict(tasks=[dict(id='reference',period_ps=36000)])
            with patch('experiments.arithmetic_dse.workload_tight_continue.physical.verify',return_value=admission),patch('builtins.print'):
                self.assertTrue(freeze_reference_target(root))
                self.assertTrue(freeze_reference_target(root))
            result=read(root/'targets/montgomery256.json')
            self.assertEqual(result['targets_ps'],[1200,1450])
            self.assertEqual(result['L'],32)
            self.assertTrue(result['predecessor_failure_retained'])
            self.assertFalse(result['application_PPA_for_model'])

    def test_unfinished_reference_does_not_create_target(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            with patch('experiments.arithmetic_dse.workload_tight_continue.physical.verify',return_value=dict(tasks=[dict(id='reference')])):
                self.assertFalse(freeze_reference_target(root))
            self.assertFalse((root/'targets/montgomery256.json').exists())

    def test_reference_without_consumed_proof_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);out=root/'A-reference-repair-v1/runs/reference'
            (out/'clock-readout').mkdir(parents=True)
            write(out/'clock-readout/result.json',dict(full_setup_minimum_period_ps=30001.0))
            with patch('experiments.arithmetic_dse.workload_tight_continue.physical.verify',return_value=dict(tasks=[dict(id='reference')])):
                with self.assertRaisesRegex(ValueError,'consumed repair proof'):freeze_reference_target(root)
            self.assertFalse((root/'targets/montgomery256.json').exists())


if __name__=='__main__':unittest.main()
