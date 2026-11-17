"""Diagnosed PPL-0024 successor: retain paid labels/synth, enlarge one G shell.

The original admission is byte identical. A separately hashed prospective
physical amendment changes one source's core floor and the failed task ID.
It never changes sources, clocks, roles, fitting or the frozen D algorithm.
"""
import argparse
from copy import deepcopy
import inspect
from pathlib import Path
import shutil
from unittest.mock import patch

from . import nangate45_refit_samples as campaign, nangate45_refit_run as worker
from . import nangate45_collect as collect
from .nangate45_samples import read,write,sha

BASE_VERIFY=campaign.verify
ORIGINAL_TASK_RUN=collect.task_run
LINE="side=max(60,math.ceil(math.sqrt(m['metrics'][0]['cell_area_um2']/.4)))"
REPLACEMENT="side=max(360 if t['source']=='G-aca48b1fead906bf' else 60,math.ceil(math.sqrt(m['metrics'][0]['cell_area_um2']/.4)))"


def prepare(root,parent):
    root=Path(root).resolve();parent=Path(parent).resolve();a=BASE_VERIFY(parent);p=read(parent/'progress.json')
    failed='G-aca48b1fead906bf-T1025';prior=parent/'runs'/failed
    if root.exists() or root.is_relative_to(campaign.ROOT):raise ValueError('new external root required')
    if (p['phase']!='stopped_on_error' or len(p['errors'])!=1 or p['errors'][0]['task']!=failed or
        len(p['completed'])!=6 or any((parent/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train')):
        raise ValueError('only diagnosed pre-validation pin failure may continue')
    if '[ERROR PPL-0024] Number of IO pins (2309)' not in (prior/'grt.log').read_text():raise ValueError('pin capacity diagnosis differs')
    if (prior/'grt-labels.json').exists():raise ValueError('failed point cannot be a label')
    root.mkdir();shutil.copyfile(parent/'admission.json',root/'admission.json');(root/'runs').mkdir()
    inherited={}
    for name in p['completed']:
        d=parent/'runs'/name
        inherited[name]=dict(directory=str(d),label_sha256=sha(d/'grt-labels.json'),status_sha256=sha(d/'collection-status.json'))
        (root/'runs'/name).symlink_to(d,target_is_directory=True)
    tasks=deepcopy(a['tasks']);t=next(t for t in tasks if t['id']==failed);t['id']=failed+'-IO360'
    t['inherit_synth']=dict(directory=str(prior),files={str(f.relative_to(prior)):sha(f) for f in prior.rglob('*') if f.is_file() and not f.is_symlink()},
        reason='paid synthesis checkpoint retained; fresh placement with core>=360um for 2309 IO pins')
    text=inspect.getsource(ORIGINAL_TASK_RUN)
    if text.count(LINE)!=1:raise ValueError('worker amendment anchor changed')
    amendment=dict(version='nangate45-N4-pin-capacity-amendment-v1',parent=str(parent),admission_sha256=sha(root/'admission.json'),
        implementation_sha256=sha(__file__),parent_progress_sha256=sha(parent/'progress.json'),
        reason='PPL-0024: 2309 IO exceeds 2048 positions; required die perimeter1293.04um vs1156um',
        source='G-aca48b1fead906bf',minimum_core_side_um=360,all_three_requests_same_floor=True,
        source_role_clock_and_fit_unchanged=True,validation_or_test_labels_opened=False,
        inherited=inherited,tasks=tasks,call_caps=dict(synth=30,grt=31,final=0,support=310),
        retained_failed_call=dict(stage='grt',task=failed,log=str(prior/'grt.log'),log_sha256=sha(prior/'grt.log')),
        original_worker_sha256=sha(collect.__file__),exact_worker_line_before=LINE,exact_worker_line_after=REPLACEMENT)
    write(root/'physical-amendment.json',amendment)
    write(root/'progress.json',dict(completed=p['completed'],phase='admitted_physical_successor',errors=[]))
    for name in ('preflight.json','semantic-verification.json','historical-producer-audit.json','baseline-verification-before-validation.json','implementation-index.json'):
        shutil.copyfile(parent/name,root/name)
    return dict(inherited_labels=6,new_physical_points=24,paid_synthesis_reused=1,retained_failures=1,amendment_sha256=sha(root/'physical-amendment.json'))


def verify(root):
    root=Path(root);a=BASE_VERIFY(root);amend=read(root/'physical-amendment.json')
    if amend['admission_sha256']!=sha(root/'admission.json') or amend['implementation_sha256']!=sha(__file__):raise ValueError('physical amendment drift')
    if sha(Path(amend['parent'])/'progress.json')!=amend['parent_progress_sha256']:raise ValueError('retained parent progress changed')
    for name,item in amend['inherited'].items():
        d=Path(item['directory'])
        if sha(d/'grt-labels.json')!=item['label_sha256'] or sha(d/'collection-status.json')!=item['status_sha256']:
            raise ValueError('retained valid label changed')
    a['tasks']=amend['tasks'];a['call_caps']=amend['call_caps']
    a['sampling_layout_overrides']=dict(a['sampling_layout_overrides'],
        source_core_floor_um={amend['source']:360},physical_amendment_sha256=sha(root/'physical-amendment.json'))
    return a


def run(root):
    verify(root);text=inspect.getsource(ORIGINAL_TASK_RUN)
    if text.count(LINE)!=1:raise ValueError('unexpected source worker')
    ns=dict(ORIGINAL_TASK_RUN.__globals__);exec(compile(text.replace(LINE,REPLACEMENT),__file__,'exec'),ns)
    with patch.object(campaign,'verify',verify),patch.object(collect,'task_run',ns['task_run']):
        return worker.run(root)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path)
    args=p.parse_args();print(prepare(args.root,args.parent) if args.action=='prepare' else run(args.root),flush=True)
