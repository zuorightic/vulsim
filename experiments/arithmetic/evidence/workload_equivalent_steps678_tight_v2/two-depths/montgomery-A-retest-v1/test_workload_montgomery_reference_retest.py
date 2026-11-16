"""Clock evidence, slot coordination and immutable single-attempt admission."""
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_montgomery_reference_retest as retest


class MontgomeryReferenceRetest(unittest.TestCase):
    def test_request_uses_maximum_physical_stage_with_margin_not_pipeline_clock(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);reports=run/'reports/asap7/arithmetic_probe/base';reports.mkdir(parents=True)
            for name,period in zip(retest.STAGES,[20496.48,24030.65,24030.65,23703.61,23796.44]):
                (reports/name).write_text(f'core_clk period_min = {period} fmax = 42\nworst slack max 12203.56\n')
            basis=retest.timing_basis(run)
            self.assertEqual(basis['request_ps'],27000)
            self.assertEqual(basis['maximum_intermediate_period_ps'],24030.65)
            self.assertEqual(len(basis['stages']),5)

    def test_missing_or_ambiguous_clock_data_is_not_silently_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            run=Path(tmp);reports=run/'reports/asap7/arithmetic_probe/base';reports.mkdir(parents=True)
            (reports/retest.STAGES[0]).write_text('core_clk period_min = 0.00\n')
            with self.assertRaisesRegex(ValueError,'ambiguous'):retest.timing_basis(run)

    def test_dispatcher_is_resumed_even_when_preclaim_validation_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            parent=dict(pid=42,state='S',argv=['controller'],start='10')
            with patch.object(retest.previous,'find_processes',return_value=[parent]),\
                 patch.object(retest.previous,'signal_exact') as send,\
                 patch.object(retest.time,'sleep'):
                with self.assertRaisesRegex(ValueError,'claim validation'):
                    with retest.suspend_dispatch(Path(tmp),Path(tmp)):
                        raise ValueError('claim validation')
            self.assertEqual([c.args for c in send.call_args_list],[(parent,signal.SIGSTOP),(parent,signal.SIGCONT)])
            self.assertTrue((Path(tmp)/'dispatch-resume.json').exists())

    def test_inflight_unclaimed_dispatch_is_detected_before_competing_for_its_slot(self):
        def info(pid):
            return dict(pid=pid,argv=['python3','-u','-m','experiments.arithmetic_dse.workload_nine_runtime',
                'task','--root','/root/backend/matrix-case','--task-id',f't{pid}'])
        with patch.object(Path,'read_text',return_value='101 102'),\
             patch.object(retest.previous,'process_info',side_effect=info):
            pending=retest.unclaimed_children(dict(pid=42),dict(jobs=[dict(admission_id='matrix-case',task_id='t101')]))
        self.assertEqual(pending,[102])

    def test_frozen_retest_rejects_different_clock_threads_or_timeout(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            task=dict(id=retest.TASK,case='montgomery256',method='A',L=1,period_ps=27000,abc_target_ps=27000,
                threads=2,synth_timeout_s=3600,grt_timeout_s=21600,support_timeout_s=300,memory_limit_MiB=16384)
            def save(t):
                retest.previous.write(folder/'freeze.json',dict(tasks=[t],files={}))
                retest.previous.write(folder/'admission.json',dict(version=retest.VERSION,tasks=[t],
                    source_sha256=retest.sha(retest.SOURCE),runtime_source_sha256=retest.sha(retest.runtime.SOURCE),
                    policy_sha256=retest.sha(retest.runtime.POLICY),freeze_sha256=retest.sha(folder/'freeze.json')))
            save(task);self.assertEqual(retest.verify(folder)['tasks'][0]['period_ps'],27000)
            for change in [dict(period_ps=1500),dict(threads=4),dict(grt_timeout_s=7200)]:
                save(dict(task,**change))
                with self.assertRaisesRegex(ValueError,'resources'):retest.verify(folder)

    def test_failed_worker_is_retained_and_process_local_runtime_bindings_are_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);folder=retest.directory(root);folder.mkdir(parents=True)
            ledger=root/'ledger.json';retest.previous.write(ledger,dict(jobs=[]))
            original_verify=retest.runtime.verify;original_ledger=retest.runtime.TaskLedger
            def failed(*args):
                self.assertIs(retest.runtime.verify,retest.verify)
                self.assertIs(retest.runtime.TaskLedger,retest.ReferenceLedger)
                raise RuntimeError('physical failure')
            with patch.object(retest,'verify',return_value=dict(id=folder.name)),\
                 patch.object(retest.runtime.budget,'LEDGER',ledger),\
                 patch.object(retest.runtime,'run_task',side_effect=failed) as execute,\
                 patch.object(retest,'publish',return_value={}):
                with self.assertRaisesRegex(RuntimeError,'physical failure'):retest.run(root)
                self.assertEqual(retest.previous.read(folder/'progress.json')['status'],'failed')
                with self.assertRaisesRegex(ValueError,'already attempted'):retest.run(root)
                self.assertEqual(execute.call_count,1)
            self.assertIs(retest.runtime.verify,original_verify)
            self.assertIs(retest.runtime.TaskLedger,original_ledger)


if __name__=='__main__':unittest.main()
