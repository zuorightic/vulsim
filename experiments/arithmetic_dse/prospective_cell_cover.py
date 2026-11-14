"""Deterministic single-output logical cell cover, before physical mapping.

Constants are from the frozen ASAP7 library after the flow's dont-use rules.
Interior signals may be absorbed only when their sole user is in the cut.
This models legal logical work, not ABC's chosen netlist or electrical size.
"""
import math

VERSION = 'asap7-legal-single-output-cover-v1'
AREA = {'and2': .08748, 'and3': .08748, 'and4': .10206, 'and5': .11664,
        'or2': .08748, 'or3': .08748, 'or4': .10206, 'or5': .11664,
        'nand2': .08748, 'nand3': .16038, 'nor2': .08748, 'nor3': .16038,
        'xor2': .16038, 'not': .04374, 'ao21': .08748, 'oa21': .10206,
        'aoi21': .11664, 'oai21': .11664}


def cover(circuit, outputs, *, witnesses=False):
    nodes = circuit.nodes
    live, users, pending = set(), {}, list(outputs)
    for n in outputs:
        users.setdefault(n, []).append(-1)
    while pending:
        n = pending.pop()
        if n not in nodes or n in live:
            continue
        live.add(n)
        kind, a, b = nodes[n]
        for child in (a,) if kind == 'not' else (a, b):
            users.setdefault(child, []).append(n)
            pending.append(child)
    primitive = {'and': AREA['and2'], 'or': AREA['or2'], 'xor': AREA['xor2'], 'not': AREA['not']}
    owned, chosen = set(), []
    for root in sorted(live, reverse=True):
        if root in owned:
            continue
        kind, a, b = nodes[root]
        candidates = [(kind if kind == 'not' else kind + '2', {root}, [a] if kind == 'not' else [a, b])]
        # Associative AND/OR cuts, absorbing only exclusive interior signals.
        if kind in ('and', 'or'):
            members, leaves = {root}, [a, b]
            for fanin in range(3, 6):
                eligible = [n for n in leaves if n in live and n not in owned
                            and nodes[n][0] == kind and len(users[n]) == 1]
                if not eligible:
                    break
                child = max(eligible)
                leaves.remove(child)
                members.add(child)
                leaves.extend(nodes[child][1:])
                candidates.append((kind + str(fanin), set(members), list(leaves)))
        # Two-level AO/OA and their complemented outputs.
        inverted = kind == 'not'
        outer = a if inverted else root
        if outer in live and (not inverted or len(users[outer]) == 1):
            op, u, v = nodes[outer]
            if op in ('and', 'or'):
                opposite = 'or' if op == 'and' else 'and'
                for inner, other in ((u, v), (v, u)):
                    if inner in live and inner not in owned and nodes[inner][0] == opposite and len(users[inner]) == 1:
                        name = ('oa' if op == 'and' else 'ao') + ('i21' if inverted else '21')
                        candidates.append((name, {root, outer, inner}, [*nodes[inner][1:], other]))
                if inverted:
                    name = ('nand' if op == 'and' else 'nor') + '2'
                    candidates.append((name, {root, outer}, [u, v]))
        eligible = []
        for name, members, leaves in candidates:
            if members & owned or any(any(user not in members for user in users[n]) for n in members if n != root):
                continue
            saving = math.fsum(primitive[nodes[n][0]] for n in members) - AREA[name]
            eligible.append((saving, len(members), name, members, leaves))
        _, _, name, members, leaves = max(eligible, key=lambda x: (x[0], x[1], x[2]))
        owned.update(members)
        chosen.append(dict(root=root, cell=name, members=sorted(members), inputs=leaves))
    if owned != live:
        raise ValueError('logical cover does not own every live gate exactly once')
    depth = {}
    for cut in reversed(chosen):
        depth[cut['root']] = 1 + max((depth.get(n, 0) for n in cut['inputs']), default=0)
    result = dict(area=math.fsum(AREA[c['cell']] for c in chosen), cells=float(len(chosen)),
                  depth=float(max((depth.get(n, 0) for n in outputs), default=0)),
                  wide_cells=float(sum(c['cell'] in ('and3', 'and4', 'and5', 'or3', 'or4', 'or5') for c in chosen)),
                  compound_cells=float(sum(c['cell'] in ('ao21', 'oa21', 'aoi21', 'oai21') for c in chosen)),
                  absorbed_gates=float(len(live) - len(chosen)))
    if witnesses:
        result['cuts'] = chosen
    return result
