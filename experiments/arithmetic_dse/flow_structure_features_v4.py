"""Keep compressor context when estimating an unfused sparse sum boundary."""
import math
from . import flow_structure_features_v3 as previous

VERSION = 'flow-structure-word-context-features-v4'
operator_features = previous.operator_features
operator_circuit = previous.operator_circuit
state_controls = previous.state_controls
reduction_circuit = previous.reduction_circuit


def reduction_features(query):
    f = previous.reduction_features(query)
    z = f['intensive']
    # Compression creates a vector tree rather than the raw serial-add limit.
    # Restrict the intermediate-extension proxy to the zero-compression graph.
    # This is a shared structural condition, independent of source and width.
    risk = z['initial_sum_precision'] < z['effective_sum_precision'] and z['ks_compressor_rounds'] == 0
    depth = max(z['ks_fused_depth'], z['ks_serial_depth'] if risk else 0.)
    for side in f.values():
        side.update(log2_sparse_boundary_depth=math.log2(depth + 1.),
                    ks_sparse_boundary_work_ratio=1. + float(risk) * (z['ks_serial_work_ratio'] - 1.))
    return f
