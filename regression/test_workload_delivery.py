"""A physical table alone cannot close a still-queued auxiliary proof."""
from pathlib import Path
import tempfile
import unittest

from experiments.arithmetic_dse.workload_abcd import write
from experiments.arithmetic_dse.workload_delivery import ensure_support_settled


class DeliverySettlement(unittest.TestCase):
    def fixture(self, root, exit_code=0):
        folder=root/'proofs/proof'
        folder.mkdir(parents=True)
        write(folder/'admission.json',dict(id='finite-proof'))
        write(folder/'command.json',dict(exit_code=exit_code,cleanup=dict(remaining_live_pids=[])))
        return folder,dict(measurement_cost=dict(pending=0))

    def test_a_proof_waiting_for_a_slot_keeps_the_delivery_open(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder,report=self.fixture(root)
            (folder/'command.json').unlink()
            with self.assertRaisesRegex(ValueError,'queued or running'):
                ensure_support_settled(root,report)

    def test_a_paid_support_reservation_keeps_the_delivery_open(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);_,report=self.fixture(root)
            report['measurement_cost']['pending']=1
            with self.assertRaisesRegex(ValueError,'every physical or proof leaf'):
                ensure_support_settled(root,report)

    def test_successful_command_requires_a_terminal_proof_receipt(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder,report=self.fixture(root)
            with self.assertRaisesRegex(ValueError,'terminal validation receipt'):
                ensure_support_settled(root,report)
            (folder/'result').mkdir()
            write(folder/'result/proof.json',dict(status='passed'))
            ensure_support_settled(root,report)

    def test_failed_proof_is_settled_only_after_descendant_cleanup(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);folder,report=self.fixture(root,exit_code=124)
            ensure_support_settled(root,report)
            write(folder/'command.json',dict(exit_code=124,cleanup=dict(remaining_live_pids=[123])))
            with self.assertRaisesRegex(ValueError,'cleanup is incomplete'):
                ensure_support_settled(root,report)


if __name__=='__main__':unittest.main()
