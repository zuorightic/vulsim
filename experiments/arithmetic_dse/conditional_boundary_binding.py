"""Reuse frozen S coefficients, derive training-only shared baselines, probe gaps.

No old independent labels or current operator training labels are read. New
state-only banks validate the frozen reuse candidate; they never retrain S.
"""
import argparse
from collections import Counter
import csv
from datetime import datetime,timezone
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
from functools import lru_cache
from types import FunctionType,SimpleNamespace

from .model_fast_preflight import read,write,sha,key
from .budget import Ledger,POLICY,usage

ROOT=Path(__file__).resolve().parents[2]
PARENT=ROOT/'experiments/arithmetic/evidence/step7_general_state_v1'
SUFFIX=Path('asap7/arithmetic_probe/base')
_LIBRARIES={}

@lru_cache(maxsize=384)
def raw_context(directory,stage):
    from .model_physical_path_v2 import canonical,connections
    from .model_reference_labels import liberty
    from .model_qualification_labels import with_timing_arcs
    directory=Path(directory);m=read(directory/'manifest.json');identity=key(m['libraries'])
    if identity not in _LIBRARIES:_LIBRARIES[identity]=with_timing_arcs(liberty(m['libraries'],read(directory/'liberty_cells.json')['cells']),m['libraries'])
    prefix=directory/'reports'/SUFFIX/('vulsim_'+stage)
    instances={canonical(parts[0]):parts[1] for parts in (s.split('\t') for s in Path(str(prefix)+'_instances.tsv').read_text().splitlines())}
    return _LIBRARIES[identity],instances,connections(Path(str(prefix)+'_reference_connections.tsv'))


def frozen_fit():
    manifest=read(PARENT/'manifest.json');p=PARENT/'documents-pool.json.gz'
    if sha(p)!=manifest['files'][p.name]:raise ValueError('S frozen fit archive changed')
    item=json.loads(gzip.decompress(p.read_bytes()))['fit-data.json']
    if hashlib.sha256(item['text'].encode()).hexdigest()!=item['sha256']:raise ValueError('S fitting dataset changed')
    fit=json.loads(item['text'])
    if fit['test_labels_read'] or {r['split'] for r in fit['rows']}!={'train','validation'}:raise ValueError('S fitting-only role mismatch')
    return fit,item['sha256']


def strict_data_wires(directory,stage,path):
    """Actual connected data-wire increments, excluding the expanded clock leg."""
    from .model_physical_path_v2 import canonical,connections,verify_combinational_arc
    pins,instances,nets=raw_context(str(directory),stage)
    base=directory/'reports'/SUFFIX;prefix=base/('vulsim_'+stage)
    points=[(canonical(n),float(v)) for n,v in (s.split('\t') for s in Path(str(prefix)+'_reference_'+path['id']+'_points.tsv').read_text().splitlines())]
    start=canonical(path['start_pin']);end=canonical(path['end_pin']);offset=[i for i,(n,_) in enumerate(points) if n==start]
    if len(offset)!=1 or points[-1][0]!=end:raise ValueError('state path start/end changed')
    points=points[offset[0]:];values=[]
    for (a,ta),(b,tb) in zip(points,points[1:]):
        if not all(math.isfinite(v) for v in (ta,tb)) or tb<ta-1e-5:raise ValueError('invalid state data arrival')
        ca,pa=a.rsplit('/',1);cb,pb=b.rsplit('/',1)
        if ca==cb:verify_combinational_arc(pins[instances[ca]],pa,pb)
        elif a in nets and b in nets and nets[a]['direction']=='output' and nets[b]['direction']=='input' and nets[a]['net']==nets[b]['net']:
            values.append(max(0.,tb-ta))
        else:raise ValueError('state data wire is not actually connected')
    return values


def new_specs():
    from .model_general_state_samples import bits,semantic_signature,features
    result=[]
    for index,(depth,widths) in enumerate([(1,[5,13,17,32,49,64]),(2,[16,24,33,41,49,57,64,64])]):
        roots=[dict(width=w,reset=bits('conditional-S-new/root/'+str(index)+'/'+str(j),w)) for j,w in enumerate([32,32,64])]
        packed=sum(r['reset']<<sum(x['width'] for x in roots[:j]) for j,r in enumerate(roots));pairs=[(a,b) for b in range(1,128) for a in range(b)];cursor=1213+index*881;words=[]
        for j,width in enumerate(widths):
            declared=width+3 if index==1 and j==7 else width;mask=(1<<width)-1
            selected=[pairs[(cursor+k)%len(pairs)] for k in range(width)];cursor+=width
            reset=bits('conditional-S-new/word/'+str(index)+'/'+str(j),width)
            original=sum((((packed>>a)^(packed>>b))&1)<<k for k,(a,b) in enumerate(selected))
            start=2 if depth==2 and j%3==1 else 1;end=1 if depth==2 and j%3==2 else depth
            words.append(dict(declared_width=declared,variable_bits=width,variable_mask=mask,reset=reset,
                source_positions=[a for a,b in selected],source_positions_second=[b for a,b in selected],invert=original^reset,start=start,end=end))
        external=[];external_bits=0
        for j,w in enumerate(words):
            if w['end']==depth and external_bits+w['variable_bits']<=256:external.append(j);external_bits+=w['variable_bits']
        s=dict(id='conditional-S-validation-'+str(index),split='binding_validation',roots=roots,depth=depth,service_mode=index,words=words,external_words=external)
        s['slots']=[dict(name=f'data_{j}_s{k}',word=j,stage=k,variable_bits=w['variable_bits'],reset=w['reset']) for j,w in enumerate(words) for k in range(w['start'],w['end']+1)]
        s['expected_FF_bits']=dict(input_service=129,native_state=sum(x['variable_bits'] for x in s['slots'])+depth,external_state=external_bits+1)
        s['features']=features(s,1500);s['semantic_signature']=semantic_signature(s);result.append(s)
    return result


def prepare(out):
    from .model_general_state_samples_v2 import source
    out.mkdir(parents=True,exist_ok=False);fit,dataset_hash=frozen_fit();model=read(PARENT/'asap7-general-state.json')
    train=[r for r in fit['rows'] if r['split']=='train' and r['stage']=='grt'];runs={r['task_id']:r for r in fit['runs']}
    clock=max(r['owner_area_um2'].get('shared_clock',0)/sum(r['owner_FF_bits'].values()) for r in train)
    bounds=model['stages']['grt']['boundary_model'];six={path:max(rows[path]['overhead_ps'] for rows in bounds['immutable_by_exact_SDC'].values()) for path in next(iter(bounds['immutable_by_exact_SDC'].values()))}
    wire=0.;witness=None;raw=[]
    # Only original training state paths establish this baseline; no held-out
    # or consumed-test observations select parameters or enlarge the domain.
    for row in train:
        directory=Path(runs[row['task_id']]['directory'])
        for path in row['boundary_paths']:
            if path['kind']!='register' or path['id']=='birth_data':continue
            values=strict_data_wires(directory,'grt',path)
            if values and max(values)>wire:wire=max(values);witness=dict(row=row['id'],path=path['id'])
        raw.append(dict(row=row['id'],manifest_sha256=sha(directory/'manifest.json')))
    shell=ROOT/'build/step6-integration-20261031/public-final/MAC_32/sim/top.sv'
    if not shell.exists():shell=ROOT/'build/step6-integration-20261031/public-remaining/MAC_32/sim/top.sv'
    text=shell.read_text();tokens=['assign wen_iv = push__vld;','if (wen_iv__)','__vul_pipeline_q_iv <= wdata_iv__;','__vul_pipeline_q_ov <= __vul_pipeline_d_ov;']
    if not all(x in text for x in tokens):raise ValueError('actual public input/output service protocol changed')
    shutil.copy2(PARENT/'asap7-general-state.json',out/'reused-S.json');shutil.copy2(shell,out/'public-service-witness.sv')
    bundle=dict(version='conditional-boundary-binding-v1',quality_status='candidate_reuse',target_platform='asap7',
        profile_sha256=model['platform_profile_sha256'],operator_boundary_policy='unsigned-op-hierarchy-v1',
        state_model=dict(path='reused-S.json',sha256=sha(out/'reused-S.json'),version=model['version']),
        service_contract=dict(path='public-service-witness.sv',sha256=sha(out/'public-service-witness.sv'),required_tokens=tokens,
            data_enable_policy='independent_per_input_port',valid_enable_policy='independent_held_valid',external_capture='unconditional'),
        candidate_domain=dict(target_min_ps=250,target_max_ps=3000,max_input_data_bits=130,max_native_data_bits=1024,max_external_data_bits=256,
            max_variable_word_bits=64,max_parallel_words=18,max_internal_stages=2),
        six_path_upper_ps=six,control_models=bounds['control_models'],control_exact_clocks=model['exact_SDC_ps'],
        shared=dict(clock_area_per_FF_um2=clock,physical_area_um2=max(r['owner_area_um2'].get('shared_physical',0) for r in train),
            physical_area_per_functional_um2=max(r['owner_area_um2'].get('shared_physical',0)/sum(r['owner_area_um2'][o] for o in model['owners']) for r in train),
            root_repair_area_um2=max(r['owner_area_um2'].get('root_boundary_repair',0) for r in train),wire_per_edge_ps=wire),
        derivation=dict(fit_only_sha256=dataset_hash,training_rows=len(train),wire_witness=witness,
            S_coefficients_changed=False,shared_policy='training-only empirical upper baseline; no independent/full-stage qualification'),
        required_validation=['ABC_equals_SDC_new_targets','actual_native_projection_and_service_protocol','arithmetic_source_retention',
            'shared_area_and_wire_context','full_joint_operator_boundary_G'],full_D_ready=False)
    write(out/'binding-candidate.json',bundle);write(out/'training-derivation.json',dict(raw_training_manifests=raw,bundle_sha256=sha(out/'binding-candidate.json'),old_test_labels_read=False))
    tasks=[]
    for s in new_specs():
        directory=out/'sources'/s['id'];directory.mkdir(parents=True);(directory/'input.sv').write_text(source(s));write(directory/'contract.json',dict(spec=s,source_role='binding_validation',old_test_reused=False))
        for target in (500,1500,3000):tasks.append(dict(id=s['id']+'-T'+str(target),source=s['id'],split='binding_validation',period_ps=target,abc_target_ps=target,
            rtl=str(directory/'input.sv'),rtl_sha256=sha(directory/'input.sv'),contract=str(directory/'contract.json'),contract_sha256=sha(directory/'contract.json')))
    own=[Path(__file__),ROOT/'rtlzz/src/backend/arithmetic_state_boundary.cpp',ROOT/'rtlzz/src/backend/arithmetic_state_boundary.hpp']
    write(out/'proposal.json',dict(version='conditional-S-limited-validation-v1',tasks=tasks,new_synth_max=6,new_grt_max=6,automatic_retries=0,parallel_jobs=1,
        frozen_candidate_sha256=sha(out/'binding-candidate.json'),S_sha256=sha(out/'reused-S.json'),old_S_coefficients_changed=False,
        admission_requires_software_proof=True,physical_admission_allowed=False,source_sha256={str(p.relative_to(ROOT)):sha(p) for p in own if p.exists()},
        later_work_reserved=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3),
        validation_gates=dict(S_area_source_median_max=.20,S_area_source_P95_max=.50,all_state_boundary_upper_cover=True,shared_upper_cover=True),
        no_test_based_tuning=True,old_consumed_test_labels_excluded=True,full_D_ready=False))
    print(dict(status='prepared',old_S_unchanged=True,shared=bundle['shared'],validation_points=len(tasks),physical_admission_allowed=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare',));p.add_argument('--out',type=Path,required=True);a=p.parse_args();prepare(a.out.resolve())
