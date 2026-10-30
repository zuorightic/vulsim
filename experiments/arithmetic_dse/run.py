"""Generate, validate, and evaluate the original full-width multiplier probe."""
import argparse
import json
import os
from pathlib import Path
import sys

from .backend import ROOT, run_command, sha256, write_json
from .budget import Ledger, POLICY
from .platforms import profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform',choices=['asap7','nangate45','sky130hd','gf180'],default='asap7')
    parser.add_argument('--abc-target-ps',type=float,help='separate ps ABC target; defaults to SDC period')
    parser.add_argument('--out', type=Path, required=True, help='new evidence directory')
    parser.add_argument('--orfs', type=Path, default=Path('/home/zyrv/OpenROAD-flow-scripts'))
    parser.add_argument('--period-ps', type=float, help='resource trial only; defaults to the platform profile, not a main-case target')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--stage', choices=['synth','grt','final'], default='grt')
    parser.add_argument('--budget-purpose', choices=['prototype','characterization','search','final_evaluation','physical_recheck','repeat','retry'], default='prototype')
    args = parser.parse_args()
    selected=profile(args.platform)
    if args.period_ps is None:args.period_ps=selected['trial_period_ps']
    out = args.out.resolve()
    if out.exists():
        parser.error('use a new output directory to preserve earlier evidence')
    out.mkdir(parents=True)
    env = os.environ.copy()
    ledger = Ledger()
    manifest = {'version':'backend-probe-v3','target_platform':args.platform,'platform_profile_sha256':selected['profile_sha256'], 'status':'running', 'commands':[],
                'main_case_target':False, 'probe':'full_unsigned_32x32_to_64',
                'budget_ledger':str(ledger.path),
                'source_sha256':{str(p.relative_to(ROOT)):sha256(p)
                    for p in (ROOT/'experiments/arithmetic/backend_probe').iterdir() if p.is_file()}}
    def run(command, stem, timeout):
        reservation = ledger.reserve(None,timeout,1,'validation_or_generation',command,out/stem,
            context={'target_platform':args.platform,'admission_id':'explicit-single-probe-v3','task_id':stem})
        record = run_command(command, out, stem, timeout, env, cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record)
        record['budget_reservation_id'] = reservation['id']
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
        # This driver launches the leaf backend, which performs the authoritative
        # reservation. Do not charge this nesting wrapper or double-count CPU.
        command = [sys.executable, '-m', 'experiments.arithmetic_dse.backend','--platform',args.platform,
             '--rtl', str(out/'native/sim/top.sv'), '--top', 'MulProbe_sim_top',
             '--out', str(out/'evaluation'), '--orfs', str(args.orfs.resolve()),
             '--period-ps', str(args.period_ps), '--threads', str(args.threads), '--stage', args.stage,
             '--budget-purpose', args.budget_purpose]
        if args.abc_target_ps is not None:command += ['--abc-target-ps',str(args.abc_target_ps)]
        limits=json.loads(POLICY.read_text())['resources']
        outer_timeout=(limits['synthesis_timeout_s']+limits['floorplan_through_global_route_timeout_s']
                       +limits['detailed_route_extraction_timeout_s']+4*limits['snapshot_timeout_s'])
        record = run_command(command,out,'evaluate',outer_timeout,env)
        record['accounting_scope'] = 'wrapper_excluded_nested_leaf_commands_are_charged'
        manifest['commands'].append(record)
        write_json(out/'probe-manifest.json',manifest)
        if record['exit_code'] != 0:
            raise RuntimeError(f'evaluate: see {record["log"]}')
        manifest['status'] = 'completed'
    except Exception as error:
        manifest.update(status='failed', failure_reason=str(error))
    write_json(out/'probe-manifest.json', manifest)
    print(json.dumps({'status':manifest['status'], 'output':str(out)}, indent=2))
    return 0 if manifest['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
