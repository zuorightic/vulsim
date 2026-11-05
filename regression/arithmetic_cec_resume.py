"""Fail-closed coverage and exact proof consumption for structural CTS CEC."""
import copy
import tempfile
from pathlib import Path
import unittest

from experiments.arithmetic_dse.model_m2_cec import cut_boundary, aig_map, check_result, invert_aig_output
from experiments.arithmetic_dse.model_m2_cec_resume import render_cts


class StructuralCEC(unittest.TestCase):
    def design(self):
        return {'modules': {
            'top': {'ports': {'a': {'direction': 'input', 'bits': [2]}, 'y': {'direction': 'output', 'bits': [4]}},
                    'cells': {'state': {'type': 'ff', 'connections': {'CLK': [2], 'D': [3], 'Q': [4]}}}},
            'ff': {'ports': {'CLK': {'direction': 'input', 'bits': [2]}, 'D': {'direction': 'input', 'bits': [3]},
                             'Q': {'direction': 'output', 'bits': [4]}}, 'cells': {'ff': {'type': '$_DFF_P_'}}}}}

    def test_all_register_inputs_are_obligations(self):
        d = self.design(); boundary, states, counts = cut_boundary(d, 'top')
        self.assertEqual(counts, {'input': 2, 'output': 3})
        self.assertEqual(boundary['state:state:CLK']['direction'], 'output')
        self.assertEqual(boundary['state:state:D']['direction'], 'output')
        self.assertEqual(boundary['state:state:Q']['direction'], 'input')
        self.assertEqual(d['modules']['top']['cells'], {})

    def test_unknown_cell_rejected(self):
        d = self.design(); d['modules']['top']['cells']['unknown'] = {'type': 'missing'}
        with self.assertRaisesRegex(ValueError, 'missing cell model'): cut_boundary(d, 'top')

    def test_no_sequential_boundary_rejected(self):
        d = self.design(); d['modules']['ff']['cells'] = {}
        with self.assertRaisesRegex(ValueError, 'empty sequential'): cut_boundary(d, 'top')

    def test_inout_rejected(self):
        d = self.design(); d['modules']['top']['ports']['a']['direction'] = 'inout'
        with self.assertRaises(ValueError): cut_boundary(d, 'top')

    def test_missing_and_inconsistent_conclusions_rejected(self):
        for s in ('', 'Starting solver', 'Networks are equivalent.\nError: failed',
                  'Networks are equivalent.\nNetworks are NOT EQUIVALENT'):
            with self.subTest(s=s), self.assertRaises(ValueError): check_result(s, True)
        check_result('Networks are equivalent.', True)
        check_result('Networks are NOT EQUIVALENT after structural hashing.\nVerification failed for at least 1 outputs', False)
        with self.assertRaises(ValueError): check_result('Networks are equivalent.', False)

    def test_aig_map_requires_all_unique_positions(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'map'; p.write_text('input 0 0 a\noutput 0 0 y\n')
            self.assertEqual(len(aig_map(p, 1, 1)), 2)
            for text in ('input 0 0 a\n', 'input 0 0 a\noutput 1 0 y\n', 'input 0 0 a\noutput 0 0 y\noutput 1 0 y\n'):
                p.write_text(text)
                with self.assertRaises(ValueError): aig_map(p, 1, 1)

    def test_mutation_changes_exactly_one_output_literal(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td)/'a'; q = Path(td)/'b'
            p.write_bytes(b'aig 2 1 0 2 1\n2\n4\n\x02\x00i0 a\no0 y\no1 d\nc\n')
            invert_aig_output(p, q, 1)
            self.assertEqual(q.read_bytes(), b'aig 2 1 0 2 1\n2\n5\n\x02\x00i0 a\no0 y\no1 d\nc\n')

    def test_replay_replaces_only_lec_call(self):
        original = 'prefix\n    run_lec_test 4_rsz 4_before_rsz_lec.v 4_after_rsz_lec.v\nsuffix'
        rendered = render_cts(original, Path('/proof'), Path('/wrapper'), False)
        self.assertTrue(rendered.startswith('prefix\n')); self.assertTrue(rendered.endswith('\nsuffix'))
        self.assertNotIn('run_lec_test', rendered)
        self.assertIn('4_before_rsz_lec.v', rendered); self.assertIn('4_after_rsz_lec.v', rendered)
        with self.assertRaises(ValueError): render_cts('unsupported', Path('/proof'), Path('/wrapper'), False)


if __name__ == '__main__': unittest.main()
