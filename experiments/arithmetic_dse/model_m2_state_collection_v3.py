"""State successor with strict singleton-port naming and saved-map continuation."""
import argparse
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import copy
import fcntl
import json
from pathlib import Path
import re
import shutil
import sys
import types

from . import model_m2_state_collection as base
from . import model_m2_state_collection_v2 as v2
from . import sdc
from .budget import Ledger
from .model_collection import sha, write
from .model_m2_cec import leaf

ROOT = base.ROOT
VERSION = 'asap7-m2-state-fitting-successor-v3'
ORIGINAL_PORTS = sdc.rtl_ports


def rtl_ports(text, top=None):
    """Yosys scalarizes [0:0]; never collapse bit zero of a wider vector."""
    result = ORIGINAL_PORTS(text, top)
    for direction in ('inputs', 'outputs'):
        names = result[direction]
        vector = {}
        for name in names:
            match = re.fullmatch(r'(.+)\[([0-9]+)\]', name)
            if match:
                vector.setdefault(match[1], []).append(int(match[2]))
        rewritten = [name[:-3] if name.endswith('[0]') and vector[name[:-3]] == [0] else name for name in names]
        if len(set(rewritten)) != len(names):
            raise ValueError('ambiguous scalar/singleton-vector port identity')
        result[direction] = sorted(rewritten)
    return result


def install():
    from . import backend
    sdc.rtl_ports = backend.rtl_ports = rtl_ports
    base.verify = v2.verify = verify
    base.state_witness = v2.state_witness
    base.seed_mapping = seed_mapping


def verify(folder):
    a = v2.BASE_VERIFY(folder)
    if a.get('successor_version') != VERSION:
        raise ValueError('state v3 admission required')
    parent = a['predecessor']
    if sha(parent['admission_path']) != parent['admission_sha256']:
        raise ValueError('state v2 predecessor changed')
    # Invoke the v2 verifier with its original globals, not the runtime hook.
    namespace = dict(V2_VERIFY.__globals__)
    namespace['BASE_VERIFY'] = v2.BASE_VERIFY
    types.FunctionType(V2_VERIFY.__code__, namespace)(Path(parent['admission_path']).parent)
    for ref in [*a['inherited_paid_raw_runs'].values(), *a['synthesis_resume'].values()]:
        if sha(Path(ref['directory'])/'manifest.json') != ref['manifest_sha256']:
            raise ValueError('saved state source manifest changed')
    return a


V2_VERIFY = v2.verify


def paid_ancestry(directory, seen=None):
    seen = set() if seen is None else seen
    directory = Path(directory)
    if str(directory) in seen:
        raise ValueError('cyclic state physical ancestry')
    seen.add(str(directory))
    m = base.read(directory/'manifest.json')
    entries = {e['id']: e for e in base.read(Ledger().path)['entries']}
    owner = sha(directory.parent.parent/'admission.json')
    commands = list(m['commands'])
    for c in commands:
        e = entries[c['budget_reservation_id']]
        if (e['status'] != 'completed' or e['command'] != c['command']
            or e.get('admission_sha256') != owner or c['exit_code']
            or c['cleanup']['remaining_live_pids']):
            raise ValueError('unpaid or mismatched saved state command')
    for name, h in m.get('evidence_sha256', {}).items():
        if sha(directory/name) != h:
            raise ValueError('changed saved state raw report: '+name)
    inherited = m.get('inherited_raw_run')
    if inherited:
        if sha(Path(inherited['directory'])/'manifest.json') != inherited['manifest_sha256']:
            raise ValueError('changed state physical ancestor')
        commands += paid_ancestry(inherited['directory'], seen)
    return commands


def prepare(folder, predecessor, proof):
    old = V2_VERIFY(predecessor)
    progress = base.read(predecessor/'progress.json')
    if progress['phase'] != 'stopped_on_error' or progress['active']:
        raise ValueError('settled v2 parser stop required')
    tid = 'state-train-small-w1-t0'
    if progress['errors'] != [{'task_id': tid, 'reason': tid+': initial synthesis failed: SDC IO coverage mismatch (includes reset/valid/data)'}]:
        raise ValueError('unexpected predecessor failure')
    inherited = {}
    for completed in progress['completed']:
        directory = predecessor/'runs'/completed
        paid_ancestry(directory)
        m = base.read(directory/'manifest.json')
        if m['status'] != 'completed':
            raise ValueError('inherited state run not complete')
        inherited[completed] = {'directory': str(directory), 'manifest_sha256': sha(directory/'manifest.json'),
                                 'role': 'same registered train source; completed paid evidence'}
    raw = predecessor/'runs'/tid
    m = base.read(raw/'manifest.json')
    paid_ancestry(raw)
    if len(m['commands']) != 2 or m['failure_reason'] != 'SDC IO coverage mismatch (includes reset/valid/data)':
        raise ValueError('not an exact completed-synthesis checkpoint')
    ports = rtl_ports((raw/'input.sv').read_text(), 'ModelBundle')
    from .platforms import profile
    sdc.verify_sdc((raw/'results'/base.SUFFIX/'1_synth.sdc').read_text(), profile('asap7'), 40500, ports)
    base.prepare(folder, proof)
    a = base.read(folder/'admission.json')
    for path in (Path(v2.__file__).resolve(), Path(__file__).resolve()):
        name = str(path.relative_to(ROOT))
        shutil.copy2(path, folder/'source'/name)
        a['sources'][name] = sha(path)
    a.update(successor_version=VERSION,
             predecessor={'admission_path': str(predecessor/'admission.json'), 'admission_sha256': sha(predecessor/'admission.json')},
             inherited_paid_raw_runs=inherited,
             synthesis_resume={tid: {'directory': str(raw), 'manifest_sha256': sha(raw/'manifest.json'),
                                      'mapped_netlist_sha256': sha(raw/'results'/base.SUFFIX/'1_2_yosys.v')}},
             successor_change='SDC singleton [0:0] naming only; completed raw replay and exact saved synthesis mapping',
             inherited_complete_physical_relaunch=False)
    for t in a['tasks']:
        if t['id'] == tid:
            t['mapping_source_task'] = tid
            t['mapping_role'] = 'explicit saved t0 synthesis continuation; fresh SDC/ODB, no ABC rerun'
    write(folder/'admission.json', a)
    verify(folder)


def seed_mapping(folder, task, out):
    a = verify(folder)
    tid = task['mapping_source_task']
    ref = a['synthesis_resume'].get(tid) or a['inherited_paid_raw_runs'].get(tid)
    if ref is None:
        return v2.BASE_SEED(folder, task, out)
    raw = Path(ref['directory'])
    commands = paid_ancestry(raw)
    m = copy.deepcopy(base.read(raw/'manifest.json'))
    # Imported manifests name a replay support leaf. Resolve the actual
    # physical ancestor so every make/config path is rebased from that run.
    while m.get('inherited_raw_run'):
        raw = Path(m['inherited_raw_run']['directory'])
        m = copy.deepcopy(base.read(raw/'manifest.json'))
    m.update(status='completed')
    m.pop('failure_reason', None)
    m.pop('failure_stage', None)
    net = raw/'results'/base.SUFFIX/'1_2_yosys.v'
    if 'mapped_netlist_sha256' in ref and sha(net) != ref['mapped_netlist_sha256']:
        raise ValueError('saved synthesis mapping changed')
    m.setdefault('evidence_sha256', {})[str(net.relative_to(raw))] = sha(net)
    namespace = dict(v2.BASE_SEED.__globals__)
    namespace['read'] = lambda path: m if Path(path) == raw/'manifest.json' else base.read(path)
    return types.FunctionType(v2.BASE_SEED.__code__, namespace)(raw.parent.parent, task, out)


def run_task(folder, task):
    a = verify(folder)
    if task['id'] not in a['inherited_paid_raw_runs']:
        return v2.BASE_TASK(folder, task)
    out = folder/'runs'/task['id']
    out.mkdir(parents=True, exist_ok=False)
    ledger = base.StateLedger(folder, task)
    ctx = {'target_platform': 'asap7', 'admission_id': a['id'], 'task_id': task['id']}
    with ledger.job(ctx):
        record = leaf([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_m2_state_collection_v3',
            'replay', '--folder', str(folder), '--task', task['id']], out, 'raw-replay', 120, ledger, ctx)
        m = base.read(out/'manifest.json')
        m.update(commands=[record], budget_job_id=ledger.job_id, state_collection_version=VERSION)
        write(out/'manifest.json', m)
    return task['id']


def seal_capacity(folder, a):
    rows = []
    for tid in a['capacity_pilots']:
        directory = folder/'runs'/tid
        m = base.read(directory/'manifest.json')
        if m['status'] != 'completed' or len(m['metrics']) != 2:
            raise ValueError('state capacity replay incomplete')
        cells = base.read(directory/'liberty_cells.json')['cells']
        for g in m['metrics']:
            if v2.state_witness(directory, g['stage'], cells) != g['state_witness']:
                raise ValueError('state capacity witness changed')
        cmds = paid_ancestry(m['inherited_raw_run']['directory'])+m['commands']
        rows.append({'task_id': tid, 'manifest_sha256': sha(directory/'manifest.json'),
            'actual_register_bits': m['metrics'][-1]['state_witness']['actual_register_bits'],
            'peak_RSS_MiB': max(c['sampled_process_tree_peak_rss_KiB'] for c in cmds)/1024,
            'physical_reexecuted': False})
    base.exclusive(folder/'capacity-proof.json', {'status': 'passed', 'version': VERSION,
        'admission_sha256': sha(folder/'admission.json'), 'runs': rows,
        'scope': 'registered fitting geometries; independent capacity and stage combination remain gated'})


def run(folder):
    a = verify(folder)
    indexed = {t['id']: t for t in a['tasks'] if t['split'] != 'test'}
    with (folder/'advance.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
        if any((folder/'runs'/tid).exists() for tid in indexed):
            raise ValueError('preserve state attempts; explicit successor required')
        waiting = list(indexed)
        active, completed, errors, capacity = {}, [], [], False
        with ThreadPoolExecutor(max_workers=4) as pool:
            while waiting or active:
                if not capacity and set(a['capacity_pilots']) <= set(completed):
                    seal_capacity(folder, a)
                    capacity = True
                while waiting and len(active) < 4 and not errors:
                    ready = next((tid for tid in waiting if
                        (capacity or tid in a['capacity_pilots']) and
                        (tid in a['inherited_paid_raw_runs'] or tid in a['synthesis_resume'] or
                         not indexed[tid]['mapping_source_task'] or indexed[tid]['mapping_source_task'] in completed)), None)
                    if ready is None:
                        break
                    waiting.remove(ready)
                    active[pool.submit(run_task, folder, indexed[ready])] = ready
                write(folder/'progress.json', {'phase': 'fitting_collecting', 'active': list(active.values()),
                    'waiting': waiting, 'completed': completed, 'errors': errors,
                    'capacity_qualified': capacity, 'test_locked': True})
                if not active:
                    if waiting and not errors:
                        raise ValueError('state dependency deadlock')
                    break
                done, _ = wait(active, timeout=1, return_when=FIRST_COMPLETED)
                for future in done:
                    tid = active.pop(future)
                    try:
                        completed.append(future.result())
                    except Exception as e:
                        errors.append({'task_id': tid, 'reason': str(e)})
        write(folder/'progress.json', {'phase': 'stopped_on_error' if errors else 'fitting_collection_complete',
            'active': [], 'waiting': waiting, 'completed': completed, 'errors': errors,
            'capacity_qualified': capacity, 'test_locked': True})
        if errors:
            raise RuntimeError(str(errors))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('prepare', 'run', 'status', 'verify', 'replay'))
    parser.add_argument('--folder', type=Path, required=True)
    parser.add_argument('--predecessor', type=Path)
    parser.add_argument('--rtl-proof', type=Path)
    parser.add_argument('--task')
    args = parser.parse_args()
    folder = args.folder.resolve()
    if args.action == 'prepare':
        if args.predecessor is None or args.rtl_proof is None:
            parser.error('prepare requires predecessor and RTL proof')
        prepare(folder, args.predecessor.resolve(), args.rtl_proof.resolve())
    elif args.action == 'status':
        base.status(folder)
    elif args.action == 'verify':
        verify(folder)
        print('verified state successor v3')
    else:
        install()
        if args.action == 'replay':
            a = verify(folder)
            paid_ancestry(a['inherited_paid_raw_runs'][args.task]['directory'])
            v2.replay(folder, args.task)
        else:
            run(folder)


if __name__ == '__main__':
    main()
