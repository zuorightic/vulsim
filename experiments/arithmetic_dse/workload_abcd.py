"""Common nine-workload baselines and immutable implementation records.

The static successor extends the prescribed power-of-two Mul buckets to 4096
bits. It is an abstract cost table, without application or backend prices.
All methods consume the same compiler graphs, schedules and service shell.
"""
import argparse
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import shutil
import gzip

from . import workload_contracts as contracts
from .workload_demand import Graph, WIRE
from .workload_software_validation import bench, run

ROOT = Path(__file__).resolve().parents[2]
STATIC_VERSION = 'fixed-op-width-workload-v2'


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def static_node(graph, node):
    """Prescribed weights on actual, live compiler nodes, including G members."""
    i, op = node['id'], node['operation']
    if not graph.demand[i] or node['constant'] or op in WIRE | {'input'} or graph.wire_equivalent(i):
        return 0.
    if op == 'mul':
        width = max(map(graph.billing, node['operands'][:2]))
        if not 1 <= width <= 4096:
            raise ValueError('static successor input width outside 1..4096')
        bucket = 1 << (width - 1).bit_length()
        return float(max(1, bucket // 2))
    if op in ('shl', 'shr'):
        a = node['operands'][1]
        return 0. if a['node'] is None or graph.nodes[a['node']]['constant'] else 2.
    if op in {'add', 'adc', 'sub', 'ult', 'ule', 'ugt', 'uge', 'eq', 'ne', 'mux',
              'and', 'or', 'xor', 'not', 'lnot', 'land', 'lor', 'neg'}:
        return 1.
    raise ValueError('unpriced static operation: ' + op)


def dag_timing(graph, placement, delays, state, L):
    """Parallel max, serial sum; a saved value starts a new timing cone.

    Data capture endpoints come from the materialized state layout, rather
    than an assumption that every operation ends a stage.
    """
    active = set()

    @lru_cache(None)
    def arrival(i):
        if i in active:
            raise ValueError('cyclic compiler graph')
        active.add(i)
        n = graph.nodes[i]
        upstream = max((arrival(a['node']) for a in n['operands']
                        if a['node'] is not None and placement[a['node']] == placement[i]), default=0.)
        active.remove(i)
        return upstream + delays.get(i, 0.)

    stages = [0.] * L
    for slot in state['slots']:
        if slot['valid'] or not slot['variable_bits']:
            continue
        origin, capture = slot['origin'], slot['stage'] - 1
        if not 0 <= capture < L or placement[origin] > capture:
            raise ValueError('capture inconsistent with actual placement')
        # Repeated pass-through banks are new register-to-register paths.
        value = arrival(origin) if placement[origin] == capture else 0.
        stages[capture] = max(stages[capture], value)
    return stages


def static_cost(graph, view, state, L):
    weights = {n['id']: static_node(graph, n) for n in graph.nodes}
    stages = dag_timing(graph, view['placement'], weights, state, L)
    f = state['features']
    comb = sum(weights.values())
    return dict(version=STATIC_VERSION, stage_delay_weights=stages,
                maximum_stage_abstract_delay=max(stages), comb_weight=comb,
                saved_bits=f['state_bits'], saved_signals=f['state_signals'],
                comb_weight_plus_saved_bits=comb + f['state_bits'])


def static_score(row):
    c = row['static']
    return (c['maximum_stage_abstract_delay'], c['comb_weight_plus_saved_bits'],
            c['saved_bits'], c['saved_signals'], row['structure'], int(row['view']))


def candidate_records(target_root, L):
    rows = []
    directories = (p for p in Path(target_root).glob('structure-*') if p.is_dir())
    for directory in sorted(directories, key=lambda p: int(p.name.split('-')[1])):
        inventory = read(directory / 'inventory.json')
        graph = Graph(read(directory / 'graph.json'))
        for view in inventory['views']:
            folder = directory / view['directory']
            state = read(folder / 'state.json')
            if sha(folder / 'workload.sv') != view['artifact']['sha256']:
                raise ValueError('candidate RTL changed since compiler export')
            rows.append(dict(structure=int(directory.name.split('-')[1]), view=view['directory'],
                             folder=str(folder.resolve()), mul_block_width=inventory['mul_block_width'],
                             rtl_sha256=view['artifact']['sha256'],
                             graph_sha256=state['graph_sha256'], layout_sha256=state['layout_sha256'],
                             static=static_cost(graph, view, state, L)))
        graph.origins.cache_clear(); graph.roots.cache_clear()
    if not rows:
        raise ValueError('empty finite candidate set')
    return rows


def prepare_baselines(out, parent, binary):
    out, parent, binary = Path(out).resolve(), Path(parent).resolve(), Path(binary).resolve()
    out.mkdir(parents=True, exist_ok=False)
    doc = contracts.load()
    write(out / 'protocol.json', dict(version='nine-workload-ABCD-v1', contracts=doc,
          parent=str(parent), binary_sha256=sha(binary), static_version=STATIC_VERSION,
          static_extension='power-of-two Mul buckets through 4096, weight max(1,bucket/2); other rules v1',
          A='original unsplit graph, L=1 including capture',
          B='original unsplit graph, declared L, static placement score',
          C='all declared split structures, declared L, static score',
          D='pending complete common model selection', candidate_PPA_calls=0,
          all_selection_must_freeze_before_application_PPA=True, application_PPA_feedback=False))
    records = []
    env = dict(os.environ, OMP_NUM_THREADS='1')
    for case in doc['cases']:
        case_id = case['id']; case_out = out / case_id; case_out.mkdir()
        source_request = parent / case_id / 'source/request.json'
        # Every original implementation has exactly one all-combinational placement.
        spec = read(source_request.with_name('semantics.json'))
        a_dir = case_out / 'A-original'
        run([binary, ROOT, source_request, 1, 0, 1, 200000, a_dir, 0,
             case['formal_targets'][0]['T_ps'], 'owned'], case_out / 'A-export.log', env, 300)
        inv = read(a_dir / 'inventory.json')
        if len(inv['views']) != 1 or any(inv['views'][0]['placement']):
            raise ValueError('A must have exactly one original combinational implementation')
        view = inv['views'][0]; folder = a_dir / view['directory']
        tb, checks = bench(spec, view['artifact'], 1); (folder / 'tb.sv').write_text(tb)
        run(['iverilog', '-g2012', '-s', 'tb', '-o', folder / 'sim.out', folder / 'workload.sv', folder / 'tb.sv'],
            folder / 'iverilog.log', env, 300)
        output = run(['vvp', folder / 'sim.out'], folder / 'simulation.log', env, 300)
        if 'PASS' not in output:
            raise ValueError('A simulation failed: ' + case_id)
        a = dict(structure=0, view='0', folder=str(folder), rtl_sha256=sha(folder / 'workload.sv'),
                 simulation_checks=checks, L=1)
        for target in case['formal_targets']:
            target_id = f"T{target['T_ps']}-L{target['L']}"
            rows = candidate_records(parent / case_id / target_id, target['L'])
            b = min((r for r in rows if r['structure'] == 0), key=static_score)
            c = min(rows, key=static_score)
            result = dict(case=case_id, target=target, candidates=rows,
                          A=a, B=dict(b, L=target['L']), C=dict(c, L=target['L']),
                          selection_policy='static candidate_score; no PPA; target independent weights')
            write(case_out / (target_id + '.json'), result)
            records.append({k: result[k] for k in ('case', 'target', 'A', 'B', 'C')})
            print(json.dumps(dict(case=case_id, target=target, candidates=len(rows),
                                  B=[b['structure'], b['view']], C=[c['structure'], c['view']], A_simulation='passed')), flush=True)
    summary = dict(version='nine-workload-ABC-v1', records=records, cases=9, targets=len(records),
                   A_new_simulations=9, A_new_cycles=864, candidate_PPA_calls=0, D_selected=False)
    write(out / 'baselines.json', summary)
    return summary


def seal_baselines(out):
    """Copy selected implementations and verify their existing functional proof."""
    out = Path(out).resolve(); baselines = read(out/'baselines.json')
    destination = out/'baseline-inputs'; destination.mkdir(exist_ok=False)
    files = {}; methods = []; unique = {}
    for row in baselines['records']:
        record = dict(case=row['case'], target=row['target'], methods={})
        for method in ('A','B','C'):
            selected = row[method]; folder = Path(selected['folder']); digest = selected['rtl_sha256']
            if sha(folder/'workload.sv') != digest:
                raise ValueError('selected RTL differs from scored candidate')
            log = folder/'simulation.log'
            if 'PASS' not in log.read_text() or not (folder/'tb.sv').is_file():
                raise ValueError('selected implementation lacks successful transaction proof')
            if digest not in unique:
                dest = destination/digest; dest.mkdir()
                for name in ('workload.sv','state.json','tb.sv','simulation.log'):
                    shutil.copy2(folder/name,dest/name)
                if (folder/'owners.json').exists():
                    shutil.copy2(folder/'owners.json',dest/'owners.json')
                write(dest/'origin.json',dict(folder=str(folder),rtl_sha256=digest,
                      simulation='existing exact RTL/bench transaction verification',
                      simulation_log_sha256=sha(log),L=selected['L']))
                unique[digest] = dest
            dest = unique[digest]
            record['methods'][method] = dict(rtl=str(dest/'workload.sv'),rtl_sha256=digest,
                  L=selected['L'],simulation_status='passed',structure=selected['structure'],view=selected['view'],
                  static=selected.get('static'),input_service_additional_cycles=1,II=1)
        methods.append(record)
    write(out/'baseline-methods.json',dict(version='nine-workload-ABC-implementations-v1',records=methods,
          D='pending common complete model; no D substitute',unique_RTL=len(unique),candidate_PPA_calls=0))
    selected_paths = [p for p in destination.rglob('*') if p.is_file()]
    selected_paths += [out/n for n in ('protocol.json','baselines.json','baseline-methods.json')]
    selected_paths += [p for case in baselines['records'] for p in [out/case['case']/f"T{case['target']['T_ps']}-L{case['target']['L']}.json"]]
    for p in selected_paths: files[str(p)] = sha(p)
    freeze = dict(version='nine-workload-baselines-freeze-v1',methods=['A','B','C'],
                  files=files,unique_RTL=len(unique),target_records=19,application_PPA_seen=False,
                  final_ABCD_freeze=False,D_selected=False,qualification_granted=False)
    write(out/'baselines-freeze.json',freeze)
    # A portable selection/RTL/state/bench/log snapshot; no binary or EDA required.
    payload = {str(p.relative_to(out)):p.read_text() for p in selected_paths}
    payload['baselines-freeze.json'] = (out/'baselines-freeze.json').read_text()
    raw = json.dumps(dict(version='nine-workload-ABC-portable-v1',files=payload),ensure_ascii=False,separators=(',',':')).encode()
    (out/'baselines-portable.json.gz').write_bytes(gzip.compress(raw,mtime=0))
    return dict(status='ABC_sealed',unique_RTL=len(unique),target_records=19,
                portable_bytes=(out/'baselines-portable.json.gz').stat().st_size,new_EDA_calls=0)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--parent', type=Path)
    p.add_argument('--binary', type=Path)
    p.add_argument('--seal-baselines', action='store_true')
    a = p.parse_args()
    if a.seal_baselines: print(seal_baselines(a.out))
    else:
        if not a.parent or not a.binary: p.error('--parent and --binary required when generating baselines')
        prepare_baselines(a.out, a.parent, a.binary)
