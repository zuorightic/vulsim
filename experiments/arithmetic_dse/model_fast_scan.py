"""Pure, bounded offline characterization decisions; never invokes EDA.

The caller must separately admit source/role/coverage/resources and provide
measured labels. A replayable scan is not a physical admission or a model.
"""
import argparse
from fractions import Fraction
import json
import math
from pathlib import Path

CONFIG = Path(__file__).with_name('configs') / 'model_fast_scan_v2.json'
ROLES = ('train', 'validation', 'locked_test', 'not_training')


def policy():
    cfg = json.loads(CONFIG.read_text())
    c = cfg['clock']
    if (c['max_points'] != 10 or c['coarse_max_points'] + c['boundary_max_points']
            + len(c['tighter_factors']) != c['max_points'] or not c['ABC_equals_SDC']
            or c['automatic_retries'] or not 0 < c['minimum_ps'] < c['initial_ps'] < c['maximum_ps']):
        raise ValueError('unsupported bounded scan policy')
    return cfg


def _fraction(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError('finite measured number required')
    return Fraction(str(value))


def _bracket(rows):
    feasible = [r['SDC_ps'] for r in rows if r['data_setup_slack_ps'] >= 0]
    if not feasible:
        return None
    high = min(feasible)
    failing = [r['SDC_ps'] for r in rows if r['data_setup_slack_ps'] < 0 and r['SDC_ps'] < high]
    return (max(failing), high) if failing else None


def _next(rows, cfg):
    c = cfg['clock']; used = {r['SDC_ps'] for r in rows}
    def request(phase, period):
        if period in used or not c['minimum_ps'] <= period <= c['maximum_ps']:
            return None
        return dict(phase=phase, SDC_ps=period, ABC_ps=period)
    if len(rows) >= c['max_points'] or any(r['status'] != 'completed' for r in rows):
        return None
    if not rows:
        return request('coarse', c['initial_ps'])
    coarse = [r for r in rows if r['phase'] == 'coarse']
    if len(coarse) < c['coarse_max_points'] and all(r['phase'] == 'coarse' for r in rows) and not _bracket(rows):
        if all(r['data_setup_slack_ps'] >= 0 for r in rows):
            value = max(c['minimum_ps'], (min(used) + c['coarse_tighten_divisor'] - 1) // c['coarse_tighten_divisor'])
        elif all(r['data_setup_slack_ps'] < 0 for r in rows):
            value = min(c['maximum_ps'], max(used) * c['coarse_relax_multiplier'])
        else:
            value = None
        if value is not None:
            q = request('coarse', value)
            if q:
                return q
    refined = [r for r in rows if r['phase'] == 'boundary']
    bracket = _bracket(rows)
    if not any(r['phase'] == 'tighter' for r in rows) and len(refined) < c['boundary_max_points'] and bracket:
        low, high = bracket
        q = request('boundary', (low + high) // 2)
        if q:
            return q
    earlier = [r for r in rows if r['phase'] != 'tighter']
    anchor = min(r['SDC_ps'] for r in earlier)
    for numerator, denominator in c['tighter_factors']:
        value = max(c['minimum_ps'], (anchor * numerator + denominator - 1) // denominator)
        q = request('tighter', value)
        if q:
            return q
    return None


def validate_history(rows, role, cfg=None):
    cfg = policy() if cfg is None else cfg
    if role not in ROLES or not isinstance(rows, list):
        raise ValueError('one explicit immutable source role required')
    preceding = []; implementation_ids = set(); source = None
    common = {'phase', 'ABC_ps', 'SDC_ps', 'status', 'source_id', 'role'}
    measured = {'implementation_id', 'operator_delay_ps', 'area_um2', 'data_setup_slack_ps',
                'coverage_complete', 'operator_maximum_covered'}
    for row in rows:
        expected = _next(preceding, cfg)
        if (expected is None or not isinstance(row, dict) or set(row) - (common | measured | {'failure_reason'})
                or not common <= row.keys() or any(row[k] != v or type(row[k]) is not type(v) for k, v in expected.items())):
            raise ValueError('clock/phase is not the next frozen scan request')
        if not isinstance(row['source_id'], str) or not row['source_id'] or row['role'] != role:
            raise ValueError('scan source/role differs')
        if source is None:
            source = row['source_id']
        if source != row['source_id']:
            raise ValueError('multiple sources in one scan')
        if row['status'] == 'completed':
            if not measured <= row.keys() or 'failure_reason' in row:
                raise ValueError('complete paired implementation and coverage required')
            if (not isinstance(row['implementation_id'], str) or not row['implementation_id']
                    or row['implementation_id'] in implementation_ids):
                raise ValueError('unique measured implementation identity required')
            implementation_ids.add(row['implementation_id'])
            if _fraction(row['operator_delay_ps']) <= 0 or _fraction(row['area_um2']) <= 0:
                raise ValueError('positive paired delay/area required')
            _fraction(row['data_setup_slack_ps'])
            if row['coverage_complete'] is not True or row['operator_maximum_covered'] is not True:
                raise ValueError('whole Q-D witness alone or incomplete coverage cannot label an operator')
        elif row['status'] == 'failed':
            if set(row) != common | {'failure_reason'} or not isinstance(row['failure_reason'], str) or not row['failure_reason']:
                raise ValueError('failed points retain reason and no invented numerical label')
        else:
            raise ValueError('unknown scan point status')
        preceding.append(row)
    return cfg


def decide(rows, role):
    cfg = validate_history(rows, role); request = _next(rows, cfg)
    completed = [r for r in rows if r['status'] == 'completed']
    inversion = any(a['SDC_ps'] < b['SDC_ps'] and a['data_setup_slack_ps'] >= 0 > b['data_setup_slack_ps']
                    for a in completed for b in completed)
    reasons = []
    if request:
        reasons.append('scan_incomplete')
    if any(r['status'] == 'failed' for r in rows):
        reasons.append('failed_point_no_retry')
    if not _bracket(completed):
        reasons.append('no_observed_data_feasibility_bracket')
    if inversion:
        reasons.append('nonmonotonic_data_feasibility')
    tighter = [r for r in completed if r['phase'] == 'tighter']
    baseline = [r for r in completed if r['phase'] != 'tighter']
    eps = Fraction(cfg['stability']['epsilon_numerator'], cfg['stability']['epsilon_denominator'])
    if len(tighter) != 2 or not baseline:
        reasons.append('two_tighter_points_not_available')
    else:
        if any(r['data_setup_slack_ps'] >= 0 for r in tighter):
            reasons.append('tighter_operator_data_paths_not_both_pressured')
        if any(_fraction(r['operator_delay_ps']) <= r['SDC_ps'] for r in tighter):
            reasons.append('internal_operator_paths_not_both_pressured')
        values = [min(_fraction(r['operator_delay_ps']) for r in baseline)] + [_fraction(r['operator_delay_ps']) for r in tighter]
        # Regrowth or a faster outlier elsewhere also prevents a stable claim.
        if max(values) > min(_fraction(r['operator_delay_ps']) for r in completed) * (1 + eps):
            reasons.append('delay_response_exceeds_stability_band')
    pair = None
    if completed:
        fastest = min(_fraction(r['operator_delay_ps']) for r in completed)
        band = Fraction(cfg['paired_label_band']['epsilon_numerator'], cfg['paired_label_band']['epsilon_denominator'])
        eligible = [r for r in completed if _fraction(r['operator_delay_ps']) <= fastest * (1 + band)]
        selected = min(eligible, key=lambda r: (_fraction(r['area_um2']), _fraction(r['operator_delay_ps']), r['SDC_ps'], r['implementation_id']))
        pair = {k: selected[k] for k in ('source_id', 'role', 'implementation_id', 'SDC_ps', 'ABC_ps', 'operator_delay_ps', 'area_um2')}
        pair.update(fastest_measured_delay_ps=float(fastest), eligible_implementations=[r['implementation_id'] for r in eligible],
                    same_measured_implementation=True)
    return dict(version=cfg['version'], next_request=request, measured_points=len(rows), max_points=cfg['clock']['max_points'],
                scan_complete=request is None, stable_within_scan_envelope=not reasons, qualification_reasons=reasons,
                observed_data_bracket_ps=_bracket(completed), nonmonotonic_data_feasibility=inversion,
                provisional_pair=pair, role=role, fitting_admitted=False, physical_admission_allowed=False, PPA_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--history', type=Path, required=True)
    parser.add_argument('--role', choices=ROLES, required=True)
    args = parser.parse_args()
    print(json.dumps(decide(json.loads(args.history.read_text()), args.role), indent=2))
