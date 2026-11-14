"""Logical load on paths and signed affine incidence, before mapping.

The path work is a unit gate/load proxy, not an STA result. Phase incidence
counts logical uses; it does not recover mapped pin caps or transition slack.
"""
from collections import Counter
import math
from . import semantic_reset_features_v9 as previous
from . import semantic_fanout_features_v8 as fanout
from . import centered_response as response

VERSION = 'transition-incidence-prospective-features-v10'
SEMANTICS = previous.SEMANTICS
state_structure = previous.state_structure
validate_semantics = previous.validate_semantics


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


def signed_incidence(roots, words, sink_inputs):
    """Root-reset / result-reset / affine-invert joint incidence moments.

    All root names and raw masks are eliminated from the returned numbers.
    A high-degree root with one phase can differ from a high-degree root with
    both phases even when total resets and global invert popcounts agree.
    """
    packed = [b for group in roots for b in group]
    by_phase, by_root, by_output = Counter(), Counter(), Counter()
    count = offset = mixed = 0
    for word in words:
        for reset, invert in zip(word['reset_bits'], word['invert_bits'], strict=True):
            for root in sink_inputs[offset]:
                by_phase[root, invert] += 1
                by_root[root] += 1
                by_output[root, reset] += 1
                mixed += packed[root] != reset
                count += 1
            offset += 1
    if offset != len(sink_inputs):
        raise ValueError('signed incidence dimensions differ')
    phase_mass = sum(n*n for n in by_phase.values())
    root_mass = sum(n*n for n in by_root.values())
    reset_mass = [sum(n*n for root,n in by_root.items() if packed[root] == bit) for bit in (0,1)]
    degree = max(by_root.values(), default=0)
    return dict(log2_phase_concentration=math.log2(1. + phase_mass / max(1,count)),
                phase_split_fraction=(root_mass-phase_mass) / max(1,root_mass),
                phase_root_skew=sum(abs(by_phase[root,0]-by_phase[root,1]) for root in by_root) / max(1,count),
                output_phase_split_fraction=sum(min(by_output[root,0],by_output[root,1]) for root in by_root) / max(1,count),
                reset_cross_fraction=mixed / max(1,count),
                reset_degree_second_imbalance=abs(reset_mass[1]-reset_mass[0]) / max(1,root_mass),
                reset_one_degree_second_fraction=reset_mass[1] / max(1,root_mass),
                log2_peak_root_degree=math.log2(1. + degree))


def base_state_controls(query):
    roots, words = validate_semantics(query)
    result = previous.base_state_controls(query)
    global_work = signed_incidence(roots, words, query['input_sink_inputs'])
    for control in result:
        f = control['features']
        f.update({'phase_' + name: value for name,value in global_work.items()})
        for name in ('log2_phase_concentration', 'phase_split_fraction', 'reset_cross_fraction',
                     'reset_degree_second_imbalance', 'reset_one_degree_second_fraction'):
            value = global_work[name]
            f['phase_native_' + name] = value * f['branch_native']
            f['phase_T_' + name] = value * f['log2_target']
    return result


def state_controls(query, context_function):
    controls = base_state_controls(query)
    enable = {q['stage']:response.predict(context_function,q['features']) for q in controls if q['path_class']=='native_enable'}
    if not enable or any(not math.isfinite(v) or v <= 0 for v in enable.values()):
        raise ValueError('nonpositive predicted enable context')
    target = query['target_ps']
    for q in controls:
        f = q['features']; value = enable[min(q['stage'],max(enable))]
        pressure = math.log2(1+value/target)
        relaxation = (.25*max(0.,target-value)+.01*value)/target
        native, reset = f['branch_native'],f['reset_has_one']
        f.update(enable_context_R_ps=value,predicted_enable_pressure=pressure,
                 native_enable_pressure=native*pressure,reset_enable_pressure=reset*pressure,
                 native_reset_enable_pressure=native*reset*pressure,predicted_enable_relaxation=relaxation,
                 native_enable_relaxation=native*relaxation)
    return controls


def operator_features(query):
    f = previous.operator_features(query)
    circuit, outputs = fanout.circuits.operator_circuit(query['local_context']['producer'])
    extra = path_load_work(circuit, outputs)
    f.update({'path_' + k:v for k,v in extra.items()})
    f['path_pressure'] = extra['log2_path_load_work'] * f['clock_pressure']
    return f


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
