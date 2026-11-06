"""Seal the first S independent verdict; portable raw replay never selects a model."""
import argparse
from contextlib import redirect_stdout
import importlib
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

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'asap7-general-state-independent-evidence-v1'


def frozen_modules(source):
    name = '_general_state_sealed'
    for key in list(sys.modules):
        if key == name or key.startswith(name + '.'):
            del sys.modules[key]
    package = types.ModuleType(name)
    package.__path__ = [str(source / 'experiments/arithmetic_dse')]
    sys.modules[name] = package
    return {key: importlib.import_module(name + '.' + key) for key in (
        'backend', 'platforms', 'sdc', 'sdc_storage_v3', 'budget',
        'model_general_state_samples_v2', 'model_general_state_labels',
        'model_general_state_fit', 'model_general_state_test', 'model_m2_live_cec_v3')}


def seal(root, folder):
    from .budget import Ledger, usage
    from .model_general_state_test import verify as verify_admission, verdict as fixed_verdict
    independent = root / 'independent-v1'
    a = verify_admission(independent)
    fit_path = Path(a['dataset'])
    test_path = root / 'independent-check-v1/test-dataset.json'
    evaluation = root / 'independent-verdict-v1'
    fit, test, candidate = read(fit_path), read(test_path), read(a['candidate'])
    result, identity = read(evaluation / 'verdict.json'), read(evaluation / 'identity.json')
    marker = read(independent / 'test-consumed.json')
    if (identity['dataset_sha256'] != sha(test_path) or identity['verdict_sha256'] != sha(evaluation / 'verdict.json')
            or marker['dataset_sha256'] != sha(test_path) or marker['candidate_sha256'] != a['candidate_sha256']
            or marker['selection_freeze_sha256'] != a['selection_freeze_sha256']
            or fixed_verdict(candidate, test) != result or result['status'] != 'failed'
            or result['eligible_deployable_stages'] or result['parameters_domain_or_reserve_changed']):
        raise ValueError('immutable first S failure and one-time consumption required')
    folder.mkdir(parents=True, exist_ok=False)
    sources = {str(p.relative_to(ROOT)): p for p in (ROOT / 'experiments/arithmetic_dse').glob('*.py')}
    sources.update({str(p.relative_to(ROOT)): p for p in (ROOT / 'experiments/arithmetic_dse/configs').rglob('*') if p.is_file()})
    for name, h in a['sources'].items():
        p = independent / 'source' / name
        if sha(p) != h:
            raise ValueError('archived independent source differs')
        sources[name] = p
    pack(folder / 'source-pool.json.gz', sources)
    documents = {
        'fit-data.json': fit_path, 'test-data.json': test_path, 'candidate.json': Path(a['candidate']),
        'selection-freeze.json': Path(a['selection_freeze']),
        'validation.json': Path(a['candidate']).with_name('validation.json'),
        'immutable-baseline-diagnostic.json': Path(a['candidate']).with_name('immutable-baseline-diagnostic.json'),
        'verdict.json': evaluation / 'verdict.json', 'identity.json': evaluation / 'identity.json',
        'test-consumed.json': independent / 'test-consumed.json',
        'fit-byte-proof.json': root / 'fit-byte-proof.json', 'pin-table.json': Path(a['pin_table']),
        'fit-admission.json': Path(a['fitting_admission']), 'test-admission.json': independent / 'admission.json',
        'fit-progress.json': Path(a['fitting_admission']).with_name('progress.json'),
        'test-progress.json': independent / 'progress.json',
    }
    fa = read(a['fitting_admission'])
    documents['predecessor-admission.json'] = Path(fa['predecessor_admission'])
    documents['software-proof.json'] = Path(fa['software_proof'])
    documents['storage-proof.json'] = Path(fa['storage_proof'])
    for name in read(root / 'fit-byte-proof.json')['files']:
        if (root / 'fit-v1' / name).read_bytes() != (root / 'fit-v2' / name).read_bytes():
            raise ValueError('sealed byte reproduction differs')
        documents['repeat/' + name] = root / 'fit-v2' / name
    pack(folder / 'documents-pool.json.gz', documents)
    tasks = {t['id']: t for t in fa['tasks']}
    raw, receipts, runs, external, paid = {}, {}, [], {}, set()
    suffix = Path('asap7/arithmetic_probe/base')
    for run in fit['runs'] + test['runs']:
        key = run['task_id']; directory = Path(run['directory']); m = read(directory / 'manifest.json')
        if sha(directory / 'manifest.json') != run['manifest_sha256']:
            raise ValueError('raw S manifest differs while sealing')
        selected = [directory / name for name in ('manifest.json', 'input.sv', 'general-state-contract.json',
            'metrics.json', 'liberty_cells.json', 'general-synth-ownership.json', 'general-grt-ownership.json')]
        for stage, stem in [('synth', '1_synth'), ('grt', '5_1_grt')]:
            selected += [p for p in (directory / 'reports' / suffix).glob('vulsim_' + stage + '*')
                         if p.suffix in ('.rpt', '.tsv')]
            selected += [directory / 'results' / suffix / (stem + '.sdc'), directory / 'logs' / suffix / (stem + '.json')]
        cec = directory / 'logs' / suffix / 'structural_cec'
        selected += [p for p in cec.iterdir() if p.is_file() and (p.name == 'proof.json' or p.suffix == '.log')]
        for p in selected:
            h = sha(p); name = str(p.relative_to(directory))
            if name in m['evidence_sha256'] and m['evidence_sha256'][name] != h:
                raise ValueError('raw S artifact differs while sealing')
            raw[key + '/' + name] = p
        for c in m['commands']:
            paid.add(c['budget_reservation_id'])
            for p in (Path(c['log']), Path(c['gnu_time']), Path(c['log'].removesuffix('.log') + '.command.json')):
                receipts['current/' + key + '/' + p.name] = p
        external[str(directory / 'manifest.json')] = sha(directory / 'manifest.json')
        external.update({str(directory / name): h for name, h in m['evidence_sha256'].items()})
        runs.append({'task': tasks[key], 'manifest_sha256': run['manifest_sha256'], 'directory': str(directory)})
    for failure in fit['retained_failed_predecessors']:
        key = failure['task_id']; directory = Path(fa['predecessor_admission']).parent / 'runs' / key
        m = read(directory / 'manifest.json')
        receipts['failed/' + key + '/manifest.json'] = directory / 'manifest.json'
        for c in m['commands']:
            paid.add(c['budget_reservation_id'])
            for p in (Path(c['log']), Path(c['gnu_time']), Path(c['log'].removesuffix('.log') + '.command.json')):
                receipts['failed/' + key + '/' + p.name] = p
        external[str(directory / 'manifest.json')] = sha(directory / 'manifest.json')
        external.update({str(directory / name): h for name, h in m['evidence_sha256'].items()})
    for paths in (documents, raw, receipts):
        external.update({str(p.resolve()): sha(p) for p in paths.values()})
    entries = [e for e in read(Ledger().path)['entries'] if e['id'] in paid]
    if len(entries) != len(paid) or any(e['status'] == 'reserved' for e in entries):
        raise ValueError('S evidence has unsettled charges')
    write(folder / 'paid-entries.json', {'entries': entries, 'usage': usage(entries),
        'scope': '216 measured S banks plus four failed predecessor synth diagnostics; no refund'})
    pack(folder / 'raw-pool.json.gz', raw); pack(folder / 'receipts-pool.json.gz', receipts)
    write(folder / 'verdict.json', result)
    write(folder / 'publication.json', {'version': VERSION, 'status': 'rejected', 'published': [],
        'candidate_sha256': a['candidate_sha256'], 'selection_freeze_sha256': a['selection_freeze_sha256'],
        'test_dataset_sha256': sha(test_path), 'verdict_sha256': sha(evaluation / 'verdict.json'),
        'test_consumed_and_permanently_excluded': True, 'parameters_domain_or_reserve_changed': False,
        'production_price_binding_qualified': False, 'full_D_ready': False})
    write(folder / 'provenance.json', {'version': VERSION, 'runs': runs, 'external_artifacts': external,
        'portable_scope': '216 banks/432 stages/3888 paths, disjoint owners, FF geometry, SDC/RC, fixed validation/verdict and 1308 paid leaf receipts',
        'external_scope': 'all archived raw artifacts, actual tools/Liberty and complete saved CTS CEC; no new EDA/SAT',
        'failed_predecessor_numeric_labels_inherited': False, 'full_D_ready': False})
    (folder / 'README.md').write_text('''# ASAP7一般状态S首轮独立失败封存

108 train／54 validation／54新独立test全部完成，原始数据有效。冻结参数一次性评价：synth通过；grt三个功能状态／控制面积分项均通过原中位20%／P95 50%，控制边界69／72通过，发布为空。
失败为1431ps native_enable超14.537323ps、4528ps native_valid超60.583038ps、11913ps native_valid超2.266129ps。九目标、原50ps reserve、全部参数和范围不改；三个面积分项通过不被改写成完整S发布。

便携核验：`python3 -B -m experiments.arithmetic_dse.model_general_state_evidence verify --folder experiments/arithmetic/evidence/step7_general_state_failure_v1`
增加`--external`核验原始大产物、实际Liberty／工具和完整已存CTS CEC；两者不执行新EDA或SAT。
隔离／篡改核验：上述模块使用`isolated --folder ...`。便携回放不读原build、账本或外部工具，不重新拟合、选参数或消费测试。

216银行／432阶段／3888路径及四份旧失败综合诊断保留，全部已消费54项测试永久排除后继拟合／验证／算法／裕量／域选择。用户已确认保留面积原参数，只补控制边界后继，最终仍同时检查全部面积与边界；后继需要独立预登记和新测试。
本包不授予生产状态价格、G联合边界、整阶段、真实区间或完整D／正式36条资格。Git由用户提交。
''')
    write(folder / 'manifest.json', {'version': VERSION, 'files': {p.name: sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status': 'sealed', 'independent_status': result['status'], 'published': [],
        'banks': len(runs), 'paid_leaves': len(paid), 'bytes': sum(p.stat().st_size for p in folder.iterdir() if p.is_file())}), flush=True)


def verify(folder, external=False):
    manifest = read(folder / 'manifest.json')
    if manifest['version'] != VERSION:
        raise ValueError('S evidence schema differs')
    for name, h in manifest['files'].items():
        if sha(folder / name) != h:
            raise ValueError('S evidence identity mismatch: ' + name)
    provenance = read(folder / 'provenance.json')
    with tempfile.TemporaryDirectory(prefix='S-evidence-replay-') as td:
        base = Path(td); src, raw, docs, receipts = (base / n for n in ('source', 'raw', 'documents', 'receipts'))
        for part, dest in [('source', src), ('raw', raw), ('documents', docs), ('receipts', receipts)]:
            unpack(folder / (part + '-pool.json.gz'), dest)
        modules = frozen_modules(src); fit, test, candidate = (read(docs / n) for n in ('fit-data.json', 'test-data.json', 'candidate.json'))
        result = read(docs / 'verdict.json'); freeze = read(docs / 'selection-freeze.json')
        a, fa = read(docs / 'test-admission.json'), read(docs / 'fit-admission.json')
        for key, name in [('candidate_sha256', 'candidate.json'), ('validation_sha256', 'validation.json'),
                          ('dataset_sha256', 'fit-data.json'), ('execution_sha256', None)]:
            p = docs / name if name else src / 'experiments/arithmetic_dse/configs/model_asap7_general_state_fit_v1.json'
            if sha(p) != freeze[key]: raise ValueError('S frozen fitting identity differs')
        if (sha(docs / 'selection-freeze.json') != a['selection_freeze_sha256']
                or sha(docs / 'test-data.json') != read(docs / 'test-consumed.json')['dataset_sha256']
                or read(docs / 'identity.json')['verdict_sha256'] != sha(docs / 'verdict.json')):
            raise ValueError('S one-time identity differs')
        for name, h in a['sources'].items():
            if sha(src / name) != h: raise ValueError('S frozen source differs')
        for name, h in read(docs / 'fit-byte-proof.json')['files'].items():
            if sha(docs / name) != h or sha(docs / 'repeat' / name) != h: raise ValueError('S fit byte replay differs')
        rows = {r['id']: r for r in fit['rows'] + test['rows']}; seen = set(); groups = {}; paid = set()
        cfg = read(src / 'experiments/arithmetic_dse/configs/model_asap7_general_state_v2.json')
        specs = {s['id']: s for s in modules['model_general_state_samples_v2'].specifications(cfg)}
        pins = read(docs / 'pin-table.json'); entries = {e['id']: e for e in read(folder / 'paid-entries.json')['entries']}
        suffix = Path('asap7/arithmetic_probe/base')
        def check_commands(m, directory, owner):
            for c in m['commands']:
                e = entries[c['budget_reservation_id']]
                expected = 'failed' if c['exit_code'] else 'completed'
                if (e['status'] != expected or e['command'] != c['command'] or e['task_id'] != m['task_id']
                        or e['admission_sha256'] != owner or e['walltime_s'] != c['walltime_s']
                        or abs(e['CPU_time_s'] - modules['budget'].cpu_seconds(directory / Path(c['gnu_time']).name)) > 1e-8
                        or c['cleanup']['remaining_live_pids']):
                    raise ValueError('S paid command receipt differs')
                sidecar = read(directory / Path(c['log'].removesuffix('.log') + '.command.json').name)
                if sidecar not in (c, {k: v for k, v in c.items() if k != 'budget_reservation_id'}):
                    raise ValueError('S command sidecar differs')
                paid.add(e['id'])
        for item in provenance['runs']:
            task = item['task']; key = task['id']; directory = raw / key; m = read(directory / 'manifest.json')
            s = specs[task['source_group']]; p = m['platform_profile']; cells = read(directory / 'liberty_cells.json')['cells']
            if (sha(directory / 'manifest.json') != item['manifest_sha256'] or m['status'] != 'completed'
                    or task['features'] != modules['model_general_state_samples_v2'].features(s, task['period_ps'])
                    or read(directory / 'general-state-contract.json')['spec'] != s
                    or modules['model_general_state_samples_v2'].source(s) != (directory / 'input.sv').read_text()
                    or groups.setdefault(s['semantic_signature'], task['split']) != task['split']):
                raise ValueError('S raw source/role/geometry differs')
            check_commands(m, receipts / 'current' / key, sha(docs / ('test-admission.json' if task['split'] == 'test' else 'fit-admission.json')))
            for stage, stem in [('synth', '1_synth'), ('grt', '5_1_grt')]:
                prefix = directory / 'reports' / suffix / ('vulsim_' + stage)
                g = modules['backend'].stage_metrics(prefix.parent, stage, cells, task['period_ps'], selected=p)
                owner, instances, _ = modules['model_general_state_labels'].partition(prefix, pins, p, s)
                paths = modules['model_general_state_labels'].labels(prefix, task['period_ps'], g['raw_report_units']['time']['to_ps'], pins, instances)
                old = next(x for x in m['metrics'] if x['stage'] == stage); row = rows[key + '/' + stage]
                for name, value in g.items():
                    if name != 'raw_reports_prefix' and value != old.get(name): raise ValueError('S raw stage metric differs: ' + name)
                if (owner != read(directory / ('general-' + stage + '-ownership.json'))
                        or owner['owner_area_um2'] != row['owner_area_um2'] or owner['owner_FF_bits'] != row['owner_FF_bits']
                        or paths != row['boundary_paths'] or abs(g['cell_area_um2'] - owner['total_area_um2']) > 1e-6
                        or row['owner_features'] != {o: modules['model_general_state_fit'].owner_features(s, task['period_ps'], o) for o in candidate['owners']}):
                    raise ValueError('S raw owned area/features/paths differ')
                modules['platforms'].verify_wire_readback(Path(str(prefix) + '_layer_rc.tsv'), p)
                actual = modules['sdc_storage_v3'].verify_sdc((directory / 'results' / suffix / (stem + '.sdc')).read_text(), p,
                    task['period_ps'], modules['sdc'].rtl_ports((directory / 'input.sv').read_text(), 'ModelBundle'))
                if actual != m['sdc_contracts'][stage]: raise ValueError('S stored SDC differs')
                native = read(directory / 'logs' / suffix / (stem + '.json'))[('synth' if stage == 'synth' else 'globalroute') + '__design__instance__area__stdcell']
                modules['backend'].verify_orfs_area(g['cell_area_um2'], native)
                seen.add(row['id'])
            cec = directory / 'logs' / suffix / 'structural_cec'; proof = read(cec / 'proof.json')
            modules['model_m2_live_cec_v3'].check_result((cec / 'cec.log').read_text(), True)
            for name in proof['negative_controls']:
                modules['model_m2_live_cec_v3'].check_result((cec / ('negative-' + name + '.log')).read_text(), False)
        for f in fit['retained_failed_predecessors']:
            local = receipts / 'failed' / f['task_id']; m = read(local / 'manifest.json')
            if sha(local / 'manifest.json') != f['manifest_sha256'] or m['status'] != 'failed': raise ValueError('S diagnostic predecessor differs')
            check_commands(m, local, sha(docs / 'predecessor-admission.json'))
        if len(provenance['runs']) != 216 or len(groups) != 24 or len(seen) != 432 or seen != set(rows) or paid != set(entries):
            raise ValueError('S portable evidence coverage differs')
        for stage in ('synth', 'grt'):
            stage_rows = [r for r in fit['rows'] if r['stage'] == stage]
            if modules['model_general_state_fit'].boundary(stage_rows, cfg) != candidate['stages'][stage]['boundary_model']:
                raise ValueError('S frozen boundary differs')
            for owner in candidate['owners']:
                validation = [r for r in stage_rows if r['split'] == 'validation']
                q = modules['model_general_state_test'].quality(candidate['stages'][stage]['area_models'][owner],
                    modules['model_general_state_fit'].owner_rows(validation, owner), cfg)
                if q != read(docs / 'validation.json')[stage]['selected_validation'][owner]: raise ValueError('S fixed validation differs')
        if modules['model_general_state_test'].verdict(candidate, test) != result or result != read(folder / 'verdict.json'):
            raise ValueError('S frozen independent verdict differs')
        if result['status'] != 'failed' or read(folder / 'publication.json')['published']: raise ValueError('S failure falsely published')
        if external:
            for name, h in provenance['external_artifacts'].items():
                if sha(name) != h: raise ValueError('S external artifact differs: ' + name)
            libraries = set()
            for item in provenance['runs']:
                m = read(Path(item['directory']) / 'manifest.json')
                for asset in [*m['tools'].values(), *m['libraries']]:
                    if sha(asset['path']) != asset['sha256']: raise ValueError('S external tool/Liberty differs')
                signature = tuple((v['path'], v['sha256']) for v in m['libraries'])
                if signature not in libraries:
                    from_cells = read(Path(item['directory']) / 'liberty_cells.json')['cells']
                    _, actual_cells = modules['platforms'].library_data([Path(v['path']) for v in m['libraries']], m['platform_profile'])
                    if actual_cells != from_cells: raise ValueError('S external Liberty area/FF table differs')
                    reference = importlib.import_module('_general_state_sealed.model_reference_labels')
                    if reference.liberty(m['libraries'], actual_cells) != pins: raise ValueError('S external Liberty pin/function table differs')
                    libraries.add(signature)
                with redirect_stdout(io.StringIO()):
                    modules['model_general_state_fit'].reparse(Path(item['directory']), item['task'], pins)
    result = {'status': 'passed', 'external': external, 'banks': 216, 'stage_rows': 432, 'path_labels': 3888,
        'paid_leaf_receipts': len(paid), 'independent_status': 'failed', 'published': [], 'PPA_calls': 0, 'full_D_ready': False}
    print(json.dumps(result), flush=True); return result


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='S-isolated-') as td:
        tmp = Path(td); local = tmp / 'evidence'; shutil.copytree(folder, local); src = tmp / 'source'
        unpack(local / 'source-pool.json.gz', src)
        code = '''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
source,folder=sys.argv[1:]
def guarded(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):
   raise RuntimeError('original tree read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guarded(builtins.open);io.open=guarded(io.open)
def forbidden(*a,**kw):raise RuntimeError('replay subprocess forbidden')
subprocess.Popen=forbidden
sys.path.insert(0,source)
sys.argv=['sealed','verify','--folder',folder]
runpy.run_module('experiments.arithmetic_dse.model_general_state_evidence',run_name='__main__')
'''
        env = os.environ.copy(); env.update(PATH='', PYTHONDONTWRITEBYTECODE='1'); env.pop('PYTHONPATH', None)
        command = [sys.executable, '-B', '-c', code, str(src), str(local)]
        p = subprocess.run(command, cwd=tmp, env=env, capture_output=True, text=True)
        if p.returncode: raise ValueError('S isolated replay failed: ' + p.stderr[-2500:])
        for name in ('raw-pool.json.gz', 'verdict.json', 'publication.json'):
            path = local / name; original = path.read_bytes(); changed = bytearray(original); changed[len(changed) // 2] ^= 1; path.write_bytes(changed)
            p = subprocess.run(command, cwd=tmp, env=env, capture_output=True, text=True)
            path.write_bytes(original)
            if p.returncode == 0 or 'S evidence identity mismatch' not in p.stderr: raise ValueError('S tamper accepted: ' + name)
    print(json.dumps({'status': 'passed', 'original_tree_denied': True, 'PATH_empty': True,
        'replay_subprocess_denied': True, 'raw_verdict_publication_tamper_rejected': True, 'PPA_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('seal', 'verify', 'isolated'))
    parser.add_argument('--folder', type=Path, required=True); parser.add_argument('--root', type=Path); parser.add_argument('--external', action='store_true')
    args = parser.parse_args()
    if args.action == 'seal': seal(args.root.resolve(), args.folder.resolve())
    elif args.action == 'isolated': isolated(args.folder.resolve())
    else: verify(args.folder.resolve(), args.external)
