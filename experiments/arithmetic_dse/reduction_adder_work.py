"""Prospective full/half-adder cuts in the live word-compression DAG.

The cuts describe Boolean work that can map to shared sum/carry cells. They
do not count mapped cells. Unpaired live gates retain their own work terms.
"""
import math
from . import reduction_structural_graph as parent

VERSION = 'wide-reduction-features-v3-adder-cuts'


def features(width, terms, target):
    f = parent.features(width, terms, target)
    graph = parent.circuit(width, terms)
    nodes = graph['nodes']
    live = set()
    xor_depth = {}
    carry_depth = {}

    def visit(node):
        if node not in nodes:
            return (0, 0)
        if node in live:
            return xor_depth[node], carry_depth[node]
        live.add(node)
        kind, a, b = nodes[node]
        x, y = visit(a), visit(b)
        xor_depth[node] = max(x[0], y[0]) + (kind == 'xor')
        carry_depth[node] = max(x[1], y[1]) + (kind != 'xor')
        return xor_depth[node], carry_depth[node]

    for output in graph['outputs']:
        visit(output)
    lookup = {nodes[n]: n for n in live}

    def at(kind, a, b):
        return lookup.get((kind, *sorted((a, b))))

    bundled = set()
    full = 0
    for carry in sorted(live):
        kind, u, v = nodes[carry]
        if kind != 'or' or u not in nodes or v not in nodes:
            continue
        for ab, pc in ((u, v), (v, u)):
            if nodes[ab][0] != 'and' or nodes[pc][0] != 'and':
                continue
            a, b = nodes[ab][1:]
            p = at('xor', a, b)
            if p is None or p not in nodes[pc][1:]:
                continue
            c = nodes[pc][2] if nodes[pc][1] == p else nodes[pc][1]
            total = at('xor', p, c)
            members = {carry, ab, pc, p, total}
            if total is None or members & bundled:
                continue
            bundled.update(members)
            full += 1
            break
    half = 0
    for node in sorted(live - bundled):
        kind, a, b = nodes[node]
        pair = at('and', a, b) if kind == 'xor' else None
        if pair is not None and pair not in bundled:
            bundled.update((node, pair))
            half += 1
    remaining = live - bundled
    extra = dict(word_full_adder_cuts=float(full), word_half_adder_cuts=float(half),
                 word_unpaired_xor=float(sum(nodes[n][0] == 'xor' for n in remaining)),
                 word_unpaired_and=float(sum(nodes[n][0] == 'and' for n in remaining)),
                 word_unpaired_or=float(sum(nodes[n][0] == 'or' for n in remaining)),
                 word_max_xor_depth=float(max((xor_depth.get(n, 0) for n in graph['outputs']), default=0)),
                 word_max_carry_depth=float(max((carry_depth.get(n, 0) for n in graph['outputs']), default=0)),
                 word_no_compression=float(graph['tree_rounds'] == 0))
    for side in f.values():
        side.update(extra)
    return f
