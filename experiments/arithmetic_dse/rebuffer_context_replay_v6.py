"""Replay v6 features, prices, paired training duties and physical settlement.

All inference runs with file reads and subprocess creation blocked. The
optional native executable is a separate software replay step.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from . import rebuffer_context_model_v6 as model
from . import rebuffer_context_features_v6 as geometry
from .common_centered_replay_v1 import load, close


def verify_path(case, pins):
    from .model_physical_path_v2 import verify_combinational_arc
    points = case['points']
    if points[0][0] != case['start_pin'] or points[-1][0] != case['end_pin']:
        raise ValueError('path endpoints differ')
    if len({n for n, _ in points}) != len(points):
        raise ValueError('path repeats a pin')
    arcs, wires = [], []
    for (a, ta), (b, tb) in zip(points, points[1:]):
        if not math.isfinite(ta) or not math.isfinite(tb) or tb < ta - 1e-5:
            raise ValueError('invalid path increment')
        ca, pa = a.rsplit('/', 1) if '/' in a else ('', a)
        cb, pb = b.rsplit('/', 1)
        if ca == cb:
            master = case['instances'][ca]
            verify_combinational_arc(pins[master], pa, pb)
            arcs.append([master, pa, pb])
        else:
            nets = case['nets']
            if b not in nets or nets[b]['direction'] != 'input':
                raise ValueError('path sink is not an actual input')
            if ca:
                if a not in nets or nets[a]['direction'] != 'output' or nets[a]['net'] != nets[b]['net']:
                    raise ValueError('disconnected path')
            elif nets[b]['net'] != a:
                raise ValueError('port path disconnected')
            wires.append(max(0., tb - ta))
    close(arcs, case['arcs'])
    close(wires, case['wires'])


def replay(root=None, native=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_rebuffer_context_v6'
    manifest = load(root / 'identity.json')
    for name, digest in manifest['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('evidence changed: ' + name)
    for name, digest in manifest['source_sha256'].items():
        if hashlib.sha256((repo / name).read_bytes()).hexdigest() != digest:
            raise ValueError('source changed: ' + name)
    for name, entry in load(root / 'source-and-tools.json.gz')['files'].items():
        if hashlib.sha256(entry['text'].encode()).hexdigest() != entry['sha256']:
            raise ValueError('archived source changed: ' + name)
    frozen = load(root / 'freeze.json.gz')
    candidate_bytes = gzip.decompress((root / 'candidate.json.gz').read_bytes())
    if hashlib.sha256(candidate_bytes).hexdigest() != frozen['candidate_sha256']:
        raise ValueError('candidate differs from numerical freeze')
    bundle = json.loads(candidate_bytes)
    close(bundle, load(root / 'runtime-bundle.json.gz'))
    train = load(root / 'train-data.json.gz')
    if train['validation_labels_read'] or train['independent_labels_read']:
        raise ValueError('training consumed a locked role')
    for pair in train['paired_folds']:
        rows = [r for r in train['data']['S'] if r['source'] in (pair['old'], pair['new'])]
        if {r['fold'] for r in rows} != {pair['group']} or len({r['source'] for r in rows}) != 2:
            raise ValueError('paired source fold leaked')
    cases, featurecases = [], []
    for name in ('consumption-cases.json.gz', 'evaluation-consumption-cases.json.gz'):
        cases.extend(load(root / name)['cases'])
    for name in ('feature-cases.json.gz', 'evaluation-feature-cases.json.gz'):
        featurecases.extend(load(root / name)['cases'])
    rejections = load(root / 'rejection-cases.json.gz')['cases']
    funcs = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
    features = dict(operator=geometry.operator_features, G=geometry.reduction_features, S=geometry.state_controls)
    counts = dict(price_queries=0, feature_queries=0, rejections=0, priced=0)
    with patch('subprocess.Popen', side_effect=AssertionError('online subprocess')):
        with patch('builtins.open', side_effect=AssertionError('online file read')):
            with patch('pathlib.Path.open', side_effect=AssertionError('online path read')):
                for case in cases:
                    for query, expected in zip(case['queries'], case['expected'], strict=True):
                        actual = funcs[case['kind']](bundle, query, diagnostic=True)
                        close(actual, expected)
                        counts['price_queries'] += 1
                        counts['priced'] += actual['status'] != 'cost_uncovered'
                for case in featurecases:
                    for query, expected in zip(case['queries'], case['expected'], strict=True):
                        actual = features[case['kind']](query)
                        if case['kind'] == 'S':
                            actual = [{k: row[k] for k in ('path_class', 'control_source', 'stage', 'features')}
                                      for row in actual]
                        close(actual, expected)
                        counts['feature_queries'] += 1
                for case in rejections:
                    candidate = deepcopy(bundle)
                    if case['badmodel']:
                        candidate['version'] = 'unregistered'
                    actual = funcs[case['kind']](candidate, case['query'], diagnostic=not case['public'])
                    if actual['status'] != 'cost_uncovered':
                        raise ValueError('public or unsupported query accepted')
                    counts['rejections'] += 1
    report = load(root / 'evaluation--report.json.gz')
    if any(report[k] for k in ('fresh_validation', 'validation_tuning', 'independent_labels_read', 'public_D_changed')):
        raise ValueError('consumed regression was given a fresh role')
    progress = load(root / 'S-factors--progress.json.gz')
    admission = load(root / 'S-factors--admission.json.gz')
    if progress['phase'] != 'bounded_complete' or progress['errors'] or len(progress['completed']) != 12:
        raise ValueError('finite training incomplete')
    if set(progress['completed']) != {t['id'] for t in admission['tasks']}:
        raise ValueError('training task list differs')
    settlement = load(root / 'settlement.json')
    if (settlement['increment_usage']['synth'] != 12 or settlement['increment_usage']['grt'] != 12
            or settlement['increment_usage']['support_calls'] != 48 or settlement['physical_failures']
            or settlement['automatic_retries'] or settlement['recorded_cumulative_ledger']['pending']):
        raise ValueError('physical settlement differs')
    proof = load(root / 'path-proof-cases.json.gz')
    if hashlib.sha256(proof['source_verifier'].encode()).hexdigest() != proof['source_verifier_sha256']:
        raise ValueError('source path verifier differs')
    negatives = 0
    for case in proof['cases']:
        verify_path(case, proof['pin_classes'])
        if case['arcs']:
            master, src, dst = case['arcs'][0]
            modified = deepcopy(proof['pin_classes'])
            modified[master]['timing_arcs'] = [arc for arc in modified[master]['timing_arcs'] if arc != [src, dst]]
            try:
                verify_path(case, modified)
            except ValueError as error:
                if 'actual Liberty' not in str(error):
                    raise
                negatives += 1
            else:
                raise ValueError('missing actual Liberty arc accepted')
    if negatives != proof['missing_actual_arc_negatives']:
        raise ValueError('path negative count differs')
    if native:
        with tempfile.TemporaryDirectory(prefix='rebuffer-context-replay-') as folder:
            folder = Path(folder)
            for mode, modecases in (('prices', cases), ('features', featurecases)):
                for case in modecases:
                    request = dict(kind=case['kind'], queries=case['queries'])
                    if mode == 'prices':
                        request.update(model=bundle, diagnostic=True)
                    (folder / 'in.json').write_text(json.dumps(request))
                    subprocess.run([str(Path(native).resolve()), str(folder / 'in.json'), str(folder / 'out.json')],
                                   check=True, timeout=120)
                    actual = load(folder / 'out.json')
                    if mode == 'features' and case['kind'] == 'S':
                        actual = [[{k: row[k] for k in ('path_class', 'control_source', 'stage', 'features')}
                                   for row in rows] for rows in actual]
                    close(actual, case['expected'])
            for case in rejections:
                candidate = deepcopy(bundle)
                if case['badmodel']:
                    candidate['version'] = 'unregistered'
                (folder / 'in.json').write_text(json.dumps(dict(kind=case['kind'], queries=[case['query']],
                                                            model=candidate, diagnostic=not case['public'])))
                subprocess.run([str(Path(native).resolve()), str(folder / 'in.json'), str(folder / 'out.json')],
                               check=True, timeout=120)
                if load(folder / 'out.json')[0]['status'] != 'cost_uncovered':
                    raise ValueError('native rejected-domain drift')
    return dict(status='passed', **counts, native_replayed=bool(native),
                evidence_files=len(manifest['files']), source_files=len(manifest['source_sha256']),
                training_physical_points=12, strict_paths=len(proof['cases']), missing_arc_negatives=negatives, online_physical_calls=0, online_file_reads=0,
                fresh_validation=False, independent_labels_read=False, public_D_changed=False, full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--native', type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.root, args.native), indent=2))
