"""Frozen v10 runtime functions; extracted without numerical edits from workload_abcd.py."""
from functools import lru_cache

from .workload_demand import WIRE

STATIC_VERSION = 'fixed-op-width-workload-v2'


def static_node(graph, node):
    """Prescribed weights on actual, live compiler nodes, including G members."""
    i, op = node['id'], node['operation']
    if not graph.demand[i] or node['constant'] or op in WIRE | {'input'} or graph.wire_equivalent(i):
        return 0.
    if op == 'mul':
        width = max(map(graph.billing, node['operands'][:2]))
        if not 1 <= width <= 4096:
            raise ValueError('static successor input width outside 1..4096')
        bucket = 1 << (width - 1).bit_length()
        return float(max(1, bucket // 2))
    if op in ('shl', 'shr'):
        a = node['operands'][1]
        return 0. if a['node'] is None or graph.nodes[a['node']]['constant'] else 2.
    if op in {'add', 'adc', 'sub', 'ult', 'ule', 'ugt', 'uge', 'eq', 'ne', 'mux',
              'and', 'or', 'xor', 'not', 'lnot', 'land', 'lor', 'neg'}:
        return 1.
    raise ValueError('unpriced static operation: ' + op)


def dag_timing(graph, placement, delays, state, L):
    """Parallel max, serial sum; a saved value starts a new timing cone.

    Data capture endpoints come from the materialized state layout, rather
    than an assumption that every operation ends a stage.
    """
    active = set()

    @lru_cache(None)
    def arrival(i):
        if i in active:
            raise ValueError('cyclic compiler graph')
        active.add(i)
        n = graph.nodes[i]
        upstream = max((arrival(a['node']) for a in n['operands']
                        if a['node'] is not None and placement[a['node']] == placement[i]), default=0.)
        active.remove(i)
        return upstream + delays.get(i, 0.)

    stages = [0.] * L
    for slot in state['slots']:
        if slot['valid'] or not slot['variable_bits']:
            continue
        origin, capture = slot['origin'], slot['stage'] - 1
        if not 0 <= capture < L or placement[origin] > capture:
            raise ValueError('capture inconsistent with actual placement')
        # Repeated pass-through banks are new register-to-register paths.
        value = arrival(origin) if placement[origin] == capture else 0.
        stages[capture] = max(stages[capture], value)
    return stages


def static_cost(graph, view, state, L):
    weights = {n['id']: static_node(graph, n) for n in graph.nodes}
    stages = dag_timing(graph, view['placement'], weights, state, L)
    f = state['features']
    comb = sum(weights.values())
    return dict(version=STATIC_VERSION, stage_delay_weights=stages,
                maximum_stage_abstract_delay=max(stages), comb_weight=comb,
                saved_bits=f['state_bits'], saved_signals=f['state_signals'],
                comb_weight_plus_saved_bits=comb + f['state_bits'])


def static_score(row):
    c = row['static']
    return (c['maximum_stage_abstract_delay'], c['comb_weight_plus_saved_bits'],
            c['saved_bits'], c['saved_signals'], row['structure'], int(row['view']))
