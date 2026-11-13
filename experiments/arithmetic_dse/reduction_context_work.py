"""Shared adder-work interactions for sparse compression and carry runs."""
from . import reduction_adder_work as parent

VERSION = 'wide-reduction-features-v4-adder-context'


def features(width, terms, target):
    f = parent.features(width, terms, target)
    a, d = f['area'], f['delay']
    half, full = a['word_half_adder_cuts'], a['word_full_adder_cuts']
    # A half-adder's sum/carry may feed the next compressor/merge rather than
    # being final outputs. Model the mixture continuously, with one coefficient.
    compressed_half = half * half / max(1., full + half) * (1. - a['word_no_compression'])
    incremental = d['post_merge_increment_columns']
    merge = incremental + d['post_merge_full_adder_columns'] + d['post_merge_half_adder_columns']
    increment_timing = d['log2_post_merge_carry_span'] * incremental / max(1., merge)
    for side in f.values():
        side.update(word_compressed_half_context=compressed_half,
                    word_increment_timing=increment_timing)
    return f
