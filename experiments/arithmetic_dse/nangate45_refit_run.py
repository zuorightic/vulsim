"""One isolated worker; freeze fitted parameters before collecting fresh test."""
import argparse
import fcntl
from pathlib import Path
import time
from unittest.mock import patch

from . import nangate45_refit_samples as campaign, nangate45_refit_fit as fitting
from . import nangate45_collect as collect, nangate45_samples as original
from .nangate45_samples import read,write,sha


def run(root):
    root=Path(root).resolve();a=campaign.verify(root);progress=read(root/'progress.json')
    if progress['errors']:raise ValueError('retained error requires explicit diagnosis, no automatic retry')
    lock=(root/'worker.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    try:
        with patch.object(original,'verify',campaign.verify),patch.object(original,'VERSION',campaign.VERSION):
            for role in ('train','validation','test'):
                if role=='test':
                    if not (root/'frozen-model.json').exists():
                        progress['phase']='fitting';write(root/'progress.json',progress)
                        print(fitting.freeze(root),flush=True)
                    seal=read(root/'model-freeze.json')
                    if sha(root/'frozen-model.json')!=seal['model_sha256']:raise ValueError('real model freeze required')
                for t in a['tasks']:
                    if t['role']!=role or t['id'] in progress['completed']:continue
                    if (root/'runs'/t['id']).exists():raise ValueError('earlier attempt retained; no automatic retry')
                    while True:
                        available=int(next(l.split()[1] for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:')))//1024
                        if available>=a['minimum_available_MiB']:break
                        progress.update(phase='waiting_memory',available_MiB=available,next_task=t['id']);write(root/'progress.json',progress)
                        time.sleep(20)
                    progress.update(phase='collecting_'+role,next_task=t['id']);write(root/'progress.json',progress)
                    collect.task_run(root,t);progress['completed'].append(t['id']);write(root/'progress.json',progress)
            if not (root/'evaluation.json').exists():fitting.evaluate(root)
            progress.update(phase='evaluated',next_task=None);write(root/'progress.json',progress)
    except Exception as e:
        progress['phase']='stopped_on_error';progress['errors'].append(dict(task=progress.get('next_task'),error=str(e)))
        write(root/'progress.json',progress);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','run'));parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();print(campaign.prepare(args.root) if args.action=='prepare' else run(args.root),flush=True)
