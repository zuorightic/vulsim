"""Replay train attribution, nested context isolation, and rejection gates."""
import argparse
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import re
from statistics import mean
from unittest.mock import patch

from . import nested_control_contexts as nested, centered_response as response
from .common_centered_replay_v1 import close, load
from .rebuffer_context_replay_v6 import verify_path
from . import transition_incidence_features_v10 as features


def percentile(values, fraction):
    values = sorted(values)
    index = (len(values)-1)*fraction
    low = int(index)
    return values[low]+(values[min(low+1,len(values)-1)]-values[low])*(index-low)


def statistics(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row['group']].append(abs(row['predicted']/row['actual']-1))
    errors = {group:mean(values) for group,values in groups.items()}
    median, p95 = percentile(list(errors.values()),.5), percentile(list(errors.values()),.95)
    return dict(rows=len(rows),sources=len(groups),median=median,P95=p95,max=max(errors.values()),
        status='passed' if median<=.15 and p95<=.35 else 'failed',source_mean_errors=errors)


def trial_statistics(rows):
    banks = defaultdict(list)
    for row in rows:
        banks[row['group'],row['target_ps']].append(row)
    cohorts = dict(bank=[dict(group=group,actual=max(r['actual'] for r in rs),
        predicted=max(r['predicted'] for r in rs)) for (group,_),rs in banks.items()],
        path=rows,service=[r for r in rows if not r['f']['branch_native']],
        native=[r for r in rows if r['f']['branch_native']],
        all_zero=[r for r in rows if not r['f']['reset_has_one']],
        mixed=[r for r in rows if r['f']['reset_has_one']])
    scores = []
    for rs in cohorts.values():
        groups = defaultdict(list)
        for row in rs:
            groups[row['group']].append(math.log(max(row['predicted'],1e-9)/row['actual'])**2)
        scores.append(mean(mean(values) for values in groups.values()))
    errors = [abs(r['predicted']/r['actual']-1) for r in rows]
    return dict(score=max(scores),LOSO={name:statistics(rs) for name,rs in cohorts.items()},
        raw_path_LOSO=dict(rows=len(rows),median=percentile(errors,.5),
                          P95=percentile(errors,.95),max=max(errors)))


def replay(root=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo/'experiments/arithmetic/evidence/common_repair_burden_v11'
    identity = load(root/'identity.json')
    for name, expected in identity['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != expected:
            raise ValueError('evidence digest differs: '+name)
    for name, expected in identity['source_sha256'].items():
        if hashlib.sha256((repo/name).read_bytes()).hexdigest() != expected:
            raise ValueError('source digest differs: '+name)
    for name, record in load(root/'source-and-tools.json.gz')['files'].items():
        if hashlib.sha256(record['text'].encode()).hexdigest() != record['sha256']:
            raise ValueError('archived source differs: '+name)
    audit = load(root/'train-path-audit.json.gz')
    proof = load(root/'train-path-proof-cases.json.gz')
    if audit['paths'] != 648 or len(audit['missing_paths']) != 108 or len(proof['cases']) != 648:
        raise ValueError('path coverage differs')
    negatives = 0
    hold_counts = {}
    for row, case in zip(audit['rows'],proof['cases'],strict=True):
        verify_path(case,proof['pin_classes'])
        for key in ('source','target_ps','stage'):
            close(row[key],case[key])
        close(row['label']['id'],case['path_id'])
        if hashlib.sha256(row['raw_points'].encode()).hexdigest() != row['points_sha256'] or hashlib.sha256(row['raw_report'].encode()).hexdigest() != row['report_sha256']:
            raise ValueError('raw path identity differs')
        cell = hold = 0.
        count = 0
        for (a,ta),(b,tb) in zip(case['points'],case['points'][1:]):
            if '/' in a and a.rsplit('/',1)[0] == b.rsplit('/',1)[0]:
                cell += tb-ta
                if re.search(r'(^|/)hold\d+$',a.rsplit('/',1)[0]):
                    hold += tb-ta; count += 1
        close(cell,row['cell_ps']);close(hold,row['hold_named_cell_ps']);close(count,row['hold_named_cells'])
        # Labels and points are saved with independently rounded decimal text.
        if not math.isclose(cell+sum(case['wires']),row['label']['delay_ps'],abs_tol=1e-4,rel_tol=0):
            raise ValueError('rounded path delay is not conserved')
        close(row['R_ps'],row['label']['delay_ps']+row['label']['H_ps'])
        close(row['R_ps'],(.8 if row['label']['kind']=='port' else 1.)*row['target_ps']-row['label']['slack_ps'])
        key = row['stage'],row['path_class']
        hold_counts[key] = hold_counts.get(key,0)+(count>0)
        master,src,dst = case['arcs'][0]
        modified = deepcopy(proof['pin_classes'])
        modified[master]['timing_arcs'] = [a for a in modified[master]['timing_arcs'] if a != [src,dst]]
        try:
            verify_path(case,modified)
        except ValueError as error:
            if 'actual Liberty' not in str(error):
                raise
            negatives += 1
        else:
            raise ValueError('deleted actual Liberty arc accepted')
    if hold_counts['grt','input_valid'] != 63 or any(hold_counts['grt',cls] for cls in ('native_valid','native_enable','external_valid')):
        raise ValueError('hold scope differs')
    operators = load(root/'train-operator-audit.json.gz')
    labels = load(root/'train-operator-labels.json.gz')['files']
    for row in operators['rows']:
        actual = {}
        for stage in ('synth','grt'):
            record = labels[row['source_paths'][stage]]
            if hashlib.sha256(record['text'].encode()).hexdigest() != row['source_sha256'][stage]:
                raise ValueError('operator physical origin differs')
            actual[stage] = json.loads(record['text'])
            close(row[stage+'_area_um2'],actual[stage]['comb_area_um2'])
            close(row[stage+'_delay_ps'],actual[stage]['operator_delay_ps'])
        close(row['area_growth_um2'],row['grt_area_um2']-row['synth_area_um2'])
        close(row['delay_growth_ps'],row['grt_delay_ps']-row['synth_delay_ps'])
        if row['role'] != 'train':
            raise ValueError('operator source role differs')
    inputs = load(root/'nested-inputs.json.gz')
    contexts = load(root/'nested-contexts.json.gz')
    lineage = nested.verify(inputs['upstream'],contexts)
    origin = load(root/'inherited-v10-contexts.json.gz')['contexts']
    for outer in contexts['folds']+['all_train']:
        excluded = [] if outer=='all_train' else [outer]
        close(contexts['contexts'][nested.digest(excluded)]['function'],origin[outer]['function'])
    predictions = load(root/'nested-predictions-compact.json.gz')
    enables = {(r['source'],r['target_ps'],r['stage']):r for r in inputs['upstream']}
    downstream = {(r['source'],r['target_ps'],r['stage']):r for r in inputs['downstream']}
    context_fields = {'enable_context_R_ps','predicted_enable_pressure','native_enable_pressure',
        'reset_enable_pressure','native_reset_enable_pressure','predicted_enable_relaxation',
        'native_enable_relaxation'}
    checks = 0
    with patch('subprocess.Popen',side_effect=AssertionError('inference subprocess')):
        with patch('builtins.open',side_effect=AssertionError('inference file read')):
            with patch('pathlib.Path.open',side_effect=AssertionError('inference path read')):
                for bank in inputs['banks']:
                    close(features.state_structure(bank['spec'],bank['target_ps']),bank['structure'])
                    actual_features = {(r['path_class'],r['stage']):r['features'] for r in
                        features.state_controls(bank['structure'],origin['all_train']['function'])}
                    for row in inputs['upstream']+inputs['downstream']:
                        if (row['source'],row['target_ps']) == (bank['source'],bank['target_ps']):
                            close(actual_features[row['path_class'],row['stage']],row['f'])
                for method, groups in predictions['contexts'].items():
                    for outer, rows in groups.items():
                        for row in rows:
                            record = nested.route(outer,row['fold'],contexts) if method=='nested_double_exclusion' else origin[outer]
                            enable = enables[row['source'],row['target_ps'],row['stage']]
                            value = response.predict(record['function'],enable['f'])
                            close(value,row['f']['enable_context_R_ps'])
                            pressure = math.log2(1+value/row['target_ps'])
                            close(pressure,row['f']['predicted_enable_pressure'])
                            close(row['f']['branch_native']*pressure,row['f']['native_enable_pressure'])
                            reset,native = row['f']['reset_has_one'],row['f']['branch_native']
                            close(reset*pressure,row['f']['reset_enable_pressure'])
                            close(native*reset*pressure,row['f']['native_reset_enable_pressure'])
                            relaxation = (.25*max(0.,row['target_ps']-value)+.01*value)/row['target_ps']
                            close(relaxation,row['f']['predicted_enable_relaxation'])
                            close(native*relaxation,row['f']['native_enable_relaxation'])
                            original = downstream[row['source'],row['target_ps'],row['stage']]
                            close({k:v for k,v in row['f'].items() if k not in context_fields},
                                  {k:v for k,v in original['f'].items() if k not in context_fields})
                            close(row['actual'],original['actual'])
                            checks += 1
                candidate = inputs['candidate']
                close(candidate['context_function'],origin['all_train']['function'])
                for row in predictions['runtime_train']:
                    upstream = enables[row['source'],row['target_ps'],row['stage']]
                    close(response.predict(candidate['context_function'],upstream['f']),
                          row['f']['enable_context_R_ps'])
                    value = response.predict(candidate['function'],row['f'])
                    if candidate['reference']:
                        value *= row['f'][candidate['reference']]
                    close(value,row['predicted'])
    report = load(root/'nested-train-report.json.gz')
    protocol = load(root/'nested-protocol.json.gz')
    for trial in report['trials']:
        rows = predictions['trial_LOSO']['|'.join(map(str,(trial['method'],trial['form'],trial['alpha'])))]
        if len(rows) != len(downstream):
            raise ValueError('trial path coverage differs')
        close(trial_statistics(rows),{k:trial[k] for k in ('score','LOSO','raw_path_LOSO')})
        for row in rows:
            original = downstream[row['source'],row['target_ps'],row['stage']]
            close(row['actual'],original['actual'])
            if row['role'] != 'train' or row['fold'] != original['fold']:
                raise ValueError('trial source role or group differs')
    chosen = min([t for t in report['trials'] if t['method']==protocol['eligible_method']],
        key=lambda t:(t['score'],len(next(f['features'] for f in protocol['forms'] if f['name']==t['form'])),-t['alpha']))
    close(chosen,report['selected'])
    close(predictions['LOSO'],predictions['trial_LOSO']['|'.join(map(str,
        (chosen['method'],chosen['form'],chosen['alpha'])))])
    selected = report['selected']
    expected_gates = dict(bank_median=selected['LOSO']['bank']['median']<=protocol['promotion_gates']['bank_median_max'],
        raw_path_P95=selected['raw_path_LOSO']['P95']<=protocol['promotion_gates']['raw_path_P95_max'],
        worst_bank_source=selected['LOSO']['bank']['max']<=protocol['promotion_gates']['bank_max_source_error_max'])
    close(expected_gates,report['promotion_gates'])
    if report['train_gates_passed'] or all(expected_gates.values()) or len(report['trials']) != 12:
        raise ValueError('failed train gates were overridden')
    if report['required_next_action'] != 'archive rejected train experiment; no new native price or consumed regression':
        raise ValueError('rejected train experiment was promoted')
    if list(root.glob('evaluation*')) or any(report[k] for k in ('validation_labels_read','independent_labels_read','public_D_changed')):
        raise ValueError('rejection boundary differs')
    settlement = load(root/'settlement.json')
    if any(settlement['increment_usage'].values()) or settlement['recorded_cumulative_ledger']['pending']:
        raise ValueError('unexpected physical work')
    return dict(status='passed',strict_train_paths=648,missing_synth_source_paths=108,
        missing_actual_arc_negatives=negatives,operator_train_points=len(operators['rows']),
        **{k:v for k,v in lineage.items() if k not in ('status','independent_labels_read')},downstream_context_checks=checks,
        runtime_candidate_predictions=len(predictions['runtime_train']),finite_trials=12,
        trial_path_statistics_recomputed=12*len(downstream),semantic_banks_rebuilt=len(inputs['banks']),
        candidate_rejected=True,consumed_regression_run=False,new_native_price_version=False,
        source_files=len(identity['source_sha256']),new_EDA_calls=0,new_support_calls=0,
        online_file_reads=0,online_physical_calls=0,independent_labels_read=False,public_D_changed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path)
    args = parser.parse_args()
    print(json.dumps(replay(args.root),indent=2))
