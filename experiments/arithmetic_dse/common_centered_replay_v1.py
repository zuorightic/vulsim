"""Portable replay of the W3--W5 centered diagnostic, without EDA.

Default replay checks identities, rebuilds prospective features, recalculates
prices and rejection behavior, and verifies the saved fresh physical labels.
An optional C++ executable repeats the same real-parameter price checks.
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

from . import centered_response as response
from . import common_centered_model_v1 as model
from . import common_mechanism_features_v1 as geometry
from . import operator_source_identity_v1 as source_identity


def load(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def close(actual, expected):
    if isinstance(actual, dict):
        if actual.get('status') == 'cost_uncovered':
            if expected.get('status') != 'cost_uncovered':
                raise ValueError('coverage differs')
            return
        if actual.keys() != expected.keys():
            raise ValueError('response keys differ')
        for name, value in actual.items():
            close(value, expected[name])
    elif isinstance(actual, list):
        if len(actual) != len(expected):
            raise ValueError('response dimensions differ')
        for a, b in zip(actual, expected, strict=True):
            close(a, b)
    elif type(actual) in (int, float):
        if not math.isclose(actual, expected, rel_tol=2e-10, abs_tol=1e-7):
            raise ValueError('response numbers differ')
    elif actual != expected:
        raise ValueError('response values differ')


def replay(root=None, native=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_centered_v1'
    identity = load(root / 'identity.json')
    for name, digest in identity['files'].items():
        if hashlib.sha256((root / name).read_bytes()).hexdigest() != digest:
            raise ValueError('evidence changed: ' + name)
    for name, digest in identity['source_sha256'].items():
        if hashlib.sha256((repo / name).read_bytes()).hexdigest() != digest:
            raise ValueError('implementation changed: ' + name)
    bundle = load(root / 'runtime-bundle.json.gz')
    predict = {'operator': model.predict_operator, 'G': model.predict_reduction, 'S': model.predict_state}
    counts = {'price_queries': 0, 'feature_queries': 0, 'rejections': 0}
    all_cases = []
    # A future accidental subprocess call from numerical inference must fail.
    with patch('subprocess.Popen', side_effect=AssertionError('online inference attempted a process launch')):
        for filename in ('consumption-cases.json.gz', 'evaluation-consumption-cases.json.gz',
                         'replacement-consumption-cases.json.gz'):
            for case in load(root / filename)['cases']:
                for query, expected in zip(case['queries'], case['expected'], strict=True):
                    close(predict[case['kind']](bundle, query, diagnostic=True), expected)
                    counts['price_queries'] += 1
                all_cases.append(case)
        for case in load(root / 'feature-cases.json.gz')['cases']:
            for query, expected in zip(case['queries'], case['expected'], strict=True):
                if case['kind'] == 'operator':
                    actual = geometry.operator_features(query)
                elif case['kind'] == 'G':
                    actual = geometry.reduction_features(query)
                else:
                    actual = [{k: row[k] for k in ('path_class', 'control_source', 'stage', 'features')}
                              for row in geometry.state_controls(query)]
                close(actual, expected)
                counts['feature_queries'] += 1
        for case in load(root / 'rejection-cases.json.gz')['cases']:
            candidate = deepcopy(bundle)
            if case['badmodel']:
                candidate['version'] = 'unregistered'
            result = predict[case['kind']](candidate, case['query'], diagnostic=not case['public'])
            if result['status'] != 'cost_uncovered':
                raise ValueError('invalid or public request accepted')
            counts['rejections'] += 1
        # Malformed exported responses cannot silently select a numerical price.
        function = deepcopy(bundle['models']['Add']['function'])
        f = geometry.operator_features(all_cases[0]['queries'][0])
        for mutation in ('scale', 'dimension', 'duplicate', 'nonfinite'):
            bad = deepcopy(function)
            if mutation == 'scale':
                bad['scales'][0] = 0.
            elif mutation == 'dimension':
                bad['centers'].pop()
            elif mutation == 'duplicate':
                bad['features'][1] = bad['features'][0]
            else:
                bad['coefficients'][0] = float('inf')
            try:
                response.predict(bad, f)
            except (ValueError, KeyError):
                pass
            else:
                raise ValueError('malformed numerical response accepted')
    physical = load(root / 'physical-receipts.json.gz')
    duties = load(root / 'validation-duties.json.gz')
    train_groups = {source_identity.group(q) for q in duties['train_queries']}
    fresh_groups = {source_identity.group(q) for q in duties['fresh_queries']}
    if train_groups & fresh_groups or len(fresh_groups) != 3:
        raise ValueError('fresh validation overlaps training under operand exchange')
    if len(train_groups) != duties['train_canonical_groups']:
        raise ValueError('canonical training source count differs')
    if not all(source_identity.group(q) in train_groups for q in duties['replication_queries']):
        raise ValueError('withdrawn exchange-equivalent source duty differs')
    physical_duties = {'fresh_validation': 0, 'exchange_equivalent_replication': 0}
    for point in physical['points']:
        label, manifest = point['grt'], point['manifest']
        if (manifest['status'] != 'completed' or label['source_role'] != 'validation'
                or not label['physical_training_label_eligible']
                or manifest['abc_target_ps'] != point['target_ps']
                or not label['ownership_complete'] or not label['operator_maximum_covered']):
            raise ValueError('physical receipt scope differs')
        if hashlib.sha256(point['RTL'].encode()).hexdigest() != point['RTL_sha256']:
            raise ValueError('physical RTL digest differs')
        group = source_identity.group(point['pricing_query'])
        expected = ('fresh_validation' if group in fresh_groups else
                    'exchange_equivalent_replication' if group in train_groups else None)
        if point['effective_duty'] != expected:
            raise ValueError('physical receipt duty differs')
        physical_duties[expected] += 1
    if physical_duties != {'fresh_validation': 9, 'exchange_equivalent_replication': 3}:
        raise ValueError('fresh and replication receipt counts differ')
    first = deepcopy(next(q for q in duties['train_queries']
                          if q['local_context']['producer']['lhs_width'] !=
                          q['local_context']['producer']['rhs_width']))
    swapped = deepcopy(first)
    spec = swapped['local_context']['producer']
    for suffix in ('width', 'zero_hex', 'one_hex'):
        a, b = 'lhs_' + suffix, 'rhs_' + suffix
        spec[a], spec[b] = spec[b], spec[a]
    if source_identity.group(first) != source_identity.group(swapped):
        raise ValueError('Add operand-exchange identity differs')
    # Borrow direction, capture load and downstream logic remain source inputs.
    for q in (first, swapped):
        q['local_context']['producer']['operation'] = 'sbb'
        if q['local_context']['producer']['status'] == 'carry':
            q['local_context']['producer']['status'] = 'borrow'
    if source_identity.group(first) == source_identity.group(swapped):
        raise ValueError('Sub source identity erased operand direction')
    original = deepcopy(duties['fresh_queries'][0])
    different = deepcopy(original)
    different['local_context']['captures'][0]['banks'] += 1
    if source_identity.group(original) == source_identity.group(different):
        raise ValueError('capture load erased from source identity')
    original = deepcopy(next(q for q in duties['fresh_queries']
                             if q['local_context']['consumers']))
    different = deepcopy(original)
    different['local_context']['consumers'] = []
    if source_identity.group(original) == source_identity.group(different):
        raise ValueError('downstream logic erased from source identity')
    if native:
        with tempfile.TemporaryDirectory(prefix='centered-response-replay-') as tmp:
            path = Path(tmp)
            for case in all_cases:
                request = dict(kind=case['kind'], model=bundle, diagnostic=True, queries=case['queries'])
                (path / 'input.json').write_text(json.dumps(request))
                subprocess.run([str(Path(native).resolve()), str(path / 'input.json'), str(path / 'output.json')],
                               check=True, timeout=120)
                close(load(path / 'output.json'), case['expected'])
    return dict(status='passed', **counts, physical_points=len(physical['points']),
                evidence_files=len(identity['files']), source_files=len(identity['source_sha256']),
                fresh_validation_sources=len(fresh_groups),
                physical_duties=physical_duties, train_semantic_groups=len(train_groups),
                native_replayed=bool(native), new_EDA_calls=0, independent_labels_read=False,
                public_D_changed=False, full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--native', type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.root, args.native), indent=2))
