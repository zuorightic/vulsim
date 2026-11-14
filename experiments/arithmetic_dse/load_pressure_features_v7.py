"""Semantic carry geometry and a one-way predicted enable-pressure context.

The context is a frozen shared numerical function. Neither measured slack nor
mapped loading participates. Its training must exclude each held-out bank.
"""
import math
from . import rebuffer_context_features_v6 as previous
from . import centered_response as response

VERSION = 'load-pressure-prospective-features-v7'
base_state_controls = previous.state_controls


def carry_context(heights):
    active = overlap = tails = gaps = reaches = longest = 0
    for height in heights:
        active += height > 0
        overlap += height >= 2
        gaps += height == 0
        if height >= 2:
            reaches += 1
        elif height == 1 and reaches:
            reaches += 1
            tails += 1
        else:
            reaches = 0
        longest = max(longest, reaches)
    return dict(carry_tail_fraction=tails / max(1, active),
                log2_carry_tail_bits=math.log2(tails + 1.),
                variable_gap_fraction=gaps / max(1, len(heights)),
                carry_reach_fraction=longest / max(1, len(heights)))


def operator_features(query):
    f = previous.operator_features(query)
    spec = query['local_context']['producer']
    circuit, _ = previous.ripple_operator_circuit(spec)
    columns = [0] * spec['arithmetic_width']
    for name, bit in circuit.leaves:
        if name in ('lhs', 'rhs'):
            columns[bit] += 1
    f.update(carry_context(columns))
    f.update(cover_to_ripple_logratio=math.log2(max(1e-9, f['cover_area']) / max(1e-9, f['ripple_cover_area'])),
             carry_tail_pressure=f['carry_tail_fraction'] * f['clock_pressure'])
    return f


def reduction_features(query):
    result = previous.reduction_features(query)
    columns = [0] * query['output_bits']
    for term in query['terms']:
        for _, _, bit in term:
            columns[bit] += 1
    z = result['intensive']
    extra = carry_context(columns)
    extra.update(cover_to_ripple_logratio=math.log2(max(1e-9, z['cover_fused_area']) / max(1e-9, z['ripple_cover_fused_area'])),
                 log2_serial_area_inflation=math.log2((z['cover_serial_area'] + 1.) / (z['cover_fused_area'] + 1.)),
                 carry_tail_pressure=extra['carry_tail_fraction'] * z['clock_pressure'])
    for f in result.values():
        f.update(extra)
    return result


def state_controls(structure, context_function):
    controls = base_state_controls(structure)
    enable = {}
    for q in controls:
        if q['path_class'] == 'native_enable':
            value = response.predict(context_function, q['features'])
            if not math.isfinite(value) or value <= 0:
                raise ValueError('nonpositive predicted enable context')
            enable[q['stage']] = value
    if not enable:
        raise ValueError('missing native enable context')
    target = structure['target_ps']
    for q in controls:
        f = q['features']
        value = enable[min(q['stage'], max(enable))]
        pressure = math.log2(1. + value / target)
        # Source-inspired relaxation proxy, not OpenROAD's actual target slack.
        relaxation = (.25 * max(0., target - value) + .01 * value) / target
        native, reset = f['branch_native'], f['reset_has_one']
        f.update(enable_context_R_ps=value,
                 predicted_enable_pressure=pressure,
                 native_enable_pressure=native * pressure,
                 reset_enable_pressure=reset * pressure,
                 native_reset_enable_pressure=native * reset * pressure,
                 predicted_enable_relaxation=relaxation,
                 native_enable_relaxation=native * relaxation)
    return controls
