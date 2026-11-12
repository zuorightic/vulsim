"""Short emitted-RTL check for a freshly compiled D consumer.

References the selected graph's integer semantics independently of its RTL and
models the public launch/valid/capture protocol, including reset and bubbles.
No expectations or physical prices enter online candidate selection.
"""

from pathlib import Path
import random
import re
import subprocess

from regression.arithmetic_fused_d import evaluate_graph


def rtl_check(cases, folder):
    folder.mkdir(parents=True, exist_ok=False)
    modules, declarations, initial, drive, checks = [], [], [], [], []
    valid_comparisons = 0
    cycles = 64
    for index, (out, report) in enumerate(cases):
        selected = next(row for row in report['candidates']
                        if row['view'] == report['selected_view'])
        ports = report['artifact']['ports']
        inputs = [p for p in ports if p['direction'] == 'input']
        outputs = [p for p in ports if p['direction'] == 'output']
        graph_ports = {p['name']: p for p in selected['ports']}
        if any(len(graph_ports[p['semantic_name']]['nodes']) != 1 for p in ports):
            raise ValueError('portable RTL check requires scalar ports')

        def reset(port):
            return int(port['reset_literal'].split("'h")[1], 16) & ((1 << port['width']) - 1)

        def reference(values):
            nodes = {graph_ports[p['semantic_name']]['nodes'][0]: values[p['name']] for p in inputs}
            return {p['name']: evaluate_graph(selected['graph'], nodes,
                    graph_ports[p['semantic_name']]['nodes'][0]) for p in outputs}

        held = {p['name']: reset(p) for p in inputs}
        reset_result = reference(held)
        if reset_result != {p['name']: reset(p) for p in outputs}:
            raise ValueError('graph/output reset differs')
        n = report['L'] - 1
        valid, data, iv = [0] * n, [dict(reset_result) for _ in range(n)], 0
        rng = random.Random(20261112)
        vectors = []
        for cycle in range(cycles):
            rst = int(cycle not in (0, 1, 23, 44))
            ivd, ivw = int(cycle % 5 != 2), int(cycle % 7 != 3)
            incoming = {p['name']: ((1 << p['width']) - 1 if cycle in (5, 6, 7)
                                   else rng.getrandbits(p['width'])) for p in inputs}
            enables = {p['name']: int((cycle + j) % 6 != 2) for j, p in enumerate(inputs)}
            expected = data[-1] if rst else reset_result
            ov = valid[-1] if rst else 0
            valid_comparisons += ov * len(outputs)
            fields = [(rst, 1), (ivd, 1), (ivw, 1)]
            fields += [(incoming[p['name']], p['width']) for p in inputs]
            fields += [(enables[p['name']], 1) for p in inputs]
            fields += [(expected[p['name']], p['width']) for p in outputs] + [(ov, 1)]
            word = 0
            for value, width in fields:
                word = (word << width) | value
            vectors.append(format(word, 'x'))
            if not rst:
                held = {p['name']: reset(p) for p in inputs}
                iv, valid, data = 0, [0] * n, [dict(reset_result) for _ in range(n)]
            else:
                oldv, oldd = valid[:], data[:]
                for stage in range(n):
                    enabled = iv if stage == 0 else oldv[stage - 1]
                    if enabled:
                        data[stage] = reference(held) if stage == 0 else oldd[stage - 1]
                valid = [iv] + oldv[:-1]
                held.update({name: incoming[name] for name in held if enables[name]})
                if ivw:
                    iv = ivd
        vector = folder / ('vectors' + str(index) + '.hex')
        vector.write_text('\n'.join(vectors) + '\n')
        raw = (Path(out) / 'D.sv').read_text()
        names = re.findall(r'\bmodule\s+(\w+)\s*\(', raw)
        rename = {name: 'Case' + str(index) + '_' + name for name in names}
        raw = re.sub(r'\b(?:' + '|'.join(re.escape(name) for name in sorted(names, key=len, reverse=True))
                     + r')\b', lambda m: rename[m[0]], raw)
        modules.append(raw)
        i = index
        bits = 3 + sum(p['width'] + 1 for p in inputs) + sum(p['width'] for p in outputs) + 1
        declarations.append(f'reg r{i},ivd{i},ivw{i};wire ov{i};reg ev{i};reg [{bits-1}:0] vectors{i}[0:{cycles-1}];')
        connections = ['.clk(clk)', f'.rstn(r{i})', f'.iv_data(ivd{i})', f'.iv_wen(ivw{i})', f'.ov(ov{i})']
        fields = [f'r{i}', f'ivd{i}', f'ivw{i}']
        for j, p in enumerate(inputs):
            declarations.append(f'reg [{p["width"]-1}:0] in{i}_{j};reg we{i}_{j};')
            connections += [f'.{p["name"]}_data(in{i}_{j})', f'.{p["name"]}_wen(we{i}_{j})']
            fields.append(f'in{i}_{j}')
        fields += [f'we{i}_{j}' for j in range(len(inputs))]
        for j, p in enumerate(outputs):
            declarations.append(f'wire [{p["width"]-1}:0] y{i}_{j};reg [{p["width"]-1}:0] e{i}_{j};')
            connections.append(f'.{p["name"]}(y{i}_{j})')
            fields.append(f'e{i}_{j}')
            checks.append(f'if((ev{i}||!r{i})&&y{i}_{j}!==e{i}_{j})$fatal(1,"data case{i} output{j} cycle%0d",cycle);')
        fields.append(f'ev{i}')
        declarations.append(f'Case{i}_D dut{i}(' + ','.join(connections) + ');')
        # Relative filenames make the generated testbench usable after moving
        # the checkout, and avoid quoting host paths in Verilog source.
        initial.append(f'$readmemh("{vector.name}",vectors{i});')
        drive.append('{' + ','.join(fields) + f'}}=vectors{i}[cycle];')
        checks.append(f'if(ov{i}!==ev{i})$fatal(1,"valid case{i} cycle%0d",cycle);')
    (folder / 'all.sv').write_text('\n'.join(modules))
    (folder / 'tb.sv').write_text('module TB;reg clk=0;integer cycle;\n' + '\n'.join(declarations)
        + '\ninitial begin\n' + '\n'.join(initial)
        + f'\nfor(cycle=0;cycle<{cycles};cycle=cycle+1)begin clk=0;\n' + '\n'.join(drive)
        + '\n#5;clk=1;#1;\n' + '\n'.join(checks)
        + '\n#4;end $display("PORTABLE_D_RTL_PASS");$finish;end endmodule\n')
    with (folder / 'compile.log').open('w') as stream:
        subprocess.run(['iverilog', '-g2012', '-s', 'TB', '-o', 'sim.vvp', 'all.sv', 'tb.sv'],
                       cwd=folder, stdout=stream, stderr=subprocess.STDOUT, timeout=60, check=True)
    with (folder / 'simulation.log').open('w') as stream:
        subprocess.run(['vvp', 'sim.vvp'], cwd=folder, stdout=stream, stderr=subprocess.STDOUT,
                       timeout=60, check=True)
    if 'PORTABLE_D_RTL_PASS' not in (folder / 'simulation.log').read_text():
        raise ValueError('missing RTL verification success')
    return dict(status='passed', cases=len(cases), cycles_per_case=cycles,
                valid_data_comparisons=valid_comparisons,
                behaviors=['independent input writes', 'held valid', 'bubbles',
                           'unsigned overflow', 'nonzero reset', 'in-flight reset'],
                reset_timing_checked=False)
