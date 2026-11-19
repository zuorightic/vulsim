#!/usr/bin/env python3
"""AddCarry arithmetic and packed Verilator ports across word boundaries."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
CIRCT_ENABLED = os.environ.get('VUL_REGRESSION_CIRCT', '1') != '0'
BACKENDS = [('sim', 'vulsimgen'), ('native', 'vulrtlgen')]
if CIRCT_ENABLED:
    BACKENDS.append(('circt', 'vulrtlgen'))
ADD_WIDTHS = (1, 8, 16, 32, 64, 96)
PORT_WIDTHS = (65, 80, 96, 127, 128, 129, 193, 256)

HEADER = '''CONFIG(LATENCY, 3);
STRUCT(Input) { Int<96> lhs; Int<96> rhs; bool carry; Int<193> tag; };
STRUCT(Output) {
'''
HEADER += ''.join(f'    Int<{w+1}> sum{w};\n' for w in ADD_WIDTHS)
HEADER += '''    Int<4> truncated;
    Int<128> extended;
    Int<9> no_carry;
    Int<9> one_carry;
    Int<193> tag;
};
'''

TOP = '''INTERFACE() {
    SERVICE(push, ARG(Input) value, ARG(bool) valid);
    QUERY(result, Output);
    QUERY(valid, bool);
'''
TOP += ''.join(f'    SERVICE(echo{w}, ARG(Int<{w}>) value, RESP(Int<{w}>) result);\n'
               for w in PORT_WIDTHS)
TOP += '''}
PIPELINE(calculate, LATENCY, IREG(input, Input), IVALID(iv),
         OREG(output, Output), OVALID(ov)) {
'''
for w in ADD_WIDTHS:
    TOP += (f'    output.sum{w} = AddCarry(Int<{w}>(input.lhs), '
            f'Int<{w}>(input.rhs), input.carry);\n')
TOP += '''    output.truncated = AddCarry(Int<8>(input.lhs), Int<8>(input.rhs), input.carry);
    output.extended = AddCarry(Int<8>(input.lhs), Int<8>(input.rhs), Int<1>(input.carry));
    output.no_carry = AddCarry(Int<8>(input.lhs), Int<8>(input.rhs));
    output.one_carry = AddCarry(Int<8>(input.lhs), Int<8>(input.rhs), true);
    output.tag = input.tag;
}
SERVICE(push, ARG(Input) value, ARG(bool) valid) { input.setnext(value); iv.setnext(valid); }
QUERY(result, Output) { return output.get(); }
QUERY(valid, bool) { return ov; }
'''
TOP += ''.join(f'SERVICE(echo{w}, ARG(Int<{w}>) value, RESP(Int<{w}>) result) '
               '{ result=value; }\n' for w in PORT_WIDTHS)

MAIN = '''#include <cstdlib>
#include <cstdio>
#include <vector>
#include <run.hpp>
TOP("Top.vul"); PROJECT(".");
REQUEST(push, ARG(Input) value, ARG(bool) valid);
QUERY(result, Output); QUERY(valid, bool);
'''
MAIN += ''.join(f'REQUEST(echo{w}, ARG(Int<{w}>) value, RESP(Int<{w}>) result);\n'
                for w in PORT_WIDTHS)
MAIN += '''SIMULATION() {
    auto fail = [](const char* what) { printf("BASELINE FAIL: %s\\n", what); std::exit(1); };
    auto bits = []<uint32_t Width>(__uint128_t raw) {
        Int<Width> value{};
        for (uint32_t bit=0; bit<Width; ++bit)
            value.template pick<1>(bit)=uint32_t((raw>>bit)&1);
        return value;
    };
    auto raw96 = [](const Int<96>& value) {
        return __uint128_t(uint64_t(value.template at<63,0>())) |
               (__uint128_t(uint32_t(value.template at<95,64>()))<<64);
    };
    auto check = [&](const Input& input, const Output& output) {
        const __uint128_t a=raw96(input.lhs), b=raw96(input.rhs);
'''
for w in ADD_WIDTHS:
    MAIN += (f'        const __uint128_t mask{w}=(__uint128_t(1)<<{w})-1;\n'
             f'        if (output.sum{w} != bits.template operator()<{w+1}>('
             f'(a&mask{w})+(b&mask{w})+input.carry)) fail("sum{w}");\n')
MAIN += '''        const __uint128_t sum=(a&255)+(b&255)+input.carry;
        if (output.truncated != bits.template operator()<4>(sum)) fail("truncated");
        if (output.extended.template at<127,64>() != Int<64>(0) ||
            uint64_t(output.extended.template at<63,0>()) != uint64_t(sum)) fail("extended");
        if (output.no_carry != bits.template operator()<9>((a&255)+(b&255))) fail("no carry");
        if (output.one_carry != bits.template operator()<9>((a&255)+(b&255)+1)) fail("one carry");
        if (output.tag != input.tag) fail("packed tag");
    };
    uint32_t checks=0;
    for (uint32_t pass=0; pass<2; ++pass) {
        sim_reset();
        check(Input{}, result());
        if (valid()) fail("reset valid");
'''
for w in PORT_WIDTHS:
    MAIN += f'''        {{
            Int<{w}> value{{}}, response{{}};
            // Move a single bit through every position, including the top word.
            for (uint32_t bit=0; bit<{w}; ++bit) {{
                value=0; value.template pick<1>(bit)=1;
                echo{w}(value, response);
                if (response!=value) fail("echo{w} walking bit");
                sim_nextcycle();
                ++checks;
            }}
            value=~Int<{w}>(0);
            echo{w}(value, response);
            if (response!=value) fail("echo{w} all ones");
            sim_nextcycle();
            value=0;
            echo{w}(value, response);
            if (response!=value) fail("echo{w} clear");
            sim_nextcycle();
            checks+=2;
        }}
'''
MAIN += '''        std::vector<Input> history;
        std::vector<bool> validity;
        uint64_t random=0x123456789abcdef0ULL+pass;
        auto next = [&]() { random=random*6364136223846793005ULL+1442695040888963407ULL; return random; };
        const uint64_t edges[6]={0,1,0xffffffffffffffffULL,0x8000000000000000ULL,
                                 0x7fffffffffffffffULL,0xaaaaaaaaaaaaaaaaULL};
        for (uint32_t i=0; i<192+LATENCY+2; ++i) {
            Input value{};
            const bool edge=i<72;
            value.lhs.template at<63,0>()=edge ? edges[(i/2)%6] : next();
            value.rhs.template at<63,0>()=edge ? edges[(i/12)%6] : next();
            value.lhs.template at<95,64>()=edge ? uint32_t(edges[(i/2)%6]) : uint32_t(next());
            value.rhs.template at<95,64>()=edge ? uint32_t(edges[(i/12)%6]) : uint32_t(next());
            value.carry=bool(i&1);
            for (uint32_t bit=0; bit<193; ++bit)
                value.tag.template pick<1>(bit)=uint32_t(((bit+i+pass)%3)==0);
            const bool v=i<192 && (i<72 || i%7!=3);
            push(value,v);
            history.push_back(value); validity.push_back(v);
            sim_nextcycle();
            const int source=int(i)-int(LATENCY);
            const bool expected_valid=source>=0 && validity[source];
            if (valid()!=expected_valid) fail("cycle alignment");
            if (expected_valid) { check(history[source],result()); ++checks; }
        }
        // Leave valid transactions in flight before the next reset.
        Input pending{}; pending.lhs=~Int<96>(0); pending.rhs=1; pending.carry=true;
        for (uint32_t i=0; i<LATENCY+1; ++i) { push(pending,true); sim_nextcycle(); }
    }
    sim_reset(); check(Input{},result());
    if (valid()) fail("final reset valid");
    printf("RTL BASELINE PASS checks=%u\\n",checks);
}
'''


def run(args):
    result = subprocess.run(list(map(str, args)), cwd=ROOT, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    if result.returncode:
        raise AssertionError(f'{args}: exit={result.returncode}\n{result.stdout[-10000:]}')
    return result.stdout


with tempfile.TemporaryDirectory(prefix='vul-rtl-baseline-') as directory:
    case = Path(directory)
    for name, source in [('header.uh', HEADER), ('Top.vul', TOP), ('Main.utb', MAIN)]:
        (case/name).write_text(source)
    for backend, tool in BACKENDS:
        output = case/backend
        flags = ['--circt'] if backend == 'circt' else []
        run([ROOT/'build'/tool, '-m', case/'Main.utb', '-o', output, *flags])
        log = run([output/'run.sh'])
        assert 'RTL BASELINE PASS' in log, log
        print(f'PASS {backend}: {log.strip().splitlines()[-1]}', flush=True)
