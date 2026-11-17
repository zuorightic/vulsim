"""Finite hold-buffer guard successor for the one dense G sampling shell."""
import argparse
from copy import deepcopy
import inspect
from pathlib import Path
import shutil
from unittest.mock import patch

from . import nangate45_refit_pin_successor as pins
from . import nangate45_refit_samples as campaign, nangate45_refit_run as worker
from . import nangate45_collect as collect
from .nangate45_samples import read,write,sha


def prepare(root,parent):
    root=Path(root).resolve();parent=Path(parent).resolve();a=pins.verify(parent);p=read(parent/'progress.json')
    failed='G-aca48b1fead906bf-T1425';prior=parent/'runs'/failed
    if root.exists() or root.is_relative_to(campaign.ROOT):raise ValueError('new external root required')
    if p['phase']!='stopped_on_error' or len(p['errors'])!=1 or p['errors'][0]['task']!=failed or len(p['completed'])!=7:
        raise ValueError('only diagnosed pre-validation hold guard failure may continue')
    if any((parent/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train'):raise ValueError('must precede validation')
    log=(prior/'grt.log').read_text()
    if '[ERROR RSZ-0060] Max buffer count reached' not in log or 'Inserted 16687 hold buffers' not in log:
        raise ValueError('hold guard diagnosis differs')
    if (prior/'grt-labels.json').exists():raise ValueError('failure is not a training label')
    root.mkdir();(root/'runs').mkdir()
    for name in ('admission.json','physical-amendment.json','preflight.json','semantic-verification.json',
                 'historical-producer-audit.json','baseline-verification-before-validation.json','implementation-index.json'):
        shutil.copyfile(parent/name,root/name)
    inherited={}
    for name in p['completed']:
        d=parent/'runs'/name;inherited[name]=dict(directory=str(d),label_sha256=sha(d/'grt-labels.json'))
        (root/'runs'/name).symlink_to(d,target_is_directory=True)
    tasks=deepcopy(a['tasks']);t=next(t for t in tasks if t['id']==failed);t['id']=failed+'-H1000'
    t['inherit_synth']=dict(directory=str(prior),files={str(f.relative_to(prior)):sha(f) for f in prior.rglob('*') if f.is_file() and not f.is_symlink()},
        reason='paid synthesis retained; fresh physical run with dense G hold-buffer guard1000%, same core/clock/algorithm')
    write(root/'hold-amendment.json',dict(version='nangate45-N4-hold-guard-amendment-v1',parent=str(parent),
        implementation_sha256=sha(__file__),parent_progress_sha256=sha(parent/'progress.json'),
        admission_sha256=sha(root/'admission.json'),physical_amendment_sha256=sha(root/'physical-amendment.json'),
        source='G-aca48b1fead906bf',max_buffer_percent=1000,previous_max_buffer_percent=100,
        scope='termination guard only; no repair algorithm/clock/source/roles/fit change; 4GiB and1200s caps retained',
        existing_1025_label='completed below original guard; higher inactive guard does not change executed flow',
        inherited=inherited,tasks=tasks,call_caps=dict(synth=30,grt=32,final=0,support=320),
        retained_failed_log=str(prior/'grt.log'),retained_failed_log_sha256=sha(prior/'grt.log'),
        validation_or_test_labels_opened=False))
    write(root/'progress.json',dict(completed=p['completed'],phase='admitted_hold_guard_successor',errors=[]))
    return dict(inherited_labels=7,remaining_points=23,paid_synthesis_reused=1,retained_total_failures=2,hold_amendment_sha256=sha(root/'hold-amendment.json'))


def verify(root):
    root=Path(root);a=pins.verify(root);h=read(root/'hold-amendment.json')
    if (sha(__file__)!=h['implementation_sha256'] or sha(root/'admission.json')!=h['admission_sha256'] or
        sha(root/'physical-amendment.json')!=h['physical_amendment_sha256'] or
        sha(Path(h['parent'])/'progress.json')!=h['parent_progress_sha256']):raise ValueError('hold amendment drift')
    for item in h['inherited'].values():
        if sha(Path(item['directory'])/'grt-labels.json')!=item['label_sha256']:raise ValueError('inherited label drift')
    a['tasks']=h['tasks'];a['call_caps']=h['call_caps']
    a['sampling_layout_overrides'].update(source_repair_max_buffer_percent={h['source']:h['max_buffer_percent']},
        hold_amendment_sha256=sha(root/'hold-amendment.json'))
    return a


def run(root):
    verify(root);text=inspect.getsource(pins.ORIGINAL_TASK_RUN)
    if text.count(pins.LINE)!=1:raise ValueError('worker anchor drift')
    replacement=pins.REPLACEMENT+"\n        if t['source']=='G-aca48b1fead906bf':base+=['VULSIM_REPAIR_MAX_BUFFER_PERCENT=1000']"
    ns=dict(pins.ORIGINAL_TASK_RUN.__globals__);exec(compile(text.replace(pins.LINE,replacement),__file__,'exec'),ns)
    with patch.object(campaign,'verify',verify),patch.object(collect,'task_run',ns['task_run']):return worker.run(root)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path)
    args=p.parse_args();print(prepare(args.root,args.parent) if args.action=='prepare' else run(args.root),flush=True)
