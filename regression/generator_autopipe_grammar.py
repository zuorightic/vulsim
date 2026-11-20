#!/usr/bin/env python3
"""Compare real VUL/Python candidate pools on identical extracted source inputs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    dict(id='mac32-asap7', case='mac32', platform='asap7', period=1200, profile='mac32'),
    dict(id='mac32-nangate45', case='mac32', platform='nangate45', period=1500, profile='mac32'),
    dict(id='add512-asap7', case='add512', platform='asap7', period=1000, profile='add512'),
    dict(id='add512-nangate45', case='add512', platform='nangate45', period=1000, profile='add512'),
    dict(id='generic-mac32', case='mac32', platform='asap7', period=1200),
    dict(id='custom-mul24', case='mac32', platform='asap7', period=1200, mul='24', add='0'),
    dict(id='custom-add96', case='add512', platform='asap7', period=1000, mul='0', add='96'),
]


def read(path):
    return json.loads(Path(path).read_text())


def normalized_rtl(path):
    text = Path(path).read_text()
    text = re.sub(r'//[^\n]*|/\*[\s\S]*?\*/', '', text)
    return hashlib.sha256(re.sub(r'\s+', '', text).encode()).hexdigest()


def candidate_identity(row):
    return {k: row[k] for k in ('grammar', 'placement', 'rtl_sha256', 'origin', 'structure', 'view', 'static')}


def fingerprint(selection):
    row = selection['selected_candidate']
    data = dict(graph=read(row['graph']), placement=row['placement'])
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def command(args, log):
    start = time.monotonic()
    with log.open('w') as stream:
        result = subprocess.run(list(map(str, args)), cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT, timeout=900)
    if result.returncode:
        raise RuntimeError(str(args) + '\n' + log.read_text(errors='replace')[-7000:])
    return time.monotonic() - start


def check(spec, base, baselines):
    folder = base / spec['id']
    folder.mkdir()
    flags = []
    for key, option in [('profile', '--candidate-profile'), ('mul', '--mul-block-widths'), ('add', '--add-limb-widths')]:
        if key in spec:
            flags.extend([option, spec[key]])
    vul = folder / 'vul'
    vul_time = command([ROOT / 'build/vulrtlgen', '-m', ROOT / 'example/autopipe' / spec['case'] / 'Main.utb',
        '--auto-pipeline', '--target-backend', spec['platform'], '--target-period-ps', spec['period'],
        '-o', vul, *flags], folder / 'vul.log')
    reports = list(vul.rglob('*.autopipe/result.json'))
    assert len(reports) == 1, reports
    report_path = reports[0]
    report = read(report_path)
    selected_vul = read(report['selection'])
    python = folder / 'python'
    python_time = command([sys.executable, '-B', '-m', 'tools.autopipe', 'generate',
        '--source-request', report_path.parent / 'source-request.json',
        '--platform', spec['platform'], '--latency', report['L'], '--period-ps', spec['period'],
        '--out', python, *flags], folder / 'python.log')
    selected_python = read(python / 'selection.json')
    pool_vul = read(Path(report['selection']).parent / 'candidate-pool.json')
    pool_python = read(python / 'candidate-pool.json')
    assert pool_vul['grammar'] == pool_python['grammar']
    assert [candidate_identity(r) for r in pool_vul['candidates']] == [candidate_identity(r) for r in pool_python['candidates']]
    assert selected_vul['rtl_sha256'] == selected_python['rtl_sha256']
    assert selected_vul['prediction'] == selected_python['prediction']
    assert selected_vul['selected_candidate']['placement'] == selected_python['selected_candidate']['placement']
    assert selected_vul['search_grammar'] == selected_python['search_grammar']
    simulation_time = command([vul / 'run.sh'], folder / 'simulation.log')
    assert f"AUTOPIPE {spec['case'].upper()} PASS" in (folder / 'simulation.log').read_text()
    row = dict(**spec, L=report['L'], candidate_count=selected_vul['candidate_count'],
        search_grammar=selected_vul['search_grammar'], selected_grammar=selected_vul['selected_candidate']['grammar'],
        vul_time_s=vul_time, python_time_s=python_time, simulation_time_s=simulation_time,
        identical_candidate_pool=True, identical_selected_RTL=True, identical_prediction=True,
        simulation='passed', normalized_RTL_sha256=normalized_rtl(selected_vul['rtl']),
        graph_placement_sha256=fingerprint(selected_vul), predicted_period_ps=selected_vul['prediction']['critical_required_ps'],
        predicted_area_um2=selected_vul['prediction']['total_area_um2'], selection=report['selection'])
    old = next((b for b in baselines if b['case'] == spec['case'] and b['platform'] == spec['platform'] and b['period_ps'] == spec['period']), None)
    if old:
        prior = read(old['selection'])
        row['before'] = dict(selected_grammar=prior['selected_candidate']['grammar'], candidate_count=prior['candidate_count'],
            normalized_RTL_sha256=normalized_rtl(prior['rtl']), graph_placement_sha256=fingerprint(prior))
        row['same_as_before'] = row['normalized_RTL_sha256'] == row['before']['normalized_RTL_sha256']
        row['same_graph_and_placement_as_before'] = row['graph_placement_sha256'] == row['before']['graph_placement_sha256']
    (folder / 'comparison.json').write_text(json.dumps(row, ensure_ascii=False, indent=2) + '\n')
    return row


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--baseline-json', type=Path)
    parser.add_argument('--jobs', type=int, choices=range(1, 5), default=1)
    parser.add_argument('--cases', nargs='+', choices=[c['id'] for c in CASES])
    args = parser.parse_args()
    temporary = tempfile.TemporaryDirectory(prefix='vul-grammar-parity-') if args.out is None else None
    base = Path(temporary.name) if temporary else args.out.resolve()
    if temporary is None:
        base.mkdir(parents=True, exist_ok=False)
    baselines = read(args.baseline_json) if args.baseline_json else []
    specs = [c for c in CASES if not args.cases or c['id'] in args.cases]
    results, errors = [], []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        pending = {executor.submit(check, c, base, baselines): c['id'] for c in specs}
        for future in as_completed(pending):
            try:
                row = future.result()
                results.append(row)
                print(f"PASS {row['id']}: pool={row['candidate_count']} selected={row['selected_grammar']} "
                      f"Python/VUL RTL identical, simulation passed; old RTL same={row.get('same_as_before')}", flush=True)
            except Exception as error:
                errors.append(dict(case=pending[future], error=str(error)))
                print(f"FAIL {pending[future]}: {error}", flush=True)
    (base / 'results.json').write_text(json.dumps(dict(results=results, errors=errors), ensure_ascii=False, indent=2) + '\n')
    if errors:
        raise SystemExit(1)
    if temporary:
        temporary.cleanup()


if __name__ == '__main__':
    main()
