"""Failure-specific timing, immutable successors and retained software retry."""
import json
from pathlib import Path
import resource
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_failure_relaxation as retry


class FailureRelaxation(unittest.TestCase):
    def test_targets_use_failed_physical_periods_not_A_over_depth(self):
        self.assertEqual(retry.relaxed_targets([1680.89,2027.07,1157.53],[850,1050]),[2250,2450])
        self.assertEqual(retry.relaxed_targets([2527.10],[2150]),[2800])
        self.assertEqual(retry.relaxed_targets([1000],[2000]),[2200])

    def test_intermediate_reports_choose_clock_but_do_not_claim_complete_readout(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);p=run/'reports/asap7/arithmetic_probe/base';p.mkdir(parents=True)
            (p/'vulsim_synth_period.rpt').write_text('core_clk period_min = 1700.5 fmax = 0\n')
            result=retry.timing_basis(run)
            self.assertEqual(result[0]['period_ps'],1700.5)
            self.assertFalse((run/'clock-readout/result.json').exists())
            (p/'vulsim_synth_period.rpt').write_text('core_clk period_min = 0\n')
            with self.assertRaisesRegex(ValueError,'ambiguous'):retry.timing_basis(run)

    def test_frozen_admission_rejects_resource_clock_and_input_changes(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);inp=folder/'input.sv';inp.write_text('module Workload; endmodule\n')
            task=dict(threads=2,memory_limit_MiB=8192,synth_timeout_s=3600,grt_timeout_s=14400,
                support_timeout_s=300,period_ps=2250,abc_target_ps=2250)
            def freeze(t):
                retry.write(folder/'freeze.json',dict(tasks=[t],files={str(inp):retry.sha(inp)}))
                retry.write(folder/'admission.json',dict(version=retry.VERSION,tasks=[t],
                    source_sha256=retry.sha(retry.SOURCE),runtime_source_sha256=retry.sha(retry.runtime.SOURCE),
                    policy_sha256=retry.sha(retry.runtime.POLICY),freeze_sha256=retry.sha(folder/'freeze.json')))
            freeze(task);retry.verify(folder)
            for change in [dict(threads=4),dict(grt_timeout_s=7200),dict(abc_target_ps=850)]:
                freeze(dict(task,**change))
                with self.assertRaisesRegex(ValueError,'resource/clock'):retry.verify(folder)
            freeze(task);inp.write_text('different bytes')
            with self.assertRaisesRegex(ValueError,'input changed'):retry.verify(folder)

    def test_worker_extensions_stay_local_and_restore_even_on_backend_failure(self):
        original_verify=retry.runtime.verify;original_ledger=retry.runtime.TaskLedger
        def failed(*args):
            self.assertIs(retry.runtime.verify,retry.verify)
            self.assertIs(retry.runtime.TaskLedger,retry.SuccessorLedger)
            raise RuntimeError('retained physical failure')
        with patch.object(retry,'verify',return_value={}),patch.object(retry.runtime,'run_task',side_effect=failed):
            with self.assertRaisesRegex(RuntimeError,'retained'):retry.task(Path('/tmp/example'),'t1')
        self.assertIs(retry.runtime.verify,original_verify)
        self.assertIs(retry.runtime.TaskLedger,original_ledger)

    def test_software_failure_retains_old_log_and_does_not_retry_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);log=root/'software-logs/ntt8x64-L8.log';log.parent.mkdir();log.write_text('47/48\n')
            before=retry.sha(log)
            with patch.object(retry.resource,'getrlimit',return_value=(8*1024**2,resource.RLIM_INFINITY)),\
                 patch.object(retry.resource,'setrlimit') as limits,\
                 patch.object(retry.faulthandler,'enable'),patch.object(retry.faulthandler,'dump_traceback_later'),\
                 patch.object(retry.faulthandler,'cancel_dump_traceback_later'),\
                 patch.object(retry.previous.matrix,'software',side_effect=MemoryError('bounded retry')) as execute:
                with self.assertRaises(MemoryError):retry.software(root)
                doc=retry.read(retry.directory(root)/'ntt-software-result.json')
                self.assertEqual(doc['status'],'failed');self.assertEqual(doc['stack_bytes'],64*1024**2)
                self.assertEqual(retry.sha(log),before)
                with self.assertRaisesRegex(ValueError,'already attempted'):retry.software(root)
                self.assertEqual(execute.call_count,1)
                self.assertEqual(len(limits.call_args_list),4)

    def test_ready_software_does_not_spawn_another_existing_dispatcher(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            with patch.object(retry.previous.matrix,'ready_selection',return_value=Path('/tmp/ready.json')),\
                 patch.object(retry.previous,'find_processes',return_value=[dict(pid=42)]),\
                 patch.object(retry.subprocess,'Popen') as spawn:
                retry.ensure_ntt_dispatch(root,retry.directory(root));spawn.assert_not_called()


if __name__=='__main__':unittest.main()
