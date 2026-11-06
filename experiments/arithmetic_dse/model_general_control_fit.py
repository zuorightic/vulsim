"""Replay S control data; preserve areas/six bounds and fit only two controls."""
import argparse
from collections import Counter
import copy
from importlib.metadata import version as package_version
import json
import math
import os
from pathlib import Path
import shutil
import sys

from .budget import Ledger
from .model_collection import sha, write
from .model_general_control_collection import CONFIG, dependencies, verify as verify_collection
from . import model_general_control_samples as control
from . import model_general_state_samples_v2 as original
from .model_general_state_collection import ROOT, SUFFIX
from .model_general_state_fit import OWNERS, owner_features, owner_rows, reparse
from .model_m2_state_fit import nnls, predict, quality
from .model_reference_audit import ReferenceAudit
from .model_reference_labels import liberty

EXECUTION = Path(__file__).with_name('configs') / 'model_asap7_general_control_fit_v1.json'
EPSILON_PS = 1e-6


def read(path):
    return json.loads(Path(path).read_text())


def extract(folder, out):
    if out.exists():
        raise ValueError('preserve previous control-boundary extraction')
    cfg = dependencies(); a = verify_collection(folder); progress = read(folder / 'progress.json')
    ids = {t['id'] for t in a['tasks'] if t['split'] != 'test'}
    if (progress['phase'] != 'fitting_collection_complete' or progress['active'] or progress['waiting']
            or progress['errors'] or not progress['test_locked'] or set(progress['completed']) != ids):
        raise ValueError('complete fitting-only control collection required')
    old = read(ROOT / cfg['parent_fitting_dataset'])
    old_admission = read(old['admission_path']); pins = read(a['pin_table'])
    if (old['test_labels_read'] or not old['test_collection_locked'] or old['audit']['status'] != 'passed'
            or old['measurement_static_identity_sha256'] != a['measurement_static_identity_sha256']):
        raise ValueError('reusable fitting-only predecessor physical identity differs')
    old_cfg = read(ROOT / 'experiments/arithmetic_dse/configs/model_asap7_general_state_v2.json')
    old_specs = {s['id']: s for s in original.specifications(old_cfg)}
    new_specs = {s['id']: s for s in control.specifications(cfg)}
    if len({s['semantic_signature'] for s in [*old_specs.values(), *new_specs.values()]}) != 48:
        raise ValueError('new semantic sources overlap a predecessor source role')
    audit = ReferenceAudit(read(Ledger().path)['entries'])
    first = folder / 'runs' / a['capacity_pilots'][0]
    m = read(first / 'manifest.json'); cells = read(first / 'liberty_cells.json')['cells']
    if liberty(m['libraries'], cells) != pins:
        raise ValueError('control actual Liberty pin/function/FF table differs')
    old_tasks = {t['id']: t for t in old_admission['tasks']}
    old_rows = {r['id']: r for r in old['rows']}
    jobs = [(old_tasks[r['task_id']], Path(r['directory']), 'inherited', old_specs) for r in old['runs']]
    jobs += [(t, folder / 'runs' / t['id'], 'supplement', new_specs) for t in a['tasks'] if t['split'] != 'test']
    rows, runs, groups = [], [], {}
    for task in a['tasks']:
        if task['split'] == 'test' and (folder / 'runs' / task['id']).exists():
            raise ValueError('new independent physical labels observed before freeze')
    for task, directory, origin, specs in jobs:
        if task['split'] not in ('train', 'validation'):
            raise ValueError('consumed independent row entered control fitting')
        spec = specs[task['source_group']]
        contract = read(directory / 'general-state-contract.json')
        generator = original if origin == 'inherited' else control
        if (contract['spec'] != spec or generator.source(spec) != (directory / 'input.sv').read_text()
                or task['features'] != generator.features(spec, task['period_ps'])
                or groups.setdefault(spec['semantic_signature'], task['split']) != task['split']):
            raise ValueError('control source/role/geometry does not reproduce')
        audit.ancestry(directory); manifest, metrics, identity = reparse(directory, task, pins)
        if (identity != a['measurement_static_identity_sha256']
                or manifest['general_state_admission_sha256'] != sha(directory.parent.parent / 'admission.json')):
            raise ValueError('control physical/admission identity differs')
        for metric in metrics:
            row = {'id': task['id'] + '/' + metric['stage'], 'task_id': task['id'],
                'source_group': task['source_group'], 'source_semantic_signature': spec['semantic_signature'],
                'split': task['split'], 'stage': metric['stage'], 'period_ps': task['period_ps'],
                'owner_features': {owner: owner_features(spec, task['period_ps'], owner) for owner in OWNERS},
                'owner_area_um2': metric['general_state_owner_area_um2'], 'owner_FF_bits': metric['general_state_owner_FF_bits'],
                'boundary_paths': metric['general_state_paths'], 'whole_setup_slack_ps': metric['setup_worst_slack_ps'],
                'whole_hold_slack_ps': metric['hold_worst_slack_ps'], 'source_sha256': task['rtl_sha256'],
                'manifest_sha256': sha(directory / 'manifest.json')}
            if origin == 'inherited' and row != old_rows[row['id']]:
                raise ValueError('inherited fitting labels changed during control replay')
            row.update(origin=origin, control_features=control.control_features(spec))
            rows.append(row)
        runs.append({'task_id': task['id'], 'directory': str(directory), 'origin': origin,
            'manifest_sha256': sha(directory / 'manifest.json'), 'CTS_proof_sha256': sha(directory / 'logs' / SUFFIX / 'structural_cec/proof.json')})
    if (len(runs) != 324 or len(rows) != 648 or len(groups) != 36
            or Counter(r['split'] for r in rows) != {'train': 432, 'validation': 216}
            or Counter(r['origin'] for r in rows) != {'inherited': 324, 'supplement': 324}):
        raise ValueError('complete combined control fitting coverage differs')
    result = {'version': 'asap7-general-control-fitting-dataset-v1', 'protocol_sha256': sha(CONFIG),
        'admission_path': str(folder / 'admission.json'), 'admission_sha256': sha(folder / 'admission.json'),
        'parent_fitting_dataset': cfg['parent_fitting_dataset'], 'parent_fitting_dataset_sha256': cfg['parent_fitting_dataset_sha256'],
        'measurement_static_identity_sha256': a['measurement_static_identity_sha256'],
        'test_labels_read': False, 'test_collection_locked': True, 'area_parameters_changed': False,
        'rows': sorted(rows, key=lambda r: r['id']), 'runs': runs,
        'audit': {'status': 'passed', 'physical_runs': 324, 'new_physical_runs': 162, 'reused_physical_runs': 162,
            'source_groups': 36, 'stage_rows': 648, 'path_labels': 5832,
            'paid_leaf_commands': len(audit.commands), 'paid_leaf_ids': sorted(audit.commands),
            'raw_file_hashes_checked': len(audit.hashed), 'PPA_calls': 0}}
    write(out, result)
    print(json.dumps({k: v for k, v in result['audit'].items() if k != 'paid_leaf_ids'}), flush=True)


def features(row, cfg, exact=False):
    result = dict(row['control_features'])
    if set(result) != set(cfg['control_features']) or any(not math.isfinite(v) or v < 0 for v in result.values()):
        raise ValueError('control semantic feature schema differs')
    if row['period_ps'] not in cfg['SDC_ps']:
        raise ValueError('control model only supports nine exact frozen clocks')
    if exact:
        result.update({'exact_SDC_' + str(t): int(row['period_ps'] == t) for t in cfg['SDC_ps']})
    return result


def required(row, path):
    values = [p for p in row['boundary_paths'] if p['id'] == path]
    if len(values) != 1:
        raise ValueError('control path class not unique')
    result = values[0]['H_ps'] + values[0]['delay_ps']
    if not math.isfinite(result):
        raise ValueError('nonfinite control requirement')
    return result


def upper(model, row, cfg):
    f = features(row, cfg, model['kind'] == 'train_NNLS_semantic_control_load_exact_clock')
    if model['kind'] == 'train_pooled_path_max':
        return model['upper_ps']
    if model['kind'] not in ('train_NNLS_semantic_control_load', 'train_NNLS_semantic_control_load_exact_clock'):
        raise ValueError('unknown control upper model')
    return predict(model['regression'], {'features': f, 'period_ps': row['period_ps']}) + model['train_upper_correction_ps'] + model['reserve_ps']


def train_model(name, rows, path, cfg):
    reserve = cfg['boundary']['engineering_reserve_ps']
    if reserve != 50 or any(r['split'] != 'train' for r in rows):
        raise ValueError('train-only control calibration and original50ps required')
    if name == 'train_pooled_path_max':
        witness = max(rows, key=lambda r: (required(r, path), r['id']))
        return {'kind': name, 'upper_ps': required(witness, path) + reserve,
            'max_train_required_ps': required(witness, path), 'witness': witness['id'], 'reserve_ps': reserve}
    exact = name == 'train_NNLS_semantic_control_load_exact_clock'
    names = cfg['control_features'] + (['exact_SDC_' + str(t) for t in cfg['SDC_ps']] if exact else [])
    prepared = [{'id': r['id'], 'features': features(r, cfg, exact), 'period_ps': r['period_ps'], 'state_area_um2': required(r, path)} for r in rows]
    regression = nnls(prepared, names)
    witness = max(rows, key=lambda r: (required(r, path) - predict(regression,
        {'features': features(r, cfg, exact), 'period_ps': r['period_ps']}), r['id']))
    correction = max(0., required(witness, path) - predict(regression, {'features': features(witness, cfg, exact), 'period_ps': witness['period_ps']}))
    return {'kind': name, 'regression': regression, 'train_upper_correction_ps': correction,
        'train_residual_witness': witness['id'], 'reserve_ps': reserve, 'calibration_splits': ['train']}


def coverage(rows, paths, query, clocks):
    result = []
    for period in clocks:
        for path in paths:
            selected = [r for r in rows if r['period_ps'] == period]
            values = [{'row_id': r['id'], 'required_ps': required(r, path), 'upper_ps': query(r, path),
                'margin_ps': query(r, path) - required(r, path)} for r in selected]
            worst = min(values, key=lambda v: (v['margin_ps'], v['row_id']))
            result.append({'period_ps': period, 'path_class': path, 'covered': worst['margin_ps'] >= -EPSILON_PS,
                'minimum_margin_ps': worst['margin_ps'], 'witness': worst, 'rows': len(values)})
    return {'status': 'passed' if all(r['covered'] for r in result) else 'failed',
        'minimum_margin_ps': min(r['minimum_margin_ps'] for r in result), 'contexts': result}


def fit(dataset, out):
    cfg = dependencies(); d = read(dataset); execution = read(EXECUTION)
    if (out.exists() or d['version'] != 'asap7-general-control-fitting-dataset-v1' or d['audit']['status'] != 'passed'
            or d['protocol_sha256'] != sha(CONFIG) or d['test_labels_read'] or not d['test_collection_locked']
            or execution['protocol_sha256'] != sha(CONFIG) or d['audit']['stage_rows'] != 648):
        raise ValueError('audited fitting-only control data and prospective execution required')
    verify_collection(Path(d['admission_path']).parent)
    if sha(d['admission_path']) != d['admission_sha256']:
        raise ValueError('control fitting admission differs')
    parent = read(ROOT / cfg['parent_general_candidate']); stages, validation = {}, {}
    mutable = cfg['boundary_mutable_paths']; immutable = [n for n in cfg['timing_labels'] if n not in mutable + ['birth_data']]
    for stage in ('synth', 'grt'):
        rows = [r for r in d['rows'] if r['stage'] == stage]
        train, val = ([r for r in rows if r['split'] == split] for split in ('train', 'validation'))
        if len(train) != 216 or len(val) != 108:
            raise ValueError('control complete stage row counts differ')
        fixed = parent['stages'][stage]
        area = {origin: {o: quality(fixed['area_models'][o], owner_rows(
            [r for r in val if origin == 'combined' or r['origin'] == origin], o), cfg) for o in OWNERS}
            for origin in ('combined', 'inherited', 'supplement')}
        area_ok = all(q['status'] == 'passed' for part in area.values() for q in part.values())
        old_bounds = fixed['boundary_model']['by_exact_SDC']
        fixed_check = coverage(val, immutable, lambda r, p: old_bounds[str(r['period_ps'])][p]['overhead_ps'], cfg['SDC_ps'])
        candidates = []
        for order, name in enumerate(cfg['boundary_candidates']):
            models = {p: train_model(name, train, p, cfg) for p in mutable}
            checked = coverage(val, mutable, lambda r, p: upper(models[p], r, cfg), cfg['SDC_ps'])
            mean = sum(upper(models[p], r, cfg) for r in val for p in mutable) / (len(val) * len(mutable))
            candidates.append({'name': name, 'models': models, 'validation': checked, 'status': checked['status'],
                'mean_validation_upper_ps': mean, 'serialized_bytes': len(json.dumps(models, sort_keys=True, separators=(',', ':')).encode()),
                'declared_order': order})
        passing = [c for c in candidates if c['status'] == 'passed']
        selected = min(passing, key=lambda c: (c['mean_validation_upper_ps'], c['serialized_bytes'], c['declared_order'])) if passing else None
        ready = area_ok and fixed_check['status'] == 'passed' and selected is not None
        boundary = {'kind': 'fixed_six_paths_and_semantic_control_upper',
            'immutable_by_exact_SDC': {t: {p: copy.deepcopy(v[p]) for p in immutable} for t, v in old_bounds.items()},
            'control_models': selected['models'] if selected else None,
            'mutable_paths': mutable, 'birth_data_diagnostic_only': True,
            'arbitrary_joint_arithmetic_boundary_qualified': False}
        stages[stage] = {'quality_status': 'awaiting_independent_test' if ready else 'failed_validation',
            'area_models': copy.deepcopy(fixed['area_models']), 'area_parameters_unchanged': True,
            'boundary_model': boundary, 'control_algorithm': selected['name'] if selected else None}
        validation[stage] = {'status': 'passed' if ready else 'failed', 'area_quality': area,
            'immutable_boundary_validation': fixed_check, 'candidates': candidates,
            'selected_algorithm': selected['name'] if selected else None,
            'selected_control_validation': selected['validation'] if selected else None}
    ready = stages['grt']['quality_status'] == 'awaiting_independent_test'
    candidate = {k: copy.deepcopy(v) for k, v in parent.items() if k not in ('stages', 'execution_definition', 'dataset_sha256', 'execution_sha256', 'protocol_sha256', 'quality_status', 'version')}
    candidate.update(version='arithmetic-general-control-candidate-v1', quality_status='awaiting_independent_test' if ready else 'failed_validation',
        stages=stages, execution_definition=execution, dataset_sha256=sha(dataset), execution_sha256=sha(EXECUTION),
        protocol_sha256=sha(CONFIG), parent_general_candidate_sha256=cfg['parent_general_candidate_sha256'],
        test_observed=False, full_D_ready=False, production_price_binding_qualified=False)
    out.mkdir(parents=True)
    write(out / 'candidate.json', candidate); write(out / 'validation.json', validation)
    sources = {}
    paths = [Path(__file__), CONFIG, EXECUTION, Path(control.__file__), Path(original.__file__),
        Path(__file__).with_name('model_general_state_fit.py'), Path(__file__).with_name('model_m2_state_fit.py'),
        Path(__file__).with_name('model_training.py'), Path(__file__).with_name('model_general_state_labels.py')]
    for path in paths:
        name = str(path.relative_to(ROOT)); dest = out / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dest); sources[name] = sha(path)
    write(out / 'selection-freeze.json', {'version': 'asap7-general-control-selection-freeze-v1',
        'status': 'frozen_awaiting_independent_test' if ready else 'failed_validation',
        'dataset_path': str(dataset), 'dataset_sha256': sha(dataset), 'admission_path': d['admission_path'],
        'admission_sha256': d['admission_sha256'], 'protocol_sha256': sha(CONFIG), 'execution_sha256': sha(EXECUTION),
        'candidate_sha256': sha(out / 'candidate.json'), 'validation_sha256': sha(out / 'validation.json'),
        'parent_general_candidate_sha256': cfg['parent_general_candidate_sha256'], 'sources': sources,
        'test_observed': False, 'required_independent_tasks': 54, 'area_parameters_changed': False,
        'immutable_boundary_parameters_changed': False, 'production_price_binding_qualified': False,
        'environment': {'python': sys.version, 'numpy': package_version('numpy'), 'scipy': package_version('scipy'),
            'threads': {k: os.environ.get(k) for k in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS')}}})
    print(json.dumps({'status': 'validation_passed' if ready else 'validation_failed', 'stages': {
        name: {'status': v['status'], 'selected_algorithm': v['selected_algorithm'],
            'fixed_area_status': {o: q['status'] for o, q in v['area_quality']['supplement'].items()},
            'immutable_boundary_status': v['immutable_boundary_validation']['status'],
            'control_candidates': {c['name']: c['status'] for c in v['candidates']}} for name, v in validation.items()},
        'test_observed': False, 'PPA_calls': 0}), flush=True)


def verify_fit(folder):
    f = read(folder / 'selection-freeze.json')
    cfg = dependencies()
    if (f['version'] != 'asap7-general-control-selection-freeze-v1' or f['test_observed']
            or f['area_parameters_changed'] or f['immutable_boundary_parameters_changed']
            or sha(CONFIG) != f['protocol_sha256'] or sha(EXECUTION) != f['execution_sha256']
            or sha(f['dataset_path']) != f['dataset_sha256'] or sha(f['admission_path']) != f['admission_sha256']):
        raise ValueError('control frozen fitting input identity differs')
    for name, key in [('candidate.json', 'candidate_sha256'), ('validation.json', 'validation_sha256')]:
        if sha(folder / name) != f[key]: raise ValueError('control selected output changed')
    for name, h in f['sources'].items():
        if sha(ROOT / name) != h or sha(folder / 'source' / name) != h: raise ValueError('control fitting producer changed')
    parent = read(ROOT / cfg['parent_general_candidate']); candidate = read(folder / 'candidate.json')
    for stage, value in candidate['stages'].items():
        if value['area_models'] != parent['stages'][stage]['area_models']:
            raise ValueError('control successor changed immutable area coefficients')
        for t, paths in value['boundary_model']['immutable_by_exact_SDC'].items():
            for path, model in paths.items():
                if model != parent['stages'][stage]['boundary_model']['by_exact_SDC'][t][path]:
                    raise ValueError('control successor changed a retained path bound')
    return f


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('extract', 'fit', 'verify'))
    parser.add_argument('--out', type=Path, required=True); parser.add_argument('--folder', type=Path); parser.add_argument('--dataset', type=Path)
    args = parser.parse_args()
    if args.action == 'extract': extract(args.folder.resolve(), args.out.resolve())
    elif args.action == 'fit': fit(args.dataset.resolve(), args.out.resolve())
    else: verify_fit(args.out.resolve()); print('frozen control-boundary fit verified')
