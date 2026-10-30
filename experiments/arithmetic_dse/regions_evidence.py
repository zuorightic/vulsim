"""Verify current and historical step4 evidence without build artifacts or EDA."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify(root=ROOT):
    root = Path(root)
    freeze = json.loads((root/'experiments/arithmetic/arithmetic_regions_freeze_v2.json').read_text())

    def check(relative, expected):
        if hashlib.sha256((root/relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f'SHA-256 mismatch: {relative}')

    for relative, expected in freeze['files_sha256'].items():
        from .freeze_history import source_location
        path=source_location(root,'experiments/arithmetic/arithmetic_regions_freeze_v2.json',relative,expected)
        check(str(path.relative_to(root)), expected)
    for relative, expected in freeze['evidence_sha256'].items():
        check(relative, expected)
    parent_info = freeze['supersedes']
    check(parent_info['path'], parent_info['sha256'])
    parent = json.loads((root/parent_info['path']).read_text())
    for relative, expected in parent['files_sha256'].items():
        check(str(Path(freeze['previous_source_snapshot'])/relative), expected)
    for relative, expected in parent['evidence_sha256'].items():
        check(relative, expected)
    for key in ('BC_precondition', 'backend_precondition'):
        check(freeze[key]['path'], freeze[key]['sha256'])
    bc = json.loads((root/freeze['BC_precondition']['path']).read_text())
    for relative, expected in bc['files_sha256'].items():
        from .freeze_history import source_location
        path=source_location(root,freeze['BC_precondition']['path'],relative,expected)
        check(str(path.relative_to(root)), expected)

    def artifacts(report, directory):
        for name, expected in report['artifacts_sha256'].items():
            path = directory/(name if name == 'regions.txt' else name+'.gz')
            data = path.read_bytes() if name == 'regions.txt' else gzip.decompress(path.read_bytes())
            if hashlib.sha256(data).hexdigest() != expected:
                raise ValueError(f'Archived artifact differs from regression: {name}')

    historical = root/'experiments/arithmetic/evidence/step4'
    artifacts(json.loads((historical/'regression.json').read_text()), historical)
    evidence = root/freeze['evidence_directory']
    summary = json.loads((evidence/'acceptance.json').read_text())
    if summary['status'] != 'passed' or summary['legal_FP_cuts'] != []:
        raise ValueError('step4 acceptance or atomicity policy mismatch')
    scenarios = {'absent-disabled':(False,False), 'present-disabled':(False,True),
                 'present-enabled':(True,True)}
    matrix = json.loads((evidence/'mode_matrix.json').read_text())
    if {row['scenario'] for row in matrix} != set(scenarios) or len(matrix) != 3:
        raise ValueError('incomplete CIRCT mode evidence')
    for name, (enabled, available) in scenarios.items():
        report = json.loads((evidence/(name+'.json')).read_text())
        artifacts(report, evidence)
        if (set(report['cases']) != {'single','serial','parallel','shared','identical','constant'}
                or report['host_vectors'] != 20484
                or report['RTL_combinational_output_checks'] != 245808
                or report['RTL_valid_pipeline_output_checks'] != 173520
                or report['RTL_reset_output_checks'] != 960
                or report['region_checks'] != 'PASS arithmetic regions checks=55'
                or any(report['physical_calls'].values())
                or any(c['exit_code'] for c in report['commands'])):
            raise ValueError(f'incomplete functional evidence: {name}')
        policy = report['CIRCT']
        if (policy['enabled'] != enabled or policy['tool_available'] != available
                or policy['status'] != ('executed' if enabled else 'skipped')
                or policy['reason'] != (None if enabled else 'VUL_REGRESSION_CIRCT=0')):
            raise ValueError(f'incorrect CIRCT policy: {name}')
        paths = {p['backend']:p for p in report['VUL_end_to_end']}
        if len(report['VUL_end_to_end']) != 3 or set(paths) != {'sim','native','circt'}:
            raise ValueError('missing end-to-end path status')
        for backend, result in paths.items():
            skipped = backend == 'circt' and not enabled
            if result['status'] != ('skipped' if skipped else 'passed'):
                raise ValueError('executed/skipped path mismatch')
            if skipped and result['reason'] != 'VUL_REGRESSION_CIRCT=0':
                raise ValueError('missing CIRCT skip reason')
        units = report['pipeline_unit_tests']
        if ({r['test'] for r in units} != {'pipeline-test','pipeline-reset-test','pipeline-valid-test'}
                or any(r['status'] != 'passed' for r in units)
                or (not enabled and any('SKIP CIRCT' not in r['output'] for r in units))):
            raise ValueError('incomplete native unit tests or skip evidence')
        regions = report['arithmetic_regions']
        if len(regions) != 10 or len({r['id'] for r in regions}) != 10:
            raise ValueError('incomplete region identity records')
        for region in regions:
            if (region['sharing_policy'] != 'semantic-marker-and-isolated-BEOPT-v1'
                    or region['template_version'] != 'softfloat3d-bitvector-mul-v1'
                    or region['semantics'] != 'binary32-rne-tininess-after-canonicalNaN-v1'
                    or region['legal_cut_count'] != 0):
                raise ValueError('region policy or template identity mismatch')
        row = next(row for row in matrix if row['scenario'] == name)
        if (row['exit_code'] or row['CIRCT_enabled'] != enabled
                or bool(row['tool_on_PATH']) != available
                or (row['observed_CIRCT_invocations'] <= 0 if enabled else row['observed_CIRCT_invocations'] != 0)):
            raise ValueError('CIRCT invocation observation mismatch')
    missing = json.loads((evidence/'missing_tool.json').read_text())
    if not missing['exit_code'] or 'CIRCT checks are enabled but circt-opt is not on PATH' not in missing['stderr']:
        raise ValueError('missing enabled/no-tool diagnostic')
    direct = json.loads((evidence/'direct_disabled.json').read_text())
    if len(direct) != 3 or any(r['exit_code'] or 'SKIP CIRCT' not in r['stdout'] for r in direct):
        raise ValueError('direct C++ disable policy failed')
    resources = json.loads((evidence/'resources.json').read_text())
    if (resources['cumulative_backend_usage']['pending'] or resources['caps_increased']
            or any(resources['new_backend_calls'].values())):
        raise ValueError('unsettled budget reservation, altered caps or unexpected PPA calls')
    return {'status':'passed', 'freeze':freeze['version'],
            'source_files':len(freeze['files_sha256']),
            'evidence_files':len(freeze['evidence_sha256']),
            'historical_source_files':len(parent['files_sha256']),
            'historical_evidence_files':len(parent['evidence_sha256']),
            'step4_acceptance':summary['acceptance'], 'region_checks':55,
            'CIRCT_modes_verified':list(scenarios),
            'legal_FP_cuts':[], 'new_physical_calls':resources['new_backend_calls'],
            'requires_build_directory':False, 'requires_EDA_tools':False,
            'full_budget_status':resources['full_experiment_budget_status']}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
