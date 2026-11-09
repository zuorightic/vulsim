"""Deterministic thirteen-target conditional sampling; pure decisions, no EDA."""
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path

CONFIG = Path(__file__).with_name('configs') / 'model_three_region_scan_v1.json'
ROLES = ('train', 'validation', 'locked_test', 'not_training')
REFERENCES = ((Fraction(-1, 2), Fraction(-3, 10), Fraction(-3, 20)),
              (Fraction(-1, 20), Fraction(0), Fraction(1, 20)),
              (Fraction(3, 20), Fraction(3, 10), Fraction(1, 2)))


def number(value):
    if isinstance(value, Fraction):
        return value
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError('finite decimal measured value required')
    try:
        result = Fraction(str(value))
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise ValueError('nonfinite measured value') from error
    return result


def policy():
    cfg = json.loads(CONFIG.read_text())
    if (cfg['max_unique_targets'] != 13 or cfg['points_per_region'] != 3
            or cfg['automatic_retries'] != 0 or not cfg['ABC_equals_SDC']
            or not 0 < cfg['minimum_ps'] < cfg['initial_ps'] < cfg['maximum_ps']):
        raise ValueError('unsupported three-region policy')
    return cfg


def region(ratio):
    r = number(ratio)
    return 0 if r < Fraction(-1, 10) else 2 if r > Fraction(1, 10) else 1


def ratio(row):
    return number(row['data_setup_slack_ps']) / row['SDC_ps']


def spread(rows, index, cfg):
    minimum_r = number(cfg['minimum_ratio_separation'])
    span = number(cfg['minimum_ratio_span'][index])
    minimum_t = number(cfg['minimum_relative_target_separation'])
    for chosen in combinations(rows, 3):
        ordered = sorted(ratio(row) for row in chosen)
        periods = sorted(row['SDC_ps'] for row in chosen)
        if (ordered[-1] - ordered[0] >= span
                and all(b - a >= minimum_r for a, b in zip(ordered, ordered[1:]))
                and all(Fraction(b - a, a) >= minimum_t for a, b in zip(periods, periods[1:]))):
            return True
    return False


def groups(rows):
    return [[r for r in rows if r['status'] == 'completed' and region(ratio(r)) == index] for index in range(3)]


def _next(rows, role, cfg):
    if len(rows) >= cfg['max_unique_targets'] or any(row['status'] == 'failed' for row in rows):
        return None
    used = {row['SDC_ps'] for row in rows}
    def request(t, proposal, ref=None):
        if type(t) is not int or not cfg['minimum_ps'] <= t <= cfg['maximum_ps'] or t in used:
            return None
        return dict(SDC_ps=t, ABC_ps=t, proposal=proposal, reference_ratio=None if ref is None else str(ref))
    if not rows:
        return request(cfg['initial_ps_by_role'][role], 'initial')
    buckets = groups(rows)
    ready = [spread(bucket, index, cfg) for index, bucket in enumerate(buckets)]
    if all(ready):
        return None
    proposals = []
    for index, refs in enumerate(REFERENCES):
        if ready[index]: continue
        remaining = list(refs)
        for row in sorted(buckets[index], key=lambda r: (ratio(r), r['SDC_ps'])):
            if remaining:
                remaining.remove(min(remaining, key=lambda ref: (abs(ref-ratio(row)), ref)))
        wanted = remaining or [refs[0], refs[-1], refs[1]]
        for ref in wanted:
            for i, row in enumerate(rows):
                # This is a proposal using a locally estimated timing budget,
                # never an assertion of a monotone or fixed-delay response.
                budget = row['SDC_ps'] - number(row['data_setup_slack_ps'])
                if budget <= 0: continue
                estimate = budget / (1-ref)
                t = (estimate.numerator * 2 + estimate.denominator) // (2 * estimate.denominator)
                t = min(cfg['maximum_ps'], max(cfg['minimum_ps'], t))
                step = max(1, (t + 99)//100)
                offsets = [0] + [sign * step * k for k in range(1, 9) for sign in (-1, 1)]
                for j, offset in enumerate(offsets):
                    q = request(t + offset, 'ratio_proposal', ref)
                    if q and all(Fraction(abs(q['SDC_ps']-old), min(q['SDC_ps'], old)) >= number(cfg['minimum_relative_target_separation']) for old in used):
                        score = (min(len(buckets[index]), 3), j, abs(ratio(row)-ref), index, refs.index(ref), -i, q['SDC_ps'])
                        proposals.append((score, q)); break
    if proposals:
        return min(proposals, key=lambda item: item[0])[1]
    # Bounded fallback explores unmeasured gaps even with unusable/nonmonotone
    # local estimates. At most 15 candidates, never an unbounded integer search.
    knots = sorted(used | {cfg['minimum_ps'], cfg['maximum_ps']})
    candidates = [(b-a, (a+b)//2) for a, b in zip(knots, knots[1:]) if b-a > 1]
    candidates += [(cfg['maximum_ps']-cfg['minimum_ps'], t) for t in (cfg['minimum_ps'], cfg['maximum_ps']) if t not in used]
    for _, t in sorted(candidates, key=lambda item: (-item[0], item[1])):
        q = request(t, 'bounded_gap_fallback')
        if q: return q
    return None


def decide(rows, source_id, role, cfg=None):
    cfg = policy() if cfg is None else cfg
    if role not in ROLES or not isinstance(source_id, str) or not source_id or not isinstance(rows, list):
        raise ValueError('explicit immutable source and role required')
    before = []; identities = set()
    common = {'SDC_ps', 'ABC_ps', 'proposal', 'reference_ratio', 'source_id', 'role', 'status'}
    labels = {'implementation_id', 'operator_delay_ps', 'comb_area_um2', 'data_setup_slack_ps',
              'operator_maximum_covered', 'data_through_operator_covered', 'ownership_complete'}
    for row in rows:
        expected = _next(before, role, cfg)
        if (expected is None or not isinstance(row, dict) or not common <= row.keys()
                or any(row[k] != v or type(row[k]) is not type(v) for k, v in expected.items())
                or row['source_id'] != source_id or row['role'] != role):
            raise ValueError('history differs from deterministic source/role/target request')
        if row['status'] == 'completed':
            if set(row) != common | labels or any(row[k] is not True for k in ('operator_maximum_covered', 'data_through_operator_covered', 'ownership_complete')):
                raise ValueError('independent operator, through-data and ownership coverage required')
            if number(row['operator_delay_ps']) < 0 or number(row['comb_area_um2']) < 0:
                raise ValueError('finite nonnegative same-implementation delay and area required')
            number(row['data_setup_slack_ps'])
            impl = row['implementation_id']
            if not isinstance(impl, str) or not impl or impl in identities:
                raise ValueError('unique implementation identity required')
            identities.add(impl)
        elif row['status'] == 'failed':
            if set(row) != common | {'failure_reason'} or not isinstance(row['failure_reason'], str) or not row['failure_reason']:
                raise ValueError('failed point has a reason and no numerical labels')
        else:
            raise ValueError('unknown point status')
        before.append(row)
    buckets = groups(rows); next_request = _next(rows, role, cfg)
    complete = all(spread(bucket, i, cfg) for i, bucket in enumerate(buckets))
    reason = ('regions_complete' if complete else 'failed_point_no_retry' if any(r['status']=='failed' for r in rows)
              else 'target_cap_reached' if len(rows)==13 else 'bounded_proposals_exhausted' if next_request is None else 'sampling_in_progress')
    summary = []
    for i, bucket in enumerate(buckets):
        summary.append(dict(region=('negative','transition','positive')[i], effective_points=len(bucket), missing_count=max(0,3-len(bucket)),
            spacing_and_span_met=spread(bucket,i,cfg), targets_ps=[r['SDC_ps'] for r in bucket],
            ratio_span=None if not bucket else [str(min(map(ratio,bucket))),str(max(map(ratio,bucket)))],
            reference_deviations=[None if not bucket else str(min(abs(ratio(r)-ref) for r in bucket)) for ref in REFERENCES[i]]))
    return dict(next_request=next_request, stop_reason=reason, unique_targets=len(rows), regions=summary,
                coverage_shortfall=next_request is None and not complete,
                eligible_rows_retained=[i for i,r in enumerate(rows) if r['status']=='completed'],
                production_qualification=False, physical_admission_allowed=False)
