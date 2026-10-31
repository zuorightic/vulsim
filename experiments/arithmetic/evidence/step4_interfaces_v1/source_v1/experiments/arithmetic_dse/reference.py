"""Independent bit-exact experiment oracles; never use these as RTL templates.

binary32 multiplication uses exact Python integers and one explicit RNE step.
It does not use host floating point or the prospective hardware implementation.
"""
from dataclasses import dataclass
import json
import sys
from .contracts import case_manifest
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


def logical_shift(a, shift, width, *, right=False):
    if (type(width) is not int or width <= 0 or type(a) is not int
            or not 0 <= a < 1 << width or type(shift) is not int or shift < 0):
        raise ValueError('invalid unsigned shift input')
    if shift >= width:
        return 0
    return a >> shift if right else (a << shift) & ((1 << width)-1)


def evaluate_spec(case, inputs):
    if inputs.keys() != case['inputs'].keys():
        raise ValueError(f'{case["id"]}: input signature mismatch')
    for name, width in case['inputs'].items():
        if type(inputs[name]) is not int or not 0 <= inputs[name] < 1 << width:
            raise ValueError(f'{case["id"]}: {name} exceeds uint{width}')
    x, family, w = inputs, case['family'], case['width']
    if w is not None:
        mask = (1 << w)-1
        if family == 'MUL': result = {'y': x['a']*x['b']}
        elif family == 'MAC': result = {'y': (x['a']*x['b']+x['c']) & ((1 << (2*w))-1)}
        elif family == 'DOT2': result = {'y': x['a']*x['b']+x['c']*x['d']}
        elif family in ('UDR', 'DIVSEL', 'H_D'):
            q, r = udivrem(x['a'], x['d'], w)
            if family == 'UDR': result = {'q': q, 'r': r}
            elif family == 'DIVSEL':
                result = {'y': (q+x['bias']) & mask if x['select'] else x['bypass'], 'r': r}
            else:
                q2, r2 = udivrem(q, x['e'], w)
                result = {'q': q2, 'r1': r, 'r2': r2}
        elif family == 'MIX':
            left = logical_shift((x['a']+x['b']) & mask, x['s'], w)
            right = logical_shift((x['a']-x['b']) & mask, x['s'], w, right=True)
            remainder = udivrem(x['a'], x['d'], w)[1]
            result = {'y': ((left & x['mask']) | (right & (~x['mask'] & mask))) ^ remainder,
                      'less': int(x['a'] < x['b'])}
        elif family == 'H_M':
            product = (x['a']*x['b']) & mask
            result = {'y': (product + (x['c'] if x['select'] else 0)) & mask}
        else:
            raise ValueError(f'unknown integer family: {family}')
    else:
        if family == 'F2': fp = f32_chain(x['a'], x['b'], x['c'])
        elif family == 'H_F1' and not x['select']: fp = FPResult(x['bypass'], 0)
        elif family in ('F1', 'H_F1'): fp = f32_mul(x['a'], x['b'])
        else: raise ValueError(f'unknown FP family: {family}')
        result = {'bits': fp.bits, 'flags': fp.flags}
    if result.keys() != case['outputs'].keys():
        raise ValueError('reference output signature mismatch')
    for name, width in case['outputs'].items():
        if type(result[name]) is not int or not 0 <= result[name] < 1 << width:
            raise ValueError('reference output exceeds declared width')
    return result


def evaluate_case(case_id, inputs):
    cases = {case['id']: case for case in case_manifest()['cases']}
    if case_id not in cases:
        raise ValueError(f'unknown revised case: {case_id}')
    return evaluate_spec(cases[case_id], inputs)


def main():
    for number, line in enumerate(sys.stdin, 1):
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            result = evaluate_case(request['case'], request['inputs'])
        except (ValueError, KeyError, TypeError) as error:
            raise SystemExit(f'revised reference input line {number}: {error}') from error
        print(json.dumps({'case': request['case'], 'outputs': result}, sort_keys=True))


if __name__ == '__main__':
    main()
