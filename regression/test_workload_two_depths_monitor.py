from pathlib import Path
import os
import json
import signal
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_two_depths_monitor as monitor


class FatalMonitor(unittest.TestCase):
    def test_silence_and_recent_progress_do_not_trigger_cleanup(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'grt.log';log.write_text('[INFO DRT-0165] Start pin access.\n')
            os.utime(log,(100,100))
            self.assertIsNone(monitor.fatal_tail(log,1000))
            log.write_text('malloc_consolidate(): invalid chunk size\nSignal 6 received\nStack trace:\n')
            os.utime(log,(950,950))
            self.assertIsNone(monitor.fatal_tail(log,1000))
            os.utime(log,(800,800))
            self.assertEqual(monitor.fatal_tail(log,1000)['marker'],'malloc_consolidate(): invalid chunk size')

    def test_allocator_diagnostic_without_terminal_crash_is_not_enough(self):
        with tempfile.TemporaryDirectory() as tmp:
            log=Path(tmp)/'grt.log';log.write_text('double free or corruption\n')
            os.utime(log,(100,100))
            self.assertIsNone(monitor.fatal_tail(log,1000))

    def test_only_exact_admitted_runtime_command_matches(self):
        batch=Path('/task/backend/matrix-test');task='test'
        argv=['/usr/bin/python3','-u','-m','experiments.arithmetic_dse.workload_nine_runtime',
              'task','--root',str(batch),'--task-id',task]
        self.assertTrue(monitor.exact_wrapper(argv,batch,task))
        self.assertFalse(monitor.exact_wrapper(argv,batch,'different'))
        self.assertFalse(monitor.exact_wrapper(argv,Path('/other'),task))
        self.assertFalse(monitor.exact_wrapper(['sh','-c',' '.join(argv)],batch,task))

    def test_normal_long_stage_never_signals_or_retries(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);run=root/'backend/matrix-test/runs/test';run.mkdir(parents=True)
            log=run/'grt.log';log.write_text('[INFO RSZ] continuing timing repair\n')
            os.utime(log,(100,100))
            state=dict(jobs=[dict(id='job',status='active',admission_id='matrix-test',task_id='test')],
                entries=[dict(id='entry',status='reserved',job_id='job',output=str(run/'grt'))])
            with patch.object(monitor.os,'kill') as kill:
                self.assertEqual(monitor.settle_confirmed_aborts(root,state,1000),[])
                kill.assert_not_called()

    def test_confirmed_abort_signals_only_unique_wrapper_once(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);batch=root/'backend/matrix-test';run=batch/'runs/test';run.mkdir(parents=True)
            log=run/'grt.log';log.write_text('malloc_consolidate(): invalid chunk size\nSignal 6 received\nStack trace:\n')
            os.utime(log,(100,100))
            state=dict(jobs=[dict(id='job',status='active',admission_id='matrix-test',task_id='test')],
                entries=[dict(id='entry',status='reserved',job_id='job',output=str(run/'grt'))])
            ledger=root/'usage.json';ledger.write_text(json.dumps(state))
            proc=root/'proc';p=proc/'123';p.mkdir(parents=True)
            argv=['python3','-u','-m','experiments.arithmetic_dse.workload_nine_runtime',
                  'task','--root',str(batch),'--task-id','test']
            (p/'cmdline').write_bytes(b'\0'.join(s.encode() for s in argv)+b'\0')
            fields=['S']+['0']*19;fields[19]='456'
            (p/'stat').write_text('123 (python3) '+' '.join(fields))
            with patch.object(monitor.runtime.budget,'LEDGER',ledger),patch.object(monitor.runtime,'verify',
                return_value=dict(tasks=[dict(id='test')])),patch.object(monitor.os,'kill') as kill:
                incidents=monitor.settle_confirmed_aborts(root,state,1000,proc)
                self.assertEqual(len(incidents),1)
                kill.assert_called_once_with(123,signal.SIGTERM)
                self.assertFalse(incidents[0]['automatic_retry'])
                self.assertEqual(monitor.settle_confirmed_aborts(root,state,1000,proc),[])
                self.assertEqual(kill.call_count,1)


if __name__=='__main__':
    unittest.main()
