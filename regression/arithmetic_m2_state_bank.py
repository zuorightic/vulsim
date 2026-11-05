"""Actual RTL checks of state-bank register/reset/enable semantics and grouping."""
import argparse
import json
from pathlib import Path
import random
import subprocess
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from experiments.arithmetic_dse.budget import Ledger
from experiments.arithmetic_dse.model_collection import write, sha
from experiments.arithmetic_dse.model_m2_cec import leaf
from experiments.arithmetic_dse.model_m2_state_samples import specifications, features, source, step
from experiments.arithmetic_dse.model_m2_state_collection import CONFIG, run_task


def worker(out):
    out.mkdir(parents=True, exist_ok=False)
    cfg = json.loads(CONFIG.read_text())
    specs = specifications(cfg)
    if len(specs) != 48:
        raise ValueError('wrong source count')
    seen = set()
    for s in specs:
        text, labels = source(s)
        if text in seen or len(labels) != 3 or s['features'] != features(s, 1500):
            raise ValueError('duplicate source, labels or inconsistent static features')
        seen.add(text)
    # The fitting producer must refuse a test before creating a run or job.
    with patch('experiments.arithmetic_dse.model_m2_state_collection.verify', return_value={}):
        try:
            run_task(out, {'split': 'test'})
        except ValueError as e:
            if 'independent test' not in str(e):
                raise
        else:
            raise ValueError('independent state test was not locked')
    selected = ['state-train-small-w1', 'state-train-large-w37', 'state-train-large-w65',
                'state-validation-w32', 'state-test-w5']
    count = 0
    for name in selected:
        s = next(s for s in specs if s['id'] == name)
        directory = out/name
        directory.mkdir()
        rtl, _ = source(s)
        (directory/'bank.sv').write_text(rtl)
        names = [x['name'] for x in s['slots']]+[f'enable_q{i}' for i in range(s['separate_enable_registers'])]+[f'valid_q{i}' for i in range(s['valid_registers'])]
        state = dict.fromkeys(names, 0)
        declarations = ['reg clk=0,rstn=0,iv=0;wire y,ov;']
        declarations += [f'reg [{w["variable_width"]-1}:0] in{i}=0;' for i, w in enumerate(s['words'])]
        declarations += [f'reg en{i}=0;' for i in range(s['separate_enable_registers'])]
        connections = ['.clk(clk)', '.rstn(rstn)', '.iv(iv)', '.y(y)', '.ov(ov)']
        connections += [f'.in{i}(in{i})' for i in range(len(s['words']))]+[f'.en{i}(en{i})' for i in range(s['separate_enable_registers'])]
        bench = ['module tb;', *declarations, 'ModelBundle dut('+','.join(connections)+');', 'initial begin']
        rng = random.Random(20261105+sum(map(ord, name)))
        for cycle in range(80):
            inputs = {f'in{i}': rng.getrandbits(w['variable_width']) for i, w in enumerate(s['words'])}
            inputs.update({f'en{i}': int(cycle % (i+3) != 1) for i in range(s['separate_enable_registers'])})
            inputs['iv'] = int(cycle % 7 not in (1, 2))
            reset = cycle in (0, 1, 25, 53)
            state = step(s, state, inputs, reset)
            bench.append('clk=0;rstn='+str(int(not reset))+';'+''.join(f'{key}=65\'h{value:x};' for key, value in inputs.items())+'#4;clk=1;#1;')
            widths = {slot['name']: slot['variable_width'] for slot in s['slots']}
            for key, value in state.items():
                w = widths.get(key, 1)
                bench.append(f'if(dut.bank.{key} !== {w}\'h{value:x}) $fatal(1,"{name} cycle{cycle} {key}");')
                count += 1
            observed = 0
            for word in range(len(s['words'])):
                observed ^= state[f'dst{s["depth"]}_{word}'].bit_count() % 2
            last_valid = state['valid_q'+str(s['valid_registers']-1)]
            bench.append(f'if(y !== 1\'b{observed} || ov !== 1\'b{last_valid}) $fatal(1,"observer/valid cycle{cycle}");')
            bench.append('#1;clk=0;#4;')
        bench += ['$display("STATE_BANK_RTL_PASS");$finish;end', 'endmodule']
        (directory/'tb.sv').write_text('\n'.join(bench)+'\n')
        commands = [(['iverilog', '-g2012', '-s', 'tb', '-o', str(directory/'sim.out'),
                      str(directory/'bank.sv'), str(directory/'tb.sv')], 'compile.log'),
                    (['vvp', str(directory/'sim.out')], 'simulation.log')]
        for command, log in commands:
            result = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60)
            (directory/log).write_text(result.stdout)
            if result.returncode:
                raise ValueError(name+': '+result.stdout[-1500:])
        if 'STATE_BANK_RTL_PASS' not in (directory/'simulation.log').read_text():
            raise ValueError('missing RTL simulation verdict')
    result = {'status': 'passed', 'source_groups': len(specs), 'RTL_banks': len(selected),
        'cycles_per_bank': 80, 'full_register_vector_checks': count, 'test_collection_locked': True,
        'reset_zero_one_alternating_one_in_three': True, 'uses_previous_registered_enable': True,
        'padded_65_variable_64': True, 'PPA_calls': 0, 'valid_chain_enables': True,
        'protocol_sha256': sha(CONFIG),
        'generator_source_sha256': sha(ROOT/'experiments/arithmetic_dse/model_m2_state_samples.py')}
    write(out/'result.json', result)
    print(json.dumps(result), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('run', 'worker'))
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    if args.action == 'worker':
        worker(out)
        return
    out.mkdir(parents=True, exist_ok=False)
    ledger = Ledger()
    context = {'target_platform': 'asap7', 'admission_id': out.name, 'task_id': 'state-bank-RTL-regression'}
    with ledger.job(context):
        record = leaf([sys.executable, '-B', str(Path(__file__).resolve()), 'worker', '--out', str(out/'RTL')],
                      out, 'state-bank-RTL', 180, ledger, context)
        print(Path(record['log']).read_text(), flush=True)


if __name__ == '__main__':
    main()
