"""Validate the portable backend freeze without build artifacts or EDA tools."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_backend_evidence(root=ROOT, verify_external=False):
    root = Path(root)
    freeze_path = root/'experiments/arithmetic/backend_freeze_v3.json'
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
    historical_count = 0
    child = freeze
    while True:
        for relative, expected in parent['files_sha256'].items():
            verify(root/child['previous_source_snapshot']/relative, expected)
            historical_count += 1
        # v1 raw paths were local-only. Its portable source snapshot is checked
        # above; subsequent revisions must preserve all portable evidence too.
        if 'evidence_index' in parent:
            for relative, expected in parent['validation_evidence'].items():
                verify(root/relative, expected)
            for item in json.loads((root/parent['evidence_index']).read_text())['files']:
                verify(root/item['path'], item['sha256'])
        if 'supersedes' not in parent:
            break
        child = parent
        parent_info = parent['supersedes']
        verify(root/parent_info['path'], parent_info['sha256'])
        parent = json.loads((root/parent_info['path']).read_text())
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
    new_root = root/'experiments/arithmetic/evidence/step3_budget'
    summary = json.loads((new_root/'review_summary.json').read_text())
    if summary['status'] != 'passed':
        raise ValueError('budget review evidence is not passed')
    probes = json.loads((new_root/'target_probes.json').read_text())
    if {p['abc_target_ps'] for p in probes['points']} != {500,800,1000,1250,1500,2000}:
        raise ValueError('missing six-point probe')
    for point in probes['points']:
        context = point['mapping_context']
        if hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':')).encode()).hexdigest() != point['mapping_context_sha256']:
            raise ValueError('six-point context mismatch')
        if context['abc_target_ps'] != point['abc_target_ps'] or context['sdc_period_ps'] != point['abc_target_ps']:
            raise ValueError('ABC/SDC target mismatch')
        script = new_root/f'bound-{int(point["abc_target_ps"])}/abc_speed.script'
        verify(script,context['abc_script_sha256'])
        if context['abc_target_binding'] != 'explicit_D_on_nf_upsize_dnsize_in_rendered_script':
            raise ValueError('unbound ABC target')
        for line in script.read_text().splitlines():
            words = line.split()
            if words and words[0] in ['&nf','upsize','dnsize']:
                if '-D' not in words or float(words[words.index('-D')+1]) != point['abc_target_ps']:
                    raise ValueError('ABC mapping command missing numeric target')
        abc_log = (new_root/f'bound-{int(point["abc_target_ps"])}/abc-target-commands.log').read_text()
        if (f'target delay (' not in abc_log or
            f'target delay ({point["abc_target_ps"]:.2f} ps)' not in abc_log):
            raise ValueError('ABC execution evidence does not confirm rendered target')
    from .budget import usage, plan_cost, planning_status, cpu_seconds
    from .characterization import sensitivity_observation
    from .reference import case_manifest
    checkpoint = json.loads((new_root/'usage_checkpoint.json').read_text())
    actual = usage(checkpoint['entries'])
    if actual != summary['cumulative_usage'] or actual['pending']:
        raise ValueError('checkpoint usage mismatch or unfinished reservation')
    if len({entry['id'] for entry in checkpoint['entries']}) != len(checkpoint['entries']):
        raise ValueError('duplicated budget charges')
    cpu_reports = {item['id']:item for item in json.loads((new_root/'CPU_report_index.json').read_text())}
    if len(cpu_reports) != len(checkpoint['entries']):
        raise ValueError('incomplete CPU evidence')
    for entry in checkpoint['entries']:
        item = cpu_reports[entry['id']]
        verify(root/item['path'], item['sha256'])
        if abs(cpu_seconds(root/item['path'])-entry['CPU_time_s']) > 1e-8:
            raise ValueError('CPU ledger does not match GNU time')
        if entry['kind'] == 'historical':
            provenance = entry['provenance']
            path = new_root/'historical_manifests'/provenance['manifest']
            verify(path,provenance['manifest_sha256'])
            command = next(c for c in json.loads(path.read_text())['commands']
                           if c['command'] == provenance['command'])
            if command['walltime_s'] != entry['walltime_s']:
                raise ValueError('historical walltime ledger mismatch')
    if sensitivity_observation(probes['points']) != probes['observation']:
        raise ValueError('incorrect sensitivity observation')
    report = json.loads((new_root/'budget_check.json').read_text())
    config = json.loads((root/'experiments/arithmetic_dse/configs/characterization_v2.json').read_text())
    declared = json.loads((root/'experiments/arithmetic_dse/configs/budget_plan_v1.json').read_text())
    plan = plan_cost({name:config['initial_abc_target_points_ps'] for name in case_manifest()['calibration_only']},
                     None, historical=actual, targets_frozen=False, **declared['reserves'])
    resources = json.loads((root/freeze['evaluation_policy']).read_text())['resources']
    if report['plan'] != plan or report['status'] != planning_status(plan,resources)['status']:
        raise ValueError('budget forecast mismatch')
    return {'status':'passed', 'freeze':freeze['version'],
            'current_source_files':len(freeze['files_sha256']),
            'historical_source_files':historical_count,
            'unchanged_BC_files':len(bc['files_sha256']),
            'portable_evidence_files_current_revision':len(index['files']),
            'cumulative_calls':{key:actual[key] for key in ['synth','grt','final']},
            'full_experiment_budget_status':report['status'],
            'requires_build_directory':False, 'external_verification':verify_external}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--verify-external', action='store_true', help='also require the original local EDA installations')
    args = parser.parse_args()
    print(json.dumps(verify_backend_evidence(args.root, args.verify_external), indent=2))


if __name__ == '__main__':
    main()
