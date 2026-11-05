"""Audited M2 primitive fitting; sealed independent tests never select a model."""
import argparse
from collections import Counter
import json
from importlib.metadata import version
import os
from pathlib import Path
import shutil
import sys

from .budget import Ledger
from .model_collection import sha, write
from .model_features import infer, FEATURES, VERSION
from .model_training import algorithms, metric

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name('configs')/'model_asap7_m2_fit_v1.json'
SUFFIX = Path('asap7/arithmetic_probe/base')


def read(path): return json.loads(Path(path).read_text())


def recovered_rows(folder, item):
    from .model_m2_cec_resume import verify_admission
    from .model_m2_cec import verify_proof
    from .model_mul_interval_fit import verify_measurement
    from .model_samples import verify_capture_banks
    from .model_features import features
    a = verify_admission(folder); t = item['task']; d = folder/'runs'/t['id']; m = read(d/'manifest.json')
    if m['status'] != 'completed' or not m.get('structural_cec_resume') or m['admission_sha256'] != sha(folder/'admission.json'):
        raise ValueError('incomplete/unbound CEC recovery')
    if sha(d/'input.sv') != t['rtl_sha256'] or sha(d/'sample-contract.json') != t['sample_contract_sha256']:
        raise ValueError('recovery changed sample source/contract')
    reuse = m['checkpoint_reuse']
    if reuse['proof_path'] != item['proof'] or reuse['proof_sha256'] != sha(item['proof']):
        raise ValueError('recovery changed proof')
    verify_proof(item['proof'], d/'results'/SUFFIX/'4_before_rsz_lec.v', d/'results'/SUFFIX/'4_after_rsz_lec.v')
    ledger = {e['id']: e for e in read(Ledger().path)['entries']}
    for command in m['commands']:
        e = ledger[command['budget_reservation_id']]
        if e['status'] != 'completed' or e.get('admission_sha256') != sha(folder/'admission.json') or e.get('task_id') != t['id'] or command['exit_code']:
            raise ValueError('unpaid or failed recovery leaf')
    cells = read(d/'liberty_cells.json')['cells']; specs = read(d/'sample-contract.json')['labels']
    verify_measurement(d, m, t, {'id': a['id']}, cells)
    rows = []
    for stage in m['metrics']:
        prefix = d/'reports'/SUFFIX/('vulsim_'+stage['stage'])
        banks = verify_capture_banks(prefix, d/'sample-contract.json', cells)
        if banks != stage.get('model_capture_banks', {}): raise ValueError('changed recovered capture structure')
        instances = [line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
        labels = {v['id']: v for v in stage['model_labels']}
        for spec in specs:
            core = sum(cells[master]['area_um2'] for name, master in instances if master in cells and not cells[master]['sequential'] and name.startswith(spec['arithmetic_scope']))
            if core <= 0: raise ValueError('missing primitive core area')
            label = labels[spec['id']]
            rows.append({'id': t['id']+'/'+spec['id']+'/'+stage['stage'], 'task_id': t['id'], 'split': t['split'], 'family': t['family'],
                'stage': stage['stage'], 'operation': spec['operation'], 'rtl_operation': spec['rtl_operation'], 'spec': spec,
                'features': features(spec['lhs_width'], spec['rhs_width'], spec['result_width'], spec['fanout'], 1500, t['period_ps']),
                'delay_ps': label['data_delay_ps'], 'comb_area_um2': core, 'period_ps': t['period_ps'],
                'observed_H_ps': t['period_ps']-label['data_delay_ps']-label['slack_ps'], 'path_slack_ps': label['slack_ps'],
                'whole_setup_slack_ps': stage['setup_worst_slack_ps'], 'whole_hold_slack_ps': stage['hold_worst_slack_ps'],
                'manifest_sha256': sha(d/'manifest.json'), 'source_sha256': t['rtl_sha256'], 'bank_counts': banks.get(spec['id']), 'reference_role': t['reference_role']})
    return rows, {'task_id': t['id'], 'manifest_sha256': sha(d/'manifest.json'),
                  'peak_RSS_MiB': max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024,
                  'grt_walltime_s': next(c['walltime_s'] for c in m['commands'] if c['log'].endswith('/grt.log'))}


def extract(plan, recovery, out):
    from .model_m2_collection import verify_plan, extract_rows
    from .model_m2_cec_resume import verify_admission
    p = verify_plan(plan); a = verify_admission(recovery)
    if a['parent_plan_sha256'] != sha(plan) or read(recovery/'progress.json')['phase'] != 'recovery_complete':
        raise ValueError('recovery incomplete or wrong parent')
    replacement = {v['task']['id'] for v in a['tasks']}
    ids = {t['id'] for t in p['tasks'] if t['split'] in ('train', 'validation')}
    data = extract_rows(plan.parent, ids-replacement)
    for item in a['tasks']:
        rows, run = recovered_rows(recovery, item); data['rows'].extend(rows); data['runs'].append(run)
    data['rows'].sort(key=lambda r: r['id']); data['runs'].sort(key=lambda r: r['task_id'])
    data.update(version='asap7-m2-primitives-dataset-v2', mode='fitting',
                recovery_admission_path=str((recovery/'admission.json').resolve()), recovery_admission_sha256=sha(recovery/'admission.json'),
                expected_task_ids=sorted(ids), fitting_protocol_sha256=sha(CONFIG),
                recovery_producer_sha256=a['sources'], full_collection_complete=True)
    expected = {t['id']+'/'+s['id']+'/'+stage for t in p['tasks'] if t['id'] in ids
                for s in read(t['sample_contract'])['labels'] for stage in ('synth', 'grt')}
    if {r['id'] for r in data['rows']} != expected or len(data['rows']) != len(expected) or {r['task_id'] for r in data['runs']} != ids:
        raise ValueError('incomplete sample/task/stage coverage')
    if out.exists(): raise ValueError('preserve existing dataset')
    write(out, data)
    print(json.dumps({'status': 'extracted', 'tasks': len(ids), 'rows': len(data['rows']), 'by_split': dict(Counter(r['split'] for r in data['rows']))}), flush=True)


def quality(rows, predictor, field, margin=0):
    cfg = read(CONFIG); quantity = 'delay' if field == 'delay_ps' else 'area'; floor = 1.5 if quantity == 'delay' else 1e-4
    values = [infer(predictor, r['features'])+margin for r in rows]
    q = metric([r[field] for r in rows], values, floor)
    q['status'] = 'passed' if all(q[k+'_relative_error'] <= cfg['quality_gates'][quantity+'_'+k+'_relative_error_max'] for k in ('median', 'p95')) else 'failed'
    if quantity == 'delay':
        false = sum(pred <= r['delay_ps']*ratio < r['delay_ps'] for r, pred in zip(rows, values) for ratio in cfg['feasibility_ratios'])
        actual = sum(pred <= r['period_ps']-r['observed_H_ps'] < r['delay_ps'] for r, pred in zip(rows, values))
        q.update(false_feasible=false, denominator=len(rows)*len(cfg['feasibility_ratios']), actual_target_false_feasible=actual, actual_target_denominator=len(rows))
        if max(false/q['denominator'], actual/len(rows)) > cfg['quality_gates']['false_feasible_fraction_max']:
            q['status'] = 'failed'
    return q


def choose(rows, field):
    import numpy as np
    train = [r for r in rows if r['split'] == 'train']; validation = [r for r in rows if r['split'] == 'validation']
    if not train or not validation: raise ValueError('independent train and validation required')
    candidates = []; exported = {}
    for name, predictor in algorithms(train, field, 1.5 if field == 'delay_ps' else 1e-4):
        margin = float(np.quantile([max(0, r[field]-infer(predictor, r['features'])) for r in validation], .95))+1.5 if field == 'delay_ps' else 0.
        q = quality(validation, predictor, field, margin); point = quality(validation, predictor, field)
        candidates.append({'algorithm': name, 'quality': q, 'point_quality': point, 'delay_margin_ps': margin})
        exported[name] = predictor
    chosen = min(candidates, key=lambda c: (c['quality']['status'] != 'passed',
        c['quality']['MAE']/max(1e-4, sum(r[field] for r in validation)/len(validation)),
        c['quality']['p95_relative_error'], len(json.dumps(exported[c['algorithm']])), c['algorithm']))
    return {'predictor': exported[chosen['algorithm']], 'delay_margin_ps': chosen['delay_margin_ps'], 'algorithm': chosen['algorithm'],
            'quality': chosen['quality'], 'candidates': candidates}


def validate_data(path):
    from .model_m2_collection import verify_plan
    d = read(path); p = verify_plan(Path(d['plan_path']))
    if d.get('version') != 'asap7-m2-primitives-dataset-v2' or d.get('mode') != 'fitting' or d['failures'] or d['old_test_labels_used']:
        raise ValueError('wrong fitting data role')
    if d['plan_sha256'] != sha(d['plan_path']) or d['fitting_protocol_sha256'] != sha(CONFIG) or d['recovery_admission_sha256'] != sha(d['recovery_admission_path']):
        raise ValueError('changed fitting identity')
    tasks = {t['id']: t for t in p['tasks'] if t['split'] in ('train', 'validation')}
    expected = {t['id']+'/'+s['id']+'/'+stage for t in tasks.values() for s in read(t['sample_contract'])['labels'] for stage in ('synth', 'grt')}
    if set(d['expected_task_ids']) != set(tasks) or {r['id'] for r in d['rows']} != expected or len(d['rows']) != len(expected):
        raise ValueError('incomplete fitting coverage')
    for r in d['rows']:
        t = tasks[r['task_id']]
        if r['split'] != t['split'] or r['source_sha256'] != t['rtl_sha256'] or r['period_ps'] != t['period_ps']:
            raise ValueError('row crossed source/split/target')
    return d, p


def fit(data_path, out):
    d, p = validate_data(data_path); out.mkdir(parents=True, exist_ok=False)
    candidate = {'version': 'asap7-m2-primitives-candidate-v1', 'quality_status': 'awaiting_independent_test',
                 'target_platform': 'asap7', 'feature_schema': VERSION, 'ABC_ps': 1500, 'IO': '0.2T', 'stages': {},
                 'support_scope': read(CONFIG)['production_domain'], 'full_D_ready': False}
    report = {'version': 'asap7-m2-primitives-fit-report-v1', 'stages': {}}
    for stage in ('synth', 'grt'):
        models = {}; details = {}
        for operation in sorted({r['operation'] for r in d['rows']}):
            group = [r for r in d['rows'] if r['stage'] == stage and r['operation'] == operation]
            delay = choose(group, 'delay_ps'); area = choose(group, 'comb_area_um2')
            ready = delay['quality']['status'] == area['quality']['status'] == 'passed'
            conditions = sorted({(r['spec']['lhs_width'], r['spec']['rhs_width'], r['spec']['result_width'], r['spec']['result_shape'], r['period_ps']) for r in group})
            models[operation] = {'delay': delay['predictor'], 'delay_margin_ps': delay['delay_margin_ps'], 'area': area['predictor'],
                                 'validation_ready': ready, 'quality_status': 'awaiting_independent_test' if ready else 'failed_validation',
                                 'joint_domain': [{'lhs_width': w, 'rhs_width': rhs, 'result_width': result, 'result_shape': shape, 'sdc_period_ps': period,
                                                   'abc_target_ps': 1500, 'production_capture_fanout': 1} for w, rhs, result, shape, period in conditions]}
            details[operation] = {'delay': delay, 'area': area, 'validation_ready': ready,
                                  'counts': dict(Counter(r['split'] for r in group))}
        ready = all(m['validation_ready'] for m in models.values())
        candidate['stages'][stage] = {'operations': models, 'validation_ready': ready}
        report['stages'][stage] = {'operations': details, 'validation_ready': ready, 'passing_operations': sum(m['validation_ready'] for m in models.values()), 'operation_count': len(models)}
    # References are designated train F1 t0 only, with result semantics retained.
    refs = [r for r in d['rows'] if r['reference_role'] == 'training_primitive_reference' and r['stage'] == 'grt']
    candidate['training_references'] = {r['rtl_operation']+'/'+str(r['spec']['lhs_width']):
        {'D_ref_ps': r['delay_ps'], 'H_ref_ps': r['observed_H_ps'], 'source_row': r['id']} for r in refs}
    report['environment'] = {'python': sys.version, 'numpy': version('numpy'), 'scikit-learn': version('scikit-learn'),
        'threads': {k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS')}, 'seed': 20261102}
    write(out/'candidate.json', candidate); write(out/'fit-report.json', report)
    paths = [Path(__file__), CONFIG, Path(__file__).with_name('model_training.py'), Path(__file__).with_name('model_features.py'),
             Path(__file__).with_name('model_m2_collection.py'), Path(__file__).with_name('model_m2_cec.py'), Path(__file__).with_name('model_m2_cec_resume.py')]
    sources = {}
    for path in paths:
        name = str(path.relative_to(ROOT)); dst = out/'source'/name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dst); sources[name] = sha(path)
    freeze = {'version': 'asap7-m2-primitives-fit-freeze-v1', 'plan_path': d['plan_path'], 'plan_sha256': d['plan_sha256'],
              'dataset_path': str(data_path.resolve()), 'dataset_sha256': sha(data_path), 'protocol_sha256': sha(CONFIG),
              'candidate_sha256': sha(out/'candidate.json'), 'fit_report_sha256': sha(out/'fit-report.json'), 'sources': sources,
              'grt_validation_ready': candidate['stages']['grt']['validation_ready'], 'test_consumed': False}
    write(out/'fit-freeze.json', freeze)
    if freeze['grt_validation_ready']: write(out/'selection-freeze.json', {**freeze, 'version': 'asap7-m2-primitives-selection-v1'})
    print(json.dumps({'stages': {s: {k: v for k, v in v.items() if k != 'operations'} for s, v in report['stages'].items()},
                      'independent_test_eligible': freeze['grt_validation_ready']}), flush=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('action', choices=['extract', 'fit', 'reproduce', 'verify'])
    ap.add_argument('--plan', type=Path); ap.add_argument('--recovery', type=Path); ap.add_argument('--data', type=Path); ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--selection', type=Path)
    args = ap.parse_args()
    if args.action == 'extract': extract(args.plan.resolve(), args.recovery.resolve(), args.out.resolve())
    elif args.action == 'fit': fit(args.data.resolve(), args.out.resolve())
    elif args.action == 'reproduce':
        freeze = verify_fit(args.selection.resolve())
        fit(Path(freeze['dataset_path']), args.out.resolve())
        for name, key in (('candidate.json', 'candidate_sha256'), ('fit-report.json', 'fit_report_sha256')):
            if sha(args.out/name) != freeze[key]: raise ValueError('refit differs: '+name)
        write(args.out/'reproduction.json', {'status': 'passed', 'parent_fit_freeze_sha256': sha(args.selection), 'test_labels_read': False})
    else:
        freeze = verify_fit(args.selection.resolve())
        print(json.dumps({'status': 'verified', 'grt_validation_ready': freeze['grt_validation_ready']}))


def verify_fit(path):
    f = read(path); folder = path.parent
    if f['version'] not in ('asap7-m2-primitives-fit-freeze-v1', 'asap7-m2-primitives-selection-v1') or f['test_consumed'] is not False:
        raise ValueError('wrong fit freeze')
    if sha(CONFIG) != f['protocol_sha256'] or sha(f['dataset_path']) != f['dataset_sha256']:
        raise ValueError('changed fitting data/protocol')
    for name, h in f['sources'].items():
        if sha(ROOT/name) != h or sha(folder/'source'/name) != h:
            raise ValueError('changed fitting source')
    for name, key in (('candidate.json', 'candidate_sha256'), ('fit-report.json', 'fit_report_sha256')):
        if sha(folder/name) != f[key]: raise ValueError('changed frozen predictor/report')
    data, _ = validate_data(Path(f['dataset_path'])); candidate = read(folder/'candidate.json'); report = read(folder/'fit-report.json')
    for stage, value in candidate['stages'].items():
        for op, model in value['operations'].items():
            rows = [r for r in data['rows'] if r['stage'] == stage and r['operation'] == op and r['split'] == 'validation']
            delay = quality(rows, model['delay'], 'delay_ps', model['delay_margin_ps']); area = quality(rows, model['area'], 'comb_area_um2')
            detail = report['stages'][stage]['operations'][op]
            if delay != detail['delay']['quality'] or area != detail['area']['quality'] or model['validation_ready'] != (delay['status'] == area['status'] == 'passed'):
                raise ValueError('validation quality does not recompute')
    ready = all(m['validation_ready'] for m in candidate['stages']['grt']['operations'].values())
    if ready != f['grt_validation_ready']: raise ValueError('wrong release decision')
    if path.name == 'selection-freeze.json' and not ready: raise ValueError('unready selection')
    return f


if __name__ == '__main__': main()
