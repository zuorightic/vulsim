"""Run an isolated ASAP7 TT ORFS evaluation and retain stage-specific evidence.

Usage: python3 -m experiments.arithmetic_dse.backend --help
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import time

ASSETS = Path(__file__).with_suffix('')
ROOT = Path(__file__).resolve().parents[2]


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def library_data(paths):
    """Read only the platform-selected libraries, not a wildcard of corners."""
    libraries, cells = [], {}
    for path in paths:
        text = gzip.open(path, 'rt').read() if path.suffix == '.gz' else path.read_text()
        def attribute(name):
            match = re.search(r'\b'+name+r'\s*:\s*([^;]+);', text)
            if not match:
                raise ValueError(f'missing {name}: {path}')
            return match[1].strip().strip('"')
        pvt = {'voltage_V':float(attribute('nom_voltage')),
               'temperature_C':float(attribute('nom_temperature')), 'time_unit':attribute('time_unit')}
        if ('_RVT_TT_' not in path.name or 'FAKE' in path.name or pvt !=
            {'voltage_V':0.7, 'temperature_C':25.0, 'time_unit':'1ps'}):
            raise ValueError(f'unexpected TT/RVT library: {path}: {pvt}')
        if not re.search(r'capacitive_load_unit\s*\(\s*1\s*,\s*ff\s*\)', text):
            raise ValueError(f'expected fF capacitance unit: {path}')
        libraries.append({'path':str(path), 'sha256':sha256(path), **pvt, 'capacitance_unit':'fF'})
        matches = list(re.finditer(r'\bcell\s*\(\s*([^\s)]+)\s*\)\s*\{', text))
        for i, match in enumerate(matches):
            body = text[match.end():matches[i+1].start() if i+1 < len(matches) else len(text)]
            area = re.search(r'\barea\s*:\s*([\d.eE+-]+)', body)
            if not area:
                raise ValueError(f'cell without area: {match[1]}')
            cells[match[1]] = {'area_um2':float(area[1]),
                              'sequential':bool(re.search(r'\b(?:ff|ff_bank|latch|latch_bank)\s*\(', body))}
    return libraries, cells


def run_command(command, directory, stem, timeout_s, env, memory_limit_mib=8192):
    """Kill the entire process group on timeout; sample aggregate process RSS."""
    log = directory/f'{stem}.log'
    resource_log = directory/f'{stem}.resources.txt'
    wrapped = ['/usr/bin/time', '-v', '-o', str(resource_log), *map(str, command)]
    start = time.monotonic()
    peak_rss_kib, peak_threads = 0, 0
    timed_out, memory_limit_exceeded = False, False
    with log.open('w') as output:
        process = subprocess.Popen(wrapped, stdout=output, stderr=subprocess.STDOUT,
                                   env=env, start_new_session=True)
        while process.poll() is None:
            rss, threads = 0, 0
            for stat in Path('/proc').glob('[0-9]*/stat'):
                try:
                    fields = stat.read_text().rsplit(')', 1)[1].split()
                    if int(fields[2]) == process.pid:
                        rss += int(fields[21])*os.sysconf('SC_PAGE_SIZE')//1024
                        threads += int(fields[17])
                except (OSError, ValueError, IndexError):
                    continue
            peak_rss_kib = max(peak_rss_kib, rss)
            peak_threads = max(peak_threads, threads)
            remaining = timeout_s-(time.monotonic()-start)
            if remaining <= 0 or rss > memory_limit_mib*1024:
                timed_out = remaining <= 0
                memory_limit_exceeded = rss > memory_limit_mib*1024
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
                break
            try:
                process.wait(timeout=min(0.5, remaining))
            except subprocess.TimeoutExpired:
                pass
    record = {'command':list(map(str, command)), 'exit_code':process.returncode,
              'timed_out':timed_out, 'walltime_s':time.monotonic()-start,
              'memory_limit_exceeded':memory_limit_exceeded, 'memory_limit_MiB':memory_limit_mib,
              'sampled_process_group_peak_rss_KiB':peak_rss_kib,
              'sampled_process_group_peak_threads':peak_threads,
              'resource_sampling_interval_s':0.5, 'log':str(log), 'gnu_time':str(resource_log)}
    write_json(directory/f'{stem}.command.json', record)
    return record


def stage_metrics(reports, stage, cells, period_ps):
    prefix = reports/f'vulsim_{stage}'
    def text(suffix):
        return Path(str(prefix)+suffix).read_text()
    units = text('_units.rpt')
    # Match the OpenSTA human-readable unit report explicitly; reject unknown units.
    if not re.search(r'^\s*time\s+(?:1ps|1e-12\s*s)\s*$', units, re.I | re.M):
        raise ValueError(f'expected ps in report_units: {units}')
    if not re.search(r'^\s*capacitance\s+(?:1fF|1e-15\s*F)\s*$', units, re.I | re.M):
        raise ValueError(f'expected fF in report_units: {units}')
    def number(suffix, pattern):
        match = re.search(pattern, text(suffix))
        if not match:
            raise ValueError(f'missing numeric metric: {prefix}{suffix}')
        value = float(match[1])
        if not float('-inf') < value < float('inf'):
            raise ValueError('non-finite timing metric')
        return value
    setup = number('_setup.rpt', r'worst slack max\s+([-+\d.eE]+)')
    hold = number('_hold.rpt', r'worst slack min\s+([-+\d.eE]+)')
    setup_tns = number('_setup_tns.rpt', r'tns max\s+([-+\d.eE]+)')
    hold_tns = number('_hold_tns.rpt', r'tns min\s+([-+\d.eE]+)')
    area, functional_area, sequential_area, sequential_count = 0, 0, 0, 0
    physical_only_area, filler_area = 0, 0
    for line in text('_cells.tsv').splitlines():
        master, count, lef_area, filler, cell_type = line.split('\t')
        count, lef_area = int(count), float(lef_area)
        if not cell_type.startswith('CORE'):
            raise ValueError(f'non-standard-cell master unsupported: {master}: {cell_type}')
        if filler == '1':
            filler_area += count*lef_area
        else:
            area += count*lef_area
        if master not in cells:
            if not re.match(r'(?:FILLER|TAPCELL|DECAP)', master):
                raise ValueError(f'unrecognized physical master: {master}')
            physical_only_area += count*lef_area
            continue
        liberty = cells[master]
        if abs(liberty['area_um2']-lef_area) > 1e-6:
            raise ValueError(f'Liberty/LEF area mismatch: {master}')
        functional_area += count*lef_area
        if liberty['sequential']:
            sequential_area += count*lef_area
            sequential_count += count
    coverage = text('_coverage.rpt').strip()
    minimum_period = number('_period.rpt', r'core_clk period_min\s*=\s*([-+\d.eE]+)')
    sta_ok = not coverage and setup >= 0 and hold >= 0
    return {'stage':stage, 'target_period_ps':period_ps, 'cell_area_um2':area,
            'functional_cell_area_um2':functional_area, 'excluded_filler_area_um2':filler_area,
            'area_definition':'OpenDB_stdcell_area_excluding_CORE_SPACER_including_taps',
            'sequential_area_um2':sequential_area, 'sequential_cells':sequential_count,
            'physical_only_area_um2':physical_only_area, 'setup_worst_slack_ps':setup,
            'hold_worst_slack_ps':hold, 'setup_tns_ps':setup_tns, 'hold_tns_ps':hold_tns,
            'timing_coverage_complete':not coverage, 'timing_coverage_diagnostics':coverage,
            'minimum_clock_period_ps':minimum_period, 'sta_feasibility':sta_ok,
            'measured_feasibility':sta_ok if stage != 'synth' else None,
            'parasitics':{'synth':'none', 'grt':'global_route_estimate', 'final':'OpenRCX_extracted_SPEF'}[stage],
            'raw_reports_prefix':str(prefix)}


def evaluate(args):
    out = args.out.resolve()
    if out.exists():
        raise ValueError(f'output must be a new directory to preserve prior evidence: {out}')
    out.mkdir(parents=True)
    manifest = {'version':'asap7-evaluation-v1', 'started_at':datetime.now(timezone.utc).isoformat(),
                'status':'running', 'commands':[], 'metrics':[], 'retry_count':0,
                'threads_per_tool':args.threads, 'stages_requested':args.stage,
                'memory_limit_MiB':args.memory_limit_mib,
                'period_ps':args.period_ps, 'period_role':args.period_role,
                'BC_rules_modified':False}
    env = os.environ.copy()
    env.update({'OMP_NUM_THREADS':str(args.threads), 'OPENBLAS_NUM_THREADS':str(args.threads),
                'QT_QPA_PLATFORM':'offscreen'})
    try:
        orfs = args.orfs.resolve()
        flow = orfs/'flow'
        rtl = args.rtl.resolve()
        for path in [out, flow, rtl, ASSETS]:
            if re.search(r'\s|[#:$]', str(path)):
                raise ValueError(f'unsupported Make path characters: {path}')
        shutil.copy2(rtl, out/'input.sv')
        config = out/'config.mk'
        config.write_text(f'include {ASSETS}/asap7.mk\n'
                          f'export DESIGN_NAME = {args.top}\nexport DESIGN_NICKNAME = arithmetic_probe\n'
                          f'export VERILOG_FILES = {out}/input.sv\n'
                          f'export SDC_FILE = {ASSETS}/constraints.sdc\n'
                          f'export VULSIM_CLOCK_PERIOD_PS = {args.period_ps}\n')
        command = ['make', '--no-print-directory', '-C', str(flow), '-f', str(flow/'Makefile'),
                   '-f', str(ASSETS/'environment.mk'), f'DESIGN_CONFIG={config}', f'WORK_HOME={out}',
                   f'NUM_CORES={args.threads}', 'TC_TEMPERATURE=25C', f'ABC_CLOCK_PERIOD_IN_PS={args.period_ps}']
        def run(extra, stem, timeout):
            record = run_command(command+extra, out, stem, timeout, env, args.memory_limit_mib)
            manifest['commands'].append(record)
            write_json(out/'manifest.json', manifest)
            if record['exit_code'] != 0:
                reason = ('timeout' if record['timed_out'] else 'memory_limit' if record['memory_limit_exceeded']
                          else f'exit {record["exit_code"]}')
                raise RuntimeError(f'{stem}: {reason}')
        run(['vulsim-environment', f'VULSIM_ENV_FILE={out}/effective-environment.txt'], 'environment', 60)
        effective = dict(line.strip().split('=', 1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
        manifest['effective_environment'] = effective
        libraries, cells = library_data([Path(p) for p in effective['LIB_FILES'].split()])
        if len(libraries) != 5 or effective['TEMPERATURE'] != '25C':
            raise ValueError('expected five TT/RVT libraries and temperature metadata aligned to 25C')
        manifest['libraries'] = libraries
        files = {str(rtl), str(out/'input.sv'), str(ROOT/'experiments/arithmetic/freeze_v3.json')}
        for key in ['TECH_LEF','SC_LEF','ADDER_MAP_FILE','LATCH_MAP_FILE','CLKGATE_MAP_FILE','RCX_RULES','SET_RC_TCL','MAKE_TRACKS','PDN_TCL','FASTROUTE_TCL']:
            files.update(effective[key].split())
        for directory in [flow/'scripts', flow/'util', ASSETS]:
            files.update(str(p) for p in directory.rglob('*') if p.is_file() and p.suffix in {'.py','.tcl','.mk','.yaml','.v','.sdc','.sh'})
        files.update(map(str, [flow/'Makefile', flow/'platforms/asap7/config.mk', config, Path(__file__)]))
        manifest['files_sha256'] = {p:sha256(p) for p in sorted(files)}
        manifest['tools'] = {}
        for name, path, flags in [('yosys',effective['YOSYS_EXE'],['-V']),
                                  ('openroad',effective['OPENROAD_EXE'],['-version']),
                                  ('abc',str(Path(effective['YOSYS_EXE']).with_name('yosys-abc')),['-c','version'])]:
            result = subprocess.run([path,*flags], capture_output=True, text=True, check=True)
            manifest['tools'][name] = {'path':path, 'sha256':sha256(path), 'version':result.stdout.strip()}
        manifest['orfs_commit'] = subprocess.check_output(['git','-C',str(orfs),'rev-parse','HEAD'],text=True).strip()
        manifest['orfs_status'] = subprocess.check_output(['git','-C',str(orfs),'status','--short'],text=True)
        suffix = Path('asap7/arithmetic_probe/base')
        results, reports, logs = (out/folder/suffix for folder in ['results','reports','logs'])
        stages = [('synth','synth','1_synth.odb','1_synth.sdc',args.synth_timeout_s),
                  ('grt','grt','5_1_grt.odb','5_1_grt.sdc',args.route_timeout_s),
                  ('final',str(logs/'6_report.log'),'6_final.odb','6_final.sdc',args.route_timeout_s)]
        for stage, target, db, sdc, timeout in stages:
            manifest['active_stage'] = stage
            run([target], stage, timeout)
            if not (results/db).exists():
                raise ValueError(f'missing {stage} database: {results/db}')
            if stage == 'final' and not (results/'6_final.spef').exists():
                raise ValueError('missing extracted SPEF; detailed-route metrics unavailable')
            run(['run', f'RUN_SCRIPT={ASSETS}/snapshot.tcl', f'RUN_LOG_NAME_STEM=vulsim_{stage}',
                 f'VULSIM_EVAL_STAGE={stage}', f'VULSIM_EVAL_DB={db}', f'VULSIM_EVAL_SDC={sdc}'],
                f'{stage}-snapshot', 120)
            metrics = stage_metrics(reports, stage, cells, args.period_ps)
            native_json = json.loads((logs/{'synth':'1_synth.json','grt':'5_1_grt.json','final':'6_report.json'}[stage]).read_text())
            key = {'synth':'synth','grt':'globalroute','final':'finish'}[stage]+'__design__instance__area__stdcell'
            if abs(metrics['cell_area_um2']-native_json[key]) > 0.001:
                raise ValueError(f'OpenDB area disagrees with ORFS metric: {key}')
            metrics['orfs_stdcell_area_um2'] = native_json[key]
            if stage == 'final':
                drc = json.loads((logs/'5_2_route.json').read_text())['detailedroute__route__drc_errors']
                metrics['detailed_route_drc_errors'] = drc
                metrics['measured_feasibility'] = metrics['measured_feasibility'] and drc == 0
            manifest['metrics'].append(metrics)
            write_json(out/'metrics.json', manifest['metrics'])
            if args.stage == stage:
                break
        manifest['status'] = 'completed'
    except Exception as error:
        manifest['status'] = 'failed'
        manifest['failure_stage'] = manifest.get('active_stage', 'preflight')
        manifest['failure_reason'] = str(error)
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
    parser.add_argument('--rtl', type=Path, required=True, help='native generated single-module SystemVerilog')
    parser.add_argument('--top', required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--orfs', type=Path, default=Path('/home/zyrv/OpenROAD-flow-scripts'))
    parser.add_argument('--period-ps', type=float, required=True)
    parser.add_argument('--period-role', choices=['resource_trial','frozen_case_target'], default='resource_trial')
    parser.add_argument('--threads', type=int, default=2)
    parser.add_argument('--memory-limit-mib', type=int, default=8192, help='sampled aggregate process-group RSS cap')
    parser.add_argument('--stage', choices=['synth','grt','final'], default='final')
    parser.add_argument('--synth-timeout-s', type=float, default=300)
    parser.add_argument('--route-timeout-s', type=float, default=1200)
    args = parser.parse_args()
    if args.period_ps <= 0 or args.threads < 1 or args.memory_limit_mib < 1 or min(args.synth_timeout_s,args.route_timeout_s) <= 0:
        parser.error('period, threads and timeouts must be positive')
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', args.top):
        parser.error('top must be a simple Verilog identifier')
    return evaluate(args)


if __name__ == '__main__':
    raise SystemExit(main())
