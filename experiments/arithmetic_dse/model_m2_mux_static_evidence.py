"""Replay raw Mux evidence and the frozen P4 verdict without retraining or EDA."""
import argparse
import hashlib
import json
from pathlib import Path
import tempfile

from .budget import Ledger, usage
from .model_collection import sha, write
from .model_features import features as base_features
from .model_m2_f5_evidence import Pool, load_pool
from .model_m2_mux_static_evaluate import report, verify_result
from .model_m2_mux_static_features import descriptor, features
from .model_m2_mux_static_fit import digest, quality

ROOT = Path(__file__).resolve().parents[2]
SUFFIX = Path('asap7/arithmetic_probe/base')


def read(path):
    return json.loads(Path(path).read_text())


def package(result_path, publication, out):
    from .model_m2_collection import run_directory
    result = verify_result(result_path)
    selection = Path(result['selection_path'])
    frozen = read(selection)
    fitting = read(frozen['dataset_path'])
    test = read(result['dataset_path'])
    collection = read(fitting['admission_path'])
    out.mkdir(parents=True, exist_ok=False)
    pool = Pool(out)
    paths = {
        'selection': selection, 'candidate': selection.parent/'candidate.json',
        'validation': selection.parent/'fit-report.json', 'fitting-data': frozen['dataset_path'],
        'test-data': result['dataset_path'], 'test-result': result_path,
        'test-admission': test['admission_path'], 'collection-admission': fitting['admission_path'],
        'inherited11': frozen['inherited11_path'], 'publication': publication/'publication.json',
        'evaluation-receipt': selection.parent/'mux-static-independent-evaluation.json',
        'test-consumption': selection.parent/'mux-static-independent-consumption.json',
        'reproduction': selection.parent.parent/'mux-static-refit-v1/reproduction.json',
        'published-query-proof': selection.parent.parent/'mux-static-verdict-work-v1/raw-fitting-and-production-query.json',
        'parent-F5-index': ROOT/'experiments/arithmetic/evidence/step7_m2_F5_v1/index.json',
    }
    for item in read(paths['publication'])['published']:
        paths['released-model'] = publication/item['file']
    documents = {name: pool.add(path) for name, path in paths.items()}
    freezes = []
    path = selection
    while path:
        f = read(path)
        freezes.append(pool.add(path))
        for name, expected in f['sources'].items():
            if pool.add(path.parent/'source'/name) != expected:
                raise ValueError('changed frozen fitter source')
        for name in ('candidate.json', 'fit-report.json'):
            pool.add(path.parent/name)
        path = Path(f['parent_fit_path']) if f.get('parent_fit_path') else None
    for name, expected in result['sources'].items():
        if pool.add(result_path.parent/'source'/name) != expected:
            raise ValueError('changed executed evaluator source')
    for name in ('candidate.json', 'fit-report.json'):
        if (selection.parent/name).read_bytes() != (selection.parent.parent/'mux-static-refit-v1'/name).read_bytes():
            raise ValueError('actual static model reproduction changed')
    parent_plan = read(collection['parent_plan'])
    parent_tasks = {t['id']: t for t in parent_plan['tasks']}
    tasks = [(parent_tasks[r['task_id']], run_directory(Path(collection['parent_plan']).parent, parent_tasks[r['task_id']]), False)
             for r in fitting['legacy_runs']]
    registered = {t['id']: t for t in collection['tasks']}
    tasks += [(registered[r['task_id']], Path(r['directory']), True) for r in fitting['runs']+test['runs']]
    runs = []
    charged = set()
    for task, directory, mux_labels in tasks:
        manifest = read(directory/'manifest.json')
        selected = [directory/name for name in ('manifest.json', 'input.sv', 'sample-contract.json', 'liberty_cells.json')]
        for stage in manifest['metrics']:
            prefix = directory/'reports'/SUFFIX/('vulsim_'+stage['stage'])
            selected += sorted(p for p in prefix.parent.glob(prefix.name+'*') if p.is_file())
            selected.append(directory/'results'/SUFFIX/({'synth': '1_synth', 'grt': '5_1_grt'}[stage['stage']]+'.sdc'))
        proof = directory/'logs'/SUFFIX/'structural_cec'
        if proof.exists():
            selected += sorted(p for p in proof.iterdir() if p.is_file() and (p.name in ('proof.json', 'state-correspondence.json', 'complete-boundary.json') or p.suffix == '.log'))
        files = {str(p.relative_to(directory)): pool.add(p) for p in selected}
        for name, h in files.items():
            if name in manifest['evidence_sha256'] and h != manifest['evidence_sha256'][name]:
                raise ValueError('changed raw measurement text')
        charged.update(c['budget_reservation_id'] for c in manifest['commands'])
        runs.append({'task': task, 'files': files, 'mux_labels': mux_labels,
                     'external_directory': str(directory), 'external_artifacts': manifest['evidence_sha256']})
    ledger = read(Ledger().path)
    entries = [e for e in ledger['entries'] if e['id'] in charged]
    if len(entries) != len(charged) or any(e['status'] == 'reserved' for e in entries):
        raise ValueError('unsettled consumed measurement charges')
    cost = out/'consumed-run-ledger.json'
    write(cost, {'entries': entries, 'usage': usage(entries),
                'scope': '240 successful source measurements consumed by Mux; global receipt retains all historical failures and support'})
    documents['consumed-run-ledger'] = pool.add(cost)
    # Save the replay sources as text; the original executed sources above remain separate.
    replay = {}
    for path in sorted(Path(__file__).parent.glob('*.py'))+sorted(Path(__file__).with_name('configs').rglob('*.json')):
        replay[str(path.relative_to(ROOT))] = pool.add(path)
    pool.flush()
    write(out/'index.json', {'version': 'asap7-m2-mux-static-evidence-v1', 'documents': documents,
        'fit_freezes': freezes, 'runs': runs, 'text_pool_parts': pool.parts, 'replay_code': replay,
        'verifier_sha256': sha(__file__), 'quality_status': result['quality_status'],
        'combined_passing_operations': result['combined_passing_operations'], 'full_D_ready': False,
        'scope': result['prospective_release_scope'], 'parent_F5_index_sha256': documents['parent-F5-index'],
        'portable_scope': '240 raw measurements / 480 stages / 1152 main Mux rows; raw diagnostic arcs; fixed validation and P4 numerical verdict; inherited11 identity and F5 pass receipts',
        'external_scope': 'original raw artifact hashes and full saved CTS CEC, exact mapping and paid provenance; no new SAT or EDA'})
    (out/'README.md').write_text('''# ASAP7 Mux静态上下文独立资格与组件发布

冻结参数的一次性P4评价通过，grt组件12／12合格；原F5整体失败保持。
新Mux只独立验收parallel_dynamic_mux、原精确位宽／ABC-SDC及生产单捕获银行。
mixed-control新系数、任意阶段／共享／混合算术／状态／区间及完整D仍未合格。

便携回放：`python3 -m experiments.arithmetic_dse.model_m2_mux_static_evidence verify --folder experiments/arithmetic/evidence/step7_m2_mux_static_v1`

增加`--external`核验本机原始大产物与完整已存CEC，再重新提取合法拟合和P4标签。两种模式均不启动EDA或重训；便携模式不重新执行SAT。240份测量中只消费Mux主标签，共1152行；其他控制标签仅核对原始阶段完整性。11类保持原模型／域／裕量及F5合格收据，原F5封存包仍是其原始证据来源。

可部署组件模型保存于`asap7-primitives.json`；`publication.json`和`capabilities.json`明确发布范围与未完成项。独立P4标签已经消费，永久排除后续拟合、验证和算法／裕量／域选择。Git提交由用户执行。
''')
    for name in ('publication.json', 'asap7-primitives.json'):
        if (publication/name).exists():
            (out/name).write_bytes((publication/name).read_bytes())
    write(out/'capabilities.json', {'quality_status': result['quality_status'], 'qualified_grt_operations': result['combined_passing_operations'],
        'mux_schema': 'arithmetic-mux-static-features-v1', 'scope': result['prospective_release_scope'],
        'unchanged11': True, 'native_feature_and_numeric_parity': True, 'production_Python_query_checked': True,
        'production_native_stage_binding': False, 'state_and_composition_qualified': False,
        'formal_targets_qualified': False, 'full_D_ready': False, 'nine_case_36_records_complete': False})
    print(json.dumps({'status': 'packaged', 'runs': len(runs), 'rows': len(fitting['rows'])+len(test['rows']),
                      'pool_bytes': sum(p['bytes'] for p in pool.parts)}), flush=True)


def verify(folder, external=False):
    from .backend import stage_metrics
    from .model_samples import read_labels as old_labels, verify_capture_banks as old_banks
    from .model_m2_mux_labels import read_labels as mux_labels, verify_capture_banks as mux_banks
    from .sdc import verify_sdc, rtl_ports
    index = read(folder/'index.json')
    objects = load_pool(folder, index)
    docs = index['documents']
    obj = lambda name: json.loads(objects[docs[name]])
    if sha(__file__) != index['verifier_sha256']:
        raise ValueError('changed replay implementation')
    for name, h in index['replay_code'].items():
        if sha(ROOT/name) != h:
            raise ValueError('changed replay source/configuration: '+name)
    frozen, candidate, validation = obj('selection'), obj('candidate'), obj('validation')
    fitting, test, result = obj('fitting-data'), obj('test-data'), obj('test-result')
    for name, key in (('candidate', 'candidate_sha256'), ('validation', 'fit_report_sha256'), ('fitting-data', 'dataset_sha256')):
        if docs[name] != frozen[key]:
            raise ValueError('changed frozen fit input')
    if result['selection_sha256'] != docs['selection'] or result['dataset_sha256'] != docs['test-data']:
        raise ValueError('changed independent inputs')
    for h in index['fit_freezes']:
        f = json.loads(objects[h])
        if any(v not in objects for v in (f['candidate_sha256'], f['fit_report_sha256'], *f['sources'].values())):
            raise ValueError('missing executed parent/source')
        if f.get('parent_fit_sha256') and f['parent_fit_sha256'] not in objects:
            raise ValueError('broken fit parent chain')
    inherited = obj('inherited11')
    if len(inherited['operations']) != 11 or inherited['mux_test_labels_present'] or inherited['source_F5_overall_status'] != 'failed':
        raise ValueError('invalid inherited qualification')
    for op, value in inherited['operations'].items():
        if value['independent_quality']['status'] != 'passed' or value['model'] != candidate['stages']['grt']['operations'][op]:
            raise ValueError('changed inherited model/domain/receipt')
    rows = fitting['rows']+test['rows']
    if len(rows) != 1152 or len(index['runs']) != 240 or len({r['id'] for r in rows}) != 1152:
        raise ValueError('incomplete Mux raw evidence')
    if any(r['split'] not in ('train', 'validation') for r in fitting['rows']) or any(r['split'] != 'test' for r in test['rows']):
        raise ValueError('fitting/test role violation')
    if {r['source_sha256'] for r in fitting['rows']} & {r['source_sha256'] for r in test['rows']}:
        raise ValueError('source partition overlap')
    by_manifest = {}
    for row in rows:
        by_manifest.setdefault(row['manifest_sha256'], []).append(row)
    diagnostics = {d['row_id']: d for d in fitting['diagnostics']+test['diagnostics']}
    charges = {e['id']: e for e in obj('consumed-run-ledger')['entries']}
    if usage(list(charges.values())) != obj('consumed-run-ledger')['usage']:
        raise ValueError('changed resource receipt')
    stages = 0
    for run in index['runs']:
        files = run['files']
        m, task = json.loads(objects[files['manifest.json']]), run['task']
        if m['status'] != 'completed' or m['task_id'] != task['id'] or files['input.sv'] != task['rtl_sha256']:
            raise ValueError('changed measurement/source identity')
        contract = json.loads(objects[files['sample-contract.json']])
        cells = json.loads(objects[files['liberty_cells.json']])['cells']
        specs = {s['id']: s for s in contract['labels']}
        cut = descriptor(contract['labels'])
        reader, banker = (mux_labels, mux_banks) if run['mux_labels'] else (old_labels, old_banks)
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for name, h in files.items():
                if name in m['evidence_sha256'] and m['evidence_sha256'][name] != h:
                    raise ValueError('changed portable raw text')
                path = d/name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(objects[h])
            for stored in m['metrics']:
                stage = stored['stage']
                reports = d/'reports'/SUFFIX
                prefix = reports/('vulsim_'+stage)
                parsed = stage_metrics(reports, stage, cells, task['period_ps'], selected=m['platform_profile'])
                if any(v != stored[k] for k, v in parsed.items() if k != 'raw_reports_prefix'):
                    raise ValueError('raw stage does not recompute')
                labels = reader(prefix, d/'sample-contract.json', parsed['raw_report_units']['time']['to_ps'])
                banks = banker(prefix, d/'sample-contract.json', cells)
                if labels != stored['model_labels'] or banks != stored.get('model_capture_banks', {}):
                    raise ValueError('raw QD/bank evidence differs')
                sdc = d/'results'/SUFFIX/({'synth': '1_synth', 'grt': '5_1_grt'}[stage]+'.sdc')
                verify_sdc(sdc.read_text(), m['platform_profile'], task['period_ps'], rtl_ports((d/'input.sv').read_text(), task['top']))
                instances = [line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
                label_by_id = {v['id']: v for v in labels}
                for r in (r for r in by_manifest[files['manifest.json']] if r['stage'] == stage):
                    spec = specs[r['spec']['id']]
                    label = label_by_id[spec['id']]
                    base = base_features(spec['lhs_width'], spec['rhs_width'], spec['result_width'], spec['fanout'], 1500, task['period_ps'])
                    area = sum(cells[master]['area_um2'] for name, master in instances if master in cells and not cells[master]['sequential'] and name.startswith(spec['arithmetic_scope']))
                    if (r['spec'] != spec or r['features'] != base or r['delay_ps'] != label['data_delay_ps'] or r['comb_area_um2'] != area
                        or r['bank_counts'] != banks.get(spec['id']) or r['observed_H_ps'] != task['period_ps']-label['data_delay_ps']-label['slack_ps']
                        or r['static_context_sha256'] != digest(cut) or r['static_features'] != features(base, cut, spec['id'])):
                        raise ValueError('raw Mux row/features do not recompute')
                    if run['mux_labels']:
                        expected = {'row_id': r['id'], 'all_input_start_pin': label['start_pin'], 'diagnostic_only': True,
                                    'arcs': {a: label_by_id[spec['id']+'_'+a] for a in ('select', 'data_a', 'data_b')}}
                        if diagnostics[r['id']] != expected:
                            raise ValueError('raw diagnostic arcs differ')
                stages += 1
        for c in m['commands']:
            e = charges[c['budget_reservation_id']]
            if e['status'] != 'completed' or e['command'] != c['command'] or c['exit_code'] or c['cleanup']['remaining_live_pids']:
                raise ValueError('unpaid/unsettled raw measurement')
        if external:
            d = Path(run['external_directory'])
            if sha(d/'manifest.json') != files['manifest.json'] or any(sha(d/n) != h for n, h in run['external_artifacts'].items()):
                raise ValueError('changed external raw artifacts')
    for stage, value in candidate['stages'].items():
        selected = [r for r in fitting['rows'] if r['stage'] == stage and r['split'] == 'validation']
        for q in ('delay', 'area'):
            if quality(selected, value['operations']['mux'][q], q) != validation['stages'][stage]['mux'][q]['quality']:
                raise ValueError('frozen validation does not recompute')
    actual = report(test['rows'], candidate)
    publication = obj('publication')
    if actual != result['stages'] or actual['grt']['status'] != result['quality_status'] or result['quality_status'] != index['quality_status']:
        raise ValueError('independent verdict does not recompute')
    if bool(publication['published']) != (result['quality_status'] == 'passed') or publication['scope'] != test['prospective_release_scope']:
        raise ValueError('publication scope/verdict differs')
    for item in publication['published']:
        if sha(folder/item['file']) != item['sha256'] or docs['released-model'] != item['sha256']:
            raise ValueError('changed released model')
        released = obj('released-model')
        for op, model in candidate['stages']['grt']['operations'].items():
            if any(model[k] != released['stages']['grt']['operations'][op][k] for k in ('delay', 'area', 'joint_domain')):
                raise ValueError('publication changed frozen model numbers/domain')
    if sha(folder/'publication.json') != docs['publication']:
        raise ValueError('changed publication receipt')
    if external:
        from .model_m2_mux_fit import extract as extract_fitting
        from .model_m2_mux_static_evaluate import extract as extract_test
        with tempfile.TemporaryDirectory() as td:
            first, second = Path(td)/'fitting.json', Path(td)/'test.json'
            extract_fitting(Path(fitting['admission_path']).parent, first)
            if read(first) != read(fitting['parent_dataset_path']):
                raise ValueError('external complete fitting replay differs')
            extract_test(Path(test['admission_path']).parent, second)
            if read(second) != test:
                raise ValueError('external complete independent replay differs')
    print(json.dumps({'status': 'verified', 'runs': len(index['runs']), 'stages': stages, 'rows': len(rows),
                      'quality_status': result['quality_status'], 'combined_passing_operations': result['combined_passing_operations'],
                      'external': external}), flush=True)
    return index


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('action', choices=['package', 'verify'])
    ap.add_argument('--result', type=Path)
    ap.add_argument('--publication', type=Path)
    ap.add_argument('--folder', type=Path, required=True)
    ap.add_argument('--external', action='store_true')
    a = ap.parse_args()
    if a.action == 'package':
        package(a.result.resolve(), a.publication.resolve(), a.folder.resolve())
    else:
        verify(a.folder.resolve(), a.external)


if __name__ == '__main__':
    main()
