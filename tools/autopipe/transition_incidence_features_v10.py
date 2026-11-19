"""Frozen v10 runtime functions; extracted without numerical edits from transition_incidence_features_v10.py."""
from collections import Counter

import math

from . import semantic_reset_features_v9 as previous

from . import semantic_fanout_features_v8 as fanout

def path_load_work(circuit, outputs):
    live, loads, pending = set(), Counter(), list(outputs)
    while pending:
        node = pending.pop()
        if node < 2:
            continue
        loads[node] += 1
        if node not in circuit.nodes or node in live:
            continue
        live.add(node)
        kind, a, b = circuit.nodes[node]
        pending.append(a)
        if kind != 'not':
            pending.append(b)
    weighted, depth = {}, {}
    for node in sorted(live):
        kind, a, b = circuit.nodes[node]
        children = [a] if kind == 'not' else [a, b]
        # One unit per gate plus logical output-use pressure at that gate.
        weighted[node] = max((weighted.get(n, 0.) for n in children), default=0.) + 1. + math.log2(1. + loads[node])
        depth[node] = 1 + max((depth.get(n, 0) for n in children), default=0)
    peak = max((weighted.get(n, 0.) for n in outputs), default=0.)
    longest = max((depth.get(n, 0) for n in outputs), default=0)
    return dict(log2_path_load_work=math.log2(1. + peak),
                path_load_depth_ratio=peak / max(1, longest),
                log2_peak_internal_uses=math.log2(1. + max((loads[n] for n in live), default=0)),
                shared_internal_use_fraction=sum(max(0, loads[n]-1) for n in live) / max(1, sum(loads[n] for n in live)))


def reduction_features(query):
    result = previous.reduction_features(query)
    extra = {}
    for serial in (False, True):
        circuit, outputs, _ = fanout.circuits.reduction_circuit(query, serial=serial)
        extra.update({'path_' + ('serial_' if serial else 'fused_') + k:v for k,v in path_load_work(circuit,outputs).items()})
    extra['path_serial_work_gap'] = extra['path_serial_log2_path_load_work'] - extra['path_fused_log2_path_load_work']
    extra['path_pressure'] = extra['path_fused_log2_path_load_work'] * result['intensive']['clock_pressure']
    for values in result.values():
        values.update(extra)
    return result
