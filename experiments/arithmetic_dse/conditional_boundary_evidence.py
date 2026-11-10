"""Read-only S reuse validation, selected RTL checks and portable evidence.

New validation observations never change the frozen S/binding parameters.
The compact replay uses only bundled observations, parameters and source.
"""
import argparse
import ast
from collections import defaultdict
from contextlib import redirect_stdout
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import shutil
import statistics
import tempfile

ROOT = Path(__file__).resolve().parents[2]
SUFFIX = Path('asap7/arithmetic_probe/base')
OWNERS = ('input_service', 'native_state', 'external_state')


def read(p):
    return json.loads(Path(p).read_text())


def write(p, value):
    Path(p).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(value).hexdigest()


def predict(model, features):
    if model['kind'] != 'nonnegative_linear':
        raise ValueError('unknown frozen S predictor')
    return sum(c * features[n] for n, c in zip(model['features'], model['coefficients'], strict=True))


def percentile(values, fraction):
    values = sorted(values)
    at = (len(values) - 1) * fraction
    a, b = math.floor(at), math.ceil(at)
    return values[a] * (b - at) + values[b] * (at - a) if a != b else values[a]


def control_upper(binding, features):
    result = {}
    for name, model in binding['control_models'].items():
        result[name] = max(predict(model['regression'], {
            **features, **{'exact_SDC_' + str(t): int(t == clock) for t in binding['control_exact_clocks']}
        }) + model['train_upper_correction_ps'] + model['reserve_ps'] for clock in binding['control_exact_clocks'])
    return result


def evaluate(observations, binding, state, gates):
    """Pure deterministic replay: no raw/test/training files or EDA access."""
    rows, errors, area_groups = [], [], defaultdict(list)
    coverage = defaultdict(lambda: [0, 0])
    shared_coverage = defaultdict(lambda: [0, 0])
    for row in observations['rows']:
        if row['stage'] != 'grt':
            continue
        predicted = {o: predict(state['stages']['grt']['area_models'][o], row['owner_features'][o]) for o in OWNERS}
        area = {}
        for owner in OWNERS:
            actual = row['owner_area_um2'][owner]
            relative = abs(predicted[owner] - actual) / actual
            area[owner] = dict(predicted_um2=predicted[owner], actual_um2=actual, relative_error=relative)
            area_groups[(row['source'], owner)].append(relative)
        uppers = {**binding['six_path_upper_ps'], **control_upper(binding, row['control_features'])}
        paths = []
        for path in row['boundary_paths']:
            if path['birth_adapter_path_diagnostic_only']:
                continue
            actual = path['H_ps'] + path['delay_ps']
            upper = uppers[path['id']]
            passed = actual <= upper + 1e-6
            coverage[path['id']][0] += int(passed)
            coverage[path['id']][1] += 1
            check = dict(path_class=path['id'], measured_requirement_ps=actual, upper_ps=upper,
                         deficit_ps=max(0., actual - upper), covered=passed)
            paths.append(check)
            if not passed:
                errors.append(dict(task=row['task_id'], kind='boundary', **check))
        ff = sum(row['owner_FF_bits'].values())
        shared = dict(shared_clock=binding['shared']['clock_area_per_FF_um2'] * ff,
                      shared_physical=binding['shared']['physical_area_per_functional_um2'] * sum(predicted.values()),
                      root_boundary_repair=binding['shared']['root_repair_area_um2'])
        shared_checks = {}
        for owner, upper in shared.items():
            actual = row['owner_area_um2'].get(owner, 0.)
            passed = actual <= upper + 1e-6
            shared_checks[owner] = dict(actual_um2=actual, upper_um2=upper, covered=passed)
            shared_coverage[owner][0] += int(passed)
            shared_coverage[owner][1] += 1
            if not passed:
                errors.append(dict(task=row['task_id'], kind='shared_area', owner=owner, **shared_checks[owner]))
        wire = dict(actual_ps=row['wire_increment_max_ps'], upper_ps=binding['shared']['wire_per_edge_ps'])
        wire['covered'] = wire['actual_ps'] <= wire['upper_ps'] + 1e-6
        shared_coverage['wire'][0] += int(wire['covered'])
        shared_coverage['wire'][1] += 1
        if not wire['covered']:
            errors.append(dict(task=row['task_id'], kind='wire', **wire))
        rows.append(dict(task_id=row['task_id'], target_ps=row['period_ps'], area=area,
                         boundaries=paths, shared=shared_checks, wire=wire,
                         whole_setup_slack_ps=row['setup_slack_ps'], whole_hold_slack_ps=row['hold_slack_ps']))
    sources = []
    for (source, owner), values in sorted(area_groups.items()):
        median, p95 = statistics.median(values), percentile(values, .95)
        passed = median <= gates['S_area_source_median_max'] and p95 <= gates['S_area_source_P95_max']
        item = dict(source=source, owner=owner, points=len(values), median_relative_error=median,
                    P95_relative_error=p95, passed=passed)
        sources.append(item)
        if not passed:
            errors.append(dict(kind='state_area', **item))
    coverage = {k: dict(covered=a, total=b) for k, (a, b) in sorted(coverage.items())}
    shared_coverage = {k: dict(covered=a, total=b) for k, (a, b) in sorted(shared_coverage.items())}
    if len(rows) != 6 or len(sources) != 6 or len(coverage) != 8 or any(x['total'] != 6 for x in coverage.values()):
        raise ValueError('limited reuse coverage inventory differs')
    return dict(version='conditional-S-reuse-validation-result-v1', status='passed_limited' if not errors else 'failed_reuse_gates',
                physical_points=6, source_banks=2, synth_grt_stages=len(observations['rows']), area_by_source=sources,
                boundary_coverage=coverage, shared_coverage=shared_coverage, points=rows, failures=errors,
                original_S_coefficients_changed=False, binding_parameters_changed=False,
                new_labels_used_for_fitting=False, old_consumed_test_labels_read=False,
                arithmetic_joint_qualified=False, production_qualified=False, full_D_ready=False)


def path_wires(directory, stage, path):
    """Also validate port paths, whose first hop is a port-to-input net."""
    from .conditional_boundary_binding import raw_context
    from .model_physical_path_v2 import canonical, verify_combinational_arc
    pins, instances, nets = raw_context(str(directory), stage)
    prefix = directory / 'reports' / SUFFIX / ('vulsim_' + stage)
    points = [(canonical(n), float(t)) for n, t in (s.split('\t') for s in
              Path(str(prefix) + '_reference_' + path['id'] + '_points.tsv').read_text().splitlines())]
    start, end = canonical(path['start_pin']), canonical(path['end_pin'])
    positions = [i for i, (n, _) in enumerate(points) if n == start]
    if len(positions) != 1 or points[-1][0] != end:
        raise ValueError('actual S path endpoint differs')
    points = points[positions[0]:]
    wires = []
    for (a, ta), (b, tb) in zip(points, points[1:]):
        if not math.isfinite(ta) or not math.isfinite(tb) or tb < ta - 1e-5:
            raise ValueError('actual S path has invalid arrival')
        if a == start and path['kind'] == 'port':
            if b not in nets or nets[b]['direction'] != 'input' or nets[b]['net'] != start:
                raise ValueError('S port path is not actually connected')
        else:
            ca, pa = a.rsplit('/', 1)
            cb, pb = b.rsplit('/', 1)
            if ca == cb:
                verify_combinational_arc(pins[instances[ca]], pa, pb)
                continue
            if a not in nets or b not in nets or nets[a]['direction'] != 'output' or nets[b]['direction'] != 'input' or nets[a]['net'] != nets[b]['net']:
                raise ValueError('S data wire is not actually connected')
        wires.append(max(0., tb - ta))
    return wires


def extract(folder, out):
    from . import backend
    from .budget import Ledger, cpu_seconds
    from .model_general_state_fit import owner_features
    from .model_general_control_samples import control_features
    from .model_general_state_labels import partition, labels
    from .model_m2_live_cec_v3 import verify_proof
    from .model_fast_sdc_v3 import verify_sdc, rtl_ports
    from .platforms import profile, verify_wire_readback
    if out.exists():
        raise ValueError('preserve previous S validation extraction')
    out.mkdir(parents=True)
    admission, proposal = read(folder / 'admission.json'), read(folder / 'proposal.json')
    progress = read(folder / 'validation-progress.json')
    binding, state = read(folder / 'binding-candidate.json'), read(folder / 'reused-S.json')
    if (progress['phase'] != 'validation_complete' or progress['errors'] or progress['active'] or
            set(progress['completed']) != {t['id'] for t in admission['tasks']} or
            sha(folder / 'binding-candidate.json') != admission['candidate_sha256'] or
            sha(folder / 'reused-S.json') != admission['S_sha256']):
        raise ValueError('S validation not complete or frozen parameters changed')
    for name, h in admission['sources'].items():
        if sha(ROOT / name) != h or sha(folder / 'measurement-source' / name) != h:
            raise ValueError('S validation source drift: ' + name)
    ledger = {e['id']: e for e in read(Ledger().path)['entries']}
    rows, runs, paid = [], [], []
    for task in admission['tasks']:
        directory = folder / 'runs' / task['id']
        m = read(directory / 'manifest.json')
        spec = read(directory / 'general-state-contract.json')['spec']
        if (m['status'] != 'completed' or m['data_role'] != 'binding_validation' or
                m['period_ps'] != task['period_ps'] or m['abc_target_ps'] != task['period_ps'] or
                sha(directory / 'input.sv') != task['rtl_sha256'] or
                sha(directory / 'general-state-contract.json') != task['contract_sha256'] or
                m['metrics'] != read(directory / 'metrics.json')):
            raise ValueError('actual S point identity differs')
        for name, h in m['evidence_sha256'].items():
            if sha(directory / name) != h:
                raise ValueError('saved S physical product changed: ' + name)
        for command in m['commands']:
            e = ledger[command['budget_reservation_id']]
            if (e['status'] != 'completed' or e['command'] != command['command'] or
                    e.get('admission_id') != admission['id'] or command['exit_code'] or
                    command['cleanup']['remaining_live_pids'] or abs(e['CPU_time_s'] - cpu_seconds(command['gnu_time'])) > 1e-8):
                raise ValueError('S paid command ancestry differs')
            paid.append(e['id'])
        cells, pins = read(directory / 'liberty_cells.json')['cells'], read(directory / 'liberty-pins.json')
        proof = directory / 'logs' / SUFFIX / 'structural_cec/proof.json'
        with redirect_stdout(io.StringIO()):
            verify_proof(proof, directory / 'results' / SUFFIX / '4_before_rsz_lec.v', directory / 'results' / SUFFIX / '4_after_rsz_lec.v')
        for g in m['metrics']:
            stage = g['stage']
            prefix = directory / 'reports' / SUFFIX / ('vulsim_' + stage)
            ownership, instances, _ = partition(prefix, pins, profile('asap7'), spec)
            if ownership != read(directory / ('S-' + stage + '-ownership.json')) or ownership['owner_FF_bits'] != spec['expected_FF_bits']:
                raise ValueError('S unique ownership or exact FF projection differs')
            actual = backend.stage_metrics(directory / 'reports' / SUFFIX, stage, cells, task['period_ps'], selected=profile('asap7'))
            for key in ('cell_area_um2', 'setup_worst_slack_ps', 'hold_worst_slack_ps', 'timing_coverage_complete'):
                if actual[key] != g[key]:
                    raise ValueError('S raw stage metrics differ: ' + key)
            if abs(sum(ownership['owner_area_um2'].values()) - actual['cell_area_um2']) > 1e-6:
                raise ValueError('S area does not conserve')
            paths = labels(prefix, task['period_ps'], g['raw_report_units']['time']['to_ps'], pins, instances)
            if paths != g['boundary_paths'] or not actual['timing_coverage_complete']:
                raise ValueError('S actual path extraction differs')
            wires = {p['id']: path_wires(directory, stage, p) for p in paths}
            maximum = max(v for p in paths if p['kind'] == 'register' for v in wires[p['id']])
            if maximum != g['wire_increment_max_ps']:
                raise ValueError('S wire label differs')
            stem = '1_synth' if stage == 'synth' else '5_1_grt'
            sdc = verify_sdc((directory / 'results' / SUFFIX / (stem + '.sdc')).read_text(), profile('asap7'),
                             task['period_ps'], rtl_ports((directory / 'input.sv').read_text(), 'ModelBundle'), serialization_stage=stage)
            if sdc != m['sdc_contracts'][stage] or verify_wire_readback(Path(str(prefix) + '_layer_rc.tsv'), profile('asap7')) != g['wire_RC_readback']:
                raise ValueError('S actual SDC/RC differs')
            rows.append(dict(task_id=task['id'], source=task['source'], stage=stage, period_ps=task['period_ps'],
                             owner_features={o: owner_features(spec, task['period_ps'], o) for o in OWNERS},
                             control_features=control_features(spec), owner_area_um2=ownership['owner_area_um2'],
                             owner_FF_bits=ownership['owner_FF_bits'], boundary_paths=paths, wire_increment_max_ps=maximum,
                             port_wire_increment_max_ps=max(v for p in paths if p['kind'] == 'port' for v in wires[p['id']]),
                             setup_slack_ps=g['setup_worst_slack_ps'], hold_slack_ps=g['hold_worst_slack_ps'],
                             ownership_sha256=sha(directory / ('S-' + stage + '-ownership.json')),
                             sdc_contract=sdc, all_register_and_port_arcs_and_nets_checked=True))
        runs.append(dict(task_id=task['id'], directory=str(directory), manifest_sha256=sha(directory / 'manifest.json'),
                         CEC_proof_sha256=sha(proof), RTL_sha256=task['rtl_sha256'], contract_sha256=task['contract_sha256']))
    observations = dict(version='conditional-S-reuse-observations-v1', rows=rows, runs=runs,
                        admission_sha256=sha(folder / 'admission.json'), S_sha256=admission['S_sha256'],
                        binding_sha256=admission['candidate_sha256'], physical_leaf_ids=paid,
                        full_raw_path=str(folder), old_test_labels_read=False, parameters_retuned=False)
    result = evaluate(observations, binding, state, proposal['validation_gates'])
    write(out / 'observations.json', observations)
    write(out / 'validation.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('points', 'area_by_source')}, indent=2), flush=True)


def cycles(run, out):
    from regression.arithmetic_condition_consumer import cycles as prepare
    if out.exists():
        raise ValueError('preserve selected RTL cycle attempt')
    (out / 'native').mkdir(parents=True)
    data = read(run / 'real-boundary.json')
    write(out / 'native/consumer.json', data)
    for row in data['runs']:
        shutil.copy2(run / row['rtl_file'], out / 'native' / row['rtl_file'])
    prepare(out)


def replay(evidence):
    manifest = read(evidence / 'manifest.json')
    documents = {}
    for name, h in manifest['files'].items():
        if sha(evidence / name) != h:
            raise ValueError('compact S evidence hash mismatch: ' + name)
    raw = b''.join((evidence / name).read_bytes() for name in manifest['chunks'])
    pool = json.loads(gzip.decompress(raw))
    if {n: e['sha256'] for n, e in pool.items()} != manifest['documents']:
        raise ValueError('S evidence member inventory differs')
    with tempfile.TemporaryDirectory(prefix='conditional-S-replay-') as name:
        restored = Path(name)
        for name, entry in pool.items():
            path = Path(name)
            content = entry['text'].encode()
            if path.is_absolute() or '..' in path.parts or digest(content) != entry['sha256']:
                raise ValueError('invalid S evidence member')
            target = restored / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
            if sha(target) != entry['sha256']:
                raise ValueError('actual S evidence restore differs')
            documents[name] = entry['sha256']
        # Use bundled pure evaluator, rather than silently inheriting live code.
        namespace = dict(__file__=str(restored / 'source/conditional_boundary_evidence.py'), __name__='bundled_S_evidence')
        exec(compile((restored / 'source/conditional_boundary_evidence.py').read_text(), 'bundled_S_evidence', 'exec'), namespace)
        result = namespace['evaluate'](read(restored / 'validation/observations.json'), read(restored / 'binding/binding-candidate.json'),
                                       read(restored / 'binding/reused-S.json'), read(restored / 'binding/proposal.json')['validation_gates'])
        if result != read(restored / 'validation/validation.json'):
            raise ValueError('bundled S scientific replay differs')
        # Recompute real state, S/shared prices, controls, DAG and selections.
        tree = ast.parse((restored / 'source/arithmetic_state_boundary.py').read_text())
        body = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('word', 'projection', 'close', 'verify')]
        parity = dict(read=read, write=write, sha=sha, math=math, defaultdict=defaultdict)
        exec(compile(ast.Module(body=body, type_ignores=[]), 'bundled_S_parity', 'exec'), parity)
        with redirect_stdout(io.StringIO()):
            parity['verify'](restored / 'native', restored / 'binding/binding-candidate.json', restored / 'input/request.json')
        if read(restored / 'native/state-boundary-proof.json') != read(restored / 'expected-state-proof.json'):
            raise ValueError('bundled actual-state/DAG replay differs')
        cycle = read(restored / 'cycles/cycle-proof.json')
        if cycle['status'] != 'passed' or len(cycle['RTL']) != 3:
            raise ValueError('selected cycle proof missing')
        for row in cycle['RTL']:
            if sha(restored / 'native' / row['rtl_file']) != row['sha256']:
                raise ValueError('simulated selected RTL differs')
        for name, h in cycle['vectors_and_testbench_sha256'].items():
            if sha(restored / 'cycles' / name) != h:
                raise ValueError('simulated vectors/testbench differ')
    receipt = dict(status='passed', members=len(documents), actual_restore_and_all_hashes_checked=True,
                   scientific_validation_recomputed=True, actual_132_view_S_DAG_and_selection_recomputed=True,
                   reuse_verdict=result['status'], full_D_ready=False)
    print(json.dumps(receipt), flush=True)
    return receipt


def package(folder, validation, run, cycle, out, support):
    if out.exists():
        raise ValueError('preserve previous compact evidence')
    out.mkdir(parents=True)
    pool = {}
    def add(name, path):
        content = Path(path).read_text()
        pool[name] = dict(text=content, sha256=digest(content.encode()))
    for name in ('binding-candidate.json', 'reused-S.json', 'public-service-witness.sv', 'proposal.json', 'admission.json', 'training-derivation.json', 'validation-progress.json'):
        add('binding/' + name, folder / name)
    for name in ('observations.json', 'validation.json'):
        add('validation/' + name, validation / name)
    for name in ('real-boundary.json', 'state-boundary-proof.json', 'selected-500.sv', 'selected-1500.sv', 'selected-3000.sv'):
        add('native/' + name, run / name)
    add('expected-state-proof.json', run / 'state-boundary-proof.json')
    add('input/request.json', ROOT / 'build/step8-condition-interface-20261110/acceptance-v1/input/request.json')
    add('input/node-fixture.json', ROOT / 'build/step8-condition-interface-20261110/acceptance-v1/input/fixture.json')
    for name in ('cycles.hex', 'cycles-tb.sv', 'cycles.sv'):
        add('cycles/' + name, cycle / name)
    result = read(support / 'cycles-run-v1/commands.json')[0]
    if result['exit_code'] or 'CONDITIONAL_SELECTED_RTL_PASS selections=3 cycles=160' not in Path(result['log']).read_text():
        raise ValueError('actual selected RTL simulation not passed')
    selected = read(run / 'real-boundary.json')['runs']
    if any(sha(cycle / 'native' / r['rtl_file']) != r['rtl_sha256'] for r in selected):
        raise ValueError('current selected RTL differs from simulated RTL')
    cycle_proof = dict(status='passed', cycles_per_RTL=160, RTL=[dict(rtl_file=r['rtl_file'], sha256=r['rtl_sha256']) for r in selected],
                       vectors_and_testbench_sha256={n: sha(cycle / n) for n in ('cycles.hex', 'cycles-tb.sv', 'cycles.sv')},
                       command_record=result, physical_or_PPA_qualification=False)
    write(out / 'cycle-proof.json', cycle_proof)
    add('cycles/cycle-proof.json', out / 'cycle-proof.json')
    for pattern in ('*cycles*.log', '*iverilog*.log'):
        for path in support.glob('*/' + pattern):
            add('receipts/' + path.parent.name + '/' + path.name, path)
    for path in sorted(support.glob('*/commands.json')):
        add('receipts/' + path.parent.name + '/commands.json', path)
    for path in sorted((folder / 'archives').glob('*.index.json')):
        add('full-artifact-restore/' + path.name, path)
    sources = ['experiments/arithmetic_dse/conditional_boundary_evidence.py', 'regression/arithmetic_state_boundary.py',
               'experiments/arithmetic_dse/conditional_boundary_binding.py', 'experiments/arithmetic_dse/conditional_boundary_binding_v2.py',
               'experiments/arithmetic_dse/conditional_boundary_probe.py', 'rtlzz/src/backend/arithmetic_state_boundary.cpp',
               'rtlzz/src/backend/arithmetic_state_boundary.hpp', 'rtlzz/src/backend/arithmetic_condition_selection.hpp',
               'rtlzz/src/backend/arithmetic_condition_selection.cpp', 'rtlzz/testv2/arithmetic_state_boundary_consumer.cpp']
    for name in sources:
        add('source/' + Path(name).name, ROOT / name)
    for task in read(folder / 'admission.json')['tasks']:
        if 'sources/' + task['source'] + '/contract.json' not in pool:
            add('sources/' + task['source'] + '/contract.json', task['contract'])
            add('sources/' + task['source'] + '/input.sv', task['rtl'])
        directory = folder / 'runs' / task['id']
        add('physical/' + task['id'] + '/CEC-proof.json', directory / 'logs' / SUFFIX / 'structural_cec/proof.json')
    raw = gzip.compress(json.dumps(pool, ensure_ascii=False, separators=(',', ':')).encode(), mtime=0)
    chunks = []
    for i, at in enumerate(range(0, len(raw), 512 * 1024)):
        name = f'pool-{i:03d}.json.gz.part'
        (out / name).write_bytes(raw[at:at + 512 * 1024])
        chunks.append(name)
    shutil.copy2(validation / 'validation.json', out / 'validation.json')
    shutil.copy2(run / 'state-boundary-proof.json', out / 'software-proof.json')
    shutil.copy2(__file__, out / 'replay.py')
    write(out / 'manifest.json', dict(version='real-conditional-state-boundary-evidence-v1', chunks=chunks,
          files={p.name: sha(p) for p in out.iterdir()}, documents={n: p['sha256'] for n, p in pool.items()},
          source_sha256={n: sha(ROOT / n) for n in sources}, full_raw_artifact_directory=str(folder),
          original_S_unchanged=True, production_qualified=False, full_D_ready=False))
    if sum(p.stat().st_size for p in out.iterdir()) > 5 * 1024**2 or any(p.stat().st_size > 1024**2 for p in out.iterdir()):
        raise ValueError('compact S evidence size budget exceeded')
    print('CONDITIONAL_S_EVIDENCE_PACKAGED documents=' + str(len(pool)), flush=True)


def closure(support, folder, out):
    from .budget import Ledger, usage, cpu_seconds
    ledger = read(Ledger().path)
    records = {}
    for path in support.glob('*/commands.json'):
        for record in read(path):
            records[record['budget_reservation_id']] = record
    admission = read(folder / 'admission.json')['id']
    entries = [e for e in ledger['entries'] if e['id'] in records or e.get('admission_id') == admission]
    physical = [e for e in entries if e.get('admission_id') == admission]
    if len(physical) != 36 or {s: sum(e['stage'] == s for e in physical) for s in ('synth', 'grt')} != {'synth': 6, 'grt': 6}:
        raise ValueError('S six-point exact fee inventory differs')
    for e in entries:
        if e['status'] not in ('completed', 'failed'):
            raise ValueError('own S task has unsettled leaves')
        record = records.get(e['id']) or read(Path(e['command_record']))
        if (record['command'] != e['command'] or record['exit_code'] != e['exit_code'] or
                record['cleanup']['remaining_live_pids'] or abs(e['CPU_time_s'] - cpu_seconds(record['gnu_time'])) > 1e-8):
            raise ValueError('S leaf receipt or fee differs')
    report = dict(version='conditional-real-boundary-resource-closure-v1', entries=entries, usage=usage(entries),
                  exact_support_reservation_ids=sorted(records), physical_admission_id=admission,
                  failures_preserved=[e['id'] for e in entries if e['status'] == 'failed'],
                  concurrent_operator_collection_excluded=True, global_closure_claimed=False,
                  global_entries_at_snapshot=len(ledger['entries']),
                  closing_bookkeeping_leaf='outer support/closure-v1 command record; included after its completion in final reported totals')
    write(out / 'resource-closure.json', report)
    print(json.dumps(dict(status='own_leaves_settled', entries=len(entries), usage=usage(entries))), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('extract', 'cycles', 'package', 'replay', 'closure'))
    for name in ('folder', 'out', 'run', 'validation', 'cycle', 'support', 'evidence'):
        p.add_argument('--' + name, type=Path)
    a = p.parse_args()
    if a.action == 'extract':
        extract(a.folder.resolve(), a.out.resolve())
    elif a.action == 'cycles':
        cycles(a.run.resolve(), a.out.resolve())
    elif a.action == 'package':
        package(a.folder.resolve(), a.validation.resolve(), a.run.resolve(), a.cycle.resolve(), a.out.resolve(), a.support.resolve())
    elif a.action == 'closure':
        closure(a.support.resolve(), a.folder.resolve(), a.out.resolve())
    else:
        replay(a.evidence.resolve())
