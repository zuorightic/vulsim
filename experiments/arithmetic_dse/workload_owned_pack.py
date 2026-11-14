"""Package a completed W2 software run; original receipts are copied verbatim."""
import argparse
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import tarfile
from .workload_owned import read

REPO=Path(__file__).resolve().parents[2]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def pack(root,support,out):
    root=Path(root).resolve();support=Path(support).resolve();out=Path(out).resolve()
    out.mkdir(parents=True,exist_ok=False);archives=[]
    def archive(name,files,**identity):
        target=out/name;target.parent.mkdir(parents=True,exist_ok=True);members={}
        with target.open('wb') as raw,gzip.GzipFile(filename='',fileobj=raw,mode='wb',mtime=0) as gz,tarfile.open(fileobj=gz,mode='w') as tf:
            for key,path in sorted(files.items()):
                data=path.read_bytes();info=tarfile.TarInfo(key);info.size=len(data);info.mtime=0
                tf.addfile(info,io.BytesIO(data));members[key]=dict(bytes=len(data),sha256=digest(data))
        if target.stat().st_size>10*1024*1024:raise ValueError('archive exceeds 10MiB: '+name)
        archives.append(dict(file=name,bytes=target.stat().st_size,sha256=digest(target.read_bytes()),members=members,**identity))
    summary=read(root/'summary.json');parent=support/'all-v1'
    assert sum(r['structures'] for r in summary)==64 and sum(r['placements'] for r in summary)==502
    for row in summary:
        case=row['case'];case_root=root/case
        files={str(p.relative_to(case_root)):p for p in case_root.rglob('*') if p.is_file() and
               not p.relative_to(case_root).parts[0].startswith('structure-') and 'no-eda-bin' not in p.parts}
        # Structure logs live next to the structure directories.
        files.update({p.name:p for p in case_root.glob('structure-*.log')})
        files['report-parent.json']=parent/case/'report.json'
        archive(f'cases/{case}.tar.gz',files,kind='case',case=case)
        for record in read(case_root/'report.json')['structures']:
            number=record['structure'];base=case_root/f'structure-{number}'
            files={str(p.relative_to(base)):p for p in base.rglob('*') if p.is_file() and p.name!='sim.out'}
            files['inventory-parent.json']=parent/case/f'structure-{number}/inventory.json'
            archive(f'structures/{case}-{number}.tar.gz',files,kind='structure',case=case,structure=number)
    # Frozen predecessor sources are an explicit overlay, never changed hashes.
    snap=support/'predecessor-sources.tar.gz';shutil.copyfile(snap,out/snap.name)
    with tarfile.open(snap,'r:gz') as tf:
        members={m.name:dict(bytes=m.size,sha256=digest(tf.extractfile(m).read())) for m in tf}
    archives.append(dict(file=snap.name,bytes=snap.stat().st_size,sha256=digest(snap.read_bytes()),members=members,kind='predecessor-sources'))
    shutil.copyfile(root/'models.json',out/'models.json');shutil.copyfile(root/'summary.json',out/'summary.json')
    shutil.copytree(support/'v1-regression-final',out/'v1-regression')
    shutil.copyfile(support/'v1-regression-final/summary.json',out/'v1-regression.json')
    edge=out/'owner-edges';edge.mkdir()
    for src,name in [('owner-edges-final.sv','design.sv'),('owner-edges-tb.sv','tb.sv'),
                     ('owner-contract-test-final.log','contract-test.log'),('owner-edges-v2-simulation.log','simulation.log'),
                     ('owner-edges-v2-iverilog.log','iverilog.log')]:shutil.copyfile(support/src,edge/name)
    # The edge RTL has not changed since the actually simulated build.
    assert (support/'owner-edges-final.sv').read_bytes()==(support/'owner-edges-v2.sv').read_bytes()
    history=out/'history';history.mkdir()
    snapshot=support/'build-v5-snapshot'
    files={str(p.relative_to(snapshot)):p for p in snapshot.rglob('*') if p.is_file() and p.name!='rtlzz-workload'}
    # This is a historical source snapshot, not replayed as the successor ABI.
    with tarfile.open(history/'parent-source-delta.tar.gz','w:gz') as tf:
        for name,p in sorted(files.items()):tf.add(p,arcname=name,recursive=False)
    retained=[]
    for p in sorted(support.glob('*.log')):
        data=p.read_bytes()
        if len(data)<1024*1024:
            shutil.copyfile(p,history/p.name);retained.append(p.name)
    dump(out/'archives.json',archives)
    dump(out/'provenance.json',dict(run_root=str(root),parent_run_root=str(parent),artifact_root=str(support),
        parent_main_commit='edb16d3',parent_binary_overwritten_during_development=True,
        parent_W2_binary_sha256=digest((snapshot/'rtlzz-workload').read_bytes()),
        original_W1_receipts_unchanged=True,retained_development_logs=retained,
        target_scope='first registered T per case',new_EDA_calls=0,new_model_sources_admitted=0,
        fitting_performed=False,independent_labels_read=False,full_D_ready=False))
    source_names=set(read(REPO/'experiments/arithmetic/evidence/workloads_software_v1/manifest.json')['implementation_sources'])
    for base,patterns in [(REPO/'rtlzz/src',('*.cpp','*.hpp','*.h')),(REPO/'rtlzz/main',('*.cpp',)),
                          (REPO/'experiments/arithmetic_dse',('*.py',))]:
        for pattern in patterns:
            source_names.update(str(p.relative_to(REPO)) for p in base.rglob(pattern) if '__pycache__' not in p.parts)
    source_names.update({'rtlzz/testv2/arithmetic_workload_owner_test.cpp','rtlzz/testv2/arithmetic_wide_query_test.cpp'})
    dump(out/'manifest.json',dict(version='workload-owners-evidence-v2',
        implementation_sources={n:digest((REPO/n).read_bytes()) for n in sorted(source_names)},
        evidence_files={str(p.relative_to(out)):digest(p.read_bytes()) for p in sorted(out.rglob('*')) if p.is_file()},
        new_EDA_calls=0,new_model_sources_admitted=0,independent_labels_read=False,full_D_ready=False))
    print(json.dumps(dict(directory=str(out),archives=len(archives),bytes=sum(p.stat().st_size for p in out.rglob('*') if p.is_file()))))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--support',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
    args=p.parse_args();pack(args.root,args.support,args.out)
