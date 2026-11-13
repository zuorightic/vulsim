"""Shared positive G functions from prospective Boolean geometry.

Reference area is a sum of prospective primitive work. Mapped cells, source
identities, candidate identities and exact period categories are never inputs.
"""
import math
from . import reduction_mapping_features as geometry
from . import conditional_function_support_v2 as support

VERSION = 'common-positive-geometry-G-functions-v6'
REFERENCE_FEATURES = {'word_full_adder_cuts', 'word_half_adder_cuts',
                      'word_unpaired_xor', 'word_unpaired_and', 'word_unpaired_or'}


def positive(function, features):
    if function['kind'] != 'positive_log_linear':
        raise ValueError('G positive function identity')
    names, coefficients = function['features'], function['coefficients']
    if len(names) != len(set(names)):
        raise ValueError('duplicate G feature')
    value = function.get('intercept', 0.) + sum(features[n] * c for n, c in zip(
        names, coefficients, strict=True))
    return math.exp(value)


def predict(model, query, *, diagnostic=False):
    try:
        if model['version'] != VERSION or model['feature_version'] != geometry.VERSION:
            raise ValueError('mapping-G model identity')
        if not diagnostic:
            raise ValueError('mapping-G candidate lacks public qualification')
        if (query.get('launch_type', 'register') != 'register'
                or query.get('capture_banks', 1) != 1 or query.get('consumer_count', 0) != 0):
            raise ValueError('unqualified mapping-G boundary')
        T = query['target_ps']
        f = geometry.features(query['output_bits'], query['terms'], T)
        verdict = support.check(model['support'], f['area'], T)
        if verdict['status'] != 'structurally_supported':
            return verdict
        weights = model['reference_area_weights']
        if set(weights) != REFERENCE_FEATURES or any(not math.isfinite(w) or w <= 0 for w in weights.values()):
            raise ValueError('invalid prospective G primitive weights')
        reference = sum(f['area'][n] * w for n, w in weights.items())
        area = reference * positive(model['area'], f['intensive'])
        delay = positive(model['delay'], f['intensive'])
        if not all(math.isfinite(x) and x > 0 for x in (area, delay)):
            raise ValueError('nonpositive or nonfinite mapping-G price')
        return dict(status='diagnostic_estimate', operator_delay_ps=delay,
                    comb_area_um2=area, qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError) as error:
        return dict(status='cost_uncovered', reason=str(error))
