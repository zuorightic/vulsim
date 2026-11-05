"""Small portable evidence for native published-component integration and D gaps."""
import argparse
import json
import math
from pathlib import Path
import shutil
import tempfile

from .model_collection import sha, write
from .model_m2_mux_static_features import predict

ROOT = Path(__file__).resolve().parents[2]
RELEASE = ROOT/'experiments/arithmetic/evidence/step7_m2_mux_static_v1'


def read(path):
    return json.loads(Path(path).read_text())


def package(work, out):
    checks = work/'checks-v6'
    parity = read(checks/'parity.json')
    if parity['status'] != 'passed' or parity['native_queries'] != 436 or parity['PPA_calls']:
        raise ValueError('successful final native parity required')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copytree(checks/'native', out/'native')
    shutil.copytree(work/'public-nine-v1/source', out/'public-source')
    (out/'public-nine').mkdir()
    for p in sorted((work/'public-nine-v1').glob('*')):
        if p.is_file():
            shutil.copyfile(p, out/'public-nine'/p.name)
    for name in ('parity.json', 'commands.json', 'resource-summary.json'):
        shutil.copyfile(checks/name, out/name)
    for name in ('ordinary-models.log', 'pipeline-test.log', 'pipeline-reset-test.log', 'pipeline-valid-test.log'):
        shutil.copyfile(checks/name, out/name)
    shutil.copyfile(RELEASE/'asap7-primitives.json', out/'model.json')
    sources = [ROOT/'rtlzz'/name for name in (
        'src/arithmetic_request.cpp', 'src/arithmetic_request.hpp', 'src/backend/arithmetic_core.hpp',
        'src/backend/arithmetic_model.cpp', 'src/backend/arithmetic_selection.cpp', 'src/backend/pipeline.cpp',
        'src/backend/arithmetic_stage.cpp', 'src/backend/arithmetic_primitives.hpp',
        'src/backend/arithmetic_primitives.cpp', 'src/backend/arithmetic_mux_context.hpp',
        'testv2/arithmetic_published_primitives_test.cpp')]
    sources += [ROOT/'regression/arithmetic_published_primitives.py', Path(__file__),
                Path(__file__).with_name('model_m2_native_coverage.py')]
    sources += [Path(__file__).with_name(name) for name in ('model_features.py',
                'model_m2_mux_static_features.py', 'model_m2_fit_v4.py', 'model_m2_fit_v3.py',
                'model_m2_fit_v2.py')]
    hashes = {}
    for p in sources:
        name = p.relative_to(ROOT)
        dst = out/'source'/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, dst)
        hashes[str(name)] = sha(p)
    write(out/'capabilities.json', {
        'published_model_native_factory': True, 'real_stage_and_capture_component_queries': True,
        'placement_refresh_checked': True, 'public_VUL_D_request_and_candidate_diagnostics': True,
        'native_Python_queries': 436, 'old_four_platform_native_checks': 250,
        'public_cases_audited': 9, 'D_candidate_attempts': 21, 'PPA_calls': 0,
        'state_boundary_composition_qualification': False, 'real_interval_successor_qualification': False,
        'formal_nine_case_targets_qualified': False, 'full_D_ready': False,
        'nine_case_36_records_complete': False,
        'limitation': 'component integration and coverage audit; complete D selection and its RTL cycle closure still require missing qualified models'})
    files = {str(p.relative_to(out)): sha(p) for p in sorted(out.rglob('*')) if p.is_file()}
    write(out/'index.json', {'version': 'asap7-m2-native-integration-evidence-v1', 'files': files,
        'source_sha256': hashes, 'model_sha256': sha(out/'model.json'),
        'parent_release_index_sha256': sha(RELEASE/'index.json'), 'verifier_sha256': sha(__file__),
        'scope': 'production component consumer, complete-placement query ABI, exact numeric parity and nine public VUL D coverage diagnostics; no new fitting or PPA',
        'full_D_ready': False})
    print(json.dumps({'status': 'packaged', 'files': len(files),
                      'bytes': sum(p.stat().st_size for p in out.rglob('*') if p.is_file())}), flush=True)


def verify(out, external=False):
    from regression.arithmetic_published_primitives import verify as verify_native
    index = read(out/'index.json')
    if sha(__file__) != index['verifier_sha256']:
        raise ValueError('changed integration verifier')
    for name, h in index['source_sha256'].items():
        if name.endswith('.py') and sha(ROOT/name) != h:
            raise ValueError('changed numerical replay source: '+name)
    for name, h in index['files'].items():
        if sha(out/name) != h:
            raise ValueError('changed native integration evidence: '+name)
    if sha(out/'model.json') != index['model_sha256']:
        raise ValueError('changed published parameters')
    with tempfile.TemporaryDirectory() as td:
        temp = Path(td)
        shutil.copytree(out/'native', temp/'native')
        verify_native(temp, out/'model.json')
        if read(temp/'parity.json') != read(out/'parity.json'):
            raise ValueError('native parity does not reproduce')
    bundle = read(out/'model.json')
    actual = read(out/'native/actual-C-placement-components.json')
    if (actual['covered_components'] != 2 or actual['uncovered_components'] or actual['pipeline_qualified']
        or actual['candidate_PPA_calls'] or actual['model_bundle_sha256'] != index['model_sha256']):
        raise ValueError('actual PipelineV2 component binding claim differs')
    for row in actual['nodes']:
        f = row['features']
        if f['context_dynamic_mux_count'] != 2 or f['fanout'] != 1 or row['operation'] != 'mux':
            raise ValueError('actual-stage Mux context changed')
        r = {'features': f, 'static_features': f, 'period_ps': f['sdc_period_ps'],
             'spec': {'lhs_width': int(f['lhs_width']), 'rhs_width': 0, 'result_width': int(f['result_width'])}}
        for q, key in (('delay', 'delay_ps'), ('area', 'comb_area_um2')):
            value = predict(bundle['stages']['grt']['operations']['mux'][q], r, q)
            if not math.isclose(value, row[key], rel_tol=1e-9, abs_tol=1e-8):
                raise ValueError('actual PipelineV2 stage query price differs')
    coverage = read(out/'public-nine/coverage.json')
    if (len(coverage['cases']) != 9 or coverage['PPA_calls'] or coverage['full_D_ready']
        or coverage['formal_target_qualification'] or coverage['model_sha256'] != index['model_sha256']):
        raise ValueError('wrong public VUL coverage scope')
    attempts = 0
    for case in coverage['cases']:
        diagnostic = read(out/'public-nine'/case['report'])
        if sha(out/'public-nine'/case['report']) != case['report_sha256']:
            raise ValueError('public D report identity changed')
        for name, h in case['source_sha256'].items():
            if sha(out/'public-source'/case['case']/name) != h:
                raise ValueError('public source identity changed')
        selection = diagnostic['selection']
        if (diagnostic['failure_code'] != 'cost_uncovered' or selection['candidate_PPA_calls']
            or selection['formal_D_selection'] or selection['candidate_model_coverage_complete']):
            raise ValueError('coverage failure reclassified as success/infeasibility')
        if [c['id'] for c in selection['candidates']] != case['candidate_order']:
            raise ValueError('D ordered policy changed')
        attempts += len(selection['candidates'])
    if attempts != 21:
        raise ValueError('incomplete ordered candidate evidence')
    for name, marker in (('ordinary-models.log', 'Arithmetic model native checks: 250'),
                         ('pipeline-test.log', 'pipeline tests passed'),
                         ('pipeline-reset-test.log', 'pipeline reset API tests passed'),
                         ('pipeline-valid-test.log', 'pipeline valid API and IR tests passed')):
        if marker not in (out/name).read_text():
            raise ValueError('missing successful existing regression: '+name)
    if external:
        for name, h in index['source_sha256'].items():
            if sha(ROOT/name) != h:
                raise ValueError('changed production source: '+name)
        if sha(RELEASE/'asap7-primitives.json') != index['model_sha256'] or sha(RELEASE/'index.json') != index['parent_release_index_sha256']:
            raise ValueError('changed parent release')
    print(json.dumps({'status': 'verified', 'native_queries': 436, 'actual_pipeline_component_queries': 2,
                      'public_cases': 9, 'ordered_D_attempts': attempts, 'PPA_calls': 0,
                      'full_D_ready': False, 'external': external}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('package', 'verify'))
    parser.add_argument('--work', type=Path)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--external', action='store_true')
    args = parser.parse_args()
    if args.action == 'package':
        package(args.work.resolve(), args.out.resolve())
    else:
        verify(args.out.resolve(), args.external)


if __name__ == '__main__':
    main()
