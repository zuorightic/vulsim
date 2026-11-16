"""User-authorized fourth physical worker for already frozen tasks.

The original three-worker controller and its sources stay unchanged. The
global ledger's atomic, permanent task claims prevent duplicate EDA leaves.
Later duplicate dispatch rejections by that controller are retained as
coordination events, separately from real measurement failures.
"""
import argparse
import fcntl
import os
from pathlib import Path
import subprocess
import sys
import time

from .workload_abcd import read,write,sha
from .workload_tight_run import DEFAULT
from . import workload_final_backend as physical
from .budget import Ledger,POLICY


def candidate(root):
    state=read(Ledger().path)
    if len([j for j in state['jobs'] if j['status']=='active'])>=4:return None
    claimed={(j['admission_id'],j['task_id']) for j in state['jobs']}
    # Start at the far end of the existing queue to minimize dispatch races.
    for cid in ('karatsuba256','barrett64','horner64','mul128','ntt8x64','dot16','montgomery256'):
        batch=root/('final-'+cid)
        if not (batch/'admission.json').exists():continue
        a=physical.verify(batch)
        for task in a['tasks']:
            if ((a['id'],task['id']) not in claimed and
                    not (batch/'runs'/task['id']).exists()):return batch,task
    return None


def reconcile(root):
    """Annotate retained duplicate rejections; never erase original errors."""
    state=read(Ledger().path);active={j['admission_id'] for j in state['jobs'] if j['status'] in ('active','unsettled')}
    rows=[]
    for p in (root/'fourth-worker-transfers').glob('*.json'):
        receipt=read(p);batch=Path(receipt['batch']);a=read(batch/'admission.json')
        if receipt['status']!='measured_grt' or a['id'] in active:continue
        progress=read(batch/'progress.json')
        if progress['status']!='batch_settled':continue
        errors=[e for e in progress['errors'] if e['task']==receipt['task_id']]
        for error in errors:
            log=batch/'dispatch-logs'/(receipt['task_id']+'.log')
            text=log.read_text() if log.exists() else ''
            if 'backend task already claimed; no automatic retry' not in text:
                raise ValueError('transferred task has an unexpected later dispatch failure')
            rows.append(dict(batch=str(batch),task_id=receipt['task_id'],
                classification='duplicate_dispatch_rejected_after_transfer',original_progress_error=error,
                dispatch_log_sha256=sha(log),successful_transfer_receipt_sha256=sha(p),
                actual_measurement_failure=False,original_error_retained=True))
    write(root/'fourth-worker-reconciliation.json',dict(rows=rows,errors_erased=False,EDA_retries=0))


def run(root):
    root=Path(root).resolve();folder=root/'fourth-worker-transfers';folder.mkdir(exist_ok=True)
    with (root/'fourth-worker.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        source=Path(__file__).resolve();record=root/'concurrency-amendment.json'
        value=dict(version='tight-four-physical-workers-v1',old_dispatch_workers=3,new_global_workers=4,
            threads_per_tool=4,memory_limit_MiB=8192,global_policy_sha256=sha(POLICY),
            user_authorization='可不可以4并行每个4线程，如果并行数比这个效率还高，你就不用改',
            source=str(source),source_sha256=sha(source),original_frozen_sources_modified=False,
            model_or_selection_changed=False,task_claims='same append-only ledger; atomic once-only identity',
            duplicate_dispatch_is_not_a_tool_failure=True)
        if record.exists() and read(record)!=value:raise ValueError('concurrency amendment changed')
        if not record.exists():write(record,value)
        while True:
            reconcile(root)
            result=read(root/'comparison.json')
            if result['physical_comparison_complete']:break
            chosen=candidate(root)
            if chosen is None:time.sleep(10);continue
            batch,task=chosen;a=physical.verify(batch)
            receipt=folder/(batch.name+'__'+task['id']+'.json')
            if receipt.exists():raise ValueError('fourth worker refuses a repeated transfer')
            command=[sys.executable,'-m','experiments.arithmetic_dse.workload_tight_continue',
                'task','--root',str(batch),'--task-id',task['id']]
            row=dict(batch=str(batch),task_id=task['id'],admission_sha256=sha(batch/'admission.json'),
                amendment_sha256=sha(record),command=command,status='dispatching',worker_pid=os.getpid(),
                started_epoch=time.time(),period_ps=task['period_ps'],rtl_sha256=task['rtl_sha256'])
            write(receipt,row);log=receipt.with_suffix('.log')
            print('FOURTH_START '+task['id'],flush=True)
            with log.open('w') as stream:
                child=subprocess.run(command,cwd=Path(__file__).resolve().parents[2],stdout=stream,stderr=subprocess.STDOUT)
            clock=batch/'runs'/task['id']/'clock-readout/result.json'
            row.update(status='measured_grt' if child.returncode==0 else 'dispatch_rejected_or_failed',
                exit_code=child.returncode,finished_epoch=time.time(),log_sha256=sha(log))
            if child.returncode==0:
                if not clock.exists():raise ValueError('fourth worker returned without complete clock evidence')
                row['clock_readout_sha256']=sha(clock)
            write(receipt,row);print('FOURTH_DONE '+task['id']+' '+row['status'],flush=True)
        reconcile(root)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=DEFAULT);a=p.parse_args();run(a.root)
