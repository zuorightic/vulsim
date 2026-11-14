"""Prospective prefix, emitted sum order and local state-bank features.

The fused and serial reduction graphs describe two implementation limits.
They deliberately do not claim to reproduce Yosys's work-queue ordering or
infer a particular ALUMACC fusion from a source identifier. Their difference
measures sensitivity to the intermediate boundaries in the emitted sum.
"""
import math
from . import common_mechanism_features_v1 as previous
from . import wide_arithmetic as arithmetic, wide_operator_samples as samples
from .prospective_logic import Circuit

VERSION = 'flow-structure-prospective-features-v2'
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


def operator_features(query):
    f = previous.operator_features(query)
    c, outputs = operator_circuit(query['local_context']['producer'])
    work = c.work(outputs)
    f.update({'ks_' + name: value for name, value in work.items()})
    f.update(ks_primitive_area=weighted(work, PRIMITIVES), ks_cut_area=weighted(work, CUTS),
             log2_ks_work=math.log2(work['work'] + 1.),
             log2_ks_depth=math.log2(work['depth'] + 1.),
             ks_unpaired_fraction=sum(work['unpaired_' + k] for k in PRIMITIVES) / max(1., work['work']),
             ks_half_fraction=work['half_cuts'] / max(1., work['full_cuts'] + work['half_cuts']))
    return f


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


def state_controls(structure):
    result = previous.state_controls(structure)
    stages = structure['stage_words']
    input_bits = sum(structure['input_widths'])
    bits = list(map(sum, stages))
    resets = structure['stage_reset_one_bits']
    held = structure['service_mode'] != 2
    for q in result:
        stage = q['stage']
        source_is_input = q['control_source'] in ('port_iv', 'service_valid')
        source = min(max(stage - 1, 0), len(stages) - 1)
        launch_bits = input_bits if source_is_input else bits[source]
        capture_bits = bits[stage] if stage < len(stages) else structure['external_bits']
        launch_reset = structure['input_reset_one_bits'] if source_is_input else resets[source]
        capture_reset = resets[stage] if stage < len(stages) else 0
        f = q['features']
        f.update(log2_source_bank_bits=math.log2(launch_bits + 1.),
                 log2_capture_bank_bits=math.log2(capture_bits + 1.),
                 source_bank_reset_fraction=launch_reset / max(1., launch_bits),
                 capture_bank_reset_fraction=capture_reset / max(1., capture_bits),
                 source_has_hold=float(source_is_input and held),
                 stage_fraction=stage / max(1., len(stages)),
                 log2_state_depth=math.log2(len(stages) + 1.),
                 target_linear=structure['target_ps'] / 1500.,
                 source_sqrt_bank_bits=math.sqrt(launch_bits),
                 capture_sqrt_bank_bits=math.sqrt(capture_bits))
    return result
