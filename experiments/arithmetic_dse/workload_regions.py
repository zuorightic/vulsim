"""Conservative, exact additive-region demand from a prospective compiler DAG.

This discovers candidate geometry only. It neither changes RTL hierarchy nor
grants a G boundary price. Nonzero carry, shared interiors, truncation with
possible overflow, and known-one terms remain explicit boundaries.
"""
from collections import Counter
from . import reduction_mapping_features as geometry


def extract(graph, stages, state, target_ps):
    candidates = {n['id'] for n in graph.nodes if n['operation'] in ('add', 'adc')
                  and graph.demand[n['id']] and not n['constant']}
    zero_carry = {i for i in candidates if graph.nodes[i]['operation'] == 'add'
                  or graph.operand(graph.nodes[i]['operands'][2]) == ('0',)}
    users = {i: set() for i in zero_carry}
    for n in graph.nodes:
        if not graph.demand[n['id']] or n['constant']:
            continue
        for a in n['operands']:
            if a['node'] is not None:
                for bit in graph.operand(a):
                    if isinstance(bit, tuple) and bit[0] in users and bit[0] != n['id']:
                        users[bit[0]].add(n['id'])
    observed = set()
    for slot in state['slots']:
        if slot['valid'] or not slot['variable_bits']:
            continue
        for bit in graph.origins(slot['origin']):
            if isinstance(bit, tuple) and bit[0] in zero_carry and slot['stage'] == stages[bit[0]] + 1:
                observed.add(bit[0])

    def no_overflow(i):
        n = graph.nodes[i]
        maximum = 0
        for a in n['operands'][:2]:
            maximum += sum((value != '0') << b for b, value in enumerate(graph.operand(a)))
        return maximum < 1 << n['width']

    consumed = set()
    rows = []
    # Process downstream nodes first so an interior cannot get a second owner.
    order, visiting = [], set()

    def visit(i):
        if i in visiting:
            return
        visiting.add(i)
        for a in graph.nodes[i]['operands']:
            if a['node'] is not None:
                visit(a['node'])
        order.append(i)

    for i in sorted(zero_carry):
        visit(i)
    for root in reversed(order):
        if root not in zero_carry or root in consumed:
            continue
        width = max(graph.demand[root]) + 1
        members = {root}
        terms = []
        reasons = []

        def operands(i, offset):
            for a in graph.nodes[i]['operands'][:2]:
                mapped = graph.operand(a)
                leaves = []
                groups = {}
                for col, bit in enumerate(mapped):
                    if col + offset >= width or bit == '0':
                        continue
                    if bit == '1':
                        reasons.append('known-one summand requires successor geometry semantics')
                        continue
                    groups.setdefault(bit[0], []).append((bit[1], col + offset))
                for child, pairs in groups.items():
                    shifts = {column - bit for bit, column in pairs}
                    shift = next(iter(shifts)) if len(shifts) == 1 else -1
                    child_width = graph.nodes[child]['width']
                    # A child modular sum can only be flattened when discarded
                    # carry is also discarded by the root, or cannot occur.
                    flatten = (child in zero_carry and child not in consumed and child not in observed
                               and stages[child] == stages[root] and len(users[child]) == 1
                               and 0 <= shift < width and (child_width + shift >= width or no_overflow(child)))
                    expected = {(b, b + shift) for b, value in enumerate(graph.origins(child))
                                if value != '0' and b + shift < width}
                    if flatten and set(pairs) == expected:
                        members.add(child)
                        operands(child, shift)
                    else:
                        leaves += [[child, bit, column] for bit, column in pairs]
                if leaves:
                    terms.append(leaves)

        operands(root, 0)
        consumed |= members
        if len(members) < 2:
            continue  # Standalone Add remains an operator, never duplicate G.
        row = dict(root=root, stage=stages[root], output_bits=width, members=sorted(members), terms=terms,
                   ownership='proposed region replaces member Add prices only after matching emitter/boundary qualification',
                   price_qualification_granted=False, effective_RTL_region_installed=False)
        try:
            if reasons:
                raise ValueError('; '.join(sorted(set(reasons))))
            row['features'] = geometry.features(width, terms, target_ps)
            row['geometry_status'] = 'represented'
        except (ValueError, KeyError, TypeError, OverflowError) as error:
            row['geometry_status'] = 'needs_successor'
            row['reason'] = str(error)
        rows.append(row)
    counts = Counter(n for r in rows for n in r['members'])
    if any(c > 1 for c in counts.values()):
        raise ValueError('overlapping G ownership')
    return dict(regions=rows, disjoint_members_checked=True,
                nonzero_carry_nodes=sorted(candidates - zero_carry),
                area_or_timing_prices_requested=False, boundary_qualification_granted=False)
