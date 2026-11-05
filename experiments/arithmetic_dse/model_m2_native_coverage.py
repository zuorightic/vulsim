"""Public VUL to native D coverage audit; no PPA, fitting or target qualification."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from .model_collection import sha, write

ROOT = Path(__file__).resolve().parents[2]
MODEL = ROOT/'experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json'
CASES = ('MAC_32', 'DOT2_16', 'UDR_16', 'DIVSEL_32', 'F1', 'F2', 'H_M_32', 'H_D_32', 'H_F1')


def read(path):
    return json.loads(Path(path).read_text())


def collect(sources, out, tool):
    out.mkdir(parents=True, exist_ok=False)
    records = []
    for name in CASES:
        source = sources/name
        local = out/'source'/name
        local.mkdir(parents=True)
        files = {}
        for filename in ('Top.vul', 'header.uh', 'Main.utb'):
            shutil.copyfile(source/filename, local/filename)
            files[filename] = sha(local/filename)
        request = read(source/'request.json')
        request.update(target_platform='asap7',
            platform_profile=str(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json'),
            platform_profile_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json'),
            cost_mode='backend-model', fixed_cost_table='', fixed_cost_table_sha256='',
            model_bundle=str(MODEL), model_bundle_sha256=sha(MODEL),
            candidate_policy='mul-candidates-v1', target_period_ps=1500)
        write(local/'request.json', request)
        command = [str(tool), '-m', str(local/'Main.utb'), '-f', '-o', str(out/'generated'/name),
                   '--arithmetic-request', str(local/'request.json')]
        result = subprocess.run(command, cwd=ROOT, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=120)
        (out/(name+'.log')).write_text(result.stdout)
        reports = sorted((out/'generated'/name).rglob('*.arithmetic.json'))
        if len(reports) != 1:
            raise ValueError(f'{name}: expected one persisted native D report, found {len(reports)}')
        diagnostic = read(reports[0])
        selection = diagnostic.get('selection', {})
        if (result.returncode == 0 or diagnostic.get('failure_code') != 'cost_uncovered'
            or selection.get('candidate_PPA_calls') != 0 or not selection.get('candidates')
            or selection.get('formal_D_selection')):
            raise ValueError(f'{name}: missing/incorrect qualification rejection: {result.stdout[-1200:]}')
        if any(c.get('failure_code') != 'cost_uncovered' for c in selection['candidates']):
            raise ValueError(f'{name}: unexpected candidate outcome')
        write(out/(name+'.D.json'), diagnostic)
        records.append({'case': name, 'status': 'cost_uncovered', 'L': request['L'], 'II': request['II'],
            'source_sha256': files, 'request_sha256': sha(local/'request.json'), 'command': command,
            'exit_code': result.returncode, 'report': name+'.D.json', 'report_sha256': sha(out/(name+'.D.json')),
            'evaluated_structures': selection['evaluated_structures'],
            'candidate_order': [c['id'] for c in selection['candidates']],
            'failure_reason': diagnostic['failure_reason']})
        print(json.dumps({'case': name, 'status': 'cost_uncovered',
                          'candidates': selection['evaluated_structures']}), flush=True)
    write(out/'coverage.json', {'version': 'asap7-m2-native-D-coverage-v1',
        'status': 'audit_complete', 'model_sha256': sha(MODEL), 'compiler_sha256': sha(tool),
        'cases': records, 'PPA_calls': 0, 'full_D_ready': False, 'formal_target_qualification': False,
        'target_role': '1500ps exact-model diagnostic only; formal nine-case targets remain to be qualified',
        'scope': 'actual common public VUL PIPELINE -> native request/factory -> ordered D attempts; compilation support remains uncovered; not 36 final records'})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, default=ROOT/'build/step6-integration-20261031/vul-v5')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--tool', type=Path, default=ROOT/'build/vulrtlgen')
    args = parser.parse_args()
    collect(args.sources.resolve(), args.out.resolve(), args.tool.resolve())


if __name__ == '__main__':
    main()
