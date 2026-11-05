"""Production native prices and D coverage diagnostics for the published ASAP7 bundle.

Only declared model conditions/parameters are read. No measurement labels,
fitting, physical tools, or new qualification claims are involved.
"""
import argparse
import json
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.model_collection import sha, write
from experiments.arithmetic_dse.model_features import features as base_features, FEATURES
from experiments.arithmetic_dse.model_m2_cec import leaf
from experiments.arithmetic_dse.model_m2_mux_static_features import predict
from experiments.arithmetic_dse.model_m2_fit_v4 import predict as ordinary_predict

MODEL = ROOT/'experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json'


def read(path):
    return json.loads(Path(path).read_text())


def verify(folder, model):
    bundle = read(model)
    data = read(folder/'native/queries.json')
    if data['model_sha256'] != sha(model) or data['PPA_calls'] or data['operations'] != 12:
        raise ValueError('wrong model/query identity')
    expected_count = sum(len(m['joint_domain'])*(9 if op == 'mux' else 1)
                         for op, m in bundle['stages']['grt']['operations'].items())
    if len(data['rows']) != expected_count:
        raise ValueError('incomplete published-domain query coverage')
    operations = set()
    maximum_delta = 0.
    for row in data['rows']:
        f = row['features']
        op = row['operation']
        operations.add(op)
        base = base_features(int(f['lhs_width']), int(f['rhs_width']), int(f['result_width']),
                             1, 1500, f['sdc_period_ps'])
        expected = {k: base[k] for k in FEATURES}
        if op == 'mux':
            n, w = row['parallel_count'], int(f['lhs_width'])
            expected.update(context_operation_count=n, context_dynamic_mux_count=n,
                context_constant_mux_count=0, context_boolean_count=0,
                context_launch_bits=n*(2*w+1), context_capture_bits=n*w,
                context_result_bits=n*w, selector_fanout_bits=w)
        if f != expected:
            raise ValueError('native actual graph features disagree with independent reconstruction')
        value = {'spec': {'lhs_width': int(f['lhs_width']), 'rhs_width': int(f['rhs_width']),
                         'result_width': int(f['result_width'])},
                 'period_ps': f['sdc_period_ps'], 'features': base, 'static_features': expected}
        component = bundle['stages']['grt']['operations'][op]
        for quantity, key in (('delay', 'delay_ps'), ('area', 'comb_area_um2')):
            expected_value = (predict if op == 'mux' else ordinary_predict)(component[quantity], value, quantity)
            maximum_delta = max(maximum_delta, abs(expected_value-row[key]))
            if not math.isclose(expected_value, row[key], rel_tol=1e-9, abs_tol=1e-8):
                raise ValueError('native frozen parameter prediction differs from Python')
    if len(operations) != 12 or not data['placement_refresh_checked']:
        raise ValueError('incomplete component/context coverage')
    diagnostic = read(folder/'native/D-diagnostic.json')
    selection = diagnostic['selection']
    candidates = selection['candidates']
    if (diagnostic['failure_code'] != 'cost_uncovered' or selection['candidate_PPA_calls']
        or selection['formal_D_selection'] or len(candidates) != 3
        or [c['id'].split('/')[-1] for c in candidates] != ['original', 'half', 'quarter']
        or any(c['failure_code'] != 'cost_uncovered' for c in candidates)
        or any(c['component_coverage']['pipeline_qualified'] for c in candidates)):
        raise ValueError('D candidate failure/coverage trace was lost or misclassified')
    result = {'status': 'passed', 'model_sha256': sha(model), 'native_queries': len(data['rows']),
              'operations': sorted(operations), 'maximum_native_Python_delta': maximum_delta,
              'placement_refresh': True, 'guard_rejections': len(data['rejections']),
              'D_original_half_quarter_attempts_retained': True, 'PPA_calls': 0,
              'production_component_consumer': True, 'full_D_ready': False,
              'scope': 'native factory and real stage/capture component queries; whole pipeline still requires independent state/boundary/composition/interval qualification'}
    write(folder/'parity.json', result)
    print(json.dumps(result), flush=True)


def run(folder, build, model, skip_build, circt_bin):
    folder.mkdir(parents=True, exist_ok=False)
    ledger = Ledger()
    context = {'target_platform': 'asap7', 'admission_id': folder.name,
               'task_id': 'published-provider-regression'}
    commands = []
    with ledger.job(context):
        def execute(command, stem, timeout=300):
            record = leaf(command, folder, stem, timeout, ledger, context)
            commands.append(record)
            write(folder/'commands.json', commands)
            print(Path(record['log']).read_text()[-3500:], flush=True)
        if not skip_build:
            execute(['cmake', '-S', str(ROOT/'rtlzz'), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release'], 'configure')
            execute(['cmake', '--build', str(build), '--target', 'arithmetic-published-primitives-test',
                     'arithmetic-model-test', 'pipeline-test', 'pipeline-reset-test',
                     'pipeline-valid-test', '-j4'], 'build', 1800)
        execute([str(build/'testv2/arithmetic-published-primitives-test'), str(ROOT), str(model),
                 str(folder/'native')], 'native', 600)
        execute([sys.executable, '-B', str(Path(__file__).resolve()), 'verify', '--out', str(folder),
                 '--model', str(model)], 'independent-parity')
        execute([str(build/'testv2/arithmetic-model-test'), str(ROOT),
                 str(ROOT/'experiments/arithmetic/evidence/step7_models_v1/models'),
                 str(folder/'ordinary-regression')], 'ordinary-models', 900)
        for name in ('pipeline-test', 'pipeline-reset-test', 'pipeline-valid-test'):
            env = ['env', '--chdir='+str(ROOT/'rtlzz')]
            if circt_bin:
                env.append('PATH='+str(circt_bin)+os.pathsep+os.environ.get('PATH', ''))
            execute(env+[str(build/'testv2'/name), str(folder/name)], name, 300)
    write(folder/'resource-summary.json', ledger.summary())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'verify'))
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--model', type=Path, default=MODEL)
    parser.add_argument('--build', type=Path, default=ROOT/'build/step4-rtlzz')
    parser.add_argument('--skip-build', action='store_true')
    parser.add_argument('--circt-bin', type=Path)
    args = parser.parse_args()
    if args.action == 'verify':
        verify(args.out.resolve(), args.model.resolve())
    else:
        run(args.out.resolve(), args.build.resolve(), args.model.resolve(), args.skip_build,
            args.circt_bin.resolve() if args.circt_bin else None)


if __name__ == '__main__':
    main()
