"""G's register-launched unsigned reduction function, independent of graph IDs.

The bit terms are a semantic query, not a price key. A whole fused region
replaces its internal Add costs; S and inter-region accounting remain separate.
"""
import math

POLICY = 'register-launched-reduction-v1'
VERSION = 'asap7-G-reduction-function-v1'


def features(width, terms, target):
    if type(width) is not int or not 1 <= width <= 257 or not math.isfinite(target) or target <= 0:
        raise ValueError('invalid reduction dimensions/period')
    heights = [0] * width
    independent = set()
    for term in terms:
        columns = set()
        for source, bit, column in term:
            if any(type(v) is not int or v < 0 for v in (source, bit, column)) or column >= width or column in columns:
                raise ValueError('invalid reduction term column')
            if (source, bit) in independent:
                raise ValueError('correlated/repeated reduction input bit')
            independent.add((source, bit)); columns.add(column); heights[column] += 1
    if len(terms) < 3 or not independent or any(not t for t in terms):
        raise ValueError('reduction requires at least three live terms')
    total = sum(heights); maximum = max(heights)
    lo = next(i for i, h in enumerate(heights) if h)
    hi = max(i for i, h in enumerate(heights) if h)
    first = next((i for i, h in enumerate(heights) if h >= 2), width)
    counters = depth = 0
    while max(heights) > 2:
        nxt = [0] * width
        for i, h in enumerate(heights):
            n = h // 3; counters += n; nxt[i] += h % 3 + n
            if i + 1 < width: nxt[i + 1] += n
        heights = nxt; depth += 1
        if depth > 257: raise ValueError('unbounded compressor analysis')
    carry = max(0, hi - first + 1)
    return dict(one=1., output_bits=float(width), term_count=float(len(terms)), active_bits=float(total),
                max_column_height=float(maximum), counter_count=float(counters), compressor_depth=float(depth),
                carry_span=float(carry), log2_carry_span=math.log2(carry + 1.), active_span=float(hi - lo + 1),
                clock_pressure=1500. / target, log2_target=math.log2(target / 500.),
                pressure_work=(counters + carry) * 1500. / target)


def predict(model, width, terms, target):
    if model['version'] != VERSION or model['policy'] != POLICY or model['quality_status'] != 'passed_independent':
        raise ValueError('G reduction model is not independently qualified')
    f = features(width, terms, target)
    if not model['target_interval_ps'][0] <= target <= model['target_interval_ps'][1]:
        raise ValueError('G target outside frozen interval')
    for name, (lo, hi) in model['numeric_support'].items():
        if name not in f or not lo - 1e-10 * max(1, abs(lo), abs(hi)) <= f[name] <= hi + 1e-10 * max(1, abs(lo), abs(hi)):
            raise ValueError('G feature outside frozen support: ' + name)
    result = {}
    for name in ('delay_ps', 'area_um2'):
        m = model[name]
        if len(m['features']) != len(m['coefficients']) or len(set(m['features'])) != len(m['features']):
            raise ValueError('G model feature/coefficient mismatch')
        y = sum(f[k] * c for k, c in zip(m['features'], m['coefficients']))
        if not math.isfinite(y) or y <= 0: raise ValueError('invalid G prediction')
        result[name] = y
    return dict(**result, features=f, residual_G_delay_ps=0., residual_G_area_um2=0.)
