"""Saved pre-migration predictions exercise both process models and the owner DAG."""
import gzip
import json
import math
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from tools.autopipe import resources
from tools.autopipe.resources import runtime
from tools.autopipe.workload_demand import Graph


class FrozenPredictionTests(unittest.TestCase):
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

    def test_nangate_platform_identity_is_required(self):
        data = json.loads(gzip.decompress(Path(__file__).with_name('frozen_predictions.json.gz').read_bytes()))
        fixture = next(r for r in data['fixtures'] if r['platform'] == 'nangate45')
        model = runtime('nangate45')
        fixture['owners']['profile_sha256'] = 'wrong-platform'
        with self.assertRaisesRegex(ValueError, 'profile mismatch'):
            model.evaluate(Graph(fixture['graph']), fixture['view'], fixture['state'], fixture['owners'])


if __name__ == '__main__':
    unittest.main()
