"""Separate S-control independent admission and immutable one-time evaluation."""
import argparse
import fcntl
from pathlib import Path
import shutil

from .budget import Ledger, POLICY, usage
from .model_collection import sha, write
from . import model_general_state_test as base
from .model_general_control_collection import CONFIG, function, verify as verify_collection
from .model_general_state_collection import ROOT
from .model_general_control_fit import EXECUTION, OWNERS, verify_fit, features, upper, coverage
from .model_general_state_fit import owner_features, owner_rows, reparse
from .model_general_control_samples import specifications, source, control_features
from .model_reference_audit import ReferenceAudit
from .model_m2_state_fit import quality


def read(path):
    import json
    return json.loads(Path(path).read_text())


def prepare(folder, parent, fit):
    if folder.exists():
        raise ValueError('preserve independent control attempts')
    a, f = verify_collection(parent), verify_fit(fit)
    cfg = read(CONFIG); candidate = read(fit / 'candidate.json'); dataset = read(f['dataset_path'])
    tasks = [t for t in a['tasks'] if t['split'] == 'test']
    if (f['status'] != 'frozen_awaiting_independent_test' or candidate['quality_status'] != 'awaiting_independent_test'
            or f['admission_sha256'] != sha(parent / 'admission.json') or len(tasks) != 54
            or dataset['test_labels_read'] or not dataset['test_collection_locked'] or dataset['audit']['physical_runs'] != 324
            or any((parent / 'runs' / t['id']).exists() for t in tasks)):
        raise ValueError('new control independent role and validation-ready freeze required')
    used = usage(read(Ledger().path)['entries']); limits = read(POLICY)['resources']; later = cfg['later_work_reserved']
    wall = 54 * cfg['resources']['per_task_walltime_envelope_s'] + 3600
    if (used['walltime_s'] + wall + later['walltime_s'] > limits['max_global_walltime_h'] * 3600
            or used['CPU_time_s'] + 4 * wall + later['CPU_time_s'] > limits['max_tool_CPU_time_h'] * 3600
            or used['synth'] + 54 + later['synth'] > limits['max_synthesis_calls']
            or used['grt'] + 54 + later['grt'] > limits['max_global_route_calls']
            or shutil.disk_usage(folder.parent).free < 54 * cfg['resources']['storage_per_task_bytes'] + later['storage_bytes']):
        raise ValueError('independent control tests and later work not funded')
    folder.mkdir(parents=True)
    paths = {ROOT / n for n in a['sources']} | {ROOT / n for n in f['sources']}
    paths |= {Path(__file__), Path(base.__file__), Path(__file__).with_name('model_reference_audit.py'),
        Path(__file__).with_name('model_m2_state_replay.py'), ROOT / 'regression/arithmetic_general_control_fit.py'}
    sources = {}
    for path in sorted(paths):
        name = str(path.relative_to(ROOT)); dest = folder / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dest); sources[name] = sha(path)
    pilots = [cfg['independent_capacity_pilot_source'] + f'-t{i}' for i in cfg['capacity_pilot_clock_indices']]
    admission = {'version': 'asap7-general-control-independent-admission-v1', 'id': folder.name,
        'sources': sources, 'tasks': tasks, 'protocol_sha256': sha(CONFIG), 'execution_sha256': sha(EXECUTION),
        'policy_sha256': sha(POLICY), 'fitting_admission': str(parent / 'admission.json'),
        'fitting_admission_sha256': sha(parent / 'admission.json'),
        'selection_freeze': str(fit / 'selection-freeze.json'), 'selection_freeze_sha256': sha(fit / 'selection-freeze.json'),
        'candidate': str(fit / 'candidate.json'), 'candidate_sha256': sha(fit / 'candidate.json'),
        'dataset': f['dataset_path'], 'dataset_sha256': f['dataset_sha256'],
        'measurement_static_identity_sha256': a['measurement_static_identity_sha256'],
        'pin_table': a['pin_table'], 'pin_table_sha256': a['pin_table_sha256'], 'capacity_pilots': pilots,
        'evaluation': {'area_gate': 'three unchanged owned-state classes independently median20%/P95 50% per stage',
            'boundary_gate': 'every independent row at each of nine exact clocks and all eight non-birth path classes must satisfy its frozen upper function',
            'six_path_bounds_and_area_models_unchanged': True, 'engineering_reserve_ps': 50,
            'test_labels_for_fitting_or_selection': False, 'deployable_stage_if_passed': 'grt'},
        'resource_plan': {'tasks': 54, 'synth': 54, 'grt': 54, 'walltime_envelope_s': wall,
            'CPU_envelope_s': 4 * wall, 'storage_bytes': 54 * cfg['resources']['storage_per_task_bytes'],
            'later_work_reserved': later},
        'automatic_retries': 0, 'automatic_fit_evaluate_or_publish': False, 'full_D_ready': False}
    write(folder / 'admission.json', admission)
    base.collection.progress_write(folder, {'phase': 'independent_admitted', 'active': [], 'completed': [],
        'waiting': [t['id'] for t in tasks], 'errors': [], 'capacity_qualified': False, 'test_locked': False})
    verify(folder)
    print({'status': 'independent_admitted', 'tasks': 54, 'capacity_pilots': pilots,
        'walltime_envelope_s': wall, 'CPU_envelope_s': 4 * wall, 'automatic_evaluation': False}, flush=True)


def verify(folder):
    a = read(folder / 'admission.json')
    if (a['version'] != 'asap7-general-control-independent-admission-v1' or sha(CONFIG) != a['protocol_sha256']
            or sha(EXECUTION) != a['execution_sha256'] or sha(POLICY) != a['policy_sha256']
            or sha(a['fitting_admission']) != a['fitting_admission_sha256']
            or sha(a['selection_freeze']) != a['selection_freeze_sha256'] or sha(a['candidate']) != a['candidate_sha256']
            or sha(a['dataset']) != a['dataset_sha256'] or sha(a['pin_table']) != a['pin_table_sha256']):
        raise ValueError('control independent frozen identity differs')
    f = verify_fit(Path(a['selection_freeze']).parent)
    if f['status'] != 'frozen_awaiting_independent_test' or f['test_observed']:
        raise ValueError('control selection not independently frozen')
    expected = [t for t in read(a['fitting_admission'])['tasks'] if t['split'] == 'test']
    if a['tasks'] != expected or len(expected) != 54:
        raise ValueError('control independent task roles changed')
    for name, h in a['sources'].items():
        if sha(ROOT / name) != h or sha(folder / 'source' / name) != h:
            raise ValueError('control independent producer changed: ' + name)
    for t in a['tasks']:
        if sha(t['rtl']) != t['rtl_sha256'] or sha(t['contract']) != t['contract_sha256']:
            raise ValueError('control independent RTL changed')
    return a


class IndependentLedger(base.IndependentLedger):
    pass


_reserve = function(base.IndependentLedger.reserve, verify=verify)
_old = 'asap7-general-state-independent-v1'
if _reserve.__code__.co_consts.count(_old) != 1:
    raise ValueError('unsupported control independent accounting identity')
_reserve.__code__ = _reserve.__code__.replace(co_consts=tuple('asap7-general-control-independent-v1' if c == _old else c for c in _reserve.__code__.co_consts))
IndependentLedger.reserve = _reserve


def run_task(folder, task):
    return function(base.run_task, CONFIG=CONFIG, verify=verify,
        IndependentLedger=IndependentLedger, __file__=__file__)(folder, task)


def run(folder):
    function(base.run, verify=verify, run_task=run_task)(folder)


def bound(candidate, row, path, cfg):
    b = candidate['stages'][row['stage']]['boundary_model']
    if path in b['mutable_paths']:
        return upper(b['control_models'][path], row, cfg)
    features(row, cfg)  # Validate the exact clock and semantic feature schema for fixed paths too.
    return b['immutable_by_exact_SDC'][str(row['period_ps'])][path]['overhead_ps']


def extract(folder, out):
    if out.exists():
        raise ValueError('preserve previous independent control extraction')
    a = verify(folder); progress = read(folder / 'progress.json'); cfg = read(CONFIG)
    if (progress['phase'] != 'independent_collection_complete' or progress['active'] or progress['waiting']
            or progress['errors'] or set(progress['completed']) != {t['id'] for t in a['tasks']}):
        raise ValueError('complete independent control collection required')
    specs = {s['id']: s for s in specifications(cfg)}
    audit = ReferenceAudit(read(Ledger().path)['entries']); pins = read(a['pin_table']); rows, runs = [], []
    for task in a['tasks']:
        directory = folder / 'runs' / task['id']; spec = specs[task['source_group']]
        if task['split'] != 'test' or source(spec) != (directory / 'input.sv').read_text():
            raise ValueError('independent control source/role mismatch')
        audit.ancestry(directory); manifest, metrics, identity = reparse(directory, task, pins)
        if (identity != a['measurement_static_identity_sha256']
                or manifest['selection_freeze_sha256'] != a['selection_freeze_sha256']
                or manifest['general_state_admission_sha256'] != sha(folder / 'admission.json')):
            raise ValueError('independent control selection/physical identity differs')
        for metric in metrics:
            rows.append({'id': task['id'] + '/' + metric['stage'], 'task_id': task['id'], 'source_group': task['source_group'],
                'split': 'test', 'stage': metric['stage'], 'period_ps': task['period_ps'],
                'control_features': control_features(spec),
                'owner_features': {o: owner_features(spec, task['period_ps'], o) for o in OWNERS},
                'owner_area_um2': metric['general_state_owner_area_um2'], 'owner_FF_bits': metric['general_state_owner_FF_bits'],
                'boundary_paths': metric['general_state_paths'], 'whole_setup_slack_ps': metric['setup_worst_slack_ps'],
                'whole_hold_slack_ps': metric['hold_worst_slack_ps'], 'source_sha256': task['rtl_sha256'],
                'manifest_sha256': sha(directory / 'manifest.json')})
        runs.append({'task_id': task['id'], 'directory': str(directory), 'manifest_sha256': sha(directory / 'manifest.json')})
    if len(rows) != 108 or len({r['source_group'] for r in rows}) != 6:
        raise ValueError('independent control complete coverage differs')
    write(out, {'version': 'asap7-general-control-independent-dataset-v1',
        'admission_path': str(folder / 'admission.json'), 'admission_sha256': sha(folder / 'admission.json'),
        'selection_freeze_sha256': a['selection_freeze_sha256'], 'candidate_sha256': a['candidate_sha256'],
        'rows': rows, 'runs': runs, 'audit': {'status': 'passed', 'physical_runs': 54, 'stage_rows': 108,
            'path_labels': 972, 'paid_leaf_commands': len(audit.commands), 'paid_leaf_ids': sorted(audit.commands),
            'raw_file_hashes_checked': len(audit.hashed), 'PPA_calls': 0}})
    print({'status': 'passed', 'physical_runs': 54, 'stage_rows': 108, 'path_labels': 972, 'PPA_calls': 0}, flush=True)


def verdict(candidate, dataset):
    cfg = read(CONFIG); stages = {}
    paths = [p for p in cfg['timing_labels'] if p != 'birth_data']
    for stage in ('synth', 'grt'):
        rows = [r for r in dataset['rows'] if r['stage'] == stage]
        areas = {o: quality(candidate['stages'][stage]['area_models'][o], owner_rows(rows, o), cfg) for o in OWNERS}
        bounds = coverage(rows, paths, lambda r, p: bound(candidate, r, p, cfg), cfg['SDC_ps'])
        stages[stage] = {'status': 'passed' if all(q['status'] == 'passed' for q in areas.values()) and bounds['status'] == 'passed' else 'failed',
            'owner_area_quality': areas, 'boundary_coverage': bounds,
            'minimum_boundary_margin_ps': bounds['minimum_margin_ps']}
    return {'version': 'asap7-general-control-independent-verdict-v1', 'status': stages['grt']['status'], 'stages': stages,
        'parameters_domain_or_reserve_changed': False, 'area_models_and_six_path_bounds_unchanged': True,
        'test_labels_consumed': True, 'test_labels_permanently_excluded_from_future_fitting': True,
        'eligible_deployable_stages': ['grt'] if stages['grt']['status'] == 'passed' else [],
        'production_price_binding_qualified': False, 'full_D_ready': False, 'PPA_calls': 0}


def evaluate(folder, dataset, out):
    a = verify(folder); data = read(dataset)
    if (data['audit']['status'] != 'passed' or data['admission_sha256'] != sha(folder / 'admission.json')
            or data['selection_freeze_sha256'] != a['selection_freeze_sha256']
            or data['candidate_sha256'] != a['candidate_sha256'] or len(data['rows']) != 108
            or any(r['split'] != 'test' for r in data['rows'])):
        raise ValueError('audited immutable independent control data required')
    if out.exists(): raise ValueError('preserve independent control verdict')
    with (folder / 'evaluation.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        marker = folder / 'test-consumed.json'
        if marker.exists(): raise ValueError('independent control test already consumed; replay existing verdict')
        out.mkdir(parents=True)
        base.collection.exclusive(marker, {'dataset_sha256': sha(dataset), 'selection_freeze_sha256': a['selection_freeze_sha256'],
            'candidate_sha256': a['candidate_sha256'], 'out': str(out), 'parameters_or_margins_may_change': False})
        result = verdict(read(a['candidate']), data); write(out / 'verdict.json', result)
        write(out / 'identity.json', {'admission_sha256': sha(folder / 'admission.json'), 'dataset_path': str(dataset),
            'dataset_sha256': sha(dataset), 'candidate_sha256': a['candidate_sha256'], 'verdict_sha256': sha(out / 'verdict.json')})
    print({'status': result['status'], 'eligible_deployable_stages': result['eligible_deployable_stages'],
        'test_consumed': True, 'parameters_changed': False, 'PPA_calls': 0}, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('prepare', 'verify', 'run', 'status', 'extract', 'evaluate'))
    parser.add_argument('--folder', type=Path, required=True); parser.add_argument('--parent', type=Path); parser.add_argument('--fit', type=Path)
    parser.add_argument('--dataset', type=Path); parser.add_argument('--out', type=Path); args = parser.parse_args(); folder = args.folder.resolve()
    if args.action == 'prepare': prepare(folder, args.parent.resolve(), args.fit.resolve())
    elif args.action == 'verify': verify(folder); print('frozen control independent admission verified')
    elif args.action == 'run': run(folder)
    elif args.action == 'status': base.status(folder)
    elif args.action == 'extract': extract(folder, args.out.resolve())
    else: evaluate(folder, args.dataset.resolve(), args.out.resolve())
