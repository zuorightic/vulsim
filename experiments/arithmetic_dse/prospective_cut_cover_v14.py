"""Bounded Boolean cut covering of prospective DAGs, with shared outputs.

The caller supplies frozen single-output Liberty truth tables and areas. Cuts
may overlap: a live internal signal can remain a separately mapped root while
also being absorbed in another cell. Area counts the selected physical roots,
including explicit output inversion, once each. This is a work proxy, not an
ABC replica, a timing mapper, or a physical area prediction.

There is no I/O, process creation, model fitting, or measured-netlist input.
"""
from collections import Counter
from functools import lru_cache
from itertools import permutations
import ast
import math

VERSION = 'bounded-shared-DAG-cut-cover-v14'
MAX_INPUTS = 4
CUT_LIMIT = 16
FLOW_PASSES = 3


def expression(text, values, mask):
    """Evaluate the supported Liberty Boolean grammar on bit-packed vectors."""
    tree = ast.parse(text.replace('*', '&').replace('+', '|').replace('!', '~'), mode='eval')

    def walk(node):
        if isinstance(node, ast.Name):
            return values[node.id]
        if isinstance(node, ast.Constant) and type(node.value) is int and node.value in (0, 1):
            return mask if node.value else 0
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Invert):
            return mask ^ walk(node.operand)
        if isinstance(node, ast.BinOp) and type(node.op) in (ast.BitAnd, ast.BitOr, ast.BitXor):
            a, b = walk(node.left), walk(node.right)
            return a & b if isinstance(node.op, ast.BitAnd) else a | b if isinstance(node.op, ast.BitOr) else a ^ b
        raise ValueError('unsupported Liberty Boolean grammar')

    return walk(tree.body) & mask


def variable(index, count):
    return sum(((assignment >> index) & 1) << assignment for assignment in range(1 << count))


def library_table(cells):
    """Compile already-filtered library constants; retain pin-binding witnesses."""
    table = {(1, 2): dict(area=0., cell='wire', inputs=['A'], permutation=[0], invert=False)}
    inverters = [c for c in cells if len(c['inputs']) == 1 and c['truth'] == 1]
    if not inverters:
        raise ValueError('a legal inverter is required')
    inv = min(inverters, key=lambda c: (c['area_um2'], c['cell']))
    for cell in cells:
        count = len(cell['inputs'])
        if not 1 <= count <= MAX_INPUTS or not math.isfinite(cell['area_um2']) or cell['area_um2'] <= 0:
            raise ValueError('bounded positive single-output library constants required')
        mask = (1 << (1 << count)) - 1
        if not 0 <= cell['truth'] <= mask:
            raise ValueError('invalid library truth table')
        for order in permutations(range(count)):
            truth = 0
            for assignment in range(1 << count):
                native = sum(((assignment >> order[i]) & 1) << i for i in range(count))
                truth |= ((cell['truth'] >> native) & 1) << assignment
            for invert in (False, True):
                key = count, truth ^ (mask if invert else 0)
                candidate = dict(area=cell['area_um2'] + (inv['area_um2'] if invert else 0.),
                    cell=cell['cell'], inputs=cell['inputs'], permutation=list(order), invert=invert,
                    inverter=inv['cell'] if invert else None)
                rank = lambda c: (c['area'], c['invert'], c['cell'], c['permutation'])
                if key not in table or rank(candidate) < rank(table[key]):
                    table[key] = candidate
    return table


def live_graph(circuit, outputs):
    live, pending, users = set(), list(outputs), Counter(outputs)
    while pending:
        node = pending.pop()
        if node in live or node not in circuit.nodes:
            continue
        live.add(node)
        kind, a, b = circuit.nodes[node]
        children = (a,) if kind == 'not' else (a, b)
        users.update(children)
        pending.extend(children)
    for node in live:
        if any(child >= node for child in circuit.nodes[node][1:] if child in circuit.nodes):
            raise ValueError('topologically ordered acyclic prospective DAG required')
    return live, users


def cut_truth(circuit, root, leaves):
    """Exact local truth function; leaf identifiers carry no numerical meaning."""
    count = len(leaves)
    mask = (1 << (1 << count)) - 1
    terminal = {node: variable(i, count) for i, node in enumerate(leaves)}

    @lru_cache(maxsize=None)
    def visit(node):
        if node < 2:
            return mask if node else 0
        if node in terminal:
            return terminal[node]
        if node not in circuit.nodes:
            raise ValueError('cut does not separate the root from primary inputs')
        kind, a, b = circuit.nodes[node]
        x = visit(a)
        if kind == 'not':
            return x ^ mask
        y = visit(b)
        return x & y if kind == 'and' else x | y if kind == 'or' else x ^ y

    return visit(root)


def cover(circuit, outputs, table, *, witnesses=False):
    live, users = live_graph(circuit, outputs)
    cuts = {n: [(n,)] for n in circuit.leaves.values()}
    cuts.update({0: [()], 1: [()]})
    options, combinations, truncated = {}, 0, 0
    for node in sorted(live):
        kind, a, b = circuit.nodes[node]
        children = (a,) if kind == 'not' else (a, b)
        unions = set(cuts[children[0]]) if len(children) == 1 else set()
        if len(children) == 2:
            for left in cuts[a]:
                for right in cuts[b]:
                    combinations += 1
                    leaves = tuple(sorted(set(left) | set(right)))
                    if len(leaves) <= MAX_INPUTS:
                        unions.add(leaves)
        immediate = tuple(sorted(set(children) - {0, 1}))
        ordered = sorted(unions, key=lambda c: (len(c), c))
        selected = ordered[:CUT_LIMIT]
        if immediate not in selected:
            selected = selected[:CUT_LIMIT-1] + [immediate]
        truncated += max(0, len(ordered)-len(selected))
        cuts[node] = [(node,)] + selected
        options[node] = []
        for leaves in selected:
            truth = cut_truth(circuit, node, leaves)
            match = table.get((len(leaves), truth))
            if match is not None:
                options[node].append(dict(root=node, leaves=list(leaves), truth=truth, **match))
        if not options[node]:
            raise ValueError('no legal library cover for a prospective primitive')
    refs = dict(users)
    chosen, active, depth = {}, set(), {}
    for _ in range(FLOW_PASSES):
        flow = {}
        for node in sorted(live):
            def rank(cut):
                cost = cut['area'] + math.fsum(flow.get(n, 0.) for n in cut['leaves'])
                levels = (cut['cell'] != 'wire') + cut['invert'] + max((depth.get(n, 0) for n in cut['leaves']), default=0)
                return cost, levels, len(cut['leaves']), cut['cell'], cut['leaves']
            cut = min(options[node], key=rank)
            chosen[node] = cut
            flow[node] = rank(cut)[0] / max(1., refs.get(node, 1))
            depth[node] = rank(cut)[1]
        active, pending, refs = set(), list(outputs), Counter(outputs)
        while pending:
            node = pending.pop()
            if node not in chosen or node in active:
                continue
            active.add(node)
            refs.update(chosen[node]['leaves'])
            pending.extend(chosen[node]['leaves'])
    selected = [chosen[n] for n in sorted(active)]
    histogram = Counter(c['cell'] for c in selected if c['cell'] != 'wire')
    histogram.update(c['inverter'] for c in selected if c['invert'])
    # Report coverage of semantic interior gates; overlaps are legal cloning,
    # not an assertion of disjoint Boolean-gate ownership.
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
        cells=sum(histogram.values()), depth=max((depth.get(n, 0) for n in outputs), default=0),
        mapped_roots=len(active), shared_roots=sum(refs[n] > 1 for n in active),
        overlapping_interior_gates=sum(v > 1 for v in interiors.values()),
        absorbed_gate_instances=sum(interiors.values())-len(active),
        primitive_gates=len(live), candidate_combinations=combinations, truncated_cuts=truncated,
        max_inputs=MAX_INPUTS, cut_limit=CUT_LIMIT, flow_passes=FLOW_PASSES,
        histogram=dict(sorted(histogram.items())), physical_timing_modeled=False)
    if witnesses:
        result.update(cuts=selected, outputs=list(outputs))
    return result


def verify(circuit, outputs, mapped, table):
    """Prove every emitted cut locally, and complete reachability/area globally."""
    if list(outputs) != mapped['outputs']:
        raise ValueError('mapped output boundary changed')
    cuts = {c['root']: c for c in mapped['cuts']}
    if len(cuts) != len(mapped['cuts']):
        raise ValueError('duplicate mapped root')
    for root, cut in cuts.items():
        truth = cut_truth(circuit, root, cut['leaves'])
        match = table.get((len(cut['leaves']), truth))
        if match is None or any(cut[k] != v for k, v in match.items()) or cut['truth'] != truth:
            raise ValueError('mapped cut disagrees with the legal Boolean cell')
    seen, pending = set(), list(outputs)
    while pending:
        node = pending.pop()
        if node < 2 or node in circuit.leaves.values() or node in seen:
            continue
        if node not in cuts:
            raise ValueError('missing live mapped root')
        seen.add(node)
        pending.extend(cuts[node]['leaves'])
    if seen != set(cuts) or not math.isclose(mapped['area'], math.fsum(c['area'] for c in cuts.values()), abs_tol=1e-12):
        raise ValueError('mapped area/reachability does not conserve selected roots')
    return len(cuts)
