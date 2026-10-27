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
from experiments.arithmetic_dse.characterization import sensitivity_observation, mapped_netlist_hash
from experiments.arithmetic_dse.budget import Ledger, BudgetExceeded, plan_cost, planning_status
from concurrent.futures import ThreadPoolExecutor


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

    def test_identical_scalar_metrics_do_not_prove_insensitivity_or_gap_coverage(self):
        point = {'abc_target_ps':500, 'comparison_identity_sha256':'kernel-1',
                 'mapped_netlist_sha256':'netlist-1', 'cell_area_um2':7,
                 'functional_cell_area_um2':6, 'sequential_area_um2':2,
                 'minimum_clock_period_ps':900}
        result = sensitivity_observation([point, dict(point,abc_target_ps=800)])
        self.assertEqual(result['status'],'equal_at_measured_points')
        self.assertFalse(result['early_exit_authorized'])
        self.assertFalse(result['family_target_insensitive'])
        self.assertEqual(target_coverage(result['measured_targets_ps'],1000)['status'],'uncovered')
        different = sensitivity_observation([point,dict(point,abc_target_ps=800,mapped_netlist_sha256='netlist-2')])
        self.assertEqual(different['status'],'differences_observed')

    def test_netlist_hash_ignores_locations_but_preserves_wiring(self):
        a = '/* Generated by Yosys version A */\n(* src = "first.sv:1" *)\nassign y = a;\n'
        b = '/* Generated by Yosys version B */\n(* src = "second.sv:2" *)\nassign y = a;\n'
        self.assertEqual(mapped_netlist_hash(a),mapped_netlist_hash(b))
        self.assertNotEqual(mapped_netlist_hash(a),mapped_netlist_hash(b.replace('y = a','y = b')))

    def budget_ledger(self):
        policy = self.directory/'policy.json'
        policy.write_text(json.dumps({'resources':{'max_synthesis_calls':2,'max_global_route_calls':1,
            'max_detailed_route_calls':1,'max_global_walltime_h':1,'max_tool_CPU_time_h':1}}))
        checkpoint = self.directory/'checkpoint.json'
        checkpoint.write_text(json.dumps({'entries':[{'id':'history','stage':'synth', 'status':'failed',
            'walltime_s':3,'CPU_time_s':2}]}))
        return Ledger(self.directory/'ledger.json',policy,checkpoint)

    def test_budget_reserves_before_launch_and_failure_stays_charged(self):
        ledger = self.budget_ledger()
        reservation = ledger.reserve('synth',10,2,'prototype',['missing-tool'],self.directory)
        self.assertEqual(ledger.summary()['synth'],2)
        self.assertEqual(ledger.summary()['pending'],1)
        ledger.finish(reservation,{'exit_code':1,'walltime_s':1,'timed_out':False,
                                  'log':str(self.directory/'x.log'),'gnu_time':str(self.directory/'missing')})
        self.assertEqual(ledger.summary()['synth'],2)
        self.assertEqual(ledger.summary()['CPU_time_s'],22)  # unknown CPU keeps reservation
        with self.assertRaises(BudgetExceeded):
            Ledger(ledger.path,ledger.policy,ledger.checkpoint).reserve('synth',1,1,'retry',[],self.directory)

    def test_concurrent_admission_cannot_overspend_and_pending_is_not_refunded(self):
        ledger = self.budget_ledger()
        def reserve(_):
            try:
                return ledger.reserve('synth',10,2,'prototype',[],self.directory)
            except BudgetExceeded:
                return None
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(reserve,range(4)))
        self.assertEqual(sum(r is not None for r in results),1)
        self.assertEqual(ledger.summary()['pending'],1)
        with self.assertRaises(BudgetExceeded):
            Ledger(ledger.path,ledger.policy,ledger.checkpoint).reserve('grt',10,2,'prototype',[],self.directory)

    def test_snapshot_time_does_not_double_count_synthesis_and_policy_cannot_reset_usage(self):
        ledger = self.budget_ledger()
        resource = self.directory/'x.resources.txt'
        resource.write_text('User time (seconds): 0.20\nSystem time (seconds): 0.10\n')
        reservation = ledger.reserve(None,10,2,'prototype',['snapshot'],self.directory)
        ledger.finish(reservation,{'exit_code':0,'walltime_s':1,'timed_out':False,
                                  'log':str(self.directory/'x.log'),'gnu_time':str(resource)})
        self.assertEqual(ledger.summary()['synth'],1)
        self.assertEqual(ledger.summary()['walltime_s'],4)
        self.assertAlmostEqual(ledger.summary()['CPU_time_s'],2.3)
        ledger.policy.write_text('{}')
        with self.assertRaises(ValueError):
            ledger.summary()

    def test_budget_includes_six_targets_and_unfrozen_case_supplements(self):
        families = {str(i):[500,800,1000,1250,1500,2000] for i in range(19)}
        plan = plan_cost(families,None,historical={'synth':13,'grt':5,'final':4},
                         prototype_reserve=36,repeat_reserve=8,retry_reserve=16,targets_frozen=False)
        self.assertEqual(plan['base_characterization'],114)
        self.assertEqual(plan['supplemental_characterization'],171)
        self.assertEqual(plan['requested_calls'],{'synth':446,'grt':420,'final':44})
        policy = {'max_synthesis_calls':128,'max_global_route_calls':96,'max_detailed_route_calls':28}
        self.assertEqual(planning_status(plan,policy)['status'],'blocked')
        exact = plan_cost(families,[1000]*8+[1100],historical={'synth':0,'grt':0,'final':0},
                         prototype_reserve=0,repeat_reserve=0,retry_reserve=0,targets_frozen=True)
        self.assertEqual(exact['supplemental_characterization'],19)

    def test_wall_budget_rejects_before_creating_a_reservation(self):
        ledger = self.budget_ledger()
        with self.assertRaises(BudgetExceeded):
            ledger.reserve('grt',3600,2,'prototype',[],self.directory)
        self.assertEqual(ledger.summary()['grt'],0)

    def test_removing_live_ledger_cannot_restore_checkpoint_budget(self):
        ledger = self.budget_ledger()
        self.assertEqual(ledger.summary()['synth'],1)
        ledger.path.unlink()
        with self.assertRaises(ValueError):
            ledger.summary()

    def test_sampled_CPU_allowance_cancels_busy_tool(self):
        result = run_command([sys.executable,'-c','while True: pass'],self.directory,
                             'cpu-limit',5,os.environ.copy(),cpu_limit_s=0.05)
        self.assertTrue(result['CPU_limit_exceeded'])
        self.assertNotEqual(result['exit_code'],0)
        self.assertEqual(result['cleanup']['remaining_live_pids'],[])

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
