#!/usr/bin/env python3
"""Check report rejection, feasibility, area accounting and timeout handling.

These checks use synthetic reports and a local child process, without PPA tools.
"""
import os
import json
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.backend import run_command, stage_metrics
from experiments.arithmetic_dse.characterization import target_coverage


class BackendContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='arithmetic-backend-test-')
        self.directory = Path(self.temp.name)
        self.cells = {'DFF':{'area_um2':2.0,'sequential':True},
                      'AND':{'area_um2':1.0,'sequential':False}}
        self.reports = {'units':' time 1ps\n capacitance 1fF\n distance 1um\n',
                        'setup':'worst slack max 10.000000\n',
                        'hold':'worst slack min 0.500000\n',
                        'setup_tns':'tns max 0.000000\n', 'hold_tns':'tns min 0.000000\n',
                        'period':'core_clk period_min = 1490.00 fmax = 671.14\n',
                        'coverage':'', 'cells':'DFF\t2\t2.0\t0\tCORE\nAND\t3\t1.0\t0\tCORE\n'
                            'TAPCELL_TEST\t1\t0.5\t0\tCORE_WELLTAP\n'
                            'FILLER_TEST\t4\t0.5\t1\tCORE_SPACER\n'}
        self.write_reports()

    def tearDown(self):
        self.temp.cleanup()

    def write_reports(self):
        for key, value in self.reports.items():
            (self.directory/f'vulsim_grt_{key}.{ "tsv" if key == "cells" else "rpt"}').write_text(value)

    def metrics(self):
        return stage_metrics(self.directory, 'grt', self.cells, 1500)

    def test_area_and_feasibility(self):
        result = self.metrics()
        self.assertEqual(result['cell_area_um2'], 7.5)  # includes tap, excludes fillers
        self.assertEqual(result['functional_cell_area_um2'], 7)
        self.assertEqual(result['sequential_area_um2'], 4)
        self.assertEqual(result['excluded_filler_area_um2'], 2)
        self.assertTrue(result['measured_feasibility'])

    def test_grt_hold_is_reported_without_changing_setup_feasibility(self):
        self.reports['hold'] = 'worst slack min -0.000001\n'
        self.write_reports()
        result = self.metrics()
        self.assertTrue(result['measured_feasibility'])
        self.assertFalse(result['sta_feasibility'])
        self.assertTrue(result['hold_review_required'])
        self.assertEqual(result['feasibility_scope'], 'TT_setup_only')

    def test_final_hold_remains_a_gate(self):
        self.reports['hold'] = 'worst slack min -0.000001\n'
        self.write_reports()
        for path in self.directory.glob('vulsim_grt_*'):
            (self.directory/path.name.replace('grt','final')).write_bytes(path.read_bytes())
        self.assertFalse(stage_metrics(self.directory, 'final', self.cells, 1500)['measured_feasibility'])

    def test_hold_review_band_is_not_signoff(self):
        result = self.metrics()
        self.assertTrue(result['hold_review_required'])
        self.assertFalse(result['multi_corner_signoff'])
        self.reports['hold'] = 'worst slack min 5.000000\n'
        self.write_reports()
        self.assertFalse(self.metrics()['hold_review_required'])

    def test_target_axis_rejects_unmeasured_and_outside_points(self):
        self.assertEqual(target_coverage([1000,1500,2000], 1500)['status'],'covered')
        for target in [900,1250,2100]:
            self.assertEqual(target_coverage([1000,1500,2000],target)['status'],'uncovered')
        with self.assertRaises(ValueError):
            target_coverage([1000],float('nan'))

    def test_unconstrained_endpoint_is_not_feasible(self):
        self.reports['coverage'] = 'Warning: There is 1 unconstrained endpoint.\n'
        self.write_reports()
        self.assertFalse(self.metrics()['measured_feasibility'])

    def test_nan_or_missing_report_is_rejected(self):
        self.reports['hold'] = 'worst slack min nan\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()
        (self.directory/'vulsim_grt_hold.rpt').unlink()
        with self.assertRaises(FileNotFoundError):
            self.metrics()

    def test_unit_mismatch_is_rejected(self):
        self.reports['units'] = ' time 1ns\n capacitance 1pF\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()

    def test_unknown_master_or_area_mismatch_is_rejected(self):
        self.reports['cells'] = 'UNKNOWN\t1\t1.0\t0\tCORE\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()
        self.reports['cells'] = 'DFF\t1\t2000000\t0\tCORE\n'
        self.write_reports()
        with self.assertRaises(ValueError):
            self.metrics()

    def test_timeout_retains_failure_record(self):
        result = run_command([sys.executable,'-c','import time; time.sleep(5)'],
                             self.directory, 'timeout', 0.1, os.environ.copy())
        self.assertTrue(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)
        self.assertTrue((self.directory/'timeout.command.json').exists())
        self.assertTrue(Path(result['log']).exists())

    def test_memory_cap_retains_failure_record(self):
        result = run_command([sys.executable,'-c','import time; data = bytearray(16*1024*1024); time.sleep(5)'],
                             self.directory, 'memory', 3, os.environ.copy(), memory_limit_mib=8)
        self.assertTrue(result['memory_limit_exceeded'])
        self.assertFalse(result['timed_out'])
        self.assertNotEqual(result['exit_code'], 0)

    def nested_command(self, ignore_term=False, allocate_mib=0):
        pidfile = self.directory/'worker.json'
        worker = ("import os,json,time,signal; from pathlib import Path; "
                  +( "signal.signal(signal.SIGTERM,signal.SIG_IGN); " if ignore_term else '')
                  +f"data=bytearray({allocate_mib}*1024*1024); "
                  +f"Path({str(pidfile)!r}).write_text(json.dumps({{'pid':os.getpid(),'pgid':os.getpgrp()}})); time.sleep(20)")
        inner = ("from experiments.arithmetic_dse.backend import run_command; import os,sys; from pathlib import Path; "
                 +f"run_command([sys.executable,'-c',{worker!r}],Path({str(self.directory)!r}),'inner',15,os.environ.copy())")
        env = os.environ.copy()
        env['PYTHONPATH'] = str(ROOT)
        return [sys.executable,'-c',inner], env, pidfile

    def assert_worker_dead(self, pidfile):
        self.assertTrue(pidfile.exists(), 'nested worker must start before cancellation')
        pid = json.loads(pidfile.read_text())['pid']
        try:
            state = Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()[0]
        except FileNotFoundError:
            state = 'gone'
        if state not in ['gone','Z']:
            try:
                os.kill(pid,signal.SIGKILL)
            except ProcessLookupError:
                pass
        self.assertIn(state, ['gone','Z'], f'worker {pid} survived cancellation')

    def test_outer_timeout_kills_nested_session_and_term_ignoring_worker(self):
        command, env, pidfile = self.nested_command(ignore_term=True)
        result = run_command(command,self.directory,'nested-timeout',1,env)
        self.assertTrue(result['timed_out'])
        self.assertGreater(result['cleanup']['kill_sent'],0)
        self.assertEqual(result['cleanup']['remaining_live_pids'],[])
        self.assert_worker_dead(pidfile)

    def test_outer_memory_limit_counts_nested_session(self):
        command, env, pidfile = self.nested_command(allocate_mib=32)
        result = run_command(command,self.directory,'nested-memory',5,env,memory_limit_mib=24)
        self.assertTrue(result['memory_limit_exceeded'])
        self.assert_worker_dead(pidfile)

    def test_external_term_cleans_nested_tool(self):
        command, env, pidfile = self.nested_command()
        wrapper = ("from experiments.arithmetic_dse.backend import run_command; import os; from pathlib import Path; "
                   +f"run_command({command!r},Path({str(self.directory)!r}),'cancelled',10,os.environ.copy())")
        process = subprocess.Popen([sys.executable,'-c',wrapper],env=env)
        try:
            deadline = time.monotonic()+3
            while not pidfile.exists() and time.monotonic() < deadline:
                time.sleep(0.02)
            self.assertTrue(pidfile.exists())
            process.send_signal(signal.SIGTERM)
            process.wait(timeout=6)
            result = json.loads((self.directory/'cancelled.command.json').read_text())
            self.assertEqual(result['cancelled_signal'],signal.SIGTERM)
            self.assertNotEqual(result['exit_code'],0)
            self.assert_worker_dead(pidfile)
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()

    def test_fast_exiting_parent_cannot_leave_detached_worker(self):
        pidfile = self.directory/'detached.json'
        worker = ("import os,json,time; from pathlib import Path; "
                  +f"Path({str(pidfile)!r}).write_text(json.dumps({{'pid':os.getpid()}})); time.sleep(20)")
        parent = ("import subprocess,sys,time\nfrom pathlib import Path\n"
                  +f"subprocess.Popen([sys.executable,'-c',{worker!r}],start_new_session=True)\n"
                  +f"while not Path({str(pidfile)!r}).exists(): time.sleep(0.01)\n")
        command = [sys.executable,'-c',parent]
        result = run_command(command,self.directory,'orphan',5,os.environ.copy())
        self.assertTrue(result['unexpected_live_descendants'])
        self.assertNotEqual(result['exit_code'],0)
        self.assert_worker_dead(pidfile)


if __name__ == '__main__':
    unittest.main()
