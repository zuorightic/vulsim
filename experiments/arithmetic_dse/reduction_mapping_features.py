"""Intensive G geometry, including conjunctions of direct input bits."""
import math
from . import reduction_context_work as parent, reduction_structural_graph as graph

VERSION = 'common-positive-geometry-G-features-v6'


def features(width, terms, target):
    f = parent.features(width, terms, target)
    c = graph.circuit(width, terms)
    memo = {}
    live = set()

    def visit(n):
        if n not in c['nodes']:
            return frozenset((n,)) if n >= 2 else None
        if n in memo:
            return memo[n]
        live.add(n)
        kind, a, b = c['nodes'][n]
        aa, bb = visit(a), visit(b)
        memo[n] = aa | bb if kind == 'and' and aa is not None and bb is not None else None
        return memo[n]

    for n in c['outputs']:
        visit(n)
    raw = [atoms for n, atoms in memo.items() if atoms is not None]
    maximum = max(map(len, raw), default=0)
    a, d = f['area'], f['delay']
    fa, ha = a['word_full_adder_cuts'], a['word_half_adder_cuts']
    unpaired = a['word_unpaired_xor'] + a['word_unpaired_and'] + a['word_unpaired_or']
    merge = d['post_merge_increment_columns'] + d['post_merge_full_adder_columns'] + d['post_merge_half_adder_columns']
    intensive = dict(one=1., log2_output_scale=math.log2(width / 64.),
                     log2_logic_depth=math.log2(a['word_logic_depth'] + 1),
                     half_fraction=ha / max(1., fa + ha), full_fraction=fa / max(1., fa + ha),
                     unpaired_fraction=unpaired / max(1., fa + ha + unpaired),
                     compressed_half_fraction=ha / max(1., fa + ha) * (1. - a['word_no_compression']),
                     increment_fraction=d['post_merge_increment_columns'] / max(1., merge),
                     raw_and_fraction=len(raw) / max(1., len(live)),
                     log2_raw_and_inputs=math.log2(maximum + 1),
                     log2_target=a['log2_target'], clock_pressure=a['clock_pressure'])
    f['intensive'] = intensive
    return f
