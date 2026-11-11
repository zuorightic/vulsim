"""Explicit successor for unused input in two-product reduction generator.

Old source/snapshots/failure receipts remain intact. Only changed source
identities are recompiled and remeasured; unchanged train snapshots are reused.
No new regression feature, clock, fit rule, test role or quality gate.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha
from . import stage67_shared_fit_v1 as base

RENAMES={'train_r24':'train_r24_disjoint','train_r32':'train_r32_disjoint','validation_r28':'validation_r28_disjoint'}


def prepare(parent,out):
    if out.exists():raise ValueError('preserve generator repair')
    out.mkdir(parents=True);old=read(parent/'sources.json');rows=[];changes=[]
    for value in old['sources']:
        r=deepcopy(value);prior=r['id'];d=out/'sources'/RENAMES.get(prior,prior);d.mkdir(parents=True)
        text=Path(r['source']).read_text()
        if prior in RENAMES:
            w=r['w'];a=f'Int<{2*w}> p1=Int<{2*w}>(b*c);';b=f'Int<{2*w}> p1=Int<{2*w}>(c*d);'
            if text.count(a)!=1:raise ValueError('two-product repair callsite differs')
            text=text.replace(a,b);r['id']=RENAMES[prior];r['pairs']=[['a','b'],['c','d']]
            r['output_reset']=base.reference(r,{p['name']:int(p['reset_hex'],16) for p in r['inputs']})
            changes.append(dict(old_id=prior,new_id=r['id'],old_source_sha256=r['source_sha256'],role=r['role'],reason='consume all declared independent inputs in disjoint two-product reduction'))
        p=d/'source.cpp';p.write_text(text);r.update(source=str(p),source_sha256=sha(p));write(d/'request.json',r);rows.append(r)
        if prior not in RENAMES and (parent/'sources'/prior/'native').exists():shutil.copytree(parent/'sources'/prior/'native',d/'native')
    protocol=read(parent/'protocol.json');protocol.update(version='shared-compatible-function-fit-v2',parent_protocol_sha256=sha(parent/'protocol.json'),
        source_generator_repairs=changes,failed_source_roles_retained=True,prior_successful_snapshots_reused=True)
    protocol['roles']={r['id']:r['role'] for r in rows}
    protocol['initial_batch_sources']=[r['id'] for r in rows if r['role']=='train']
    for role in ('train','validation'):protocol[role+'_requests']=[dict(source=r['id'],target_ps=t) for r in rows if r['role']==role for t in protocol['targets_ps']]
    protocol['successor_physical_batch']=dict(train_sources=[RENAMES[n] for n in ('train_r24','train_r32')],synth_max=6,grt_max=6,support_max=72,automatic_retries=0,
        kind='new RTL/source identities; no repetition of a successful point')
    write(out/'protocol.json',protocol);write(out/'sources.json',dict(sources=rows));shutil.copy2(parent/'demand-summary.json',out/'demand-summary.json')
    print('SHARED_GENERATOR_SUCCESSOR train_sources=2 validation_sources=1 changed; old successes preserved',flush=True)


def export(out,tool):
    from regression.arithmetic_steps123 import execute
    for r in read(out/'sources.json')['sources']:
        if r['id'] not in RENAMES.values():continue
        d=out/'sources'/r['id'];execute(out/'receipts'/(out.name+'-export-'+r['id']),'export',[str(tool),str(base.ROOT),str(d/'request.json'),str(base.NODE),str(base.BINDING),str(d/'native')],120)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','export','products'));p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--tool',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.parent.resolve(),a.out.resolve())
    elif a.action=='export':export(a.out.resolve(),a.tool.resolve())
    else:base.products(a.out.resolve())
