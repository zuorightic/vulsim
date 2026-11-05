"""Versioned exact-width alternative to pooled M2 primitive fitting."""
import argparse
from collections import Counter
import json
from pathlib import Path
import shutil

from . import model_m2_fit as base
from .model_collection import sha, write
from .model_features import infer
from .model_training import metric

CONFIG = Path(__file__).with_name('configs')/'model_asap7_m2_fit_v2.json'


def key(row):
    s = row['spec']
    return '/'.join(str(s[k]) for k in ('lhs_width', 'rhs_width', 'result_width'))


def predict(model, row, quantity):
    entry = model['slices'][key(row)] if model['kind'] == 'exact_width_slices' else model
    return infer(entry['predictor'], row['features'])+(entry['delay_margin_ps'] if quantity == 'delay' else 0)


def quality(rows, model, quantity):
    # Evaluate the exact deployed predictions with the original quality code.
    # A row's synthetic feature is internal to this reporting adapter only;
    # it is never a fitted feature or a model input.
    field = 'delay_ps' if quantity == 'delay' else 'comb_area_um2'
    adjusted = [{**r, 'features': {**r['features'], 'lhs_width': predict(model, r, quantity)}} for r in rows]
    identity = {'kind': 'linear', 'features': ['lhs_width'], 'coefficients': [1.], 'intercept': 0.}
    return base.quality(adjusted, identity, field)


def choice(rows, quantity, pooled):
    field = 'delay_ps' if quantity == 'delay' else 'comb_area_um2'
    baseline = {'kind': 'pooled', 'predictor': pooled['predictor'], 'delay_margin_ps': pooled['delay_margin_ps'], 'algorithm': pooled['algorithm']}
    sliced = {'kind': 'exact_width_slices', 'slices': {}}
    reports = {}
    for identity in sorted({key(r) for r in rows}):
        group = [r for r in rows if key(r) == identity]
        c = base.choose(group, field)
        sliced['slices'][identity] = {k: c[k] for k in ('predictor', 'delay_margin_ps', 'algorithm')}
        reports[identity] = c
    validation = [r for r in rows if r['split'] == 'validation']
    candidates = [(name, model, quality(validation, model, quantity)) for name, model in (('pooled', baseline), ('exact_width_slices', sliced))]
    chosen = min(candidates, key=lambda c: (c[2]['status'] != 'passed', c[2]['MAE'], c[2]['p95_relative_error'], len(json.dumps(c[1])), c[0]))
    return chosen[1], {'selected': chosen[0], 'quality': chosen[2], 'partition_candidates': {n: q for n, _, q in candidates}, 'slices': reports}


def fit(data_path, prior, out):
    freeze = base.verify_fit(prior/'fit-freeze.json')
    if freeze['dataset_sha256'] != sha(data_path): raise ValueError('partition successor changed fitting data')
    data, _ = base.validate_data(data_path); candidate = base.read(prior/'candidate.json'); old_report = base.read(prior/'fit-report.json')
    out.mkdir(parents=True, exist_ok=False)
    candidate.update(version='asap7-m2-primitives-candidate-v2', parent_candidate_sha256=sha(prior/'candidate.json'))
    report = {'version': 'asap7-m2-primitives-fit-report-v2', 'environment': old_report['environment'], 'stages': {}}
    for stage in ('synth', 'grt'):
        models = {}; details = {}
        for op, old in candidate['stages'][stage]['operations'].items():
            rows = [r for r in data['rows'] if r['stage'] == stage and r['operation'] == op]
            delay, dr = choice(rows, 'delay', old_report['stages'][stage]['operations'][op]['delay'])
            area, ar = choice(rows, 'area', old_report['stages'][stage]['operations'][op]['area'])
            ready = dr['quality']['status'] == ar['quality']['status'] == 'passed'
            models[op] = {'delay': delay, 'area': area, 'joint_domain': old['joint_domain'], 'validation_ready': ready,
                          'quality_status': 'awaiting_independent_test' if ready else 'failed_validation'}
            details[op] = {'delay': dr, 'area': ar, 'validation_ready': ready, 'counts': dict(Counter(r['split'] for r in rows))}
        ready = all(m['validation_ready'] for m in models.values())
        candidate['stages'][stage] = {'operations': models, 'validation_ready': ready}
        report['stages'][stage] = {'operations': details, 'validation_ready': ready, 'passing_operations': sum(m['validation_ready'] for m in models.values()), 'operation_count': len(models)}
    write(out/'candidate.json', candidate); write(out/'fit-report.json', report)
    sources = {**freeze['sources'], str(Path(__file__).relative_to(base.ROOT)): sha(__file__), str(CONFIG.relative_to(base.ROOT)): sha(CONFIG)}
    for name in sources:
        dst = out/'source'/name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(base.ROOT/name, dst)
    frozen = {'version': 'asap7-m2-primitives-fit-freeze-v2', 'dataset_path': str(data_path.resolve()), 'dataset_sha256': sha(data_path),
              'parent_fit_path': str((prior/'fit-freeze.json').resolve()), 'parent_fit_sha256': sha(prior/'fit-freeze.json'),
              'plan_path': freeze['plan_path'], 'plan_sha256': freeze['plan_sha256'],
              'protocol_sha256': sha(CONFIG), 'base_protocol_sha256': sha(base.CONFIG), 'candidate_sha256': sha(out/'candidate.json'),
              'fit_report_sha256': sha(out/'fit-report.json'), 'sources': sources, 'test_consumed': False,
              'grt_validation_ready': candidate['stages']['grt']['validation_ready']}
    write(out/'fit-freeze.json', frozen)
    if frozen['grt_validation_ready']: write(out/'selection-freeze.json', {**frozen, 'version': 'asap7-m2-primitives-selection-v2'})
    print(json.dumps({'stages': {s: {k: v for k, v in v.items() if k != 'operations'} for s, v in report['stages'].items()},
                      'independent_test_eligible': frozen['grt_validation_ready']}), flush=True)


def verify_fit(path):
    f = base.read(path); folder = path.parent
    if f['version'] not in ('asap7-m2-primitives-fit-freeze-v2', 'asap7-m2-primitives-selection-v2') or f['test_consumed'] is not False:
        raise ValueError('wrong partition fit freeze')
    if sha(CONFIG) != f['protocol_sha256'] or sha(base.CONFIG) != f['base_protocol_sha256'] or sha(f['dataset_path']) != f['dataset_sha256'] or sha(f['parent_fit_path']) != f['parent_fit_sha256']:
        raise ValueError('changed partition fitting identity')
    base.verify_fit(Path(f['parent_fit_path']))
    for name, h in f['sources'].items():
        if sha(base.ROOT/name) != h or sha(folder/'source'/name) != h: raise ValueError('changed partition source')
    for name, field in (('candidate.json', 'candidate_sha256'), ('fit-report.json', 'fit_report_sha256')):
        if sha(folder/name) != f[field]: raise ValueError('changed partition predictor/report')
    data, _ = base.validate_data(Path(f['dataset_path'])); candidate = base.read(folder/'candidate.json'); report = base.read(folder/'fit-report.json')
    for stage, value in candidate['stages'].items():
        for op, model in value['operations'].items():
            rows = [r for r in data['rows'] if r['stage'] == stage and r['operation'] == op and r['split'] == 'validation']
            for q in ('delay', 'area'):
                if quality(rows, model[q], q) != report['stages'][stage]['operations'][op][q]['quality']: raise ValueError('partition validation does not recompute')
    ready = all(m['validation_ready'] for m in candidate['stages']['grt']['operations'].values())
    if ready != f['grt_validation_ready'] or path.name == 'selection-freeze.json' and not ready: raise ValueError('wrong partition release decision')
    return f


def main():
    ap = argparse.ArgumentParser(description=__doc__); ap.add_argument('action', choices=['fit', 'reproduce', 'verify'])
    ap.add_argument('--data', type=Path); ap.add_argument('--prior', type=Path); ap.add_argument('--selection', type=Path); ap.add_argument('--out', type=Path, required=True)
    args = ap.parse_args()
    if args.action == 'fit': fit(args.data.resolve(), args.prior.resolve(), args.out.resolve())
    elif args.action == 'verify': print(json.dumps({'status': 'verified', 'ready': verify_fit(args.selection)['grt_validation_ready']}))
    else:
        f = verify_fit(args.selection)
        fit(Path(f['dataset_path']), Path(f['parent_fit_path']).parent, args.out.resolve())
        for name, field in (('candidate.json', 'candidate_sha256'), ('fit-report.json', 'fit_report_sha256')):
            if sha(args.out/name) != f[field]: raise ValueError('partition refit differs')
        write(args.out/'reproduction.json', {'status': 'passed', 'parent_fit_sha256': sha(args.selection), 'test_labels_read': False})


if __name__ == '__main__': main()
