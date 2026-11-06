"""Qualified S release: bounded raw archives and portable numerical/training replay."""
import argparse
from contextlib import redirect_stdout
import copy
import gzip
import hashlib
import importlib
from importlib.metadata import version as package_version
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import types

from .model_d_requirements_evidence import pack, unpack, sha, read, write
from .model_m2_f5_evidence import Pool

ROOT = Path(__file__).resolve().parents[2]
SUFFIX = Path('asap7/arithmetic_probe/base')
VERSION = 'asap7-general-state-publication-v1'
RAW_VERSION = 'asap7-general-control-raw-evidence-v1'


def frozen_modules(source):
    name = '_qualified_S_frozen'
    for key in list(sys.modules):
        if key == name or key.startswith(name + '.'):
            del sys.modules[key]
    package = types.ModuleType(name); package.__path__ = [str(source / 'experiments/arithmetic_dse')]
    sys.modules[name] = package
    names = ('backend', 'platforms', 'sdc', 'sdc_storage_v3', 'budget', 'model_general_state_samples_v2',
        'model_general_control_samples', 'model_general_state_labels', 'model_general_state_fit',
        'model_general_control_fit', 'model_general_control_test', 'model_reference_labels',
        'model_m2_live_cec_v3', 'model_reference_audit')
    return {n: importlib.import_module(name + '.' + n) for n in names}


def released_model(candidate, verdict, selection_sha, verdict_sha, cfg):
    result = copy.deepcopy(candidate)
    result.update(version='arithmetic-general-state-qualified-v1', id='asap7-general-state-grt-qualified-v1',
        quality_status='passed', test_observed=True, independent_labels_consumed=True,
        independent_labels_excluded_from_future_fitting=True, selection_freeze_sha256=selection_sha,
        independent_verdict_sha256=verdict_sha, area_models_and_six_path_bounds_unchanged=True,
        production_price_binding_qualified=False, full_D_ready=False)
    stage = copy.deepcopy(candidate['stages']['grt'])
    stage.update(quality_status='passed', independent_quality=verdict['stages']['grt'])
    result['stages'] = {'grt': stage}
    result['query_contract'] = {'owners': ['input_service', 'native_state', 'external_state'],
        'control_features': cfg['control_features'], 'exact_SDC_ps': cfg['SDC_ps'],
        'native_enable_and_valid': 'semantic control-load upper function, including train-only correction and original50ps',
        'other_six_paths': 'unchanged exact-clock parent upper bounds',
        'comparison': 'each query uses its own conditional upper; do not compare a maximum required value to another sample upper',
        'source_scope': cfg['source_relations'], 'arbitrary_arithmetic_source_correlation_qualified': False,
        'shared_clock_physical_root_repair_area_included': False,
        'production_binding_and_joint_arithmetic_qualification_required': True}
    return result


def capabilities(cfg):
    return {'version': VERSION, 'ASAP7_grt_general_synthetic_state_prices': True,
        'input_service_native_external_owned_functional_state_control_area': True,
        'eight_state_boundary_path_classes': True, 'conditional_native_enable_and_valid_upper': True,
        'area_models_and_six_path_bounds_unchanged': True, 'ABC_ps': 1500, 'exact_SDC_ps': cfg['SDC_ps'], 'IO': '0.2T',
        'synthetic_two_root_affine_source_scope_only': True, 'shared_clock_physical_root_repair_area_prices': False,
        'production_price_binding_qualified': False, 'arbitrary_arithmetic_source_correlation_qualified': False,
        'joint_arithmetic_or_formal_boundary_qualified': False, 'whole_stage_model_qualified': False,
        'real_half_quarter_interval_model_qualified': False, 'full_D_ready': False,
        'nine_case_36_complete': False, 'full_step7_complete': False,
        'independent_labels_consumed_and_permanently_excluded': True}


def check_manifest(folder, version):
    manifest = read(folder / 'manifest.json')
    if manifest['version'] != version:
        raise ValueError('qualified S evidence schema differs')
    for name, h in manifest['files'].items():
        if sha(folder / name) != h:
            raise ValueError('qualified S evidence identity mismatch: ' + name)
    return manifest


def archive(root, folder):
    from .budget import Ledger, usage
    from .model_general_control_test import verify, verdict as fixed_verdict
    independent = root / 'independent-v1'; a = verify(independent)
    f = read(a['selection_freeze']); fit = read(a['dataset']); test_path = root / 'independent-check-v1/test-dataset.json'
    test = read(test_path); candidate = read(a['candidate']); evaluation = root / 'independent-verdict-v1'
    verdict, identity = read(evaluation / 'verdict.json'), read(evaluation / 'identity.json')
    marker = read(independent / 'test-consumed.json')
    if (verdict['status'] != 'passed' or verdict['eligible_deployable_stages'] != ['grt']
            or fixed_verdict(candidate, test) != verdict or verdict['parameters_domain_or_reserve_changed']
            or marker['dataset_sha256'] != sha(test_path) or marker['candidate_sha256'] != a['candidate_sha256']
            or marker['selection_freeze_sha256'] != a['selection_freeze_sha256']
            or identity['verdict_sha256'] != sha(evaluation / 'verdict.json') or identity['dataset_sha256'] != sha(test_path)):
        raise ValueError('immutable passed one-time S verdict required')
    folder.mkdir(parents=True, exist_ok=False)
    cfg_path = ROOT / 'experiments/arithmetic_dse/configs/model_asap7_general_control_v1.json'; cfg = read(cfg_path)
    old_fit = read(ROOT / cfg['parent_fitting_dataset']); old_admission = Path(old_fit['admission_path'])
    new_admission = Path(a['fitting_admission'])
    documents = {'fit-data.json': Path(a['dataset']), 'test-data.json': test_path, 'candidate.json': Path(a['candidate']),
        'validation.json': Path(a['candidate']).with_name('validation.json'), 'selection-freeze.json': Path(a['selection_freeze']),
        'verdict.json': evaluation / 'verdict.json', 'identity.json': evaluation / 'identity.json',
        'test-consumed.json': independent / 'test-consumed.json', 'fit-byte-proof.json': root / 'fit-byte-proof.json',
        'pin-table.json': Path(a['pin_table']), 'old-fit-admission.json': old_admission,
        'new-fit-admission.json': new_admission, 'test-admission.json': independent / 'admission.json',
        'parent-candidate.json': ROOT / cfg['parent_general_candidate'], 'parent-fit-data.json': ROOT / cfg['parent_fitting_dataset'],
        'parent-failed-verdict.json': ROOT / cfg['parent_independent_verdict'],
        'parent-failure-manifest.json': ROOT / 'experiments/arithmetic/evidence/step7_general_state_failure_v2/manifest.json',
        'new-software-proof.json': Path(read(new_admission)['software_proof']),
        'frozen-query-guards.json': root / 'frozen-query-guards.json', 'independent-lock-guards.json': root / 'independent-lock-guards.json'}
    for name, h in read(root / 'fit-byte-proof.json')['files'].items():
        if sha(root / 'fit-v1' / name) != h or (root / 'fit-v1' / name).read_bytes() != (root / 'fit-v2' / name).read_bytes():
            raise ValueError('S byte reproduction changed')
        documents['repeat/' + name] = root / 'fit-v2' / name
    pack(folder / 'documents-pool.json.gz', documents)
    sources = {str(p.relative_to(ROOT)): p for p in (ROOT / 'experiments/arithmetic_dse').glob('*.py')}
    sources.update({str(p.relative_to(ROOT)): p for p in (ROOT / 'experiments/arithmetic_dse/configs').rglob('*') if p.is_file()})
    for name, h in a['sources'].items():
        p = independent / 'source' / name
        if sha(p) != h: raise ValueError('archived S independent source differs')
        sources[name] = p
    pack(folder / 'source-pool.json.gz', sources)
    tasks = {t['id']: t for p in (old_admission, new_admission) for t in read(p)['tasks']}
    pool = Pool(folder); runs, external, charged = [], {}, set()
    for run in fit['runs'] + test['runs']:
        key = run['task_id']; directory = Path(run['directory']); m = read(directory / 'manifest.json')
        if sha(directory / 'manifest.json') != run['manifest_sha256'] or m['status'] != 'completed':
            raise ValueError('S archive raw manifest differs')
        selected = [directory / name for name in ('manifest.json', 'input.sv', 'general-state-contract.json',
            'metrics.json', 'liberty_cells.json', 'general-synth-ownership.json', 'general-grt-ownership.json')]
        for stage, stem in [('synth', '1_synth'), ('grt', '5_1_grt')]:
            selected += sorted(p for p in (directory / 'reports' / SUFFIX).glob('vulsim_' + stage + '*') if p.suffix in ('.rpt', '.tsv'))
            selected += [directory / 'results' / SUFFIX / (stem + '.sdc'), directory / 'logs' / SUFFIX / (stem + '.json')]
        cec = directory / 'logs' / SUFFIX / 'structural_cec'
        selected += sorted(p for p in cec.iterdir() if p.is_file() and (p.name == 'proof.json' or p.suffix == '.log'))
        files = {str(p.relative_to(directory)): pool.add(p) for p in selected}
        for name, h in files.items():
            if name in m['evidence_sha256'] and m['evidence_sha256'][name] != h:
                raise ValueError('S selected raw artifact changed while archiving')
        receipts = {}
        for command in m['commands']:
            charged.add(command['budget_reservation_id'])
            for p in (Path(command['log']), Path(command['gnu_time']), Path(command['log'].removesuffix('.log') + '.command.json')):
                receipts[p.name] = pool.add(p); external[str(p)] = sha(p)
        owner = directory.parent.parent / 'admission.json'
        runs.append({'task': tasks[key], 'origin': run.get('origin', 'independent'), 'files': files, 'receipts': receipts,
            'manifest_sha256': run['manifest_sha256'], 'admission_sha256': sha(owner), 'external_directory': str(directory)})
        external[str(directory / 'manifest.json')] = sha(directory / 'manifest.json')
        external.update({str(directory / name): h for name, h in m['evidence_sha256'].items()})
    ledger = read(Ledger().path); entries = [e for e in ledger['entries'] if e['id'] in charged]
    if len(entries) != 2268 or len(entries) != len(charged) or any(e['status'] != 'completed' for e in entries):
        raise ValueError('S archive measured commands incomplete or unpaid')
    packed = {'entries': entries, 'usage': usage(entries),
        'scope': '378 measured S banks: old162 fitting, new162 fitting and new54 independent; prior failed tests and diagnostics remain in immutable parents/global ledger'}
    (folder / 'paid-entries.json.gz').write_bytes(gzip.compress(json.dumps(packed, separators=(',', ':')).encode(), mtime=0))
    pool.flush()
    write(folder / 'index.json', {'version': RAW_VERSION, 'runs': runs, 'parts': pool.parts, 'external_artifacts': external,
        'banks': 378, 'stage_rows': 756, 'path_labels': 6804, 'source_groups': 42,
        'consumed_paid_leaf_commands': 2268, 'no_new_EDA_or_SAT': True, 'full_D_ready': False})
    write(folder / 'manifest.json', {'version': RAW_VERSION, 'files': {p.name: sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status': 'archived', 'banks': 378, 'stage_rows': 756, 'path_labels': 6804,
        'paid_leaf_commands': 2268, 'parts': len(pool.parts), 'bytes': sum(p.stat().st_size for p in folder.iterdir() if p.is_file())}), flush=True)


def unpack_objects(folder, index, destination):
    destination.mkdir(); result = {}
    for part in index['parts']:
        p = folder / part['file']
        if sha(p) != part['sha256']: raise ValueError('S raw object part changed')
        for h, text in json.loads(gzip.decompress(p.read_bytes())).items():
            if h in result or hashlib.sha256(text.encode()).hexdigest() != h:
                raise ValueError('S raw object identity differs')
            target = destination / h; target.write_text(text); result[h] = target
    return result


def materialize(mapping, objects, directory):
    for name, h in mapping.items():
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise ValueError('unsafe S raw archive member')
        p = directory / name; p.parent.mkdir(parents=True, exist_ok=True); os.link(objects[h], p)


def numerical(modules, docs, retrain=False):
    cfg = read(modules['model_general_control_fit'].CONFIG)
    candidate, fit, test, verdict, selection = (read(docs / n) for n in ('candidate.json', 'fit-data.json', 'test-data.json', 'verdict.json', 'selection-freeze.json'))
    admission = read(docs / 'test-admission.json'); parent = read(docs / 'parent-candidate.json')
    marker = read(docs / 'test-consumed.json'); identity = read(docs / 'identity.json')
    if (sha(docs / 'candidate.json') != selection['candidate_sha256'] or sha(docs / 'validation.json') != selection['validation_sha256']
            or sha(docs / 'fit-data.json') != selection['dataset_sha256']
            or sha(docs / 'selection-freeze.json') != admission['selection_freeze_sha256']
            or sha(docs / 'test-data.json') != marker['dataset_sha256']
            or marker['candidate_sha256'] != admission['candidate_sha256']
            or sha(docs / 'verdict.json') != identity['verdict_sha256']
            or sha(docs / 'new-fit-admission.json') != selection['admission_sha256']):
        raise ValueError('qualified S frozen numeric input identity differs')
    for name, h in read(docs / 'fit-byte-proof.json')['files'].items():
        if sha(docs / name) != h or sha(docs / 'repeat' / name) != h: raise ValueError('S frozen byte reproduction differs')
    old_cfg = read(modules['model_general_state_samples_v2'].__file__.replace('model_general_state_samples_v2.py', 'configs/model_asap7_general_state_v2.json'))
    specs = {s['id']: s for s in modules['model_general_state_samples_v2'].specifications(old_cfg)}
    specs.update({s['id']: s for s in modules['model_general_control_samples'].specifications(cfg)})
    groups, seen = {}, set()
    for row in fit['rows'] + test['rows']:
        s = specs[row['source_group']]
        generator = modules['model_general_state_samples_v2'] if row.get('origin') == 'inherited' else modules['model_general_control_samples']
        if (row['control_features'] != modules['model_general_control_samples'].control_features(s)
                or row['owner_features'] != {o: modules['model_general_state_fit'].owner_features(s, row['period_ps'], o) for o in candidate['owners']}
                or hashlib.sha256(generator.source(s).encode()).hexdigest() != row['source_sha256']
                or row['id'] in seen or groups.setdefault(s['semantic_signature'], row['split']) != row['split']):
            raise ValueError('S frozen semantics/features/grouping differ')
        seen.add(row['id'])
    if len(seen) != 756 or len(groups) != 42 or any(r['split'] not in ('train', 'validation') for r in fit['rows']):
        raise ValueError('S numeric source/role coverage differs')
    report = read(docs / 'validation.json'); fitter = modules['model_general_control_fit']
    immutable = [p for p in cfg['timing_labels'] if p not in cfg['boundary_mutable_paths'] + ['birth_data']]
    for stage in ('synth', 'grt'):
        frozen = candidate['stages'][stage]; baseline = parent['stages'][stage]
        if frozen['area_models'] != baseline['area_models']: raise ValueError('qualified S area coefficients changed')
        for t, paths in frozen['boundary_model']['immutable_by_exact_SDC'].items():
            for p, value in paths.items():
                if value != baseline['boundary_model']['by_exact_SDC'][t][p]: raise ValueError('qualified S retained bound changed')
        rows = [r for r in fit['rows'] if r['stage'] == stage]; train = [r for r in rows if r['split'] == 'train']; val = [r for r in rows if r['split'] == 'validation']
        for origin in ('combined', 'inherited', 'supplement'):
            for owner in candidate['owners']:
                q = modules['model_general_control_test'].quality(frozen['area_models'][owner],
                    fitter.owner_rows([r for r in val if origin == 'combined' or r['origin'] == origin], owner), cfg)
                if q != report[stage]['area_quality'][origin][owner]: raise ValueError('S unchanged area validation differs')
        old = fitter.coverage(val, immutable, lambda r, p: baseline['boundary_model']['by_exact_SDC'][str(r['period_ps'])][p]['overhead_ps'], cfg['SDC_ps'])
        if old != report[stage]['immutable_boundary_validation']: raise ValueError('S retained boundary validation differs')
        for item in report[stage]['candidates']:
            models = item['models']
            if retrain:
                actual = {p: fitter.train_model(item['name'], train, p, cfg) for p in cfg['boundary_mutable_paths']}
                if actual != models: raise ValueError('S train-only NNLS coefficients/calibration do not reproduce')
            q = fitter.coverage(val, cfg['boundary_mutable_paths'], lambda r, p: fitter.upper(models[p], r, cfg), cfg['SDC_ps'])
            mean = sum(fitter.upper(models[p], r, cfg) for r in val for p in cfg['boundary_mutable_paths']) / (len(val) * 2)
            size = len(json.dumps(models, sort_keys=True, separators=(',', ':')).encode())
            if q != item['validation'] or mean != item['mean_validation_upper_ps'] or size != item['serialized_bytes']:
                raise ValueError('S fixed control candidate replay differs')
        passing = [i for i in report[stage]['candidates'] if i['status'] == 'passed']
        selected = min(passing, key=lambda i: (i['mean_validation_upper_ps'], i['serialized_bytes'], i['declared_order']))
        if selected['name'] != frozen['control_algorithm'] or selected['models'] != frozen['boundary_model']['control_models']:
            raise ValueError('S frozen validation selection differs')
    if modules['model_general_control_test'].verdict(candidate, test) != verdict or verdict['status'] != 'passed':
        raise ValueError('qualified S one-time fixed verdict differs')
    return candidate, verdict, cfg


def verify_raw(folder, external=False):
    from .budget import Ledger
    check_manifest(folder, RAW_VERSION); index = read(folder / 'index.json')
    entries = {e['id']: e for e in json.loads(gzip.decompress((folder / 'paid-entries.json.gz').read_bytes()))['entries']}
    with tempfile.TemporaryDirectory(prefix='qualified-S-raw-') as td:
        temp = Path(td); source, docs = temp / 'source', temp / 'documents'
        unpack(folder / 'source-pool.json.gz', source); unpack(folder / 'documents-pool.json.gz', docs)
        modules = frozen_modules(source)
        for name, h in read(docs / 'test-admission.json')['sources'].items():
            if sha(source / name) != h: raise ValueError('S archived executed producer differs')
        numerical(modules, docs)
        objects = unpack_objects(folder, index, temp / 'objects')
        rows = {r['id']: r for name in ('fit-data.json', 'test-data.json') for r in read(docs / name)['rows']}
        pins = read(docs / 'pin-table.json'); paid, seen, groups = set(), set(), {}
        old_cfg = read(source / 'experiments/arithmetic_dse/configs/model_asap7_general_state_v2.json')
        cfg = read(source / 'experiments/arithmetic_dse/configs/model_asap7_general_control_v1.json')
        specs = {s['id']: s for s in modules['model_general_state_samples_v2'].specifications(old_cfg)}
        specs.update({s['id']: s for s in modules['model_general_control_samples'].specifications(cfg)})
        for item in index['runs']:
            with tempfile.TemporaryDirectory(dir=temp) as td_run:
                directory = Path(td_run); materialize(item['files'], objects, directory)
                receipts = directory / 'receipts'; materialize(item['receipts'], objects, receipts)
                task = item['task']; key = task['id']; m = read(directory / 'manifest.json'); s = specs[task['source_group']]
                generator = modules['model_general_state_samples_v2'] if item['origin'] == 'inherited' else modules['model_general_control_samples']
                if (sha(directory / 'manifest.json') != item['manifest_sha256'] or m['status'] != 'completed'
                        or generator.source(s) != (directory / 'input.sv').read_text()
                        or read(directory / 'general-state-contract.json')['spec'] != s
                        or task['features'] != generator.features(s, task['period_ps'])
                        or groups.setdefault(s['semantic_signature'], task['split']) != task['split']):
                    raise ValueError('qualified S raw source/role differs')
                for command in m['commands']:
                    e = entries[command['budget_reservation_id']]
                    saved = read(receipts / Path(command['log'].removesuffix('.log') + '.command.json').name)
                    if (e['status'] != 'completed' or command['exit_code'] or command['timed_out']
                            or command['memory_limit_exceeded'] or command['CPU_limit_exceeded']
                            or command['cleanup']['remaining_live_pids'] or e['command'] != command['command']
                            or e['task_id'] != key or e['admission_sha256'] != item['admission_sha256']
                            or e['walltime_s'] != command['walltime_s']
                            or abs(e['CPU_time_s'] - modules['budget'].cpu_seconds(receipts / Path(command['gnu_time']).name)) > 1e-8
                            or saved not in (command, {k: v for k, v in command.items() if k != 'budget_reservation_id'})):
                        raise ValueError('qualified S paid leaf receipt differs')
                    paid.add(e['id'])
                p = m['platform_profile']; cells = read(directory / 'liberty_cells.json')['cells']
                for stage, stem in [('synth', '1_synth'), ('grt', '5_1_grt')]:
                    prefix = directory / 'reports' / SUFFIX / ('vulsim_' + stage)
                    g = modules['backend'].stage_metrics(prefix.parent, stage, cells, task['period_ps'], selected=p)
                    owner, instances, _ = modules['model_general_state_labels'].partition(prefix, pins, p, s)
                    paths = modules['model_general_state_labels'].labels(prefix, task['period_ps'], g['raw_report_units']['time']['to_ps'], pins, instances)
                    original = next(r for r in m['metrics'] if r['stage'] == stage); row = rows[key + '/' + stage]
                    for name, value in g.items():
                        if name != 'raw_reports_prefix' and original.get(name) != value: raise ValueError('S archived raw stage differs: ' + name)
                    if (owner != read(directory / ('general-' + stage + '-ownership.json'))
                            or owner['owner_area_um2'] != row['owner_area_um2'] or owner['owner_FF_bits'] != row['owner_FF_bits']
                            or paths != row['boundary_paths'] or abs(g['cell_area_um2'] - owner['total_area_um2']) > 1e-6):
                        raise ValueError('S archived raw ownership/FF/path differs')
                    actual = modules['sdc_storage_v3'].verify_sdc((directory / 'results' / SUFFIX / (stem + '.sdc')).read_text(), p,
                        task['period_ps'], modules['sdc'].rtl_ports((directory / 'input.sv').read_text(), 'ModelBundle'))
                    if actual != m['sdc_contracts'][stage]: raise ValueError('S archived actual SDC differs')
                    modules['platforms'].verify_wire_readback(Path(str(prefix) + '_layer_rc.tsv'), p)
                    native = read(directory / 'logs' / SUFFIX / (stem + '.json'))[('synth' if stage == 'synth' else 'globalroute') + '__design__instance__area__stdcell']
                    modules['backend'].verify_orfs_area(g['cell_area_um2'], native); seen.add(row['id'])
                proof_dir = directory / 'logs' / SUFFIX / 'structural_cec'; proof = read(proof_dir / 'proof.json')
                modules['model_m2_live_cec_v3'].check_result((proof_dir / 'cec.log').read_text(), True)
                for name in proof['negative_controls']:
                    modules['model_m2_live_cec_v3'].check_result((proof_dir / ('negative-' + name + '.log')).read_text(), False)
        if len(index['runs']) != 378 or len(groups) != 42 or len(seen) != 756 or seen != set(rows) or paid != set(entries):
            raise ValueError('qualified S raw coverage incomplete')
        if external:
            for name, h in index['external_artifacts'].items():
                if sha(name) != h: raise ValueError('qualified S original artifact differs: ' + name)
            audit = modules['model_reference_audit'].ReferenceAudit(read(Ledger().path)['entries'])
            libraries = set()
            for item in index['runs']:
                directory = Path(item['external_directory']); audit.ancestry(directory)
                m = read(directory / 'manifest.json'); signature = tuple((v['path'], v['sha256']) for v in m['libraries'])
                if signature not in libraries:
                    cells = read(directory / 'liberty_cells.json')['cells']
                    if modules['model_reference_labels'].liberty(m['libraries'], cells) != pins: raise ValueError('S actual Liberty pin/function table differs')
                    libraries.add(signature)
                with redirect_stdout(io.StringIO()): modules['model_general_state_fit'].reparse(directory, item['task'], pins)
    result = {'status': 'passed', 'external': external, 'banks': 378, 'stage_rows': 756, 'path_labels': 6804,
        'paid_leaf_receipts': len(paid), 'independent_status': 'passed', 'PPA_calls': 0, 'full_D_ready': False}
    print(json.dumps(result), flush=True); return result


def publish(archive, root, folder):
    from .budget import Ledger
    raw_manifest = check_manifest(archive, RAW_VERSION)
    folder.mkdir(parents=True, exist_ok=False)
    for name in ('source-pool.json.gz', 'documents-pool.json.gz', 'paid-entries.json.gz'):
        shutil.copy2(archive / name, folder / name)
    receipt_paths, support = {}, set()
    for label, stems in [('independent-check-v1', ['raw-extract', 'one-time-evaluate']),
                          ('publication-raw-check-v1', ['archive', 'portable', 'external', 'isolated'])]:
        for stem in stems:
            directory = root / label; record = read(directory / (stem + '.command.json'))
            if record['exit_code']: raise ValueError('S publication requires passed full raw checks')
            support.add(record['budget_reservation_id'])
            for suffix in ('.command.json', '.log', '.resources.txt'):
                receipt_paths[label + '/' + stem + suffix] = directory / (stem + suffix)
    pack(folder / 'check-receipts.json.gz', receipt_paths)
    write(folder / 'check-paid-entries.json', [e for e in read(Ledger().path)['entries'] if e['id'] in support])
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td); unpack(folder / 'source-pool.json.gz', temp / 'source'); unpack(folder / 'documents-pool.json.gz', temp / 'docs')
        modules = frozen_modules(temp / 'source'); c, v, cfg = numerical(modules, temp / 'docs')
        a = read(temp / 'docs/test-admission.json')
        model = released_model(c, v, a['selection_freeze_sha256'], sha(temp / 'docs/verdict.json'), cfg)
        write(folder / 'asap7-general-state.json', model)
        write(folder / 'capabilities.json', capabilities(cfg))
        write(folder / 'independent-verdict.json', v)
        write(folder / 'publication.json', {'version': VERSION, 'status': 'passed',
            'published': [{'file': 'asap7-general-state.json', 'sha256': sha(folder / 'asap7-general-state.json'), 'stage': 'grt'}],
            'candidate_sha256': a['candidate_sha256'], 'selection_freeze_sha256': a['selection_freeze_sha256'],
            'independent_verdict_sha256': sha(temp / 'docs/verdict.json'),
            'parent_general_candidate_sha256': cfg['parent_general_candidate_sha256'],
            'area_models_and_six_path_bounds_unchanged': True, 'parameters_domain_or_reserve_changed_after_test': False,
            'production_price_binding_qualified': False, 'full_D_ready': False})
    write(folder / 'raw-archive.json', {'path': str(archive), 'manifest_sha256': sha(archive / 'manifest.json'),
        'files': raw_manifest['files'], 'banks': 378, 'stage_rows': 756, 'path_labels': 6804,
        'bytes': sum(p.stat().st_size for p in archive.iterdir() if p.is_file()),
        'portable_scope': 'fixed semantic features, validation/selection/verdict, unchanged parameters, byte refit proof and verification receipts',
        'external_scope': 'full raw378 banks and2268 paid measurement receipts, actual tools/Liberty and saved complete CTS CEC',
        'raw_archive_not_required_for_portable_or_training_replay': True})
    (folder / 'README.md').write_text('''# ASAP7一般状态S：grt有界组件发布

原162拟合测量复用，新增108 train／54 validation／54新独立test完成。冻结参数一次性评价synth／grt均通过，grt八类非birth边界72／72，最小覆盖余量37.372788ps。
grt功能状态／控制面积独立中位／P95：input_service 0.339440%／1.095993%、native_state 0.486566%／0.902302%、external_state 0.046844%／0.172164%。原中位20%／P95 50%门槛、九目标和50ps工程reserve不变。

asap7-general-state.json仅发布ASAP7 grt：三个互斥所有者的功能状态／控制面积，六类原精确周期边界，以及native_enable／native_valid的冻结语义控制负载上界函数。
ABC1500ps、精确SDC1119／1253／1431／3141／3385／4162／4528／11913／14897ps、IO0.2T。一般复位／已知零位／部分寿命／service使能及无条件external捕获只在登记合成原生银行范围内取得资格；来源相关性仅两输入XOR／排列／反相，不授予任意算术来源相关性。
面积排除shared clock／physical／root repair、adapter和observer；联合阶段未来须明确一次计费。三个面积系数和六类原边界完整保持，控制模型只由train拟合、validation选择并在新独立测试前冻结。

便携数值核验：`python3 -B -m experiments.arithmetic_dse.model_general_control_evidence verify --folder experiments/arithmetic/evidence/step7_general_state_v1`
不依赖原build、活账本或EDA；重生成语义特征、重算固定验证／模型选择及独立结论，不再次消费测试。原始报告位于build中的分块压缩大归档，见raw-archive.json。
完整本机核验：上述命令增加`--external`，回放378银行／756阶段／6804路径、2268收费测量叶、实际Liberty／工具和完整已存CTS CEC，不执行新EDA／SAT。
训练复现：上述模块使用`retrain --folder ...`；使用冻结train／validation重算全部候选参数／校正／选择，检查系数精确一致，不读取任何独立标签来拟合。Python／NumPy／SciPy版本见selection-freeze归档。
隔离／篡改核验：上述模块使用`isolated --folder ...`，禁原树／build／账本读取、PATH为空、禁回放子进程，检查原始文档／发布参数／能力清单篡改拒绝。

旧首轮S失败、旧原生银行和12类primitive发布保留原字节；所有已消费独立标签永久排除后继拟合／验证／算法／裕量／域选择。
production_price_binding_qualified=false、full_D_ready=false。下一步仍需实际C++所有权／查询绑定、G联合边界／受限整阶段、I真实half／quarter区间和完整D选择／RTL／正式36条，不将本组件发布改写成步骤七或九例完成。Git由用户提交。
''')
    write(folder / 'manifest.json', {'version': VERSION, 'files': {p.name: sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status': 'published', 'stage': 'grt', 'model_sha256': sha(folder / 'asap7-general-state.json'),
        'bytes': sum(p.stat().st_size for p in folder.iterdir() if p.is_file()), 'production_price_binding_qualified': False, 'full_D_ready': False}), flush=True)


def verify(folder, external=False, retrain=False):
    check_manifest(folder, VERSION)
    with tempfile.TemporaryDirectory(prefix='qualified-S-numeric-') as td:
        temp = Path(td); source, docs, receipts = temp / 'source', temp / 'docs', temp / 'receipts'
        unpack(folder / 'source-pool.json.gz', source); unpack(folder / 'documents-pool.json.gz', docs)
        unpack(folder / 'check-receipts.json.gz', receipts)
        modules = frozen_modules(source)
        for name, h in read(docs / 'test-admission.json')['sources'].items():
            if sha(source / name) != h: raise ValueError('qualified S source snapshot changed')
        if retrain:
            env = read(docs / 'selection-freeze.json')['environment']
            if any(package_version(p) != env[p] for p in ('numpy', 'scipy')):
                raise ValueError('S exact training replay requires archived NumPy/SciPy versions')
        c, v, cfg = numerical(modules, docs, retrain=retrain)
        a = read(docs / 'test-admission.json')
        expected = released_model(c, v, a['selection_freeze_sha256'], sha(docs / 'verdict.json'), cfg)
        publication = read(folder / 'publication.json')
        if (expected != read(folder / 'asap7-general-state.json') or capabilities(cfg) != read(folder / 'capabilities.json')
                or v != read(folder / 'independent-verdict.json') or publication['published'] != [
                    {'file': 'asap7-general-state.json', 'sha256': sha(folder / 'asap7-general-state.json'), 'stage': 'grt'}]
                or publication['full_D_ready'] or publication['production_price_binding_qualified']):
            raise ValueError('qualified S published coefficients/domain/scope differ')
        support = {e['id']: e for e in read(folder / 'check-paid-entries.json')}
        for path in receipts.rglob('*.command.json'):
            command = read(path); e = support.pop(command['budget_reservation_id'])
            if (command['exit_code'] or e['status'] != 'completed' or e['command'] != command['command']
                    or e['walltime_s'] != command['walltime_s']
                    or abs(e['CPU_time_s'] - modules['budget'].cpu_seconds(path.with_name(path.name.removesuffix('.command.json') + '.resources.txt'))) > 1e-8):
                raise ValueError('qualified S verification receipt differs')
        if support: raise ValueError('qualified S check receipt coverage incomplete')
    if external:
        archive = read(folder / 'raw-archive.json'); raw = Path(archive['path'])
        if sha(raw / 'manifest.json') != archive['manifest_sha256']: raise ValueError('qualified S raw archive changed')
        with redirect_stdout(io.StringIO()): verify_raw(raw, external=True)
    print(json.dumps({'status': 'passed', 'external': external, 'training_reproduced': retrain,
        'stage_rows': 756, 'independent_status': 'passed', 'published_stages': ['grt'], 'PPA_calls': 0,
        'production_price_binding_qualified': False, 'full_D_ready': False}), flush=True)


def isolated(folder, raw=False):
    with tempfile.TemporaryDirectory(prefix='qualified-S-isolated-') as td:
        temp = Path(td); local = temp / 'evidence'; shutil.copytree(folder, local); source = temp / 'source'
        unpack(local / 'source-pool.json.gz', source)
        action = 'verify-raw' if raw else 'verify'
        code = '''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
source,folder,action=sys.argv[1:]
def guard(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):
   raise RuntimeError('original tree read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guard(builtins.open);io.open=guard(io.open)
def forbidden(*a,**kw):raise RuntimeError('S replay subprocess forbidden')
subprocess.Popen=forbidden
sys.path.insert(0,source);sys.argv=['sealed',action,'--folder',folder]
runpy.run_module('experiments.arithmetic_dse.model_general_control_evidence',run_name='__main__')
'''
        env = os.environ.copy(); env.update(PATH='', PYTHONDONTWRITEBYTECODE='1'); env.pop('PYTHONPATH', None)
        command = [sys.executable, '-B', '-c', code, str(source), str(local), action]
        p = subprocess.run(command, cwd=temp, env=env, capture_output=True, text=True)
        if p.returncode: raise ValueError('qualified S isolated replay failed: ' + p.stderr[-2500:])
        targets = ['documents-pool.json.gz', 'index.json'] if raw else ['documents-pool.json.gz', 'asap7-general-state.json', 'capabilities.json']
        for name in targets:
            path = local / name; original = path.read_bytes(); changed = bytearray(original); changed[len(changed) // 2] ^= 1; path.write_bytes(changed)
            p = subprocess.run(command, cwd=temp, env=env, capture_output=True, text=True); path.write_bytes(original)
            if p.returncode == 0 or 'qualified S evidence identity mismatch' not in p.stderr:
                raise ValueError('qualified S altered evidence accepted: ' + name)
        if not raw:
            # Same isolated source/data tree: retraining may import only the installed numerical runtime.
            # /home/zyrv runtime packages are absent in the declared environment.
            again = command[:-1] + ['retrain']
            p = subprocess.run(again, cwd=temp, env=env, capture_output=True, text=True)
            if p.returncode: raise ValueError('qualified S isolated training replay failed: ' + p.stderr[-2500:])
    print(json.dumps({'status': 'passed', 'raw': raw, 'original_tree_build_ledger_denied': True,
        'PATH_empty': True, 'replay_subprocess_denied': True, 'tamper_rejected': True,
        'isolated_train_only_reproduction': not raw, 'PPA_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('archive', 'verify-raw', 'isolate-raw', 'publish', 'verify', 'retrain', 'isolated'))
    parser.add_argument('--folder', type=Path, required=True); parser.add_argument('--root', type=Path)
    parser.add_argument('--archive', type=Path); parser.add_argument('--external', action='store_true')
    args = parser.parse_args(); folder = args.folder.resolve()
    if args.action == 'archive': archive(args.root.resolve(), folder)
    elif args.action == 'verify-raw': verify_raw(folder, external=args.external)
    elif args.action == 'isolate-raw': isolated(folder, raw=True)
    elif args.action == 'publish': publish(args.archive.resolve(), args.root.resolve(), folder)
    elif args.action in ('verify', 'retrain'): verify(folder, external=args.external, retrain=args.action == 'retrain')
    else: isolated(folder)
