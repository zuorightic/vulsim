"""Portable W3--W5 flow-structure diagnostic replay, without physical tools."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch
from . import flow_structure_model as model
from . import flow_structure_features_v4 as geometry
from . import operator_source_identity_v1 as identity
from .common_centered_replay_v1 import load, close


def replay(root=None, native=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_flow_structure_v2'
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
    bundle = load(root / 'runtime-bundle.json.gz')
    functions = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
    counts = dict(price_queries=0, feature_queries=0, rejections=0)
    cases = []
    with patch('subprocess.Popen', side_effect=AssertionError('online model launched a subprocess')):
        for name in ('consumption-cases.json.gz', 'evaluation-consumption-cases.json.gz', 'supplement-consumption-cases.json.gz'):
            for case in load(root / name)['cases']:
                for q, expected in zip(case['queries'], case['expected'], strict=True):
                    close(functions[case['kind']](bundle, q, diagnostic=True), expected)
                    counts['price_queries'] += 1
                cases.append(case)
        for case in load(root / 'feature-cases.json.gz')['cases'] + load(root / 'evaluation-feature-cases.json.gz')['cases']:
            for q, expected in zip(case['queries'], case['expected'], strict=True):
                if case['kind'] == 'operator':
                    result = geometry.operator_features(q)
                elif case['kind'] == 'G':
                    result = geometry.reduction_features(q)
                else:
                    result = [{k: p[k] for k in ('path_class', 'control_source', 'stage', 'features')}
                              for p in geometry.state_controls(q)]
                close(result, expected)
                counts['feature_queries'] += 1
        for case in load(root / 'rejection-cases.json.gz')['cases']:
            candidate = deepcopy(bundle)
            if case['badmodel']:
                candidate['version'] = 'unregistered'
            result = functions[case['kind']](candidate, case['query'], diagnostic=not case['public'])
            if result['status'] != 'cost_uncovered':
                raise ValueError('invalid or public query accepted')
            counts['rejections'] += 1
    duties = load(root / 'validation-duties.json.gz')
    known_op = set(duties['known_operator_groups'])
    known_g = set(duties['known_G_groups'])
    registration = load(root / 'validation-registration.json.gz')
    fresh_op, fresh_g = set(), set()
    # A G source identity ignores period and uses the emitted ordered terms.
    def gkey(q):
        data = dict(output_bits=q['output_bits'], terms=q['terms'])
        return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    for row in registration['checks']:
        group = identity.group(row['query']) if row['family'] == 'operator' else gkey(row['query'])
        if group != row['semantic_group']:
            raise ValueError('registered source identity differs')
        known, fresh = (known_op, fresh_op) if row['family'] == 'operator' else (known_g, fresh_g)
        if group in known:
            raise ValueError('fresh validation source was previously declared')
        fresh.add(group)
        result = functions[row['family']](bundle, row['query'], diagnostic=True)
        close(result, row['predicted'])
    if len(fresh_op) != 3 or len(fresh_g) != 3 or len(registration['checks']) != 18:
        raise ValueError('finite source duties differ')
    audit = load(root / 'source-duty-audit.json.gz')
    def word_key(q):
        return json.dumps(dict(output_bits=q['output_bits'],
                               ordered_word_columns=[sorted(b[2] for b in t) for t in q['terms']]),
                          sort_keys=True)
    canonical_known = {json.dumps(q, sort_keys=True) for q in audit['known_G_canonical']}
    canonical_fresh = {word_key(r['query']) for r in registration['checks'] if r['family'] == 'G'}
    if canonical_known & canonical_fresh or len(canonical_fresh) != 3 or audit['train_groups_split_by_names']:
        raise ValueError('independent root renaming changes G source duty')
    physical = load(root / 'physical-receipts.json.gz')['points']
    by_source = {}
    for point in physical:
        label, physical_manifest = point['grt'], point['manifest']
        if (physical_manifest['status'] != 'completed' or label['source_role'] != 'validation'
                or not label['physical_training_label_eligible'] or not label['ownership_complete']
                or not label['operator_maximum_covered'] or not label['data_through_operator_covered']
                or physical_manifest['abc_target_ps'] != point['target_ps']):
            raise ValueError('physical measurement scope differs')
        if hashlib.sha256(point['RTL'].encode()).hexdigest() != point['RTL_sha256']:
            raise ValueError('physical RTL changed')
        q = point['pricing_query']
        group = identity.group(q) if point['family'] == 'operator' else gkey(q)
        if group not in (fresh_op if point['family'] == 'operator' else fresh_g):
            raise ValueError('physical receipt has no fresh duty')
        by_source.setdefault((point['family'], group), []).append(point['target_ps'])
    if len(physical) != 18 or len(by_source) != 6 or any(sorted(v) != [500, 1373, 3000] for v in by_source.values()):
        raise ValueError('physical finite matrix differs')
    settlement = load(root / 'settlement.json')
    ledger = load(root / 'ledger-receipts.json.gz')['entries']
    if settlement['increment_usage']['pending'] or settlement['recorded_cumulative_ledger']['pending']:
        raise ValueError('physical ledger not settled')
    for stage in ('synth', 'grt'):
        if sum(e['stage'] == stage for e in ledger) != 18:
            raise ValueError('physical call count differs')
        task_ids = [e['task_id'] for e in ledger if e['stage'] == stage]
        if len(set(task_ids)) != 18:
            raise ValueError('paid physical retry detected')
    if native:
        with tempfile.TemporaryDirectory(prefix='flow-structure-replay-') as tmp:
            folder = Path(tmp)
            for case in cases:
                (folder / 'in.json').write_text(json.dumps(dict(kind=case['kind'], queries=case['queries'], model=bundle, diagnostic=True)))
                subprocess.run([str(Path(native).resolve()), str(folder / 'in.json'), str(folder / 'out.json')], check=True, timeout=120)
                close(load(folder / 'out.json'), case['expected'])
    return dict(status='passed', **counts, physical_points=18, fresh_operator_sources=3,
                fresh_G_sources=3, evidence_files=len(manifest['files']),
                source_files=len(manifest['source_sha256']), native_replayed=bool(native),
                new_EDA_calls=0, independent_labels_read=False, public_D_changed=False, full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--native', type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.root, args.native), indent=2))
