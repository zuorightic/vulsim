#!/usr/bin/env python3
"""Step-one wide arithmetic: Python integer oracle, VUL ports and RTLzz facts.

No physical-backend calls. Each preparation, generator, build, simulation and
oracle check is a support command in the existing cumulative ledger. Keep the
output directory to inspect vectors, generated RTL, traces and resource logs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
import re
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.processes import run_command

WIDTHS = (8, 16, 32, 64, 128)
PORT_WIDTHS = (128, 129, 193, 256, 257)
SEED = 20261029
MASK128 = (1 << 128) - 1
RESET = [MASK128] * 4 + [(1 << 256) - 1, (1 << 257) - 1, 127, 1]


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fields():
    result = []
    for w in WIDTHS:
        result.extend((f'{name}{w}', size) for name, size in (
            ('full', 2*w), ('low', w), ('dot', 2*w+1), ('mac', 2*w),
            ('sum', w), ('carry', w+1), ('diff', w), ('bits', w),
            ('left', w), ('right', w), ('less', 1)))
    return result + [('tag', 257), ('merged', 257),
                     ('constant_product', 256), ('constant_sum', 257)]


def reference(values):
    a, b, c, d, bias, tag, shift, carry = values
    result = []
    for w in WIDTHS:
        mask = (1 << w) - 1
        x, y, z, t = (v & mask for v in (a, b, c, d))
        p, q = x*y, z*t
        result.extend((p, p & mask, p+q, (p+bias) & ((1 << (2*w))-1),
                       (x+y) & mask, x+y+carry, (x-y) & mask,
                       (x & y) ^ (z | t), (x << (shift & (w-1))) & mask,
                       x >> (shift & (w-1)), int(x < y)))
    constant = MASK128*MASK128
    result.extend((tag, (a*b+c*d) ^ tag, constant, constant+constant+1))
    assert all(0 <= v < (1 << size) for v, (_, size) in zip(result, fields()))
    return result


def body(source, destination):
    lines = []
    for w in WIDTHS:
        lines += [f'Int<{w}> a{w} = Int<{w}>({source}.a);',
                  f'Int<{w}> b{w} = Int<{w}>({source}.b);',
                  f'Int<{w}> c{w} = Int<{w}>({source}.c);',
                  f'Int<{w}> d{w} = Int<{w}>({source}.d);',
                  f'Int<{2*w}> p{w} = a{w} * b{w};',
                  f'Int<{2*w}> q{w} = c{w} * d{w};',
                  f'{destination}.full{w} = p{w};',
                  f'{destination}.low{w} = Int<{w}>(p{w});',
                  f'{destination}.dot{w} = Int<{2*w+1}>(p{w}) + Int<{2*w+1}>(q{w});',
                  f'{destination}.mac{w} = p{w} + Int<{2*w}>({source}.bias);',
                  f'{destination}.sum{w} = a{w} + b{w};',
                  f'{destination}.carry{w} = AddCarry(a{w}, b{w}, {source}.carry);',
                  f'{destination}.diff{w} = a{w} - b{w};',
                  f'{destination}.bits{w} = (a{w} & b{w}) ^ (c{w} | d{w});',
                  f'{destination}.left{w} = a{w} << ({source}.shift.to<uint32_t>() & {w-1}u);',
                  f'{destination}.right{w} = a{w} >> ({source}.shift.to<uint32_t>() & {w-1}u);',
                  f'{destination}.less{w} = a{w} < b{w};']
    lines += [f'{destination}.tag = {source}.tag;',
              f'{destination}.merged = {destination}.dot128 ^ {source}.tag;',
              f'{destination}.constant_product = (~Int<128>(0)) * (~Int<128>(0));',
              f'{destination}.constant_sum = AddCarry({destination}.constant_product, '
              f'{destination}.constant_product, true);']
    return '\n'.join(lines)


def main_source(vectors):
    text = r'''#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <run.hpp>
TOP("Top.vul"); PROJECT(".");
REQUEST(push, ARG(Input) value, ARG(bool) valid);
REQUEST(combine, ARG(Input) value, RESP(Output) result);
QUERY(result, Output); QUERY(valid, bool);
'''
    text += ''.join(f'REQUEST(echo{w}, ARG(Int<{w}>) value, RESP(Int<{w}>) result);\n'
                    for w in PORT_WIDTHS)
    text += r'''
GLOBAL() {
template<uint32_t W> Int<W> read_hex(std::istream& stream) {
    std::string token;
    if (!(stream >> token)) { std::fprintf(stderr,"missing vector token\n"); std::exit(1); }
    Int<W> value{};
    for (size_t n=0; n<token.size(); ++n) {
        char c=token[token.size()-1-n];
        unsigned digit=c>='a' ? unsigned(c-'a'+10) : unsigned(c-'0');
        for (unsigned j=0; j<4; ++j) {
            unsigned bit=unsigned(n)*4+j;
            if (bit<W) {
                if constexpr (W==1) value=(digit>>j)&1;
                else value.template pick<1>(bit)=(digit>>j)&1;
            }
            else if ((digit>>j)&1) std::exit(2);
        }
    }
    return value;
}
template<uint32_t W> void print_hex(const Int<W>& value) {
    const auto words=value.get_data();
    std::putchar(' ');
    for (int nibble=int((W+3)/4)-1; nibble>=0; --nibble) {
        unsigned digit=0;
        for (unsigned j=0; j<4; ++j) {
            unsigned bit=unsigned(nibble)*4+j;
            if (bit<W && ((words[bit/64]>>(bit%64))&1)) digit|=1u<<j;
        }
        std::putchar("0123456789abcdef"[digit]);
    }
}
void print_output(const Output& output) {
'''
    text += ''.join(f'    print_hex(Int<{size}>(output.{name}));\n' for name, size in fields())
    text += r'''}
}
SIMULATION() {
    uint32_t echo_checks=0;
'''
    for w in PORT_WIDTHS:
        text += f'''    {{
        Int<{w}> value{{}}, response{{}};
        for (uint32_t bit=0; bit<{w}; ++bit) {{
            value=0; value.template pick<1>(bit)=1;
            echo{w}(value,response);
            if (response!=value) std::exit(3);
            sim_nextcycle(); ++echo_checks;
        }}
        value=~Int<{w}>(0); echo{w}(value,response);
        if (response!=value) std::exit(4);
        sim_nextcycle(); ++echo_checks;
        value=0; echo{w}(value,response);
        if (response!=value) std::exit(5);
        sim_nextcycle(); ++echo_checks;
    }}
'''
    text += f'    std::ifstream stream({json.dumps(str(vectors))});\n'
    text += r'''    unsigned count=0;
    if (!(stream >> count)) std::exit(6);
    sim_reset();
    std::printf("INITIAL %u",unsigned(valid())); print_output(result()); std::putchar('\n');
    for (unsigned cycle=0; cycle<count; ++cycle) {
        Input input{};
        input.a=read_hex<128>(stream); input.b=read_hex<128>(stream);
        input.c=read_hex<128>(stream); input.d=read_hex<128>(stream);
        input.bias=read_hex<256>(stream); input.tag=read_hex<257>(stream);
        input.shift=read_hex<8>(stream); input.carry=read_hex<1>(stream).to<bool>();
        bool iv=read_hex<1>(stream).to<bool>(), reset=read_hex<1>(stream).to<bool>();
        if (reset) sim_reset();
        Output comb{}; combine(input,comb);
        if (!reset) push(input,iv);
        sim_nextcycle();
        std::printf("ROW %u",cycle); print_output(comb);
        std::printf(" %u",unsigned(valid())); print_output(result()); std::putchar('\n');
    }
    sim_reset();
    std::printf("FINAL %u",unsigned(valid())); print_output(result()); std::putchar('\n');
    std::printf("WIDE RUN PASS rows=%u echo_checks=%u\n",count,echo_checks);
}
'''
    return text


def prepare(out):
    rng = random.Random(SEED)
    values = [[0]*8, RESET.copy()]
    for w in WIDTHS:
        mask = (1 << w)-1
        edges = sorted({0, 1, 2, mask, mask-1, 1 << (w-1), (1 << (w-1))-1,
                        (1 << min(32, w))-1, (1 << min(64, w))-1})
        for a in edges:
            for b in edges:
                values.append([a, b, mask, mask, rng.getrandbits(256),
                               rng.getrandbits(257), rng.randrange(128), (a+b) & 1])
    for bit in range(128):
        values.extend(([1 << bit, MASK128, MASK128, 1 << (127-bit),
                        (1 << 256)-1, 1 << bit, bit, bit & 1],
                       [MASK128, 1 << bit, 1 << bit, MASK128, 1,
                        1 << (bit+129), 127-bit, (bit+1) & 1]))
    for bit in range(257):
        values.append([rng.getrandbits(128) for _ in range(4)] +
                      [1 << min(bit, 255), 1 << bit, bit % 128, bit & 1])
    for _ in range(1024):
        values.append([rng.getrandbits(128) for _ in range(4)] +
                      [rng.getrandbits(256), rng.getrandbits(257), rng.randrange(128), rng.randrange(2)])
    rows = [v + [int(i < 400 or i % 7 not in (2, 3)), int(i in (0, 137, 138, 777, 1501))]
            for i, v in enumerate(values)]
    rows += [[0]*10 for _ in range(12)]
    write_json(out/'vectors.json', rows)
    (out/'vectors.txt').write_text(str(len(rows))+'\n'+''.join(
        ' '.join(f'{x:x}' for x in row)+'\n' for row in rows))
    write_json(out/'fields.json', fields())
    # The direct BEIR test consumes independent Python products, sums and limbs.
    facts = []
    for w in WIDTHS:
        mask = (1 << w)-1
        pairs = [(0, 0), (mask, mask), (1 << (w-1), 1 << (w-1)),
                 (mask, 1), (0, mask)]
        pairs += [(rng.getrandbits(w), rng.getrandbits(w)) for _ in range(32)]
        for a, b in pairs:
            c, d = mask, mask
            facts.append([w, a, b, c, d, a*b, a*b+c*d, a+b+1, (a-b)&mask, (a*b)&mask])
    (out/'facts.txt').write_text(''.join(str(row[0])+' '+' '.join(f'{v:x}' for v in row[1:])+'\n' for row in facts))
    header = '''CONFIG(LATENCY, 3);
STRUCT(Input) { Int<128> a; Int<128> b; Int<128> c; Int<128> d;
    Int<256> bias; Int<257> tag; Int<8> shift; bool carry; };
STRUCT(Output) {
'''+''.join(f'    {"bool" if size == 1 else f"Int<{size}>"} {name};\n'
            for name, size in fields())+'};\n'
    interface = '''INTERFACE() {
    SERVICE(push, ARG(Input) value, ARG(bool) valid);
    SERVICE(combine, ARG(Input) value, RESP(Output) result);
    QUERY(result, Output); QUERY(valid, bool);
'''+''.join(f'    SERVICE(echo{w}, ARG(Int<{w}>) value, RESP(Int<{w}>) result);\n'
            for w in PORT_WIDTHS)+'}\n'
    reset = '''input.a=~Int<128>(0); input.b=~Int<128>(0);
input.c=~Int<128>(0); input.d=~Int<128>(0);
input.bias=~Int<256>(0); input.tag=~Int<257>(0); input.shift=127; input.carry=true;'''
    top = interface+'PIPELINE(calculate, LATENCY, IREG(input, Input) {'+reset+'''
}, IVALID(iv), OREG(output, Output), OVALID(ov)) {
'''+body('input', 'output')+'''
}
SERVICE(push, ARG(Input) value, ARG(bool) valid) { input.setnext(value); iv.setnext(valid); }
QUERY(result, Output) { return output.get(); }
QUERY(valid, bool) { return ov; }
SERVICE(combine, ARG(Input) value, RESP(Output) result) {
'''+body('value', 'result')+'\n}\n'+''.join(
        f'SERVICE(echo{w}, ARG(Int<{w}>) value, RESP(Int<{w}>) result) {{ result=value; }}\n'
        for w in PORT_WIDTHS)
    for latency in (1, 3):
        case = out/f'case-L{latency}'
        case.mkdir()
        (case/'header.uh').write_text(header.replace('CONFIG(LATENCY, 3)', f'CONFIG(LATENCY, {latency})'))
        (case/'Top.vul').write_text(top)
        (case/'Main.utb').write_text(main_source(out/'vectors.txt'))
    print(f'PREPARED rows={len(rows)} facts={len(facts)} seed={SEED}', flush=True)


def check_trace(out, trace, latency):
    rows = json.loads((out/'vectors.json').read_text())
    description = fields()
    count = len(description)
    reset_output = reference(RESET)
    history, held = [], reset_output
    checks = {'comb_values': 0, 'pipeline_values': 0, 'valid_cycles': 0,
              'transactions': 0, 'bubble_cycles': 0, 'reset_cycles': 0}

    def check_values(tokens, expected, where):
        assert len(tokens) == count, (where, len(tokens), count)
        for token, value, (name, size) in zip(tokens, expected, description):
            observed = int(token, 16)
            assert 0 <= observed < (1 << size), (where, name, 'padding bits')
            assert observed == value, (where, name, hex(observed), hex(value))

    observed_rows = 0
    initial = final = echo = False
    with trace.open() as stream:
        for line in stream:
            tokens = line.split()
            if not tokens:
                continue
            if tokens[0] in ('INITIAL', 'FINAL'):
                assert tokens[1] == '0', line
                check_values(tokens[2:], reset_output, tokens[0])
                if tokens[0] == 'INITIAL':
                    initial = True
                else:
                    final = True
            elif tokens[0] == 'ROW':
                cycle = int(tokens[1])
                assert cycle == observed_rows < len(rows)
                row = rows[cycle]
                expected = reference(row[:8])
                check_values(tokens[2:2+count], expected, (cycle, 'comb'))
                checks['comb_values'] += count
                if row[9]:
                    history, held = [], reset_output
                    expected_valid = 0
                    checks['reset_cycles'] += 1
                else:
                    history.append((row[8], expected))
                    expected_valid = len(history) > latency and history[-latency-1][0]
                    if expected_valid:
                        held = history[-latency-1][1]
                        checks['transactions'] += 1
                    else:
                        checks['bubble_cycles'] += 1
                assert int(tokens[2+count]) == expected_valid, (cycle, 'valid')
                # The frozen cycle contract compares data only for valid
                # transactions (and explicit resets), not for invalid bubbles.
                if expected_valid or row[9]:
                    check_values(tokens[3+count:], held, (cycle, 'pipe/reset'))
                    checks['pipeline_values'] += count
                checks['valid_cycles'] += 1
                observed_rows += 1
            elif line.startswith('WIDE RUN PASS'):
                assert line.strip() == (f'WIDE RUN PASS rows={len(rows)} '
                                        f'echo_checks={sum(PORT_WIDTHS)+2*len(PORT_WIDTHS)}')
                echo = True
    assert initial and final and echo and observed_rows == len(rows)
    report = {'status': 'passed', 'L': latency, 'internal_boundaries': latency-1,
              'II': 1, 'rows': len(rows), 'fields_per_output': count, **checks,
              'echo_checks': sum(PORT_WIDTHS)+2*len(PORT_WIDTHS),
              'seed': SEED, 'oracle': 'Python arbitrary-precision integers',
              'invalid_data': 'not_compared_per_arithmetic-semantics-v1',
              'trace_sha256': digest(trace), 'vectors_sha256': digest(out/'vectors.txt')}
    write_json(trace.with_suffix('.checks.json'), report)
    print(json.dumps(report), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path,
                        default=ROOT/'build'/('step1-wide-'+uuid.uuid4().hex[:12]))
    parser.add_argument('--rtlzz-build', type=Path, default=ROOT/'build/step4-rtlzz')
    parser.add_argument('--compatibility-only', action='store_true',
                        help='run the inherited pipeline/valid/ports/mulu32 checks')
    parser.add_argument('--phase', choices=('prepare', 'check'))
    parser.add_argument('--trace', type=Path)
    parser.add_argument('--latency', type=int)
    args = parser.parse_args()
    out = args.output.resolve()
    if args.phase == 'prepare':
        prepare(out)
        return
    if args.phase == 'check':
        check_trace(out, args.trace, args.latency)
        return
    if out.exists():
        parser.error('use a new output directory to preserve evidence')
    out.mkdir(parents=True)
    ledger = Ledger()
    before = ledger.summary()
    commands = []
    env = os.environ.copy()

    def run(command, stem, timeout=300, cwd=ROOT):
        reservation = ledger.reserve(None, timeout, 2, 'step1_wide_validation', command, out/stem)
        previous = Path.cwd()
        try:
            os.chdir(cwd)
            record = run_command(command, out, stem, timeout, env,
                                 cpu_limit_s=reservation['CPU_time_s'])
        finally:
            os.chdir(previous)
        ledger.finish(reservation, record)
        record['budget_reservation_id'] = reservation['id']
        commands.append(record)
        write_json(out/'commands.json', commands)
        if record['exit_code']:
            raise RuntimeError(f'{stem}: see {record["log"]}')
        print(f'PASS {stem} ({record["walltime_s"]:.2f}s)', flush=True)
        return Path(record['log'])

    if args.compatibility_only:
        build = args.rtlzz_build.resolve()
        run(['cmake', '--build', ROOT/'build', '--target', 'vulrtlgen', 'vulsimgen', '-j2'], 'build-tools', 600)
        run(['cmake', '-S', ROOT/'rtlzz', '-B', build], 'configure-rtlzz')
        targets = ['pipeline-test', 'pipeline-reset-test', 'pipeline-valid-test', 'beopt-width-test']
        run(['cmake', '--build', build, '--target', *targets, '-j2'], 'build-inherited-unit-tests', 600)
        circt = env.get('VUL_REGRESSION_CIRCT', '1') != '0'
        for target in targets:
            run([build/'testv2'/target], target+'-native', cwd=ROOT/'rtlzz')
            if circt and target != 'beopt-width-test':
                run([build/'testv2'/target, '--circt'], target+'-circt', cwd=ROOT/'rtlzz')
        for script in ('generator_pipeline', 'generator_pipeline_instances',
                       'generator_pipeline_valid', 'generator_query_api', 'generator_rtl_baseline'):
            run([sys.executable, ROOT/'regression'/(script+'.py')], script, 1200)
        backends = [('sim', 'vulsimgen'), ('native', 'vulrtlgen')]
        if circt:
            backends.append(('circt', 'vulrtlgen'))
        for backend, tool in backends:
            generated = out/('mulu32-'+backend)
            flags = ['--circt'] if backend == 'circt' else []
            run([ROOT/'build'/tool, '-m', ROOT/'regression/mulu32/Main.utb',
                 '-o', generated, *flags], 'mulu32-'+backend+'-generate')
            log = run([generated/'run.sh'], 'mulu32-'+backend+'-run', 600)
            assert 'mulu32 regression passed: 100000 cycles' in log.read_text()
        write_json(out/'summary.json', {
            'version': 'step1-inherited-compatibility-v1', 'status': 'passed',
            'CIRCT': 'executed' if circt else 'explicitly_skipped',
            'commands': commands, 'usage_before': before, 'usage_after': ledger.summary(),
            'new_PPA_calls': {'synth': 0, 'grt': 0, 'final': 0}})
        print(f'INHERITED VALIDATION PASS output={out}', flush=True)
        return

    run([sys.executable, __file__, '--phase', 'prepare', '--output', out], 'prepare')
    run(['cmake', '--build', ROOT/'build', '--target', 'vulrtlgen', 'vulsimgen', '-j2'], 'build-tools', 600)
    build = args.rtlzz_build.resolve()
    run(['cmake', '-S', ROOT/'rtlzz', '-B', build], 'configure-rtlzz')
    run(['cmake', '--build', build, '--target', 'wide-value-test', '-j2'], 'build-facts', 600)
    run([build/'testv2/wide-value-test', out/'facts.txt'], 'facts')
    backends = [('sim', 'vulsimgen'), ('native', 'vulrtlgen')]
    circt = env.get('VUL_REGRESSION_CIRCT', '1') != '0'
    if circt:
        backends.append(('circt', 'vulrtlgen'))
    else:
        print('SKIP CIRCT checks: VUL_REGRESSION_CIRCT=0; all software/native checks continue', flush=True)
    reports = []
    for latency in (1, 3):
        for backend, tool in backends:
            stem = f'{backend}-L{latency}'
            generated = out/stem
            flags = ['--circt'] if backend == 'circt' else []
            run([ROOT/'build'/tool, '-m', out/f'case-L{latency}'/'Main.utb',
                 '-o', generated, *flags], stem+'-generate')
            trace = run([generated/'run.sh'], stem+'-run', 600)
            run([sys.executable, __file__, '--phase', 'check', '--output', out,
                 '--trace', trace, '--latency', latency], stem+'-oracle')
            report = json.loads(trace.with_suffix('.checks.json').read_text())
            report['backend'] = backend
            if backend != 'sim':
                rtl = generated/'sim/top.sv'
                report['RTL_sha256'] = digest(rtl)
                report['internal_valid_registers'] = len(re.findall(r'logic rtlzz_valid_s\d+;', rtl.read_text()))
                if backend == 'native':
                    assert report['internal_valid_registers'] == latency-1
            reports.append(report)
    summary = {'version': 'step1-wide-validation-v1', 'status': 'passed',
               'widths': WIDTHS, 'result_widths': [256, 257], 'port_widths': PORT_WIDTHS,
               'CIRCT': 'executed' if circt else 'explicitly_skipped',
               'facts': 'ValueFacts before/after BEOPT, Python expected limbs',
               'reports': reports, 'usage_before': before, 'usage_after': ledger.summary(),
               'new_PPA_calls': {'synth': 0, 'grt': 0, 'final': 0},
               'commands': commands,
               'artifacts_sha256': {name: digest(out/name) for name in
                                     ('vectors.json', 'vectors.txt', 'facts.txt', 'fields.json')}}
    write_json(out/'summary.json', summary)
    print(f'WIDE VALIDATION PASS output={out}', flush=True)


if __name__ == '__main__':
    main()
