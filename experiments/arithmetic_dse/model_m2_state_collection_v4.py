"""State v3 policy with distinct replay logs and preserved support failures."""
import argparse
from pathlib import Path
import shutil
import sys

from . import model_m2_state_collection as base
from . import model_m2_state_collection_v2 as v2
from . import model_m2_state_collection_v3 as v3
from .model_collection import sha, write
from .model_m2_cec import leaf

VERSION = 'asap7-m2-state-fitting-execution-v4'
V3_VERIFY = v3.verify


def verify(folder):
    a = V3_VERIFY(folder)
    if a.get('execution_successor_version') != VERSION:
        raise ValueError('state execution v4 required')
    failed = a['support_predecessor']
    if sha(failed['admission_path']) != failed['admission_sha256']:
        raise ValueError('failed replay admission changed')
    V3_VERIFY(Path(failed['admission_path']).parent)
    for name, h in failed['failed_replay_sha256'].items():
        if sha(Path(failed['admission_path']).parent/name) != h:
            raise ValueError('failed replay support evidence changed')
    return a


def prepare(folder, predecessor, proof):
    stopped = V3_VERIFY(predecessor)
    progress = base.read(predecessor/'progress.json')
    if progress['phase'] != 'stopped_on_error' or progress['active'] or progress['completed']:
        raise ValueError('settled v3 support-only failure required')
    if {x['task_id'] for x in progress['errors']} != set(stopped['capacity_pilots']):
        raise ValueError('unexpected support predecessor tasks')
    hashes = {}
    for tid in stopped['capacity_pilots']:
        directory = predecessor/'runs'/tid
        text = (directory/'raw-replay.log').read_text()
        if 'FileExistsError' not in text or 'raw-replay.log' not in text or 'LIVE_CEC_EXACT_PAIR_VERIFIED' not in text:
            raise ValueError('not the inherited replay log-name collision')
        for path in directory.rglob('*'):
            if path.is_file() and not path.is_symlink():
                hashes[str(path.relative_to(predecessor))] = sha(path)
    data_parent = Path(stopped['predecessor']['admission_path']).parent
    v3.prepare(folder, data_parent, proof)
    a = base.read(folder/'admission.json')
    for path in (Path(v3.__file__).resolve(), Path(__file__).resolve()):
        name = str(path.relative_to(base.ROOT))
        shutil.copy2(path, folder/'source'/name)
        a['sources'][name] = sha(path)
    a.update(execution_successor_version=VERSION,
        support_predecessor={'admission_path': str(predecessor/'admission.json'),
            'admission_sha256': sha(predecessor/'admission.json'), 'failed_replay_sha256': hashes},
        execution_change='distinct raw-replay-v4 leaf logs; no physical or statistical change')
    write(folder/'admission.json', a)
    verify(folder)


def run_task(folder, task):
    a = verify(folder)
    if task['id'] not in a['inherited_paid_raw_runs']:
        return v2.BASE_TASK(folder, task)
    out = folder/'runs'/task['id']
    out.mkdir(parents=True, exist_ok=False)
    ledger = base.StateLedger(folder, task)
    ctx = {'target_platform': 'asap7', 'admission_id': a['id'], 'task_id': task['id']}
    with ledger.job(ctx):
        record = leaf([sys.executable, '-B', '-m', 'experiments.arithmetic_dse.model_m2_state_collection_v4',
            'replay', '--folder', str(folder), '--task', task['id']], out, 'raw-replay-v4', 120, ledger, ctx)
        m = base.read(out/'manifest.json')
        m.update(commands=[record], budget_job_id=ledger.job_id, state_collection_version=VERSION)
        write(out/'manifest.json', m)
    return task['id']


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
        print('verified state execution successor v4')
    else:
        v3.verify, v3.run_task = verify, run_task
        v3.install()
        if args.action == 'replay':
            a = verify(folder)
            v3.paid_ancestry(a['inherited_paid_raw_runs'][args.task]['directory'])
            v2.replay(folder, args.task)
        else:
            v3.run(folder)


if __name__ == '__main__':
    main()
