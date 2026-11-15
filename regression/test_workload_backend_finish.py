"""The corrected readout must share the physical implementation's job lease."""
from contextlib import contextmanager
from pathlib import Path
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_backend_finish as finish


class SingleJobReadout(unittest.TestCase):
    def test_clock_runs_before_implementation_job_is_released(self):
        events=[]
        class FakeLedger:
            active=False
            @contextmanager
            def job(self,ctx):
                if self.active:raise AssertionError('nested job lease')
                self.active=True;events.append('acquire')
                try:yield 'job'
                finally:self.active=False;events.append('release')
        ledger=FakeLedger()
        def clock(root,task,l):
            self.assertIs(l,ledger);self.assertTrue(l.active);events.append('clock');return task['id']
        task=dict(id='example',period_ps=1000,abc_target_ps=1000,rtl='/frozen/workload.sv')
        parent=dict(id='parent',selection_freeze='/frozen/selection.json')
        with patch.object(finish,'verify',return_value=({'id':'correction'},parent)), \
             patch.object(finish,'ComparisonLedger',return_value=ledger), \
             patch('experiments.arithmetic_dse.backend._evaluate',return_value=0), \
             patch.object(finish,'clock',side_effect=clock):
            self.assertEqual(finish.run_task(Path('/frozen'),task),'example')
        self.assertEqual(events,['acquire','clock','release'])


if __name__=='__main__':unittest.main()
