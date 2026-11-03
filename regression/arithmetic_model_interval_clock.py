"""Fail-closed target, IO, mapping reuse and path accounting checks; no EDA."""
import copy
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from experiments.arithmetic_dse import model_interval_clock as clock


class ClockDiagnosisContracts(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.rtl = self.root / 'input.sv'
        self.rtl.write_text('module ModelBundle; endmodule\n')
        self.contract = self.root / 'contract.json'
        self.contract.write_text('{}\n')
        self.admission = self.root / 'admission.json'
        self.t = {'id': 'case-reference', 'variant': 'reference', 'case': 'case',
                  'platform': 'asap7', 'profile_sha256': 'profile', 'top': 'ModelBundle',
                  'stage': 'grt', 'period_ps': 1500, 'abc_target_ps': 1500,
                  'io_delay_max_ps': 300, 'rtl_sha256': clock.sha(self.rtl),
                  'sample_contract_sha256': clock.sha(self.contract), 'resume_synth_from': None}
        self.a = {'id': 'fixture', 'purpose': clock.PURPOSE, 'not_training': True,
                  'automatic_retries': 0, 'resources': clock.read(clock.CONFIG)['resources'],
                  'tasks': [self.t]}
        self.args = SimpleNamespace(admission=self.admission, admission_id='fixture', task_id='case-reference',
                                    platform='asap7', top='ModelBundle', stage='grt', period_ps=1500,
                                    abc_target_ps=1500, io_delay_max_ps=300, threads=2, memory_limit_mib=8192,
                                    synth_timeout_s=300, route_timeout_s=1200, period_role='resource_trial',
                                    budget_purpose='characterization', sample_contract=self.contract,
                                    rtl=self.rtl, resume_synth_from=None)
        self.save()

    def save(self):
        self.admission.write_text(json.dumps(self.a))

    def test_reference_targets_are_fixed_once_with_nonoverlapping_overhead(self):
        self.assertEqual(clock.target_points(420.25, 99.5), [
            ('sdc-0.8', 1500, 436, True), ('sdc-1.0', 1500, 520, True),
            ('sdc-1.5', 1500, 730, True), ('abc-0.8', 337, 520, False),
            ('abc-1.5', 631, 520, False)])
        for d, h in ((0, 1), (float('nan'), 1), (1, float('inf')), (1, -100)):
            with self.assertRaises(ValueError): clock.target_points(d, h)

    def test_wrong_io_abc_sdc_resource_or_role_rejected(self):
        with patch.object(clock, 'verify_sources'):
            clock.task(self.args)
            for key, value in [('io_delay_max_ps', None), ('io_delay_max_ps', 299), ('period_ps', 1000),
                               ('abc_target_ps', 750), ('threads', 4), ('route_timeout_s', 3600),
                               ('memory_limit_mib', 32768), ('period_role', 'frozen_case_target'),
                               ('budget_purpose', 'final_evaluation')]:
                args = copy.copy(self.args)
                setattr(args, key, value)
                with self.subTest(key=key, value=value), self.assertRaises(ValueError): clock.task(args)

    def test_sdc_requires_mapping_reuse_and_abc_requires_new_mapping(self):
        with patch.object(clock, 'verify_sources'):
            self.t['variant'] = 'sdc-1.0'
            self.save()
            with self.assertRaises(ValueError): clock.task(self.args)
            self.t['resume_synth_from'] = str(self.root.resolve())
            self.args.resume_synth_from = self.root
            self.save()
            clock.task(self.args)
            self.t['variant'] = 'abc-0.8'
            self.save()
            with self.assertRaises(ValueError): clock.task(self.args)

    def test_changed_source_or_sample_contract_rejected(self):
        with patch.object(clock, 'verify_sources'):
            self.rtl.write_text('changed RTL')
            with self.assertRaises(ValueError): clock.task(self.args)
            self.t['rtl_sha256'] = clock.sha(self.rtl)
            self.save()
            self.contract.write_text('changed boundary')
            with self.assertRaises(ValueError): clock.task(self.args)

    def test_pending_leaf_and_global_future_reserve_are_enforced(self):
        totals = {'pending': 1, 'synth': 0, 'grt': 0, 'walltime_s': 0, 'CPU_time_s': 0}
        with self.assertRaisesRegex(ValueError, 'pending'): clock.check_funding(totals, 24, self.root)
        totals.update(pending=0, synth=4090)
        with self.assertRaisesRegex(ValueError, 'call reserve'): clock.check_funding(totals, 24, self.root)
        totals.update(synth=0, walltime_s=168*3600-100)
        with self.assertRaisesRegex(ValueError, 'time reserve'): clock.check_funding(totals, 24, self.root)

    def test_cell_wire_accounting_starts_at_Q_excludes_clock_points(self):
        path = self.root / 'points.tsv'
        path.write_text('launch/CLK\t2\nlaunch/Q\t12\ngate/A\t13\ngate/Y\t33\ncapture/D\t36\n')
        label = {'start_pin': 'launch/Q', 'end_pin': 'capture/D', 'data_delay_ps': 24}
        result = clock.point_delays(path, label, 1)
        self.assertEqual((result['cell_delay_ps'], result['wire_delay_ps']), (20, 4))
        label['data_delay_ps'] = 34
        with self.assertRaises(ValueError): clock.point_delays(path, label, 1)

    def test_existing_freeze_never_overwritten(self):
        with self.assertRaisesRegex(ValueError, 'preserve existing'):
            clock.new_write(self.admission, {'changed': True})

    def test_explicit_clock_representation_preserves_internal_time_not_tolerance(self):
        actual = clock.represented_clock_ps(1021)
        self.assertEqual(actual, 1020.9999389648438)
        self.assertEqual(format(actual, '.4f'), '1020.9999')
        self.assertEqual(clock.f32(actual*clock.f32(1e-12)), clock.f32(1021*clock.f32(1e-12)))
        self.assertNotEqual(clock.f32(1020*clock.f32(1e-12)), clock.f32(1021*clock.f32(1e-12)))


if __name__ == '__main__': unittest.main()
