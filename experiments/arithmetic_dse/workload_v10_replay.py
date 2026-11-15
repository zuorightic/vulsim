"""Portable receipts for the v10 W6/W7/W8 integration trial.

Reconstructs numerical queries from the already portable W2 compiler plans,
retargets only numerical T, and replays all owner prices with no external tree
or label access. Packing also verifies actual new exports against those plans.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import json
from pathlib import Path
import tarfile
from unittest.mock import patch

from . import workload_v10 as trial, workload_owned as owned

DEFAULT = trial.REPO / 'experiments/arithmetic/evidence/workload_transition_v10_v1'
PARENT = trial.REPO / 'experiments/arithmetic/evidence/workload_owners_v2'


def canonical(value):
    # LLVM emits an integral double as e.g. 3; Python's numerical retarget
    # produces 3.0. Bind numerical JSON meaning, preserving all other values.
    def normalize(v):
        if isinstance(v, float) and v.is_integer():
            return int(v)
        if isinstance(v, dict):
            return {k: normalize(x) for k, x in v.items()}
        if isinstance(v, list):
            return [normalize(x) for x in v]
        return v
    return json.dumps(normalize(value), sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return trial.sha(canonical(value))


def retarget(plan, target):
    p = deepcopy(plan); p['target_ps'] = target
    for op in p['operators']:
        for q in (op['query'], op['predecessor_projection']):
            if q is not None:
                q['flow_context']['target_period_ps'] = target
                q['flow_context']['abc_target_ps'] = target
        op['interface_features']['target_ps'] = target
        op['interface_features']['clock_pressure'] = 1500 / target
    for region in p['G_regions']:
        region['query']['target_ps'] = target
    return p


def compressed(path, value):
    path.write_bytes(gzip.compress(canonical(value), mtime=0))


def read_archive(path):
    # W2's archive manifest binds every member as well as each compressed file.
    index = owned.read(PARENT / 'archives.json')
    entry = next(e for e in index if e['file'] == str(path.relative_to(PARENT)))
    if trial.sha(path.read_bytes()) != entry['sha256']:
        raise ValueError('W2 archive SHA mismatch')
    with tarfile.open(path) as tar:
        result = {}
        for member in tar:
            if member.isfile():
                data = tar.extractfile(member).read()
                if trial.sha(data) != entry['members'][member.name]['sha256']:
                    raise ValueError('W2 member SHA mismatch')
                result[member.name] = data
    return result


def old_structure(case, structure):
    return read_archive(PARENT / f'structures/{case}-{structure}.tar.gz')


def restore_parent(destination):
    """Restore verified W2 inputs to reproduce fresh native trials anywhere."""
    destination = Path(destination); destination.mkdir(parents=True, exist_ok=False)
    for case in trial.contracts.load()['cases']:
        cid = case['id']; case_root = destination / cid
        policy = case['structural_search']
        count = len(policy['mul_block_widths']) * len(policy['add_sub_limb_widths'])
        for i in range(-1, count):
            members = read_archive(PARENT / f'cases/{cid}.tar.gz') if i < 0 else old_structure(cid, i)
            root = case_root if i < 0 else case_root / f'structure-{i}'
            for name, data in members.items():
                path = Path(name)
                if path.is_absolute() or '..' in path.parts:
                    raise ValueError('unsafe archive path')
                target = root / path; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
    return dict(status='restored_verified_W2_parent', directory=str(destination), cases=9)


def minimal(report):
    value = deepcopy(report)
    for row in value['owners']:
        raw = row['result']
        row['result'] = {k: raw[k] for k in ('status', 'comb_area_um2', 'operator_delay_ps', 'reason') if k in raw}
    return value


def pack(root, out):
    root, out = Path(root), Path(out); out.mkdir(parents=True, exist_ok=False)
    summary = owned.read(root / 'summary.json'); contract = owned.read(root / 'contract.json')
    if summary['targets'] != sum(len(c['formal_targets']) for c in contract['contracts']['cases'] if c['id'] in contract['selected_cases']):
        raise ValueError('declared targets not completed')
    trial.write(out / 'summary.json', summary); trial.write(out / 'contract.json', contract)
    files, exports, fresh, inherited = {}, 0, 0, 0
    for case in contract['contracts']['cases']:
        cid = case['id']
        if cid not in contract['selected_cases']:
            continue
        receipts = []
        for target in case['formal_targets']:
            folder = root / cid / f"T{target['T_ps']}-L{target['L']}"
            report = owned.read(folder / 'report.json'); evidence = []
            for structure in report['structures']:
                number = structure['structure']; dest = folder / f'structure-{number}'
                prior = old_structure(cid, number); old_inv = json.loads(prior['inventory.json'])
                inv = owned.read(dest / 'inventory.json')
                if (inv['views'] != old_inv['views'] or inv['search'] != old_inv['search']
                        or (dest / 'graph.json').read_bytes() != prior['graph.json']
                        or inv['diagnostic_T_ps'] != target['T_ps'] or inv['L'] != target['L']
                        or inv['model_bindings_sha256'] != contract['model_binding_sha256']):
                    raise ValueError('actual graph/finite search/target/model binding mismatch')
                views = []
                for view in inv['views']:
                    directory = view['directory']; vroot = dest / directory
                    expected_plan = retarget(json.loads(prior[directory + '/owners.json']), target['T_ps'])
                    plan = owned.read(vroot / 'owners.json')
                    if not owned.close(plan, expected_plan):
                        raise ValueError('actual owner plan differs from numerical retarget of W2')
                    expected_state = json.loads(prior[directory + '/state.json'])
                    expected_state['features']['sdc_period_ps'] = target['T_ps']
                    state = owned.read(vroot / 'state.json')
                    if state != expected_state:
                        raise ValueError('actual state differs from unchanged W2 function/state')
                    hashes = {}
                    for name in ('workload.sv', 'tb.sv'):
                        data = (vroot / name).read_bytes()
                        if data != prior[directory + '/' + name]:
                            raise ValueError('actual RTL/bench changed since archived W2')
                        hashes[name] = trial.sha(data)
                    cost = minimal(owned.read(vroot / 'costs-diagnostic.json'))
                    public = owned.read(vroot / 'costs-public.json')
                    trial.state_report(cost, state, target['L']); trial.state_report(public, state, target['L'])
                    if public['component_covered'] or any(r['result']['status'] != 'cost_uncovered' for r in public['owners']):
                        raise ValueError('public v10 price granted')
                    fresh_log = vroot / 'simulation-fresh.log'
                    is_fresh = fresh_log.exists()
                    simulation = fresh_log if is_fresh else vroot / 'simulation.log'
                    if 'PASS' not in simulation.read_text():
                        raise ValueError('missing passing simulation')
                    fresh += is_fresh; inherited += not is_fresh; exports += 1
                    views.append(dict(directory=directory, actual_plan_sha256=digest(plan),
                                      actual_state_sha256=digest(state), identical_functional_files=hashes,
                                      costs=cost, public_covered=0, fresh_simulation=is_fresh,
                                      simulation_log_sha256=trial.sha(simulation.read_bytes())))
                evidence.append(dict(structure=number, views=views))
            receipts.append(dict(target=target, report=report, structures=evidence))
        file = out / f'{cid}.json.gz'; compressed(file, receipts); files[file.name] = trial.sha(file.read_bytes())
    # Preserve the implementation used for collection; current code can be
    # inspected separately and portable replay never needs an external binary.
    paths = ['experiments/arithmetic_dse/workload_v10.py', 'experiments/arithmetic_dse/workload_v10_replay.py',
             'experiments/arithmetic_dse/workload_owned.py', 'rtlzz/src/backend/arithmetic_workload_provider.cpp',
             'regression/test_workload_v10.py']
    source = {p: (trial.REPO / p).read_text() for p in paths}
    compressed(out / 'source.json.gz', source)
    for name in ('summary.json', 'contract.json', 'source.json.gz'):
        files[name] = trial.sha((out / name).read_bytes())
    trial.write(out / 'manifest.json', dict(version='W678-v10-portable-v1', files=files,
                actual_exports_verified=exports, fresh_simulations=fresh, inherited_simulations=inherited,
                parent_archive_manifest_sha256=trial.sha((PARENT / 'archives.json').read_bytes()),
                model_sha256=trial.MODEL_SHA, labels_read=False, new_EDA_calls=0, full_D_ready=False))


def replay(root=DEFAULT):
    root = Path(root); manifest = owned.read(root / 'manifest.json')
    for name, expected in manifest['files'].items():
        if trial.sha((root / name).read_bytes()) != expected:
            raise ValueError('portable receipt SHA mismatch')
    if trial.sha((PARENT / 'archives.json').read_bytes()) != manifest['parent_archive_manifest_sha256']:
        raise ValueError('parent archive manifest changed')
    prices = trial.Prices(trial.binding()); total = Counter(); targets = 0
    contract = owned.read(root / 'contract.json')
    for case in contract['contracts']['cases']:
        cid = case['id']
        if cid not in contract['selected_cases']:
            continue
        receipt = json.loads(gzip.decompress((root / f'{cid}.json.gz').read_bytes()))
        if [r['target'] for r in receipt] != case['formal_targets']:
            raise ValueError('target denominator changed')
        for row in receipt:
            targets += 1; counts = Counter(); target = row['target']; candidate_count = 0
            candidates = {(c['structure'], c['view']): c for c in row['report']['candidates']}
            if len(candidates) != len(row['report']['candidates']):
                raise ValueError('duplicate candidate receipt')
            for structure in row['structures']:
                prior = old_structure(cid, structure['structure'])
                for view in structure['views']:
                    directory = view['directory']; candidate_count += 1
                    plan = retarget(json.loads(prior[directory + '/owners.json']), target['T_ps'])
                    state = json.loads(prior[directory + '/state.json']); state['features']['sdc_period_ps'] = target['T_ps']
                    if digest(plan) != view['actual_plan_sha256'] or digest(state) != view['actual_state_sha256']:
                        raise ValueError('actual new export/portable reconstruction differs')
                    for name, expected in view['identical_functional_files'].items():
                        if trial.sha(prior[directory + '/' + name]) != expected:
                            raise ValueError('functional artifact inheritance differs')
                    cost = view['costs']; trial.state_report(cost, state, target['L'])
                    candidate = candidates[(structure['structure'], directory)]
                    if (candidate['rtl_sha256'] != view['identical_functional_files']['workload.sv']
                            or candidate['graph_sha256'] != state['graph_sha256']
                            or candidate['layout_sha256'] != state['layout_sha256']
                            or candidate['state_bits'] != state['features']['state_bits']
                            or candidate['component_covered'] != cost['component_covered']
                            or candidate['component_uncovered'] != cost['component_uncovered']
                            or candidate['stage_status'] != cost['stage_status']
                            or candidate['total_area_um2'] is not None or candidate['critical_required_ps'] is not None
                            or not owned.close(candidate['partial_comb_area_um2'], cost['covered_comb_area_partial_um2'])):
                        raise ValueError('candidate table differs from complete native receipt')
                    operators = {o['node']: o for o in plan['operators']}; regions = {g['root']: g for g in plan['G_regions']}
                    if len(cost['owners']) != len(operators) + len(regions) + len(plan['functional_logic']):
                        raise ValueError('owner denominator changed')
                    expected_owners = {(n, 'operator') for n in operators} | {(n, 'G') for n in regions} | {(n, 'functional') for n in plan['functional_logic']}
                    if {(r['node'], r['owner']) for r in cost['owners']} != expected_owners:
                        raise ValueError('native pricing ownership changed')
                    # Each complete query enters the real pure Python model;
                    # no label, external tree, file or subprocess is available.
                    with patch('builtins.open', side_effect=AssertionError('online file read')), \
                         patch('io.open', side_effect=AssertionError('online pathlib read')), \
                         patch('subprocess.Popen', side_effect=AssertionError('online subprocess')):
                        covered = 0; partial = 0.
                        for owner in cost['owners']:
                            expected = prices.owner(owner, operators, regions, True); actual = owner['result']
                            accepted = actual['status'] in ('diagnostic_estimate', 'covered')
                            if accepted != (expected is not None and expected['status'] in ('diagnostic_estimate', 'covered')):
                                raise ValueError('cross-language price coverage differs')
                            if accepted:
                                for key in ('comb_area_um2', 'operator_delay_ps'):
                                    if not owned.close(actual[key], expected[key]):
                                        raise ValueError('cross-language numerical price differs')
                                partial += actual['comb_area_um2']; covered += 1
                    if covered != cost['component_covered'] or len(cost['owners']) - covered != cost['component_uncovered']:
                        raise ValueError('component total differs')
                    if not owned.close(partial, cost['covered_comb_area_partial_um2']):
                        raise ValueError('partial sum differs')
                    counts.update(views=1, owners=len(cost['owners']), diagnostic_covered=covered,
                                  diagnostic_uncovered=len(cost['owners'])-covered, stages=target['L'],
                                  fresh_simulations=int(view['fresh_simulation']), inherited_simulations=int(not view['fresh_simulation']))
            if candidate_count != len(row['report']['candidates']) or trial.selection(row['report']['candidates']) != row['report']['selection']:
                raise ValueError('selection was fabricated from incomplete prices')
            for key in ('diagnostic_covered', 'diagnostic_uncovered', 'fresh_simulations', 'inherited_simulations'):
                if counts[key] != row['report']['counts'][key]:
                    raise ValueError('target summary denominator differs')
            total.update(counts)
    summary = owned.read(root / 'summary.json')
    if targets != summary['targets']:
        raise ValueError('global target denominator changed')
    for key in ('diagnostic_covered', 'diagnostic_uncovered', 'fresh_simulations', 'inherited_simulations'):
        if total[key] != summary['counts'][key]:
            raise ValueError('global coverage/simulation count differs')
    if total['stages'] != summary['counts']['stage_requests']:
        raise ValueError('global stage/capture count differs')
    return dict(status='passed', targets=targets, counts=dict(total), unique_queries=len(prices.cache),
                external_artifacts_read=False, independent_labels_read=False, online_files_or_processes=False,
                new_EDA_calls=0, full_D_ready=False)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--evidence', type=Path, default=DEFAULT)
    p.add_argument('--pack', type=Path)
    p.add_argument('--restore-parent', type=Path)
    args = p.parse_args()
    if args.restore_parent:
        if args.pack:
            p.error('--restore-parent and --pack are separate actions')
        print(json.dumps(restore_parent(args.restore_parent), indent=2))
        raise SystemExit(0)
    if args.pack:
        pack(args.pack, args.evidence)
    print(json.dumps(replay(args.evidence), indent=2))
