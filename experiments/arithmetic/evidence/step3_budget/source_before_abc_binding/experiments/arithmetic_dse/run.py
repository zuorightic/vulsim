"""Generate, validate, and evaluate the original full-width multiplier probe."""
import argparse
import json
import os
from pathlib import Path
import sys

from .backend import ROOT, run_command, sha256, write_json


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='new evidence directory')
    parser.add_argument('--orfs', type=Path, default=Path('/home/zyrv/OpenROAD-flow-scripts'))
    parser.add_argument('--period-ps', type=float, default=1500, help='resource trial only; not a main-case target')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--stage', choices=['synth','grt','final'], default='grt')
    parser.add_argument('--budget-purpose', choices=['prototype','characterization','search','final_evaluation','physical_recheck','repeat','retry'], default='prototype')
    args = parser.parse_args()
    out = args.out.resolve()
    if out.exists():
        parser.error('use a new output directory to preserve earlier evidence')
    out.mkdir(parents=True)
    env = os.environ.copy()
    manifest = {'version':'backend-probe-v1', 'status':'running', 'commands':[],
                'main_case_target':False, 'probe':'full_unsigned_32x32_to_64',
                'source_sha256':{str(p.relative_to(ROOT)):sha256(p)
                    for p in (ROOT/'experiments/arithmetic/backend_probe').iterdir() if p.is_file()}}
    def run(command, stem, timeout):
        record = run_command(command, out, stem, timeout, env)
        manifest['commands'].append(record)
        write_json(out/'probe-manifest.json', manifest)
        if record['exit_code'] != 0:
            raise RuntimeError(f'{stem}: see {record["log"]}')
    # Generator input is absolute; execution does not depend on the caller's cwd.
    try:
        for name, tool in [('sim','vulsimgen'), ('native','vulrtlgen')]:
            executable = ROOT/'build'/tool
            manifest[tool+'_sha256'] = sha256(executable)
            run([str(executable), '-m', str(ROOT/'experiments/arithmetic/backend_probe/Main.utb'),
                 '-f', '-o', str(out/name)], 'generate-'+name, 120)
            run(['bash',str(out/name/'run.sh')], 'validate-'+name, 300)
        run([sys.executable, '-m', 'experiments.arithmetic_dse.backend',
             '--rtl', str(out/'native/sim/top.sv'), '--top', 'MulProbe_sim_top',
             '--out', str(out/'evaluation'), '--orfs', str(args.orfs.resolve()),
             '--period-ps', str(args.period_ps), '--threads', str(args.threads), '--stage', args.stage,
             '--budget-purpose', args.budget_purpose],
             'evaluate', 2800)
        manifest['status'] = 'completed'
    except Exception as error:
        manifest.update(status='failed', failure_reason=str(error))
    write_json(out/'probe-manifest.json', manifest)
    print(json.dumps({'status':manifest['status'], 'output':str(out)}, indent=2))
    return 0 if manifest['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
