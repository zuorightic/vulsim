"""N1: freeze actual old-D inputs and inventory only the six scoped demands.

All snapshots and full demand records stay outside Git. Existing exports are
read-only prospective observations, never training labels or application PPA.
"""
import argparse
from collections import Counter, defaultdict
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from . import workload_tight_run as tight, workload_latency_matrix as matrix
from . import workload_final_software as software
from . import workload_final_selection as selector
from .workload_equivalent import SearchConfig
from .equivalent_period import InversionConfig
from .platforms import profile

ROOT = Path(__file__).resolve().parents[2]
SCOPE = dict(mac32=[2, 3], add512=[2, 4], mul128=[2, 4])
ACTIVE = ROOT.parent / 'vulsim-artifacts/old-D-clock-successor-20261117-v2/protocol.json'
VERSION = 'nangate45-frozen-D-N1-v1'


def canonical(doc):
    return json.dumps(doc, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, doc):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')


def software_root(case, depth):
    return (tight.DEFAULT / 'software' if depth == dict(mac32=3, add512=4, mul128=4)[case]
            else matrix.DEFAULT / 'variants' / case / f'L{depth}' / 'software')


def freeze(out):
    out = Path(out).resolve()
    if out.is_relative_to(ROOT):
        raise ValueError('freeze snapshots must stay outside Git')
    if (out / 'baseline.json').exists():
        raise ValueError('use a new freeze directory')
    parent = read(ACTIVE)
    changed = [p for p, expected in parent['files'].items() if sha(p) != expected]
    if changed:
        raise ValueError('active old-D input drift: ' + str(changed))
    files = {Path(p) for p in parent['files']}
    # The active parent binds the binary. Also preserve the available native
    # sources, compile graph, and software functions as a reviewable source chain.
    files.update(p for base in ('rtlzz/src', 'rtlzz/main', 'vullib')
                 for p in (ROOT/base).rglob('*') if p.is_file() and p.suffix in ('.cpp', '.hpp', '.h', '.uh'))
    files.update([ACTIVE, ROOT/'build/workload-v10-20261115/build.ninja'])
    files.update(Path(__file__).parent/n for n in ('nangate45_migration.py', 'nangate45_connection.py',
        'nangate45_connection_check.py', 'nangate45_entry_check.py', 'workload_platform_entry.py',
        'configs/nangate45_frozen_d_v1.json'))
    for case, depths in SCOPE.items():
        for depth in depths:
            soft = software_root(case, depth)
            files.update(soft/n for n in ('bindings.json', 'characterization-contract.json'))
            files.add(soft/case/'static-pool.json')
            files.update(p for p in (soft/case/'source').iterdir() if p.is_file())
    copied = {}
    for source in sorted(files):
        relative = source.relative_to(ROOT) if source.is_relative_to(ROOT) else Path('external')/source.relative_to('/')
        saved = out / 'snapshot' / relative
        saved.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, saved)
        expected = sha(source)
        if sha(saved) != expected:
            raise ValueError('snapshot changed during copy: ' + str(source))
        copied[str(source)] = dict(sha256=expected, snapshot=str(saved.relative_to(out)), bytes=source.stat().st_size)
    doc = dict(version=VERSION, parent=str(ACTIVE), parent_sha256=sha(ACTIVE),
        active_parent_files_verified=len(parent['files']), files=copied,
        compiler=dict(path=str(software.BINARY), sha256=sha(software.BINARY)),
        model=dict(path=str(selector.BASE/'diagnostic-model.json'), sha256=sha(selector.BASE/'diagnostic-model.json')),
        component_model_sha256='a1466f0272b55bd20358ea9e3beb84844db8fe8fefe4152e0478224d8f13243d',
        diagnostic_identity='workload-v10-complete-diagnostic-v1', scope=SCOPE,
        search=asdict(SearchConfig()), inversion=asdict(InversionConfig()),
        selectors=['workload_final_selection.py', 'workload_latency_matrix.py', 'workload_guided_search.py'],
        budget_path=['workload_tight_equivalent.py', 'workload_final_adapter.py', 'workload_equivalent.py', 'local_budget.py', 'equivalent_period.py'],
        selection_key='feasible: area,id; otherwise full violation,area,id; current finite pool only',
        implementation='global ABC at requested T; equivalent tau affects prediction only',
        known_limits='R1-R5 deferred; no position-feedback or effective-state-bit repair',
        frozen_live_files_modified=False, application_PPA_read=False, new_EDA_calls=0)
    write(out/'baseline.json', doc)
    return doc


def inventory(out):
    out = Path(out).resolve()
    if (out/'demand-summary.json').exists():
        raise ValueError('demand inventory already frozen')
    variants = []
    source_index = {}
    descriptors = defaultdict(dict)
    def bind(path):
        path = Path(path)
        if str(path) not in source_index:
            source_index[str(path)] = sha(path)
    for case, depths in SCOPE.items():
        for depth in depths:
            soft = software_root(case, depth)
            pool_path = soft/case/'static-pool.json'
            pool = read(pool_path)
            bind(pool_path)
            inventories = set((soft/case).glob('*/inventory.json'))
            inventories.update(Path(r['graph']).parent/'inventory.json' for r in pool['candidates']
                               if (Path(r['graph']).parent/'inventory.json').exists())
            # MAC L3's frozen selector also uses the finite step45 pool,
            # including block12. Inspect native prospective exports directly,
            # without reading its score traces or measured results.
            if case == 'mac32' and depth == 3:
                inventories.update((ROOT.parent/'vulsim-artifacts/workload-equivalent-steps45-v1/search/native').glob('*/inventory.json'))
            candidates = {}
            for row in pool['candidates']:
                folder = Path(row['folder'])
                state = read(folder/'state.json')
                if state['internal_stages'] + 1 != depth:
                    raise ValueError('static pool contains another L')
                graph_path = Path(row['graph'])
                bind(graph_path)
                candidates.setdefault((row['rtl_sha256'],tuple(row['placement'])),
                    (folder,dict(placement=row['placement']),read(graph_path),graph_path.parent/'inventory.json'))
            for path in sorted(inventories):
                inv = read(path)
                if inv['L'] != depth:
                    continue
                bind(path)
                graph_path = path.parent/'graph.json'
                bind(graph_path)
                graph = read(graph_path)
                for view in inv['views']:
                    folder = path.parent/view['directory']
                    identity = (view['artifact']['sha256'], tuple(view['placement']))
                    candidates.setdefault(identity, (folder, view, graph, path))
            counts = Counter()
            features = defaultdict(list)
            shapes = defaultdict(set)
            occupancies = []
            for folder, view, graph, inv_path in candidates.values():
                owner_path, state_path = folder/'owners.json', folder/'state.json'
                bind(owner_path); bind(state_path)
                owners, state = read(owner_path), read(state_path)
                if owners['profile_sha256'] != profile('asap7')['profile_sha256']:
                    raise ValueError('unexpected source platform')
                active = set()
                for row in owners['operators']:
                    query = json.loads(json.dumps(row['query']))
                    spec = query['local_context']['producer']
                    family = spec['operation']
                    query['flow_context'].pop('target_period_ps')
                    query['flow_context'].pop('abc_target_ps')
                    key = hashlib.sha256(canonical(query)).hexdigest()
                    descriptors[family].setdefault(key, query)
                    counts[family] += 1
                    shapes[family].add((spec['lhs_width'], spec['rhs_width'], spec['result_width'], spec['value_width'], spec['result_lo']))
                    active.add(view['placement'][row['node']])
                for row in owners['G_regions']:
                    query = json.loads(json.dumps(row['query']))
                    query.pop('target_ps')
                    roots = {}
                    for term in query['terms']:
                        for value in term:
                            roots.setdefault(value[0], len(roots))
                            value[0] = roots[value[0]]
                    key = hashlib.sha256(canonical(query)).hexdigest()
                    descriptors['G'].setdefault(key, query)
                    counts['G'] += 1
                    shapes['G'].add((row['output_bits'], len(query['terms']), query['launch_type'], query['capture_banks'], query.get('consumer_count', 0)))
                    active.add(view['placement'][row['root']])
                counts['functional'] += len(owners['functional_logic'])
                for name, value in state['features'].items():
                    if name != 'sdc_period_ps':
                        features[name].append(value)
                occupancies.append(dict(folder=str(folder), inventory=str(inv_path),
                    graph_sha256=sha(inv_path.parent/'graph.json'), layout_sha256=state['layout_sha256'],
                    arithmetic_G_stages=sorted(active), arithmetic_G_empty_stages=[i for i in range(depth) if i not in active],
                    functional_nodes=len(owners['functional_logic']),
                    boundary_kinds=['input_service->native_state'] + (['native_state->native_state'] if depth>2 else []) + ['native_state->external_state']))
            variants.append(dict(case=case, L=depth, grammar=pool['grammar'], prospective_candidates=len(candidates),
                operator_G_observations=dict(counts), shapes={k:[list(s) for s in sorted(v)] for k,v in shapes.items()},
                state_feature_ranges={k:dict(min=min(v), max=max(v)) for k,v in features.items()},
                deepest_arithmetic_G_stage_count=max(len(r['arithmetic_G_stages']) for r in occupancies),
                occupancy=occupancies))
    payload = dict(version=VERSION, source_files=source_index, variants=variants,
        shared_query_descriptors={k:list(v.values()) for k,v in descriptors.items()},
        role='prospective_demand_only_not_prices', normalization='remove T; G root names alpha-renamed, equality/columns retained',
        target_T='Nangate45 A not measured yet; exact tau/budget domains determined after N3-N6',
        frozen_ASAP_candidate_union_not_all_future_price_dependent_positions=True)
    (out/'demand.json.gz').write_bytes(gzip.compress(canonical(payload), mtime=0))
    summary = dict(version=VERSION, scope=SCOPE, variants=[{k:v for k,v in r.items() if k!='occupancy'} for r in variants],
        unique_shared_descriptors={k:len(v) for k,v in descriptors.items()},
        source_files=len(source_index), full_demand_sha256=sha(out/'demand.json.gz'),
        demand_role=payload['role'], target_T=payload['target_T'],
        price_dependent_positions='candidate grammar unchanged; new models may propose new positions; N5-N7 re-extract before claiming coverage',
        new_EDA_calls=0, application_PPA_read=False)
    write(out/'demand-summary.json', summary)
    return summary


def verify(out):
    out = Path(out)
    baseline = read(out/'baseline.json')
    for name, item in baseline['files'].items():
        if sha(name) != item['sha256'] or sha(out/item['snapshot']) != item['sha256']:
            raise ValueError('baseline input drift: ' + name)
    summary = read(out/'demand-summary.json')
    if sha(out/'demand.json.gz') != summary['full_demand_sha256']:
        raise ValueError('demand payload drift')
    full = json.loads(gzip.decompress((out/'demand.json.gz').read_bytes()))
    for name, expected in full['source_files'].items():
        if sha(name) != expected:
            raise ValueError('demand input drift: ' + name)
    return dict(status='passed', baseline_files=len(baseline['files']), demand_files=len(full['source_files']))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('action', choices=['freeze', 'inventory', 'verify'])
    a = p.parse_args()
    result = globals()[a.action](a.out)
    print(json.dumps({k:v for k,v in result.items() if k not in ('files','variants')}, ensure_ascii=False, indent=2))
