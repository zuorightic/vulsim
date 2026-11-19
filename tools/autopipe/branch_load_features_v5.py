"""Frozen v10 runtime functions; extracted without numerical edits from branch_load_features_v5.py."""
import math

from . import flow_structure_features_v4 as previous

from .prospective_cell_cover import cover

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
