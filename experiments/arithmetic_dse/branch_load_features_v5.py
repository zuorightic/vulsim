"""Legal cell work and semantic control branches, with numerical T inputs."""
import math
from . import flow_structure_features_v4 as previous
from .prospective_cell_cover import cover

VERSION = 'branch-load-prospective-features-v5'


def operator_features(query):
    f = previous.operator_features(query)
    circuit, outputs = previous.operator_circuit(query['local_context']['producer'])
    c = cover(circuit, outputs)
    f.update({'cover_' + k: v for k, v in c.items()})
    f.update(log2_cover_work=math.log2(c['cells'] + 1.),
             squared_log_cover_work=math.log2(c['cells'] + 1.) ** 2,
             cover_pressure_response=math.log2(1. + c['cells'] / 64.) * f['clock_pressure'],
             cover_T_response=math.log2(1. + c['cells'] / 64.) * f['log2_target'],
             cover_compound_fraction=c['compound_cells'] / max(1., c['cells']),
             cover_wide_fraction=c['wide_cells'] / max(1., c['cells']),
             work_pressure=f['log2_ks_work'] * f['clock_pressure'],
             work_log_target=f['log2_ks_work'] * f['log2_target'],
             selector_log_load=math.log2(f['control_input_bits'] + 1.) if 'control_input_bits' in f else f['log2_ks_work'],
             log_target_squared=f['log2_target'] ** 2)
    return f


def reduction_features(query):
    f = previous.reduction_features(query)
    for serial in (False, True):
        c, outputs, _ = previous.reduction_circuit(query, serial=serial)
        work = cover(c, outputs)
        name = 'serial' if serial else 'fused'
        for side in f.values():
            side.update({'cover_' + name + '_' + k: v for k, v in work.items()})
    z = f['intensive']
    risk = z['initial_sum_precision'] < z['effective_sum_precision'] and z['ks_compressor_rounds'] == 0
    spans = [set(b[2] for b in term) for term in query['terms']]
    overlap = [len(spans[i] & set.union(*spans[:i])) for i in range(1, len(spans))]
    for side in f.values():
        side.update(log2_cover_boundary_depth=math.log2(max(z['cover_fused_depth'], z['cover_serial_depth'] if risk else 0.) + 1.),
                    cover_wide_fraction=z['cover_fused_wide_cells'] / max(1., z['cover_fused_cells']),
                    cover_compound_fraction=z['cover_fused_compound_cells'] / max(1., z['cover_fused_cells']),
                    word_overlap_fraction=sum(overlap) / max(1., sum(map(len, spans))),
                    log2_max_word_overlap=math.log2(max(overlap, default=0) + 1.))
    return f


def state_controls(structure):
    controls = previous.state_controls(structure)
    for q in controls:
        f = q['features']
        native = f['native_launch']
        sinks = f['enabled_data_sinks']
        ones = sinks * f['capture_bank_reset_fraction']
        zeros = sinks - ones
        # A port iv path captures the service valid FF; its context is the
        # service bank, rather than the first arithmetic-stage data bank.
        capture_bits = sum(structure['input_widths']) if q['path_class'] == 'input_valid' else 2. ** f['log2_capture_bank_bits'] - 1.
        nonzero_reset = float(ones > 0)
        logt = f['log2_target']
        f.update(branch_native=native,
                 log2_context_capture=math.log2(capture_bits + 1.),
                 log2_global_FF=math.log2(f['total_FF_bits'] + 1.),
                 reset_has_one=nonzero_reset,
                 branch_reset_one=native * nonzero_reset,
                 reset_load_imbalance=abs(zeros - ones) / max(1., sinks),
                 branch_load=native * f['log2_logical_sinks'],
                 branch_log_T=native * logt,
                 branch_log_T2=native * logt * logt,
                 log_T2=logt * logt,
                 reset_log_load=nonzero_reset * f['log2_logical_sinks'],
                 branch_reset_log_load=native * nonzero_reset * f['log2_logical_sinks'],
                 reset_log_T=nonzero_reset * logt,
                 branch_reset_log_T=native * nonzero_reset * logt,
                 reset_log_T2=nonzero_reset * logt * logt,
                 branch_reset_log_T2=native * nonzero_reset * logt * logt,
                 log2_mean_word=math.log2(sinks / max(1., f['enabled_word_count']) + 1.))
    return controls
