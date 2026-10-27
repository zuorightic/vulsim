"""Run one predeclared two-point SDC study; preserve failures without retries.

The ordinary backend performs and charges synth/grt. Reopening the resulting
ODB for common-SDC STA is a support command, with its own ledger reservation.
"""
import argparse
import json
from pathlib import Path
import shutil
import sys
import os

from .backend import ASSETS, ROOT, sha256, write_json, library_data, stage_metrics
from .budget import Ledger, POLICY, STAGE_LIMITS
from .processes import run_command


def admission(used, resources):
    requested = {'synth':2, 'grt':2, 'final':0}
    remaining = {s:resources[key]-used[s] for s,key in STAGE_LIMITS.items()}
    # Include environment, two snapshots, and the common-STA reload per point.
    wall_reserve = 2*(60+resources['synthesis_timeout_s']+
                      resources['floorplan_through_global_route_timeout_s']+3*resources['snapshot_timeout_s'])
    if (used['pending'] or any(remaining[s] < requested[s] for s in requested)
        or used['walltime_s']+wall_reserve > resources['max_global_walltime_h']*3600
        or used['CPU_time_s']+wall_reserve*resources['threads_per_tool'] > resources['max_tool_CPU_time_h']*3600):
        raise ValueError('insufficient shared budget for predeclared two-point study')
    return {'status':'admitted', 'usage_before':used, 'remaining_calls':remaining,
            'planned_new_calls':requested, 'support_walltime_reserve_s':wall_reserve,
            'automatic_retries':0, 'caps_increased':False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--study',type=Path,default=ROOT/'experiments/arithmetic_dse/configs/physical_control_v1.json')
    args = parser.parse_args()
    config = json.loads(args.study.read_text())
    out = args.out.resolve()
    if out.exists():
        parser.error('study output must be a new directory')
    ledger = Ledger()
    resources = json.loads(POLICY.read_text())['resources']
    before = admission(ledger.summary(),resources)
    rtl = ROOT/config['rtl']
    if sha256(rtl) != config['rtl_sha256']:
        raise ValueError('predeclared RTL hash mismatch')
    out.mkdir(parents=True)
    write_json(out/'admission.json',before)
    shutil.copy2(args.study,out/'study.json')
    study = {'version':'physical-target-study-v1', 'study_sha256':sha256(args.study),
             'admission':before, 'points':[], 'status':'running', 'commands':[]}
    write_json(out/'study-manifest.json',study)
    for target in config['sdc_periods_ps']:
        directory = out/f'sdc-{target}'
        argv = [sys.executable,'-m','experiments.arithmetic_dse.backend','--rtl',str(rtl),
                '--top',config['top'],'--out',str(directory),'--period-ps',str(target),
                '--abc-target-ps',str(config['abc_target_ps']),
                '--io-delay-max-ps',str(config['io_delay_max_ps']),
                '--stage','grt','--budget-purpose','prototype']
        # Backend's leaf commands charge resources. Charging this nested wrapper
        # would duplicate the same CPU and wall time.
        result = run_command(argv,out,f'sdc-{target}.driver',2800,os.environ.copy())
        result['accounting_scope'] = 'wrapper_excluded_leaf_backend_is_charged'
        study['commands'].append(result)
        manifest = json.loads((directory/'manifest.json').read_text())
        point = {'sdc_period_ps':target,'backend_exit_code':result['exit_code'],
                 'manifest':str(directory/'manifest.json'),
                 'status':manifest['status'],'failure_stage':manifest.get('failure_stage'),
                 'failure_reason':manifest.get('failure_reason')}
        study['points'].append(point)
        if manifest['status'] == 'completed':
            suffix = 'asap7/arithmetic_probe/base'
            results = directory/'results'/suffix
            reports = directory/'reports'/suffix
            # Same RTL and explicit fixed ABC target should produce exactly the
            # same mapped connectivity; fail interpretation, never retry to fit.
            point['synth_netlist_sha256'] = manifest['metrics'][0]['mapped_netlist_sha256']
            sdc_name = 'vulsim_common1500.sdc'
            shutil.copy2(ASSETS/'constraints.sdc',results/sdc_name)
            base = manifest['commands'][0]['command'][:-2]
            common = base+['run',f'RUN_SCRIPT={ASSETS}/snapshot.tcl',
                'RUN_LOG_NAME_STEM=common1500','VULSIM_EVAL_STAGE=grt',
                'VULSIM_REPORT_TAG=common1500','VULSIM_EVAL_DB=5_1_grt.odb',
                f'VULSIM_EVAL_SDC={sdc_name}',
                f'VULSIM_CLOCK_PERIOD_PS={config["common_sdc_period_ps"]}',
                f'VULSIM_IO_DELAY_MAX_PS={config["io_delay_max_ps"]}']
            reservation = ledger.reserve(None,resources['snapshot_timeout_s'],2,
                                         'physical_control_common_STA',common,directory/'common1500')
            record = run_command(common,directory,'common1500',resources['snapshot_timeout_s'],
                                 os.environ.copy(),cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation,record)
            record['budget_reservation_id'] = reservation['id']
            study['commands'].append(record)
            point['common_STA_exit_code'] = record['exit_code']
            if record['exit_code'] == 0:
                _,cells = library_data([Path(lib['path']) for lib in manifest['libraries']])
                metrics = stage_metrics(reports,'grt',cells,config['common_sdc_period_ps'],'common1500')
                metrics.update(abc_target_ps=config['abc_target_ps'],
                               implementation_sdc_period_ps=target,
                               assessment_sdc_period_ps=config['common_sdc_period_ps'])
                write_json(directory/'common1500.metrics.json',metrics)
                point['common_STA_metrics'] = metrics
        write_json(out/'study-manifest.json',study)
    complete = [p for p in study['points'] if p['status'] == 'completed' and p.get('common_STA_exit_code') == 0]
    study['same_synth_netlist'] = len(complete) == 2 and len({p['synth_netlist_sha256'] for p in complete}) == 1
    study['status'] = 'completed' if len(complete) == 2 and study['same_synth_netlist'] else 'incomplete'
    study['usage_after'] = ledger.summary()
    write_json(out/'study-manifest.json',study)
    print(json.dumps(study,indent=2))
    return 0 if study['status'] == 'completed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
