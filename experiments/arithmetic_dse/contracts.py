"""Case signatures, deterministic target rules, and freeze verification."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def fixed_latency(case: dict) -> int:
    depth = case['heavy_depth']
    if not isinstance(depth, int) or depth < 1:
        raise ValueError('positive heavy-operation depth required')
    return max(2, depth+1)


def target_period_ps(case: dict, calibration_ps: dict, overhead_ps) -> int:
    def nonnegative(value):
        result = Fraction(str(value))
        if result < 0:
            raise ValueError('negative timing measurement')
        return result
    delays = []
    for primitive in case['calibration_path']:
        if primitive not in calibration_ps:
            raise ValueError(f'missing calibration: {primitive}')
        value = nonnegative(calibration_ps[primitive])
        if value == 0:
            raise ValueError('arithmetic calibration delay must be positive')
        delays.append(value)
    budget = max(max(delays), sum(delays)/fixed_latency(case))
    period = nonnegative(overhead_ps)+Fraction(11, 10)*budget
    return (period.numerator+period.denominator-1)//period.denominator


def check_partition(manifest: dict) -> dict:
    cases = manifest['cases']
    if len(cases) != 9 or len({case['id'] for case in cases}) != 9:
        raise ValueError('expected nine unique cases')
    formal = [case for case in cases if case['split'] == 'formal']
    holdout = [case for case in cases if case['split'] == 'holdout']
    if len(formal) != 6 or len(holdout) != 3:
        raise ValueError('expected six formal and three holdout cases')
    families = {'integer_mul', 'integer_div', 'float_mul'}
    if {case['family'] for case in formal} != families or {case['family'] for case in holdout} != families:
        raise ValueError('both partitions must cover all three families')
    calibration = set(manifest['calibration_only'])
    if calibration & {case['id'] for case in cases}:
        raise ValueError('case/calibration identity overlap')
    for case in cases:
        if not set(case['calibration_path']) <= calibration:
            raise ValueError(f'{case["id"]}: unknown calibration primitive')
        if not all(isinstance(w, int) and w > 0 for w in [*case['inputs'].values(), *case['outputs'].values()]):
            raise ValueError('invalid case bit width')
    return {'formal': len(formal), 'holdout': len(holdout), 'group_records': 4*len(cases),
            'fixed_L': {case['id']: fixed_latency(case) for case in cases}}


def check_freeze(path: Path) -> dict:
    lock = json.loads(path.read_text())
    for relative, expected in lock['files_sha256'].items():
        actual = hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'freeze mismatch: {relative}')
    return lock
