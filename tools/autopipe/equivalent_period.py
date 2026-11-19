"""Frozen v10 runtime functions; extracted without numerical edits from equivalent_period.py."""
from dataclasses import asdict, dataclass

import math

@dataclass(frozen=True)
class InversionConfig:
    min_period_ps: float = 1.
    max_period_ps: float = 6000.
    scan_intervals: int = 32
    refinement_steps: int = 28
    tolerance_ps: float = .05
    quantum_ps: float = 0.
    max_roots: int = 3

    def __post_init__(self):
        if not (0 < self.min_period_ps < self.max_period_ps and
                self.scan_intervals >= 2 and self.refinement_steps >= 1 and
                self.tolerance_ps > 0 and self.quantum_ps >= 0 and self.max_roots >= 1):
            raise ValueError('invalid finite inversion policy')
        if not all(math.isfinite(x) for x in (self.min_period_ps, self.max_period_ps,
                   self.tolerance_ps, self.quantum_ps)):
            raise ValueError('nonfinite inversion policy')


def invert_window(budget_ps, window, config=InversionConfig(), *, direct=None):
    """window(T) returns positive or negative effective windows per endpoint.

    direct=(alpha,H) is allowed only for a fixed-boundary shell without other
    arithmetic. Otherwise scan all declared intervals before refining sign
    changes. Finite scanning does not certify the absence of unsampled roots.
    Quantization happens AFTER inversion, with a fresh endpoint/residual check.
    """
    if not math.isfinite(budget_ps) or budget_ps <= 0:
        return dict(status='nonpositive_budget', budget_ps=budget_ps, roots=[], evaluations=0)
    samples = {}

    def sample(t):
        if t not in samples:
            values = tuple(float(x) for x in window(t))
            if not values or not all(map(math.isfinite, values)):
                raise ValueError('finite nonempty characterization endpoints required')
            samples[t] = values
        return min(samples[t]) - budget_ps

    proposals = []
    if direct is not None:
        alpha, overhead = direct
        if not math.isfinite(alpha) or alpha <= 0 or not math.isfinite(overhead):
            raise ValueError('invalid analytical shell')
        t = (budget_ps + overhead) / alpha
        if config.min_period_ps <= t <= config.max_period_ps:
            sample(t); proposals.append(t)
    else:
        lo, hi, n = config.min_period_ps, config.max_period_ps, config.scan_intervals
        grid = [lo * (hi / lo) ** (i / n) for i in range(n + 1)]
        grid[0], grid[-1] = lo, hi
        values = [sample(t) for t in grid]
        proposals.extend(t for t, v in zip(grid, values) if abs(v) <= config.tolerance_ps)
        for a, b, fa, fb in zip(grid, grid[1:], values, values[1:]):
            if fa * fb >= 0:
                continue
            for _ in range(config.refinement_steps):
                mid = (a + b) / 2; fm = sample(mid)
                if abs(fm) <= config.tolerance_ps / 8:
                    a = b = mid; break
                if fa * fm <= 0:
                    b, fb = mid, fm
                else:
                    a, fa = mid, fm
            proposals.append((a + b) / 2)
    roots, rejected = [], []
    for t in sorted(proposals):
        tau = (math.floor(t / config.quantum_ps + .5) * config.quantum_ps
               if config.quantum_ps else t)
        if not config.min_period_ps <= tau <= config.max_period_ps:
            rejected.append(dict(T_eq_ps=t, tau_ps=tau, reason='quantized_outside_search_interval'))
            continue
        residual = sample(tau); endpoints = samples[tau]
        row = dict(T_eq_ps=t, tau_ps=tau, window_ps=min(endpoints),
                   endpoint_windows_ps=list(endpoints), residual_ps=residual,
                   quantum_ps=config.quantum_ps)
        if min(endpoints) <= 0 or abs(residual) > config.tolerance_ps:
            rejected.append(dict(row, reason='window_residual_exceeds_tolerance'))
        elif not any(abs(r['tau_ps'] - tau) <= 1e-7 for r in roots):
            roots.append(row)
    all_roots = len(roots); roots = roots[:config.max_roots]
    return dict(status='converted' if roots else 'conversion_uncovered', budget_ps=budget_ps,
                roots=roots, rejected=rejected, evaluations=len(samples),
                compatible_roots_found=all_roots, roots_omitted=max(0, all_roots-len(roots)),
                policy=asdict(config), exhaustive_root_claim=False,
                method='analytical' if direct is not None else 'finite_scan_and_bracket_refinement')
