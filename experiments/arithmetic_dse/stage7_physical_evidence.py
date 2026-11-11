"""Seal stage7 preparation and actually restore every archived byte."""
import argparse
from pathlib import Path
import shutil
import sys
import tarfile

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def seal(out,evidence,node_root):
    if evidence.exists() or (out/'archive').exists():raise ValueError('preserve earlier seals')
    evidence.mkdir(parents=True);payload=out/'archive/payload';payload.mkdir(parents=True)
    latest=read(node_root/read(node_root/'active-collection.json')['path']);freeze=read(node_root/'fit-v2/selection-freeze.json')
    for label,files in [('measurement',latest['measurement_sources']),('node_inference',freeze['implementation_sources'])]:
        failures=[name for name,digest in files.items() if sha(ROOT/name)!=digest]
        if failures:raise ValueError('active frozen dependencies changed: '+repr(failures))
    write(evidence/'unchanged-dependencies.json',dict(measurement_files=len(latest['measurement_sources']),
        node_inference_files=len(freeze['implementation_sources']),unchanged=True,S_sha256=sha(ROOT/'experiments/arithmetic/evidence/step7_general_state_v1/asap7-general-state.json')))
    # Keep full sources, generated RTL, queries, vectors and software receipts
    # in the retained artifact tree; only compact evidence belongs in Git.
    for p in sorted(out.rglob('*')):
        if not p.is_file() or 'archive' in p.relative_to(out).parts:continue
        target=payload/'preparation'/p.relative_to(out);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    source_paths=[ROOT/'experiments/arithmetic_dse/stage7_physical_prepare.py',Path(__file__),ROOT/'regression/arithmetic_stage7_physical.py',
        ROOT/'rtlzz/testv2/arithmetic_stage7_export.cpp',ROOT/'experiments/arithmetic_dse/reference_assets/stage7_readout_v1.tcl']
    for p in source_paths:
        target=payload/'implementation'/p.relative_to(ROOT);target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
    deps=read(out/'dependencies.json')
    for key in ('model','S_binding'):
        p=Path(deps[key]['path']);target=payload/'dependencies'/key/p.name;target.parent.mkdir(parents=True);shutil.copy2(p,target)
    binding=Path(deps['S_binding']['path'])
    for key in ('state_model','service_contract'):
        ref=read(binding)[key];p=Path(ref['path']);p=p if p.is_absolute() else binding.parent/p
        assert sha(p)==ref['sha256'];shutil.copy2(p,payload/'dependencies/S_binding'/p.name)
    members={str(p.relative_to(payload)):dict(bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(payload.rglob('*')) if p.is_file()}
    write(out/'archive/members.json',members);archive=out/'archive/preparation.tar.gz'
    with tarfile.open(archive,'w:gz') as tar:
        for name in members:tar.add(payload/name,arcname=name,recursive=False)
    restored=out/'archive/restored';restored.mkdir()
    with tarfile.open(archive,'r:gz') as tar:tar.extractall(restored,filter='data')
    assert {str(p.relative_to(restored)) for p in restored.rglob('*') if p.is_file()}==set(members)
    for name,expected in members.items():
        p=restored/name;assert p.stat().st_size==expected['bytes'] and sha(p)==expected['sha256'],name
    for source,target in [('protocol.json','protocol.json'),('structures.json','structures.json'),('coverage-diagnostic.json','coverage-diagnostic.json'),
        ('verification/proof.json','proof.json'),('verification/acceptance-table.json','acceptance-table.json')]:shutil.copy2(out/source,evidence/target)
    write(evidence/'restore-proof.json',dict(status='passed_byte_restore',members=len(members),bytes=sum(m['bytes'] for m in members.values()),
        archive=str(archive),archive_sha256=sha(archive),archive_bytes=archive.stat().st_size,restored=str(restored),
        retained_until_user_cleanup=True,off_machine_backup=False,physical_calls=0,full_D_ready=False))
    print(dict(status='passed_byte_restore',members=len(members),archive_bytes=archive.stat().st_size),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path,required=True);p.add_argument('--evidence',type=Path,required=True);p.add_argument('--node-root',type=Path,required=True)
    a=p.parse_args();seal(a.out.resolve(),a.evidence.resolve(),a.node_root.resolve())
