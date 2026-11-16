"""Matrix and resource-transition invariants independent of EDA tools."""
from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse.budget import Ledger,BudgetExceeded,POLICY
from experiments.arithmetic_dse.workload_abcd import read,write,sha
from experiments.arithmetic_dse.workload_latency_matrix import DEPTHS,target_pair


class LatencyMatrix(unittest.TestCase):
    def test_exactly_two_depths_and_shallower_extension(self):
        self.assertEqual(len(DEPTHS),9)
        for cid,depths in DEPTHS.items():
            self.assertEqual(len(set(depths)),2)
            self.assertGreater(depths[0],1)
            self.assertLess(depths[0],depths[1])
        self.assertEqual(DEPTHS['dot16'],[4,5])
        self.assertEqual(DEPTHS['montgomery256'],[16,32])
        self.assertEqual(sum(3 if cid=='mac32' and L==3 else 2
            for cid,depths in DEPTHS.items() for L in depths),37)

    def test_shallow_targets_use_same_measured_A_and_rounding_rule(self):
        for A,deep,shallow,expected in [
            (1059.684803,4,2,[700,800]),(1884.844337,4,2,[1200,1450]),
            (5981.928589,8,4,[1900,2250]),(5603.325317,8,4,[1800,2150]),
            (7201.306396,8,4,[2300,2750]),(9734.198421,16,8,[1550,1850])]:
            self.assertEqual(target_pair(A,shallow),expected)
            self.assertTrue(all(a>b for a,b in zip(target_pair(A,shallow),target_pair(A,deep))))
        self.assertEqual(target_pair(1444.706055,2),[950,1100])


class NineWorkerLedger(unittest.TestCase):
    def setup_ledger(self,tmp):
        root=Path(tmp); old=read(POLICY); new=read(POLICY)
        new['resources'].update(parallel_jobs=9,threads_per_tool=2)
        for name,value in [('old.json',old),('new.json',new),('checkpoint-old.json',dict(entries=[]))]:
            write(root/name,value)
        args=dict(path=root/'usage.json',policy=root/'old.json',checkpoint=root/'checkpoint-old.json')
        ledger=Ledger(**args); ledger.summary()
        return root,ledger

    def test_migration_preserves_claims_and_allows_nine_but_not_ten_jobs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,old=self.setup_ledger(tmp)
            with old.job(dict(target_platform='asap7',admission_id='old',task_id='completed')):
                pass
            before=read(old.path)
            write(root/'checkpoint-new.json',dict(entries=before['entries']))
            def ledger():
                return Ledger(path=old.path,policy=root/'new.json',checkpoint=root/'checkpoint-new.json')
            ledger().migrate(root/'old.json',root/'checkpoint-old.json','explicit user resource change')
            after=read(old.path)
            self.assertEqual(before['entries'],after['entries'])
            self.assertEqual(before['jobs'],after['jobs'])
            with ExitStack() as stack:
                for i in range(9):
                    stack.enter_context(ledger().job(dict(target_platform='asap7',admission_id='new',task_id=str(i))))
                with self.assertRaisesRegex(BudgetExceeded,'slots occupied'):
                    with ledger().job(dict(target_platform='asap7',admission_id='new',task_id='tenth')):
                        pass
            with ledger().job(dict(target_platform='asap7',admission_id='new',task_id='thread-check')) as identity:
                # Use the same ledger instance for reservation ownership.
                pass
            self.assertEqual(len(read(old.path)['jobs']),11)

    def test_migration_rejects_active_old_job_and_new_policy_rejects_four_threads(self):
        with tempfile.TemporaryDirectory() as tmp:
            root,old=self.setup_ledger(tmp)
            write(root/'checkpoint-new.json',dict(entries=[]))
            new=Ledger(path=old.path,policy=root/'new.json',checkpoint=root/'checkpoint-new.json')
            with old.job(dict(target_platform='asap7',admission_id='old',task_id='active')):
                with self.assertRaisesRegex(ValueError,'unsettled ledger'):
                    new.migrate(root/'old.json',root/'checkpoint-old.json','resource change')
            new.migrate(root/'old.json',root/'checkpoint-old.json','resource change')
            ctx=dict(target_platform='asap7',admission_id='new',task_id='two-threads')
            with new.job(ctx):
                with self.assertRaisesRegex(ValueError,'threads exceed'):
                    new.reserve('synth',1,4,'final_evaluation',['true'],root/'test',context=ctx)
                r=new.reserve('synth',1,2,'final_evaluation',['true'],root/'test',context=ctx)
                self.assertEqual(r['CPU_time_s'],2)

    def test_active_old_leaf_and_eight_new_leaves_share_nine_slots_and_settle(self):
        from experiments.arithmetic_dse import workload_nine_runtime as runtime
        with tempfile.TemporaryDirectory() as tmp:
            root,old=self.setup_ledger(tmp)
            with ExitStack() as patches:
                for obj,name,value in [
                    (runtime.budget,'LEDGER',old.path),(runtime.budget,'POLICY',root/'old.json'),
                    (runtime.budget,'CHECKPOINT',root/'checkpoint-old.json'),
                    (runtime,'POLICY',root/'new.json'),(runtime,'CHECKPOINT',root/'checkpoint-new.json'),
                    (runtime,'BRIDGE',root/'bridge.json')]:
                    patches.enter_context(patch.object(obj,name,value))
                patches.enter_context(patch.object(runtime,'prepare_policy'))
                old_ctx=dict(target_platform='asap7',admission_id='final-karatsuba256',task_id='old')
                with old.job(old_ctx):
                    before=read(old.path)
                    bridge=runtime.activate_bridge(root)
                    self.assertEqual(bridge['predecessor_job_ids'],[old.job_id])
                    self.assertEqual(runtime.active_predecessors(),1)
                    with ExitStack() as jobs:
                        new=[]
                        for i in range(8):
                            ledger=runtime.NineLedger()
                            ctx=dict(target_platform='asap7',admission_id='matrix-test',task_id=str(i))
                            jobs.enter_context(ledger.job(ctx)); new.append((ledger,ctx))
                        with self.assertRaisesRegex(BudgetExceeded,'slots occupied'):
                            with runtime.NineLedger().job(dict(target_platform='asap7',admission_id='matrix-test',task_id='tenth')):
                                pass
                        cpu=root/'time.txt'; cpu.write_text('User time (seconds): 0.1\nSystem time (seconds): 0.2\n')
                        for ledger,ctx,threads in [(old,old_ctx,4),(*new[0],2)]:
                            r=ledger.reserve(None,1,threads,'final_evaluation',['true'],root/'test',context=ctx)
                            ledger.finish(r,dict(exit_code=0,walltime_s=0.5,timed_out=False,log='test.log',gnu_time=str(cpu)))
                        self.assertEqual(read(old.path)['policy_sha256'],before['policy_sha256'])
                        self.assertEqual(len(read(old.path)['entries']),2)
                        self.assertEqual(runtime.NineLedger().summary()['pending'],0)
                    self.assertEqual(runtime.active_predecessors(),1)
                settled=read(old.path)
                self.assertTrue(all(j['status']=='released' for j in settled['jobs']))
                write(root/'checkpoint-new.json',dict(entries=settled['entries']))
                runtime.NineLedger().migrate(root/'old.json',root/'checkpoint-old.json','authorized bridge settled')
                after=read(old.path)
                self.assertEqual(settled['entries'],after['entries'])
                self.assertEqual(settled['jobs'],after['jobs'])
                self.assertEqual(runtime.NineLedger().summary()['support_calls'],2)


class MatrixPublication(unittest.TestCase):
    def test_incomplete_matrix_publishes_without_tools_or_measurements(self):
        from experiments.arithmetic_dse import workload_two_depths_run as driver
        from experiments.arithmetic_dse import workload_nine_runtime as runtime
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); write(root/'protocol.json',dict(test=True))
            write(root/'target-matrix.json',dict(rows=[dict(case=cid,L=L) for cid,ls in DEPTHS.items() for L in ls]))
            ledger=root/'usage.json'; write(ledger,dict(policy_sha256=sha(runtime.POLICY),entries=[],jobs=[]))
            with patch.object(driver,'EVIDENCE',root/'evidence'),patch.object(driver.budget,'LEDGER',ledger):
                result=driver.publish(root)
            self.assertEqual(result['main_measured'],0)
            self.assertEqual(result['required_main_records'],148)
            self.assertFalse(result['physical_comparison_complete'])
            self.assertTrue((root/'evidence/README.md').exists())


class ConcurrentReadout(unittest.TestCase):
    def completed_backend(self,root):
        run=root/'runs/task'; (run/'clock-readout').mkdir(parents=True)
        write(run/'manifest.json',dict(status='completed',threads_per_tool=2))
        write(run/'clock-readout/result.json',dict(target_ps=750,
            full_setup_minimum_period_ps=752.7,area_um2=1400,hold_WNS_ps=0.1,
            classes={'threshold_check_-0.1':dict(slack_ps=-0.1),
                     'threshold_check_0.1':dict(slack_ps=0.1)}))
        return run

    def test_partial_live_json_is_pending_without_masking_frozen_input_errors(self):
        from experiments.arithmetic_dse import workload_two_depths_run as driver
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'manifest.json'; p.write_text('{"status":')
            self.assertIsNone(driver.live_json(p))
            with self.assertRaises(json.JSONDecodeError):
                read(p)
            self.assertIsNone(driver.live_json(Path(tmp)/'not-created.json'))

    def test_new_readout_requires_settled_success_and_rejects_failed_bracket(self):
        from experiments.arithmetic_dse import workload_two_depths_run as driver
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); run=self.completed_backend(root)
            self.assertIsNone(driver.checked_readout(run,750,inherited=False))
            self.assertIsNotNone(driver.checked_readout(run,750,inherited=True))
            outcome=dict(status='completed',ledger_settled=True,
                manifest_sha256=sha(run/'manifest.json'),
                clock_readout_sha256=sha(run/'clock-readout/result.json'))
            write(run/'measurement-outcome.json',outcome)
            self.assertIsNotNone(driver.checked_readout(run,750,inherited=False))
            bad=read(run/'clock-readout/result.json')
            bad['classes']['threshold_check_-0.1']['slack_ps']=0.01
            write(run/'clock-readout/result.json',bad)
            outcome['clock_readout_sha256']=sha(run/'clock-readout/result.json')
            write(run/'measurement-outcome.json',outcome)
            self.assertIsNone(driver.checked_readout(run,750,inherited=False))
            self.assertIsNone(driver.checked_readout(run,750,inherited=True))

    def test_leaf_publishes_success_after_release_and_retains_readout_failure(self):
        from experiments.arithmetic_dse import workload_nine_runtime as runtime
        from experiments.arithmetic_dse import workload_two_depths_run as driver
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); run=self.completed_backend(root)
            ledger=root/'usage.json'
            write(ledger,dict(jobs=[dict(id='job',admission_id='batch',task_id='task',status='released')]))
            admission=dict(id='batch',tasks=[dict(id='task')])
            with patch.object(runtime,'verify',return_value=admission),patch.object(runtime.budget,'LEDGER',ledger):
                with patch.object(runtime,'_run_task',return_value='task'):
                    self.assertEqual(runtime.run_task(root,'task'),'task')
                self.assertIsNotNone(driver.checked_readout(run,750,inherited=False))
                with patch.object(runtime,'_run_task',side_effect=ValueError('bracket failed')):
                    with self.assertRaisesRegex(ValueError,'bracket failed'):
                        runtime.run_task(root,'task')
                self.assertEqual(read(run/'measurement-outcome.json')['status'],'failed')
                self.assertIsNone(driver.checked_readout(run,750,inherited=False))


if __name__=='__main__':
    unittest.main()
