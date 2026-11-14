"""Prospective cut work with separately referenced positive/negative signals.

This tests the phase treatment absent from v14, keeping its library, cut and
pass bounds. It is a Boolean work proxy, not ABC, timing mapping or placement.
All inputs are semantic DAGs and frozen library constants; no I/O is performed.
"""
from collections import Counter
from functools import lru_cache
import math

from . import prospective_cut_cover_v14 as base

VERSION = 'bounded-dual-phase-cut-work-v15'


@lru_cache(maxsize=4096)
def phase_truth(count, truth, input_phases, output_phase):
    mask = (1 << (1 << count)) - 1
    if not 0 <= input_phases < (1 << count) or output_phase not in (0, 1):
        raise ValueError('invalid phase assignment')
    value = sum(((truth >> (i ^ input_phases)) & 1) << i for i in range(1 << count))
    return value ^ (mask if output_phase else 0)


def enumerate_cuts(circuit, outputs):
    live, users = base.live_graph(circuit, outputs)
    cuts = {n: [(n,)] for n in circuit.leaves.values()}
    cuts.update({0: [()], 1: [()]})
    records = {}
    for node in sorted(live):
        kind, a, b = circuit.nodes[node]
        children = (a,) if kind == 'not' else (a, b)
        unions = set(cuts[a]) if len(children) == 1 else {
            tuple(sorted(set(x) | set(y))) for x in cuts[a] for y in cuts[b]
            if len(set(x) | set(y)) <= base.MAX_INPUTS}
        immediate = tuple(sorted(set(children) - {0, 1}))
        selected = sorted(unions, key=lambda c: (len(c), c))[:base.CUT_LIMIT]
        if immediate not in selected:
            selected = selected[:base.CUT_LIMIT-1] + [immediate]
        cuts[node] = [(node,)] + selected
        records[node] = [(leaves, base.cut_truth(circuit, node, leaves)) for leaves in selected]
    return live, users, records


def cover(circuit, outputs, table, *, witnesses=False):
    live, users, records = enumerate_cuts(circuit, outputs)
    inverter = table[(1, 1)]
    primary = set(circuit.leaves.values())

    @lru_cache(maxsize=None)
    def matches(count, truth, phase):
        return [(mask, table[key]) for mask in range(1 << count)
                if (key := (count, phase_truth(count, truth, mask, phase))) in table]

    refs = Counter({(node, phase): count for node, count in users.items() for phase in (0, 1)})
    chosen, active, depth = {}, set(), {}
    for _ in range(base.FLOW_PASSES):
        flow = {}
        for node in primary:
            flow[node, 0] = 0.
            flow[node, 1] = inverter['area'] / max(1., refs[node, 1])
            depth[node, 0], depth[node, 1] = 0, 1
            chosen[node, 1] = dict(root=node, phase=1, leaves=[node], input_phases=0,
                truth=1, **inverter)
        for node in sorted(live):
            for phase in (0, 1):
                best = None
                for leaves, truth in records[node]:
                    for mask, match in matches(len(leaves), truth, phase):
                        deps = [(n, (mask >> i) & 1) for i, n in enumerate(leaves)]
                        cost = match['area'] + math.fsum(flow.get(n, 0.) for n in deps)
                        levels = (match['cell'] != 'wire') + match['invert'] + max((depth.get(n, 0) for n in deps), default=0)
                        rank = cost, levels, len(leaves), match['cell'], leaves, mask
                        if best is None or rank < best[0]:
                            best = rank, dict(root=node, phase=phase, leaves=list(leaves),
                                input_phases=mask, truth=phase_truth(len(leaves), truth, mask, phase), **match)
                if best is None:
                    raise ValueError('no legal phase-aware primitive cover')
                rank, chosen[node, phase] = best
                flow[node, phase] = rank[0] / max(1., refs[node, phase])
                depth[node, phase] = rank[1]
        active, pending, refs = set(), [(n, 0) for n in outputs], Counter((n, 0) for n in outputs)
        while pending:
            key = pending.pop()
            if key not in chosen or key in active:
                continue
            active.add(key)
            cut = chosen[key]
            deps = [(n, (cut['input_phases'] >> i) & 1) for i, n in enumerate(cut['leaves'])]
            refs.update(deps)
            pending.extend(deps)
    selected = [chosen[n] for n in sorted(active)]
    histogram = Counter(c['cell'] for c in selected if c['cell'] != 'wire')
    histogram.update(c['inverter'] for c in selected if c['invert'])
    # Count semantic overlap exactly as v14, independent of signal phase.
    interiors = Counter()
    for cut in selected:
        pending, seen, boundary = [cut['root']], set(), set(cut['leaves'])
        while pending:
            n = pending.pop()
            if n in boundary or n in seen or n not in circuit.nodes:
                continue
            seen.add(n)
            kind, a, b = circuit.nodes[n]
            pending.extend((a,) if kind == 'not' else (a, b))
        interiors.update(seen)
    result = dict(version=VERSION, area=math.fsum(c['area'] for c in selected),
        cells=sum(histogram.values()), depth=max((depth.get((n, 0), 0) for n in outputs), default=0),
        mapped_roots=len(active), shared_roots=sum(refs[n] > 1 for n in active),
        overlapping_interior_gates=sum(v > 1 for v in interiors.values()), primitive_gates=len(live),
        negative_phase_roots=sum(phase for _, phase in active),
        dual_phase_signals=sum((n, 0) in active and (n, 1) in active for n in live | primary),
        histogram=dict(sorted(histogram.items())), max_inputs=base.MAX_INPUTS,
        cut_limit=base.CUT_LIMIT, flow_passes=base.FLOW_PASSES, physical_timing_modeled=False)
    if witnesses:
        result.update(cuts=selected, outputs=list(outputs))
    return result


def verify(circuit, outputs, mapped, table):
    if list(outputs) != mapped['outputs']:
        raise ValueError('mapped output boundary changed')
    cuts = {(c['root'], c['phase']): c for c in mapped['cuts']}
    if len(cuts) != len(mapped['cuts']):
        raise ValueError('duplicate mapped phase root')
    primary = set(circuit.leaves.values())
    for (root, phase), cut in cuts.items():
        if phase not in (0, 1) or not 0 <= cut['input_phases'] < (1 << len(cut['leaves'])):
            raise ValueError('invalid mapped phase assignment')
        if cut['leaves'] != sorted(set(cut['leaves'])):
            raise ValueError('noncanonical cut leaves')
        if root in primary:
            if phase != 1 or cut['leaves'] != [root] or cut['input_phases'] != 0:
                raise ValueError('primary inversion must terminate at native input')
        elif root not in circuit.nodes or any(n >= root for n in cut['leaves']):
            raise ValueError('mapped dependency is not topologically earlier')
        truth = phase_truth(len(cut['leaves']), base.cut_truth(circuit, root, cut['leaves']), cut['input_phases'], phase)
        match = table.get((len(cut['leaves']), truth))
        if match is None or any(cut[k] != v for k, v in match.items()) or cut['truth'] != truth:
            raise ValueError('phase cut disagrees with legal Boolean cell')
    seen, pending = set(), [(n, 0) for n in outputs]
    while pending:
        key = pending.pop()
        node, phase = key
        if node < 2 or (node in primary and phase == 0) or key in seen:
            continue
        if key not in cuts:
            raise ValueError('missing live mapped phase root')
        seen.add(key)
        cut = cuts[key]
        pending.extend((n, (cut['input_phases'] >> i) & 1) for i, n in enumerate(cut['leaves']))
    if seen != set(cuts) or not math.isclose(mapped['area'], math.fsum(c['area'] for c in cuts.values()), abs_tol=1e-12):
        raise ValueError('phase mapping area/reachability does not conserve roots')
    return len(cuts)
