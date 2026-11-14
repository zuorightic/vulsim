"""Replay the finite local-sharing and factorized-area train experiment."""
import argparse
import hashlib
import math
from pathlib import Path
from statistics import mean
from collections import defaultdict
from unittest.mock import patch

from .common_centered_replay_v1 import load, close
from .repair_burden_replay_v11 import statistics, trial_statistics
from . import local_bank_features_v12 as local, factorized_area_v12 as area
from . import transition_incidence_features_v10 as geometry, centered_response as response
from . import nested_control_contexts as nested


def score(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[row['group']].append(math.log(max(row['predicted'],1e-9)/row['actual'])**2)
    return mean(mean(values) for values in grouped.values())


def area_statistics(rows):
    parts = dict(grt=rows,
        mapping=[dict(r,actual=r['synth_area_um2'],predicted=r['predicted_synth']) for r in rows],
        physical_ratio=[dict(r,actual=r['grt_area_um2']/r['synth_area_um2'],predicted=r['predicted_ratio']) for r in rows])
    return dict(score=max(score(rs) for rs in parts.values()),
        LOSO={name:statistics(rs) for name,rs in parts.items()})


def replay(root=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo/'experiments/arithmetic/evidence/common_local_sharing_v12'
    identity = load(root/'identity.json')
    for name,expected in identity['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('evidence digest differs: '+name)
    for name,expected in identity['source_sha256'].items():
        if hashlib.sha256((repo/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('source digest differs: '+name)
    for name,record in load(root/'source-and-tools.json.gz')['files'].items():
        if hashlib.sha256(record['text'].encode()).hexdigest()!=record['sha256']:
            raise ValueError('archived source differs: '+name)
    previous = load(root/'inherited-v11-identity.json.gz')
    if any(identity['source_sha256'][name]!=expected for name,expected in previous['source_sha256'].items()):
        raise ValueError('predecessor source drift')
    source_audit = load(root/'source-audit.json.gz')
    if hashlib.sha256(source_audit['text'].encode()).hexdigest()!=source_audit['sha256']:
        raise ValueError('matched OpenROAD source archive differs')
    inputs = load(root/'train-inputs.json.gz')
    predictions = load(root/'predictions.json.gz')
    candidate = load(root/'candidate.json.gz')['models']
    protocol = load(root/'protocol.json.gz')
    report = load(root/'train-report.json.gz')
    oldinputs = load(root/'inherited-v11-nested-inputs.json.gz')
    contexts = load(root/'inherited-v11-nested-contexts.json.gz')
    nested.verify(oldinputs['upstream'],contexts)
    physical = load(root/'inherited-v11-train-operator-audit.json.gz')['rows']
    labels = {(r['source'],r['target_ps']):r for r in physical}
    banks = {(r['source'],r['target_ps']):r for r in oldinputs['banks']}
    downstream = {(r['source'],r['target_ps'],r['stage']):r for r in oldinputs['downstream']}
    checked_contexts = area_runtime = final_fit_runtime = deployment_runtime = 0
    with patch('builtins.open',side_effect=AssertionError('inference file')):
        with patch('pathlib.Path.open',side_effect=AssertionError('inference path file')):
            with patch('subprocess.Popen',side_effect=AssertionError('inference process')):
                for family,rows in inputs['area'].items():
                    for row in rows:
                        origin = labels[row['source'],row['target_ps']]
                        if row['role']!='train' or origin['role']!='train':
                            raise ValueError('nontrain area label')
                        close(row['synth_area_um2'],origin['synth_area_um2'])
                        close(row['grt_area_um2'],origin['grt_area_um2'])
                        f = geometry.operator_features(origin['query']) if family=='Add' else geometry.reduction_features(origin['query'])['intensive']
                        close(f,row['f'])
                    for row in predictions[family]['runtime_train']:
                        value = area.predict(candidate[family],row['f'])
                        close(value['predicted_grt_area_um2'],row['predicted'])
                        close(value['predicted_synth_area_um2'],row['predicted_synth'])
                        close(value['predicted_grt_synth_ratio'],row['predicted_ratio'])
                        area_runtime += 1
                for outer,rows in inputs['S'].items():
                    cache = {}
                    for row in rows:
                        key = row['source'],row['target_ps']
                        if key not in cache:
                            record = nested.route(outer,row['fold'],contexts)
                            cache[key] = {(c['path_class'],c['stage']):c['features'] for c in
                                local.state_controls(banks[key]['structure'],record['function'])}
                        close(row['f'],cache[key][row['path_class'],row['stage']])
                        close(row['actual'],downstream[row['source'],row['target_ps'],row['stage']]['actual'])
                        checked_contexts += 1
                for row in predictions['S']['runtime_train']:
                    # Immutable fitter's historical name refers to final-fit OOF contexts.
                    close(response.predict(candidate['native_valid']['function'],row['f']),row['predicted'])
                    final_fit_runtime += 1
    deployment = load(root/'deployment-cases.json.gz')
    with patch('builtins.open',side_effect=AssertionError('deployment file')):
        with patch('pathlib.Path.open',side_effect=AssertionError('deployment path file')):
            with patch('subprocess.Popen',side_effect=AssertionError('deployment process')):
                cache = {}
                for row in deployment['S']:
                    key = row['source'],row['target_ps']
                    if key not in cache:
                        cache[key] = {(c['path_class'],c['stage']):c['features'] for c in
                            local.state_controls(banks[key]['structure'],candidate['native_valid']['context_function'])}
                    close(row['f'],cache[key][row['path_class'],row['stage']])
                    close(response.predict(candidate['native_valid']['function'],row['f']),row['predicted'])
                    deployment_runtime += 1
    trial_rows = 0
    for family,record in report['results'].items():
        forms = protocol['S']['forms'] if family=='S' else protocol['area'][family]['forms']
        expected_trials = {(f['name'],alpha) for f in forms for alpha in protocol['alphas']}
        if {(t['form'],t['alpha']) for t in record['trials']}!=expected_trials or len(record['trials'])!=6:
            raise ValueError('finite trial grid differs')
        expected_observations = {(r['source'],r['target_ps'],r['stage']) for r in oldinputs['downstream']} if family=='S' else {
            (r['source'],r['target_ps']) for r in inputs['area'][family]}
        for trial in record['trials']:
            rows = predictions[family]['trial_LOSO'][f"{trial['form']}|{trial['alpha']}"]
            identities = [(r['source'],r['target_ps'],r['stage']) if family=='S' else
                          (r['source'],r['target_ps']) for r in rows]
            if set(identities)!=expected_observations or len(identities)!=len(expected_observations):
                raise ValueError('trial observation coverage differs')
            actual = trial_statistics(rows) if family=='S' else area_statistics(rows)
            close(actual,{k:trial[k] for k in actual})
            trial_rows += len(rows)
        selected = min(record['trials'],key=lambda t:(t['score'],len(next(
            f['features'] if family=='S' else f['mapping_features'] for f in forms if f['name']==t['form'])),-t['alpha']))
        close(selected,record['selected'])
        if family=='S':
            gates = dict(bank_median=selected['LOSO']['bank']['median']<=protocol['S']['bank_median_max'],
                raw_path_P95=selected['raw_path_LOSO']['P95']<=protocol['S']['raw_path_P95_max'],
                max_bank_source=selected['LOSO']['bank']['max']<=protocol['S']['max_bank_source_error'])
        else:
            limits = protocol['area'][family]['gates']
            gates = dict(median=selected['LOSO']['grt']['median']<=limits['median_max'],
                P95=selected['LOSO']['grt']['P95']<=limits['P95_max'],
                max_source=selected['LOSO']['grt']['max']<=limits['max_source_error_max'])
        close(gates,record['gates'])
        if record['train_gates_passed'] or all(gates.values()):
            raise ValueError('failed component promoted')
    if report['total_trials']!=18 or any(report[k] for k in ('validation_labels_read','independent_labels_read','public_D_changed')):
        raise ValueError('experiment boundary differs')
    if any(root.glob('evaluation*')):
        raise ValueError('unexpected consumed regression')
    settlement = load(root/'settlement.json')
    if any(settlement['increment_usage'].values()) or settlement['recorded_cumulative_ledger']['pending']:
        raise ValueError('unexpected physical calls')
    return dict(status='passed',area_train_points=134,semantic_banks=63,
        inherited_context_functions=92,new_context_fits=0,downstream_context_checks=checked_contexts,
        finite_trials=18,trial_path_statistics_recomputed=trial_rows,area_runtime_predictions=area_runtime,
        final_fit_context_predictions=final_fit_runtime,deployment_context_predictions=deployment_runtime,
        all_candidates_rejected=True,new_native_price_version=False,consumed_regression_run=False,
        source_files=len(identity['source_sha256']),new_EDA_calls=0,new_support_calls=0,
        online_file_reads=0,online_physical_calls=0,independent_labels_read=False,public_D_changed=False)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path)
    args = parser.parse_args()
    import json
    print(json.dumps(replay(args.root),indent=2))
