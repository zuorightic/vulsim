"""Bounded conditional sampling for numerical-function successors.

Retains the thirteen-target, three-region protocol. Guard periods are offline
measurement requests; neither guards nor observed slack are inference inputs.
"""
from types import FunctionType
from . import model_three_region_scan as parent

VERSION = 'common-function-three-region-v1'


def decide(history, source_id, role, guards=(1500, 500, 3000),
           reserved=(750, 1000, 1125, 1250)):
    cfg = parent.policy()
    if role not in ('train', 'validation'):
        raise ValueError('independent acquisition needs a separate frozen admission')
    if (not guards or len(set(guards)) != len(guards) or
            any(type(t) is not int or not cfg['minimum_ps'] <= t <= cfg['maximum_ps']
                for t in (*guards, *reserved)) or set(guards) & set(reserved)):
        raise ValueError('invalid or reserved fitting guard')

    def next_request(rows, role_, policy):
        if len(rows) >= 13 or any(r['status'] == 'failed' for r in rows):
            return None
        used = {r['SDC_ps'] for r in rows}
        for t in guards:
            if t not in used:
                return dict(SDC_ps=t, ABC_ps=t,
                            proposal='required_domain_clock_probe', reference_ratio=None)
        q = parent._next(rows, role_, policy)
        if q is None or q['SDC_ps'] not in reserved:
            return q
        for delta in range(1, 33):
            for sign in (1, -1):
                t = q['SDC_ps'] + sign * delta
                if (policy['minimum_ps'] <= t <= policy['maximum_ps'] and
                        t not in used and t not in reserved and all(
                        parent.number(abs(t - old)) / min(t, old) >=
                        parent.number(policy['minimum_relative_target_separation'])
                        for old in used)):
                    return dict(q, SDC_ps=t, ABC_ps=t, proposal='reserved_target_nudge')
        return None

    namespace = dict(parent.decide.__globals__, _next=next_request)
    result = FunctionType(parent.decide.__code__, namespace)(history, source_id, role, cfg)
    completed = {r['SDC_ps'] for r in history if r['status'] == 'completed'}
    return dict(result, required_clock_guards_ps=list(guards),
                missing_clock_guards_ps=[t for t in guards if t not in completed],
                reserved_exact_periods_ps=list(reserved))
