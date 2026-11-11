"""Restore every original report/member; inherit old snapshots by archive SHA."""
import argparse
import gzip
from pathlib import Path
import shutil
import tarfile
import tempfile
from .model_fast_preflight import read,write,sha
from .operator_stage4 import inventory
from .stage67_multiclock_v1 import verify_admission,PARENT,FREEZE,NODE,BINDING,POLICY_PATH,ROOT


def archive(root):
    verify_admission(root);verify_admission(root/'paired-readout')
    for n,h in read(FREEZE)['files'].items():
        if sha(n)!=h:raise ValueError('frozen model drift '+n)
    previous=PARENT/'archives/shared-function-raw-v2.tar.gz'
    write(root/'archive-dependencies.json',dict(prior_shared_archive_sha256=sha(previous),prior_shared_archive_path=str(previous),
        prior_primary_snapshots_reused_not_remeasured=True,freeze_sha256=sha(FREEZE),full_D_ready=False))
    for p,name in [(NODE,'operators.json'),(BINDING,'binding.json'),(BINDING.parent/'reused-S.json','reused-S.json'),(POLICY_PATH,'policy.json'),(FREEZE,'freeze.json')]:
        d=root/'dependencies'/name;d.parent.mkdir(exist_ok=True);shutil.copy2(p,d)
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):
        d=root/'final-source'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    for p in [ROOT/'regression/arithmetic_steps123.py',ROOT/'regression/arithmetic_multiclock_stage.py']:
        d=root/'final-source'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    shutil.copytree(ROOT/'build/step67-multiclock-20261111',root/'support-receipts-before-archive')
    members={}
    for path in root.iterdir():
        if path.name in ('archives','restore'):continue
        if path.is_dir():
            for p in path.rglob('*'):
                if p.is_file():members[str(p.relative_to(root))]=p
        elif path.is_file():members[str(path.relative_to(root))]=path
    index={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in members.items()}
    target=root/'archives/multiclock-raw-v1.tar.gz';target.parent.mkdir(exist_ok=True);(root/'restore').mkdir(exist_ok=True)
    with target.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,compresslevel=1) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as bundle:
                for n,p in sorted(members.items()):bundle.add(p,arcname=n,recursive=False)
    with tempfile.TemporaryDirectory(prefix='actual-restore-',dir=root/'restore') as directory:
        out=Path(directory);seen=set()
        with tarfile.open(target,'r|gz') as bundle:
            for member in bundle:
                if not member.isfile() or member.name not in index or member.name in seen or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('unexpected archive member')
                seen.add(member.name);p=out/member.name;p.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(member) as source,p.open('wb') as dest:shutil.copyfileobj(source,dest)
        if seen!=set(index) or inventory(out)!=index:raise ValueError('actual restored member bytes differ')
    write(target.with_suffix(target.suffix+'.index.json'),dict(status='passed',version='multiclock-whole-artifact-restore-v1',archive=str(target),archive_sha256=sha(target),archive_bytes=target.stat().st_size,
        logical_bytes=sum(v['bytes'] for v in index.values()),members=index,actual_restore_and_every_member_hash_checked=True,old_primary_snapshots_in_prior_archive=True,no_raw_artifacts_deleted=True,storage_class='local same-disk archive'))
    print('MULTICLOCK_RAW_RESTORED members='+str(len(index))+' bytes='+str(target.stat().st_size),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args();archive(a.root.resolve())
