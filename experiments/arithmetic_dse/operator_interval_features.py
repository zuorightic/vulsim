"""Live bit geometry and consumer pin load from an ordinary OperatorQuery.

This successor leaves the published feature functions unchanged. The output
contains numerical descriptors, not measured capacitance or qualified prices.
"""
import math
from .common_operator_features import features as previous_features

VERSION = 'operator-live-interval-load-features-v2'


def variable_positions(spec, prefix, result_width):
    width = spec[prefix + '_width']
    zero = int(spec.get(prefix + '_zero_hex', '0x0'), 16)
    one = int(spec.get(prefix + '_one_hex', '0x0'), 16)
    if zero & one or (zero | one) >> width:
        raise ValueError('invalid known operand bits')
    return {i for i in range(min(width, result_width))
            if not ((zero | one) >> i & 1)}


def add_geometry(lhs, rhs, width):
    """Two independent unsigned variable rows; zero known bits, zero carry."""
    full = half = increment = wire = segments = maximum = span = 0
    carry = False
    for bit in range(width):
        height = int(bit in lhs) + int(bit in rhs)
        if height == 2:
            if carry:
                full += 1
            else:
                half += 1
                segments += 1
            carry = True
            span += 1
        elif height == 1 and carry:
            increment += 1
            span += 1
        else:
            wire += int(height == 1 or carry)
            carry = False
            span = 0
        maximum = max(maximum, span)
    return dict(add_full_adder_columns=float(full), add_half_adder_columns=float(half),
                add_increment_columns=float(increment), add_wire_columns=float(wire),
                add_carry_segments=float(segments), add_max_live_carry_span=float(maximum),
                log2_add_live_carry_span=math.log2(maximum + 1.))


def features(query):
    f = previous_features(query)
    local = query['local_context']
    p = local['producer']
    r = p['result_width']
    a = variable_positions(p, 'lhs', r)
    b = variable_positions(p, 'rhs', r)
    f.update(add_geometry(a, b, r))
    for name, positions in [('lhs', a), ('rhs', b)]:
        f['live_' + name + '_bits'] = float(len(positions))
        f['log2_live_' + name + '_bits'] = math.log2(len(positions) + 1.)
    f['live_operand_overlap'] = float(len(a & b))
    f['live_operand_gap'] = float(max(0, max(min(a, default=0), min(b, default=0)) -
                                     min(max(a, default=-1), max(b, default=-1)) - 1))
    uses = overlap = below = above = position = 0.
    for consumer in local['consumers']:
        spec = consumer['spec']
        width = spec['result_width']
        for binding in consumer['bindings']:
            opposite = 'rhs' if binding['operand_index'] == 0 else 'lhs'
            live = variable_positions(spec, opposite, width)
            for bit, token in enumerate(binding['result_bit_map'][:width]):
                if type(token) is not int:
                    continue
                uses += 1
                overlap += bit in live
                below += sum(i < bit for i in live)
                above += sum(i > bit for i in live)
                position += bit / max(1, width - 1)
    f.update(consumer_pin_uses=uses, consumer_overlap_pin_uses=overlap,
             consumer_carry_below_mean=below / max(1., uses),
             consumer_carry_above_mean=above / max(1., uses),
             consumer_relative_position_mean=position / max(1., uses))
    work = sum(f[n] for n in ('add_full_adder_columns', 'add_half_adder_columns',
                              'add_increment_columns'))
    f['pressure_add_logic'] = work * f['target_pressure']
    f['pressure_consumer_pin_uses'] = uses * f['target_pressure']
    return f
