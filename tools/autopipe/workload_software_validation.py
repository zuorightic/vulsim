"""Frozen v10 runtime functions; extracted without numerical edits from workload_software_validation.py."""
import random

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
