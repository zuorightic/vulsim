"""Concurrency contracts: whole-job exclusion, crash accounting, and dependency drain."""
from contextlib import ExitStack
import json
import multiprocessing as mp
import os
from pathlib import Path
import tempfile
import threading
import unittest

from experiments.arithmetic_dse.budget import Ledger, BudgetExceeded, POLICY
from experiments.arithmetic_dse.model_target_collection import _schedule, measurement_context


def context(tid):return {'target_platform':'asap7','admission_id':'wave','task_id':tid}


def child_claim(args,tid,ready,release,crash=False):
    ledger=Ledger(*args)
    with ledger.job(context(tid)):
        r=ledger.reserve('grt',60,4,'test',['true'],'unused',context=context(tid))
        ready.put(tid)
        if crash:
            ready.close();ready.join_thread();os._exit(19)
        release.wait(10)
        ledger.finish(r,{'exit_code':0,'walltime_s':1,'timed_out':False,'log':'unused.log','gnu_time':'missing'})


class ParallelBudget(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        p=json.loads(POLICY.read_text());p['resources'].update(parallel_jobs=4,threads_per_tool=4)
        (self.root/'policy.json').write_text(json.dumps(p));(self.root/'checkpoint.json').write_text('{"entries":[]}')
        self.args=(self.root/'ledger.json',self.root/'policy.json',self.root/'checkpoint.json')
        self.ledger=Ledger(*self.args)
    def tearDown(self):self.tmp.cleanup()

    def test_four_real_processes_and_fifth_rejected(self):
        ctx=mp.get_context('spawn');ready=ctx.Queue();release=ctx.Event()
        children=[ctx.Process(target=child_claim,args=(self.args,str(i),ready,release)) for i in range(4)]
        try:
            for child in children:child.start()
            self.assertEqual({ready.get(timeout=10) for _ in children},{'0','1','2','3'})
            self.assertEqual(self.ledger.summary()['pending'],4)
            self.assertEqual(self.ledger.summary()['CPU_time_s'],4*60*4)
            with self.assertRaises(BudgetExceeded),self.ledger.job(context('fifth')):pass
            with self.assertRaises(BudgetExceeded):self.ledger.reserve(None,10,2,'support',[],'unused')
        finally:
            release.set()
            for child in children:child.join(10)
        self.assertTrue(all(c.exitcode==0 for c in children))
        self.assertEqual(self.ledger.summary()['pending'],0)
        self.assertEqual(self.ledger.summary()['walltime_s'],4)

    def test_slots_cover_interstage_gaps_and_duplicate_identity(self):
        with ExitStack() as stack:
            for i in range(4):stack.enter_context(Ledger(*self.args).job(context(str(i))))
            self.assertEqual(self.ledger.summary()['pending'],0)
            with self.assertRaises(BudgetExceeded),self.ledger.job(context('fifth')):pass
        with self.assertRaises(BudgetExceeded),self.ledger.job(context('0')):pass

    def test_crashed_owner_blocks_all_new_work_without_refund(self):
        ctx=mp.get_context('spawn');ready=ctx.Queue();release=ctx.Event()
        child=ctx.Process(target=child_claim,args=(self.args,'dead',ready,release,True));child.start()
        ready.get(timeout=10);child.join(10)
        self.assertEqual(child.exitcode,19)
        with self.assertRaisesRegex(BudgetExceeded,'orphaned'),self.ledger.job(context('next')):pass
        self.assertEqual(self.ledger.summary()['pending'],1)
        self.assertEqual(self.ledger.summary()['walltime_s'],60)

    def test_own_leaf_serial_and_mismatched_context_rejected(self):
        with self.ledger.job(context('one')):
            with self.assertRaises(BudgetExceeded):self.ledger.reserve('grt',60,4,'test',[],'x',context=context('other'))
            r=self.ledger.reserve('synth',60,4,'test',[],'x',context=context('one'))
            with self.assertRaises(BudgetExceeded):self.ledger.reserve('grt',60,4,'test',[],'x',context=context('one'))
            self.ledger.finish(r,{'exit_code':1,'walltime_s':3,'timed_out':False,'log':'x.log','gnu_time':'missing'})
        self.assertEqual(self.ledger.summary()['synth'],1)
        self.assertEqual(self.ledger.summary()['pending'],0)


class Scheduling(unittest.TestCase):
    def test_dependencies_wait_for_completed_mapping(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);tasks={'dependent':{'id':'dependent','mapping_source_task':'source'},'source':{'id':'source','mapping_source_task':None}}
            order=[]
            def launch(tid):
                order.append(tid);p=folder/'runs'/tid;p.mkdir(parents=True)
                (p/'manifest.json').write_text('{"status":"completed"}');return tid
            _schedule(['dependent','source'],tasks,folder,4,launch,lambda r:None)
            self.assertEqual(order,['source','dependent'])

    def test_pause_drains_current_tasks_and_launches_no_more(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);barrier=threading.Barrier(4);started=[];finished=[]
            tasks={str(i):{'id':str(i),'mapping_source_task':None} for i in range(8)}
            def launch(tid):
                started.append(tid);barrier.wait(5);(folder/'PAUSE').touch();return tid
            _schedule(list(tasks),tasks,folder,4,launch,finished.append)
            self.assertEqual(len(started),4);self.assertEqual(set(started),set(finished))

    def test_failure_drains_and_stops_following_tasks(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);barrier=threading.Barrier(4);failed_seen=threading.Event();started=[];finished=[]
            tasks={str(i):{'id':str(i),'mapping_source_task':None} for i in range(8)}
            def launch(tid):
                started.append(tid);barrier.wait(5)
                if tid=='0':raise RuntimeError('failed')
                failed_seen.wait(.2);return tid
            with self.assertRaisesRegex(RuntimeError,'failed'):_schedule(list(tasks),tasks,folder,4,launch,finished.append)
            self.assertEqual(len(started),4);self.assertEqual(len(finished),3)

    def test_thread_variation_is_explicitly_train_only(self):
        m={'threads_per_tool':2,'mapping_context':{'tool_thread_controls':{k:2 for k in ['YOSYS_MAX_THREADS','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','NUM_CORES']},'sdc_period_ps':2250,'io_delay_max_ps':450}}
        t={'split':'train','target_roles':['absolute-2250'],'inherited_run':{'threads':2}}
        self.assertEqual(set(measurement_context(m,t)['tool_thread_controls'].values()),{4})
        with self.assertRaises(ValueError):measurement_context(m,{**t,'split':'test'})
        with self.assertRaises(ValueError):measurement_context(m,{'split':'train'})


if __name__=='__main__':unittest.main()
