"""Prospective word-compression DAG and live final-prefix work for G.

Column heights alone omit half-adders introduced when a vector compressor
also spans columns containing two bits. Reconstruct the generic summand-tree
algorithm before mapping, fold constants, and retain only demanded outputs.
No physical cell, source identity or measured value participates.
"""
import math
from . import reduction_wide_features as parent

VERSION = 'wide-reduction-features-v2-word-compression'


def circuit(width, terms):
    parent.features(width, terms, 1500.)  # Frozen semantic validation.
    nodes = {}
    intern = {}
    leaves = {}
    next_id = 2

    def leaf(key):
        nonlocal next_id
        if key not in leaves:
            leaves[key] = next_id
            next_id += 1
        return leaves[key]

    def gate(kind, a, b):
        nonlocal next_id
        if kind == 'and':
            if a == 0 or b == 0:
                return 0
            if a == 1:
                return b
            if b == 1 or a == b:
                return a
        elif kind == 'or':
            if a == 0:
                return b
            if b == 0 or a == b:
                return a
        elif kind == 'xor':
            if a == 0:
                return b
            if b == 0:
                return a
            if a == b:
                return 0
        key = (kind, *sorted((a, b)))
        if key not in intern:
            intern[key] = next_id
            nodes[next_id] = key
            next_id += 1
        return intern[key]

    columns = [[] for _ in range(width)]
    # Independent bits are interchangeable in a column. Use canonical column
    # ranks so names and term ordering cannot select a different price.
    mapping = {}
    for term in terms:
        for source, bit, col in term:
            mapping.setdefault(col, []).append((source, bit))
    for col in range(width):
        columns[col] = [leaf((col, rank)) for rank in range(len(mapping.get(col, [])))]
    summands = []
    packed = []
    while any(columns):
        summands.append([c.pop(0) if c else 0 for c in columns])
        while True:
            maximum = max(map(len, columns))
            position = max(i for i, c in enumerate(columns) if len(c) == maximum)
            if maximum == 0 or position > 4:
                break
            required = sum(1 << i for i in range(position + 1) if len(columns[i]) == maximum)
            if required > max(len(summands) - 1, 0) - len(packed):
                break
            for i in range(position + 1):
                if len(columns[i]) == maximum:
                    packed.extend([columns[i].pop(0)] * (1 << i))
    tree_rounds = 0
    while len(summands) > 2:
        following = []
        for offset in range(0, len(summands), 3):
            group = summands[offset:offset + 3]
            if len(group) < 3:
                following.extend(group)
                continue
            sums = []
            carries = []
            for a, b, c in zip(*group, strict=True):
                p = gate('xor', a, b)
                sums.append(gate('xor', p, c))
                carries.append(gate('or', gate('and', a, b), gate('and', p, c)))
            following.extend([sums, [packed.pop() if packed else 0] + carries[:-1]])
        summands = following
        tree_rounds += 1
    tree_ids = set(nodes)
    if len(summands) == 1:
        outputs = summands[0]
    else:
        aa, bb = summands
        carry_in = packed.pop() if packed else 0
        p = [gate('xor', a, b) for a, b in zip(aa, bb, strict=True)]
        initial = p.copy()
        g = [gate('and', a, b) for a, b in zip(aa, bb, strict=True)]
        g[0] = gate('or', g[0], gate('and', p[0], carry_in))
        levels = math.ceil(math.log2(width))
        for level in range(1, levels + 1):
            for j in range((1 << level) - 1, width, 1 << level):
                g[j] = gate('or', g[j], gate('and', p[j], g[j - (1 << (level - 1))]))
                p[j] = gate('and', p[j], p[j - (1 << (level - 1))])
        for level in range(levels, 0, -1):
            for j in range((1 << level) + (1 << (level - 1)) - 1, width, 1 << level):
                g[j] = gate('or', g[j], gate('and', p[j], g[j - (1 << (level - 1))]))
                p[j] = gate('and', p[j], p[j - (1 << (level - 1))])
        outputs = [gate('xor', initial[i], g[i - 1] if i else carry_in) for i in range(width)]
    if packed:
        raise ValueError('unconsumed generic compressor carry')
    return dict(nodes=nodes, leaves=leaves, outputs=outputs, tree_ids=tree_ids,
                tree_rounds=tree_rounds, column_inputs=mapping)


def features(width, terms, target):
    f = parent.features(width, terms, target)
    graph = circuit(width, terms)
    nodes = graph['nodes']
    live = set()
    depth = {0: 0, 1: 0}
    loads = {}

    def visit(node):
        loads[node] = loads.get(node, 0) + 1
        if node not in nodes:
            return 0
        if node in live:
            return depth[node]
        kind, a, b = nodes[node]
        live.add(node)
        depth[node] = max(visit(a), visit(b)) + 1
        return depth[node]

    for node in graph['outputs']:
        visit(node)
    work = {}
    for label, ids in [('tree', live & graph['tree_ids']), ('merge', live - graph['tree_ids'])]:
        for kind in ('xor', 'and', 'or'):
            work['word_' + label + '_' + kind] = float(sum(nodes[n][0] == kind for n in ids))
    work.update(word_live_logic=float(len(live)),
                word_logic_depth=float(max((depth.get(n, 0) for n in graph['outputs']), default=0)),
                word_tree_rounds=float(graph['tree_rounds']),
                word_log2_max_fanout=math.log2(max(loads.values(), default=0) + 1.),
                word_pressure_logic=len(live) * 1500. / target)
    for side in f.values():
        side.update(work)
    return f


def evaluate(width, terms, values):
    graph = circuit(width, terms)
    bits = {0: 0, 1: 1}
    for col, inputs in graph['column_inputs'].items():
        for rank, (source, bit) in enumerate(inputs):
            bits[graph['leaves'][col, rank]] = (values[source] >> bit) & 1
    for node, (kind, a, b) in graph['nodes'].items():
        aa, bb = bits[a], bits[b]
        bits[node] = aa ^ bb if kind == 'xor' else aa & bb if kind == 'and' else aa | bb
    return sum(bits[node] << i for i, node in enumerate(graph['outputs']))
