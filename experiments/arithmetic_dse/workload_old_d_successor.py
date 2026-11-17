"""User-authorized old-D generation and changed-clock evaluation successor.

Old selector/compiler/model sources are imported unchanged from this checkout.
New requests get fresh equivalent-T selection, simulation, audit and replay.
All physical jobs share the original cumulative ledger and nine kernel slots.
Software errors are durable; neither software nor physical jobs auto-retry.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

from . import backend, budget, workload_latency_matrix as matrix
from . import workload_nine_runtime as runtime
from . import workload_final_selection as selector
from . import workload_dot16_latency as dot
from .workload_abcd import read, sha
from .workload_backend import measurement_sources, PURPOSE
from .workload_contracts import load
from .workload_final_software import BINARY, ENV

SOURCE = Path(__file__).resolve()
ROOT = SOURCE.parents[2]
DEFAULT = ROOT.parent / 'vulsim-artifacts/old-D-clock-successor-20261117-v2'
POLICY = SOURCE.parent / 'configs/backend_policy_old_d_successor_v14.json'
ORIGINAL = matrix.DEFAULT
REVIEW = ROOT.parent / 'vulsim-artifacts/old-D-results-review-20261117-v1/snapshot.json'
VERSION = 'old-D-new-request-successor-20261117-v1'
MODULE = 'experiments.arithmetic_dse.workload_old_d_successor'
SPECS = [
    ('montgomery256', 16, [2000, 2350], 'missing_RTL', 'frozen A-derived requests'),
    ('montgomery256', 32, [1000, 1200], 'missing_RTL', 'frozen A-derived requests'),
    ('mul128', 4, [1200, 1500], 'relaxed_clock', 'user requested range; original 600/750'),
    ('dot16', 4, [1700, 2100], 'relaxed_clock', 'user requested range; original 850/1050'),
    ('dot16', 5, [1400, 1700], 'relaxed_clock', 'user requested range; original 700/850'),
    ('karatsuba256', 4, [4350, 4750], 'relaxed_clock', 'repair-time successor; original 2300/2750'),
    ('karatsuba256', 8, [2150, 2300], 'relaxed_clock', 'repair-time successor; original 1150/1400'),
    ('ntt8x64', 16, [2200, 2400], 'relaxed_clock', 'setup repair implies about 1970ps; retain margin'),
]


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path, doc):
    path = Path(path); path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n')
    os.replace(tmp, path)


def frozen(path, doc):
    path = Path(path)
    if path.exists() and read(path) != doc:
        raise ValueError('immutable successor input changed: ' + str(path))
    if not path.exists():
        write(path, doc)


def profile(root, cid, L):
    return Path(root) / 'variants' / cid / f'L{L}'


def initialize(root):
    root = Path(root).resolve(); root.mkdir(parents=True, exist_ok=True)
    if (root / 'protocol.json').exists():
        return verify(root)
    evidence = read(REVIEW)
    refs = {r['case']: r for r in evidence['A_references']}
    specs = []
    for cid, L, targets, reason, basis in SPECS:
        assert len(targets) == 2 and targets[0] < targets[1]
        assert all(0 < T < .85 * refs[cid]['Tmin_ps'] for T in targets)
        specs.append(dict(case=cid, L=L, targets_ps=targets, reason=reason, basis=basis,
                          A_reference=refs[cid], id=f'{cid}-L{L}'))
    used = runtime.NineLedger().summary()
    maximum_tasks = sum(4 * len(s['targets_ps']) for s in specs)
    wall = maximum_tasks * (3600 + 14400 + 4 * 1800 + 120)
    policy = read(runtime.POLICY)
    policy.update(version='old-D-authorized-finite-envelope-v14',
                  revision_reason='User authorizes old-D missing RTL and relaxed-clock successors; exact 16 groups, at most 64 physical tasks.')
    policy['resources']['max_global_walltime_h'] = 1024
    policy['resources']['memory_limit_MiB'] = 16384
    assert used['walltime_s'] + wall < 1024 * 3600
    assert used['CPU_time_s'] + 2 * wall < policy['resources']['max_tool_CPU_time_h'] * 3600
    policy['successor_authorization'] = dict(
        date='2026-11-17', user_instruction='软件未生成的代码生成后入队；修复过重者放宽周期并重新生成后端；软件错误暂不动',
        prior_authorization='2026-11-13: 物理调用额度可以不管，只要这几天能完成实验',
        memory_authorization='2026-11-17: 内存不足反复终止的几个任务少开并行、增大内存限制',
        new_heavy_worker_cap=3, memory_limit_MiB=16384, software_parallelism='1/2/4/8 according to actual available memory',
        scope=specs, maximum_new_tasks=maximum_tasks, automatic_retries=0,
        existing_policies_modified=False, ledger_history_reset=False,
        active_handoff='caller-specific policy bridge over the same original transaction and job locks')
    frozen(POLICY, policy)
    files = set(SOURCE.parent.glob('*.py')) | set(SOURCE.parent.glob('backend/*.py'))
    files.update(measurement_sources())
    files.update([BINARY, selector.BASE / 'diagnostic-model.json',
                  matrix.PARENT / 'software/bindings.json', matrix.PARENT / 'software/characterization-contract.json',
                  ORIGINAL / 'protocol.json', REVIEW, runtime.POLICY, POLICY])
    for cid in {s['case'] for s in specs}:
        files.add(matrix.PARENT / 'software' / cid / 'static-pool.json')
        files.update((matrix.PARENT / 'software' / cid / 'source').rglob('*'))
    for L in (4, 5):
        files.add(dot.DEFAULT / f'L{L}/software/dot16/static-pool.json')
    doc = dict(version=VERSION, specs=specs, created_at=now(), old_source_root=str(ROOT),
               old_compiler=str(BINARY), model_refitted=False, R1_R5_solver_enabled=False,
               changed_T_requires_fresh_selection=True, original_A_reused=True,
               software_parallel_jobs=8, physical_parallel_jobs=9, threads_per_tool=2,
               new_heavy_worker_cap=3, memory_limit_MiB=16384,
               maximum_new_physical_tasks=maximum_tasks, worst_case_leaf_walltime_s=wall,
               CPU_envelope_s=2 * wall, starting_usage=used, excluded_software_error=[dict(case='ntt8x64', L=8)],
               old_and_new_attempts_retained=True, automatic_retries=0,
               files={str(p): sha(p) for p in sorted(files) if p.is_file()})
    frozen(root / 'protocol.json', doc)
    for s in specs:
        frozen(root / 'targets' / f"{s['id']}.json", s)
    return verify(root)


def verify(root):
    doc = read(Path(root) / 'protocol.json')
    if doc['version'] != VERSION or doc['old_source_root'] != str(ROOT):
        raise ValueError('old-D successor identity changed')
    for p, digest in doc['files'].items():
        if sha(p) != digest:
            raise ValueError('old-D frozen input changed: ' + p)
    return doc


def selected_ok(method, cid, L, T):
    if (method['case'] != cid or method['L'] != L or method['T_clk_ps'] != T or
            method['simulation_status'] != 'passed' or sha(method['rtl']) != method['rtl_sha256']):
        raise ValueError('selection/backend request, depth or RTL differs')
    receipt = read(method['simulation_receipt'])
    if receipt['status'] != 'passed' or receipt['rtl_sha256'] != method['rtl_sha256']:
        raise ValueError('functional receipt differs')


def circuit_hash(path):
    """Normalize only compiler provenance comments; preserve all HDL tokens."""
    text = Path(path).read_text(); out = []; i = 0
    while i < len(text):
        start = i
        if text[i] == '"':
            i += 1
            while i < len(text):
                if text[i] == '\\': i += 2; continue
                if text[i] == '"': i += 1; break
                i += 1
        elif text[i] == '\\':
            i += 1
            while i < len(text) and not text[i].isspace(): i += 1
        elif text.startswith('/*', i):
            end = text.find('*/', i + 2); i = len(text) if end < 0 else end + 2
        elif text.startswith('//', i):
            end = text.find('\n', i); i = len(text) if end < 0 else end
            comment = text[start:i]
            if comment.startswith('// decl: ') and '; prim: ' in comment:
                comment = comment.replace('/home/zyrv/vulsim-r1-r5/', '/home/zyrv/vulsim/')
            out.append(comment); continue
        else: i += 1
        out.append(text[start:i])
    return hashlib.sha256(''.join(out).encode()).hexdigest()


def same_inflight(m, cid, L, T):
    folder = ROOT.parent / 'vulsim-artifacts/r1-r5-parallel-20261117-v2/backend/matrix-r1r5-parallel2-dot16-L5'
    p = folder / 'admission.json'
    if cid != 'dot16' or L != 5 or not p.exists(): return None
    for t in read(p)['tasks']:
        run = folder / 'runs' / t['id']
        if (t['period_ps'] == T and t['abc_target_ps'] == T and t['threads'] == 2 and
                (run / 'manifest.json').exists() and sha(t['rtl']) == t['rtl_sha256'] and
                circuit_hash(m['rtl']) == circuit_hash(t['rtl'])):
            return dict(batch=str(folder), task_id=t['id'], run=str(run),
                        circuit_sha256=circuit_hash(m['rtl']), source_RTL_sha256=t['rtl_sha256'],
                        new_RTL_sha256=m['rtl_sha256'], source_admission_sha256=sha(p),
                        rule='same circuit, L, T, ASAP7 physical flow and two threads; actual source outcome retained')
    return None


def software(root, cid, L):
    doc = verify(root); s = next(s for s in doc['specs'] if (s['case'], s['L']) == (cid, L))
    variant = profile(root, cid, L); soft = variant / 'software'; soft.mkdir(parents=True, exist_ok=True)
    for name in ('bindings.json', 'characterization-contract.json'):
        src = matrix.PARENT / 'software' / name; dst = soft / name
        if not dst.exists(): shutil.copyfile(src, dst)
        assert sha(src) == sha(dst)
    original_L = next(c for c in load()['cases'] if c['id'] == cid)['formal_targets'][0]['L']
    soft_protocol = (dict(doc, case=cid, L=L, target=read(Path(root) / 'targets' / f'{cid}-L{L}.json'))
                     if cid != 'dot16' and L != original_L else
                     dict(version=VERSION, spec=s, parent_protocol_sha256=sha(Path(root) / 'protocol.json')))
    frozen(soft / 'protocol.json', soft_protocol)
    dest = soft / cid / 'source'
    if not dest.exists(): shutil.copytree(matrix.PARENT / 'software' / cid / 'source', dest)
    complete = soft / cid / 'final-selections.json'
    if not complete.exists():
        if cid == 'dot16':
            src = dot.DEFAULT / f'L{L}/software/dot16/static-pool.json'
            shutil.copyfile(src, soft / cid / 'static-pool.json')
            with patch.object(selector, 'balanced', dot.active_balanced):
                selector.select_case(soft, cid, s['targets_ps'])
            dot.selected_occupancy(soft)
        else:
            if L == original_L:
                shutil.copyfile(matrix.PARENT / 'software' / cid / 'static-pool.json', soft / cid / 'static-pool.json')
                selector.select_case(soft, cid, s['targets_ps'])
            else:
                # Directory override only: the original finite selector remains unchanged.
                with patch.object(matrix, 'variant_root', lambda r, c, d: profile(r, c, d)):
                    matrix.select_new(root, cid, L)
    from .workload_final_replay import replay
    from .workload_final_audit import audit
    replayed = replay(soft); audited = audit(soft); matrix.occupancy(soft, cid)
    if replayed['targets'] != 2 or audited['records'] != 10:
        raise ValueError('old-D software validation incomplete')
    selections = read(complete)
    if selections['targets_ps'] != s['targets_ps']:
        raise ValueError('selected requests differ')
    for g in selections['records']:
        for method in ('B', 'C', 'D', 'same_policy_static'):
            selected_ok(g['methods'][method], cid, L, g['target']['T_ps'])
    files = [complete, soft / 'selected-replay.json', soft / 'all-selected-owner-audit.json',
             soft / 'matrix-stage-occupancy.json']
    for p in (soft / 'selected').rglob('*'):
        if p.is_file(): files.append(p)
    frozen(variant / 'software-ready.json', dict(status='passed', spec=s, EDA_calls=0,
            protocol_sha256=sha(Path(root) / 'protocol.json'), files={str(p): sha(p) for p in files}))
    return str(complete)


class WaveLedger(runtime.NineLedger):
    """Versioned caller envelope; preserve the live predecessor ledger identity."""
    def __init__(self, batch=None, task=None):
        super().__init__(); self.policy = POLICY; self.batch = batch; self.task = task

    @contextmanager
    def _transaction(self):
        bridge = dict(version=VERSION, policy=str(POLICY), policy_sha256=sha(POLICY),
                      cumulative_ledger=str(budget.LEDGER), original_policy_sha256=sha(runtime.POLICY),
                      authorization='explicit old-D successor tasks; inherited 2026-11-13 finite envelope authorization',
                      old_policies_and_all_usage_preserved=True)
        with runtime.NineLedger()._transaction() as state:
            entries = state.setdefault('caller_policy_bridges', [])
            matching = [e for e in entries if e['version'] == VERSION]
            if matching and matching != [bridge]: raise ValueError('caller policy bridge changed')
            if not matching: entries.append(bridge)
            yield state

    def reserve(self, stage, timeout_s, threads, purpose, command, output, *, context=None):
        a = verify_batch(self.batch); t = self.task
        if t not in a['tasks'] or threads != 2 or purpose != a['role']:
            raise ValueError('unregistered old-D successor leaf')
        prior = [e for e in read(self.path)['entries'] if e.get('admission_id') == a['id'] and e.get('task_id') == t['id']]
        if stage in ('synth', 'grt'):
            if timeout_s != t[stage + '_timeout_s'] or any(e['stage'] == stage for e in prior):
                raise ValueError('repeated or changed physical stage')
        else:
            if Path(output).name in ('synth-snapshot', 'grt-snapshot', 'clock-readout'):
                timeout_s = t['support_timeout_s']
            if stage is not None or timeout_s > t['support_timeout_s'] or sum(e['stage'] is None for e in prior) >= 4:
                raise ValueError('support envelope exceeded')
        return budget.Ledger.reserve(self, stage, timeout_s, threads, purpose, command, output, context=context)


def admit(root, s):
    variant = profile(root, s['case'], s['L']); ready = variant / 'software-ready.json'
    if not ready.exists(): return None
    batch = Path(root) / 'backend' / ('matrix-old-d-' + s['id'])
    if (batch / 'admission.json').exists(): return verify_batch(batch)
    r = read(ready)
    for p, h in r['files'].items():
        if sha(p) != h: raise ValueError('validated selection changed')
    doc = read(variant / 'software' / s['case'] / 'final-selections.json'); tasks = {}; reused = []
    for g in doc['records']:
        T = g['target']['T_ps']
        for method in ('B', 'C', 'D', 'same_policy_static'):
            m = g['methods'][method]; selected_ok(m, s['case'], s['L'], T)
            reuse = same_inflight(m, s['case'], s['L'], T)
            if reuse:
                reused.append(dict(case=s['case'], L=s['L'], T_ps=T, method=method, **reuse))
                continue
            key = T, m['rtl_sha256']
            if key not in tasks:
                t = dict(id=f"{s['id']}-T{T}-{m['rtl_sha256'][:12]}-old-d", case=s['case'], L=s['L'],
                         period_ps=T, abc_target_ps=T, rtl=m['rtl'], rtl_sha256=m['rtl_sha256'],
                         simulation_receipt=m['simulation_receipt'], simulation_status='passed', shared_methods=[],
                         threads=2, memory_limit_MiB=16384,
                         synth_timeout_s=3600, grt_timeout_s=14400, support_timeout_s=1800,
                         software_ready=str(ready), source_selection_file=str(Path(m['rtl']).with_name('selection.json')))
                if s['case'] == 'montgomery256':
                    from .workload_tight_continue import PROXY, PROVER
                    t['verification_override'] = dict(proxy=str(PROXY), proxy_sha256=sha(PROXY),
                                                      prover=str(PROVER), prover_sha256=sha(PROVER), sufficient_condition_only=True)
                tasks[key] = t
            tasks[key]['shared_methods'].append(method)
    frozen(variant / 'physical-reuse.json', dict(rows=reused, source_outcomes_not_promoted=True))
    files = dict(r['files']); files.update({str(p): sha(p) for p in [SOURCE, POLICY, ready, Path(root) / 'protocol.json', *measurement_sources()]})
    for t in tasks.values():
        if t.get('verification_override'):
            for key in ('proxy', 'prover'):
                p = Path(t['verification_override'][key]); files[str(p)] = sha(p)
    frozen(batch / 'freeze.json', dict(version=VERSION, tasks=list(tasks.values()), files=files,
            selection_frozen_before_measurement=True, application_PPA_for_selection=False))
    frozen(batch / 'admission.json', dict(version=VERSION, id=batch.name, role='final_evaluation', purpose=PURPOSE,
            tasks=list(tasks.values()), source_sha256=sha(SOURCE), freeze_sha256=sha(batch / 'freeze.json'),
            policy_sha256=sha(POLICY), original_shared_ledger=str(budget.LEDGER), parallel_jobs=9,
            threads_per_tool=2, automatic_retries=0, call_caps=dict(synth=len(tasks), grt=len(tasks), support=4 * len(tasks)),
            old_model_and_selector=True, created_at=now()))
    return verify_batch(batch)


def verify_batch(batch):
    batch = Path(batch); a = read(batch / 'admission.json'); f = read(batch / 'freeze.json')
    if a['version'] != VERSION or a['tasks'] != f['tasks'] or a['freeze_sha256'] != sha(batch / 'freeze.json') or a['policy_sha256'] != sha(POLICY):
        raise ValueError('old-D admission differs')
    for p, h in f['files'].items():
        if sha(p) != h: raise ValueError('old-D admitted input changed: ' + p)
    return a


def physical(batch, tid):
    a = verify_batch(batch); t = next(t for t in a['tasks'] if t['id'] == tid)
    original_command = backend.run_command
    original_clock = runtime.clock
    def command(cmd, out, stem, timeout, env, memory_limit_mib=None, **kwargs):
        if stem in ('synth-snapshot', 'grt-snapshot', 'clock-readout'): timeout = t['support_timeout_s']
        return original_command(cmd, out, stem, timeout, env, memory_limit_mib, **kwargs)
    def clock(out, task, execute, manifest):
        def support(extra, stem, timeout, stage):
            return execute(extra, stem, t['support_timeout_s'], stage)
        return original_clock(out, task, support, manifest)
    with patch.object(runtime, 'verify', verify_batch), patch.object(runtime, 'TaskLedger', WaveLedger), \
            patch.object(backend, 'POLICY', POLICY), patch.object(backend, 'run_command', command), patch.object(runtime, 'clock', clock):
        # _run_task normally installs runtime.POLICY; restore only the snapshot
        # policy inside _evaluate so old active callers retain their own policy.
        original_evaluate = backend._evaluate
        def evaluate(args, ledger):
            with patch.object(backend, 'POLICY', POLICY): return original_evaluate(args, ledger)
        with patch.object(backend, '_evaluate', evaluate): return runtime.run_task(batch, tid)


def status(root, software_children=None, physical_children=None):
    root = Path(root); doc = read(root / 'protocol.json'); attempts = read(root / 'software-attempts.json') if (root / 'software-attempts.json').exists() else {}
    rows = []
    for s in doc['specs']:
        ready = profile(root, s['case'], s['L']) / 'software-ready.json'
        rows.append(dict(s, status='ready' if ready.exists() else attempts.get(s['id'], {}).get('status', 'queued'),
                         attempt=attempts.get(s['id'])))
    tasks = []
    ledger = read(budget.LEDGER); claims = {(j['admission_id'], j['task_id']): j for j in ledger['jobs']}
    for p in sorted((root / 'backend').glob('*/admission.json')):
        a = read(p)
        for t in a['tasks']:
            out = p.parent / 'runs' / t['id'] / 'measurement-outcome.json'; claim = claims.get((a['id'], t['id']))
            state = read(out) if out.exists() else dict(status='running' if claim and claim['status'] == 'active' else 'claimed' if claim else 'queued')
            tasks.append(dict(state, case=t['case'], L=t['L'], T_ps=t['period_ps'], methods=t['shared_methods'], task_id=t['id'],
                              batch=str(p.parent), run=str(out.parent)))
    for p in sorted((root / 'variants').glob('*/L*/physical-reuse.json')):
        for r in read(p)['rows']:
            outcome = Path(r['run']) / 'measurement-outcome.json'
            state = read(outcome) if outcome.exists() else dict(status='running')
            tasks.append(dict(state, case=r['case'], L=r['L'], T_ps=r['T_ps'], methods=[r['method']],
                              run=r['run'], task_id=r['task_id'], reused_existing_attempt=True))
    result = dict(at=now(), version=VERSION, software=rows, physical=tasks,
                  software_workers=software_children if software_children is not None else sum(r['status'] == 'running' for r in rows),
                  physical_workers=physical_children if physical_children is not None else sum(t['status'] == 'running' and not t.get('reused_existing_attempt') for t in tasks),
                  global_active_jobs=sum(j['status'] in ('active', 'unsettled') for j in ledger['jobs']),
                  physical_parallel_cap=9, threads_per_tool=2, automatic_retries=0,
                  NTT_L8='retained software error; not launched', R1_R5_software='stopped')
    result['memory_available_MiB'] = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))) // 1024
    result['memory_scheduling'] = 'software 1/2/4/8 as available memory grows; at most 3 new 16GiB physical workers; global 9 slots'
    write(root / 'status.json', result)
    return result


def run(root):
    root = Path(root); doc = verify(root); soft_children = {}; physical_children = {}
    with (root / 'controller.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        journal = read(root / 'software-attempts.json') if (root / 'software-attempts.json').exists() else {}
        backend_attempts = read(root / 'backend-attempts.json') if (root / 'backend-attempts.json').exists() else {}
        while True:
            verify(root)
            for key, child in list(soft_children.items()):
                code = child.poll()
                if code is None: continue
                journal[key].update(status='completed' if code == 0 else 'error', exit_code=code, finished_at=now())
                del soft_children[key]; write(root / 'software-attempts.json', journal)
            available = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))) // 1024
            software_cap = 8 if available >= 49152 else 4 if available >= 32768 else 2 if available >= 20480 else 1
            for s in doc['specs']:
                if s['id'] in journal or len(soft_children) >= software_cap or available < 12288: continue
                logfile = root / 'software-logs' / (s['id'] + '.log'); logfile.parent.mkdir(exist_ok=True)
                with logfile.open('a') as log:
                    child = subprocess.Popen([sys.executable, '-B', '-u', '-X', 'faulthandler', '-m', MODULE, 'software',
                            '--root', str(root), '--case', s['case'], '--L', str(s['L'])], cwd=ROOT,
                            stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                            env=dict(os.environ, OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1'))
                soft_children[s['id']] = child
                journal[s['id']] = dict(status='running', pid=child.pid, started_at=now(), log=str(logfile), attempts=1)
                write(root / 'software-attempts.json', journal)
                available -= 8192
            for s in doc['specs']: admit(root, s)
            for key, child in list(physical_children.items()):
                if child.poll() is None: continue
                backend_attempts[key].update(exit_code=child.returncode, finished_at=now())
                del physical_children[key]; write(root / 'backend-attempts.json', backend_attempts)
            state = read(budget.LEDGER); claimed = {(j['admission_id'], j['task_id']) for j in state['jobs']}
            active = sum(j['status'] in ('active', 'unsettled') for j in state['jobs'])
            available = int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))) // 1024
            unclaimed = sum(tuple(key.split('/', 1)) not in claimed for key in physical_children)
            if active + unclaimed < 9 and len(physical_children) < 3 and shutil.disk_usage(root).free > 24 * 1024**3:
                candidates = []
                for p in sorted((root / 'backend').glob('*/admission.json')):
                    a = read(p)
                    for t in a['tasks']:
                        key = a['id'] + '/' + t['id']
                        if (a['id'], t['id']) not in claimed and key not in backend_attempts and available > t['memory_limit_MiB'] + 8192:
                            candidates.append((key, p.parent, t))
                if candidates:
                    key, batch, t = candidates[0]; logfile = root / 'backend-logs' / (t['id'] + '.log'); logfile.parent.mkdir(exist_ok=True)
                    with logfile.open('a') as log:
                        child = subprocess.Popen([sys.executable, '-B', '-u', '-m', MODULE, 'physical', '--root', str(batch), '--task-id', t['id']],
                                cwd=ROOT, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
                    physical_children[key] = child
                    backend_attempts[key] = dict(pid=child.pid, started_at=now(), log=str(logfile), attempts=1)
                    write(root / 'backend-attempts.json', backend_attempts)
            result = status(root, len(soft_children), len(physical_children))
            if len(journal) == len(doc['specs']) and not soft_children and not physical_children and not any(t['status'] in ('queued', 'running', 'claimed') for t in result['physical']):
                write(root / 'controller-completed.json', dict(at=now(), status='settled', software_errors_retained=True)); return
            time.sleep(10)


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('action', choices=('initialize', 'run', 'software', 'physical', 'status'))
    p.add_argument('--root', type=Path, default=DEFAULT); p.add_argument('--case'); p.add_argument('--L', type=int); p.add_argument('--task-id')
    a = p.parse_args()
    if a.action == 'initialize': result = initialize(a.root)
    elif a.action == 'software': result = software(a.root, a.case, a.L)
    elif a.action == 'physical': result = physical(a.root, a.task_id)
    elif a.action == 'run': result = run(a.root)
    else: result = status(a.root)
    print(json.dumps(result, ensure_ascii=False, indent=2))
