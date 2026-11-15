"""A concurrent admission race may wait, but may not repeat physical work."""
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import workload_wave as wave
from experiments.arithmetic_dse.budget import BudgetExceeded


class SlotWait(unittest.TestCase):
    def test_slot_race_waits_then_runs_unclaimed_task(self):
        with tempfile.TemporaryDirectory() as d:
            with patch.object(wave, 'run_task', side_effect=[
                    BudgetExceeded('all backend job slots occupied'), 'done']) as run, \
                 patch.object(wave, 'verify', return_value=({}, dict(id='parent'))), \
                 patch.object(wave, 'read', return_value=dict(entries=[], jobs=[])):
                sleeps = []
                self.assertEqual(wave.wait_task(Path(d), dict(id='x'), sleeps.append), 'done')
                self.assertEqual(run.call_count, 2)
                self.assertEqual(sleeps, [2])

    def test_recorded_leaf_or_job_cannot_be_repeated(self):
        for key in ('entries', 'jobs'):
            with self.subTest(key=key), tempfile.TemporaryDirectory() as d:
                state = dict(entries=[], jobs=[])
                state[key] = [dict(admission_id='parent', task_id='x')]
                with patch.object(wave, 'run_task', side_effect=BudgetExceeded('all backend job slots occupied')), \
                     patch.object(wave, 'verify', return_value=({}, dict(id='parent'))), \
                     patch.object(wave, 'read', return_value=state):
                    with self.assertRaisesRegex(ValueError, 'cannot restart'):
                        wave.wait_task(Path(d), dict(id='x'), lambda _: self.fail('must not wait'))

    def test_tool_or_other_budget_failure_never_retried(self):
        for error in (ValueError('synth: timeout'), BudgetExceeded('global budget exhausted')):
            with self.subTest(error=str(error)), patch.object(wave, 'run_task', side_effect=error) as run:
                with self.assertRaises(type(error)):
                    wave.wait_task(Path('/unused'), dict(id='x'), lambda _: self.fail('must not wait'))
                self.assertEqual(run.call_count, 1)


if __name__ == '__main__':
    unittest.main()
