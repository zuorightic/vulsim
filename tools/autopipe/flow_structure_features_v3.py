"""Frozen v10 runtime functions; extracted without numerical edits from flow_structure_features_v3.py."""
import math

from . import flow_structure_features as previous

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
