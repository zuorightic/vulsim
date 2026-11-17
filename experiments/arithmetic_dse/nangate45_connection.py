"""Three one-shot connection probes, sharing the live nine-slot ledger.

No source, policy, controller, or installation used by ASAP7 is changed.
The patched admission callback lives only in this worker process.
"""
import argparse
from contextlib import ExitStack
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from . import backend, budget, platform_probe
from .platforms import profile
from . import workload_nine_runtime as runtime

ROOT = Path(__file__).resolve().parents[2]
VERSION = 'nangate45-n12-connection-v1'
TASKS = ('add32', 'mul32', 'mac8')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def prepare(root):
    root = Path(root).resolve()
    admission = root / 'admission.json'
    if admission.exists():
        return verify(root)
    if root.is_relative_to(ROOT):
        raise ValueError('physical artifacts must stay outside the repository')
    root.mkdir(parents=True, exist_ok=True)
    tasks = []
    for name in TASKS:
        width = 8 if name == 'mac8' else 32
        result = 33 if name == 'add32' else 2 * width
        expression = "{1'b0, la} + {1'b0, lb}" if name == 'add32' else 'la * lb'
        if name == 'mac8':
            expression = '(la * lb) + lc'
        extra_port = ', input wire [15:0] c' if name == 'mac8' else ''
        extra_decl = 'reg [15:0] lc;' if name == 'mac8' else ''
        extra_reset = 'lc <= 0;' if name == 'mac8' else ''
        extra_update = 'lc <= c;' if name == 'mac8' else ''
        rtl = root / 'rtl' / (name + '.sv')
        rtl.parent.mkdir(exist_ok=True)
        rtl.write_text(f'''module Probe(input wire clk, input wire rstn,
  input wire [{width-1}:0] a, input wire [{width-1}:0] b{extra_port},
  output reg [{result-1}:0] y);
reg [{width-1}:0] la, lb; {extra_decl}
always @(posedge clk) begin
  if (!rstn) begin la <= 0; lb <= 0; y <= 0; {extra_reset} end
  else begin la <= a; lb <= b; {extra_update} y <= {expression}; end
end
endmodule
''')
        tasks.append(dict(id=name, platform='nangate45', profile_sha256=profile('nangate45')['profile_sha256'],
            rtl=str(rtl), rtl_sha256=sha(rtl), top='Probe', period_ps=3000, abc_target_ps=3000,
            stage='grt', threads=2, memory_limit_MiB=2048, synth_timeout_s=300,
            route_timeout_s=1200, purpose='prototype', sampling_role='connection_only_not_training'))
    sources = [Path(__file__), runtime.SOURCE, runtime.POLICY, runtime.BRIDGE,
               budget.POLICY, budget.CHECKPOINT,
               *[ROOT / 'experiments/arithmetic_dse' / n for n in
                 ('backend.py', 'budget.py', 'platforms.py', 'platform_probe.py', 'processes.py', 'sdc.py')],
               ROOT / 'experiments/arithmetic_dse/configs/platforms/nangate45.json']
    sources += [p for p in backend.ASSETS.iterdir() if p.is_file()]
    state = read(budget.LEDGER)
    wall = 3 * (300 + 1200 + 60 + 120 + 120)
    limits = read(runtime.POLICY)['resources']
    used = budget.usage(state['entries'])
    if (used['walltime_s'] + wall > 3600 * limits['max_global_walltime_h'] or
            used['CPU_time_s'] + 2 * wall > 3600 * limits['max_tool_CPU_time_h'] or
            any(used[s] + 3 > limits[k] for s, k in budget.STAGE_LIMITS.items() if s != 'final')):
        raise ValueError('finite probe envelope exceeds shared remaining funding')
    write(admission, dict(version=VERSION, id='matrix-nangate45-n12-connection-v1',
        purpose='nangate45_connection_only', policy_sha256=sha(runtime.POLICY),
        tasks=tasks, automatic_retries=0, call_caps=dict(synth=3, grt=3, final=0, support=9),
        serial_workers=1, threads=2, memory_limit_MiB=2048, minimum_available_MiB=10240,
        worst_case_leaf_walltime_s=wall, CPU_envelope_s=2*wall, storage_envelope_MiB=1024,
        starting_usage=used, ledger=str(budget.LEDGER),
        files={str(p): sha(p) for p in sources},
        active_ledger_identity=dict(policy_sha256=state['policy_sha256'], checkpoint_sha256=state['checkpoint_sha256']),
        runtime_checkpoint_pending_migration=not runtime.CHECKPOINT.exists(),
        model_training=False, application_selection=False, shared_policies_modified=False))
    return verify(root)


def verify(root):
    doc = read(Path(root) / 'admission.json')
    if doc['version'] != VERSION or tuple(t['id'] for t in doc['tasks']) != TASKS:
        raise ValueError('connection admission identity differs')
    for name, expected in doc['files'].items():
        if sha(name) != expected:
            raise ValueError('connection frozen source changed: ' + name)
    for task in doc['tasks']:
        if task['rtl_sha256'] != sha(task['rtl']) or task['profile_sha256'] != profile('nangate45')['profile_sha256']:
            raise ValueError('connection RTL/profile changed')
    return doc


def verify_admission(args, selected, rtl, ledger):
    doc = verify(args.admission.parent)
    task = next(t for t in doc['tasks'] if t['id'] == args.task_id)
    expected = dict(platform=selected['platform'], profile_sha256=selected['profile_sha256'],
        rtl=str(rtl), rtl_sha256=sha(rtl), top=args.top, period_ps=args.period_ps,
        abc_target_ps=args.abc_target_ps, stage=args.stage, threads=args.threads,
        memory_limit_MiB=args.memory_limit_mib, synth_timeout_s=args.synth_timeout_s,
        route_timeout_s=args.route_timeout_s, purpose=args.budget_purpose)
    if any(task[k] != v for k, v in expected.items()) or args.admission_id != doc['id']:
        raise ValueError('requested probe differs from frozen task')
    if args.period_role != 'resource_trial' or args.io_delay_max_ps is not None or args.resume_synth_from:
        raise ValueError('connection clock/IO/resume contract differs')
    ledger.check_job_admission()  # other live reservations are allowed, never refunded
    state = read(ledger.path)
    previous = [e for e in state['entries'] if e.get('admission_id') == doc['id']]
    if any(e.get('task_id') == task['id'] for e in previous):
        raise ValueError('probe already attempted; no automatic retry')
    for stage in ('synth', 'grt'):
        if sum(e['stage'] == stage for e in previous) >= doc['call_caps'][stage]:
            raise ValueError('probe physical-call envelope exhausted')
    return sha(args.admission)


def run(root, name):
    root = Path(root).resolve()
    doc = verify(root)
    index = TASKS.index(name)
    if index:
        previous = read(root / 'runs' / TASKS[index-1] / 'manifest.json')
        if previous['status'] != 'completed':
            raise ValueError('previous small connection probe must complete first')
    available = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines()
                         if l.startswith('MemAvailable:'))) // 1024
    if available < doc['minimum_available_MiB']:
        raise budget.BudgetExceeded('leave 8GiB available beyond the 2GiB probe cap')
    if any(j['admission_id'] == doc['id'] and j['status'] == 'active'
           for j in read(budget.LEDGER).get('jobs', [])):
        raise budget.BudgetExceeded('one serial Nangate45 connection worker only')
    t = doc['tasks'][index]
    args = SimpleNamespace(out=root/'runs'/name, platform=t['platform'], threads=t['threads'],
        stage=t['stage'], memory_limit_mib=t['memory_limit_MiB'], period_ps=t['period_ps'],
        period_role='resource_trial', abc_target_ps=t['abc_target_ps'], io_delay_max_ps=None,
        budget_purpose=t['purpose'], admission_id=doc['id'], task_id=t['id'],
        sample_contract=None, admission=root/'admission.json', resume_synth_from=None,
        orfs=Path('/home/zyrv/OpenROAD-flow-scripts'), rtl=Path(t['rtl']), top=t['top'],
        synth_timeout_s=t['synth_timeout_s'], route_timeout_s=t['route_timeout_s'])
    args.out.parent.mkdir(exist_ok=True)
    ledger = runtime.NineLedger()
    with ledger.job(dict(target_platform=t['platform'], admission_id=doc['id'], task_id=name)):
        with ExitStack() as stack:
            stack.enter_context(patch.object(backend, 'POLICY', runtime.POLICY))
            stack.enter_context(patch.object(platform_probe, 'verify_admission', verify_admission))
            return backend._evaluate(args, ledger)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--prepare', action='store_true')
    p.add_argument('--task', choices=TASKS)
    a = p.parse_args()
    if a.prepare:
        print(json.dumps(prepare(a.root), indent=2))
    elif a.task:
        raise SystemExit(run(a.root, a.task))
    else:
        p.error('--prepare or --task is required')
