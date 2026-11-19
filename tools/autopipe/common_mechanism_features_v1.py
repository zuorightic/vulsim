"""Frozen v10 runtime functions; extracted without numerical edits from common_mechanism_features_v1.py."""
import math

from . import reduction_mapping_features as reduction

def carry_geometry(heights):
    """Potential carry reach through occupied input columns, including gaps.

    A column with two or more operands can generate carry. One operand can
    propagate it; an empty column absorbs it. This describes original input
    columns for both dense and sparse reductions, rather than mapped topology.
    """
    reach = longest = single = propagated = runs = 0
    previous_overlap = False
    for height in heights:
        overlap = height >= 2
        runs += int(overlap and not previous_overlap)
        previous_overlap = overlap
        if overlap or (height == 1 and reach):
            reach += 1
            longest = max(longest, reach)
            propagated += 1
            single += int(height == 1)
        else:
            reach = 0
    return dict(log2_carry_reach=math.log2(longest + 1.),
                carry_single_fraction=single / max(1, propagated),
                log2_overlap_runs=math.log2(runs + 1.))


def reduction_features(query):
    f = reduction.features(query['output_bits'], query['terms'], query['target_ps'])
    heights = [0] * query['output_bits']
    for term in query['terms']:
        for _, _, column in term:
            heights[column] += 1
    extra = carry_geometry(heights)
    f['intensive'].update(extra)
    # Support uses the same prospective geometry, never the numerical target
    # itself as a nearest-source identity.
    f['area'].update(extra)
    f['delay'].update(extra)
    return f
