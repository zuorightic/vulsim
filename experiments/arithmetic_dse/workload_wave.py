"""Finish unattempted frozen measurements, waiting for a Ledger slot atomically.

The v1 wave's free-slot observation could race a different admitted batch.
Only an unclaimed task with no physical output or reserved leaf may wait and
try to acquire a slot again. Tool failures remain settled, explicit failures.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
import shutil
import time

from .workload_abcd import read, write, sha
from .workload_backend_finish import verify, run_task
from .budget import Ledger, BudgetExceeded

VERSION = 'nine-workload-unattempted-wave-v2'


def wait_task(root, task, pause=time.sleep):
    while True:
        try:
            return run_task(root, task)
        except BudgetExceeded as error:
            if str(error) != 'all backend job slots occupied':
                raise
            _, parent = verify(root)
            state = read(Ledger().path)
            if ((root/'runs'/task['id']).exists()
                    or any(e.get('admission_id') == parent['id']
                           and e.get('task_id') == task['id'] for e in state['entries'])
                    or any(j['admission_id'] == parent['id']
                           and j['task_id'] == task['id'] for j in state['jobs'])):
                raise ValueError('slot wait cannot restart an attempted physical task')
            pause(2)


def admit(root, name, cases):
    _, parent = verify(root)
    directory = root/'waves'/name
    if directory.exists() or not cases:
        raise ValueError('fresh finite wave and named cases required')
    declared = {a['case'] for t in parent['tasks'] for a in t['attribution']}
    if set(cases) - declared:
        raise ValueError('case absent from frozen matrix')
    state = read(Ledger().path)
    claimed = {j['task_id'] for j in state['jobs'] if j['admission_id'] == parent['id']}
    tasks = [t for t in parent['tasks']
             if any(a['case'] in cases for a in t['attribution'])
             and not (root/'runs'/t['id']).exists() and t['id'] not in claimed]
    if not tasks:
        raise ValueError('no unattempted measurements in wave')
    directory.mkdir(parents=True)
    source = Path(__file__)
    shutil.copy2(source, directory/'driver.py')
    a = dict(version=VERSION, created_at=datetime.now(timezone.utc).isoformat(),
             tasks=tasks, cases=cases, source=str(source), source_sha256=sha(source),
             parent_admission_sha256=sha(root/'admission.json'),
             selection_freeze_sha256=parent['selection_freeze_sha256'],
             automatic_retries=0, selection_feedback=False,
             scope='original finite physical admission; slot waits only before job acquisition')
    write(directory/'admission.json', a)
    write(directory/'progress.json', dict(status='admitted', completed=[], errors=[], active=[]))
    return dict(tasks=len(tasks), ids=[t['id'] for t in tasks])


def run(root, name):
    _, parent = verify(root)
    directory = root/'waves'/name
    a = read(directory/'admission.json')
    if (a['version'] != VERSION or sha(root/'admission.json') != a['parent_admission_sha256']
            or sha(a['source']) != a['source_sha256']
            or sha(directory/'driver.py') != a['source_sha256']):
        raise ValueError('wave identity changed')
    progress = read(directory/'progress.json')
    if progress['active']:
        raise ValueError('wave is already active')
    attempted = set(progress['completed']) | {e['task'] for e in progress['errors']}
    tasks = [t for t in a['tasks'] if t['id'] not in attempted]
    if any((root/'runs'/t['id']).exists() for t in tasks):
        raise ValueError('wave task attempted elsewhere')
    progress.update(status='running', active=[t['id'] for t in tasks])
    write(directory/'progress.json', progress)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(wait_task, root, t): t for t in tasks}
        for future in as_completed(futures):
            t = futures[future]
            try:
                future.result()
                progress['completed'].append(t['id'])
                print('COMPLETED '+t['id'], flush=True)
            except Exception as error:
                progress['errors'].append(dict(task=t['id'], reason=str(error)))
                print('FAILED '+t['id']+': '+str(error), flush=True)
            progress['active'].remove(t['id'])
            write(directory/'progress.json', progress)
    progress['status'] = 'batch_settled'
    write(directory/'progress.json', progress)
    return progress


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('admit', 'run'))
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--wave', required=True)
    p.add_argument('--case', action='append')
    args = p.parse_args()
    root = args.root.resolve()
    print(admit(root, args.wave, args.case) if args.action == 'admit' else run(root, args.wave))
