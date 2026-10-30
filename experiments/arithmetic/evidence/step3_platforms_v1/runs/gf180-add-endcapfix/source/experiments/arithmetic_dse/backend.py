"""Run an isolated platform-specific TT ORFS evaluation with stage evidence.

Usage: python3 -m experiments.arithmetic_dse.backend --help
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess

from .processes import run_command
from .budget import Ledger, POLICY
from .characterization import mapped_netlist_hash
from .platforms import profile, library_data, report_scales, resolve_environment, validate_environment

ASSETS = Path(__file__).with_suffix('')
ROOT = Path(__file__).resolve().parents[2]


class BackendCommandError(RuntimeError):
    def __init__(self,stem,code):
        super().__init__(f'{stem}: {code}')
        self.code=code


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def render_abc_script(period_ps):
    if not math.isfinite(period_ps) or period_ps <= 0:
        raise ValueError('invalid ABC target')
    return (ASSETS/'abc_speed_target.script').read_text().replace('@TARGET_PS@',str(float(period_ps)))


def verify_orfs_area(area,native_area):
    # OpenROAD utl::Logger::metric emits doubles using defaultfloat with six
    # significant digits. The independent per-master LEF/Liberty checks above
    # remain much tighter; only this rounded JSON comparison uses its ULP.
    if not math.isfinite(native_area) or native_area<=0:
        raise ValueError('invalid native standard-cell area')
    tolerance=0.500001*10**(math.floor(math.log10(native_area))-5)
    if abs(area-native_area)>tolerance:
        raise ValueError('OpenDB area disagrees with six-significant-digit ORFS metric')
    return {'native_json_significant_digits':6,'rounding_tolerance_um2':tolerance,
            'absolute_difference_um2':abs(area-native_area)}


def stage_metrics(reports, stage, cells, period_ps, report_tag=None, selected=None):
    prefix = reports/f'vulsim_{report_tag or stage}'
    def text(suffix):
        return Path(str(prefix)+suffix).read_text()
    units = text('_units.rpt')
    p = selected or profile('asap7')
    scales = report_scales(units,p)
    time_to_ps = scales['time']['to_ps']
    def number(suffix, pattern):
        match = re.search(pattern, text(suffix))
        if not match:
            raise ValueError(f'missing numeric metric: {prefix}{suffix}')
        value = float(match[1])
        if not float('-inf') < value < float('inf'):
            raise ValueError('non-finite timing metric')
        return value * time_to_ps
    setup = number('_setup.rpt', r'worst slack max\s+([-+\d.eE]+)')
    hold = number('_hold.rpt', r'worst slack min\s+([-+\d.eE]+)')
    setup_tns = number('_setup_tns.rpt', r'tns max\s+([-+\d.eE]+)')
    hold_tns = number('_hold_tns.rpt', r'tns min\s+([-+\d.eE]+)')
    area, functional_area, sequential_area, sequential_count = 0, 0, 0, 0
    physical_only_area, filler_area = 0, 0
    for line in text('_cells.tsv').splitlines():
        master, count, lef_area, filler, cell_type = line.split('\t')
        count, lef_area = int(count), float(lef_area)
        if not cell_type.startswith('CORE') and cell_type not in p['physical_master_types']:
            raise ValueError(f'non-standard-cell master unsupported: {master}: {cell_type}')
        if filler == '1':
            filler_area += count*lef_area
        else:
            area += count*lef_area
        if selected is not None and (filler=='1' or cell_type in p['physical_master_types']
                or any(master.startswith(prefix) for prefix in p['allowed_physical_prefixes'])):
            if filler!='1':physical_only_area += count*lef_area
            continue
        if master not in cells:
            if not (cell_type=='CORE_SPACER' or cell_type in p['physical_master_types'] or any(master.startswith(prefix) for prefix in p['allowed_physical_prefixes'])):
                raise ValueError(f'unrecognized physical master: {master}')
            physical_only_area += count*lef_area
            continue
        liberty = cells[master]
        if not math.isclose(liberty['area_um2'],lef_area,rel_tol=1e-6,abs_tol=1e-6):
            raise ValueError(f'Liberty/LEF area mismatch: {master}')
        functional_area += count*lef_area
        if liberty['sequential']:
            sequential_area += count*lef_area
            sequential_count += count
    coverage = text('_coverage.rpt').strip()
    minimum_period = number('_period.rpt', r'core_clk period_min\s*=\s*([-+\d.eE]+)')
    hold_margin = p['hold_review_margin_ps']
    setup_ok = not coverage and setup >= 0
    sta_ok = setup_ok and hold >= 0
    measured = setup_ok if stage == 'grt' else sta_ok if stage == 'final' else None
    result = {'stage':stage, 'target_period_ps':period_ps, 'cell_area_um2':area,
            'functional_cell_area_um2':functional_area, 'excluded_filler_area_um2':filler_area,
            'area_definition':'OpenDB_stdcell_area_excluding_CORE_SPACER_including_taps',
            'sequential_area_um2':sequential_area, 'sequential_cells':sequential_count,
            'physical_only_area_um2':physical_only_area, 'setup_worst_slack_ps':setup,
            'hold_worst_slack_ps':hold, 'setup_tns_ps':setup_tns, 'hold_tns_ps':hold_tns,
            'timing_coverage_complete':not coverage, 'timing_coverage_diagnostics':coverage,
            'minimum_clock_period_ps':minimum_period, 'sta_feasibility':sta_ok,
            'measured_feasibility':measured,
            'feasibility_scope':{'synth':'synthesis_STA_only', 'grt':'TT_setup_only', 'final':'TT_setup_and_hold'}[stage],
            'multi_corner_signoff':False, 'hold_feasible_at_TT':not coverage and hold >= 0,
            'hold_review_margin_ps':hold_margin, 'hold_review_required':hold < hold_margin,
            'hold_margin_status':'negative' if hold < 0 else 'below_review_band' if hold < hold_margin else 'review_band_met',
            'parasitics':{'synth':'none', 'grt':'global_route_estimate', 'final':'OpenRCX_extracted_SPEF'}[stage],
            'raw_reports_prefix':str(prefix)}

    if selected is not None:
        result.update(target_platform=p['platform'], platform_profile_sha256=p['profile_sha256'],
                      raw_report_units=scales, unit_conversion='Liberty_and_report_units_verified',
                      raw_timing_values={key:result[key]/time_to_ps for key in
                          ['setup_worst_slack_ps','hold_worst_slack_ps','setup_tns_ps','hold_tns_ps','minimum_clock_period_ps']})
    return result


def evaluate(args):
    out = args.out.resolve()
    if out.exists():
        raise ValueError(f'output must be a new directory to preserve prior evidence: {out}')
    out.mkdir(parents=True)
    ledger = Ledger()
    p = profile(args.platform)
    manifest = {'version':'multiplatform-evaluation-v1', 'started_at':datetime.now(timezone.utc).isoformat(),
                'status':'running', 'target_platform':p['platform'], 'platform_profile':p, 'commands':[], 'metrics':[], 'retry_count':0,
                'threads_per_tool':args.threads, 'stages_requested':args.stage,
                'memory_limit_MiB':args.memory_limit_mib,
                'period_ps':args.period_ps, 'period_role':args.period_role,
                'abc_target_ps':args.abc_target_ps,
                'io_delay_max_ps':args.io_delay_max_ps,
                'BC_rules_modified':False, 'policy_version':json.loads(POLICY.read_text())['version'],
                'budget_ledger':str(ledger.path), 'budget_purpose':args.budget_purpose,
                'admission_id':args.admission_id, 'task_id':args.task_id}
    env = os.environ.copy()
    env.update({'OMP_NUM_THREADS':str(args.threads), 'OPENBLAS_NUM_THREADS':str(args.threads),
                'QT_QPA_PLATFORM':'offscreen'})
    try:
        # Capture executable source before any environment/physical command;
        # later edits cannot change the provenance of an in-flight run.
        source_paths=[Path(__file__),Path(__file__).with_name('platforms.py'),
                      Path(__file__).with_name('platform_probe.py'),Path(__file__).with_name('budget.py'),
                      Path(__file__).with_name('processes.py'),Path(__file__).with_name('characterization.py'),
                      Path(__file__).parent/'configs/platforms'/(p['platform']+'.json'),POLICY]
        source_paths += [s for s in ASSETS.iterdir() if s.is_file()]
        manifest['source_sha256']={}
        for source in source_paths:
            relative=source.relative_to(ROOT)
            saved=out/'source'/relative
            saved.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,saved)
            manifest['source_sha256'][str(relative)]=sha256(saved)
        orfs = args.orfs.resolve()
        flow = orfs/'flow'
        rtl = args.rtl.resolve()
        for path in [out, flow, rtl, ASSETS]:
            if re.search(r'\s|[#:$]', str(path)):
                raise ValueError(f'unsupported Make path characters: {path}')
        shutil.copy2(rtl, out/'input.sv')
        # Yosys sources a named custom script verbatim: its -D switch does not
        # reach commands in ORFS abc_speed.script. Render explicit constraints
        # without modifying the external ORFS installation.
        scripts = out/'flow-scripts'
        scripts.mkdir()
        for original in (flow/'scripts').iterdir():
            if original.name != 'abc_speed.script':
                (scripts/original.name).symlink_to(original)
        (scripts/'abc_speed.script').write_text(render_abc_script(args.abc_target_ps))
        config = out/'config.mk'
        settings = {'PLATFORM':p['platform'], **p['make_overrides'],
                    'CORE_MARGIN':p['core_margin_um'],
                    'ABC_DRIVER_CELL':p['driver_cell'],
                    'ABC_LOAD_IN_FF':p.get('abc_load_fF',p['output_load_fF']),
                    'VULSIM_TIME_TO_PS':1 if p['time_unit']=='ps' else 1000,
                    'VULSIM_CAP_TO_FF':1 if p['capacitance_unit']=='fF' else 1000,
                    'VULSIM_DRIVER_CELL':p['driver_cell'], 'VULSIM_DRIVER_PIN':p['driver_pin'],
                    'VULSIM_OUTPUT_LOAD_FF':p['output_load_fF'],
                    'VULSIM_SETUP_UNCERTAINTY_PS':p['setup_uncertainty_ps'],
                    'VULSIM_HOLD_UNCERTAINTY_PS':p['hold_uncertainty_ps'],
                    'VULSIM_CLOCK_TRANSITION_PS':p['clock_transition_ps']}
        config.write_text(f'include {ASSETS}/platform.mk\n'
                          + ''.join(f'export {key} = {value}\n' for key,value in settings.items())
                          + f'export DESIGN_NAME = {args.top}\nexport DESIGN_NICKNAME = arithmetic_probe\n'
                          + f'export VERILOG_FILES = {out}/input.sv\n'
                          + f'export SDC_FILE = {ASSETS}/constraints.sdc\n'
                          + f'export VULSIM_CLOCK_PERIOD_PS = {args.period_ps}\n'
                          + (f'export VULSIM_IO_DELAY_MAX_PS = {args.io_delay_max_ps}\n'
                             if args.io_delay_max_ps is not None else ''))
        command = ['make', '--no-print-directory', '-C', str(flow), '-f', str(flow/'Makefile'),
                   '-f', str(ASSETS/'environment.mk'), f'DESIGN_CONFIG={config}', f'WORK_HOME={out}',
                   f'NUM_CORES={args.threads}',f'ABC_CLOCK_PERIOD_IN_PS={args.abc_target_ps}',
                   f'SCRIPTS_DIR={scripts}']
        # Platform config.mk may use unconditional assignments (ASAP7's
        # nominal-temperature metadata does); command-line overrides must win.
        command += [f'{key}={value}' for key,value in p['make_overrides'].items()]
        command += [f'ABC_DRIVER_CELL={p["driver_cell"]}',
                    f'ABC_LOAD_IN_FF={p.get("abc_load_fF",p["output_load_fF"])}']
        context={'target_platform':p['platform'],'admission_id':args.admission_id,
                 'task_id':args.task_id,'model_version':'not_applicable_platform_connection'}
        if args.admission:
            from .platform_probe import verify_admission
            context['admission_sha256']=verify_admission(args,p,rtl,ledger)
        def run(extra, stem, timeout, stage=None):
            reservation = ledger.reserve(stage, timeout, args.threads, args.budget_purpose, command+extra, out/stem, context=context)
            manifest['active_reservation'] = reservation['id']
            write_json(out/'manifest.json', manifest)
            record = run_command(command+extra, out, stem, timeout, env, args.memory_limit_mib,
                                 cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation, record)
            record['budget_reservation_id'] = reservation['id']
            manifest['commands'].append(record)
            write_json(out/'manifest.json', manifest)
            if record['exit_code'] != 0:
                reason = ('timeout' if record['timed_out'] else 'CPU_limit' if record['CPU_limit_exceeded']
                          else 'memory_limit' if record['memory_limit_exceeded']
                          else 'tool_nonzero_exit')
                raise BackendCommandError(stem,reason)
        run(['vulsim-environment', f'VULSIM_ENV_FILE={out}/effective-environment.txt'], 'environment', 60)
        raw = dict(line.strip().split('=', 1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
        manifest['raw_make_environment'] = raw
        effective, origins = resolve_environment(raw)
        manifest['effective_environment'] = effective
        manifest['asset_resolution'] = origins
        validate_environment(effective,p)
        libraries, cells = library_data([Path(s) for s in effective['LIB_FILES'].split()],p)
        write_json(out/'liberty_cells.json',{'platform':p['platform'],'cells':cells})
        manifest['libraries'] = libraries
        files = {str(rtl), str(out/'input.sv'), str(ROOT/'experiments/arithmetic/step2_freeze_v4.json'),
                 str(POLICY), str(Path(__file__).with_name('processes.py')),
                 str(Path(__file__).with_name('budget.py')), str(scripts/'abc_speed.script')}
        for key in ['TECH_LEF','SC_LEF','ADDER_MAP_FILE','LATCH_MAP_FILE','CLKGATE_MAP_FILE','RCX_RULES','LAYER_PARASITICS_FILE','MAKE_TRACKS','PDN_TCL','FASTROUTE_TCL','TAPCELL_TCL','ADDITIONAL_LEFS']:
            files.update(effective.get(key,'').split())
        for directory in [flow/'scripts', flow/'util', ASSETS]:
            files.update(str(p) for p in directory.rglob('*') if p.is_file() and p.suffix in {'.py','.tcl','.mk','.yaml','.v','.sdc','.sh','.script'})
        files.update(map(str, [flow/'Makefile', flow/'platforms'/p['platform']/'config.mk', config, Path(__file__)]))
        files.add(str(Path(__file__).with_name('platforms.py')))
        files.add(str(Path(__file__).parent/'configs/platforms'/(p['platform']+'.json')))
        manifest['files_sha256'] = {p:sha256(p) for p in sorted(files)}
        manifest['tools'] = {}
        for name, path, flags in [('yosys',effective['YOSYS_EXE'],['-V']),
                                  ('openroad',effective['OPENROAD_EXE'],['-version']),
                                  ('abc',str(Path(effective['YOSYS_EXE']).with_name('yosys-abc')),['-c','version'])]:
            result = subprocess.run([path,*flags], capture_output=True, text=True, check=True)
            manifest['tools'][name] = {'path':path, 'sha256':sha256(path), 'version':result.stdout.strip()}
        manifest['orfs_commit'] = subprocess.check_output(['git','-C',str(orfs),'rev-parse','HEAD'],text=True).strip()
        manifest['orfs_status'] = subprocess.check_output(['git','-C',str(orfs),'status','--short'],text=True)
        manifest['mapping_context'] = {
            'abc_target_ps':float(effective['ABC_CLOCK_PERIOD_IN_PS']), 'sdc_period_ps':args.period_ps,
            'abc_mode':'speed', 'abc_script_sha256':sha256(scripts/'abc_speed.script'),
            'abc_script_template_sha256':sha256(ASSETS/'abc_speed_target.script'),
            'abc_target_binding':'explicit_D_on_nf_upsize_dnsize_in_rendered_script',
            'sdc_rule_sha256':sha256(ASSETS/'constraints.sdc'),
            'io_delay_policy':'fixed_absolute' if args.io_delay_max_ps is not None else 'fraction_of_period',
            'io_delay_max_ps':args.io_delay_max_ps if args.io_delay_max_ps is not None else 0.2*args.period_ps,
            'libraries_sha256':{Path(lib['path']).name:lib['sha256'] for lib in libraries},
            'tool_binaries_sha256':{name:tool['sha256'] for name,tool in manifest['tools'].items()},
            'platform':p['platform'],'platform_profile_sha256':p['profile_sha256'],
            'abc_driver_cell':effective['ABC_DRIVER_CELL'],
            'abc_load_fF':float(effective['ABC_LOAD_IN_FF']),
            'corner':effective['CORNER'], 'VT':p['VT'],
            'liberty_model':p['liberty_model'], 'evaluation_stage':args.stage,
            'flow_and_platform_sha256':{
                ('orfs/'+str(Path(path).relative_to(orfs)) if Path(path).is_relative_to(orfs)
                 else 'vulsim/'+str(Path(path).relative_to(ROOT))):digest
                for path,digest in manifest['files_sha256'].items()
                if Path(path).is_relative_to(orfs) or Path(path).is_relative_to(ASSETS)},
            'target_dependent_measurement':True, 'intrinsic_operator_delay':False}
        manifest['mapping_context_sha256'] = hashlib.sha256(json.dumps(
            manifest['mapping_context'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        suffix = Path(p['platform'])/'arithmetic_probe/base'
        results, reports, logs = (out/folder/suffix for folder in ['results','reports','logs'])
        stages = [('synth','synth','1_synth.odb','1_synth.sdc',args.synth_timeout_s),
                  ('grt','grt','5_1_grt.odb','5_1_grt.sdc',args.route_timeout_s),
                  ('final',str(logs/'6_report.log'),'6_final.odb','6_final.sdc',args.route_timeout_s)]
        for stage, target, db, sdc, timeout in stages:
            manifest['active_stage'] = stage
            run([target], stage, timeout, stage)
            if not (results/db).exists():
                raise ValueError(f'missing {stage} database: {results/db}')
            if stage == 'final' and not (results/'6_final.spef').exists():
                raise ValueError('missing extracted SPEF; detailed-route metrics unavailable')
            run(['run', f'RUN_SCRIPT={ASSETS}/snapshot.tcl', f'RUN_LOG_NAME_STEM=vulsim_{stage}',
                 f'VULSIM_EVAL_STAGE={stage}', f'VULSIM_EVAL_DB={db}', f'VULSIM_EVAL_SDC={sdc}'],
                f'{stage}-snapshot', 120)
            metrics = stage_metrics(reports, stage, cells, args.period_ps, selected=p)
            metrics.update(abc_target_ps=manifest['mapping_context']['abc_target_ps'],
                           mapping_context_sha256=manifest['mapping_context_sha256'],
                           target_dependent_measurement=True)
            if stage == 'synth':
                netlist = results/'1_2_yosys.v'
                metrics['mapped_netlist_sha256'] = mapped_netlist_hash(netlist.read_text())
                metrics['mapped_netlist_hash_rule'] = 'Yosys_Verilog_remove_banner_src_blank_lines_v1'
                identity = dict(manifest['mapping_context'], evaluation_stage='synth',
                                input_rtl_sha256=sha256(rtl), top=args.top)
                for key in ['abc_target_ps','sdc_period_ps','abc_script_sha256']:
                    del identity[key]
                metrics['comparison_identity_sha256'] = hashlib.sha256(json.dumps(
                    identity, sort_keys=True, separators=(',',':')).encode()).hexdigest()
            native_json = json.loads((logs/{'synth':'1_synth.json','grt':'5_1_grt.json','final':'6_report.json'}[stage]).read_text())
            key = {'synth':'synth','grt':'globalroute','final':'finish'}[stage]+'__design__instance__area__stdcell'
            metrics['orfs_area_crosscheck']=verify_orfs_area(metrics['cell_area_um2'],native_json[key])
            metrics['orfs_stdcell_area_um2'] = native_json[key]
            if stage == 'final':
                drc = json.loads((logs/'5_2_route.json').read_text())['detailedroute__route__drc_errors']
                metrics['detailed_route_drc_errors'] = drc
                metrics['measured_feasibility'] = metrics['measured_feasibility'] and drc == 0
            manifest['metrics'].append(metrics)
            write_json(out/'metrics.json', manifest['metrics'])
            if not metrics['timing_coverage_complete']:
                raise ValueError('timing_coverage_incomplete')
            if args.stage == stage:
                break
        manifest['status'] = 'completed'
    except Exception as error:
        manifest['status'] = 'failed'
        manifest['failure_stage'] = manifest.get('active_stage', 'preflight')
        manifest['failure_reason'] = str(error)
        manifest['failure_code'] = (error.code if isinstance(error,BackendCommandError)
            else 'timing_coverage_incomplete' if str(error)=='timing_coverage_incomplete'
            else 'invalid_platform_environment' if manifest['failure_stage']=='preflight'
            else 'stage_evidence_rejected')
    finally:
        manifest['finished_at'] = datetime.now(timezone.utc).isoformat()
        manifest['evidence_sha256'] = {str(p.relative_to(out)):sha256(p)
            for folder in ['logs','reports','results'] for p in (out/folder).rglob('*') if p.is_file()}
        write_json(out/'manifest.json', manifest)
    print(json.dumps({'status':manifest['status'], 'output':str(out),
                      'failure_reason':manifest.get('failure_reason'), 'metrics':manifest['metrics']}, indent=2))
    return 0 if manifest['status'] == 'completed' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform',choices=['asap7','nangate45','sky130hd','gf180'],default='asap7')
    parser.add_argument('--admission',type=Path,help='frozen bounded platform/stage task list')
    parser.add_argument('--admission-id',default='explicit-backend-request')
    parser.add_argument('--task-id',default='explicit-single-kernel')
    parser.add_argument('--rtl', type=Path, required=True, help='native generated single-module SystemVerilog')
    parser.add_argument('--top', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--orfs', type=Path, default=Path('/home/zyrv/OpenROAD-flow-scripts'))
    parser.add_argument('--period-ps', type=float, required=True)
    parser.add_argument('--abc-target-ps', type=float, help='defaults to SDC period; can be held fixed for physical target comparisons')
    parser.add_argument('--io-delay-max-ps', type=float, help='fixed absolute I/O max delay; default is 20%% of SDC period')
    parser.add_argument('--period-role', choices=['resource_trial','frozen_case_target'], default='resource_trial')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--memory-limit-mib', type=int, default=8192, help='sampled aggregate process-group RSS cap')
    parser.add_argument('--stage', choices=['synth','grt','final'], default='final')
    parser.add_argument('--budget-purpose', choices=['prototype','characterization','search','final_evaluation','physical_recheck','repeat','retry'], default='prototype')
    parser.add_argument('--synth-timeout-s', type=float, default=300)
    parser.add_argument('--route-timeout-s', type=float, default=1200)
    args = parser.parse_args()
    if args.abc_target_ps is None:
        args.abc_target_ps = args.period_ps
    limits = json.loads(POLICY.read_text())['resources']
    if (any(not math.isfinite(v) or v <= 0 for v in [args.period_ps,args.abc_target_ps,args.synth_timeout_s,args.route_timeout_s])
        or args.threads < 1 or args.memory_limit_mib < 1):
        parser.error('period, threads and timeouts must be positive')
    if args.io_delay_max_ps is not None and (not math.isfinite(args.io_delay_max_ps) or args.io_delay_max_ps < 0):
        parser.error('absolute I/O delay must be finite and nonnegative')
    if (args.threads > limits['threads_per_tool'] or args.memory_limit_mib > limits['memory_limit_MiB']
        or args.synth_timeout_s > limits['synthesis_timeout_s']
        or args.route_timeout_s > min(limits['floorplan_through_global_route_timeout_s'], limits['detailed_route_extraction_timeout_s'])):
        parser.error('requested resources exceed frozen per-job policy')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', args.top):
        parser.error('top must be a simple Verilog identifier')
    return evaluate(args)


if __name__ == '__main__':
    raise SystemExit(main())
