"""Pre-validation source amendment: bounded overlapping G replaces huge shell.

All physical failures and the one eligible large-G diagnostic remain external.
Only the original twelve intended training points enter the recalibration.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
from unittest.mock import patch

from . import nangate45_refit_samples as campaign,nangate45_refit_run as worker
from . import nangate45_collect as collect
from . import nangate45_refit_pin_successor as pins,nangate45_refit_hold_successor as holds
from .nangate45_samples import read,write,sha


def prepare(root,parent):
    root=Path(root).resolve();parent=Path(parent).resolve();prior=holds.verify(parent);p=read(parent/'progress.json')
    if root.exists() or root.is_relative_to(campaign.ROOT):raise ValueError('new external root required')
    if p['phase']!='stopped_on_error' or len(p['completed'])!=7 or len(p['errors'])!=1:raise ValueError('retain known integration failures')
    if any((parent/'runs'/t['id']).exists() for t in prior['tasks'] if t['role']!='train'):raise ValueError('amend before validation')
    root.mkdir();(root/'runs').mkdir();shutil.copyfile(parent/'admission.json',root/'admission.json')
    a=pins.BASE_VERIFY(root);a=deepcopy(a);name='refit-G128-five-overlap'
    query=dict(output_bits=128,terms=[[[0,b,b] for b in range(128)]]+
               [[[i,b,b+17*i] for b in range(32)] for i in range(1,5)],consumers=[],target_ps=1500)
    campaign.reduction.geometry(query);g=campaign.group(query)
    if any(g==campaign.group(s['query']) for s in a['sources']):raise ValueError('replacement source collision')
    rtl=root/'sources'/name/'input.sv';rtl.parent.mkdir(parents=True);rtl.write_text(campaign.reduction.source(query))
    ref=campaign.reference(query,'G',campaign.load(campaign.PACKAGE),campaign.profile('nangate45'))
    s=dict(id=name,family='G',role='train',query=query,local_context=None,producer_group=g,
           rtl=str(rtl),rtl_sha256=sha(rtl),reference=ref,historical_role=None,fresh_producer=True)
    excluded='G-aca48b1fead906bf';a['sources']=[x for x in a['sources'] if x['id']!=excluded]+[s]
    a['tasks']=[x for x in a['tasks'] if x['source']!=excluded]
    a['tasks'] += [dict(id=name+'-T'+str(t),source=name,family='G',role='train',rtl=str(rtl),rtl_sha256=sha(rtl),
                       period_ps=t,requested_region=region) for region,t in ref['periods_ps'].items()]
    a['tasks'].sort(key=lambda t:({'train':0,'validation':1,'test':2}[t['role']],t['family'],t['source'],t['period_ps']))
    inherited={}
    for task in a['tasks']:
        if task['id'] not in p['completed']:continue
        d=parent/'runs'/task['id'];inherited[task['id']]=dict(directory=str(d),label_sha256=sha(d/'grt-labels.json'))
        (root/'runs'/task['id']).symlink_to(d,target_is_directory=True)
    if len(inherited)!=6:raise ValueError('only six add labels inherited into matrix')
    files={str(x):sha(x) for x in (campaign.ROOT/'experiments/arithmetic_dse').glob('nangate45_refit_*.py')}
    files[str(rtl)]=sha(rtl)
    write(root/'source-amendment.json',dict(version='nangate45-N4-compact-G-amendment-v1',parent=str(parent),
        admission_sha256=sha(root/'admission.json'),implementation_sha256=sha(__file__),parent_progress_sha256=sha(parent/'progress.json'),
        reason='large G needs pin and hold integration changes; keep this recalibration a small-source experiment with original backend settings',
        sources=a['sources'],tasks=a['tasks'],inherited=inherited,files=files,call_caps=dict(synth=32,grt=34,final=0,support=360),
        excluded_source=excluded,excluded_valid_diagnostic=str(Path('/home/zyrv/vulsim-artifacts/nangate45-refit-20261117-v2/runs/G-aca48b1fead906bf-T1025-IO360/grt-labels.json')),
        retained_failures=['v1 PPL-0024','v2 RSZ-0060 buffer guard','v3 STA-0576 percent1000 outside0..100'],
        diagnostic_not_used_in_fit_or_selection=True,only_reference_clock_rule_reapplied_to_new_geometry=True,
        fit_forms_features_grids_thresholds_and_selection_unchanged=True,validation_or_test_labels_opened=False,
        baseline_layout_and_hold_guard_restored=True))
    write(root/'progress.json',dict(completed=list(inherited),phase='admitted_compact_source_successor',errors=[]))
    for f in ('preflight.json','historical-producer-audit.json','baseline-verification-before-validation.json'):
        shutil.copyfile(parent/f,root/f)
    return dict(sources=len(a['sources']),tasks=len(a['tasks']),train_points=12,inherited_labels=6,new_source=s['id'],reference=ref,
                excluded_large_G_point_not_used=True,source_amendment_sha256=sha(root/'source-amendment.json'))


def verify(root):
    root=Path(root);a=pins.BASE_VERIFY(root);s=read(root/'source-amendment.json')
    if s['admission_sha256']!=sha(root/'admission.json') or sha(Path(s['parent'])/'progress.json')!=s['parent_progress_sha256']:
        raise ValueError('source amendment or retained parent changed')
    for path,h in s['files'].items():
        if sha(path)!=h:raise ValueError('source amendment dependency drift: '+path)
    for item in s['inherited'].values():
        if sha(Path(item['directory'])/'grt-labels.json')!=item['label_sha256']:raise ValueError('inherited label changed')
    a['sources']=s['sources'];a['tasks']=s['tasks'];a['call_caps']=s['call_caps']
    a['source_amendment_sha256']=sha(root/'source-amendment.json')
    a['sampling_layout_overrides']['source_amendment_sha256']=a['source_amendment_sha256']
    return a


def run(root):
    verify(root)
    base_freeze=worker.fitting.freeze
    def freeze_with_source_seal(out):
        result=base_freeze(out)
        payload=read(out/'frozen-model.json');payload['source_amendment_sha256']=sha(out/'source-amendment.json')
        payload['excluded_large_G_diagnostic_used']=False;write(out/'frozen-model.json',payload)
        seal=read(out/'model-freeze.json');seal.update(model_sha256=sha(out/'frozen-model.json'),
            source_amendment_sha256=sha(out/'source-amendment.json'));write(out/'model-freeze.json',seal)
        return result
    with patch.object(campaign,'verify',verify),patch.object(worker.fitting,'freeze',freeze_with_source_seal):return worker.run(root)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path)
    args=p.parse_args();print(prepare(args.root,args.parent) if args.action=='prepare' else run(args.root),flush=True)
