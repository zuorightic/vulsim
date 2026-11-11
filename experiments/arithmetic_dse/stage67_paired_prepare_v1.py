"""Structural alternate placements for the same validation sources, no EDA.

The placement is the opposite preregistered early/first cut. No physical labels
or prices choose it. The original source role and all original artifacts stay.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
from .model_fast_preflight import read,write,sha
from . import stage67_shared_fit_v1 as shared
from .stage67_multiclock_v1 import PARENT,POLICY_PATH,FREEZE


def prepare(out):
    if out.exists():raise ValueError('preserve paired software preparation')
    out.mkdir(parents=True);rows=[];original=PARENT/'preparation-v2'
    for value in read(original/'sources.json')['sources']:
        if value['role']!='validation':continue
        r=deepcopy(value);oldcut=r['cut'];r['cut']='first' if oldcut=='early' else 'early';r['structural_alternate_of']=oldcut
        dest=out/'sources'/r['id'];dest.mkdir(parents=True);source=dest/'source.cpp';shutil.copy2(r['source'],source)
        if sha(source)!=r['source_sha256']:raise ValueError('same source bytes required')
        r['source']=str(source);write(dest/'request.json',r);rows.append(r)
    write(out/'sources.json',dict(sources=rows))
    write(out/'protocol.json',dict(version='structural-paired-stage-validation-software-v1',targets_ps=[500,1500,3000],
        roles={r['id']:r['role'] for r in rows},rule='opposite fixed early/first arithmetic cut; no price or physical feedback',
        shared_policy_sha256=sha(POLICY_PATH),freeze_sha256=sha(FREEZE),source_bytes_unchanged=True,parameter_changes=False,
        physical_capacity=dict(synth=9,grt=9,support=144,threads=4,parallel_jobs=4,memory_MiB=8192),
        physical_gate='complete-stage and false-feasible primary-nine validation must pass first',physical_admission_allowed=False,independent_test_unlocked=False,full_D_ready=False))
    print('STRUCTURAL_ALTERNATES_REGISTERED sources=3 EDA=0',flush=True)


def export(out,tool):
    from regression.arithmetic_steps123 import execute
    for r in read(out/'sources.json')['sources']:
        d=out/'sources'/r['id'];execute(out/'receipts'/('paired-export-'+r['id']),'export',[
            str(tool),str(shared.ROOT),str(d/'request.json'),str(shared.NODE),str(shared.BINDING),str(d/'native')],120)


def products(out):
    for r in read(out/'sources.json')['sources']:
        d=out/'sources'/r['id']/'native';e=read(d/'export.json');v=e['variants'][0]
        old=read(PARENT/'preparation-v2/sources'/r['id']/'native/export.json')['variants'][0]
        if v['placement']==old['placement']:raise ValueError('alternate must have different actual native register placement')
        if e['graph']['sha256']!=read(PARENT/'preparation-v2/sources'/r['id']/'native/export.json')['graph']['sha256']:raise ValueError('same combinational graph required')
        v['id']='placement-1'
        for key in ('rtl_file',):
            name=v[key];new=name.replace('placement-0','placement-1');(d/name).rename(d/new);v[key]=new
        p=d/'placement-0.beir';p.rename(d/'placement-1.beir')
        write(d/'export.json',e)
    shared.products(out)
    manifest=dict(sources=[dict(request=str(out/'sources'/r['id']/'request.json'),parent_export=str(out/'sources'/r['id']/'native/export.json')) for r in read(out/'sources.json')['sources']])
    write(out/'consumer-manifest.json',manifest)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','export','products'));p.add_argument('--out',type=Path,required=True);p.add_argument('--tool',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve())
    elif a.action=='export':export(a.out.resolve(),a.tool.resolve())
    else:products(a.out.resolve())
