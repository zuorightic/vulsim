"""Replay the v7 shared context, training isolation and frozen consumption.

Numerical inference is exercised with file reads and subprocesses blocked.
An optional C++ program runs only as an explicit software verification step.
"""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from . import load_pressure_model_v7 as model
from . import load_pressure_features_v7 as geometry
from .common_centered_replay_v1 import load, close
from .rebuffer_context_replay_v6 import verify_path
from .model_fast_preflight import key


def rejection_bundle(bundle, case):
    candidate = deepcopy(bundle)
    if case['badmodel']:
        candidate['version'] = 'unregistered'
    mutation = case.get('model_mutation')
    if mutation == 'different_context':
        candidate['context_function']['intercept'] += 1
    elif mutation == 'missing_context':
        candidate.pop('context_function')
    elif mutation == 'missing_both_class':
        candidate['models']['S'].pop('external_valid')
        candidate['state_support'].pop('external_valid')
    elif mutation == 'missing_support':
        candidate['state_support'].pop('native_valid')
    elif mutation == 'nonpositive_context':
        function = candidate['context_function']
        function['intercept'] = -10000.
        function['coefficients'] = [0.] * len(function['coefficients'])
        candidate['models']['S']['native_enable']['functions']['R'] = deepcopy(function)
    elif mutation is not None:
        raise ValueError('unknown rejection mutation')
    return candidate


def verify_context_lineage(train, crossfit, predictions, bundle):
    rows = train['data']['S']
    if train['validation_labels_read'] or train['independent_labels_read'] or crossfit['uses_held_out_labels']:
        raise ValueError('training role differs')
    folds = {r['fold'] for r in rows}
    if set(crossfit['contexts']) != folds | {'all_train'}:
        raise ValueError('crossfit folds differ')
    for pair in train['paired_folds']:
        matched = [r for r in rows if r['source'] in (pair['old'], pair['new'])]
        if {r['fold'] for r in matched} != {pair['group']} or len({r['source'] for r in matched}) != 2:
            raise ValueError('paired source leakage')
    for fold, context in crossfit['contexts'].items():
        training = [r for r in rows if fold == 'all_train' or r['fold'] != fold]
        held = [r for r in rows if r['fold'] == fold]
        if (set(context['training_sources']) != {r['source'] for r in training}
                or set(context['excluded_sources']) != {r['source'] for r in held}
                or set(context['training_sources']) & set(context['excluded_sources'])
                or context['uses_held_out_labels']):
            raise ValueError('held-out context training leaked')
        lineage = []
        for row in training:
            if row['path_class'] == 'native_enable':
                features = next(q['features'] for q in geometry.base_state_controls(row['structure'])
                                if q['path_class'] == row['path_class'] and q['stage'] == row['stage'])
                lineage.append(dict(source=row['source'], target_ps=row['target_ps'], stage=row['stage'],
                                    actual=row['actual'], features=features))
        if key(lineage) != context['training_rows_sha256']:
            raise ValueError('context training lineage differs')
    checks = 0
    for mode in ('LOSO', 'train'):
        cached = {}
        for row in predictions['S'][mode]:
            fold = row['fold'] if mode == 'LOSO' else 'all_train'
            identity = fold, row['source'], row['target_ps']
            if identity not in cached:
                cached[identity] = {(q['path_class'], q['stage']): q['features']
                                    for q in geometry.state_controls(row['structure'], crossfit['contexts'][fold]['function'])}
            close(row['f'], cached[identity][row['path_class'], row['stage']])
            checks += 1
    close(bundle['context_function'], crossfit['contexts']['all_train']['function'])
    close(bundle['context_function'], bundle['models']['S']['native_enable']['functions']['R'])
    return checks


def replay(root=None, native=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_load_pressure_v7'
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
        raise ValueError('candidate differs from freeze')
    bundle = json.loads(candidate_bytes)
    close(bundle, load(root / 'runtime-bundle.json.gz'))
    context_checks = verify_context_lineage(load(root / 'train-data.json.gz'),
                                           load(root / 'context-crossfit.json.gz'),
                                           load(root / 'train-predictions.json.gz'), bundle)
    cases, featurecases = [], []
    for name in ('consumption-cases.json.gz', 'evaluation-consumption-cases.json.gz'):
        cases.extend(load(root / name)['cases'])
    for name in ('feature-cases.json.gz', 'evaluation-feature-cases.json.gz'):
        featurecases.extend(load(root / name)['cases'])
    rejections = load(root / 'rejection-cases.json.gz')['cases']
    rejections += load(root / 'depth-rejection-cases.json.gz')['cases']
    functions = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
    features = dict(operator=geometry.operator_features, G=geometry.reduction_features,
                    S=lambda q: geometry.state_controls(q, bundle['context_function']))
    counts = dict(price_queries=0, feature_queries=0, rejections=0, priced=0)
    with patch('subprocess.Popen', side_effect=AssertionError('online subprocess')):
        with patch('builtins.open', side_effect=AssertionError('online file read')):
            with patch('pathlib.Path.open', side_effect=AssertionError('online path read')):
                for case in cases:
                    for query, expected in zip(case['queries'], case['expected'], strict=True):
                        actual = functions[case['kind']](bundle, query, diagnostic=True)
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
                    candidate = rejection_bundle(bundle, case)
                    actual = functions[case['kind']](candidate, case['query'], diagnostic=not case['public'])
                    if actual['status'] != 'cost_uncovered':
                        raise ValueError('unsupported/public query accepted')
                    counts['rejections'] += 1
    report = load(root / 'evaluation--report.json.gz')
    if any(report[k] for k in ('fresh_validation', 'validation_tuning', 'independent_labels_read', 'public_D_changed')):
        raise ValueError('consumed regression role differs')
    settlement = load(root / 'settlement.json')
    if any(settlement['increment_usage'].values()) or settlement['recorded_cumulative_ledger']['pending']:
        raise ValueError('unexpected physical usage')
    proof = load(root / 'inherited-path-proof-cases.json.gz')
    inherited = load(root / 'inherited-evidence.json')
    for name, digest in [('path-proof-cases', inherited['strict_path_origin_sha256']),
                         ('openroad-source-audit', inherited['source_audit_origin_sha256'])]:
        if hashlib.sha256(gzip.decompress((root / ('inherited-' + name + '.json.gz')).read_bytes())).hexdigest() != digest:
            raise ValueError('inherited evidence identity differs')
    if hashlib.sha256(proof['source_verifier'].encode()).hexdigest() != proof['source_verifier_sha256']:
        raise ValueError('inherited path verifier differs')
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
        raise ValueError('inherited path negatives differ')
    if native:
        with tempfile.TemporaryDirectory(prefix='load-pressure-replay-') as folder:
            folder = Path(folder)
            def invoke(request):
                (folder / 'in.json').write_text(json.dumps(request))
                subprocess.run([str(Path(native).resolve()), str(folder / 'in.json'), str(folder / 'out.json')],
                               check=True, timeout=120)
                return load(folder / 'out.json')
            for mode, modecases in (('prices', cases), ('features', featurecases)):
                for case in modecases:
                    request = dict(kind=case['kind'], queries=case['queries'])
                    if mode == 'prices':
                        request.update(model=bundle, diagnostic=True)
                    elif case['kind'] == 'S':
                        request['context_function'] = bundle['context_function']
                    actual = invoke(request)
                    if mode == 'features' and case['kind'] == 'S':
                        actual = [[{k: row[k] for k in ('path_class', 'control_source', 'stage', 'features')}
                                   for row in rows] for rows in actual]
                    close(actual, case['expected'])
            for case in rejections:
                result = invoke(dict(kind=case['kind'], queries=[case['query']],
                                     model=rejection_bundle(bundle, case), diagnostic=not case['public']))
                if result[0]['status'] != 'cost_uncovered':
                    raise ValueError('native rejection differs')
            (folder / 'in.json').write_text(json.dumps(dict(kind='S', queries=featurecases[-1]['queries'][:1])))
            malformed = subprocess.run([str(Path(native).resolve()), str(folder / 'in.json'), str(folder / 'out.json')],
                                       capture_output=True, text=True, timeout=120)
            if malformed.returncode != 1 or 'context_function required' not in malformed.stderr:
                raise ValueError('missing-context request was not rejected safely')
    return dict(status='passed', **counts, context_feature_checks=context_checks,
                native_replayed=bool(native), evidence_files=len(manifest['files']),
                source_files=len(manifest['source_sha256']), strict_paths_inherited=len(proof['cases']),
                missing_arc_negatives=negatives, new_EDA_calls=0, online_physical_calls=0,
                online_file_reads=0, fresh_validation=False, independent_labels_read=False,
                public_D_changed=False, full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--native', type=Path)
    arguments = parser.parse_args()
    print(json.dumps(replay(arguments.root, arguments.native), indent=2))
