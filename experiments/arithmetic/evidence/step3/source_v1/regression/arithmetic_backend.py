#!/usr/bin/env python3
"""Check report rejection, feasibility, area accounting and timeout handling.

These checks use synthetic reports and a local child process, without PPA tools.
"""
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.backend import run_command, stage_metrics


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

    def test_hold_failure_is_not_feasible(self):
        self.reports['hold'] = 'worst slack min -0.000001\n'
        self.write_reports()
        self.assertFalse(self.metrics()['measured_feasibility'])

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


if __name__ == '__main__':
    unittest.main()
