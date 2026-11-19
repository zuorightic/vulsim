"""Frozen v10 runtime functions; extracted without numerical edits from flow_structure_features.py."""
import math

from . import common_mechanism_features_v1 as previous

from . import wide_arithmetic as arithmetic, wide_operator_samples as samples

from .prospective_logic import Circuit

PRIMITIVES = {'xor': .16038, 'and': .08748, 'or': .08748, 'not': .05832}


CUTS = {'full_cuts': .20412, 'half_cuts': .13122,
        'unpaired_xor': .16038, 'unpaired_and': .08748,
        'unpaired_or': .08748, 'unpaired_not': .05832}


def weighted(work, weights):
    return math.fsum(work[n] * coefficient for n, coefficient in weights.items())


def operator_circuit(spec):
    arithmetic.validate(spec)
    c = Circuit()
    width = spec['arithmetic_width']

    def operand(name):
        needed = samples.input_demand(spec, name)
        result = []
        for bit in range(width):
            possible = arithmetic.bit_values(spec, name, bit)
            result.append(c.leaf((name, bit)) if len(possible) == 2 and bit in needed else
                          possible[0] if len(possible) == 1 else 0)
        return result

    a, b = operand('lhs'), operand('rhs')
    control = c.leaf(('cin', 0)) if spec['carry'] == 'dynamic' else int(spec['carry'] == 'one')
    op = spec['operation']
    status = 0
    if op in ('add', 'adc', 'sub', 'sbb'):
        if op in ('sub', 'sbb'):
            b = [c.gate('not', bit) for bit in b]
            control = c.gate('not', control)
        native, carry = c.prefix(a, b, control)
        status = c.gate('not', carry[-1]) if op in ('sub', 'sbb') else carry[-1]
    elif op == 'mux':
        native = [c.gate('or', c.gate('and', c.gate('not', control), x), c.gate('and', control, y))
                  for x, y in zip(a, b, strict=True)]
    else:
        raise ValueError('flow-structure operator scope is Add/ADC/Sub/SBB/Mux')
    outputs = native[spec['result_lo']:spec['result_lo'] + spec['value_width']]
    if spec['status'] != 'none':
        outputs.append(status)
    return c, outputs


def reduction_circuit(query, *, serial=False):
    # Semantic validation also enforces independent bit roots and column bounds.
    from .reduction_wide_features import features
    width, terms = query['output_bits'], query['terms']
    features(width, terms, query['target_ps'])
    c = Circuit()
    vectors = []
    for rank, term in enumerate(terms):
        vector = [0] * width
        for _, _, column in term:
            vector[column] = c.leaf((rank, column))
        vectors.append(vector)
    if serial:
        outputs = vectors[0]
        for following in vectors[1:]:
            outputs, _ = c.prefix(outputs, following)
        rounds = 0
    else:
        columns = [[vector[col] for vector in vectors if vector[col]] for col in range(width)]
        outputs, rounds = c.compress(columns)
    return c, outputs, rounds


def reduction_features(query):
    f = previous.reduction_features(query)
    fused, fo, rounds = reduction_circuit(query)
    serial, so, _ = reduction_circuit(query, serial=True)
    fw, sw = fused.work(fo), serial.work(so)
    for name, work in [('fused', fw), ('serial', sw)]:
        f['intensive'].update({'ks_' + name + '_' + n: v for n, v in work.items()})
        f['intensive']['ks_' + name + '_area'] = weighted(work, CUTS)
    extra = dict(log2_ks_depth=math.log2(fw['depth'] + 1.),
                 log2_ks_serial_depth=math.log2(sw['depth'] + 1.),
                 ks_serial_depth_gap=(sw['depth'] - fw['depth']) / max(1., fw['depth']),
                 ks_serial_work_ratio=sw['work'] / max(1., fw['work']),
                 ks_fused_half_fraction=fw['half_cuts'] / max(1., fw['full_cuts'] + fw['half_cuts']),
                 ks_fused_unpaired_fraction=sum(fw['unpaired_' + n] for n in PRIMITIVES) / max(1., fw['work']),
                 ks_serial_carry_depth=sw['carry_depth'],
                 log2_ks_fanout=fw['log2_max_fanout'], ks_compressor_rounds=float(rounds))
    for side in f.values():
        side.update(extra)
    return f
