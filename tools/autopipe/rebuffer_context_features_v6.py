"""Frozen v10 runtime functions; extracted without numerical edits from rebuffer_context_features_v6.py."""
import math

from . import branch_load_features_v5 as previous

from .prospective_logic import Circuit

from .prospective_cell_cover import cover

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
