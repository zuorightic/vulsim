"""Train-derived structural support for common numerical functions.

Anchors hold geometry only, never a price. T is checked as a continuous range
and does not select an anchor or coefficient vector. This helper by itself
grants neither independent model qualification nor production D access.
"""
import math

VERSION = 'numerical-structural-support-v1'


def derive(rows, names, target_interval=(500., 3000.), k=2, radius_factor=1.05):
    if not rows or any(r['role'] != 'train' for r in rows):
        raise ValueError('support derivation accepts train features only')
    if (not names or len(set(names)) != len(names) or
            any('target' in n or 'pressure' in n or n.endswith('_id') for n in names)):
        raise ValueError('support geometry must exclude T and identifiers')
    vectors = {}
    for r in rows:
        v = tuple(float(r['features'][n]) for n in names)
        if not all(math.isfinite(x) for x in v):
            raise ValueError('nonfinite support geometry')
        vectors.setdefault(r['source'], v)
        if vectors[r['source']] != v:
            raise ValueError('source geometry changed across targets')
    items = sorted(vectors.items())
    if len(items) <= k or k < 1 or radius_factor < 1:
        raise ValueError('independent structural neighbors required')
    bounds = [[min(v[i] for _, v in items), max(v[i] for _, v in items)]
              for i in range(len(names))]
    scales = [max(hi - lo, 1.) for lo, hi in bounds]
    def distance(a, b):
        return math.sqrt(sum(((x-y)/s)**2 for x, y, s in zip(a,b,scales,strict=True)))
    held = [sorted(distance(v, other) for src, other in items if src != source)[k-1]
            for source, v in items]
    # Exact duplicate geometry is stored once. It never selects a price.
    anchors = sorted(set(vectors.values()))
    return dict(version=VERSION, features=list(names), bounds=bounds, scales=scales,
                anchors=[list(a) for a in anchors], k=min(k, len(anchors)),
                radius=max(held) * radius_factor, radius_factor=radius_factor,
                target_interval_ps=list(target_interval), label_values_stored=False,
                train_sources=len(items), qualified_for_production=False)


def check(support, features, target):
    try:
        if support['version'] != VERSION or not math.isfinite(target):
            raise ValueError('support identity or target invalid')
        lo, hi = support['target_interval_ps']
        if not lo <= target <= hi:
            raise ValueError('outside continuous target interval')
        vector = [float(features[n]) for n in support['features']]
        if not all(math.isfinite(v) for v in vector):
            raise ValueError('nonfinite structural feature')
        for n, v, (lo, hi) in zip(support['features'], vector, support['bounds'], strict=True):
            if not lo-1e-9 <= v <= hi+1e-9:
                raise ValueError('outside structural range '+n)
        distances = sorted(math.sqrt(sum(((a-b)/s)**2 for a,b,s in
                                        zip(vector,anchor,support['scales'],strict=True)))
                           for anchor in support['anchors'])
        if len(distances) < support['k'] or distances[support['k']-1] > support['radius']+1e-9:
            raise ValueError('outside structural neighborhood')
        return dict(status='structurally_supported',price_qualification_granted=False)
    except (KeyError,ValueError,TypeError,OverflowError) as e:
        return dict(status='cost_uncovered',reason=str(e))


def operator_semantics(query):
    """Validate the first declared live-interval and load contract separately."""
    from .operator_interval_features import features,variable_positions
    f = features(query)
    p = query['local_context']['producer']
    if (p['operation'] not in ('mul','add') or f['lhs_one_count'] or f['rhs_one_count']
            or f['carry_dynamic'] or f['carry_one'] or f['consumer_count'] > 1
            or f['consumer_mul'] or f['consumer_addcarry']
            or f['consumer_known_one_bits'] or f['consumer_nonzero_carry']
            or f['capture_banks'] > 2):
        raise ValueError('unsupported operator/consumer semantics')
    for spec in [p] + [c['spec'] for c in query['local_context']['consumers']]:
        for name in ('lhs','rhs'):
            bits = variable_positions(spec,name,spec['result_width'])
            if not bits or len(bits) != max(bits)-min(bits)+1:
                raise ValueError('outside contiguous live operand interval')
    if p['operation'] == 'add' and f['add_half_adder_columns'] == 0:
        raise ValueError('pure wiring Add requires zero-intrinsic-cost lowering')
    return f
