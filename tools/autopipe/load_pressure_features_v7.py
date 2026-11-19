"""Frozen v10 runtime functions; extracted without numerical edits from load_pressure_features_v7.py."""
import math

from . import rebuffer_context_features_v6 as previous

def carry_context(heights):
    active = overlap = tails = gaps = reaches = longest = 0
    for height in heights:
        active += height > 0
        overlap += height >= 2
        gaps += height == 0
        if height >= 2:
            reaches += 1
        elif height == 1 and reaches:
            reaches += 1
            tails += 1
        else:
            reaches = 0
        longest = max(longest, reaches)
    return dict(carry_tail_fraction=tails / max(1, active),
                log2_carry_tail_bits=math.log2(tails + 1.),
                variable_gap_fraction=gaps / max(1, len(heights)),
                carry_reach_fraction=longest / max(1, len(heights)))


def reduction_features(query):
    result = previous.reduction_features(query)
    columns = [0] * query['output_bits']
    for term in query['terms']:
        for _, _, bit in term:
            columns[bit] += 1
    z = result['intensive']
    extra = carry_context(columns)
    extra.update(cover_to_ripple_logratio=math.log2(max(1e-9, z['cover_fused_area']) / max(1e-9, z['ripple_cover_fused_area'])),
                 log2_serial_area_inflation=math.log2((z['cover_serial_area'] + 1.) / (z['cover_fused_area'] + 1.)),
                 carry_tail_pressure=extra['carry_tail_fraction'] * z['clock_pressure'])
    for f in result.values():
        f.update(extra)
    return result
