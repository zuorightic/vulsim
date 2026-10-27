"""Contract for target coverage; physical cost library construction is step seven."""
import math


def target_coverage(measured_targets_ps, requested_target_ps):
    targets = sorted(set(float(value) for value in measured_targets_ps))
    target = float(requested_target_ps)
    if not math.isfinite(target) or target <= 0 or any(not math.isfinite(t) or t <= 0 for t in targets):
        raise ValueError('targets must be finite and positive')
    if target in targets:
        return {'status':'covered', 'abc_target_ps':target, 'mode':'exact_measured_target'}
    return {'status':'uncovered', 'abc_target_ps':target,
            'reason':'unmeasured_target' if targets and targets[0] < target < targets[-1]
                     else 'outside_measured_targets', 'extrapolated':False}
