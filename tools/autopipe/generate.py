"""Prospective finite candidate search using the unchanged v10 cost functions."""
import gzip
import itertools
import math
from pathlib import Path
import shutil
import signal
import subprocess
import time

from .compiler import verified_build
from .resources import ROOT, MODELS, EXAMPLES, read, write, sha, runtime
from .workload_abcd import static_node, static_cost, static_score
from .workload_demand import Graph
from .workload_dot16_latency import depth_schedule
from .workload_final_software import balanced
from .workload_equivalent import score_key
from .workload_platform_entry import rebind_owners
from .workload_v10_replay import retarget


def widths(text, default):
    result = list(default) if text is None else [int(v) for v in text.split(',')]
    if not result or len(result) != len(set(result)) or any(v < 0 or v > 4096 for v in result):
        raise ValueError('width grammar must contain distinct integers in 0..4096')
    return result


class Generation:
    def __init__(self, args):
        self.args = args
        self.out = args.out.resolve()
        if self.out.exists():
            raise ValueError('output already exists; use a fresh --out directory')
        if not math.isfinite(args.period_ps) or args.period_ps <= 0 or not 1 <= args.latency <= 256:
            raise ValueError('positive finite period and L=1..256 required')
        if not math.isfinite(args.timeout_s) or not 0 < args.timeout_s <= 3600:
            raise ValueError('software timeout must be in (0,3600] seconds')
        if not 1 <= args.candidate_limit <= 4096:
            raise ValueError('candidate limit must be in 1..4096')
        if args.method == 'A' and args.latency != 1:
            raise ValueError('A is the original L=1 implementation')
        if args.check and not args.workload:
            raise ValueError('--check requires a bundled workload with an independent reference')
        self.binary, self.native_root = verified_build(args.build_dir)
        self.rt = runtime(args.platform)
        self.source_request = (EXAMPLES / args.workload / 'request.json' if args.workload else args.source_request).resolve()
        doc = read(self.source_request)
        source = Path(doc['source']['source'])
        if not source.is_absolute():
            source = self.source_request.parent / source
        if sha(source) != doc['source']['generated_source_sha256']:
            raise ValueError('source SHA-256 differs from request')
        self.out.mkdir(parents=True)
        source_out = self.out / 'input'
        source_out.mkdir()
        shutil.copyfile(source, source_out / 'source.cpp')
        doc['source']['source'] = 'source.cpp'
        self.request = source_out / 'request.json'
        write(self.request, doc)
        catalog = read(MODELS / 'workloads.json')
        case = next((c for c in catalog['cases'] if c['id'] == args.workload), None)
        grammar = case['structural_search'] if case else dict(mul_block_widths=[0, 4, 8, 16], add_sub_limb_widths=[0, 32, 64, 128])
        mul = widths(args.mul_block_widths, grammar['mul_block_widths'])
        limb = widths(args.add_limb_widths, grammar['add_sub_limb_widths'])
        if any(v > 128 for v in mul):
            raise ValueError('frozen native multiplier block width must be in 0..128')
        self.grammar = [(0, 0)] if args.method in ['A', 'B'] else list(itertools.product(mul, limb))
        if len(self.grammar) > 16:
            raise ValueError('frozen structural policy permits at most 16 grammars')
        self.started = time.monotonic()
        self.counter = 0
        self.exported = {}

    def remaining(self):
        left = self.args.timeout_s - (time.monotonic() - self.started)
        if left <= 0:
            raise TimeoutError('software budget exhausted; partial traces retained in ' + str(self.out))
        return left

    def export(self, block, limb, placements=None):
        key = block, limb, None if placements is None else tuple(tuple(p) for p in placements)
        if key in self.exported:
            return self.exported[key]
        self.counter += 1
        folder = self.out / 'candidates' / f'{self.counter:03d}-b{block}-w{limb}'
        folder.parent.mkdir(exist_ok=True)
        command = [str(self.binary), str(self.native_root), str(self.request), str(self.args.latency), str(limb),
                   '1', '200000', str(folder), str(block), str(self.args.period_ps), 'owned']
        if placements is not None:
            probe = self.export(block, limb)
            explicit = folder.with_suffix('.placements.json')
            empty = folder.with_suffix('.models.json')
            write(explicit, dict(version='workload-explicit-schedules-v1', L=self.args.latency,
                T_clk_ps=self.args.period_ps, graph_export_sha256=sha(probe / 'graph.json'), placements=placements))
            write(empty, {})
            command.extend([str(empty), str(explicit)])
        with folder.with_suffix('.log').open('w') as log:
            subprocess.run(command, check=True, stdout=log, stderr=subprocess.STDOUT, timeout=min(600, self.remaining()))
        self.exported[key] = folder
        return folder

    def rows(self, folder, number, grammar, origin='native_beam'):
        graph = Graph(read(folder / 'graph.json'))
        result = []
        for view in read(folder / 'inventory.json')['views']:
            path = folder / view['directory']
            state = read(path / 'state.json')
            result.append(dict(structure=number, view=view['directory'], folder=str(path),
                graph=str(folder / 'graph.json'), grammar=list(grammar), placement=view['placement'], origin=origin,
                artifact=view['artifact'], rtl_sha256=sha(path / 'workload.sv'), L=self.args.latency,
                static=static_cost(graph, view, state, self.args.latency)))
        Graph.origins.cache_clear()
        Graph.roots.cache_clear()
        return result

    def metadata(self, row):
        path = Path(row['folder'])
        state = read(path / 'state.json')
        owners = retarget(read(path / 'owners.json'), self.args.period_ps)
        if self.args.platform != 'asap7':
            owners = rebind_owners(owners, self.args.platform)
            for region in owners['G_regions']:
                region['query'].update(target_platform=self.args.platform, profile_sha256=owners['profile_sha256'])
        return Graph(read(row['graph'])), dict(placement=row['placement']), state, owners

    def pool(self):
        seeds = []
        candidates = []
        seen = set()

        def add(row):
            if row['rtl_sha256'] not in seen:
                if len(candidates) >= self.args.candidate_limit:
                    raise ValueError('candidate limit reached; increase --candidate-limit; partial pool retained')
                seen.add(row['rtl_sha256'])
                candidates.append(row)

        for number, grammar in enumerate(self.grammar):
            block, limb = grammar
            native = self.export(block, limb)
            raw = read(native / 'graph.json')
            graph = Graph(raw)
            weights = {n['id']:static_node(graph, n) for n in graph.nodes}
            units = read(native / 'scheduling-units.json')['units']
            placements = balanced(raw, units, self.args.latency, weights)
            try:
                depth = depth_schedule(raw, units, self.args.latency, weights)
            except ValueError as error:
                if 'depth cannot fill' not in str(error) and 'arithmetic-empty stage' not in str(error):
                    raise
            else:
                if depth not in placements:
                    placements.append(depth)
            rows = self.rows(native, number, grammar)
            balanced_rows = self.rows(self.export(block, limb, placements), number, grammar, 'balanced_static')
            rows.extend(balanced_rows)
            seeds.extend(rows)
            if self.args.method != 'D':
                continue
            chosen = [min(rows, key=static_score),
                      min(rows, key=lambda r:(r['static']['saved_bits'], static_score(r))),
                      min(balanced_rows, key=static_score)]
            for row in chosen:
                add(row)
            graph, view, state, owners = self.metadata(chosen[0])
            prediction = self.rt.evaluate(graph, view, state, owners)
            groups = {r['root']:r['members'] for r in owners['G_regions']}
            pressure_weights = {}
            for owner in prediction['owners']:
                members = groups.get(owner['node'], [owner['node']])
                for node in members:
                    pressure_weights[node] = owner['delay_ps'] / len(members)
            pressure = balanced(raw, units, self.args.latency, pressure_weights)[:2]
            for row in self.rows(self.export(block, limb, pressure), number, grammar, 'model_pressure_balanced'):
                add(row)
            self.remaining()
            print(f'Prepared structure {number + 1}/{len(self.grammar)}; candidates={len(candidates)}', flush=True)
        static_winner = min(seeds, key=static_score)
        if self.args.method == 'D':
            add(static_winner)
        else:
            candidates = [static_winner]
        write(self.out / 'candidate-pool.json', dict(policy='frozen-v10-finite-native-and-balanced-v1',
            grammar=self.grammar, candidates=candidates, candidate_PPA_calls=0,
            exhaustive_global_search=False, R1_R5_enabled=False))
        return candidates

    def select(self):
        candidates = self.pool()
        scored = []
        for index, row in enumerate(candidates):
            graph, view, state, owners = self.metadata(row)
            if self.args.method == 'D':
                result = self.rt.optimize(graph, view, state, owners)
                prediction = result['prediction']
                trace = self.out / 'scores' / f'{index:03d}.json.gz'
                trace.parent.mkdir(exist_ok=True)
                import json
                trace.write_bytes(gzip.compress(json.dumps(result, allow_nan=False, separators=(',', ':')).encode(), mtime=0))
            else:
                prediction = self.rt.evaluate(graph, view, state, owners)
            if prediction is not None:
                scored.append(dict(row=row, prediction=prediction))
            self.remaining()
            print(f'Scored {index + 1}/{len(candidates)}', flush=True)
            Graph.origins.cache_clear()
            Graph.roots.cache_clear()
        if not scored:
            raise ValueError('no candidate has a complete model prediction; no RTL selected')
        winner = min(scored, key=lambda r:score_key(r['prediction']) + (r['row']['rtl_sha256'],))
        row = winner['row']
        selected = self.out / (self.args.method + '.sv')
        shutil.copyfile(Path(row['folder']) / 'workload.sv', selected)
        result = dict(schema='autopipe-frozen-v10-selection-v1', method=self.args.method, platform=self.args.platform,
            T_clk_ps=self.args.period_ps, L=self.args.latency, II=1, additional_input_service_cycles=1,
            selection_status='target_met' if winner['prediction']['target_met'] else 'target_unmet',
            rtl=str(selected), rtl_sha256=sha(selected), prediction=winner['prediction'],
            selected_candidate=row, complete_candidates=len(scored), candidate_count=len(candidates),
            model_manifest_sha256=sha(MODELS / 'manifest.json'), model_refitted=False, R1_R5_enabled=False,
            qualification='diagnostic_only', full_D_ready=False, backend_calls=0)
        write(self.out / 'selection.json', result)
        if self.args.check:
            from .workload_software_validation import bench
            for executable in ['iverilog', 'vvp']:
                if not shutil.which(executable):
                    raise ValueError('required simulation tool missing: ' + executable)
            spec = read(EXAMPLES / self.args.workload / 'semantics.json')
            text, checks = bench(spec, row['artifact'], self.args.latency, cycles=96)
            testbench = self.out / 'tb.sv'
            testbench.write_text(text)
            sim = self.out / 'sim.vvp'
            with (self.out / 'simulation.log').open('w') as log:
                subprocess.run(['iverilog', '-g2012', '-s', 'tb', '-o', str(sim), str(selected), str(testbench)],
                               check=True, stdout=log, stderr=subprocess.STDOUT, timeout=self.remaining())
                subprocess.run(['vvp', str(sim)], check=True, stdout=log, stderr=subprocess.STDOUT, timeout=self.remaining())
            result['simulation'] = dict(status='passed', cycles=96, integer_cycle_checks=checks)
            write(self.out / 'selection.json', result)
        return result


def generate(args):
    generation = Generation(args)
    old_handler = signal.getsignal(signal.SIGALRM)

    def timeout(signum, frame):
        raise TimeoutError('software budget exhausted; partial files retained in ' + str(generation.out))

    signal.signal(signal.SIGALRM, timeout)
    signal.setitimer(signal.ITIMER_REAL, generation.remaining())
    try:
        return generation.select()
    except BaseException as error:
        write(generation.out / 'failure.json', dict(status='failed', reason=str(error), backend_calls=0,
            partial_outputs_retained=True, elapsed_s=time.monotonic() - generation.started))
        raise
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
