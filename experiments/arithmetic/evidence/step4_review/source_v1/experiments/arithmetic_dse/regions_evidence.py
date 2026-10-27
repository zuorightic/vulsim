"""Verify step4 source/evidence hashes with no build directory or EDA tools."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify(root=ROOT):
    root = Path(root)
    freeze = json.loads((root/'experiments/arithmetic/arithmetic_regions_freeze_v1.json').read_text())
    def check(relative, expected):
        if hashlib.sha256((root/relative).read_bytes()).hexdigest() != expected:
            raise ValueError(f'SHA-256 mismatch: {relative}')
    for relative, expected in freeze['files_sha256'].items():
        check(relative, expected)
    for relative, expected in freeze['evidence_sha256'].items():
        check(relative, expected)
    for key in ('BC_precondition', 'backend_precondition'):
        check(freeze[key]['path'], freeze[key]['sha256'])
    bc = json.loads((root/freeze['BC_precondition']['path']).read_text())
    for relative, expected in bc['files_sha256'].items():
        check(relative, expected)

    evidence = root/'experiments/arithmetic/evidence/step4'
    report = json.loads((evidence/'regression.json').read_text())
    summary = json.loads((evidence/'acceptance.json').read_text())
    for name, expected in report['artifacts_sha256'].items():
        data = (evidence/name).read_bytes() if name == 'regions.txt' else gzip.decompress((evidence/(name+'.gz')).read_bytes())
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Archived artifact differs from regression: {name}')

    if summary['status'] != 'passed' or summary['legal_FP_cuts'] != []:
        raise ValueError('step4 acceptance or atomicity policy mismatch')
    if (set(report['cases']) != {'single','serial','parallel','shared','identical','constant'}
            or report['host_vectors'] != 20484
            or report['RTL_combinational_output_checks'] != 245808
            or report['RTL_valid_pipeline_output_checks'] != 173520
            or report['RTL_reset_output_checks'] != 960
            or report['region_checks'] != 'PASS arithmetic regions checks=51'
            or len(report['VUL_end_to_end']) != 3
            or any(report['physical_calls'].values())):
        raise ValueError('incomplete functional evidence')
    resources = json.loads((evidence/'resources.json').read_text())
    if resources['cumulative_backend_usage']['pending'] or resources['caps_increased']:
        raise ValueError('unsettled budget reservation or altered caps')
    return {'status':'passed', 'freeze':freeze['version'],
            'source_files':len(freeze['files_sha256']),
            'evidence_files':len(freeze['evidence_sha256']),
            'step4_acceptance':summary['acceptance'],
            'legal_FP_cuts':[], 'new_physical_calls':report['physical_calls'],
            'requires_build_directory':False, 'requires_EDA_tools':False,
            'full_budget_status':resources['full_experiment_budget_status']}


if __name__ == '__main__':
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
