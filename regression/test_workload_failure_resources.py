"""Resource-only retries must keep the target that selected each implementation."""
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_failure_resources as retry


class ResourceOnlyFailureRetry(unittest.TestCase):
    def setUp(self):
        self.task=dict(period_ps=850,original_period_ps=850,abc_target_ps=850,
            rtl_sha256='original-rtl',L=4)
        self.selected=dict(T_clk_ps=850,rtl_sha256='original-rtl',L=4)

    def test_longer_time_and_larger_memory_preserve_selection(self):
        task=dict(self.task,synth_timeout_s=3600,grt_timeout_s=14400,memory_limit_MiB=16384)
        retry.check_original(task,self.selected)

    def test_reject_backend_retarget_with_old_selection(self):
        with self.assertRaisesRegex(ValueError,'changed clock'):
            retry.check_original(dict(self.task,period_ps=2250,abc_target_ps=2250),self.selected)

    def test_reject_relabelling_both_backend_and_original_clock(self):
        with self.assertRaisesRegex(ValueError,'changed clock'):
            retry.check_original(dict(self.task,period_ps=2250,abc_target_ps=2250,original_period_ps=2250),self.selected)

    def test_reject_abc_only_change_and_different_implementation(self):
        for change in (dict(abc_target_ps=2250),dict(rtl_sha256='other-rtl'),dict(L=5)):
            with self.subTest(change=change),self.assertRaises(ValueError):
                retry.check_original(dict(self.task,**change),self.selected)

    def test_worker_reuses_measured_flow_with_process_local_binding(self):
        original_verify=retry.runtime.verify;original_ledger=retry.runtime.TaskLedger
        def fail(folder,tid):
            self.assertIs(retry.runtime.verify,retry.verify)
            self.assertIs(retry.runtime.TaskLedger,retry.rejected.SuccessorLedger)
            raise RuntimeError('retained tool failure')
        with patch.object(retry,'verify',return_value={}),patch.object(retry.runtime,'run_task',side_effect=fail):
            with self.assertRaisesRegex(RuntimeError,'retained tool failure'):
                retry.task(Path('/tmp/resources'),'task1')
        self.assertIs(retry.runtime.verify,original_verify)
        self.assertIs(retry.runtime.TaskLedger,original_ledger)


if __name__=='__main__':unittest.main()
