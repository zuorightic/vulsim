"""Small raw-text archive and portable replay of the finite clock diagnosis."""
import argparse
from collections import Counter
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import struct
import tempfile

from .backend import stage_metrics
from .characterization import mapped_netlist_hash
from .model_samples import read_labels
from .sdc import verify_sdc, rtl_ports


def digest(data): return hashlib.sha256(data).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def write(path, obj): Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2)+'\n')
def same(a, b, label):
    if isinstance(a, (float, int)) and not isinstance(a, bool) and isinstance(b, (float, int)):
        okay = math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-7)
    else: okay = a == b
    if not okay: raise ValueError('clock evidence mismatch: ' + label)


def package(reference, sweep, report, out):
    out.mkdir(parents=True, exist_ok=False)
    frozen = read(reference)
    a = read(sweep / 'admission.json')
    data = read(report)
    objects = {}
    def add(path):
        value = Path(path).read_text()
        h = digest(value.encode())
        objects[h] = value
        return h
    documents = {'reference.json': add(reference), 'response.json': add(report),
                 'reference-admission.json': add(frozen['admission_path']),
                 'sweep-admission.json': add(sweep / 'admission.json')}
    failures = []
    if a.get('explicit_representation_correction'):
        proof = a['explicit_representation_correction']
        documents['parent-sweep-admission.json'] = add(proof['parent_admission'])
        for failure in proof['failures_retained']:
            directory = Path(failure['directory'])
            files = {}
            for path in [directory/'manifest.json', directory/'synth.command.json', directory/'synth.resources.txt',
                         directory/'results/asap7/arithmetic_probe/base/1_synth.sdc']:
                files[str(path.relative_to(directory))] = add(path)
            same(files['manifest.json'], failure['manifest_sha256'], 'preserved failed attempt')
            failures.append({'proof': failure, 'files': files})
    # Preserve executed source snapshots rather than substituting later code.
    source_admissions = [read(frozen['admission_path']), a]
    if a.get('explicit_representation_correction'):
        source_admissions.append(read(a['explicit_representation_correction']['parent_admission']))
    for admission in source_admissions:
        for rel, h in admission['sources'].items():
            same(add(Path(admission['source_snapshot']) / rel), h, 'executed source snapshot')
    runs = []
    tasks = [(Path(c['run']), c['task']) for c in frozen['cases']]
    tasks += [(Path(t['reuse_directory']) if t.get('reuse_directory') else sweep / 'runs' / t['id'], t) for t in a['tasks']]
    for directory, t in tasks:
        m = read(directory / 'manifest.json')
        files = {}
        required = ['manifest.json', 'input.sv', 'sample-contract.json', 'liberty_cells.json', 'effective-environment.txt',
                    'config.mk', 'flow-scripts/abc_speed.script', 'results/asap7/arithmetic_probe/base/1_2_yosys.v',
                    'results/asap7/arithmetic_probe/base/1_synth.sdc', 'results/asap7/arithmetic_probe/base/5_1_grt.sdc']
        paths = [directory / name for name in required]
        paths += sorted((directory / 'reports/asap7/arithmetic_probe/base').glob('vulsim_*'))
        paths += sorted(directory.glob('*.command.json')) + sorted(directory.glob('*.resources.txt'))
        paths += [directory / name for name in ('synth.log', 'grt.log', 'logs/asap7/arithmetic_probe/base/1_2_yosys.log')
                  if (directory / name).exists()]
        for path in paths:
            name = str(path.relative_to(directory))
            files[name] = add(path)
            if name in m['evidence_sha256']:
                same(files[name], m['evidence_sha256'][name], 'actual artifact ' + name)
        runs.append({'task': t, 'files': files, 'local_full_run': str(directory.resolve()),
                     'external_artifacts': m['evidence_sha256']})
    blob = gzip.compress(json.dumps(objects, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode(), mtime=0)
    (out / 'raw-text.json.gz').write_bytes(blob)
    write(out / 'index.json', {'version': 'interval-clock-diagnosis-text-evidence-v1',
                              'role': 'diagnosis_only_no_model_qualification', 'not_training': True,
                              'text_pool_sha256': digest(blob), 'documents': documents, 'runs': runs, 'failed_attempts': failures,
                              'portable_scope': 'raw SDC, QD paths, area, mapping reuse and generated target replay',
                              'external_scope': 'original full logs, ODB and routing artifacts retained in build',
                              'verifier_sha256': digest(Path(__file__).read_bytes())})
    shutil.copy2(report, out / 'response.json')
    keys = ['case', 'variant', 'stage', 'ABC_ps', 'SDC_ps', 'QD_ps', 'cell_delay_ps', 'wire_delay_ps',
            'core_comb_area_um2', 'total_cell_area_um2', 'path_slack_ps', 'whole_setup_slack_ps', 'whole_hold_slack_ps']
    with (out / 'response.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, keys, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(data['rows'])
    print(json.dumps({'archive_bytes': len(blob), 'runs': len(runs), 'text_objects': len(objects)}))


def verify(folder):
    index = read(folder / 'index.json')
    blob = (folder / 'raw-text.json.gz').read_bytes()
    same(digest(blob), index['text_pool_sha256'], 'text archive')
    objects = json.loads(gzip.decompress(blob))
    for h, text in objects.items(): same(digest(text.encode()), h, 'content-addressed text')
    def obj(h): return json.loads(objects[h])
    report = obj(index['documents']['response.json'])
    same(read(folder / 'response.json'), report, 'published response')
    frozen = obj(index['documents']['reference.json'])
    admissions = [obj(index['documents'][name]) for name in ('reference-admission.json', 'sweep-admission.json')]
    same(digest(objects[index['documents']['reference-admission.json']].encode()), frozen['admission_sha256'], 'reference admission')
    same(index['documents']['reference.json'], report['reference_sha256'], 'response reference')
    for a in admissions:
        for name, h in a['sources'].items():
            if h not in objects: raise ValueError('missing executed source: ' + name)
    by_case = {c['case']: c for c in frozen['cases']}
    expected_tasks = {t['id']: t for a in admissions for t in a['tasks']}
    if {r['task']['id'] for r in index['runs']} != set(expected_tasks) or len(index['runs']) != len(expected_tasks):
        raise ValueError('missing/duplicate declared diagnostic run')
    rows = {(r['task'], r['stage']): r for r in report['rows']}
    if len(rows) != len(report['rows']) or len(rows) != 2*len(index['runs']):
        raise ValueError('incomplete/duplicate diagnostic rows')
    checked = 0
    for run in index['runs']:
        t, files = run['task'], run['files']
        same(t, expected_tasks[t['id']], 'declared task')
        m = obj(files['manifest.json'])
        same(m['status'], 'completed', 'completed run')
        same(m['task_id'], t['id'], 'task identity')
        same(m['period_ps'], t['period_ps'], 'SDC request')
        same(m['abc_target_ps'], t['abc_target_ps'], 'ABC request')
        same(m['io_delay_max_ps'], 300, 'fixed IO request')
        script = objects[files['flow-scripts/abc_speed.script']]
        same(files['flow-scripts/abc_speed.script'], m['mapping_context']['abc_script_sha256'], 'executed ABC script')
        targets = re.findall(r'-D ([0-9.eE+\-]+)', script)
        if not targets or any(float(v) != t['abc_target_ps'] for v in targets):
            raise ValueError('rendered ABC target differs from request')
        environment = dict(line.strip().split('=', 1) for line in objects[files['effective-environment.txt']].splitlines() if line.strip())
        same(float(environment['ABC_CLOCK_PERIOD_IN_PS']), t['abc_target_ps'], 'effective ABC target')
        same(files['input.sv'], t['rtl_sha256'], 'source family')
        same(files['sample-contract.json'], t['sample_contract_sha256'], 'source boundary')
        if t['variant'] != 'reference':
            ref = by_case[t['case']]
            d, h = ref['D_ref_ps'], ref['H_ref_ps']
            axis, value = t['variant'].split('-')
            k = float(value)
            nominal = t.get('nominal_period_ps', t['period_ps'])
            if 'nominal_period_ps' in t:
                f32 = lambda x: struct.unpack('f', struct.pack('f', x))[0]
                scale = f32(1e-12)
                same(t['period_ps'], f32(f32(nominal*scale)/scale), 'canonical clock representation')
                if f32(t['period_ps']*scale) != f32(nominal*scale):
                    raise ValueError('canonical clock changes internal STA period')
            if axis == 'sdc':
                same(t['abc_target_ps'], 1500, 'fixed ABC')
                same(nominal, math.ceil(h + k*d), 'predeclared SDC target')
                same(files['results/asap7/arithmetic_probe/base/1_2_yosys.v'], ref['mapped_netlist_file_sha256'], 'same mapped bytes')
                same(m['checkpoint_reuse']['old_ODB_or_old_SDC_copied'], False, 'fresh physical chain')
            else:
                same(t['abc_target_ps'], math.ceil(k*d), 'predeclared ABC target')
                same(nominal, math.ceil(h+d), 'fixed SDC')
        for name, h in files.items():
            if name in m['evidence_sha256']: same(h, m['evidence_sha256'][name], 'original manifest artifact ' + name)
        cells = obj(files['liberty_cells.json'])['cells']
        spec, = obj(files['sample-contract.json'])['labels']
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name, h in files.items():
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(objects[h])
            reports = root / 'reports/asap7/arithmetic_probe/base'
            for stored in m['metrics']:
                stage = stored['stage']
                row = rows[t['id'], stage]
                parsed = stage_metrics(reports, stage, cells, m['period_ps'], selected=m['platform_profile'])
                for key in parsed:
                    if key != 'raw_reports_prefix': same(parsed[key], stored[key], 'raw stage ' + key)
                prefix = reports / ('vulsim_' + stage)
                labels = read_labels(prefix, root / 'sample-contract.json', parsed['raw_report_units']['time']['to_ps'])
                same(labels, stored['model_labels'], 'actual QD path')
                label, = labels
                same(row['QD_ps'], label['data_delay_ps'], 'reported QD')
                same(row['path_slack_ps'], label['slack_ps'], 'reported path slack')
                same(row['path_H_ps'], m['period_ps']-label['data_delay_ps']-label['slack_ps'], 'nonoverlapping overhead')
                same(row['whole_setup_slack_ps'], parsed['setup_worst_slack_ps'], 'whole setup')
                same(row['whole_hold_slack_ps'], parsed['hold_worst_slack_ps'], 'whole hold')
                same(row['total_cell_area_um2'], parsed['cell_area_um2'], 'whole area')
                same(row['manifest_sha256'], files['manifest.json'], 'row source')
                area = 0.
                masters = Counter()
                for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines():
                    name, master, *_ = line.split('\t')
                    if master in cells and name.startswith(spec['arithmetic_scope']) and not cells[master]['sequential']:
                        area += cells[master]['area_um2']; masters[master] += 1
                same(row['core_comb_area_um2'], area, 'core area')
                same(row['core_masters'], dict(masters), 'core mapping')
                scale = parsed['raw_report_units']['time']['to_ps']
                points = [(pin, float(v)*scale) for pin, v in
                          (line.split('\t') for line in Path(str(prefix)+'_model_s000_points.tsv').read_text().splitlines())]
                starts = [i for i, (pin, _) in enumerate(points) if pin == label['start_pin']]
                if len(starts) != 1 or points[-1][0] != label['end_pin']:
                    raise ValueError('incomplete data path points')
                points = points[starts[0]:]
                delays = {'cell_delay_ps': 0., 'wire_delay_ps': 0.}
                for (pin, before), (next_pin, after) in zip(points, points[1:]):
                    kind = 'cell_delay_ps' if pin.rsplit('/', 1)[0] == next_pin.rsplit('/', 1)[0] else 'wire_delay_ps'
                    delays[kind] += after-before
                for key, value in delays.items(): same(row[key], value, 'path component '+key)
                sdc = root / 'results/asap7/arithmetic_probe/base' / ({'synth':'1_synth', 'grt':'5_1_grt'}[stage]+'.sdc')
                actual = verify_sdc(sdc.read_text(), m['platform_profile'], m['period_ps'],
                                    rtl_ports((root / 'input.sv').read_text(), t['top']), io_delay_max_ps=300)
                same(actual, m['sdc_contracts'][stage], 'actual SDC semantics')
                same(row['mapped_netlist_sha256'], mapped_netlist_hash((root / 'results/asap7/arithmetic_probe/base/1_2_yosys.v').read_text()), 'mapped graph')
                if t['variant'] == 'reference' and stage == 'grt':
                    same(by_case[t['case']]['D_ref_ps'], label['data_delay_ps'], 'reference D')
                    same(by_case[t['case']]['H_ref_ps'], row['path_H_ps'], 'reference H')
                checked += 1
    comparisons = []
    for c in frozen['cases']:
        for stage in ('synth', 'grt'):
            subset = [r for r in report['rows'] if r['case'] == c['case'] and r['stage'] == stage]
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
    same(comparisons, report['comparisons'], 'response comparison recomputation')
    for failure in index.get('failed_attempts', []):
        files, proof = failure['files'], failure['proof']
        m = obj(files['manifest.json'])
        same(files['manifest.json'], proof['manifest_sha256'], 'failed manifest identity')
        same(m['failure_code'], 'sdc_contract_mismatch', 'retained failure')
        same(m['metrics'], [], 'no failed measurement relabeled as valid')
        if len(m['commands']) != 2 or any(c['exit_code'] != 0 for c in m['commands']):
            raise ValueError('failed attempt was not the diagnosed post-synth SDC check')
    return {'status': 'passed', 'runs': len(index['runs']), 'stages_and_actual_SDCs': checked,
            'raw_QD_and_area_rows': checked, 'failed_attempts_preserved': len(index.get('failed_attempts', [])),
            'model_qualification': False, 'EDA_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['package', 'verify'])
    parser.add_argument('--reference', type=Path)
    parser.add_argument('--sweep', type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'package': package(args.reference, args.sweep, args.report, args.out)
    else: print(json.dumps(verify(args.out), indent=2))


if __name__ == '__main__': main()
