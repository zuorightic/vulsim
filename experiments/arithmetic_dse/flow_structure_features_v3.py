"""Reset-polarity load interactions and emitted intermediate-width context.

This is a train-research successor to v2. A narrowed intermediate followed by
a wider use is a prospective fusion-risk proxy, not an assertion about the
optimizer's work queue. Source names and physical labels are never inputs.
"""
import math
from . import flow_structure_features as previous

VERSION = 'flow-structure-polarity-features-v3'
operator_features = previous.operator_features
operator_circuit = previous.operator_circuit
reduction_circuit = previous.reduction_circuit


def reduction_features(query):
    f = previous.reduction_features(query)
    width, terms = query['output_bits'], query['terms']
    first = min(width, max(max(bit[2] for bit in term) + 1 for term in terms[:2]) + 1)
    effective = min(width, sum(sum(1 << bit[2] for bit in term) for term in terms).bit_length())
    risk = float(first < effective)
    z = f['intensive']
    depth = max(z['ks_fused_depth'], z['ks_serial_depth'] if risk else 0.)
    extra = dict(initial_sum_precision=float(first), effective_sum_precision=float(effective),
                 intermediate_extension_fraction=max(0., effective - first) / width,
                 log2_boundary_logic_depth=math.log2(depth + 1.),
                 ks_shrink_work_ratio=1. + risk * (z['ks_serial_work_ratio'] - 1.),
                 ks_shrink_depth_gap=risk * z['ks_serial_depth_gap'])
    for side in f.values():
        side.update(extra)
    return f


def state_controls(structure):
    controls = previous.state_controls(structure)
    for q in controls:
        f = q['features']
        fraction = f['capture_bank_reset_fraction']
        zero_load = f['enabled_data_sinks'] * (1. - fraction)
        one_load = f['enabled_data_sinks'] * fraction
        f.update(log2_reset_zero_sinks=math.log2(zero_load + 1.),
                 log2_reset_one_sinks=math.log2(one_load + 1.),
                 native_reset_one_load=f['native_launch'] * math.log2(one_load + 1.),
                 native_capture_reset_fraction=f['native_launch'] * fraction,
                 native_source_reset_fraction=f['native_launch'] * f['source_bank_reset_fraction'])
    return controls
