"""Prospective carry geometry and state source distribution for W3--W5.

These are logical work proxies. They contain no mapped cells, capacitance,
physical coordinates, measured timing, source names, or exact-period routing.
The predecessor emitters and measurement ownership contracts are preserved.
"""
import math
from . import operator_function_successor as operator
from . import wide_alu_geometry as alu
from . import reduction_mapping_features as reduction
from . import state_control_distribution as state
from . import common_state_features as loads

VERSION = 'common-prospective-mechanism-features-v1'


def carry_geometry(heights):
    """Potential carry reach through occupied input columns, including gaps.

    A column with two or more operands can generate carry. One operand can
    propagate it; an empty column absorbs it. This describes original input
    columns for both dense and sparse reductions, rather than mapped topology.
    """
    reach = longest = single = propagated = runs = 0
    previous_overlap = False
    for height in heights:
        overlap = height >= 2
        runs += int(overlap and not previous_overlap)
        previous_overlap = overlap
        if overlap or (height == 1 and reach):
            reach += 1
            longest = max(longest, reach)
            propagated += 1
            single += int(height == 1)
        else:
            reach = 0
    return dict(log2_carry_reach=math.log2(longest + 1.),
                carry_single_fraction=single / max(1, propagated),
                log2_overlap_runs=math.log2(runs + 1.))


def operator_features(query):
    f = operator.features(query)
    spec = query['local_context']['producer']
    g = alu.geometry(spec)
    a, b = (set(g['used'][k]) for k in ('lhs', 'rhs'))
    width = spec['arithmetic_width']
    c = carry_geometry([int(i in a) + int(i in b) for i in range(width)])
    f.update(alu_overlap_fraction=len(a & b) / max(1, len(a | b)),
             alu_carry_reach_fraction=(2. ** c['log2_carry_reach'] - 1.) / width)
    return f


def reduction_features(query):
    f = reduction.features(query['output_bits'], query['terms'], query['target_ps'])
    heights = [0] * query['output_bits']
    for term in query['terms']:
        for _, _, column in term:
            heights[column] += 1
    extra = carry_geometry(heights)
    f['intensive'].update(extra)
    # Support uses the same prospective geometry, never the numerical target
    # itself as a nearest-source identity.
    f['area'].update(extra)
    f['delay'].update(extra)
    return f


def state_structure(spec, target):
    s = state.structure(spec, target)
    s['input_reset_one_bits'] = sum(r['reset'].bit_count() for r in spec['roots'])
    return s


def state_controls(structure):
    controls = state.controls(structure)
    widths = structure['input_widths']
    reset = structure['input_reset_one_bits']
    if type(reset) is not int or not 0 <= reset <= sum(widths):
        raise ValueError('explicit input reset polarity required')
    f = loads.input_load_features(widths, structure['input_sink_inputs'])
    result = []
    for control in controls:
        q = dict(control)
        values = dict(q['features'])
        stage = q['stage']
        if q['control_source'] in ('port_iv', 'service_valid'):
            fraction = reset / sum(widths)
        else:
            # The final native valid source launches the external bank.
            source_stage = min(max(stage - 1, 0), len(structure['stage_words']) - 1)
            bits = sum(structure['stage_words'][source_stage])
            fraction = structure['stage_reset_one_bits'][source_stage] / max(1, bits)
        values.update(source_root_spread=math.sqrt(f['input_loaded_bits']),
                      source_log_input_max_load=math.log2(f['input_max_bit_load'] + 1.),
                      source_mean_log_input_load=f['input_log_load_sum'] / max(1, f['input_loaded_bits']),
                      source_reset_one_fraction=fraction)
        q['features'] = values
        result.append(q)
    return result
