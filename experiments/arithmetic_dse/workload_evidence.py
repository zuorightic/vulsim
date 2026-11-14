"""Replay the W1/W2 software evidence using retained graph/state/RTL data.

Default: verify all archive members and sources, recompute observed nine-case
requirements and the 19 targeted graph/query/G/bench checks. --reextract also
recomputes every formal-T demand for all 64 structures. --simulate recompiles
and runs all retained RTL benches, with backend PATH entries disabled.
No model parameters or independent labels are consumed.
"""
import argparse
import gzip
import hashlib
import io
import json
import math
import os
from pathlib import Path, PurePosixPath
import random
import shlex
import tarfile
import tempfile
from . import workload_contracts, workload_demand, workload_requirements
from .workload_software_validation import bench, run

REPO = Path(__file__).resolve().parents[2]
DEFAULT = REPO / 'experiments/arithmetic/evidence/workloads_software_v1'


def check(condition, message):
    if not condition:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def normalized(value):
    # JSON round trips also normalize integer stage keys in actual state maps.
    return json.loads(json.dumps(value))


def unpack(evidence, archive, dest):
    blob = (evidence / archive['file']).read_bytes()
    check(sha(blob) == archive['sha256'] and len(blob) == archive['bytes'],
          f'archive identity changed: {archive["file"]}')
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as tar:
        for member in tar:
            name = PurePosixPath(member.name)
            check(member.isfile() and not name.is_absolute() and '..' not in name.parts,
                  'only relative regular archive members are accepted')
            check(member.name not in seen and member.name in archive['members'],
                  'duplicate or undeclared member')
            seen.add(member.name)
            data = tar.extractfile(member).read()
            check(archive['members'][member.name] == dict(bytes=len(data), sha256=sha(data)),
                  f'member identity changed: {member.name}')
            target = dest / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
    check(seen == set(archive['members']), 'missing archive member')
    return len(seen)


def verify_views(root, spec, L, env, simulate):
    inv = read(root / 'inventory.json')
    graph = workload_demand.Graph(read(root / 'graph.json'))
    views, cycles = 0, 0
    check(inv['candidate_PPA_calls'] == 0 and not inv['model_selection_performed']
          and not inv['full_D_ready'], 'software identity changed')
    check(len(inv['views']) == inv['search']['returned_placements'], 'placement denominator changed')
    for view in inv['views']:
        dest = root / view['directory']
        rtl = (dest / 'workload.sv').read_bytes()
        artifact = view['artifact']
        check(sha(rtl) == artifact['sha256'], 'RTL differs from compiler receipt')
        check(artifact['L_including_capture'] == L and not artifact['model_boundary_qualification'],
              'pipeline/boundary identity changed')
        check(len(view['placement']) == len(graph.nodes), 'stage vector is not bound to the graph')
        state = read(dest / 'state.json')
        check(state['materialized_checked'], 'missing native state projection check')
        expected_tb, _ = bench(spec, artifact, L)
        check((dest / 'tb.sv').read_text() == expected_tb, 'reference/transaction bench changed')
        check('PASS' in (dest / 'simulation.log').read_text(), 'missing successful simulation receipt')
        if simulate:
            run(['iverilog', '-g2012', '-s', 'tb', '-o', dest / 'sim.out',
                 dest / 'workload.sv', dest / 'tb.sv'], dest / 'replay-iverilog.log', env)
            output = run(['vvp', dest / 'sim.out'], dest / 'replay-simulation.log', env)
            check('PASS' in output, 'replayed RTL did not finish successfully')
        views += 1
        cycles += 96
    return inv, views, cycles


def verify_g(graph, query):
    checks = 0
    for seed in range(8):
        rng = random.Random(837 + seed)
        values = graph.evaluate({p['name']: rng.getrandbits(p['width'])
                                 for p in graph.ports if p['input']})
        for view in query['views']:
            for region in view['G']['regions']:
                if region['geometry_status'] != 'represented':
                    continue
                total = sum(((values[int(source)] >> bit) & 1) << col
                            for term in region['terms'] for source, bit, col in term)
                mask = (1 << region['output_bits']) - 1
                check(total & mask == values[region['root']] & mask,
                      'proposed G replacement changes arithmetic')
                checks += 1
    return checks


def replay(evidence=DEFAULT, *, reextract=False, simulate=False):
    evidence = Path(evidence)
    manifest = read(evidence / 'manifest.json')
    check(manifest['version'] == 'W1W2-software-evidence-v1', 'unknown evidence version')
    for name, digest in manifest['implementation_sources'].items():
        check(sha((REPO / name).read_bytes()) == digest, f'implementation changed: {name}')
    for name, digest in manifest['evidence_files'].items():
        check(sha((evidence / name).read_bytes()) == digest, f'evidence changed: {name}')
    config = workload_contracts.load()
    binding_root = REPO / 'experiments/arithmetic/examples/workloads_v1'
    bindings = read(binding_root / 'contracts.json')
    config_sha = sha(workload_contracts.DEFAULT.read_bytes())
    check(bindings['contract_sha256'] == config_sha, 'source contract hash changed')
    cases = {c['id']: c for c in config['cases']}
    for binding in bindings['cases']:
        case = cases[binding['id']]
        check(binding['formal_targets'] == case['formal_targets']
              and binding['semantics'] == case['semantics'], 'bound case semantics/targets changed')
        for name, digest in binding['files'].items():
            check(sha((binding_root / binding['directory'] / name).read_bytes()) == digest,
                  'canonical unpipelined source binding changed')

    with tempfile.TemporaryDirectory(prefix='w1w2-replay-') as tmp:
        temp = Path(tmp)
        sentinels = temp / 'no-eda-bin'
        sentinels.mkdir()
        marker = temp / 'backend-attempt'
        for name in ('yosys', 'abc', 'yosys-abc', 'openroad', 'opensta', 'sta'):
            path = sentinels / name
            path.write_text('#!/bin/sh\nprintf forbidden > ' + shlex.quote(str(marker)) + '\nexit 97\n')
            path.chmod(0o755)
        env = dict(os.environ, PATH=str(sentinels) + os.pathsep + os.environ['PATH'])
        members = 0
        for archive in read(evidence / 'archives.json'):
            kind = archive['kind']
            if kind == 'case':
                dest = temp / 'cases' / archive['case']
            elif kind == 'structure':
                dest = temp / 'cases' / archive['case'] / f'structure-{archive["structure"]}'
            elif kind == 'diagnostic':
                dest = temp / 'diagnostics' / archive['case']
            else:
                check(kind in ('budget-stop', 'history-budget'), 'unknown archive kind')
                dest = temp / kind
            members += unpack(evidence, archive, dest)

        structures, placements, cycles, demands = 0, 0, 0, 0
        roots = []
        for case in config['cases']:
            root = temp / 'cases' / case['id']
            roots.append(root)
            record = read(root / 'inventory.json')
            check(record['case'] == case and record['new_EDA_calls'] == 0
                  and not record['independent_labels_read'], 'effective per-case config differs')
            check((root / 'source/source.cpp').read_bytes() ==
                  (binding_root / case['id'] / 'source.cpp').read_bytes(), 'actual source differs')
            check(record['declared_structures'] == len(record['structures']), 'incomplete structure list')
            for row in record['structures']:
                check(row['status'] == 'software_exported' and row['exit_code'] == 0,
                      'effective inventory is not completely exported')
                dest = root / row['directory']
                inv, nv, nc = verify_views(dest, record['source_spec'], case['formal_targets'][0]['L'], env, simulate)
                check(inv['source_sha256'] == sha((root / 'source/source.cpp').read_bytes())
                      and inv['search'] == row['search'], 'source/search identity differs')
                check(len(row['functional']) == nv and sum(f['cycles'] for f in row['functional']) == nc,
                      'functional coverage denominator differs')
                check(not inv['search']['budget_exhausted'], 'effective structure hit budget')
                for name, target in zip(row['demand_files'], case['formal_targets'], strict=True):
                    query = json.loads(gzip.decompress((dest / name).read_bytes()))
                    check(query['target_ps'] == target['T_ps'] and len(query['views']) == nv,
                          'formal-T demand denominator differs')
                    if reextract:
                        check(normalized(workload_demand.extract(dest, target['T_ps'])) == query,
                              'actual graph/state demand differs from stored formal-T data')
                        demands += 1
                structures += 1
                placements += nv
                cycles += nc
        actual_requirements = workload_requirements.collect(roots)
        check(normalized(actual_requirements) == read(evidence / 'requirements.json'),
              'observed W1 requirements differ from real W2 records')

        validation = read(evidence / 'validation.json')
        native_checks, g_checks, diagnostic_views = 0, 0, 0
        for case in validation['cases']:
            root = temp / 'diagnostics' / case['case']
            spec = read(root / 'source/semantics.json')
            inv, nv, _ = verify_views(root / 'export', spec, case['L'], env, simulate)
            check(inv['search'] == case['search'], 'diagnostic search changed')
            query = workload_demand.extract(root / 'export', 1373.)
            check(normalized(query) == read(root / 'demand.json'), 'diagnostic demand changed')
            represented = [r for v in query['views'] for r in v['operators']
                           if r['interface_status'] == 'represented']
            check([dict(query=r['query']) for r in represented] == read(root / 'queries.json'),
                  'native Query input differs from real graph extraction')
            native = read(root / 'native-queries.json')
            for row, cpp in zip(represented, native, strict=True):
                expected = workload_demand.wide.features(row['query'])
                check(cpp['accepted'] and expected.keys() == cpp['features'].keys()
                      and all(math.isclose(v, cpp['features'][k], rel_tol=1e-12, abs_tol=1e-8)
                              for k, v in expected.items()), 'Python/recorded-C++ features differ')
            ng = verify_g(workload_demand.Graph(read(root / 'export/graph.json')), query)
            check(ng == case['G_integer_replacement_checks'] and len(native) == case['native_wide_query_checks'],
                  'targeted feature/G coverage differs')
            native_checks += len(native)
            g_checks += ng
            diagnostic_views += nv

        stop = read(temp / 'budget-stop/export/inventory.json')
        check(stop['search']['budget_exhausted'] and not stop['views'], 'budget stop did not fail closed')
        old = read(temp / 'history-budget/inventory.json')
        old_case = old['case']
        check(old_case['structural_search']['max_extensions_per_structure'] == 100000,
              'original Montgomery budget identity differs')
        inherited_case = normalized(old_case)
        inherited_case['structural_search']['max_extensions_per_structure'] = 200000
        inherited_case['structural_search']['budget_provenance'] = (
            'finite software successor after two 100000-extension stops; '
            'original failures retained; no EDA')
        check(inherited_case == cases['montgomery256'], 'successor changed more than software budget')
        old_stops = [r for r in old['structures'] if r['status'] != 'software_exported']
        check(len(old_stops) == 2 and all(r['search']['budget_exhausted'] for r in old_stops),
              'original Montgomery 100k failures not preserved')
        legacy = json.loads(gzip.decompress((evidence / 'legacy-505.json.gz').read_bytes()))
        check(legacy['complete'] and legacy['assignments'] == 505 and len(legacy['views']) == 505,
              'legacy enumeration trace differs')
        check(not marker.exists(), 'backend startup attempted')
        result = dict(status='passed', archive_members_verified=members,
                      structures=structures, placements=placements, cycles=cycles,
                      targeted_groups=len(validation['cases']), targeted_placements=diagnostic_views,
                      recorded_CPP_feature_checks=native_checks, G_integer_checks=g_checks,
                      formal_T_demands_reextracted=demands, RTL_simulations_rerun=(placements + diagnostic_views if simulate else 0),
                      original_budget_stops_retained=len(old_stops), legacy_assignment_trace=505,
                      new_EDA_calls=0, independent_labels_read=False, full_D_ready=False)
        check(structures == 64 and placements == 502 and cycles == 48192 and
              diagnostic_views == 141 and native_checks == 6144 and g_checks == 1472,
              'acceptance totals changed')
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence', type=Path, default=DEFAULT)
    parser.add_argument('--reextract', action='store_true')
    parser.add_argument('--simulate', action='store_true')
    args = parser.parse_args()
    print(json.dumps(replay(args.evidence, reextract=args.reextract, simulate=args.simulate), indent=2))
