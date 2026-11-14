"""Prospective alternate carry work and semantic rebuffer context.

Ripple is a shared work proxy, not a claim about the mapper's chosen topology.
All features derive from semantic graphs, numerical T and frozen constants.
"""
import math
from . import branch_load_features_v5 as previous
from . import wide_arithmetic as arithmetic, wide_operator_samples as samples
from .prospective_logic import Circuit
from .prospective_cell_cover import cover

VERSION = 'rebuffer-context-prospective-features-v6'


class RippleCircuit(Circuit):
    def prefix(self, a, b, carry=0):
        if len(a) != len(b) or not a:
            raise ValueError('equal nonempty ripple operands required')
        sums, carries = [], []
        for x, y in zip(a, b, strict=True):
            p = self.gate('xor', x, y)
            sums.append(self.gate('xor', p, carry))
            generate = self.gate('and', x, y)
            propagate = self.gate('and', p, carry)
            carry = self.gate('or', generate, propagate)
            carries.append(carry)
        return sums, carries


def ripple_operator_circuit(spec):
    arithmetic.validate(spec)
    c = RippleCircuit()
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



def ripple_reduction_circuit(query, *, serial=False):
    # Semantic validation also enforces independent bit roots and column bounds.
    from .reduction_wide_features import features
    width, terms = query['output_bits'], query['terms']
    features(width, terms, query['target_ps'])
    c = RippleCircuit()
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



def operator_features(query):
    f = previous.operator_features(query)
    c, outputs = ripple_operator_circuit(query['local_context']['producer'])
    work = cover(c, outputs)
    f.update({'ripple_cover_' + k: v for k, v in work.items()})
    f.update(log2_ripple_cover_work=math.log2(work['cells'] + 1.),
             ripple_prefix_area_ratio=work['area'] / max(1e-9, f['cover_area']),
             ripple_work_pressure=math.log2(work['cells'] + 1.) * f['clock_pressure'],
             ripple_work_log_T=math.log2(work['cells'] + 1.) * f['log2_target'])
    return f


def reduction_features(query):
    result = previous.reduction_features(query)
    for serial in (False, True):
        c, outputs, _ = ripple_reduction_circuit(query, serial=serial)
        work = cover(c, outputs)
        name = 'serial' if serial else 'fused'
        for f in result.values():
            f.update({'ripple_cover_' + name + '_' + k: v for k, v in work.items()})
    z = result['intensive']
    risk = z['initial_sum_precision'] < z['effective_sum_precision'] and z['ks_compressor_rounds'] == 0
    for f in result.values():
        f.update(log2_ripple_boundary_depth=math.log2(max(z['ripple_cover_fused_depth'], z['ripple_cover_serial_depth'] if risk else 0.) + 1.),
                 ripple_prefix_area_ratio=z['ripple_cover_fused_area'] / max(1e-9, z['cover_fused_area']),
                 log2_ripple_cover_work=math.log2(z['ripple_cover_fused_cells'] + 1.),
                 ripple_half_fraction=z['ks_fused_half_fraction'])
    return result


def state_controls(structure):
    controls = previous.state_controls(structure)
    for q in controls:
        f = q['features']
        sinks = f['enabled_data_sinks']
        ones = sinks * f['capture_bank_reset_fraction']
        zeros = sinks - ones
        # A prospective measure of competing state relative to this source's
        # local enabled bank. No measured load, timing budget or slack enters.
        competition = math.log2(1. + f['total_FF_bits'] / max(1., sinks))
        native = f['branch_native']
        f.update(log2_reset_zero_sinks=math.log2(zeros + 1.),
                 log2_reset_one_sinks=math.log2(ones + 1.),
                 log2_competing_state=competition,
                 branch_competing_state=native * competition,
                 competing_state_pressure=competition * f['clock_pressure'],
                 branch_capture_context=native * f['log2_context_capture'],
                 branch_source_context=native * f['log2_source_bank_bits'])
    return controls
