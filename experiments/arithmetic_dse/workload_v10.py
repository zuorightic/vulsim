"""Frozen v10 integration trial on actual W2 owners, all nineteen T/L requests.

Application graphs are never training sources. Missing arithmetic S/shared,
functional logic, correlations or operator contexts remain explicit. This trial
does not turn partial component sums into full-stage timing or a D winner.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import itertools
import json
import os
from pathlib import Path
import shlex
import shutil

from . import workload_contracts as contracts, workload_sources as sources
from . import workload_owned as owned, workload_demand as demand
from . import transition_incidence_model_v10 as transition
from . import operator_function_successor as inherited_operator
from .workload_software_validation import bench, run as command

REPO = Path(__file__).resolve().parents[2]
MODEL_SHA = 'a1466f0272b55bd20358ea9e3beb84844db8fe8fefe4152e0478224d8f13243d'
BINDING_VERSION = 'workload-transition-v10-bindings-v1'
EVIDENCE = REPO / 'experiments/arithmetic/evidence/common_transition_incidence_v10'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def binding():
    raw = gzip.decompress((EVIDENCE / 'runtime-bundle.json.gz').read_bytes())
    if sha(raw) != MODEL_SHA:
        raise ValueError('frozen v10 runtime SHA mismatch')
    model = json.loads(raw)
    profile = model['inherited_flow']['inherited_centered']['operator_profile_sha256']
    return dict(version=BINDING_VERSION, profile_sha256=profile,
                transition_model_json=raw.decode())


class Prices:
    """In-memory numeric consumption. Cache keys contain only full queries."""
    def __init__(self, bindings):
        raw = bindings['transition_model_json'].encode()
        if bindings['version'] != BINDING_VERSION or sha(raw) != MODEL_SHA:
            raise ValueError('frozen v10 binding mismatch')
        self.model = json.loads(raw)
        centered = self.model['inherited_flow']['inherited_centered']
        if bindings['profile_sha256'] != centered['operator_profile_sha256']:
            raise ValueError('v10 profile mismatch')
        self.inherited = centered['semantic_operator_model']
        self.cache = {}

    def price(self, kind, query, diagnostic):
        key = (kind, diagnostic, json.dumps(query, sort_keys=True, separators=(',', ':')))
        if key in self.cache:
            return self.cache[key]
        if not diagnostic:
            result = dict(status='cost_uncovered', reason='v10 workload integration requires explicit diagnostics')
        elif kind == 'G':
            result = transition.predict_reduction(self.model, query, diagnostic=True)
        else:
            op = query['local_context']['producer']['operation']
            if op in ('add', 'adc', 'mux'):
                result = transition.predict_operator(self.model, query, diagnostic=True)
                if op == 'mux' and result['status'] == 'diagnostic_delay_only':
                    area = inherited_operator.predict(self.inherited, query, diagnostic=True)
                    if area['status'] != 'diagnostic_estimate' or 'comb_area_um2' not in area:
                        result = dict(status='cost_uncovered', reason='declared inherited Mux area unavailable')
                    else:
                        result = dict(result, status='diagnostic_estimate', comb_area_um2=area['comb_area_um2'],
                                      area_source='v10.inherited_flow.inherited_centered.semantic_operator_model')
            else:
                result = inherited_operator.predict(self.inherited, query, diagnostic=True)
        self.cache[key] = result
        return result

    def owner(self, owner, operators, regions, diagnostic):
        n = owner['node']
        if owner['owner'] == 'operator':
            q = operators[n]['predecessor_projection']
            return self.price('operator', q, diagnostic) if q is not None else None
        if owner['owner'] == 'G':
            q = regions[n]['query']
            return self.price('G', q, diagnostic) if not q['shared_input_root_pairs'] else None
        return None


def state_report(report, state, L):
    if (report['transition_model_sha256'] != MODEL_SHA or report['binding_version'] != BINDING_VERSION
            or report['state_graph_sha256'] != state['graph_sha256']
            or report['state_layout_sha256'] != state['layout_sha256']):
        raise ValueError('v10 report lost actual model/graph/state binding')
    if (report['S_adapter']['affine_semantics_fabricated'] is not False
            or report['S_adapter']['status'] != 'cost_uncovered'
            or report['selection_status'] != 'cost_uncovered'):
        raise ValueError('actual arithmetic state silently converted to affine prices')
    if len(report['stages']) != L:
        raise ValueError('stage denominator excludes output capture')
    for stage in report['stages']:
        slots = [s for s in state['slots'] if s['stage'] == stage['stage'] and not s['valid']]
        if (stage['retained_data_words'] != len(slots)
                or stage['retained_variable_bits'] != sum(s['variable_bits'] for s in slots)
                or stage['status'] != 'cost_uncovered'):
            raise ValueError('actual state bank denominator changed')


def inherit(dest, previous, view, old_view, state, tb):
    """T affects costs and SDC only; prove the complete functional artifacts."""
    if view != old_view:
        raise ValueError('inherited placement/RTL identity differs')
    identities = {}
    for name in ('workload.sv', 'tb.sv'):
        data = (dest / name).read_bytes()
        if data != (previous / name).read_bytes():
            raise ValueError('simulation reuse changed ' + name)
        identities[name] = sha(data)
    old_state = owned.read(previous / 'state.json')
    normalized, old_normalized = deepcopy(state), deepcopy(old_state)
    for s in (normalized, old_normalized):
        del s['features']['sdc_period_ps']
    if normalized != old_normalized:
        raise ValueError('simulation reuse changed state/reset/enable/capture')
    output = (previous / 'simulation.log').read_text()
    if 'PASS' not in output:
        raise ValueError('parent simulation did not pass')
    write(dest / 'simulation-inheritance.json', dict(parent=str(previous), identical_files=identities,
          state_unchanged_except_sdc_period=True, previous_T_ps=old_state['features']['sdc_period_ps'],
          T_ps=state['features']['sdc_period_ps'], parent_log_sha256=sha(output.encode())))
    shutil.copyfile(previous / 'simulation.log', dest / 'simulation.log')


def selection(candidates):
    """No timing/area ordering exists when every complete price is missing."""
    if any(c['stage_status'] != 'cost_uncovered' for c in candidates):
        raise ValueError('new complete-stage support requires a separately frozen selector contract')
    return dict(status='cost_uncovered', selected=None, target_met=None,
                requested_candidates=len(candidates), complete_candidates=0,
                reason='no complete arithmetic S/shared/data/control timing and total area',
                incomplete_candidates_competed=False, static_fallback=False)


def trial(out, binary, parent, cases=None):
    out, binary, parent = Path(out).resolve(), Path(binary).resolve(), Path(parent).resolve()
    out.mkdir(parents=True, exist_ok=False)
    bindings = binding(); write(out / 'models.json', bindings)
    prices = Prices(bindings); doc = contracts.load()
    chosen = [c for c in doc['cases'] if cases is None or c['id'] in cases]
    # Freeze the finite work before compiling any application at any target.
    write(out / 'contract.json', dict(version='W678-v10-integration-trial-v1', model_sha256=MODEL_SHA,
          model_binding_sha256=sha((out / 'models.json').read_bytes()), contracts=doc,
          binary_sha256=sha(binary.read_bytes()), selected_cases=[c['id'] for c in chosen],
          dispatch={'add_adc': 'v10', 'mux_delay': 'v10',
                    'mux_area_and_other_operators': 'v10 frozen inherited semantic operator', 'G': 'v10'},
          complete_stage_missing='cost_uncovered; no static/affine substitution; no selection',
          search='unchanged finite W2 grammar and bounded proposals at every declared T/L',
          fresh_simulations='first structure/view of every case/T; additionally MAC32 4-bit first view',
          parent_functional_evidence=str(parent), candidate_PPA_calls=0, model_fitting=False,
          independent_labels_read=False, full_D_ready=False))
    noeda = out / 'no-eda-bin'; noeda.mkdir(); marker = out / 'backend-attempt'
    for name in ('yosys', 'abc', 'yosys-abc', 'openroad', 'opensta', 'sta'):
        p = noeda / name
        p.write_text('#!/bin/sh\nprintf forbidden > ' + shlex.quote(str(marker)) + '\nexit 97\n')
        p.chmod(0o755)
    env = dict(os.environ, PATH=str(noeda) + os.pathsep + os.environ['PATH'])
    reports = []
    for case in chosen:
        case_id = case['id']; case_root = out / case_id; case_root.mkdir()
        spec = sources.prepare_case(case_root / 'source', case_id)
        if (case_root / 'source/source.cpp').read_bytes() != (parent / case_id / 'source/source.cpp').read_bytes():
            raise ValueError('application source changed since verified W2')
        policy = case['structural_search']
        for target in case['formal_targets']:
            root = case_root / f"T{target['T_ps']}-L{target['L']}"; root.mkdir()
            candidates, structures = [], []; counts = Counter(); reasons = Counter()
            for number, (block, limb) in enumerate(itertools.product(policy['mul_block_widths'], policy['add_sub_limb_widths'])):
                dest = root / f'structure-{number}'; previous = parent / case_id / f'structure-{number}'
                command([binary, REPO, case_root / 'source/request.json', target['L'], limb,
                         policy['beam_width'], policy['max_extensions_per_structure'], dest, block,
                         target['T_ps'], 'owned', out / 'models.json'], root / f'structure-{number}.log', env, 300)
                inv, old = owned.read(dest / 'inventory.json'), owned.read(previous / 'inventory.json')
                if (dest / 'graph.json').read_bytes() != (previous / 'graph.json').read_bytes() or inv['search'] != old['search']:
                    raise ValueError('finite search/graph changed since W2')
                graph = demand.Graph(owned.read(dest / 'graph.json'))
                structures.append(dict(structure=number, mul_block_width=block, limb_width=limb, search=inv['search']))
                for i, view in enumerate(inv['views']):
                    folder = dest / view['directory']; state = owned.read(folder / 'state.json')
                    counts.update(owned.verify_plan(dest, view, graph, {}, predictor=prices.owner))
                    report = owned.read(folder / 'costs-diagnostic.json')
                    state_report(report, state, target['L'])
                    public = owned.read(folder / 'costs-public.json'); state_report(public, state, target['L'])
                    reasons.update(r['result'].get('reason', 'unspecified') for r in report['owners'] if r['result']['status'] == 'cost_uncovered')
                    tb, checks = bench(spec, view['artifact'], target['L']); (folder / 'tb.sv').write_text(tb)
                    inherit(folder, previous / view['directory'], view, old['views'][i], state, tb)
                    fresh = i == 0 and (number == 0 or (case_id == 'mac32' and block == 4))
                    if fresh:
                        command(['iverilog', '-g2012', '-s', 'tb', '-o', folder / 'sim.out', folder / 'workload.sv', folder / 'tb.sv'], folder / 'iverilog-fresh.log', env, 300)
                        output = command(['vvp', folder / 'sim.out'], folder / 'simulation-fresh.log', env, 300)
                        if 'PASS' not in output:
                            raise ValueError('fresh simulation did not pass')
                        counts['fresh_simulations'] += 1; counts['fresh_cycles'] += 96
                    else:
                        counts['inherited_simulations'] += 1; counts['inherited_cycles'] += 96
                    counts['result_checks'] += checks; counts['stage_requests'] += target['L']
                    candidates.append(dict(structure=number, view=view['directory'], rtl_sha256=view['artifact']['sha256'],
                          graph_sha256=state['graph_sha256'], layout_sha256=state['layout_sha256'],
                          state_bits=state['features']['state_bits'], component_covered=report['component_covered'],
                          component_uncovered=report['component_uncovered'], stage_status=report['stage_status'],
                          simulation='fresh_pass' if fresh else 'identical_functional_artifacts',
                          partial_comb_area_um2=report['covered_comb_area_partial_um2'],
                          total_area_um2=None, critical_required_ps=None))
                graph.origins.cache_clear(); graph.roots.cache_clear()
                print(json.dumps(dict(case=case_id, target=target, structure=number, views=len(inv['views']), status='verified')), flush=True)
            result = dict(case=case_id, target=target, structures=structures, candidates=candidates,
                          counts=dict(counts), component_rejection_reasons=dict(reasons), selection=selection(candidates))
            write(root / 'report.json', result); reports.append(result)
    if marker.exists():
        raise ValueError('online backend startup attempted')
    summary = dict(version='W678-v10-integration-trial-v1', model_sha256=MODEL_SHA, targets=len(reports),
                   cases=len(chosen), counts=dict(sum((Counter(r['counts']) for r in reports), Counter())),
                   results=[{k: r[k] for k in ('case', 'target', 'counts', 'selection', 'component_rejection_reasons')} for r in reports],
                   unique_price_queries=len(prices.cache), candidate_PPA_calls=0, model_fitting=False,
                   independent_labels_read=False, full_D_ready=False)
    write(out / 'summary.json', summary)
    return summary


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--binary', type=Path, required=True)
    p.add_argument('--parent', type=Path, required=True)
    p.add_argument('--case', action='append', choices=sorted(contracts.CASE_IDS))
    args = p.parse_args()
    trial(args.out, args.binary, args.parent, args.case)
