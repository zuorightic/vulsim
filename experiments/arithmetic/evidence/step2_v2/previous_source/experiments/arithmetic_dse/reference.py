"""Independent bit-exact experiment oracles; never use these as RTL templates.

binary32 multiplication uses exact Python integers and one explicit RNE step.
It does not use host floating point or the prospective hardware implementation.
"""
from dataclasses import dataclass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INVALID, DIVIDE_BY_ZERO, OVERFLOW, UNDERFLOW, INEXACT = 16, 8, 4, 2, 1
CANONICAL_NAN = 0x7FC00000


def unsigned(value: int, width: int) -> int:
    if not isinstance(width, int) or width <= 0:
        raise ValueError('width must be a positive integer')
    if not isinstance(value, int) or not 0 <= value < 1 << width:
        raise ValueError(f'value {value!r} is outside uint{width}')
    return value


def udivrem(a: int, d: int, width: int) -> tuple[int, int]:
    unsigned(a, width)
    unsigned(d, width)
    return divmod(a, d) if d else ((1 << width)-1, a)


def safe_divisor(d: int, width: int) -> tuple[int, bool]:
    """Input preparation contract for the later RTL wrapper (not the oracle)."""
    unsigned(d, width)
    return (d if d else 1), d == 0


@dataclass(frozen=True)
class FPResult:
    bits: int
    flags: int


def _rne(integer: int, right_shift: int) -> tuple[int, bool]:
    if right_shift <= 0:
        return integer << -right_shift, False
    quotient, remainder = divmod(integer, 1 << right_shift)
    halfway = 1 << (right_shift-1)
    increment = remainder > halfway or (remainder == halfway and quotient & 1)
    return quotient + bool(increment), bool(remainder)


def f32_mul(a: int, b: int) -> FPResult:
    unsigned(a, 32)
    unsigned(b, 32)
    ea, eb = (a >> 23) & 255, (b >> 23) & 255
    fa, fb = a & 0x7FFFFF, b & 0x7FFFFF
    na, nb = ea == 255 and fa != 0, eb == 255 and fb != 0
    if na or nb:
        signaling = (na and not fa & 0x400000) or (nb and not fb & 0x400000)
        return FPResult(CANONICAL_NAN, INVALID if signaling else 0)
    sign = (a ^ b) & 0x80000000
    za, zb = (a & 0x7FFFFFFF) == 0, (b & 0x7FFFFFFF) == 0
    if ea == 255 or eb == 255:
        if (ea == 255 and zb) or (eb == 255 and za):
            return FPResult(CANONICAL_NAN, INVALID)
        return FPResult(sign | 0x7F800000, 0)
    if za or zb:
        return FPResult(sign, 0)
    # Exact value = coefficient * 2**power, including subnormal inputs.
    ma, pa = (fa | 0x800000, ea-150) if ea else (fa, -149)
    mb, pb = (fb | 0x800000, eb-150) if eb else (fb, -149)
    coefficient, power = ma*mb, pa+pb
    exponent = coefficient.bit_length()-1+power
    precision_rounded, _ = _rne(coefficient, coefficient.bit_length()-24)
    rounded_exponent = exponent + (precision_rounded == 1 << 24)
    if exponent >= -126:
        rounded, inexact = _rne(coefficient, coefficient.bit_length()-24)
        if rounded == 1 << 24:
            rounded >>= 1
            exponent += 1
        if exponent > 127:
            return FPResult(sign | 0x7F800000, OVERFLOW | INEXACT)
        return FPResult(sign | ((exponent+127) << 23) | (rounded & 0x7FFFFF),
                        INEXACT if inexact else 0)
    rounded, inexact = _rne(coefficient, -(power+149))
    # IEEE/SoftFloat tininess-after-rounding tests a precision-p rounded value
    # with an unbounded exponent. Testing just the final encoded exponent would
    # miss underflow at some values that round up to encoded minNormal.
    flags = INEXACT if inexact else 0
    if inexact and rounded_exponent < -126:
        flags |= UNDERFLOW
    return FPResult(sign | rounded, flags)


def f32_chain(a: int, b: int, c: int) -> FPResult:
    first = f32_mul(a, b)
    second = f32_mul(first.bits, c)
    return FPResult(second.bits, first.flags | second.flags)


def case_manifest() -> dict:
    return json.loads((ROOT/'experiments/arithmetic/cases_v1.json').read_text())


def evaluate_case(case_id: str, inputs: dict[str, int]) -> dict[str, int]:
    cases = {case['id']: case for case in case_manifest()['cases']}
    if case_id not in cases:
        raise ValueError(f'unknown case: {case_id}')
    case = cases[case_id]
    if inputs.keys() != case['inputs'].keys():
        raise ValueError(f'{case_id}: expected inputs {sorted(case["inputs"])}')
    for name, width in case['inputs'].items():
        unsigned(inputs[name], width)
    x = inputs
    mask32 = (1 << 32)-1
    if case_id == 'M1':
        result = {'y': (x['a']*x['b']+x['c']) & ((1 << 64)-1)}
    elif case_id == 'M2':
        result = {'y': x['a']*x['b']+x['c']*x['d']}
    elif case_id == 'D1':
        q, r = udivrem(x['a'], x['d'], 16)
        result = {'q': q, 'r': r}
    elif case_id == 'D2':
        q, r = udivrem(x['a'], x['d'], 32)
        result = {'y': (q+x['bias']) & mask32 if x['select'] else x['bypass'], 'r': r}
    elif case_id in ('F1', 'F2', 'H_F1'):
        if case_id == 'F2':
            fp = f32_chain(x['a'], x['b'], x['c'])
        elif case_id == 'H_F1' and not x['select']:
            fp = FPResult(x['bypass'], 0)
        else:
            fp = f32_mul(x['a'], x['b'])
        result = {'bits': fp.bits, 'flags': fp.flags}
    elif case_id == 'H_M1':
        result = {'y': ((x['a']*x['b'] & mask32)+(x['c'] if x['select'] else 0)) & mask32}
    elif case_id == 'H_D1':
        q1, r1 = udivrem(x['a'], x['d'], 32)
        q2, r2 = udivrem(q1, x['e'], 32)
        result = {'q': q2, 'r1': r1, 'r2': r2}
    else:
        raise ValueError(f'missing reference implementation: {case_id}')
    if result.keys() != case['outputs'].keys():
        raise ValueError(f'{case_id}: reference output signature mismatch')
    for name, width in case['outputs'].items():
        unsigned(result[name], width)
    return result


if __name__ == '__main__':
    import sys
    for line_number, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            result = evaluate_case(request['case'], request['inputs'])
        except (ValueError, KeyError, TypeError) as error:
            raise SystemExit(f'reference input line {line_number}: {error}') from error
        print(json.dumps({'case':request['case'], 'outputs':result}, sort_keys=True))
