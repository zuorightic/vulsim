"""Queue an existing finite 8 GiB capacity batch before its first paid leaf.

The frozen capacity executor prepares its fresh output before acquiring a job.
This driver waits inside that first acquisition, without restarting run_task,
changing physical recipes, or retrying any attempted job or leaf.
"""
import argparse
from contextlib import contextmanager, ExitStack
from datetime import datetime, timezone
from pathlib import Path
import shutil
import time

from . import workload_capacity as capacity
from .workload_abcd import read, write, sha
from .budget import BudgetExceeded

VERSION = 'nine-workload-capacity-slot-queue-v1'
BaseCapacityLedger = capacity.CapacityLedger


def admit(root, batch):
    folder = root/'capacity'/batch
    a = capacity.verify(root, folder)
    p = read(folder/'progress.json')
    output = folder/'queue-admission.json'
    if (output.exists() or p['status'] != 'admitted' or p['active']
            or p['completed'] or p['errors']
            or a['memory_limit_MiB'] != 8192 or a['threads'] != 4):
        raise ValueError('queue requires an existing unstarted finite 8 GiB capacity batch')
    state = read(BaseCapacityLedger(root, folder, a['tasks'][0]).path)
    if any(e.get('admission_id') == a['id'] for e in state['entries']) or any(
            j['admission_id'] == a['id'] for j in state['jobs']):
        raise ValueError('queue cannot restart an attempted capacity batch')
    if (folder/'runs').exists():
        raise ValueError('preserve prepared or attempted capacity outputs')
    source = Path(__file__)
    shutil.copy2(source, folder/'queue-driver.py')
    q = dict(version=VERSION, capacity_admission_sha256=sha(folder/'admission.json'),
             source=str(source), source_sha256=sha(source),
             created_at=datetime.now(timezone.utc).isoformat(),
             tasks=[t['id'] for t in a['tasks']], added_physical_calls=0,
             automatic_retries=0, application_PPA_feedback=False,
             scope='wait only inside the first job acquisition; frozen capacity run_task is invoked once')
    write(output, q)
    return q


def verify(root, folder):
    a = capacity.verify(root, folder)
    q = read(folder/'queue-admission.json')
    if (q['version'] != VERSION or sha(folder/'admission.json') != q['capacity_admission_sha256']
            or sha(q['source']) != q['source_sha256']
            or sha(folder/'queue-driver.py') != q['source_sha256']
            or q['tasks'] != [t['id'] for t in a['tasks']]):
        raise ValueError('capacity queue identity changed')
    return a


@contextmanager
def wait_for_job(ledger, context, acquire, pause=time.sleep):
    """Retry acquisition only while no previous job or leaf has been claimed."""
    with ExitStack() as stack:
        while True:
            try:
                identity = stack.enter_context(acquire(context))
                break
            except BudgetExceeded as error:
                if str(error) != 'all backend job slots occupied':
                    raise
                state = read(ledger.path)
                same = lambda item: (item.get('admission_id') == context['admission_id']
                                     and item.get('task_id') == context['task_id'])
                if ledger.job_id is not None or any(same(e) for e in state['entries']) or any(
                        same(j) for j in state['jobs']):
                    raise ValueError('slot wait cannot restart an attempted capacity job or leaf')
                pause(2)
        yield identity

class WaitingCapacityLedger(BaseCapacityLedger):
    @contextmanager
    def job(self, context):
        verify(self.root, self.folder)
        with wait_for_job(self, context, super().job) as identity:
            yield identity

    def reserve(self, *args, **kwargs):
        verify(self.root, self.folder)
        return super().reserve(*args, **kwargs)


def run(root, batch):
    folder = root/'capacity'/batch
    verify(root, folder)
    if read(folder/'progress.json')['status'] != 'admitted':
        raise ValueError('queued capacity batch already started')
    # Process-local substitution changes only lease acquisition. Every physical
    # command and stage admission still belongs to the frozen capacity executor.
    original = capacity.CapacityLedger
    capacity.CapacityLedger = WaitingCapacityLedger
    try:
        return capacity.run(root, batch)
    finally:
        capacity.CapacityLedger = original


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('admit', 'run'))
    p.add_argument('--root', type=Path, required=True)
    p.add_argument('--batch', required=True)
    args = p.parse_args()
    root = args.root.resolve()
    print(admit(root, args.batch) if args.action == 'admit' else run(root, args.batch))
