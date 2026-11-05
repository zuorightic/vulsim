"""Frozen four-thread ASAP7 state/boundary fitting collection; tests stay locked."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import copy
from datetime import datetime, timezone
import fcntl
from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import re
import shutil
import sys
from types import SimpleNamespace

from .budget import Ledger, POLICY, usage
from .model_collection import sha, write
from .model_m2_state_samples import specifications, source, features, VERSION

ROOT = Path(__file__).resolve().parents[2]
CONFIG = Path(__file__).with_name('configs')/'model_asap7_m2_state_boundary_v1.json'
ORFS = Path('/home/zyrv/OpenROAD-flow-scripts')
SUFFIX = Path('asap7/arithmetic_probe/base')


def read(path):
    return json.loads(Path(path).read_text())


def exclusive(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def prepare(folder, rtl_proof):
    from .platforms import profile
    from .model_m2_evaluate import measurement_identity
    cfg = read(CONFIG)
    proof = read(rtl_proof)
    if (proof['status'] != 'passed' or proof['source_groups'] != 48
        or proof.get('protocol_sha256') != sha(CONFIG)
        or proof.get('generator_source_sha256') != sha(Path(__file__).with_name('model_m2_state_samples.py'))):
        raise ValueError('current actual state-bank RTL preflight required')
    parent = ROOT/cfg['parent_primitives']
    if sha(parent) != cfg['parent_primitives_sha256'] or read(parent)['quality_status'] != 'passed':
        raise ValueError('unchanged qualified primitive parent required')
    count = sum(s['tasks'] for s in cfg['splits'].values())
    limits = read(POLICY)['resources']
    current = usage(read(Ledger().path)['entries'])
    later = cfg['later_work_reserved']
    wall = count*cfg['resources']['per_task_walltime_envelope_s']+cfg['support_walltime_envelope_s']
    if (current['walltime_s']+wall+later['walltime_s'] > limits['max_global_walltime_h']*3600
        or current['CPU_time_s']+4*wall+later['CPU_time_s'] > limits['max_tool_CPU_time_h']*3600
        or current['synth']+count+later['synth'] > limits['max_synthesis_calls']
        or current['grt']+count+later['grt'] > limits['max_global_route_calls']):
        raise ValueError('full state cohort and later work not funded')
    reserve = count*cfg['resources']['storage_per_task_bytes']+later['storage_bytes']
    if shutil.disk_usage(folder.parent).free < reserve:
        raise ValueError('state cohort and later storage reserve unavailable')
    folder.mkdir(parents=True, exist_ok=False)
    selected = profile('asap7')
    tasks = []
    seen = {}
    for spec in specifications(cfg):
        directory = folder/'sources'/spec['id']
        directory.mkdir(parents=True)
        rtl, labels = source(spec)
        (directory/'input.sv').write_text(rtl)
        exclusive(directory/'contract.json', {'version': 'arithmetic-model-labels-v1',
            'split': spec['split'], 'source_group': spec['id'], 'labels': labels,
            'state_geometry': spec, 'feature_schema': VERSION, 'protocol_sha256': sha(CONFIG)})
        h = sha(directory/'input.sv')
        if h in seen:
            raise ValueError('duplicate state source across registered groups')
        seen[h] = spec['split']
        for index, period in enumerate(cfg['SDC_ps']):
            tasks.append({'id': spec['id']+f'-t{index}', 'source_group': spec['id'], 'split': spec['split'],
                'platform': 'asap7', 'profile_sha256': selected['profile_sha256'], 'top': 'ModelBundle',
                'period_ps': period, 'abc_target_ps': 1500, 'stage': 'grt',
                'rtl': str((directory/'input.sv').resolve()), 'rtl_sha256': h,
                'sample_contract': str((directory/'contract.json').resolve()),
                'sample_contract_sha256': sha(directory/'contract.json'),
                'features': features(spec, period), 'input_bits': spec['input_bits'], 'capture_bits': spec['capture_bits'],
                'mapping_source_task': spec['id']+'-t0' if index else None})
    if dict(Counter(t['split'] for t in tasks)) != {s: v['tasks'] for s, v in cfg['splits'].items()}:
        raise ValueError('state source/task counts differ from registration')
    names = ['model_m2_state_collection.py', 'model_m2_state_samples.py', 'backend.py', 'budget.py',
        'processes.py', 'platforms.py', 'sdc.py', 'model_collection.py', 'model_samples.py',
        'model_m2_live_cec_v3.py', 'model_m2_cec.py', 'model_m2_aig.py', 'model_m2_state.py',
        'model_m2_mux_collection.py', 'model_m2_evaluate.py']
    paths = [Path(__file__).with_name(n) for n in names]+[CONFIG, POLICY]
    paths += sorted(p for p in Path(__file__).with_name('backend').iterdir() if p.is_file())
    hashes = {}
    for path in paths:
        name = str(path.relative_to(ROOT))
        dst = folder/'source'/name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dst)
        hashes[name] = sha(path)
    reference = ROOT/'build/step7-m2-models-20261105/mux-context-v1/runs/mux-train-P2-F1-w8-t0/manifest.json'
    exclusive(folder/'admission.json', {'version': 'asap7-m2-state-fitting-admission-v1', 'id': folder.name,
        'protocol_sha256': sha(CONFIG), 'policy_sha256': sha(POLICY), 'sources': hashes, 'tasks': tasks,
        'parent_model_path': str(parent), 'parent_model_sha256': sha(parent),
        'baseline_model_path': str(ROOT/cfg['old_state_baseline']), 'baseline_model_sha256': sha(ROOT/cfg['old_state_baseline']),
        'measurement_static_identity_sha256': measurement_identity(read(reference)),
        'physical_tools': read(reference)['tools'], 'capacity_pilots': cfg['capacity_pilots'],
        'resource_plan': {'tasks': count, 'walltime_envelope_s': wall, 'CPU_envelope_s': 4*wall,
            'storage_reserved_bytes': reserve, 'later_work_reserved': later},
        'RTL_preflight_path': str(rtl_proof.resolve()), 'RTL_preflight_sha256': sha(rtl_proof),
        'test_locked': True, 'automatic_retries': 0, 'formal_PPA_or_consumed_test_labels_read': False})
    exclusive(folder/'progress.json', {'phase': 'admitted', 'completed': [], 'active': [], 'errors': [],
        'waiting': [t['id'] for t in tasks if t['split'] != 'test'], 'capacity_qualified': False, 'test_locked': True})
    print(json.dumps({'status': 'prepared', 'tasks': dict(Counter(t['split'] for t in tasks)),
        'independent_locked': True, 'walltime_envelope_s': wall, 'storage_reserved_bytes': reserve}), flush=True)


def verify(folder):
    a = read(folder/'admission.json')
    if (a['version'] != 'asap7-m2-state-fitting-admission-v1' or a['protocol_sha256'] != sha(CONFIG)
        or a['policy_sha256'] != sha(POLICY) or not a['test_locked']
        or sha(a['parent_model_path']) != a['parent_model_sha256']
        or sha(a['baseline_model_path']) != a['baseline_model_sha256']):
        raise ValueError('changed state admission, baseline or frozen parent')
    for name, h in a['sources'].items():
        if sha(ROOT/name) != h or sha(folder/'source'/name) != h:
            raise ValueError('changed state producer: '+name)
    if sha(a['RTL_preflight_path']) != a['RTL_preflight_sha256']:
        raise ValueError('changed state RTL preflight')
    cfg = read(CONFIG)
    counts = Counter(t['split'] for t in a['tasks'])
    if dict(counts) != {name: s['tasks'] for name, s in cfg['splits'].items()}:
        raise ValueError('changed state split counts')
    for t in a['tasks']:
        if (t['period_ps'] not in cfg['SDC_ps'] or t['abc_target_ps'] != 1500
            or t['stage'] != 'grt' or t['platform'] != 'asap7'
            or t['id'] != t['source_group']+'-t'+str(cfg['SDC_ps'].index(t['period_ps']))):
            raise ValueError('changed registered state clock/role')
    return a


class StateLedger(Ledger):
    def __init__(self, folder, task):
        super().__init__()
        self.folder, self.task = folder, task

    def reserve(self, stage, timeout_s, threads, purpose, command, output, *, context=None):
        a = verify(self.folder)
        t = next(t for t in a['tasks'] if t['id'] == self.task['id'])
        if (t != self.task or t['split'] not in ('train', 'validation') or threads != 4
            or sha(t['rtl']) != t['rtl_sha256'] or sha(t['sample_contract']) != t['sample_contract_sha256']):
            raise ValueError('unregistered/locked state physical request')
        return super().reserve(stage, timeout_s, threads, purpose, command, output, context={**(context or {}),
            'target_platform': 'asap7', 'admission_id': a['id'], 'task_id': t['id'],
            'admission_sha256': sha(self.folder/'admission.json'), 'model_version': 'asap7-m2-state-bank-v1'})


def state_witness(directory, stage, cells):
    spec = read(directory/'sample-contract.json')['state_geometry']
    prefix = directory/'reports'/SUFFIX/('vulsim_'+stage)
    instances = [line.split('\t')[:2] for line in Path(str(prefix)+'_instances.tsv').read_text().splitlines()]
    counts = Counter({'data': 0, 'valid': 0, 'enable': 0})
    observer = functional = 0.
    for name, master in instances:
        c = cells.get(master)
        if c is None:
            raise ValueError('unknown state-bank cell')
        if name.startswith('bank/observer/'):
            if c['sequential']:
                raise ValueError('post-capture observer has state')
            observer += c['area_um2']
        elif name.startswith('bank/'):
            functional += c['area_um2']
            if c['sequential']:
                leaf = name.removeprefix('bank/')
                role = 'data' if any(fnmatchcase(leaf, p) for p in ('src*', 'dst*', 'y*')) else 'valid' if any(fnmatchcase(leaf, p) for p in ('valid_q*', 'ov*')) else 'enable' if leaf.startswith('enable_q') else None
                if role is None:
                    raise ValueError('unrecognized actual state register: '+name)
                counts[role] += 1
        elif c['sequential']:
            raise ValueError('unaccounted state outside the declared bank')
    expected = {'data': spec['features']['data_bits'], 'valid': spec['valid_registers'], 'enable': spec['separate_enable_registers']}
    if dict(counts) != expected:
        raise ValueError(f'actual state/control bits differ: {dict(counts)} != {expected}')
    return {'actual_register_bits': dict(counts), 'scoped_state_control_area_um2': functional,
            'excluded_observer_area_um2': observer, 'mapped_counts_are_prediction_inputs': False}


def seed_mapping(folder, t, out):
    source_dir = folder/'runs'/t['mapping_source_task']
    old = read(source_dir/'manifest.json')
    if old['status'] != 'completed' or sha(source_dir/'input.sv') != t['rtl_sha256']:
        raise ValueError('state source mapping incomplete or changed')
    out.mkdir(parents=True)
    for name in ('input.sv', 'sample-contract.json', 'liberty_cells.json', 'label_requests.tcl'):
        shutil.copy2(source_dir/name, out/name)
    shutil.copytree(source_dir/'source', out/'source')
    shutil.copytree(source_dir/'flow-scripts', out/'flow-scripts', symlinks=True)
    # Replace the t0 observer-only CTS override below, before any physical leaf.
    (out/'config.mk').write_text(re.sub(r'export VULSIM_CLOCK_PERIOD_PS = [^\n]+',
        'export VULSIM_CLOCK_PERIOD_PS = '+str(t['period_ps']),
        (source_dir/'config.mk').read_text().replace(str(source_dir), str(out))))
    results = out/'results'/SUFFIX
    results.mkdir(parents=True)
    net = source_dir/'results'/SUFFIX/'1_2_yosys.v'
    if sha(net) != old['evidence_sha256'][str(net.relative_to(source_dir))]:
        raise ValueError('changed exact state ABC mapping')
    shutil.copy2(net, results/net.name)
    from .model_m2_mux_collection import physical_base
    base = [x.replace(str(source_dir), str(out)) for x in physical_base(old) if not x.startswith('--assume-old=')]
    base.append('--assume-old='+str(results/'1_2_yosys.v'))
    m = copy.deepcopy(old)
    m.update(commands=[], metrics=[], task_id=t['id'], status='running', period_ps=t['period_ps'])
    m.pop('finished_at', None)
    m.pop('evidence_sha256', None)
    m['files_sha256'] = {name.replace(str(source_dir), str(out)): h for name, h in old['files_sha256'].items()}
    m['mapping_context']['sdc_period_ps'] = t['period_ps']
    m['mapping_context']['io_delay_max_ps'] = .2*t['period_ps']
    import hashlib
    m['mapping_context_sha256'] = hashlib.sha256(json.dumps(m['mapping_context'], sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    m['checkpoint_reuse'] = {'mode': 'exact_t0_mapping_fresh_SDC_ODB', 'source_run': str(source_dir),
        'source_manifest_sha256': sha(source_dir/'manifest.json'), 'source_netlist_sha256': sha(net),
        'old_ODB_or_SDC_copied': False, 'Yosys_ABC_reexecuted': False}
    return m, base


def run_task(folder, t):
    from .backend import _evaluate, stage_metrics, verify_orfs_area
    from .model_m2_mux_collection import render_cts
    from .model_m2_live_cec_v3 import verify_proof
    from .model_m2_evaluate import measurement_identity
    from .model_samples import read_labels
    from .platforms import profile, verify_wire_readback, resolve_environment, validate_environment
    from .processes import run_command
    from .sdc import verify_sdc, rtl_ports
    a = verify(folder)
    if t['split'] == 'test':
        raise ValueError('state independent test requires a separate frozen-selection admission')
    out = folder/'runs'/t['id']
    if out.exists():
        raise ValueError('preserve state attempt; no automatic retry')
    ledger = StateLedger(folder, t)
    context = {'target_platform': 'asap7', 'admission_id': a['id'], 'task_id': t['id']}
    env = os.environ.copy()
    env.update(OMP_NUM_THREADS='4', OPENBLAS_NUM_THREADS='4', YOSYS_MAX_THREADS='4',
        PYTHONDONTWRITEBYTECODE='1', QT_QPA_PLATFORM='offscreen', VULSIM_LABEL_REQUESTS=str(out/'label_requests.tcl'))
    with ledger.job(context):
        if t['mapping_source_task']:
            m, base = seed_mapping(folder, t, out)
        else:
            args = SimpleNamespace(out=out, platform='asap7', threads=4, stage='synth', memory_limit_mib=8192,
                period_ps=t['period_ps'], period_role='resource_trial', abc_target_ps=1500, io_delay_max_ps=None,
                budget_purpose='characterization', admission_id=a['id'], task_id=t['id'],
                sample_contract=Path(t['sample_contract']), admission=None, resume_synth_from=None, orfs=ORFS,
                rtl=Path(t['rtl']), top='ModelBundle', synth_timeout_s=300, route_timeout_s=1200, selection_freeze=None)
            _evaluate(args, ledger)
            m = read(out/'manifest.json')
            if m['status'] != 'completed':
                raise RuntimeError(t['id']+': initial synthesis failed: '+str(m.get('failure_reason')))
            base = next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
        m.update(status='running', stages_requested='grt', admission_id=a['id'], budget_job_id=ledger.job_id,
            state_admission_sha256=sha(folder/'admission.json'), state_collection_version=a['version'])
        def save():
            write(out/'manifest.json', m)
        def execute(command, stem, timeout, stage=None):
            m['active_stage'] = stem
            reservation = ledger.reserve(stage, timeout, 4, 'characterization', command, out/stem, context=context)
            m['active_reservation'] = reservation['id']
            save()
            c = run_command(command, out, stem, timeout, env, 8192, cpu_limit_s=reservation['CPU_time_s'])
            ledger.finish(reservation, c)
            c['budget_reservation_id'] = reservation['id']
            m['commands'].append(c)
            save()
            if c['exit_code']:
                raise RuntimeError(stem+': failed; timeout='+str(c['timed_out']))
        try:
            for name in ('model_m2_state_collection.py', 'model_m2_state_samples.py'):
                path = Path(__file__).with_name(name)
                dst = out/'source'/path.relative_to(ROOT)
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dst)
                m['source_sha256'][str(path.relative_to(ROOT))] = sha(path)
            wrapper = out/'live-cec.py'
            wrapper.write_text('import sys\nsys.path.insert(0,'+repr(str(ROOT))+')\nfrom experiments.arithmetic_dse.model_m2_live_cec_v3 import main\nmain()\n')
            request = out/'live-cec-request.json'
            write(request, {'libraries': m['libraries'], 'admission_sha256': sha(folder/'admission.json'),
                            'collection_plan_sha256': sha(folder/'admission.json')})
            cts = out/'flow-scripts/cts.tcl'
            cts.unlink()
            cts.write_text(render_cts((ORFS/'flow/scripts/cts.tcl').read_text(), wrapper, request,
                                     out/'logs'/SUFFIX/'structural_cec'))
            m['files_sha256'].update({str(p): sha(p) for p in (cts, wrapper, request, out/'config.mk')})
            for tool in m['tools'].values():
                if sha(tool['path']) != tool['sha256']:
                    raise ValueError('state physical executable changed')
            for lib in m['libraries']:
                if sha(lib['path']) != lib['sha256']:
                    raise ValueError('state Liberty changed')
            for name, h in m['files_sha256'].items():
                path = Path(name)
                if (path.is_relative_to(ORFS) or path.is_relative_to(ROOT/'experiments/arithmetic_dse/backend')) and sha(path) != h:
                    raise ValueError('state physical asset changed')
            if t['mapping_source_task']:
                execute(base+['vulsim-environment', 'VULSIM_ENV_FILE='+str(out/'effective-environment.txt')], 'environment', 60)
                raw = dict(line.strip().split('=', 1) for line in (out/'effective-environment.txt').read_text().splitlines() if line.strip())
                effective, origins = resolve_environment(raw)
                validate_environment(effective, profile('asap7'))
                for key in ('LIB_FILES', 'TECH_LEF', 'SC_LEF', 'CORNER', 'ASAP7_USE_VT', 'LIB_MODEL',
                            'TC_TEMPERATURE', 'ABC_DRIVER_CELL', 'ABC_LOAD_IN_FF', 'YOSYS_MAX_THREADS'):
                    if effective.get(key) != m['effective_environment'].get(key):
                        raise ValueError('state exact mapping environment changed: '+key)
                m.update(raw_make_environment=raw, effective_environment=effective, asset_resolution=origins)
                execute(base+['synth'], 'synth', 300, 'synth')
                execute(base+['run', 'RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),
                    'RUN_LOG_NAME_STEM=vulsim_synth', 'VULSIM_EVAL_STAGE=synth',
                    'VULSIM_EVAL_DB=1_synth.odb', 'VULSIM_EVAL_SDC=1_synth.sdc'], 'synth-snapshot', 120)
                m['metrics'] = []
            p = profile('asap7')
            if p['profile_sha256'] != t['profile_sha256']:
                raise ValueError('state platform changed')
            if measurement_identity(m) != a['measurement_static_identity_sha256']:
                raise ValueError('state physical identity differs from new primitives')
            cells = read(out/'liberty_cells.json')['cells']
            for stage in ('synth', 'grt'):
                if stage == 'grt':
                    execute(base+['grt'], 'grt', 1200, 'grt')
                    execute(base+['run', 'RUN_SCRIPT='+str(ROOT/'experiments/arithmetic_dse/backend/snapshot.tcl'),
                        'RUN_LOG_NAME_STEM=vulsim_grt', 'VULSIM_EVAL_STAGE=grt',
                        'VULSIM_EVAL_DB=5_1_grt.odb', 'VULSIM_EVAL_SDC=5_1_grt.sdc'], 'grt-snapshot', 120)
                reports = out/'reports'/SUFFIX
                g = stage_metrics(reports, stage, cells, t['period_ps'], selected=p)
                g['model_labels'] = read_labels(reports/('vulsim_'+stage), out/'sample-contract.json', g['raw_report_units']['time']['to_ps'])
                g['state_witness'] = state_witness(out, stage, cells)
                wire = verify_wire_readback(reports/('vulsim_'+stage+'_layer_rc.tsv'), p)
                if wire is not None:
                    g['wire_RC_readback'] = wire
                sdc = out/'results'/SUFFIX/({'synth': '1_synth', 'grt': '5_1_grt'}[stage]+'.sdc')
                m['sdc_contracts'][stage] = verify_sdc(sdc.read_text(), p, t['period_ps'], rtl_ports((out/'input.sv').read_text(), t['top']))
                native = read(out/'logs'/SUFFIX/({'synth': '1_synth.json', 'grt': '5_1_grt.json'}[stage]))[('synth' if stage == 'synth' else 'globalroute')+'__design__instance__area__stdcell']
                g['orfs_area_crosscheck'] = verify_orfs_area(g['cell_area_um2'], native)
                if not g['timing_coverage_complete']:
                    raise ValueError('state timing coverage incomplete')
                m['metrics'] = [x for x in m['metrics'] if x['stage'] != stage]+[g]
                save()
            verify_proof(out/'logs'/SUFFIX/'structural_cec/proof.json',
                out/'results'/SUFFIX/'4_before_rsz_lec.v', out/'results'/SUFFIX/'4_after_rsz_lec.v')
            m['status'] = 'completed'
            write(out/'metrics.json', m['metrics'])
        except Exception as error:
            m.update(status='failed', failure_stage=m.get('active_stage', 'state_preflight'), failure_reason=str(error))
        finally:
            m['finished_at'] = datetime.now(timezone.utc).isoformat()
            m['evidence_sha256'] = {str(path.relative_to(out)): sha(path) for name in ('logs', 'reports', 'results') for path in (out/name).rglob('*') if path.is_file()}
            save()
        print(json.dumps({'task': t['id'], 'status': m['status'], 'reason': m.get('failure_reason')}), flush=True)
        if m['status'] != 'completed':
            raise RuntimeError(t['id']+': '+m['failure_reason'])
    return t['id']


def seal_capacity(folder, admission):
    rows = []
    for tid in admission['capacity_pilots']:
        directory = folder/'runs'/tid
        m = read(directory/'manifest.json')
        if m['status'] != 'completed' or len(m['metrics']) != 2:
            raise ValueError('state capacity task incomplete')
        cells = read(directory/'liberty_cells.json')['cells']
        for metric in m['metrics']:
            if state_witness(directory, metric['stage'], cells) != metric['state_witness']:
                raise ValueError('state capacity witness differs')
        rows.append({'task_id': tid, 'manifest_sha256': sha(directory/'manifest.json'),
            'actual_register_bits': m['metrics'][-1]['state_witness']['actual_register_bits'],
            'peak_RSS_MiB': max(c['sampled_process_tree_peak_rss_KiB'] for c in m['commands'])/1024})
    exclusive(folder/'capacity-proof.json', {'status': 'passed', 'admission_sha256': sha(folder/'admission.json'),
        'runs': rows, 'scope': 'registered state fitting geometries only; independent state capacity and stage composition remain separately gated'})


def run(folder):
    a = verify(folder)
    indexed = {t['id']: t for t in a['tasks'] if t['split'] != 'test'}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/tid).exists() for tid in indexed):
            raise ValueError('existing state attempts require an explicit successor, no automatic retry')
        waiting, active, completed, errors, capacity = list(indexed), {}, [], [], False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_pilots']) <= set(completed):
                    seal_capacity(folder, a)
                    capacity = True
                while waiting and len(active) < 4 and not errors:
                    ready = next((tid for tid in waiting if (capacity or tid in a['capacity_pilots'])
                        and (not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed)), None)
                    if ready is None:
                        break
                    waiting.remove(ready)
                    active[pool.submit(run_task, folder, indexed[ready])] = ready
                write(folder/'progress.json', {'phase': 'fitting_collecting', 'active': list(active.values()),
                    'waiting': waiting, 'completed': completed, 'errors': errors,
                    'capacity_qualified': capacity, 'test_locked': True})
                if not active:
                    if waiting and not errors:
                        raise ValueError('state mapping/capacity dependency deadlock')
                    break
                done, _ = wait(active, timeout=1, return_when=FIRST_COMPLETED)
                for future in done:
                    tid = active.pop(future)
                    try:
                        completed.append(future.result())
                    except Exception as error:
                        errors.append({'task_id': tid, 'reason': str(error)})
        write(folder/'progress.json', {'phase': 'stopped_on_error' if errors else 'fitting_collection_complete',
            'active': [], 'waiting': waiting, 'completed': completed, 'errors': errors,
            'capacity_qualified': capacity, 'test_locked': True})
        if errors:
            raise RuntimeError(str(errors))


def status(folder):
    a, p = read(folder/'admission.json'), read(folder/'progress.json')
    print(datetime.now().astimezone().isoformat(timespec='seconds'))
    print('当前：ASAP7状态／边界；状态：'+p['phase'])
    for split in ('train', 'validation', 'test'):
        counts = Counter()
        for t in a['tasks']:
            if t['split'] != split:
                continue
            path = folder/'runs'/t['id']/'manifest.json'
            m = read(path) if path.exists() else {}
            counts[m.get('status', 'not_started')] += 1
            if m.get('status') == 'running':
                print('任务：', t['id'], '阶段：', m.get('active_stage'))
        print(f'{split}: 完成{counts["completed"]}/{sum(counts.values())}；{dict(counts)}')
    print('容量准入：', p['capacity_qualified'], '；独立测试锁定：', p['test_locked'])
    print('最多4任务×4线程／8GiB；采完108个拟合侧任务后停止，不自动拟合或启动36个test。')
    print('错误：', p['errors'])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'verify', 'run', 'status'))
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--rtl-proof', type=Path)
    args = parser.parse_args()
    folder = args.folder.resolve()
    if args.action == 'prepare':
        if args.rtl_proof is None:
            parser.error('--rtl-proof required for prepare')
        prepare(folder, args.rtl_proof.resolve())
    elif args.action == 'run':
        run(folder)
    elif args.action == 'status':
        status(folder)
    else:
        verify(folder)
        print('verified')


if __name__ == '__main__':
    main()
