"""Structural support with one deduplicated geometry population throughout.

Source identities only audit roles. Distances, scales, k and calibration use
distinct structural vectors, so copying a source cannot change membership.
No anchor contains a physical label or selects a coefficient vector.
"""
import math

VERSION = 'numerical-structural-support-v2-distinct-geometry'


def derive(rows, names, target_interval=(500., 3000.), k=2, radius_factor=1.05):
    if not rows or any(r['role'] != 'train' for r in rows):
        raise ValueError('support derivation accepts train features only')
    if (not names or len(set(names)) != len(names) or
            any('target' in n or 'pressure' in n or n.endswith('_id') for n in names)):
        raise ValueError('support geometry must exclude T and identifiers')
    if (type(k) is not int or k < 1 or not math.isfinite(radius_factor) or radius_factor < 1
            or len(target_interval) != 2 or not all(math.isfinite(t) for t in target_interval)
            or not 0 < target_interval[0] <= target_interval[1]):
        raise ValueError('invalid support calibration parameters')
    sources = {}
    for row in rows:
        vector = tuple(float(row['features'][n]) for n in names)
        if not all(math.isfinite(v) for v in vector):
            raise ValueError('nonfinite support geometry')
        source = row['source']
        if source in sources and sources[source] != vector:
            raise ValueError('source geometry changed across targets')
        sources[source] = vector
    anchors = sorted(set(sources.values()))
    bounds = [[min(v[i] for v in anchors), max(v[i] for v in anchors)]
              for i in range(len(names))]
    scales = [max(hi-lo, 1.) for lo, hi in bounds]
    effective_k = min(k, max(1, len(anchors)-1))
    def distance(a, b):
        return math.sqrt(sum(((x-y)/s)**2 for x,y,s in zip(a,b,scales,strict=True)))
    # Leave out an entire geometry, including every duplicate source/period.
    held = [sorted(distance(v, other) for other in anchors if other != v)[effective_k-1]
            for v in anchors] if len(anchors)>1 else [0.]
    return dict(version=VERSION,features=list(names),bounds=bounds,scales=scales,
                anchors=[list(v) for v in anchors],k=effective_k,requested_k=k,
                radius=max(held)*radius_factor,radius_factor=radius_factor,
                target_interval_ps=list(target_interval),label_values_stored=False,
                train_sources=len(sources),distinct_geometries=len(anchors),
                calibration_population='leave-one-distinct-geometry-out',
                query_population='distinct-geometry',qualified_for_production=False)


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
        for n,v,(lo,hi) in zip(support['features'],vector,support['bounds'],strict=True):
            if not lo-1e-9 <= v <= hi+1e-9:
                raise ValueError('outside structural range '+n)
        anchors = support['anchors']
        if not anchors or len({tuple(a) for a in anchors}) != len(anchors):
            raise ValueError('support anchors must be distinct')
        distances = sorted(math.sqrt(sum(((a-b)/s)**2 for a,b,s in
                                        zip(vector,anchor,support['scales'],strict=True)))
                           for anchor in anchors)
        if not 1 <= support['k'] <= len(distances) or distances[support['k']-1] > support['radius']+1e-9:
            raise ValueError('outside structural neighborhood')
        return dict(status='structurally_supported',price_qualification_granted=False)
    except (KeyError,ValueError,TypeError,OverflowError,ZeroDivisionError) as e:
        return dict(status='cost_uncovered',reason=str(e))
