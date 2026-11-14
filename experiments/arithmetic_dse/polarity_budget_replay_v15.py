"""Replay sealed v15 work/area and measured branch-budget evidence, without EDA."""
import argparse
import ast
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

from . import phase_cut_cover_v15 as phase
from . import prospective_cut_cover_v14 as base
from . import flow_structure_features as circuits
from . import control_branch_budget_v15 as budget
from . import transition_incidence_features_v10 as geometry
from .cut_cover_replay_v14 import same


def load(path):
    data = Path(path).read_bytes()
    return json.loads(gzip.decompress(data) if str(path).endswith('.gz') else data)


def replay(root=None):
    repo = Path(__file__).resolve().parents[2]
    root = Path(root) if root else repo/'experiments/arithmetic/evidence/common_polarity_budget_v15'
    identity = load(root/'identity.json')
    for name, digest in identity['files'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest() != digest:
            raise ValueError('evidence changed '+name)
    for name, digest in identity['source_sha256'].items():
        if hashlib.sha256((repo/name).read_bytes()).hexdigest() != digest:
            raise ValueError('source changed '+name)
    archive = load(root/'source-and-tools.json.gz')['files']
    for name, item in archive.items():
        if hashlib.sha256(item['text'].encode()).hexdigest() != item['sha256']:
            raise ValueError('archived text changed '+name)
    recovery = load(root/'verifier-recovery.json')
    previous = ast.parse(archive['tools/phase_cut_cover_before_verifier_guard.py']['text'])
    current = ast.parse(archive['experiments/arithmetic_dse/phase_cut_cover_v15.py']['text'])
    functions = lambda tree: {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
    old, new = functions(previous), functions(current)
    if any(old[n] != new[n] for n in ('cover', 'enumerate_cuts', 'phase_truth')) or recovery['changed_functions'] != ['verify']:
        raise ValueError('numerical experiment changed during verifier recovery')
    cfg = load(root/'area-protocol.json.gz')
    data = load(root/'area-inputs.json.gz')
    prior = load(root/'inherited-v14-inputs.json.gz')
    library = load(root/'library.json.gz')['cells']
    report = load(root/'area-report.json.gz')
    predictions = load(root/'area-predictions.json.gz')
    candidate = load(root/'area-candidate.json.gz')
    S_cases = load(root/'S-budget-inputs.json.gz')
    S_audit = load(root/'S-budget-audit.json.gz')
    settlement = load(root/'settlement.json')
    fitter = {'__name__': 'v15_replay_fixed_fitter', '__file__': str(root/'inherited/v14_fit.py')}
    exec(compile(archive['inherited/v14_fit.py']['text'], 'v15_fixed_archived_fitter', 'exec'), fitter)
    graph_count = local_checks = negatives = feature_count = refits = S_count = S_negative = 0
    with patch('subprocess.Popen', side_effect=AssertionError('unexpected subprocess')):
        with patch('builtins.open', side_effect=AssertionError('unexpected computation read')):
            with patch('pathlib.Path.open', side_effect=AssertionError('unexpected computation path read')):
                table = base.library_table(library)
                work = {}
                for key, case in data['proofs'].items():
                    q, family = case['query'], case['family']
                    c, outputs = circuits.operator_circuit(q['local_context']['producer']) if family == 'Add' else circuits.reduction_circuit(q)[:2]
                    mapped = phase.cover(c, outputs, table, witnesses=True)
                    same(mapped, case['mapped'])
                    local_checks += phase.verify(c, outputs, mapped, table)
                    work[key] = mapped
                    graph_count += 1
                    for kind in ('truth', 'self_cycle', 'phase_range'):
                        bad = deepcopy(mapped)
                        if kind == 'truth':
                            bad['cuts'][0]['truth'] ^= 1
                        elif kind == 'phase_range':
                            bad['cuts'][0]['input_phases'] = 1 << len(bad['cuts'][0]['leaves'])
                        else:
                            root_node = bad['cuts'][0]['root']
                            bad['cuts'] = [dict(root=root_node, phase=0, leaves=[root_node], input_phases=0, truth=2, **table[1, 2])]
                            bad['area'] = 0.
                        try:
                            phase.verify(c, outputs, bad, table)
                        except ValueError:
                            negatives += 1
                        else:
                            raise ValueError('forged phase witness accepted')
                for family, rows in data['area'].items():
                    for row in rows:
                        if row['role'] != 'train':
                            raise ValueError('nontrain area row admitted')
                        original = next(r for r in prior['area'][family] if (r['source'], r['target_ps']) == (row['source'], row['target_ps']))
                        for k in ('source', 'group', 'role', 'target_ps', 'synth_area_um2', 'grt_area_um2'):
                            same(row[k], original[k])
                        f = dict(original['f'])
                        m = work[row['cover_identity']]
                        import math
                        f.update(cut_area=m['area'], log2_cut_cells=math.log2(1+m['cells']),
                            cut_shared_root_fraction=m['shared_roots']/max(1,m['mapped_roots']),
                            cut_overlap_gate_fraction=m['overlapping_interior_gates']/max(1,m['primitive_gates']))
                        same(f, row['f'])
                        q = deepcopy(data['proofs'][row['cover_identity']]['query'])
                        if family == 'Add':
                            q['flow_context']['target_period_ps'] = row['target_ps']
                            q['flow_context']['abc_target_ps'] = row['target_ps']
                            inherited = geometry.operator_features(q)
                        else:
                            q['target_ps'] = row['target_ps']
                            inherited = geometry.reduction_features(q)['intensive']
                        same(inherited, {k: row['f'][k] for k in inherited})
                        feature_count += 1
                    config = cfg['area'][family]
                    if config['forms'] != ['direct']:
                        raise ValueError('unregistered model form')
                    loo = []
                    for group in sorted({r['group'] for r in rows}):
                        train = [r for r in rows if r['group'] != group]
                        held = [r for r in rows if r['group'] == group]
                        if {r['source'] for r in train} & {r['source'] for r in held}:
                            raise ValueError('complete source leaked across T')
                        loo += fitter['predict'](held, fitter['train'](train, 'direct', config))
                        refits += 1
                    same(loo, predictions[family]['LOSO'])
                    stats = {q: fitter['stats'](loo, q) for q in ('grt', 'synth', 'ratio')}
                    same(stats, report['results'][family]['LOSO'])
                    entry = fitter['train'](rows, 'direct', config)
                    same(entry, candidate['models'][family])
                    same(fitter['predict'](rows, entry), predictions[family]['all_train'])
                    if family == 'G':
                        same({q: fitter['stats']([r for r in loo if r['no_compression']], q) for q in ('grt', 'synth', 'ratio')}, report['results'][family]['zero_compression_LOSO'])
                for name, case in S_cases.items():
                    args = {k: case[k] for k in ('start','instances','library','nets','endpoints','paths','origins','period_ps')}
                    value = budget.analyze(**args)
                    source, kind, stage = name.split('|')
                    expected = next(r for r in S_audit['rows'] if (r['source'],r['kind']) == (source,kind))
                    same(value, {k:v for k,v in expected.items() if k not in ('source','kind')})
                    for mutation in ('arc','wire','timing','boundary'):
                        bad = deepcopy(args)
                        endpoint = next(iter(bad['paths']))
                        points = bad['paths'][endpoint]
                        if mutation == 'timing': bad['endpoints'][endpoint]['budget_ps'] += 1
                        elif mutation == 'boundary': bad['paths'].pop(endpoint)
                        elif mutation == 'wire': bad['nets'][points[1]['pin']]['net'] = 'deliberately_disconnected'
                        else:
                            inst = points[1]['pin'].rsplit('/',1)[0]
                            bad['library'][bad['instances'][inst]]['timing_arcs'] = []
                        try:
                            budget.analyze(**bad)
                        except ValueError:
                            S_negative += 1
                        else:
                            raise ValueError('forged budget path accepted')
                    S_count += 1
    if settlement['usage']['support_calls'] != 6 or settlement['failed_calls'] != 2 or any(settlement['increment'][k] for k in ('synth','grt','final','pending')):
        raise ValueError('backend settlement changed')
    return dict(status='passed',prospective_graphs=graph_count,exact_phase_cut_checks=local_checks,
        mutated_phase_witness_negatives=negatives,pure_feature_queries=feature_count,
        sealed_fixed_trials=2,complete_group_refits=refits,candidate_inferences=feature_count,
        S_checkpoint_cases=S_count,S_endpoint_paths=sum(len(c['endpoints']) for c in S_cases.values()),
        S_path_mutation_negatives=S_negative,source_files=len(identity['source_sha256']),
        archived_text_records=len(archive),backend_calls_during_replay=0,
        new_optimization_calls=0,saved_checkpoint_support_calls=6,support_failures_preserved=2,
        validation_labels_read=False,independent_labels_read=False,new_price=False,public_D_changed=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path)
    print(json.dumps(replay(parser.parse_args().root),indent=2))
