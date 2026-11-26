"""Saved pre-migration predictions exercise both process models and the owner DAG."""
import gzip
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.autopipe import resources
from tools.autopipe import workload_diagnostic
from tools.autopipe import transition_incidence_features_v10 as reduction_features
from tools.autopipe.resources import runtime
from tools.autopipe.workload_demand import Graph


class FrozenPredictionTests(unittest.TestCase):
    def test_asap7_diagnostic_sub_and_compare_boundary(self):
        contract = runtime('asap7').contract
        for name in ('Sub', 'Compare'):
            with self.subTest(family=name):
                shell = contract['families'][name]
                self.assertAlmostEqual(shell['H_char_ps'], 114.844695)
                self.assertEqual(shell['alpha'], 1.0)
                self.assertEqual(shell['sources'], 55)
                self.assertFalse(shell['qualified'])

    def test_state_projection_uses_valid_graph_node(self):
        graph = Graph(dict(version='prospective-workload-graph-v1', nodes=[
            dict(id=0, width=7), dict(id=1, width=1)], ports=[
            dict(name='vul_port_iv', input=True, width=7, nodes=[0]),
            dict(name='__vul_port_iv', input=True, width=1, nodes=[1])]))
        state = dict(valid_input_rtl_name='vul_port_iv', slots=[
            dict(valid=True, origin=1, variable_bits=1, external_capture=True)])
        projection = workload_diagnostic.state_projection(graph, state, 1, 1200)
        self.assertEqual(projection['input_widths'], [7])
        self.assertEqual(projection['total_FF_bits'], 9)

    def test_vul_workload_arithmetic_matches_bundled_source(self):
        for name in ('mul128', 'dot16', 'horner64', 'barrett64', 'karatsuba256', 'montgomery256', 'ntt8x64'):
            with self.subTest(workload=name):
                folder = resources.EXAMPLES / name
                source = (folder / 'source.cpp').read_text()
                vul = (folder / 'TopModule.vul').read_text()
                original = re.search(r'^void workload_top\(\) \{\n(.*?)^\}', source, re.M | re.S)
                wrapped = re.search(r'^PIPELINE\([\s\S]*?^\) \{\n(.*?)^\}', vul, re.M | re.S)
                self.assertIsNotNone(original)
                self.assertIsNotNone(wrapped)
                self.assertEqual(original[1], re.sub(r'^\s*//[^\n]*\n', '', wrapped[1], flags=re.M))

    def test_g_member_rejects_separate_billing(self):
        data = json.loads(gzip.decompress(Path(__file__).with_name('frozen_predictions.json.gz').read_bytes()))
        fixture = next(f for f in data['fixtures'] if f['platform']=='asap7' and f['owners']['G_regions'])
        model = runtime('asap7')
        owners = fixture['owners']
        group = owners['G_regions'][0]
        internal = next(i for i in group['members'] if i != group['root'])
        for kind in ('operators', 'functional_logic'):
            with self.subTest(kind=kind):
                duplicate = dict(owners['operators'][0], node=internal) if kind=='operators' else internal
                invalid = dict(owners, **{kind: owners[kind]+[duplicate]})
                with self.assertRaisesRegex(ValueError, 'overlapping G member'):
                    model.evaluate(Graph(fixture['graph']), fixture['view'], fixture['state'], invalid)

    def test_saved_complete_candidate_predictions(self):
        data = json.loads(gzip.decompress(Path(__file__).with_name('frozen_predictions.json.gz').read_bytes()))
        self.assertEqual(data['schema'], 'frozen-v10-prediction-regression-v1')
        self.assertEqual(len(data['fixtures']), 13)
        for fixture in data['fixtures']:
            with self.subTest(candidate=fixture['id']):
                model = runtime(fixture['platform'])
                graph = Graph(fixture['graph'])
                queries = fixture['owner_queries']
                kwargs = dict(owner_queries={int(k):v for k,v in queries.items()}) if queries else {}
                # Parameters and prospective graphs are already in memory.
                # No physical labels, external files or tools may supply a price.
                with patch('builtins.open', side_effect=AssertionError('online file read')), \
                     patch('io.open', side_effect=AssertionError('online pathlib read')), \
                     patch('subprocess.Popen', side_effect=AssertionError('online backend call')):
                    actual = model.evaluate(graph, fixture['view'], fixture['state'], fixture['owners'], **kwargs)
                self.compare(fixture['expected'], actual)
                Graph.origins.cache_clear()
                Graph.roots.cache_clear()

    def compare(self, expected, actual):
        if isinstance(expected, dict):
            for key, value in expected.items():
                self.assertIn(key, actual)
                self.compare(value, actual[key])
        elif isinstance(expected, list):
            self.assertEqual(len(expected), len(actual))
            for a, b in zip(expected, actual):
                self.compare(a, b)
        elif isinstance(expected, (int, float)) and not isinstance(expected, bool):
            self.assertTrue(math.isclose(expected, actual, rel_tol=1e-12, abs_tol=1e-7), (expected, actual))
        else:
            self.assertEqual(expected, actual)

    def test_resource_drift_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory) / 'models'
            shutil.copytree(resources.MODELS, folder)
            with patch.object(resources, 'MODELS', folder):
                resources.verify_models()
                path = folder / 'asap7/response.json'
                path.write_bytes(path.read_bytes() + b' ')
                with self.assertRaisesRegex(ValueError, 'frozen model resource changed'):
                    resources.verify_models()

    def test_reduction_geometry_reused_without_reusing_clock_features(self):
        query = dict(output_bits=12, terms=[
            [[source, bit, bit + offset] for bit in range(8)]
            for source, offset in enumerate((0, 2, 4))
        ], target_ps=1200)
        build_features = reduction_features.reduction_features
        prices = runtime('asap7').prices
        with patch.object(reduction_features, 'reduction_features', wraps=build_features) as builder:
            reference = build_features(query)['intensive']
            for period in (1200, 1., 965.321, 6000., 100000.):
                request = dict(query, target_ps=period)
                expected = build_features(request)['intensive']
                self.assertEqual(expected, reduction_features.intensive_features_at_period(reference, period))
                prices.reduction_price(request)
            with self.assertRaisesRegex(ValueError, 'positive numerical T'):
                prices.reduction_price(dict(query, target_ps=True))
            builder.assert_called_once()

    def test_nangate_platform_identity_is_required(self):
        data = json.loads(gzip.decompress(Path(__file__).with_name('frozen_predictions.json.gz').read_bytes()))
        fixture = next(r for r in data['fixtures'] if r['platform'] == 'nangate45')
        model = runtime('nangate45')
        fixture['owners']['profile_sha256'] = 'wrong-platform'
        with self.assertRaisesRegex(ValueError, 'profile mismatch'):
            model.evaluate(Graph(fixture['graph']), fixture['view'], fixture['state'], fixture['owners'])


if __name__ == '__main__':
    unittest.main()
