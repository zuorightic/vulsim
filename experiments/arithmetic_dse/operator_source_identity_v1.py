"""Semantic source grouping for independent-operand operator studies.

Add/ADC operand exchange is already part of the emitter's normalization.
Validation duties must use that same equivalence, even if the original port
names or declared operand order differ. This key is for offline data roles;
it is never an input to a price function.
"""
from copy import deepcopy
import hashlib
import json
from . import wide_arithmetic as arithmetic


def semantic_context(query):
    arithmetic.validate(query['local_context']['producer'])
    result = deepcopy({k: v for k, v in query.items() if k != 'flow_context'})
    spec = result['local_context']['producer']
    if (not query['topology']['operand_shared_input_roots']
            and arithmetic.permutation(spec) == [1, 0]):
        for suffix in ('width', 'zero_hex', 'one_hex'):
            a, b = 'lhs_' + suffix, 'rhs_' + suffix
            spec[a], spec[b] = spec[b], spec[a]
    return result


def group(query):
    raw = json.dumps(semantic_context(query), sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()
