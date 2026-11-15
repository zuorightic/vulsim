"""Dispatch an explicitly named, frozen evaluation wave into free Ledger jobs.

Waves organize physical resources only. They never filter or rerank the frozen
candidate set, and never retry an attempted measurement. Other admitted jobs
may continue concurrently; their whole-job leases reserve the same four slots.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,wait,FIRST_COMPLETED
from datetime import datetime,timezone
from pathlib import Path
import shutil
import time

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify,run_task
from .budget import Ledger

VERSION='nine-workload-finite-evaluation-wave-v1'


def admit(root,name,cases):
    _,parent=verify(root);directory=root/'waves'/name
    if directory.exists() or not cases:raise ValueError('new named finite evaluation wave required')
    declared={a['case'] for t in parent['tasks'] for a in t['attribution']}
    if set(cases)-declared:raise ValueError('case absent from the frozen matrix')
    tasks=[t for t in parent['tasks'] if any(a['case'] in cases for a in t['attribution'])
           and not (root/'runs'/t['id']).exists()]
    directory.mkdir(parents=True)
    source=Path(__file__);saved=directory/'driver.py';shutil.copy2(source,saved)
    a=dict(version=VERSION,created_at=datetime.now(timezone.utc).isoformat(),cases=cases,
           tasks=tasks,parent_admission_sha256=sha(root/'admission.json'),
           source_sha256=sha(source),source=str(source),automatic_retries=0,
           capacity_scope='explicit case wave; original 300s synth/1200s grt/8192MiB, no resource override',
           selection_feedback=False,selection_freeze_sha256=parent['selection_freeze_sha256'])
    write(directory/'admission.json',a)
    write(directory/'progress.json',dict(status='admitted',completed=[],errors=[],active=[],queued=[t['id'] for t in tasks]))
    return a


def run(root,name):
    _,parent=verify(root);directory=root/'waves'/name;a=read(directory/'admission.json')
    if (a['version']!=VERSION or sha(root/'admission.json')!=a['parent_admission_sha256']
            or sha(a['source'])!=a['source_sha256'] or sha(directory/'driver.py')!=a['source_sha256']):
        raise ValueError('evaluation wave identity changed')
    progress=read(directory/'progress.json')
    if progress['active']:raise ValueError('unsettled wave jobs')
    attempted=set(progress['completed'])|{e['task'] for e in progress['errors']}
    queue=[t for t in a['tasks'] if t['id'] not in attempted]
    if any((root/'runs'/t['id']).exists() for t in queue):raise ValueError('wave task already attempted elsewhere')
    ledger=Ledger();inflight={};progress['status']='running'
    with ThreadPoolExecutor(max_workers=4) as pool:
        while queue or inflight:
            jobs=[j for j in read(ledger.path)['jobs'] if j['status']=='active']
            live_primary={j['task_id'] for j in jobs if j['admission_id']==parent['id']}
            submitted_unleased=sum(t['id'] not in live_primary for t in inflight.values())
            free=max(0,min(4-len(jobs)-submitted_unleased,4-len(inflight)))
            for _ in range(min(free,len(queue))):
                task=queue.pop(0);inflight[pool.submit(run_task,root,task)]=task
            progress.update(active=[t['id'] for t in inflight.values()],queued=[t['id'] for t in queue],
                            other_live_jobs=len(jobs)-sum(t['id'] in live_primary for t in inflight.values()))
            write(directory/'progress.json',progress)
            if not inflight:time.sleep(2);continue
            done,_=wait(inflight,timeout=2,return_when=FIRST_COMPLETED)
            for future in done:
                task=inflight.pop(future)
                try:future.result();progress['completed'].append(task['id'])
                except Exception as e:progress['errors'].append(dict(task=task['id'],reason=str(e)))
            if done:
                progress['active']=[t['id'] for t in inflight.values()];write(directory/'progress.json',progress)
    progress.update(status='batch_settled',active=[],queued=[]);write(directory/'progress.json',progress)
    return progress


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--wave',required=True);p.add_argument('--case',action='append')
    a=p.parse_args();root=a.root.resolve();print(admit(root,a.wave,a.case) if a.action=='admit' else run(root,a.wave))
