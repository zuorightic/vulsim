"""Portable stdlib-only restoration and frozen operator inference/quality replay."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import importlib
import json
import math
from pathlib import Path
import statistics
import sys
import tempfile


def read(path):
    return json.loads(path.read_text())


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def metrics(rows, predictor, field, floor, inference):
    grouped = defaultdict(list)
    absolute = []
    for row in rows:
        error = abs(inference.infer(predictor, row['features']) - row[field])
        grouped[row['source_id']].append(error / max(abs(row[field]), floor))
        absolute.append(error)
    medians = sorted(statistics.median(v) for v in grouped.values())
    if not medians:
        return dict(sources=0, rows=0, source_macro_median=None, source_macro_P95=None,
                    source_macro_normalized_absolute_error=None, raw_MAE=None, passed=False)
    median = medians[math.ceil(len(medians) * .5) - 1]
    p95 = medians[math.ceil(len(medians) * .95) - 1]
    return dict(sources=len(grouped), rows=len(rows), source_macro_median=median, source_macro_P95=p95,
                source_macro_normalized_absolute_error=sum(sum(v)/len(v) for v in grouped.values())/len(grouped),
                raw_MAE=sum(absolute)/len(absolute), passed=median <= .15 and p95 <= .35 and p95 <= .5)


def same(a, b):
    if isinstance(a, dict):
        return isinstance(b, dict) and a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return isinstance(b, list) and len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, float):
        return isinstance(b, (float, int)) and math.isclose(a, b, rel_tol=1e-12, abs_tol=1e-10)
    return a == b


def replay(evidence):
    manifest = read(evidence/'manifest.json')
    compressed = []
    for name, identity in manifest['chunks'].items():
        raw = (evidence/name).read_bytes()
        if sha(raw) != identity['sha256'] or len(raw) != identity['bytes']:
            raise ValueError('evidence chunk mismatch')
        compressed.append(raw)
    raw = gzip.decompress(b''.join(compressed))
    if sha(raw) != manifest['payload_sha256']:
        raise ValueError('evidence payload mismatch')
    pool = json.loads(raw)
    with tempfile.TemporaryDirectory(prefix='operator-model-restore-') as temporary:
        restored = Path(temporary)
        for name, content in pool['files'].items():
            relative = Path(name)
            if relative.is_absolute() or '..' in relative.parts:
                raise ValueError('unsafe evidence member')
            path = restored/relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            if path.read_text() != content:
                raise ValueError('actual restored member differs')
        for name, expected in manifest['source_sha256'].items():
            if sha((restored/'source'/name).read_bytes()) != expected:
                raise ValueError('restored source differs')
        # -I invocation plus empty working-tree sys.path prevents a live module
        # from silently replacing the bundled inference implementation.
        sys.path.insert(0, str(restored/'source'))
        for name in list(sys.modules):
            if name == 'experiments' or name.startswith('experiments.'):
                del sys.modules[name]
        inference = importlib.import_module('experiments.arithmetic_dse.operator_condition_model')
        if not Path(inference.__file__).is_relative_to(restored):
            raise ValueError('inference did not load from restored evidence')
        fit = read(restored/'fit-data.json')
        candidate = read(restored/'fit-v1/candidate.json')
        validation = read(restored/'fit-v1/validation.json')
        freeze = read(restored/'fit-v1/selection-freeze.json')
        if sha((restored/'fit-data.json').read_bytes()) != manifest['fit_data_sha256']:
            raise ValueError('restored fitting dataset differs')
        if sha((restored/'fit-v1/candidate.json').read_bytes()) != freeze['model_sha256']:
            raise ValueError('restored frozen candidate differs')
        queries = covered = 0
        for dataset_name in ('fit-data.json', 'test-data.json'):
            if not (restored/dataset_name).exists():
                continue
            dataset = read(restored/dataset_name)
            for row in dataset['rows']:
                label = pool['qualified_labels'][row['id']]
                if label['source_role'] != row['role'] or not label['physical_training_label_eligible']:
                    raise ValueError('role/qualification mismatch')
                if any(row[k] != label[k] for k in ('operator_delay_ps', 'comb_area_um2', 'data_setup_slack_ps')):
                    raise ValueError('restored measured values differ')
                if inference.features(row['descriptor']) != row['features']:
                    raise ValueError('restored pre-measurement features differ')
                if row['stage'] == 'grt':
                    answer = inference.query(candidate, row['descriptor'], True)
                    queries += 1
                    covered += answer['status'] == 'covered'
        for op, entry in candidate['operations'].items():
            rows = [r for r in fit['rows'] if r['stage'] == 'grt' and r['role'] == 'validation' and r['operation'] == op]
            for key, field, floor in (('delay', 'operator_delay_ps', 10.), ('area', 'comb_area_um2', .01)):
                if not same(metrics(rows, entry[key], field, floor, inference), validation['operations'][op][key]):
                    raise ValueError('frozen validation quality replay differs: '+op+'/'+key)
            reserve = max([0.] + [r['operator_delay_ps']-inference.infer(entry['delay'], r['features']) for r in rows])
            if not math.isclose(reserve, entry['delay_reserve_ps'], rel_tol=1e-12, abs_tol=1e-10):
                raise ValueError('validation-only frozen reserve differs')
        independent = None
        if (restored/'test-v1/independent-test.json').exists():
            test = read(restored/'test-data.json')
            independent = read(restored/'test-v1/independent-test.json')
            for op, entry in candidate['operations'].items():
                rows = [r for r in test['rows'] if r['stage'] == 'grt' and r['operation'] == op]
                for key, field, floor in (('delay', 'operator_delay_ps', 10.), ('area', 'comb_area_um2', .01)):
                    if not same(metrics(rows, entry[key], field, floor, inference), independent['operations'][op][key]):
                        raise ValueError('frozen independent quality replay differs')
                missing = [r['id'] for r in rows if inference.query(candidate, r['descriptor'], True)['status'] != 'covered']
                if missing != independent['operations'][op]['uncovered']:
                    raise ValueError('independent coverage replay differs')
        result = dict(status='passed', actual_restored_members=len(pool['files']), inference_queries=queries,
                      covered=covered, validation_passed=freeze['validation_passed'],
                      independent_status=independent['status'] if independent else 'not_consumed',
                      fitting_or_EDA_executed=False, full_D_ready=False)
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, required=True)
    replay(p.parse_args().evidence.resolve())
