"""Validate the portable backend freeze without build artifacts or EDA tools."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def verify_backend_evidence(root=ROOT, verify_external=False):
    root = Path(root)
    freeze_path = root/'experiments/arithmetic/backend_freeze_v4.json'
    freeze = json.loads(freeze_path.read_text())
    def verify(path, expected):
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError(f'SHA-256 mismatch: {path}')
    for relative, expected in freeze['files_sha256'].items():
        from .freeze_history import source_location
        verify(source_location(root,'experiments/arithmetic/backend_freeze_v4.json',relative,expected), expected)
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
    # Current closure evidence adds a controlled physical study and revises the
    # future collection design. Historical v3 six-point data remains immutable.
    closure = root/'experiments/arithmetic/evidence/step3_closure'
    from .timing_evidence import critical_path, master_inventory
    from .characterization import mapped_netlist_hash
    from .budget import required_data_plan
    import gzip
    paths = json.loads((closure/'critical_path/summary.json').read_text())
    for stage,path in paths['stages'].items():
        extracted = critical_path((closure/f'critical_path/vulsim_{stage}_paths_max.rpt').read_text())
        if extracted != path:
            raise ValueError('archived critical-path extraction mismatch')
    if paths['mapper_STA_error_ratio'] is not None or paths['mapper_STA_path_equivalence_proven']:
        raise ValueError('unproven ABC/STA path equivalence')
    connectivity = paths['connectivity_evidence']
    verify(closure/'critical_path/probe.sv',connectivity['input_RTL_sha256'])
    verify(closure/'critical_path/mapped_synth.v.gz',connectivity['mapped_synth_gzip_sha256'])
    rtl_lines = (closure/'critical_path/probe.sv').read_text().splitlines()
    for assignment in connectivity['RTL_assignments']:
        if assignment['text'] != rtl_lines[assignment['line']-1].split('// decl:',1)[0].strip():
            raise ValueError('operand/product RTL connectivity excerpt mismatch')
    netlist = gzip.decompress((closure/'critical_path/mapped_synth.v.gz').read_bytes()).decode()
    for instance in connectivity['instance_declarations']:
        if instance['mapped_instance'] not in netlist:
            raise ValueError('critical path register absent from mapped netlist')
    physical = json.loads((closure/'physical_comparison.json').read_text())
    if physical['status'] != 'completed' or not physical['same_synth_starting_netlist']:
        raise ValueError('two-point physical comparison incomplete')
    if {point['sdc_period_ps'] for point in physical['points']} != {500,2000}:
        raise ValueError('unexpected physical study targets')
    context_pairs = []
    synth_hashes = set()
    common_sdc_hashes = set()
    for point in physical['points']:
        target = point['sdc_period_ps']
        directory = closure/f'sdc-{target}'
        manifest = json.loads((directory/'manifest.json').read_text())
        context = manifest['mapping_context']
        context_hash = hashlib.sha256(json.dumps(context,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        if context_hash != manifest['mapping_context_sha256']:
            raise ValueError('physical context hash mismatch')
        if context['abc_target_ps'] != 1500 or context['sdc_period_ps'] != target or context['io_delay_max_ps'] != 300:
            raise ValueError('uncontrolled ABC/SDC/IO settings')
        context_pairs.append({k:v for k,v in context.items() if k != 'sdc_period_ps'})
        synth_hashes.add(manifest['metrics'][0]['mapped_netlist_sha256'])
        synth_netlist = gzip.decompress((directory/'1_2_yosys.v.gz').read_bytes()).decode()
        if mapped_netlist_hash(synth_netlist) != manifest['metrics'][0]['mapped_netlist_sha256']:
            raise ValueError('actual synthesis netlist does not match shared starting identity')
        common_sdc_hashes.add(hashlib.sha256((directory/'vulsim_common1500.sdc').read_bytes()).hexdigest())
        if json.loads((directory/'metrics.json').read_text())[-1] != point['own_SDC_metrics']:
            raise ValueError('physical own-SDC metrics mismatch')
        if json.loads((directory/'common1500.metrics.json').read_text()) != point['common_SDC_metrics']:
            raise ValueError('physical common-SDC metrics mismatch')
        if master_inventory((directory/'vulsim_grt_cells.tsv').read_text()) != point['master_inventory']:
            raise ValueError('physical master inventory mismatch')
        for tag,key in [('grt','own_path'),('common1500','common_path')]:
            if critical_path((directory/f'vulsim_{tag}_paths_max.rpt').read_text()) != point[key]:
                raise ValueError('physical path comparison mismatch')
        own_net = gzip.decompress((directory/'vulsim_grt.v.gz').read_bytes())
        common_net = gzip.decompress((directory/'vulsim_common1500.v.gz').read_bytes())
        if (own_net != common_net or hashlib.sha256(own_net).hexdigest() != point['physical_netlist_sha256']
            or (directory/'vulsim_grt_instances.tsv').read_bytes() != (directory/'vulsim_common1500_instances.tsv').read_bytes()):
            raise ValueError('STA modified physical implementation')
        verify(directory/'vulsim_grt_instances.tsv',point['placement_and_master_sha256'])
    if len(synth_hashes) != 1 or len(common_sdc_hashes) != 1 or context_pairs[0] != context_pairs[1]:
        raise ValueError('starting-point/control context mismatch')
    current_summary = json.loads((closure/'review_summary.json').read_text())
    current_resources = json.loads((root/freeze['evaluation_policy']).read_text())['resources']
    old_resources = json.loads((root/'experiments/arithmetic_dse/configs/backend_policy_v3.json').read_text())['resources']
    if current_resources != old_resources:
        raise ValueError('resource ceilings changed in closure revision')
    checkpoint = json.loads((closure/'usage_checkpoint.json').read_text())
    actual = usage(checkpoint['entries'])
    if actual != current_summary['cumulative_usage'] or actual['pending']:
        raise ValueError('current cumulative usage mismatch or pending reservations')
    old_entries = json.loads((new_root/'usage_checkpoint.json').read_text())['entries']
    if checkpoint['entries'][:len(old_entries)] != old_entries:
        raise ValueError('historical charges changed')
    extra = checkpoint['entries'][len(old_entries):]
    if {s:sum(e['stage'] == s for e in extra) for s in ['synth','grt','final']} != {'synth':2,'grt':2,'final':0}:
        raise ValueError('unexpected incremental physical calls')
    cpu_index = {item['id']:item for item in json.loads((closure/'CPU_report_index.json').read_text())}
    for entry in extra:
        item = cpu_index[entry['id']]
        verify(root/item['path'],item['sha256'])
        if abs(cpu_seconds(root/item['path'])-entry['CPU_time_s']) > 1e-8:
            raise ValueError('new command CPU charge mismatch')
    report = json.loads((closure/'budget_check.json').read_text())
    declared = json.loads((root/'experiments/arithmetic_dse/configs/budget_plan_v2.json').read_text())
    expected_plan = required_data_plan(case_manifest()['calibration_only'],None,historical=actual,
        reserves=declared['reserves'],actual_collection_manifest_frozen=False)
    if report['plan'] != expected_plan or report['status'] != 'blocked' or current_summary['status'] != 'passed':
        raise ValueError('updated budget/acceptance summary mismatch')
    return {'status':'passed', 'freeze':freeze['version'],
            'current_source_files':len(freeze['files_sha256']),
            'historical_source_files':historical_count,
            'unchanged_BC_files':len(bc['files_sha256']),
            'portable_evidence_files_current_revision':len(index['files']),
            'cumulative_calls':{key:actual[key] for key in ['synth','grt','final']},
            'step3_acceptance':current_summary['step3_acceptance'],
            'physical_control_response':physical['response'],
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
