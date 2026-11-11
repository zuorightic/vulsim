"""Seal ownership recovery separately from the unchanged v2 acquisition."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha
from .operator_stage4 import archive
from .operator_collection import measurement_sources

ROOT=Path(__file__).resolve().parents[2]


def seal(root,node,fresh,out):
    if out.exists():raise ValueError('preserve evidence')
    qualification=read(root/'qualification.json');assert qualification['status']=='passed_saved_snapshot_qualification'
    full=read(root/'all-fitting-labels.json');assert full['status']=='passed_all_fitting_labels_unchanged'
    freeze=read(node/'fit-v2/selection-freeze.json')
    assert all(sha(ROOT/n)==h for n,h in freeze['implementation_sources'].items())
    assert sha(node/'fit-v2/candidate.json')==freeze['model_sha256']==sha(fresh/'frozen-function.json')
    protocol=read(root/'protocol.json');files={};tasks=[]
    names=set(measurement_sources())|set(protocol['implementation'])
    names.update('experiments/arithmetic_dse/'+n for n in ('model_logical_labels_v1.py','model_logical_stage_v1.py','model_logical_qualification_v1.py',
        'operator_ownership_successor_v1.py','operator_ownership_followthrough_v1.py','operator_ownership_evidence_v1.py'))
    names.update(('regression/arithmetic_operator_ownership.py','regression/arithmetic_operator_ownership_dataset.py','regression/arithmetic_ownership_replay.py'))
    for n in names:files['source/'+n]=(ROOT/n).read_text()
    for n in ('experiments/__init__.py','experiments/arithmetic_dse/__init__.py','regression/__init__.py'):
        if (ROOT/n).exists():files['source/'+n]=(ROOT/n).read_text()
    for t in protocol['tasks']:
        d=root/'tasks'/t['id'];contract=read(Path(t['folder'])/'query-contract.json')
        tasks.append(dict(id=t['id'],packet=read(d/'packet.json'),nodes=contract['nodes'],banks=contract['banks'],
            ports=read(d/'top-ports.json'),certificate=read(d/'certificate.json'),label=read(d/'recovered-labels.json')))
    files['frozen-function.json']=(fresh/'frozen-function.json').read_text()
    pool=dict(files=files,tasks=tasks);raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0)
    out.mkdir(parents=True);parts={}
    for i,at in enumerate(range(0,len(compressed),512*1024)):
        p=out/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[at:at+512*1024]);parts[p.name]=sha(p)
    shutil.copy2(ROOT/'regression/arithmetic_ownership_replay.py',out/'replay.py')
    write(out/'manifest.json',dict(version='operator-logical-ownership-evidence-v1',parts=parts,payload_sha256=hashlib.sha256(raw).hexdigest(),
        replay_sha256=sha(out/'replay.py'),source_files=len(files),physical_stages=len(tasks),full_D_ready=False))
    for n in ('qualification.json','all-fitting-labels.json','boundary-change-review.json','reuse-proof.json'):shutil.copy2(root/n,out/n)
    write(out/'summary.json',dict(status=qualification['status'],recovered_failed_stages=4,recovered_cells=5,unchanged_control_stages=12,
        negative_rejections=qualification['negative_rejections'],unchanged_fitting_points=full['points'],unchanged_fitting_stages=full['stages'],
        model_sha256=freeze['model_sha256'],parameters_domain_reserve_changed=False,old_failed_test_verdict_unchanged=True,
        fresh_independent_root=str(fresh),fresh_sources=4,fresh_source_target_requests=16,
        fresh_target_ps=[500,1000,1500,3000],fresh_status=read(fresh/'progress.json')['phase'],
        fresh_admission_sha256=sha(fresh/'admission.json'),fresh_initial_restore_sha256=sha(fresh/'archives/initial-frozen-source.tar.gz.index.json'),
        new_synthesis_for_recovery=0,new_global_route_for_recovery=0,fresh_independent_pending=True,
        S_G_joint_qualified=False,full_D_ready=False))
    source=root/('sealed-source-'+out.name);source.mkdir()
    for n,text in files.items():
        p=source/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    receipt=archive(root,[root/'tasks',root/'protocol.json',root/'qualification.json',root/'all-fitting-labels.json',root/'boundary-change-review.json',root/'reuse-proof.json',source],
        out.name+'.tar.gz')
    write(out/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(members=len(receipt['members'])))
    if sum(p.stat().st_size for p in out.iterdir())>5*1024**2 or any(p.stat().st_size>1024**2 for p in out.iterdir()):raise ValueError('compact evidence envelope exceeded')
    print(dict(status='sealed_ownership_recovery',stages=len(tasks),parts=len(parts),restored_members=len(receipt['members'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for n in ('root','node','fresh','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();seal(a.root.resolve(),a.node.resolve(),a.fresh.resolve(),a.out.resolve())
