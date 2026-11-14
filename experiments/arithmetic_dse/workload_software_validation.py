"""End-to-end W2 software acceptance with independent integer/cycle references.

Only RTLzz, Icarus and its runtime are executed. PATH backend entry points are
replaced by failing sentinels. Outputs are fresh, finite and preserve failures.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import random
import subprocess
import shlex
from . import workload_sources as sources, workload_demand as demand
from .workload_contracts import load, readiness

REPO = Path(__file__).resolve().parents[2]


def run(cmd, log, env, timeout=120):
    result = subprocess.run(list(map(str, cmd)), env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    Path(log).write_text(result.stdout)
    if result.returncode:
        raise RuntimeError(f'command failed ({result.returncode}); see {log}')
    return result.stdout


def reference(spec, held):
    op = spec['operation']
    if op == 'dot16':
        return dict(y=sum(held[f'a{i}'] * held[f'b{i}'] for i in range(16)))
    if op == 'horner64':
        return dict(y=sum(held[f'c{i}'] * held['x']**i for i in range(5)) % 2**64)
    if op == 'barrett64':
        m = held['modulus']
        if m:
            assert 2**63 < m < 2**64 and held['a'] < m and held['b'] < m and held['mu'] == 2**128 // m
        return dict(y=held['a'] * held['b'] % m if m else 0)
    if op == 'montgomery256':
        m = held['modulus']
        if m:
            assert 1 < m < 2**256 and m & 1 and held['a'] < m and held['b'] < m
            assert (m * held['nprime'] + 1) % 2**32 == 0
        return dict(y=held['a'] * held['b'] * pow(2**256, -1, m) % m if m else 0)
    if op == 'karatsuba256':
        return dict(y=held['a'] * held['b'] + held['c'])
    if op == 'ntt8x64':
        p, w = spec['modulus'], spec['omega']
        assert pow(w, 8, p) == 1 and pow(w, 4, p) == p - 1
        return {f'y{k}': sum(held[f'x{j}'] * pow(w, j*k, p) for j in range(8)) % p for k in range(8)}
    a, b = held['a'], held['b']
    value = a - b - held.get('cin', 0) if spec['operation'] == 'sub' else (
        a + b + held.get('cin', 0) if spec['operation'] == 'add' else a * b + held.get('c', 0))
    return dict(y=value & ((1 << spec['result_bits']) - 1))


def bench(spec, artifact, L, cycles=96):
    rng = random.Random(73019)
    inputs = spec['inputs']
    held = {name: 0 for name in inputs}
    valid = False
    pipe = [(False, reference(spec, held))] * (L - 1)
    outputs = spec.get('outputs', dict(y=spec['result_bits']))
    wires = ['reg clk=0;always #5 clk=~clk;', 'reg rstn=0,iv_data=0,iv_wen=0;', 'wire ov;']
    bindings = ['.clk(clk)', '.rstn(rstn)', '.iv_data(iv_data)', '.iv_wen(iv_wen)', '.ov(ov)']
    for name, width in outputs.items():
        wires.append(f'wire [{width-1}:0] {name};')
        bindings.append(f'.{name}({name})')
    for name, width in inputs.items():
        wires.append(f'reg [{width-1}:0] {name}_data=0;reg {name}_wen=0;')
        bindings += [f'.{name}_data({name}_data)', f'.{name}_wen({name}_wen)']
    lines = ['module tb;', *wires, 'Workload dut(' + ','.join(bindings) + ');', 'initial begin']
    checks = 0
    for cycle in range(cycles):
        reset = cycle in (0, 1, 38, 39)
        updates = {}
        for name, width in inputs.items():
            mask = (1 << width) - 1
            if cycle < 18:
                # Long carry/borrow propagation, maximum product, unequal
                # operands, and carry-in transitions before random traffic.
                values = (0, mask, 1, mask ^ 1, 1 << (width - 1), 0)
                value = values[(cycle + (name == 'b')) % len(values)]
                if cycle == 6:
                    value = mask
                elif cycle == 7 and name in ('a', 'b'):
                    value = int(name == 'b')
                elif cycle == 8 and name in ('a', 'b'):
                    value = mask if name == 'a' else 1
                if name == 'cin':
                    value = cycle & 1
                wen = True
            else:
                value, wen = rng.getrandbits(width), bool(rng.randrange(4))
            updates[name] = (value, wen)
        if spec['operation'] in ('barrett64', 'montgomery256'):
            # Correlated configuration inputs are updated together, while
            # data write enables can remain independent inside a fixed m.
            bits = inputs['modulus']
            change = not held['modulus'] or cycle % 13 == 2
            if spec['operation'] == 'barrett64':
                choices = [2**64-1, 2**63+2, 2**63+1, 2**64-2]
            else:
                choices = [2**256-1, 3, 2**32-5, 2**127+1, 2**255-19]
            proposed = choices[(cycle//13) % len(choices)] if cycle < 65 else rng.getrandbits(bits) | (1 << (bits-1))
            if spec['operation'] == 'montgomery256':
                proposed |= 1
            m = proposed if change else held['modulus']
            updates['modulus'] = (m, change)
            for name in ('a', 'b'):
                updates[name] = ((m-1 if cycle < 18 else rng.randrange(m)), change or updates[name][1])
            if spec['operation'] == 'barrett64':
                updates['mu'] = (2**128//m, change)
            else:
                updates['nprime'] = (-pow(m, -1, 2**32) % 2**32, change)
        elif spec['operation'] == 'ntt8x64':
            p = spec['modulus']
            edge = [0, p-1, 1, p-2, 2**63, 0]
            updates = {n: ((p-1 if cycle==6 else edge[(cycle+int(n[1:]))%len(edge)]) if cycle<18 else v % p, w)
                       for n,(v,w) in updates.items()}
        iv_data, iv_wen = bool(cycle % 7 not in (3, 4)), bool(cycle % 11 != 6)
        lines += ['@(negedge clk);', f'rstn={int(not reset)};iv_data={int(iv_data)};iv_wen={int(iv_wen)};']
        lines += [f'{name}_data={inputs[name]}\'h{value:x};{name}_wen={int(wen)};' for name, (value, wen) in updates.items()]
        if reset:
            held = {name: 0 for name in inputs}
            valid = False
            pipe = [(False, reference(spec, held))] * (L - 1)
            expected_valid, expected_y = False, reference(spec, held)
        else:
            current = (valid, reference(spec, held))
            if pipe:
                expected_valid, expected_y = pipe.pop(0)
                pipe.append(current)
            else:
                expected_valid, expected_y = current
            for name, (value, wen) in updates.items():
                if wen:
                    held[name] = value
            if iv_wen:
                valid = iv_data
        lines += ['@(posedge clk);#1;', f'if(ov !== 1\'b{int(expected_valid)}) $fatal(1,"valid cycle {cycle}");']
        if expected_valid or reset:
            for name, width in outputs.items():
                checks += 1
                lines += [f'if({name} !== {width}\'h{expected_y[name]:x}) $fatal(1,"data {name} cycle {cycle}: %h",{name});']
    lines += ['$display("PASS");$finish;end', 'initial begin #20000;$fatal(1,"timeout");end', 'endmodule']
    return '\n'.join(lines) + '\n', checks


def validate(out, binary):
    out = Path(out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    sentinels = out / 'no-eda-bin'
    sentinels.mkdir()
    marker = out / 'forbidden-backend-attempt'
    for name in ('yosys', 'abc', 'yosys-abc', 'openroad', 'opensta', 'sta'):
        path = sentinels / name
        path.write_text('#!/bin/sh\nprintf "forbidden backend\\n" > ' + shlex.quote(str(marker)) + '\nexit 97\n')
        path.chmod(0o755)
    env = dict(os.environ, PATH=str(sentinels) + os.pathsep + os.environ['PATH'])
    # Software targets are regression dimensions. They never fill the eight
    # applications' unresolved formal T/L entries.
    cases = [
        ('add513-L1-original', 'add', 512, 512, 513, False, 1, 0, 0),
        ('add512-wrap', 'add', 512, 512, 512, False, 3, 64, 0),
        ('add513-full', 'add', 512, 512, 513, False, 4, 64, 0),
        ('add129-tail', 'add', 127, 65, 129, False, 4, 17, 0),
        ('add65-overflow', 'add', 65, 65, 65, False, 4, 13, 0),
        ('sub513-extend', 'sub', 512, 512, 513, False, 3, 64, 0),
        ('sub512-wrap', 'sub', 512, 512, 512, False, 4, 63, 0),
        ('sub131-tail', 'sub', 127, 65, 131, False, 3, 19, 0),
        ('adc129', 'add', 127, 65, 129, True, 3, 17, 0),
        ('sbb129', 'sub', 127, 65, 129, True, 4, 17, 0),
        ('mul128-original', 'mul', 128, 128, 256, False, 4, 0, 0),
        ('mul128-block32', 'mul', 128, 128, 256, False, 4, 0, 32),
        ('mac32-block4', 'mac', 32, 32, 64, False, 3, 16, 4),
        ('dot16-block32', 'dot16', 0, 0, 132, False, 8, 0, 32),
        ('horner64', 'horner64', 0, 0, 64, False, 8, 0, 16),
        ('barrett64', 'barrett64', 0, 0, 64, False, 8, 0, 32),
        ('karatsuba256', 'karatsuba256', 0, 0, 513, False, 8, 64, 0),
        ('montgomery256', 'montgomery256', 0, 0, 256, False, 32, 0, 0),
        ('ntt8x64', 'ntt8x64', 0, 0, 64, False, 16, 0, 0),
    ]
    reports = []
    for name, op, wa, wb, r, carry, L, limb, block in cases:
        root = out / name
        spec = (sources.prepare(root / 'source', op, wa, wb, r, carry=carry)
                if wa else sources.prepare_case(root / 'source', op))
        run([binary, REPO, root / 'source/request.json', L, limb, 8, 100000, root / 'export', block, 1373], root / 'export.log', env)
        inv = json.loads((root / 'export/inventory.json').read_text())
        if not inv['views']:
            raise ValueError('no legal software placements')
        query = demand.extract(root / 'export', 1373.)
        (root / 'demand.json').write_text(json.dumps(query, indent=2) + '\n')
        actual_graph = demand.Graph(json.loads((root / 'export/graph.json').read_text()))
        g_checks = 0
        for seed in range(8):
            rng = random.Random(837 + seed)
            values = actual_graph.evaluate({p['name']: rng.getrandbits(p['width'])
                                            for p in actual_graph.ports if p['input']})
            for v in query['views']:
                for region in v['G']['regions']:
                    if region['geometry_status'] != 'represented':
                        continue
                    predicted = sum(((values[int(source)] >> bit) & 1) << column
                                    for term in region['terms'] for source, bit, column in term)
                    mask = (1 << region['output_bits']) - 1
                    if predicted & mask != values[region['root']] & mask:
                        raise ValueError('G member replacement changed arithmetic')
                    g_checks += 1
        # Consume the actual new graph descriptors through the existing C++
        # wide ABI as well; compare real values instead of feature names only.
        represented = [row for v in query['views'] for row in v['operators']
                       if row['interface_status'] == 'represented']
        native_query = Path(binary).parent / 'testv2/arithmetic-wide-query-test'
        (root / 'queries.json').write_text(json.dumps([dict(query=row['query']) for row in represented]))
        run([native_query, root / 'queries.json', root / 'native-queries.json'], root / 'queries.log', env)
        native_results = json.loads((root / 'native-queries.json').read_text())
        for row, actual in zip(represented, native_results, strict=True):
            expected = demand.wide.features(row['query'])
            if not actual['accepted'] or expected.keys() != actual['features'].keys() or any(
                    not math.isclose(v, actual['features'][k], rel_tol=1e-12, abs_tol=1e-8) for k,v in expected.items()):
                raise ValueError('wide Query Python/C++ mismatch')
        functional = []
        for view in inv['views']:
            dest = root / 'export' / view['directory']
            tb, checks = bench(spec, view['artifact'], L)
            (dest / 'tb.sv').write_text(tb)
            run(['iverilog', '-g2012', '-s', 'tb', '-o', dest / 'sim.out', dest / 'workload.sv', dest / 'tb.sv'], dest / 'iverilog.log', env)
            output = run(['vvp', dest / 'sim.out'], dest / 'simulation.log', env)
            if 'PASS' not in output:
                raise ValueError('simulation did not finish')
            functional.append(dict(view=view['directory'], cycles=96, result_checks=checks))
        reports.append(dict(case=name, L=L, limb=limb, mul_block=block, search=inv['search'],
                            native_state_projection_checked=True,
                            price_qualification_granted=False, functional=functional,
                            query_rows=sum(len(v['operators']) for v in query['views']),
                            native_wide_query_checks=len(represented),
                            G_regions=sum(len(v['G']['regions']) for v in query['views']),
                            G_integer_replacement_checks=g_checks,
                            interface_gaps=sum(row['interface_status'] != 'represented' for v in query['views'] for row in v['operators'])))
    # Force the finite stop before any complete assignment: preserve a clear
    # incomplete result rather than silently selecting from a partial prefix.
    cap_root = out / 'budget-stop'
    cap_root.mkdir()
    req = out / 'add513-full/source/request.json'
    result = subprocess.run([str(binary), str(REPO), str(req), '3', '64', '8', '1', str(cap_root / 'export')],
                            env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=120)
    (cap_root / 'export.log').write_text(result.stdout)
    stop = json.loads((cap_root / 'export/inventory.json').read_text())
    if result.returncode != 2 or not stop['search']['budget_exhausted'] or stop['views']:
        raise ValueError('finite search budget did not fail closed')
    if marker.exists():
        raise ValueError('backend startup attempted')
    report = dict(version='W1W2-software-acceptance-v1', status='passed',
                  binary_sha256=hashlib.sha256(Path(binary).read_bytes()).hexdigest(),
                  contracts=readiness(load()), cases=reports, budget_stop_checked=True,
                  backend_startup_sentinels='yosys/abc/yosys-abc/openroad/opensta/sta; fail immediately',
                  backend_startup_attempts=0, new_EDA_calls=0, independent_labels_read=False,
                  formal_application_targets_modified=False, full_D_ready=False)
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', required=True, type=Path)
    p.add_argument('--binary', required=True, type=Path)
    args = p.parse_args()
    result = validate(args.out, args.binary.resolve())
    print(json.dumps(dict(status=result['status'], cases=len(result['cases']),
                          placements=sum(len(c['functional']) for c in result['cases']),
                          new_EDA_calls=0, full_D_ready=False), indent=2))
