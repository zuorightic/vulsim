"""Finite, preregistered ABC/SDC diagnosis; no model fitting or test consumption."""
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys

from .budget import Ledger, POLICY, usage
from .characterization import mapped_netlist_hash
from .model_collection import sha, write
from .model_mul_intervals import interval, source
from .platforms import profile

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name('configs') / 'model_interval_clock_diagnosis_v1.json'
PURPOSE = 'arithmetic_interval_clock_diagnosis_only'
SUFFIX = Path('asap7/arithmetic_probe/base')


def read(path):
    return json.loads(Path(path).read_text())


def new_write(path, data):
    if Path(path).exists():
        raise ValueError('preserve existing evidence: ' + str(path))
    write(Path(path), data)


def source_files():
    names = ['backend.py', 'platform_probe.py', 'platforms.py', 'budget.py',
             'processes.py', 'sdc.py', 'characterization.py', 'model_samples.py',
             'model_interval_clock.py', 'model_mul_intervals.py', 'model_analysis.py',
             'model_collection.py', 'model_features.py']
    base = Path(__file__).parent
    return ([base / n for n in names] + [CONFIG, POLICY, base / 'configs/platforms/asap7.json']
            + sorted(p for p in (base / 'backend').iterdir() if p.is_file()))


def verify_sources(a, *, require_active=True):
    if a['protocol_sha256'] != sha(CONFIG) or a['policy_sha256'] != sha(POLICY):
        raise ValueError('changed diagnosis protocol/policy')
    for name, digest in a['sources'].items():
        if sha(Path(a['source_snapshot']) / name) != digest or (require_active and sha(ROOT / name) != digest):
            raise ValueError('changed frozen diagnosis source: ' + name)


def check_funding(total, points, directory, *, allow_support_pending=False):
    cfg = read(CONFIG)
    limits = read(POLICY)['resources']
    later = cfg['later_work_reserved']
    # Support preparation is itself a reserved leaf; physical admission never is.
    if total['pending'] and not allow_support_pending:
        raise ValueError('pending leaf blocks diagnosis')
    wall = points * 1800 + cfg['resources']['analysis_support_walltime_s']
    if (total['walltime_s'] + wall + later['walltime_s'] > limits['max_global_walltime_h'] * 3600
            or total['CPU_time_s'] + 2 * wall + later['CPU_time_s'] > limits['max_tool_CPU_time_h'] * 3600):
        raise ValueError('diagnosis plus later time reserve not funded')
    for stage, name in [('synth', 'max_synthesis_calls'), ('grt', 'max_global_route_calls')]:
        if total[stage] + points + later[stage] > limits[name]:
            raise ValueError('diagnosis plus later call reserve not funded')
    if shutil.disk_usage(directory).free < points * cfg['storage_per_point_bytes'] + 10 * 1024**3:
        raise ValueError('insufficient disk reserve')
    return {'points_reserved': points, 'worst_case_leaf_walltime_s': wall,
            'CPU_envelope_s': 2 * wall, 'later_work_reserved': later,
            'storage_planning_bytes': points * cfg['storage_per_point_bytes'], 'usage_before': total}


def make_admission(out, tasks, phase, reference=None, correction=None):
    cfg = read(CONFIG)
    snapshot = out / 'source'
    hashes = {}
    for path in source_files():
        rel = path.relative_to(ROOT)
        target = snapshot / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        hashes[str(rel)] = sha(target)
    total = usage(read(Ledger().path)['entries'])
    new_points = sum(not t.get('reuse_directory') for t in tasks)
    reserved_points = 24 if phase == 'reference' else new_points
    funding = check_funding(total, reserved_points, out, allow_support_pending=True)
    a = {'version': 'arithmetic-interval-clock-admission-v1', 'purpose': PURPOSE,
         'id': out.name, 'phase': phase, 'not_training': True, 'automatic_retries': 0,
         'protocol_sha256': sha(CONFIG), 'policy_sha256': sha(POLICY),
         'source_snapshot': str(snapshot.resolve()), 'sources': hashes,
         'tasks': tasks, 'call_caps': {'synth': new_points, 'grt': new_points, 'final': 0},
         'funding': funding, 'resources': cfg['resources'], 'reference': reference,
         'main_matrix_authorized': False, 'quality_gates_changed': False}
    if correction is not None: a['explicit_representation_correction'] = correction
    new_write(out / 'admission.json', a)
    print(json.dumps({'admission': str(out / 'admission.json'), 'phase': phase,
                      'tasks': len(tasks), 'funding': funding}), flush=True)


def prepare_reference(graphs, out):
    cfg = read(CONFIG)
    out.mkdir(parents=True, exist_ok=False)
    indexed = {}
    for path in graphs.glob('*.json'):
        graph = read(path)
        p = graph['graph']['regions'][0]['parameters']
        if p['lhs_width'] in (16, 32):
            indexed[p['lhs_width'], p['block_width'], p['result_width']] = graph
    tasks = []
    for case in cfg['cases']:
        graph = indexed[case['width'], case['block'], case['result']]
        spec = interval(graph, case['first'], case['last'])
        rtl_text, labels = source([(graph, spec)])
        folder = out / case['id']
        folder.mkdir()
        rtl = folder / 'input.sv'
        rtl.write_text(rtl_text)
        contract = folder / 'contract.json'
        new_write(contract, {'version': 'arithmetic-model-labels-v1', 'source_group': case['id'],
                             'split': 'diagnosis', 'not_training': True,
                             'protocol_sha256': sha(CONFIG), 'labels': labels})
        new_write(folder / 'graph.json', graph)
        tasks.append({'id': case['id'] + '-reference', 'case': case['id'], 'variant': 'reference',
                      'platform': 'asap7', 'profile_sha256': profile('asap7')['profile_sha256'],
                      'rtl': str(rtl.resolve()), 'rtl_sha256': sha(rtl), 'top': 'ModelBundle',
                      'sample_contract': str(contract.resolve()), 'sample_contract_sha256': sha(contract),
                      'graph': str((folder / 'graph.json').resolve()), 'graph_file_sha256': sha(folder / 'graph.json'),
                      'period_ps': cfg['reference_SDC_ps'], 'abc_target_ps': cfg['reference_ABC_ps'],
                      'io_delay_max_ps': cfg['io_delay_max_ps'], 'stage': 'grt', 'resume_synth_from': None})
    make_admission(out, tasks, 'reference')


def target_points(d, h):
    if not math.isfinite(d) or not math.isfinite(h) or d <= 0:
        raise ValueError('invalid frozen reference path')
    cfg = read(CONFIG)
    values = [('sdc-' + str(k), cfg['reference_ABC_ps'], math.ceil(h + k*d), True)
              for k in cfg['SDC_axis']['data_budget_ratios']]
    values += [('abc-' + str(k), math.ceil(k*d), math.ceil(h + d), False)
               for k in cfg['ABC_axis']['target_ratios']]
    if any(a <= 0 or t <= 0 for _, a, t, _ in values):
        raise ValueError('nonpositive generated target')
    return values


def f32(value):
    return struct.unpack('f', struct.pack('f', value))[0]


def represented_clock_ps(nominal):
    """ASAP7 OpenSTA Clock/Unit/WriteSdc binary32 round trip, not tolerance."""
    scale = f32(1e-12)
    internal = f32(float(nominal) * scale)
    native = f32(internal / scale)
    if f32(native * scale) != internal:
        raise ValueError('canonical request would change internal STA clock')
    return native


def task(args):
    if not args.admission:
        raise ValueError('diagnosis requires named admission')
    a = read(args.admission)
    matches = [t for t in a['tasks'] if t['id'] == args.task_id]
    if (a.get('purpose') != PURPOSE or a['id'] != args.admission_id or len(matches) != 1
            or a.get('not_training') is not True or a.get('automatic_retries') != 0
            or a['resources'] != read(CONFIG)['resources']):
        raise ValueError('invalid diagnosis admission')
    verify_sources(a)
    t = matches[0]
    expected_resume = t['resume_synth_from']
    actual_resume = str(args.resume_synth_from.resolve()) if args.resume_synth_from else None
    if (args.platform != t['platform'] or args.platform != 'asap7' or args.top != t['top']
            or args.stage != 'grt' or args.period_ps != t['period_ps']
            or args.abc_target_ps != t['abc_target_ps'] or args.io_delay_max_ps != 300
            or t['io_delay_max_ps'] != 300 or args.threads != 2 or args.memory_limit_mib != 8192
            or args.synth_timeout_s != 300 or args.route_timeout_s != 1200
            or args.period_role != 'resource_trial' or args.budget_purpose != 'characterization'
            or not args.sample_contract or sha(args.sample_contract) != t['sample_contract_sha256']
            or sha(args.rtl) != t['rtl_sha256'] or actual_resume != expected_resume):
        raise ValueError('diagnosis differs from frozen task/target/IO/mapping')
    if t['variant'].startswith('sdc-') != bool(expected_resume):
        raise ValueError('SDC axis requires exact reference mapping reuse')
    return a, t


def verify_admission(args, p, rtl, ledger):
    a, t = task(args)
    if p['profile_sha256'] != t['profile_sha256']:
        raise ValueError('changed diagnosis platform')
    entries = read(ledger.path)['entries']
    if any(e.get('admission_id') == a['id'] and e.get('task_id') == t['id'] for e in entries):
        raise ValueError('previously attempted diagnosis task; no automatic retry')
    check_funding(usage(entries), len(a['tasks']), args.admission.parent)
    if a['phase'] == 'sweep':
        ref = a['reference']
        if sha(ref['path']) != ref['sha256']:
            raise ValueError('changed frozen reference')
        freeze = read(ref['path'])
        item = next(x for x in freeze['cases'] if x['case'] == t['case'])
        choices = {v: (abc, sdc, reuse) for v, abc, sdc, reuse in target_points(item['D_ref_ps'], item['H_ref_ps'])}
        nominal = t.get('nominal_period_ps', t['period_ps'])
        if choices.get(t['variant']) != (t['abc_target_ps'], nominal, bool(t['resume_synth_from'])):
            raise ValueError('target not derived from frozen reference rule')
        if 'nominal_period_ps' in t and (not a.get('explicit_representation_correction')
                or t['period_ps'] != represented_clock_ps(nominal)):
            raise ValueError('clock representation correction changes intended target')
        if t['rtl_sha256'] != item['rtl_sha256'] or t['sample_contract_sha256'] != item['sample_contract_sha256']:
            raise ValueError('target variant changed source family')
    return sha(args.admission)


def seed_mapped(args, out, results, environment, command, tools):
    _, t = task(args)
    origin = Path(t['resume_synth_from'])
    m = read(origin / 'manifest.json')
    if (sha(origin / 'manifest.json') != t['source_manifest_sha256'] or m['status'] != 'completed'
            or sha(origin / 'input.sv') != t['rtl_sha256'] or m['abc_target_ps'] != args.abc_target_ps
            or m['period_ps'] != 1500 or m['io_delay_max_ps'] != 300
            or m['platform_profile']['profile_sha256'] != t['profile_sha256']):
        raise ValueError('reference mapping provenance mismatch')
    for key in ('LIB_FILES', 'TECH_LEF', 'SC_LEF', 'CORNER', 'ASAP7_USE_VT', 'LIB_MODEL',
                'TC_TEMPERATURE', 'ABC_DRIVER_CELL', 'ABC_LOAD_IN_FF', 'YOSYS_MAX_THREADS'):
        if environment.get(key) != m['effective_environment'].get(key):
            raise ValueError('mapped reuse environment changed: ' + key)
    if any(tool['sha256'] != m['tools'][name]['sha256'] for name, tool in tools.items()):
        raise ValueError('mapped reuse tool changed')
    for lib in m['libraries']:
        if sha(lib['path']) != lib['sha256']:
            raise ValueError('mapped reuse library changed')
    for filename, digest in m['files_sha256'].items():
        path = Path(filename)
        if path.is_relative_to(args.orfs.resolve()) or path.is_relative_to(Path(__file__).parent / 'backend'):
            if sha(path) != digest:
                raise ValueError('mapped reuse backend asset changed: ' + filename)
    old = origin / 'results' / SUFFIX / '1_2_yosys.v'
    normalized = next(x['mapped_netlist_sha256'] for x in m['metrics'] if x['stage'] == 'synth')
    if (sha(old) != t['mapped_netlist_file_sha256']
            or m['evidence_sha256'].get(str(old.relative_to(origin))) != sha(old)
            or mapped_netlist_hash(old.read_text()) != normalized):
        raise ValueError('mapped checkpoint bytes/graph mismatch')
    results.mkdir(parents=True, exist_ok=True)
    if any(results.iterdir()):
        raise ValueError('new physical result directory required')
    target = results / old.name
    shutil.copy2(old, target)
    command.append('--assume-old=' + str(target))
    return {'mode': 'same_mapped_netlist_fresh_SDC_and_physical_chain',
            'source_manifest_sha256': sha(origin / 'manifest.json'),
            'source_netlist_file_sha256': sha(old), 'normalized_mapped_netlist_sha256': normalized,
            'source_ABC_target_ps': m['abc_target_ps'], 'old_SDC_period_ps': m['period_ps'],
            'new_SDC_period_ps': args.period_ps, 'IO_delay_max_ps': 300,
            'reused': ['Yosys_ABC_mapping_only'], 'old_ODB_or_old_SDC_copied': False,
            'executed': ['synthesis_ODB_SDC_regeneration', 'floorplan', 'placement', 'CTS', 'global_route']}


def point_delays(path, label, scale):
    values = [(pin, float(value)*scale) for pin, value in
              (line.split('\t') for line in Path(path).read_text().splitlines())]
    start = [i for i, (pin, _) in enumerate(values) if pin == label['start_pin']]
    if len(start) != 1 or values[-1][0] != label['end_pin']:
        raise ValueError('Q/D not found in raw points')
    values = values[start[0]:]
    cell = wire = 0.
    for (pin, a), (next_pin, b) in zip(values, values[1:]):
        if pin.rsplit('/', 1)[0] == next_pin.rsplit('/', 1)[0]:
            cell += b-a
        else:
            wire += b-a
    if not math.isclose(cell + wire, label['data_delay_ps'], abs_tol=1e-4, rel_tol=1e-6):
        raise ValueError('point cell/wire sum differs from QD')
    return {'cell_delay_ps': cell, 'wire_delay_ps': wire,
            'decomposition': 'consecutive path pins: same instance cell arc, different instances net arc'}


def audit_run(directory, t, a):
    from .backend import stage_metrics
    from .model_samples import read_labels
    from .sdc import verify_sdc, rtl_ports
    m = read(directory / 'manifest.json')
    if (m['status'] != 'completed' or m['task_id'] != t['id'] or m['admission_id'] != a['id']
            or m['budget_purpose'] != 'characterization' or m['target_platform'] != 'asap7'
            or m['platform_profile']['profile_sha256'] != t['profile_sha256']
            or m['period_ps'] != t['period_ps'] or m['abc_target_ps'] != t['abc_target_ps']
            or m['io_delay_max_ps'] != 300 or sha(directory / 'input.sv') != t['rtl_sha256']
            or sha(directory / 'sample-contract.json') != t['sample_contract_sha256']
            or {s['stage'] for s in m['metrics']} != {'synth', 'grt'}):
        raise ValueError('incomplete/different actual diagnostic measurement')
    for name, digest in m['evidence_sha256'].items():
        if sha(directory / name) != digest:
            raise ValueError('changed actual measurement: ' + name)
    cells = read(directory / 'liberty_cells.json')['cells']
    reports = directory / 'reports' / SUFFIX
    spec, = read(directory / 'sample-contract.json')['labels']
    if spec['fanout'] != 1 or spec['width'] not in (16, 32):
        raise ValueError('single-core training-side source required')
    rows = []
    for stored in m['metrics']:
        stage = stored['stage']
        parsed = stage_metrics(reports, stage, cells, m['period_ps'], selected=m['platform_profile'])
        if any(parsed[k] != stored[k] for k in parsed if k != 'raw_reports_prefix'):
            raise ValueError('stage metrics do not replay')
        prefix = reports / ('vulsim_' + stage)
        labels = read_labels(prefix, directory / 'sample-contract.json', parsed['raw_report_units']['time']['to_ps'])
        if labels != stored['model_labels']:
            raise ValueError('raw QD labels do not replay')
        label, = labels
        sdc = directory / 'results' / SUFFIX / ({'synth': '1_synth', 'grt': '5_1_grt'}[stage] + '.sdc')
        actual_sdc = verify_sdc(sdc.read_text(), m['platform_profile'], m['period_ps'],
                                rtl_ports((directory / 'input.sv').read_text(), t['top']), io_delay_max_ps=300)
        if actual_sdc != m['sdc_contracts'][stage]:
            raise ValueError('actual SDC contract differs from manifest')
        counts = Counter()
        launch = capture = 0
        comb = clock_area = 0.
        for line in Path(str(prefix) + '_instances.tsv').read_text().splitlines():
            name, master, *_ = line.split('\t')
            if master not in cells:
                continue
            cell = cells[master]
            if name.startswith(spec['arithmetic_scope']) and not cell['sequential']:
                comb += cell['area_um2']
                counts[master] += 1
            if name.startswith(spec['instance_scope']):
                launch += int(cell['sequential'] and name.startswith(spec['instance_scope'] + 'src'))
                capture += int(cell['sequential'] and (name.startswith(spec['instance_scope'] + 'dst') or name.startswith(spec['instance_scope'] + 'y')))
            if name.startswith(('clkbuf_', 'clkload')):
                clock_area += cell['area_um2']
        if not (0 < launch <= sum(spec['input_widths']) and 0 < capture <= spec['capture_width'] and comb > 0):
            raise ValueError('invalid actual interval boundary/area')
        path_text = Path(str(prefix) + '_paths_max.rpt').read_text()
        paths = re.findall(r'Startpoint: (\S+).*?Endpoint: (\S+).*?Path Group: (\S+)', path_text, re.S)
        rows.append({'task': t['id'], 'case': t['case'], 'variant': t['variant'], 'stage': stage,
                     'ABC_ps': m['abc_target_ps'], 'SDC_ps': m['period_ps'], 'IO_ps': 300,
                     'QD_ps': label['data_delay_ps'], 'path_slack_ps': label['slack_ps'],
                     'path_H_ps': m['period_ps']-label['data_delay_ps']-label['slack_ps'],
                     'start_pin': label['start_pin'], 'end_pin': label['end_pin'],
                     **point_delays(str(prefix) + '_model_s000_points.tsv', label, parsed['raw_report_units']['time']['to_ps']),
                     'core_comb_area_um2': comb, 'core_masters': dict(sorted(counts.items())),
                     'launch_DFFs': launch, 'capture_DFFs': capture,
                     'total_cell_area_um2': parsed['cell_area_um2'], 'sequential_area_um2': parsed['sequential_area_um2'],
                     'clock_named_cell_area_um2': clock_area, 'clock_area_scope': 'clkbuf_/clkload names only, not exclusive whole-design area decomposition',
                     'whole_setup_slack_ps': parsed['setup_worst_slack_ps'], 'whole_hold_slack_ps': parsed['hold_worst_slack_ps'],
                     'core_minimum_period_ps': parsed['minimum_clock_period_ps'], 'coverage_complete': parsed['timing_coverage_complete'],
                     'reported_max_paths': [{'start': x, 'end': y, 'group': z} for x, y, z in paths],
                     'points_sha256': label['points_sha256'], 'sdc_sha256': sha(sdc),
                     'manifest_sha256': sha(directory / 'manifest.json'), 'rtl_sha256': t['rtl_sha256'],
                     'mapped_netlist_sha256': next(x['mapped_netlist_sha256'] for x in m['metrics'] if x['stage'] == 'synth')})
    if t['resume_synth_from']:
        reused = m.get('checkpoint_reuse', {})
        if (reused.get('old_ODB_or_old_SDC_copied') is not False
                or sha(directory / 'results' / SUFFIX / '1_2_yosys.v') != t['mapped_netlist_file_sha256']
                or rows[0]['mapped_netlist_sha256'] != reused.get('normalized_mapped_netlist_sha256')):
            raise ValueError('SDC axis did not preserve exact mapped netlist')
    return rows


def freeze_reference(folder, out):
    a = read(folder / 'admission.json')
    verify_sources(a)
    if a['phase'] != 'reference' or len(a['tasks']) != 4:
        raise ValueError('complete four-case reference required')
    cases = []
    for t in a['tasks']:
        directory = folder / 'runs' / t['id']
        rows = audit_run(directory, t, a)
        r = next(x for x in rows if x['stage'] == 'grt')
        cases.append({'case': t['case'], 'task': t, 'run': str(directory.resolve()),
                      'manifest_sha256': sha(directory / 'manifest.json'),
                      'rtl_sha256': t['rtl_sha256'], 'sample_contract_sha256': t['sample_contract_sha256'],
                      'D_ref_ps': r['QD_ps'], 'H_ref_ps': r['path_H_ps'],
                      'mapped_netlist_file_sha256': sha(directory / 'results' / SUFFIX / '1_2_yosys.v'),
                      'measurements': rows})
    new_write(out, {'version': 'arithmetic-interval-clock-reference-v1', 'not_training': True,
                    'admission_path': str((folder / 'admission.json').resolve()), 'admission_sha256': sha(folder / 'admission.json'),
                    'protocol_sha256': sha(CONFIG), 'cases': cases})
    print(json.dumps({'frozen_reference': str(out), 'sha256': sha(out),
                      'scales': [{k: c[k] for k in ('case', 'D_ref_ps', 'H_ref_ps')} for c in cases]}))


def prepare_sweep(reference, out):
    frozen = read(reference)
    if frozen['protocol_sha256'] != sha(CONFIG) or sha(frozen['admission_path']) != frozen['admission_sha256']:
        raise ValueError('changed frozen reference identity')
    verify_sources(read(frozen['admission_path']))
    out.mkdir(parents=True, exist_ok=False)
    tasks = []
    duplicates = []
    for c in frozen['cases']:
        if sha(Path(c['run']) / 'manifest.json') != c['manifest_sha256']:
            raise ValueError('changed frozen reference run')
        seen = {(1500, 1500)}
        for name, abc, sdc, reuse in target_points(c['D_ref_ps'], c['H_ref_ps']):
            if (abc, sdc) in seen:
                duplicates.append({'case': c['case'], 'variant': name, 'ABC_ps': abc, 'SDC_ps': sdc})
                continue
            seen.add((abc, sdc))
            t = dict(c['task'], id=c['case'] + '-' + name, variant=name, period_ps=sdc, abc_target_ps=abc,
                     resume_synth_from=c['run'] if reuse else None)
            if reuse:
                t.update(source_manifest_sha256=c['manifest_sha256'], mapped_netlist_file_sha256=c['mapped_netlist_file_sha256'])
            tasks.append(t)
    new_write(out / 'deduplicated-targets.json', duplicates)
    make_admission(out, tasks, 'sweep', {'path': str(reference.resolve()), 'sha256': sha(reference)})


def prepare_correction(folder, out):
    """Preserve completed/failed v1 bytes; explicitly fix representation only."""
    parent_path = folder / 'admission.json'
    parent = read(parent_path)
    verify_sources(parent, require_active=False)
    if parent['phase'] != 'sweep' or parent.get('explicit_representation_correction'):
        raise ValueError('only original frozen sweep may receive this correction')
    out.mkdir(parents=True, exist_ok=False)
    tasks, failures = [], []
    for t in parent['tasks']:
        directory = folder / 'runs' / t['id']
        if directory.exists():
            m = read(directory / 'manifest.json')
            if m['status'] == 'completed':
                audit_run(directory, t, parent)
                tasks.append(dict(t, reuse_directory=str(directory.resolve()),
                                  reuse_manifest_sha256=sha(directory / 'manifest.json'),
                                  reuse_admission=str(parent_path.resolve()), reuse_admission_sha256=sha(parent_path)))
                continue
            expected = represented_clock_ps(t['period_ps'])
            actual = (directory / 'results' / SUFFIX / '1_synth.sdc').read_text()
            periods = re.findall(r'create_clock -name (?:core_clk|io_clk) -period (\S+)', actual)
            if (m['failure_code'] != 'sdc_contract_mismatch' or m['failure_stage'] != 'synth'
                    or m['metrics'] or len(m['commands']) != 2
                    or any(c['exit_code'] != 0 for c in m['commands'])
                    or periods != [format(expected, '.4f')]*2 or expected == t['period_ps']):
                raise ValueError('failure is not the diagnosed binary32 representation defect')
            failures.append({'task': t, 'directory': str(directory.resolve()),
                             'manifest_sha256': sha(directory / 'manifest.json'),
                             'nominal_period_ps': t['period_ps'], 'equivalent_request_period_ps': expected,
                             'actual_serialized_periods': periods, 'no_grt_executed': True,
                             'internal_seconds_equal': f32(t['period_ps']*f32(1e-12)) == f32(expected*f32(1e-12))})
        tasks.append(dict(t, id=t['id']+'-representation-v2', nominal_period_ps=t['period_ps'],
                          period_ps=represented_clock_ps(t['period_ps']), supersedes_task_id=t['id']))
    if len(failures) != 1 or sum(not t.get('reuse_directory') for t in tasks) != 3:
        raise ValueError('unexpected correction scope')
    proof = {'reason': 'explicit same-internal-clock request representation; no SDC tolerance or quality gate change',
             'parent_admission': str(parent_path.resolve()), 'parent_admission_sha256': sha(parent_path),
             'failures_retained': failures, 'additional_attempt_cost': 'one failed synth command already charged; no prior grt',
             'source_identity': 'old measurements retain exact original source snapshots; new tasks bind current successor sources'}
    new_write(out / 'correction.json', proof)
    make_admission(out, tasks, 'sweep', parent['reference'], proof)


def run(folder, max_tasks=None):
    admission = (folder / 'admission.json').resolve()
    a = read(admission)
    verify_sources(a)
    outcomes = []
    for t in a['tasks']:
        if (folder / 'PAUSE').exists():
            print('PAUSED at task boundary', flush=True)
            return
        directory = Path(t['reuse_directory']) if t.get('reuse_directory') else folder / 'runs' / t['id']
        if directory.exists():
            if not (directory / 'manifest.json').exists() or read(directory / 'manifest.json')['status'] != 'completed':
                raise ValueError('previous failed/interrupted task; explicit diagnosis required')
            if t.get('reuse_directory') and (sha(directory/'manifest.json') != t['reuse_manifest_sha256']
                    or sha(t['reuse_admission']) != t['reuse_admission_sha256']):
                raise ValueError('changed inherited diagnostic measurement')
        else:
            directory.parent.mkdir(exist_ok=True)
            cmd = [sys.executable, '-B', '-m', 'experiments.arithmetic_dse.backend', '--platform', 'asap7',
                   '--admission', str(admission), '--admission-id', a['id'], '--task-id', t['id'],
                   '--rtl', t['rtl'], '--top', t['top'], '--out', str(directory),
                   '--period-ps', str(t['period_ps']), '--abc-target-ps', str(t['abc_target_ps']),
                   '--io-delay-max-ps', '300', '--stage', 'grt', '--budget-purpose', 'characterization',
                   '--sample-contract', t['sample_contract']]
            if t['resume_synth_from']:
                cmd += ['--resume-synth-from', t['resume_synth_from']]
            print('START', t['id'], 'ABC', t['abc_target_ps'], 'SDC', t['period_ps'], flush=True)
            with (folder / (t['id'] + '.driver.log')).open('x') as log:
                result = subprocess.run(cmd, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
            m = read(directory / 'manifest.json') if (directory / 'manifest.json').exists() else {'status': 'failed_before_manifest'}
            print('DONE', t['id'], m['status'], m.get('failure_reason'), flush=True)
            if result.returncode or m['status'] != 'completed':
                raise RuntimeError('diagnosis stopped; preserve task ' + t['id'])
        outcomes.append({'task': t['id'], 'manifest_sha256': sha(directory / 'manifest.json')})
        write(folder / 'outcome.json', outcomes)
        if max_tasks and len(outcomes) >= max_tasks:
            return


def analyze(folder, reference, out):
    a = read(folder / 'admission.json')
    verify_sources(a)
    frozen = read(reference)
    if a['reference'] != {'path': str(reference.resolve()), 'sha256': sha(reference)}:
        raise ValueError('sweep reference mismatch')
    parent = read(frozen['admission_path'])
    verify_sources(parent, require_active=False)
    rows = []
    for c in frozen['cases']:
        rows += audit_run(Path(c['run']), c['task'], parent)
    for t in a['tasks']:
        origin = read(t['reuse_admission']) if t.get('reuse_directory') else a
        verify_sources(origin, require_active=not bool(t.get('reuse_directory')))
        directory = Path(t['reuse_directory']) if t.get('reuse_directory') else folder / 'runs' / t['id']
        rows += audit_run(directory, t, origin)
    comparisons = []
    for c in frozen['cases']:
        for stage in ('synth', 'grt'):
            subset = [r for r in rows if r['case'] == c['case'] and r['stage'] == stage]
            for axis, names in [('SDC', ['reference', 'sdc-']), ('ABC', ['sdc-1.0', 'abc-'])]:
                values = [r for r in subset if r['variant'] == names[0] or r['variant'].startswith(names[1])]
                comparisons.append({'case': c['case'], 'stage': stage, 'axis': axis,
                                    'variants': [r['variant'] for r in values],
                                    'mapped_graphs': len({r['mapped_netlist_sha256'] for r in values}),
                                    'QD_min_ps': min(r['QD_ps'] for r in values), 'QD_max_ps': max(r['QD_ps'] for r in values),
                                    'core_area_min_um2': min(r['core_comb_area_um2'] for r in values),
                                    'core_area_max_um2': max(r['core_comb_area_um2'] for r in values),
                                    'nonnegative_local_slack': sum(r['path_slack_ps'] >= 0 for r in values),
                                    'nonnegative_whole_slack': sum(r['whole_setup_slack_ps'] >= 0 for r in values)})
    if any(c['mapped_graphs'] != 1 for c in comparisons if c['axis'] == 'SDC'):
        raise ValueError('SDC axis lost fixed mapping')
    report = {'version': 'arithmetic-interval-clock-response-v1', 'status': 'diagnosis_completed',
              'not_training': True, 'numerical_model_qualification': False,
              'protocol_sha256': sha(CONFIG), 'reference_sha256': sha(reference),
              'sweep_admission_sha256': sha(folder / 'admission.json'),
              'rows': rows, 'comparisons': comparisons, 'limitations': read(CONFIG)['limitations']}
    new_write(out, report)
    print(json.dumps({'rows': len(rows), 'comparisons': comparisons}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare-reference', 'run', 'freeze-reference', 'prepare-sweep', 'prepare-correction', 'analyze'])
    parser.add_argument('--graphs', type=Path)
    parser.add_argument('--folder', type=Path)
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--max-tasks', type=int)
    args = parser.parse_args()
    if args.action == 'prepare-reference': prepare_reference(args.graphs, args.out)
    elif args.action == 'run': run(args.folder, args.max_tasks)
    elif args.action == 'freeze-reference': freeze_reference(args.folder, args.out)
    elif args.action == 'prepare-sweep': prepare_sweep(args.reference, args.out)
    elif args.action == 'prepare-correction': prepare_correction(args.folder, args.out)
    else: analyze(args.folder, args.reference, args.out)


if __name__ == '__main__':
    main()
