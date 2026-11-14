"""Logical fanout moments from semantic graphs, before technology mapping.

Loads count live gate-input uses plus requested output observations. They
are structural work proxies, not electrical fanout, capacitance or buffers.
"""
from collections import Counter
import math
from . import load_pressure_features_v7 as previous
from . import flow_structure_features_v4 as circuits

VERSION = 'semantic-fanout-prospective-features-v8'
base_state_controls = previous.base_state_controls


def load_moments(loads):
    values = [int(n) for n in loads if n > 0]
    mass = sum(values)
    square = sum(n * n for n in values)
    return dict(log2_mass=math.log2(mass + 1.),
                log2_concentration=math.log2(1. + square / max(1, mass)),
                log2_effective_drivers=math.log2(1. + mass * mass / max(1, square)),
                log2_repair_excess=math.log2(1. + sum(max(0, n - 4) for n in values)),
                shared_fraction=sum(n > 1 for n in values) / max(1, len(values)))


def graph_loads(circuit, outputs):
    live, pending, loads = set(), list(outputs), Counter()
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
    roots = set(circuit.leaves.values())
    result = {}
    for group, nodes in [('root', roots), ('internal', live)]:
        result.update({group + '_' + name: value for name, value in load_moments(loads[n] for n in nodes).items()})
    return result


def operator_features(query):
    result = previous.operator_features(query)
    circuit, outputs = circuits.operator_circuit(query['local_context']['producer'])
    extra = {'fanout_' + k: v for k, v in graph_loads(circuit, outputs).items()}
    extra['fanout_repair_pressure'] = extra['fanout_internal_log2_repair_excess'] * result['clock_pressure']
    extra['fanout_root_T'] = extra['fanout_root_log2_concentration'] * result['log2_target']
    result.update(extra)
    return result


def reduction_features(query):
    result = previous.reduction_features(query)
    extra = {}
    for serial in (False, True):
        circuit, outputs, _ = circuits.reduction_circuit(query, serial=serial)
        prefix = 'serial_' if serial else 'fused_'
        extra.update({prefix + k: v for k, v in graph_loads(circuit, outputs).items()})
    extra = {'fanout_' + k: v for k, v in extra.items()}
    extra['fanout_repair_pressure'] = extra['fanout_fused_internal_log2_repair_excess'] * result['intensive']['clock_pressure']
    extra['fanout_serial_concentration_gap'] = extra['fanout_serial_internal_log2_concentration'] - extra['fanout_fused_internal_log2_concentration']
    for values in result.values():
        values.update(extra)
    return result


def state_controls(structure, context_function):
    controls = previous.state_controls(structure, context_function)
    roots = Counter(root for sink in structure['input_sink_inputs'] for root in sink)
    pairs = Counter(tuple(sorted(sink)) for sink in structure['input_sink_inputs'])
    extra = {'input_' + k: v for k, v in load_moments(roots.values()).items()}
    extra['input_pair_reuse_fraction'] = (sum(pairs.values()) - len(pairs)) / max(1, sum(pairs.values()))
    for query in controls:
        f = query['features']
        native, reset, logt = f['branch_native'], f['reset_has_one'], f['log2_target']
        f.update(extra)
        for name in ['input_log2_concentration', 'input_pair_reuse_fraction', 'input_log2_repair_excess']:
            f['native_' + name] = native * extra[name]
            f['reset_' + name] = reset * extra[name]
        f['input_concentration_log_T'] = extra['input_log2_concentration'] * logt
        f['native_input_concentration_log_T'] = native * extra['input_log2_concentration'] * logt
    return controls
