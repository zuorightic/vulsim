"""Queue a frozen exact-pair CTS continuation without restarting its body."""
import argparse
from contextlib import contextmanager
from datetime import datetime,timezone
from pathlib import Path
import shutil

from . import workload_resume as resume
from .workload_abcd import read,write,sha
from .workload_capacity_queue import wait_for_job

VERSION='nine-workload-resume-slot-queue-v1'
BaseResumeLedger=resume.ResumeLedger


def admit(root,batch):
    folder=root/'capacity'/batch;a=resume.verify(root,folder)
    progress=read(folder/'progress.json')
    if ((folder/'queue-admission.json').exists() or (folder/'runs').exists()
            or progress['status']!='admitted' or progress['active']
            or progress['completed'] or progress['errors']):
        raise ValueError('queue requires a fresh unstarted exact-pair continuation')
    state=read(BaseResumeLedger(root,folder).path)
    if any(e.get('admission_id')==a['id'] for e in state['entries']) or any(
            j['admission_id']==a['id'] for j in state['jobs']):
        raise ValueError('queue cannot restart an attempted continuation')
    source=Path(__file__);shutil.copy2(source,folder/'queue-driver.py')
    q=dict(version=VERSION,capacity_admission_sha256=sha(folder/'admission.json'),
           source=str(source),source_sha256=sha(source),
           created_at=datetime.now(timezone.utc).isoformat(),tasks=[t['id'] for t in a['tasks']],
           added_physical_calls=0,automatic_retries=0,application_PPA_feedback=False,
           scope='wait inside first job acquisition of one frozen CTS continuation invocation')
    write(folder/'queue-admission.json',q);verify(root,folder);return q


def verify(root,folder):
    a=resume.verify(root,folder);q=read(folder/'queue-admission.json')
    if (q['version']!=VERSION or sha(folder/'admission.json')!=q['capacity_admission_sha256']
            or sha(q['source'])!=q['source_sha256'] or sha(folder/'queue-driver.py')!=q['source_sha256']
            or q['tasks']!=[t['id'] for t in a['tasks']]
            or a['memory_limit_MiB']!=8192 or a['threads']!=4 or a['grt_timeout_s']!=3600):
        raise ValueError('CTS continuation queue source or admitted resources changed')
    return a


class WaitingResumeLedger(BaseResumeLedger):
    @contextmanager
    def job(self,context):
        verify(self.root,self.folder)
        with wait_for_job(self,context,super().job) as identity:yield identity

    def reserve(self,*args,**kwargs):
        verify(self.root,self.folder)
        return super().reserve(*args,**kwargs)


def run(root,batch):
    folder=root/'capacity'/batch;verify(root,folder)
    if read(folder/'progress.json')['status']!='admitted':raise ValueError('continuation already started')
    original=resume.ResumeLedger;resume.ResumeLedger=WaitingResumeLedger
    try:return resume.run(root,batch)
    finally:resume.ResumeLedger=original


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True)
    args=p.parse_args();root=args.root.resolve()
    print(admit(root,args.batch) if args.action=='admit' else run(root,args.batch))
