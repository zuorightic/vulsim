"""Finite frozen nine-workload final comparison, with common backend accounting.

This runner admits selected implementations only. It cannot price candidates
or return physical observations to the selector. Identical RTL/target records
share one measurement with explicit attribution. Failed leaves are retained.
"""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from .workload_abcd import ROOT, read, write, sha
from .budget import Ledger, POLICY
from .platforms import profile

PURPOSE = 'arithmetic_workload_final_comparison'
VERSION = 'nine-workload-frozen-backend-v1'


def measurement_sources():
    directory = ROOT / 'experiments/arithmetic_dse'
    names = ['workload_backend.py', 'workload_abcd.py', 'backend.py', 'platform_probe.py', 'budget.py',
             'processes.py', 'platforms.py', 'sdc.py', 'model_fast_sdc.py',
             'sdc_storage_v3.py', 'sdc_storage_v4.py', 'sdc_storage_v5.py', 'characterization.py']
    return ([directory / n for n in names] + [p for p in (directory / 'backend').iterdir() if p.is_file()]
            + [directory / 'reference_assets/workload_minimum_period_v1.tcl'])


def verify_freeze(path):
    frozen = read(path)
    if frozen.get('version') != 'nine-workload-selection-freeze-v1' or frozen.get('application_PPA_seen') is not False:
        raise ValueError('comparison requires an immutable pre-PPA selection freeze')
    for name, digest in frozen['files'].items():
        if sha(name) != digest:
            raise ValueError('frozen implementation/selection changed: ' + name)
    if frozen.get('methods_complete') is not True:
        raise ValueError('all nine ABCD selections must freeze before application PPA')
    return frozen


def admit(root):
    root = Path(root).resolve()
    if (root / 'admission.json').exists():
        raise ValueError('preserve existing physical admission')
    freeze = root / 'selection-freeze.json'; verify_freeze(freeze)
    methods = read(root / 'methods.json')
    from .workload_contracts import load
    expected = Counter((c['id'],t['T_ps'],t['L']) for c in load()['cases'] for t in c['formal_targets'])
    actual = Counter((r['case'],r['target']['T_ps'],r['target']['L']) for r in methods['records'])
    if actual != expected:
        raise ValueError('exactly nineteen confirmed target records across nine cases required')
    p = profile('asap7'); tasks = []; identities = {}
    for row in methods['records']:
        if not {'A', 'B', 'C', 'D'} <= row['methods'].keys():
            raise ValueError('ABCD implementation missing')
        for method, data in row['methods'].items():
            if method not in ('A', 'B', 'C', 'D', 'D_static_cal'):
                raise ValueError('undeclared comparison method')
            if data['L'] != (1 if method == 'A' else row['target']['L']):
                raise ValueError('A latency or matched B/C/D latency contract changed')
            rtl = Path(data['rtl']).resolve()
            if sha(rtl) != data['rtl_sha256'] or data['simulation_status'] != 'passed':
                raise ValueError('method RTL or functional verification mismatch')
            identity = (data['rtl_sha256'], row['target']['T_ps'], 'Workload', p['profile_sha256'])
            attribution = dict(case=row['case'], target=row['target'], method=method, L=data['L'])
            if identity in identities:
                identities[identity]['attribution'].append(attribution)
                continue
            task = dict(id=f"{row['case']}-T{row['target']['T_ps']}-{method}",
                        platform='asap7', profile_sha256=p['profile_sha256'],
                        rtl=str(rtl), rtl_sha256=data['rtl_sha256'], top='Workload',
                        period_ps=row['target']['T_ps'], abc_target_ps=row['target']['T_ps'],
                        stage='grt', purpose='final_evaluation', attribution=[attribution])
            tasks.append(task); identities[identity] = task
    ablations = [r for r in methods['records'] if 'D_static_cal' in r['methods']]
    if (len(ablations) != 2 or sum(r['case'] == 'mac32' for r in ablations) != 1):
        raise ValueError('exactly one MAC32 and one wide/multinode same-policy cost attribution required')
    if str((root/'methods.json').resolve()) not in read(freeze)['files']:
        raise ValueError('method matrix is absent from the selection freeze')
    if not 1 <= len(tasks) <= 78:
        raise ValueError('finite nineteen-target ABCD plus two attribution tasks exceeded')
    limits = read(POLICY)['resources']; used = Ledger().summary()
    # Per task: environment, synth and grt snapshots, fixed-DB timing readout.
    worst_wall = len(tasks) * (300 + 1200 + 60 + 2*120 + 120)
    if used['pending'] or used['synth']+len(tasks)>limits['max_synthesis_calls'] or used['grt']+len(tasks)>limits['max_global_route_calls']:
        raise ValueError('unsettled ledger or finite physical budget exhausted')
    if used['walltime_s']+worst_wall>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+4*worst_wall>limits['max_tool_CPU_time_h']*3600:
        raise ValueError('finite comparison time envelope unfunded')
    storage = max(10*1024**3, len(tasks)*512*1024**2)
    if shutil.disk_usage(root).free < storage:
        raise ValueError('insufficient free storage for retained backend evidence')
    hashes = {}
    for path in measurement_sources():
        relative = path.relative_to(ROOT); dest = root / 'measurement-source' / relative
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dest)
        hashes[str(relative)] = sha(path)
    pilots = []
    for case in ('mac32','mul128','montgomery256','ntt8x64'):
        match = next(t for t in tasks if any(r['case'] == case and r['method'] == 'D' for r in t['attribution']))
        if match['id'] not in pilots: pilots.append(match['id'])
    value = dict(version=VERSION, id=root.name+'-physical', purpose=PURPOSE,
                 created_at=datetime.now(timezone.utc).isoformat(), tasks=tasks,
                 policy_sha256=sha(POLICY), selection_freeze=str(freeze), selection_freeze_sha256=sha(freeze),
                 methods_sha256=sha(root / 'methods.json'), sources=hashes, starting_usage=used,
                 call_caps=dict(synth=len(tasks), grt=len(tasks), final=0, support=4*len(tasks)),
                 worst_case_leaf_walltime_s=worst_wall, CPU_envelope_s=4*worst_wall,
                 storage_reserve_bytes=storage, parallel_jobs=4, threads=4, memory_limit_MiB=8192,
                 synth_timeout_s=300, grt_timeout_s=1200, support_timeout_s=120,
                 capacity_pilot_task_ids=pilots,
                 capacity_pilot_rule='named selected MAC32/Mul128/Montgomery256/NTT implementations before remaining matrix; no physical feedback to selection',
                 automatic_retries=0, application_data_role='final_evaluation_never_training',
                 selection_feedback=False, qualification=methods['qualification'])
    write(root / 'admission.json', value)
    write(root / 'backend-progress.json', dict(status='admitted', completed=[], errors=[], active=[]))
    return value


def verify_admission(args, p, rtl, ledger):
    path = args.admission.resolve(); a = read(path); root = path.parent
    if a['version'] != VERSION or a['purpose'] != PURPOSE or a['id'] != args.admission_id or a['policy_sha256'] != sha(POLICY):
        raise ValueError('workload admission identity/policy mismatch')
    if sha(a['selection_freeze']) != a['selection_freeze_sha256'] or sha(root / 'methods.json') != a['methods_sha256']:
        raise ValueError('comparison selection freeze changed')
    verify_freeze(a['selection_freeze'])
    for name, digest in a['sources'].items():
        if sha(ROOT / name) != digest or sha(root / 'measurement-source' / name) != digest:
            raise ValueError('frozen measurement code changed: ' + name)
    matches = [t for t in a['tasks'] if t['id'] == args.task_id]
    if len(matches) != 1:
        raise ValueError('physical task absent from finite frozen matrix')
    t = matches[0]
    if (str(rtl) != t['rtl'] or sha(rtl) != t['rtl_sha256'] or args.top != t['top']
            or args.platform != t['platform'] or p['profile_sha256'] != t['profile_sha256']
            or args.period_ps != t['period_ps'] or args.abc_target_ps != t['abc_target_ps']
            or args.stage != 'grt' or args.period_role != 'frozen_case_target'
            or args.budget_purpose != 'final_evaluation' or args.io_delay_max_ps is not None
            or args.threads != 4 or args.memory_limit_mib != 8192
            or args.synth_timeout_s != 300 or args.route_timeout_s != 1200
            or args.resume_synth_from or args.sample_contract
            or not args.selection_freeze or args.selection_freeze.resolve() != Path(a['selection_freeze'])):
        raise ValueError('physical invocation differs from frozen workload matrix')
    entries = [e for e in read(ledger.path)['entries'] if e.get('admission_id') == a['id']]
    if any(e.get('task_id') == t['id'] for e in entries):
        raise ValueError('task already attempted; automatic physical retries forbidden')
    for stage in ('synth', 'grt'):
        if sum(e['stage'] == stage for e in entries) >= a['call_caps'][stage]:
            raise ValueError('finite workload physical call cap exhausted')
    return sha(path)


class ComparisonLedger(Ledger):
    """Enforce the admission's per-task leaves as well as the global limits."""
    def __init__(self, root, task):
        super().__init__(); self.root, self.task = root, task

    def reserve(self, stage, timeout_s, threads, purpose, command, output, *, context=None):
        a = read(self.root / 'admission.json')
        if self.task not in a['tasks'] or threads != 4 or stage not in (None, 'synth', 'grt'):
            raise ValueError('unregistered comparison leaf')
        if sha(a['selection_freeze']) != a['selection_freeze_sha256']:
            raise ValueError('changed selection freeze during measurement')
        verify_freeze(a['selection_freeze'])
        if sha(self.task['rtl']) != self.task['rtl_sha256']:
            raise ValueError('changed selected RTL during measurement')
        for name, digest in a['sources'].items():
            if sha(ROOT / name) != digest or sha(self.root / 'measurement-source' / name) != digest:
                raise ValueError('changed measurement implementation: ' + name)
        entries = [e for e in read(self.path)['entries'] if e.get('admission_id') == a['id']]
        mine = [e for e in entries if e.get('task_id') == self.task['id']]
        if stage is not None:
            if (timeout_s > a[stage+'_timeout_s'] or any(e['stage'] == stage for e in mine)
                    or sum(e['stage'] == stage for e in entries) >= a['call_caps'][stage]):
                raise ValueError('finite stage limit exhausted; no automatic retry')
        elif timeout_s > 120 or sum(e['stage'] is None for e in mine) >= 4:
            raise ValueError('finite per-implementation support limit exhausted')
        return super().reserve(stage, timeout_s, threads, purpose, command, output,
                   context={**(context or {}), 'target_platform':'asap7', 'admission_id':a['id'],
                            'task_id':self.task['id'], 'admission_sha256':sha(self.root/'admission.json'),
                            'selection_freeze_sha256':a['selection_freeze_sha256']})


def run_task(root, task):
    from .backend import _evaluate
    a = read(root / 'admission.json')
    args = SimpleNamespace(out=root/'runs'/task['id'], platform='asap7', threads=4,
            stage='grt', memory_limit_mib=8192, period_ps=task['period_ps'], period_role='frozen_case_target',
            abc_target_ps=task['abc_target_ps'], io_delay_max_ps=None, budget_purpose='final_evaluation',
            admission_id=a['id'], task_id=task['id'], sample_contract=None,
            admission=root/'admission.json', resume_synth_from=None, orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),
            rtl=Path(task['rtl']), top='Workload', synth_timeout_s=300, route_timeout_s=1200,
            selection_freeze=Path(a['selection_freeze']))
    ledger = ComparisonLedger(root, task)
    with ledger.job(dict(target_platform='asap7', admission_id=a['id'], task_id=task['id'])):
        if _evaluate(args, ledger):
            m = read(args.out / 'manifest.json')
            raise ValueError(m.get('failure_reason', 'backend failed'))
    minimum_period(root, task)
    return task['id']


def minimum_period(root, task):
    """Read a fixed physical implementation, without resizing or reselection."""
    from .processes import run_command
    directory = root/'runs'/task['id']; m = read(directory/'manifest.json')
    suffix = Path('asap7/arithmetic_probe/base'); result_dir = directory/'results'/suffix
    sdc = (result_dir/'5_1_grt.sdc').read_text()
    if any(token in sdc for token in ('set_multicycle_path','set_false_path','set_max_delay',
                                      'set_clock_groups','set_disable_timing')):
        raise ValueError('unsupported full minimum-period timing exception')
    folder = root/'clock-readout'/task['id']; folder.mkdir(parents=True, exist_ok=False)
    fixed = {str(result_dir/name):sha(result_dir/name) for name in ('5_1_grt.odb','5_1_grt.sdc')}
    template = (ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl').read_text()
    p = profile('asap7'); output = folder/'period.tsv'
    replacements = {'PERIOD':task['period_ps'], 'OUTPUT':output,
                    'TRANSITION':p['clock_transition_ps'], 'SETUP':p['setup_uncertainty_ps'],
                    'HOLD':p['hold_uncertainty_ps']}
    for key, value in replacements.items(): template = template.replace('@'+key+'@', str(value))
    script = folder/'period.tcl'; script.write_text(template)
    base = next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
    command = base + ['run', 'RUN_SCRIPT='+str(script), 'RUN_LOG_NAME_STEM=workload_clock_limit',
                      'VULSIM_EVAL_DB=5_1_grt.odb', 'VULSIM_EVAL_SDC=5_1_grt.sdc']
    ledger = ComparisonLedger(root, task); a = read(root/'admission.json')
    ctx = dict(target_platform='asap7', admission_id=a['id'], task_id=task['id'])
    env = dict(os.environ, OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', QT_QPA_PLATFORM='offscreen')
    with ledger.job(ctx):
        reservation = ledger.reserve(None,120,4,'final_evaluation',command,folder/'readout',context=ctx)
        record = run_command(command,folder,'readout',120,env,8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record); write(folder/'command.json',dict(record,budget_reservation_id=reservation['id']))
    if record['exit_code']:
        raise ValueError('fixed-DB clock readout failed: '+record['log'])
    if any(sha(name) != digest for name,digest in fixed.items()):
        raise ValueError('physical checkpoint changed during readout')
    rows = {name:dict(slack_ps=float(slack),required_period_ps=float(period))
            for name,slack,period in (line.split('\t') for line in output.read_text().splitlines()[1:])}
    full = rows['full_setup_threshold']; metric = m['metrics'][-1]
    if abs(full['slack_ps']-metric['setup_worst_slack_ps']) > .005:
        raise ValueError('path classes do not reproduce full setup WNS')
    value = full['required_period_ps']
    write(folder/'result.json',dict(task=task['id'],target_ps=task['period_ps'],
          full_setup_minimum_period_ps=value,maximum_frequency_MHz=1e6/value,
          area_um2=metric['cell_area_um2'],hold_WNS_ps=metric['hold_worst_slack_ps'],
          hold_review_required=metric['hold_review_required'],classes=rows,fixed_inputs=fixed,
          scope='same post-CTS grt cells and RC; setup incl IO=0.2T and reset; hold reported separately'))


def run_matrix(root, task_ids=None):
    root = Path(root).resolve(); a = read(root/'admission.json')
    progress = read(root/'backend-progress.json')
    if task_ids is None and not set(a['capacity_pilot_task_ids']) <= set(progress['completed']):
        raise ValueError('run the finite named capacity pilots first; diagnose retained failures before the full matrix: '
                         + ', '.join(a['capacity_pilot_task_ids']))
    tasks = [t for t in a['tasks'] if task_ids is None or t['id'] in task_ids]
    if task_ids is not None and set(task_ids) != {t['id'] for t in tasks}:
        raise ValueError('unknown requested task')
    done = set(progress['completed']) | {e['task'] for e in progress['errors']}
    tasks = [t for t in tasks if t['id'] not in done]
    if any((root/'runs'/t['id']).exists() for t in tasks):
        raise ValueError('unsettled prior attempt; diagnose before explicit successor')
    progress.update(status='running', active=[t['id'] for t in tasks]); write(root/'backend-progress.json', progress)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(run_task, root, t): t for t in tasks}
        for future in as_completed(futures):
            task = futures[future]
            try:
                future.result(); progress['completed'].append(task['id'])
            except Exception as error:
                progress['errors'].append(dict(task=task['id'], reason=str(error)))
            progress['active'].remove(task['id']); write(root/'backend-progress.json', progress)
    progress['status'] = 'batch_settled'; write(root/'backend-progress.json', progress)
    return progress


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('action', choices=('admit', 'run'))
    p.add_argument('--root', type=Path, required=True); p.add_argument('--task', action='append')
    a = p.parse_args()
    print(admit(a.root) if a.action == 'admit' else run_matrix(a.root, a.task))
