"""Validate the portable backend freeze without build artifacts or EDA tools."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_backend_evidence(root=ROOT, verify_external=False):
    root = Path(root)
    freeze_path = root/'experiments/arithmetic/backend_freeze_v2.json'
    freeze = json.loads(freeze_path.read_text())
    def verify(path, expected):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'SHA-256 mismatch: {path}')
    for relative, expected in freeze['files_sha256'].items():
        verify(root/relative, expected)
        verify(root/freeze['validated_source_snapshot']/relative, expected)
    for relative, expected in freeze['validation_evidence'].items():
        verify(root/relative, expected)
    parent_info = freeze['supersedes']
    verify(root/parent_info['path'], parent_info['sha256'])
    parent = json.loads((root/parent_info['path']).read_text())
    for relative, expected in parent['files_sha256'].items():
        verify(root/freeze['previous_source_snapshot']/relative, expected)
    bc_info = freeze['BC_precondition']
    verify(root/bc_info['path'], bc_info['sha256'])
    bc = json.loads((root/bc_info['path']).read_text())
    for relative, expected in bc['files_sha256'].items():
        verify(root/relative, expected)
    index = json.loads((root/freeze['evidence_index']).read_text())
    for item in index['files']:
        verify(root/item['path'], item['sha256'])
    if verify_external:
        for item in freeze['libraries']:
            verify(Path(item['path']), item['sha256'])
        for item in freeze['tools'].values():
            verify(Path(item['path']), item['sha256'])
        for path, expected in freeze['external_files_sha256'].items():
            verify(Path(path), expected)
    summary = json.loads((root/'experiments/arithmetic/evidence/step3/review_summary.json').read_text())
    if summary['status'] != 'passed':
        raise ValueError('review evidence is not passed')
    points = json.loads((root/'experiments/arithmetic/evidence/step3/target_probes.json').read_text())['points']
    if {point['abc_target_ps'] for point in points} != {1000,1500,2000}:
        raise ValueError('missing target probe')
    for point in points:
        context = point['mapping_context']
        digest = hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if digest != point['mapping_context_sha256'] or context['abc_target_ps'] != point['abc_target_ps']:
            raise ValueError('target context mismatch')
    metrics = json.loads((root/'experiments/arithmetic/evidence/step3/metrics_v2.json').read_text())
    by_stage = {item['stage']:item for item in metrics}
    if (by_stage['grt']['feasibility_scope'] != 'TT_setup_only'
        or by_stage['final']['feasibility_scope'] != 'TT_setup_and_hold'
        or any(item['multi_corner_signoff'] for item in metrics)):
        raise ValueError('incorrect timing scope')
    return {'status':'passed', 'freeze':freeze['version'],
            'current_source_files':len(freeze['files_sha256']),
            'historical_source_files':len(parent['files_sha256']),
            'unchanged_BC_files':len(bc['files_sha256']),
            'portable_evidence_files':len(index['files']),
            'requires_build_directory':False, 'external_verification':verify_external}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--verify-external', action='store_true', help='also require the original local EDA installations')
    args = parser.parse_args()
    print(json.dumps(verify_backend_evidence(args.root, args.verify_external), indent=2))


if __name__ == '__main__':
    main()
