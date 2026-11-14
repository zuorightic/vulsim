"""Replay the v8 shared context, training isolation and frozen consumption.

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

from . import semantic_fanout_model_v8 as model
from . import semantic_fanout_features_v8 as geometry
from .common_centered_replay_v1 import load, close
from .rebuffer_context_replay_v6 import verify_path
from .model_fast_preflight import key
from . import common_mechanism_features_v1 as state


def serialized_sha(value):
    """Match the frozen JSON writer, including its trailing newline."""
    return hashlib.sha256((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()).hexdigest()


def verify_alias_evidence(root, bundle, train, settlement):
    protocol = load(root / 'S-alias--protocol.json.gz')
    admission = load(root / 'S-alias--admission.json.gz')
    progress = load(root / 'S-alias--progress.json.gz')
    capacity = load(root / 'S-alias--capacity-proof.json.gz')
    receipts = load(root / 'physical-receipts.json.gz')
    analysis = load(root / 'S-alias--analysis.json.gz')
    sources = load(root / 'S-alias--sources.json.gz')
    if (serialized_sha(protocol) != admission['protocol_sha256']
            or serialized_sha(admission) != capacity['admission_sha256']
            or protocol['frozen_v8_candidate_sha256'] != analysis['candidate_sha256']
            or protocol['frozen_v8_train_sha256'] != serialized_sha(train)
            or analysis['train_sha256'] != serialized_sha(train)):
        raise ValueError('alias admission or frozen training differs')
    tasks = {t['id']: t for t in admission['tasks']}
    if (len(tasks) != 6 or progress['phase'] != 'bounded_complete' or progress['errors'] or progress['active']
            or set(progress['completed']) != set(tasks) or admission['automatic_retries']
            or capacity['status'] != 'passed' or {r['id'] for r in capacity['runs']} != set(admission['capacity_pilots'])):
        raise ValueError('finite physical admission incomplete')
    if (receipts['automatic_retries'] or receipts['physical_failures'] or analysis['feeds_frozen_v8_fit']
            or analysis['validation_tuning'] or analysis['independent_labels_read']):
        raise ValueError('physical role or retry contract differs')
    runs = {r['task']: r for r in receipts['runs']}
    if set(runs) != set(tasks):
        raise ValueError('physical receipts incomplete')
    for task, run in runs.items():
        if (serialized_sha(run['manifest']) != run['manifest_sha256'] or run['manifest']['status'] != 'completed'
                or serialized_sha(run['structural_cec_proof']) != run['structural_cec_proof_sha256']
                or run['structural_cec_proof']['status'] != 'passed'):
            raise ValueError('physical run identity differs')
    parents = {(r['source'], r['target_ps']): r for r in receipts['parent_runs']}
    for identity, run in parents.items():
        row = next(r for r in train['data']['S'] if (r['source'], r['target_ps']) == identity)
        if (serialized_sha(run['manifest']) != run['manifest_sha256']
                or run['manifest_sha256'] != row['manifest_sha256']):
            raise ValueError('parent frozen train identity differs')
    for source in receipts['sources']:
        original = next(s for s in protocol['sources'] if s['id'] == source['id'])
        if (hashlib.sha256(source['rtl'].encode()).hexdigest() != source['rtl_sha256']
                or source['rtl_sha256'] != original['rtl_sha256']
                or serialized_sha(source['contract']) != original['contract_sha256']
                or source['contract']['spec'] != original['spec']):
            raise ValueError('admitted RTL or source contract differs')
    for pilot in capacity['runs']:
        if pilot['manifest_sha256'] != runs[pilot['id']]['manifest_sha256']:
            raise ValueError('pilot identity differs')
    entries = receipts['entries']
    if len(entries) != 36:
        raise ValueError('physical entry count differs')
    for task in tasks:
        local = [e for e in entries if e['task_id'] == task]
        if (len(local) != 6 or sum(e['stage'] == 'synth' for e in local) != 1
                or sum(e['stage'] == 'grt' for e in local) != 1 or sum(e['stage'] is None for e in local) != 4):
            raise ValueError('physical retry or support allowance differs')
    if any(e['status'] != 'completed' or e['exit_code'] or e['timed_out']
           or e['admission_id'] != admission['id'] or e['admission_sha256'] != serialized_sha(admission) for e in entries):
        raise ValueError('unsettled or failed physical entry')
    for quantity in ('walltime_s', 'CPU_time_s'):
        close(sum(e[quantity] for e in entries), settlement['increment_usage'][quantity])
    query_checks = 0
    for pair in sources['pairs']:
        before, after = pair['old_spec'], pair['new_spec']
        parent = [r for r in train['data']['S'] if r['source'] == pair['old']]
        if (not parent or before != parent[0]['spec'] or pair['feeds_frozen_v8_fit']
                or not pair['future_joint_fold_required'] or pair['parent_fold'] != parent[0]['fold']
                or before['semantic_signature'] == after['semantic_signature']
                or any(r['spec']['semantic_signature'] == after['semantic_signature'] for r in train['data']['S'])):
            raise ValueError('alias source or future fold duty differs')
        for target in (500, 1500, 3000):
            q1, q2 = state.state_structure(before, target), state.state_structure(after, target)
            close(q1, q2)
            f1, f2 = [geometry.state_controls(q, bundle['context_function']) for q in (q1, q2)]
            close(f1, f2)
            p1, p2 = [model.predict_state(bundle, q, diagnostic=True) for q in (q1, q2)]
            close(p1, p2)
            local = [c for c in analysis['control_comparisons'] if c['new_source'] == pair['new'] and c['target_ps'] == target]
            if len(local) != 6:
                raise ValueError('control comparison set differs')
            for c in local:
                close(c['prediction_ps'], next(p for p in p1['paths'][c['path_class']]['sources']
                                              if p['stage'] == c['source_stage'])['required_ps'])
            query_checks += 1
    if len(analysis['comparisons']) != 156 or len(analysis['bank_comparisons']) != 24:
        raise ValueError('alias comparison count differs')
    for comparison in analysis['comparisons']:
        task = next(t for t in tasks.values() if t['source_id'] == comparison['new_source'] and t['period_ps'] == comparison['target_ps'])
        run = runs[task['id']]
        if comparison['new_manifest_sha256'] != run['manifest_sha256']:
            raise ValueError('comparison physical identity differs')
        parent = parents[comparison['old_source'], comparison['target_ps']]
        if comparison['parent_manifest_sha256'] != parent['manifest_sha256']:
            raise ValueError('comparison parent identity differs')
        for side, receipt in (('old', parent), ('new', run)):
            metrics = next(m for m in receipt['manifest']['metrics'] if m['stage'] == comparison['stage'])
            actual = next(p for p in metrics['general_state_paths'] if p['id'] == comparison['path_id'])
            for name, value in actual.items():
                close(value, comparison[side][name])
        a, b = sorted(c['R_ps'] for c in (comparison['old'], comparison['new']))
        close(comparison['minimum_possible_max_APE'], (b-a)/(b+a))
        close(comparison['optimal_prediction_ps'], 2*a*b/(a+b))
        close(comparison['minimum_pair_mean_APE'], (1-a/b)/2)
        for label in (comparison['old'], comparison['new']):
            required = comparison['target_ps'] * (.8 if label['kind'] == 'port' else 1.) - label['slack_ps']
            close(label['R_ps'], required)
            close(label['R_ps'], label['delay_ps'] + label['H_ps'])
    return query_checks


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
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_semantic_fanout_v8'
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
    close(load(root / 'context-crossfit.json.gz'), load(root / 'inherited-v7-context-crossfit.json.gz'))
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
    if (settlement['increment_usage']['synth'] != 6 or settlement['increment_usage']['grt'] != 6 or settlement['increment_usage']['support_calls'] != 24 or settlement['increment_usage']['final'] or settlement['recorded_cumulative_ledger']['pending']):
        raise ValueError('unexpected physical usage')
    alias_checks = verify_alias_evidence(root, bundle, load(root / 'train-data.json.gz'), settlement)
    proof = load(root / 'inherited-path-proof-cases.json.gz')
    inherited = load(root / 'inherited-evidence.json')
    for name, digest in [('path-proof-cases', inherited['strict_path_origin_sha256']),
                         ('openroad-source-audit', inherited['source_audit_origin_sha256'])]:
        if hashlib.sha256(gzip.decompress((root / ('inherited-' + name + '.json.gz')).read_bytes())).hexdigest() != digest:
            raise ValueError('inherited evidence identity differs')
    origin = load(root / 'inherited-v6-identity.json.gz')
    for name in ('path-proof-cases.json.gz', 'openroad-source-audit.json.gz'):
        if hashlib.sha256((root / ('inherited-' + name)).read_bytes()).hexdigest() != origin['files'][name]:
            raise ValueError('strict proof not bound to v6 origin')
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
    newproof = load(root / 'path-proof-cases.json.gz')
    if (len(newproof['cases']) != 156 or newproof['missing_actual_arc_negatives'] != 156
            or hashlib.sha256(newproof['source_verifier'].encode()).hexdigest() != newproof['source_verifier_sha256']):
        raise ValueError('new strict path proof differs')
    new_negatives = 0
    receipts = load(root / 'physical-receipts.json.gz')
    for case in newproof['cases']:
        run = next(r for r in receipts['runs'] if r['task'] == case['task'])
        metrics = next(m for m in run['manifest']['metrics'] if m['stage'] == case['stage'])
        actual = next(p for p in metrics['general_state_paths'] if p['id'] == case['path_id'])
        if (case['manifest_sha256'] != run['manifest_sha256'] or case['raw_points_sha256'] != actual['points_sha256']
                or case['start_pin'] != actual['start_pin'] or case['end_pin'] != actual['end_pin']):
            raise ValueError('strict new path physical identity differs')
        verify_path(case, newproof['pin_classes'])
        master, src, dst = case['arcs'][0]
        modified = deepcopy(newproof['pin_classes'])
        modified[master]['timing_arcs'] = [arc for arc in modified[master]['timing_arcs'] if arc != [src, dst]]
        try:
            verify_path(case, modified)
        except ValueError as error:
            if 'actual Liberty' not in str(error):
                raise
            new_negatives += 1
        else:
            raise ValueError('new missing actual Liberty arc accepted')
    if native:
        with tempfile.TemporaryDirectory(prefix='semantic-fanout-replay-') as folder:
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
                missing_arc_negatives=negatives, strict_new_paths=len(newproof['cases']),
                new_missing_arc_negatives=new_negatives, alias_query_checks=alias_checks,
                new_physical_points=6, online_physical_calls=0,
                online_file_reads=0, fresh_validation=False, independent_labels_read=False,
                public_D_changed=False, full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--native', type=Path)
    arguments = parser.parse_args()
    print(json.dumps(replay(arguments.root, arguments.native), indent=2))
