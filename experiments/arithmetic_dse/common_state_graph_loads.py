"""Logical service-output loads from a typed graph and materialized placement.

This supplies the same numerical load proxy used by state-bank experiments.
It does not estimate mapped capacitance or qualify a new arithmetic boundary.
"""
from .common_state_features import input_load_features


def features(export, placement, state_query, control_nodes=()):
    graph = export['graph']
    nodes = {n['id']: n for n in graph['nodes']}
    if (not state_query['materialized_checked'] or
            state_query['graph_sha256'] != graph['graph_sha256'] or
            len(placement) != len(nodes)):
        raise ValueError('matching actual graph, placement and state required')
    controls = set(control_nodes)
    controls.update(s['origin'] for s in state_query['slots'] if s['valid'])
    roots = {}
    widths = []
    for port in export['ports']:
        if not port['input']:
            continue
        if len(port['nodes']) != 1:
            raise ValueError('first logical load scope requires scalar ports')
        at = port['nodes'][0]
        if at in controls:
            continue
        n = nodes[at]
        known = set(n['known_zero']) | set(n['known_one'])
        bits = [i for i in range(n['width']) if i not in known]
        if bits:
            offset = sum(widths)
            roots.update({(at, bit): offset + i for i, bit in enumerate(bits)})
            widths.append(len(bits))
    if sum(widths) + 1 != state_query['input_variable_bits']:
        raise ValueError('logical service data/valid census mismatch')
    memo = {}
    visiting = set()

    def origins(at):
        if at in memo:
            return memo[at]
        if at in visiting:
            raise ValueError('cyclic pure bit wiring')
        visiting.add(at)
        n = nodes[at]
        kind, width = n['kind'], n['width']

        def operand(a):
            if a.get('signed'):
                raise ValueError('signed load mapping needs a separate contract')
            if a['kind'] == 'symbol':
                return origins(a['node'])
            if a['kind'] == 'literal':
                return [None] * a['width']
            raise ValueError('unregistered pure wiring operand')

        if kind == 'input':
            values = [roots.get((at, i)) for i in range(width)]
        elif kind in ('mul', 'add', 'addcarry', 'constant'):
            values = [None] * width
        elif kind in ('assign', 'cast', 'zext', 'trunc'):
            values = (operand(n['operands'][0]) + [None] * width)[:width]
        elif kind == 'concat':
            values = [b for a in reversed(n['operands']) for b in operand(a)]
        elif kind == 'slice':
            values = operand(n['operands'][0])[n['lo']:n['hi'] + 1]
        elif kind == 'bit_select' and n['bit'] >= 0:
            values = operand(n['operands'][0])[n['bit']:n['bit'] + 1]
        else:
            raise ValueError('unregistered service load wiring: ' + kind)
        if len(values) != width:
            raise ValueError('incomplete pure bit load mapping')
        known = set(n['known_zero']) | set(n['known_one'])
        memo[at] = [None if i in known else b for i, b in enumerate(values)]
        visiting.remove(at)
        return memo[at]

    sinks = []
    arithmetic = captures = 0
    for at, n in nodes.items():
        if n['kind'] not in ('mul', 'add', 'addcarry') or placement[at] != 0:
            continue
        for a in n['operands']:
            if a['kind'] != 'symbol':
                continue
            for bit in origins(a['node'])[:min(a['width'], n['width'])]:
                if bit is not None:
                    sinks.append([bit])
                    arithmetic += 1
    for slot in state_query['slots']:
        if slot['valid'] or slot['stage'] != 1:
            continue
        mask = sum(int(limb, 16) << (64 * i)
                   for i, limb in enumerate(slot['variable_mask_hex']))
        for i, bit in enumerate(origins(slot['origin'])):
            if bit is not None and (mask >> i) & 1:
                sinks.append([bit])
                captures += 1
    return dict(features=input_load_features(widths, sinks),
                arithmetic_operand_pin_uses=arithmetic,
                first_capture_pin_uses=captures,
                variable_input_widths=widths,
                mapped_capacitance_qualified=False,
                actual_arithmetic_S_qualified=False)
