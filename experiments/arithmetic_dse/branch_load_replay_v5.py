"""Portable diagnostic replay of frozen v5 features, prices and source duties.

Inference is run with subprocess and file access blocked. Optional native
replay launches only the supplied software test executable, outside that block.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch

from . import branch_load_model_v5 as model
from . import branch_load_features_v5 as geometry
from .prospective_cell_cover import AREA
from .common_centered_replay_v1 import load, close


def replay(root=None, native=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo / 'experiments/arithmetic/evidence/common_branch_load_v5'
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
    freeze = load(root / 'freeze.json.gz')
    import gzip
    candidate_bytes = gzip.decompress((root / 'candidate.json.gz').read_bytes())
    if hashlib.sha256(candidate_bytes).hexdigest() != freeze['candidate_sha256']:
        raise ValueError('fit freeze differs from candidate')
    if json.loads(candidate_bytes) != load(root / 'runtime-bundle.json.gz'):
        raise ValueError('runtime changed the frozen numerical candidate')
    bundle = json.loads(candidate_bytes)
    funcs = dict(operator=model.predict_operator, G=model.predict_reduction, S=model.predict_state)
    allcases = []
    featurecases = []
    for name in ('consumption-cases.json.gz', 'evaluation-consumption-cases.json.gz'):
        allcases.extend(load(root / name)['cases'])
    for name in ('feature-cases.json.gz', 'evaluation-feature-cases.json.gz'):
        featurecases.extend(load(root / name)['cases'])
    rejections = load(root / 'rejection-cases.json.gz')['cases']
    counts = dict(price_queries=0, feature_queries=0, rejections=0)
    # All inputs and coefficients have been loaded above. No measured label is
    # passed to an inference function, and a hidden file read fails this replay.
    with patch('subprocess.Popen', side_effect=AssertionError('online subprocess')):
        with patch('builtins.open', side_effect=AssertionError('online file read')):
            with patch('pathlib.Path.open', side_effect=AssertionError('online path read')):
                for case in allcases:
                    for query, expected in zip(case['queries'], case['expected'], strict=True):
                        close(funcs[case['kind']](bundle, query, diagnostic=True), expected)
                        counts['price_queries'] += 1
                for case in featurecases:
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
                for case in rejections:
                    candidate = deepcopy(bundle)
                    if case['badmodel']:
                        candidate['version'] = 'unregistered'
                    result = funcs[case['kind']](candidate, case['query'], diagnostic=not case['public'])
                    if result['status'] != 'cost_uncovered':
                        raise ValueError('unsupported or public query accepted')
                    counts['rejections'] += 1
    provenance = load(root / 'legal-provenance.json.gz')
    for cell in provenance['cells']:
        if not cell['allowed'] or AREA[cell['proxy']] != cell['area_um2']:
            raise ValueError('legal cell area differs')
    if not provenance['forbidden_old_HA']['forbidden'] or provenance['FAx1_forbidden']:
        raise ValueError('dont-use attribution differs')
    decision = load(root / 'physical-decision.json.gz')
    settlement = load(root / 'settlement.json')
    if decision['new_tasks'] or decision['new_EDA_calls'] or settlement['increment_EDA_calls']:
        raise ValueError('unregistered physical work')
    if settlement['recorded_cumulative_ledger']['pending']:
        raise ValueError('unsettled physical ledger')
    report = load(root / 'evaluation--report.json.gz')
    if (report['fresh_validation'] or report['validation_tuning']
            or report['independent_labels_read'] or report['public_D_changed']):
        raise ValueError('consumed regression was assigned a new duty')
    if native:
        with tempfile.TemporaryDirectory(prefix='branch-load-replay-') as folder:
            folder = Path(folder)
            for mode, cases in (('prices', allcases), ('features', featurecases)):
                for case in cases:
                    request = dict(kind=case['kind'], queries=case['queries'])
                    if mode == 'prices':
                        request.update(model=bundle, diagnostic=True)
                    (folder / 'in.json').write_text(json.dumps(request))
                    subprocess.run([str(Path(native).resolve()), str(folder / 'in.json'), str(folder / 'out.json')],
                                   check=True, timeout=120)
                    actual = load(folder / 'out.json')
                    if mode == 'features' and case['kind'] == 'S':
                        actual = [[{k: row[k] for k in ('path_class', 'control_source', 'stage', 'features')}
                                   for row in paths] for paths in actual]
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
                new_EDA_calls=0, online_file_reads=0, fresh_validation=False,
                independent_labels_read=False, public_D_changed=False, full_D_ready=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    parser.add_argument('--native', type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.root, args.native), indent=2))
