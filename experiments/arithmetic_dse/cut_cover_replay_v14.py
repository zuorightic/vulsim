"""Replay the finite v14 train experiment without backend tools or raw artifacts."""
import argparse
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from . import cut_area_model_v14 as model
from . import prospective_cut_cover_v14 as cut
from . import mapped_logic_fingerprint_v14 as logic
from . import transition_incidence_features_v10 as geometry


def load(path):
    raw = Path(path).read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith('.gz') else raw)


def same(a, b):
    if isinstance(a, dict):
        if set(a) != set(b):
            raise ValueError('replay mapping keys differ')
        for key in a:
            same(a[key], b[key])
    elif isinstance(a, (list, tuple)):
        if len(a) != len(b):
            raise ValueError('replay sequence length differs')
        for x, y in zip(a, b, strict=True):
            same(x, y)
    elif isinstance(a, (int, float)) and not isinstance(a, bool):
        if abs(a-b) > 1e-8*max(1., abs(a)):
            raise ValueError('replay numerical mismatch')
    elif a != b:
        raise ValueError('replay value differs')


def replay(root=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo/'experiments/arithmetic/evidence/common_cut_cover_v14'
    identity = load(root/'identity.json')
    for name, digest in identity['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('evidence changed '+name)
    for name, digest in identity['source_sha256'].items():
        if hashlib.sha256((repo/name).read_bytes()).hexdigest() != digest:
            raise ValueError('source changed '+name)
    archive = load(root/'source-and-tools.json.gz')['files']
    for name, item in archive.items():
        if hashlib.sha256(item['text'].encode()).hexdigest() != item['sha256']:
            raise ValueError('archive changed '+name)
    library = load(root/'library.json.gz')['cells']
    protocol = load(root/'protocol.json.gz')
    data = load(root/'train-inputs.json.gz')
    predictions = load(root/'predictions.json.gz')
    candidate = load(root/'candidate.json.gz')
    report = load(root/'train-report.json.gz')
    audit = load(root/'S-logic-audit.json.gz')
    cases = load(root/'S-logic-proof-inputs.json.gz')
    settlement = load(root/'settlement.json')
    freeze = load(root/'freeze.json.gz')
    # The registered small fitter is archived verbatim. Loading it does not run
    # its main function. All fitting below recomputes the same sealed trials.
    namespace = {'__name__': 'v14_replay_fitter', '__file__': str(root/'tools/fit.py')}
    exec(compile(archive['tools/fit.py']['text'], 'v14_archived_fitter', 'exec'), namespace)
    if hashlib.sha256(json.dumps(candidate, indent=2, ensure_ascii=True, allow_nan=False).encode()+b'\n').hexdigest() != freeze['candidate_sha256']:
        # model_fast_preflight.write uses ensure_ascii=False; all candidate
        # identifiers here are ASCII, so both encodings must agree.
        raise ValueError('sealed candidate identity differs')
    work_count = local_checks = negative_cuts = feature_count = inference_count = 0
    fold_refits = S_checks = S_mutations = 0
    with patch('subprocess.Popen', side_effect=AssertionError('unexpected replay subprocess')):
        with patch('builtins.open', side_effect=AssertionError('unexpected inference file read')):
            with patch('pathlib.Path.open', side_effect=AssertionError('unexpected inference path read')):
                for cell in library:
                    n = len(cell['inputs'])
                    same(cell['truth'], cut.expression(cell['function'],
                        {pin: cut.variable(i, n) for i, pin in enumerate(cell['inputs'])}, (1 << (1 << n))-1))
                table = cut.library_table(library)
                work = {}
                for key, case in data['proofs'].items():
                    value = model.work(case['query'], case['family'], table, witnesses=True)
                    same(value, case['mapped'])
                    circuit, outputs = model.circuits.operator_circuit(case['query']['local_context']['producer']) if case['family'] == 'Add' else model.circuits.reduction_circuit(case['query'])[:2]
                    local_checks += cut.verify(circuit, outputs, value, table)
                    bad = deepcopy(value)
                    bad['cuts'][0]['truth'] ^= 1
                    try:
                        cut.verify(circuit, outputs, bad, table)
                    except ValueError:
                        negative_cuts += 1
                    else:
                        raise ValueError('changed cut truth accepted')
                    work[key] = value
                    work_count += 1
                for family, rows in data['area'].items():
                    for row in rows:
                        if row['role'] != 'train':
                            raise ValueError('nontrain row admitted')
                        case = data['proofs'][row['cover_identity']]
                        query = deepcopy(case['query'])
                        if family == 'Add':
                            query['flow_context']['target_period_ps'] = row['target_ps']
                            query['flow_context']['abc_target_ps'] = row['target_ps']
                            base = geometry.operator_features(query)
                        else:
                            query['target_ps'] = row['target_ps']
                            base = geometry.reduction_features(query)['intensive']
                        values = model.features(base, work[row['cover_identity']])
                        names = set(protocol['area'][family]['mapping_features'] +
                            protocol['area'][family]['physical_features'] + protocol['area'][family]['direct_grt_features']) | {'cut_area'}
                        same({k: values[k] for k in names}, {k: row['f'][k] for k in names})
                        feature_count += 1
                    cfg = protocol['area'][family]
                    recomputed = []
                    for form in cfg['forms']:
                        loo = []
                        for group in sorted({r['group'] for r in rows}):
                            training = [r for r in rows if r['group'] != group]
                            held = [r for r in rows if r['group'] == group]
                            if {r['source'] for r in training} & {r['source'] for r in held}:
                                raise ValueError('same-source T leaked across fold')
                            entry = namespace['train'](training, form, cfg)
                            loo += namespace['predict'](held, entry)
                            fold_refits += 1
                        same(loo, predictions[family]['trial_LOSO'][form])
                        stats = {q: namespace['stats'](loo, q) for q in ('grt', 'synth', 'ratio')}
                        recomputed.append(dict(form=form, score=max(v['score'] for v in stats.values()), LOSO=stats))
                    same(recomputed, report['results'][family]['trials'])
                    chosen = min(recomputed, key=lambda t: (t['score'], t['form']))
                    same(chosen, report['results'][family]['selected'])
                    entry = namespace['train'](rows, chosen['form'], cfg)
                    same(entry, candidate['models'][family])
                    actual = namespace['predict'](rows, entry)
                    same(actual, predictions[family]['all_train'])
                    inference_count += len(actual)
                for case_name, case in cases.items():
                    source, kind, stage = case_name.split('|')
                    expected = next(r for r in audit['rows'] if (r['source'], r['kind'], r['stage']) == (source, kind, stage))
                    result = logic.fingerprint(case['start'], case['instances'], case['library'], case['nets'])
                    same(result, {k: v for k, v in expected.items() if k not in ('source', 'kind', 'stage')})
                    altered = deepcopy(case['nets'])
                    endpoint = 'native/valid_2$_SDFF_PN0_/D'
                    altered[endpoint]['net'] = altered[case['start']]['net']
                    bad = logic.fingerprint(case['start'], case['instances'], case['library'], altered)
                    if bad['sinks'] == result['sinks']:
                        raise ValueError('changed valid propagation cone not detected')
                    S_mutations += 1
                    S_checks += 1
    if settlement['before'] != settlement['after'] or any(settlement['increment'].values()):
        raise ValueError('unexpected backend usage')
    if protocol['finite_trials'] != 4 or report['total_trials'] != 4:
        raise ValueError('finite trial count changed')
    return dict(status='passed',library_cells=len(library),prospective_DAGs=work_count,
        exact_local_cut_checks=local_checks,mutated_cut_truth_negatives=negative_cuts,
        pure_feature_queries=feature_count,selected_candidate_inferences=inference_count,
        complete_group_trial_refits=fold_refits,sealed_trials=4,S_connectivity_cases=S_checks,
        S_changed_propagation_negatives=S_mutations,source_files=len(identity['source_sha256']),
        archived_text_files=len(archive),backend_calls=0,validation_labels_read=False,
        independent_labels_read=False,new_price_version=False,public_D_changed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path)
    print(json.dumps(replay(parser.parse_args().root), indent=2))
