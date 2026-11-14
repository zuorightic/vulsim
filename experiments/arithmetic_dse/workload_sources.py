"""Generate unpipelined diagnostic C++ sources, never a hand-staged RTL design.

Application contracts decide formal semantics/T/L separately. Explicit dimensions
here also serve unseen arithmetic and carry-chain regression cases.
"""
import argparse
import hashlib
import json
from pathlib import Path
from .workload_contracts import load


class AlgorithmSource:
    """Unscheduled mathematical DAG expressed in ordinary VUL C++."""
    def __init__(self, inputs):
        self.inputs, self.lines = inputs, []

    def value(self, width, expression):
        name = f'n{len(self.lines)}'
        self.lines.append(f'    Int<{width}> {name} = {expression};')
        return name

    def finish(self, outputs):
        lines = ['#include <fixint.hpp>']
        for name, width in self.inputs.items():
            lines += [f'#pragma input_port {name}', f'Int<{width}> {name};']
        lines += ['#pragma input_port iv', 'bool iv;']
        for name, (width, _) in outputs.items():
            lines += [f'#pragma output_port {name}', f'Int<{width}> {name};']
        lines += ['#pragma output_port ov', 'bool ov;', 'void workload_top() {', *self.lines]
        lines += [f'    {name} = {value};' for name, (_, value) in outputs.items()]
        return '\n'.join(lines + ['}']) + '\n'


def literal(width, value):
    if value < 0 or value >= 1 << width:
        raise ValueError('unsigned literal outside width')
    if value < 1 << 64:
        return f'Int<{width}>({value}ULL)'
    return f'(({literal(width, value >> 64)} << 64) + {literal(width, value & ((1 << 64)-1))})'


def barrett(g, a, b, modulus, mu):
    x = g.value(128, f'Int<128>({a}) * Int<128>({b})')
    scaled = g.value(193, f'Int<193>({x}) * Int<193>({mu})')
    q = g.value(65, f'{scaled}.at<192,128>()')
    qm = g.value(129, f'Int<129>({q}) * Int<129>({modulus})')
    r = g.value(129, f'Int<129>({x}) - {qm}')
    corrected = g.value(129, f'({r} < Int<129>({modulus})) ? {r} : ({r} - Int<129>({modulus}))')
    return g.value(64, f'Int<64>({corrected})')


def karatsuba(g, a, b, width, base=64):
    if width <= base:
        return g.value(2 * width, f'Int<{2*width}>({a}) * Int<{2*width}>({b})')
    low, high = (width + 1) // 2, width // 2
    al = g.value(low, f'{a}.at<{low-1},0>()')
    bl = g.value(low, f'{b}.at<{low-1},0>()')
    ah = g.value(high, f'{a}.at<{width-1},{low}>()')
    bh = g.value(high, f'{b}.at<{width-1},{low}>()')
    z0 = karatsuba(g, al, bl, low, base)
    z2 = karatsuba(g, ah, bh, high, base)
    sa = g.value(low+1, f'Int<{low+1}>({al}) + Int<{low+1}>({ah})')
    sb = g.value(low+1, f'Int<{low+1}>({bl}) + Int<{low+1}>({bh})')
    z1 = karatsuba(g, sa, sb, low+1, base)
    middle = g.value(2*(low+1), f'{z1} - Int<{2*(low+1)}>({z0}) - Int<{2*(low+1)}>({z2})')
    return g.value(2*width, f'Int<{2*width}>({z0}) + (Int<{2*width}>({middle}) << {low}) + (Int<{2*width}>({z2}) << {2*low})')


def limb_product(g, a, b, width=290):
    terms = []
    for j in range(8):
        limb = g.value(32, f'{b}.at<{32*j+31},{32*j}>()')
        p = g.value(64, f'Int<64>({a}) * Int<64>({limb})')
        terms.append(g.value(width, f'Int<{width}>({p}) << {32*j}'))
    while len(terms) > 1:
        terms = [g.value(width, f'{terms[i]} + {terms[i+1]}') for i in range(0, len(terms), 2)]
    return terms[0]


def arithmetic_source(operation, lhs_bits, rhs_bits, result_bits, *, carry=False):
    for width in (lhs_bits, rhs_bits, result_bits):
        if type(width) is not int or not 1 <= width <= 4096:
            raise ValueError('software scalar widths must be 1..4096')
    if operation not in ('add', 'sub', 'mul', 'mac') or (carry and operation not in ('add', 'sub')):
        raise ValueError('unsupported software source operation')
    inputs = dict(a=lhs_bits, b=rhs_bits)
    sign = dict(add='+', sub='-', mul='*', mac='*')[operation]
    if carry:
        inputs['cin'] = 1
    if operation == 'mac':
        inputs['c'] = result_bits
    # Cast before arithmetic: explicit modulo-result semantics, full product
    # when R=A+B. No host integers hold the datapath values.
    expr = f'(Int<{result_bits}>(a) {sign} Int<{result_bits}>(b))'
    if carry:
        expr += f' {sign} Int<{result_bits}>(cin)'
    if operation == 'mac':
        expr += f' + Int<{result_bits}>(c)'
    lines = ['#include <fixint.hpp>']
    for name, width in inputs.items():
        lines += [f'#pragma input_port {name}', f'Int<{width}> {name};']
    lines += ['#pragma input_port iv', 'bool iv;', '#pragma output_port y',
              f'Int<{result_bits}> y;', '#pragma output_port ov', 'bool ov;',
              'void workload_top() {', f'    y = {expr};', '}']
    return '\n'.join(lines) + '\n', inputs


def _write(out, source, inputs, spec):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=False)
    (out / 'source.cpp').write_text(source)
    spec = dict(spec, inputs=inputs, source_role='software_diagnostic_not_training_or_independent',
                formal_application_semantics_frozen=False)
    request = dict(version='D-source-metadata-v1', source=dict(
        source='source.cpp', source_label='workload.cpp', top='workload_top', iv='iv', ov='ov',
        reset={name: ['0'] * ((width + 63) // 64) for name, width in (inputs | {'iv': 1}).items()},
        generated_source_sha256=hashlib.sha256(source.encode()).hexdigest()))
    (out / 'request.json').write_text(json.dumps(request, indent=2) + '\n')
    (out / 'semantics.json').write_text(json.dumps(spec, indent=2) + '\n')
    return spec


def prepare(out, operation, lhs_bits, rhs_bits, result_bits, *, carry=False):
    source, inputs = arithmetic_source(operation, lhs_bits, rhs_bits, result_bits, carry=carry)
    return _write(out, source, inputs, dict(operation=operation, lhs_bits=lhs_bits,
                  rhs_bits=rhs_bits, result_bits=result_bits, carry=carry))


def prepare_case(out, case_id):
    case = next(c for c in load()['cases'] if c['id'] == case_id)
    if not case['semantic_status'].startswith('confirmed'):
        raise ValueError('application mathematical semantics not confirmed')
    if case_id in ('mac32', 'add512', 'mul128'):
        op = dict(mac32='mac', add512='add', mul128='mul')[case_id]
        return prepare(out, op, case['inputs']['a'], case['inputs']['b'], case['result_bits'])
    if case_id == 'dot16':
        inputs = {f'{side}{lane}': 64 for lane in range(16) for side in ('a', 'b')}
        lines = ['#include <fixint.hpp>']
        for name, width in inputs.items():
            lines += [f'#pragma input_port {name}', f'Int<{width}> {name};']
        lines += ['#pragma input_port iv', 'bool iv;', '#pragma output_port y', 'Int<132> y;',
                  '#pragma output_port ov', 'bool ov;', 'void workload_top() {']
        terms = []
        for lane in range(16):
            terms.append(f'p{lane}')
            lines += [f'    Int<132> p{lane} = Int<132>(Int<128>(a{lane}) * Int<128>(b{lane}));']
        level = 0
        while len(terms) > 1:
            following = []
            for i in range(0, len(terms), 2):
                name = f's{level}_{i//2}'
                lines += [f'    Int<132> {name} = {terms[i]} + {terms[i+1]};']
                following.append(name)
            terms, level = following, level + 1
        lines += [f'    y = {terms[0]};', '}']
        return _write(out, '\n'.join(lines) + '\n', inputs,
                      dict(operation='dot16', result_bits=132, carry=False))
    if case_id == 'horner64':
        inputs = dict(x=64, **{f'c{i}': 64 for i in range(5)})
        g = AlgorithmSource(inputs)
        y = 'c4'
        for i in reversed(range(4)):
            product = g.value(64, f'{y} * x')
            y = g.value(64, f'{product} + c{i}')
        return _write(out, g.finish(dict(y=(64,y))), inputs,
                      dict(operation=case_id, result_bits=64, carry=False))
    if case_id == 'barrett64':
        inputs = dict(a=64, b=64, modulus=64, mu=65)
        g = AlgorithmSource(inputs)
        y = barrett(g, 'a', 'b', 'modulus', 'mu')
        return _write(out, g.finish(dict(y=(64,y))), inputs,
                      dict(operation=case_id, result_bits=64, carry=False,
                           constraints='2^63<m<2^64; a,b<m; mu=floor(2^128/m)'))
    if case_id == 'karatsuba256':
        inputs = dict(a=256, b=256, c=512)
        g = AlgorithmSource(inputs)
        product = karatsuba(g, 'a', 'b', 256)
        y = g.value(513, f'Int<513>({product}) + Int<513>(c)')
        return _write(out, g.finish(dict(y=(513,y))), inputs,
                      dict(operation=case_id, result_bits=513, carry=False, base_case_bits=64))
    if case_id == 'montgomery256':
        inputs = dict(a=256, b=256, modulus=256, nprime=32)
        g = AlgorithmSource(inputs)
        t = g.value(290, '0')
        for i in range(8):
            ai = g.value(32, f'a.at<{32*i+31},{32*i}>()')
            product = limb_product(g, ai, 'b')
            t = g.value(290, f'{t} + {product}')
            low = g.value(32, f'Int<32>({t})')
            correction = g.value(32, f'{low} * nprime')
            multiple = limb_product(g, correction, 'modulus')
            total = g.value(290, f'{t} + {multiple}')
            t = g.value(290, f'{total} >> 32')
        reduced = g.value(290, f'({t} < Int<290>(modulus)) ? {t} : ({t} - Int<290>(modulus))')
        y = g.value(256, f'Int<256>({reduced})')
        return _write(out, g.finish(dict(y=(256,y))), inputs,
                      dict(operation=case_id, result_bits=256, carry=False, limb_bits=32,
                           constraints='1<m<2^256 odd; a,b<m; nprime=-inverse(m) modulo 2^32'))
    if case_id == 'ntt8x64':
        p = 2**64 - 2**32 + 1
        omega = pow(7, (p-1)//8, p)
        inputs = {f'x{i}': 64 for i in range(8)}
        g = AlgorithmSource(inputs)
        modulus = g.value(64, literal(64, p))
        mu = g.value(65, literal(65, 2**128//p))
        values = [f'x{int(f"{i:03b}"[::-1],2)}' for i in range(8)]
        for size in (2, 4, 8):
            following = list(values)
            for start in range(0, 8, size):
                for j in range(size//2):
                    u, v = values[start+j], values[start+j+size//2]
                    twiddle = pow(omega, j*8//size, p)
                    if twiddle != 1:
                        w = g.value(64, literal(64, twiddle))
                        v = barrett(g, v, w, modulus, mu)
                    total = g.value(65, f'Int<65>({u}) + Int<65>({v})')
                    plus = g.value(65, f'({total} < Int<65>({modulus})) ? {total} : ({total} - Int<65>({modulus}))')
                    diff = g.value(65, f'Int<65>({u}) + Int<65>({modulus}) - Int<65>({v})')
                    minus = g.value(65, f'({diff} < Int<65>({modulus})) ? {diff} : ({diff} - Int<65>({modulus}))')
                    following[start+j] = g.value(64, f'Int<64>({plus})')
                    following[start+j+size//2] = g.value(64, f'Int<64>({minus})')
            values = following
        outputs = {f'y{i}': (64, v) for i, v in enumerate(values)}
        return _write(out, g.finish(outputs), inputs,
                      dict(operation=case_id, result_bits=64, outputs={n:64 for n in outputs},
                           carry=False, modulus=p, omega=omega,
                           constraints='each x_i in [0,p); forward unscaled natural order'))
    raise ValueError('algorithm source generator not implemented for this confirmed case')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', required=True, type=Path)
    parser.add_argument('--case', choices=tuple(c['id'] for c in load()['cases']))
    parser.add_argument('--operation', choices=('add', 'sub', 'mul', 'mac'))
    parser.add_argument('--lhs-bits', type=int)
    parser.add_argument('--rhs-bits', type=int)
    parser.add_argument('--result-bits', type=int)
    parser.add_argument('--carry', action='store_true')
    args = parser.parse_args()
    if args.case:
        if args.operation or args.carry or any(x is not None for x in (args.lhs_bits, args.rhs_bits, args.result_bits)):
            parser.error('named application and diagnostic dimensions are mutually exclusive')
        result = prepare_case(args.out, args.case)
    else:
        result = prepare(args.out, args.operation, args.lhs_bits, args.rhs_bits, args.result_bits, carry=args.carry)
    print(json.dumps(result, indent=2))
