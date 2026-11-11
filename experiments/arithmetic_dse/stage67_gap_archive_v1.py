"""Archive and actually restore all new gap artifacts, retaining old SHA links."""
import argparse
import gzip
from pathlib import Path
import shutil
import tarfile
import tempfile
from .model_fast_preflight import read,write,sha
from .operator_stage4 import inventory

ROOT=Path(__file__).resolve().parents[2]


def archive(root):
    for p in (root/'reset-fit-v1/freeze.json',root/'reset-fit-v2/freeze.json',Path('/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1/fit-v1/freeze-v2.json')):
        for n,h in read(p)['files'].items():
            if sha(n)!=h:raise ValueError('immutable inference changed '+n)
    if read(root/'shared-continuation-v1/progress.json')['phase']!='physical_continuation_complete':raise ValueError('physical continuation unsettled')
    prior=Path('/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1/archives/shared-function-raw-v2.tar.gz');index=read(str(prior)+'.index.json')
    if sha(prior)!=index['archive_sha256'] or index['status']!='passed':raise ValueError('old snapshot archive identity differs')
    write(root/'archive-dependencies.json',dict(prior_archive_path=str(prior),prior_archive_sha256=sha(prior),old_train_and_validation_physical_snapshots_reused=True,new_reports_in_this_archive=True,raw_artifacts_deleted=False))
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):
        d=root/'final-source'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    for p in [ROOT/'regression/arithmetic_steps123.py',ROOT/'regression/arithmetic_reset_function.py',*list((ROOT/'rtlzz/src/backend').glob('arithmetic_reset_function*')),*list((ROOT/'rtlzz/testv2').glob('arithmetic_reset_function*'))]:
        d=root/'final-source'/p.relative_to(ROOT);d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,d)
    shutil.copytree(ROOT/'build/step67-gap-20261111',root/'support-receipts-before-archive')
    members={}
    for path in root.iterdir():
        if path.name in ('archives','restore'):continue
        for p in path.rglob('*') if path.is_dir() else [path]:
            if p.is_file():members[str(p.relative_to(root))]=p
    index={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in members.items()};target=root/'archives/gap-raw-v1.tar.gz';target.parent.mkdir(exist_ok=True);(root/'restore').mkdir(exist_ok=True)
    with target.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,compresslevel=1) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as bundle:
                for n,p in sorted(members.items()):bundle.add(p,arcname=n,recursive=False)
    with tempfile.TemporaryDirectory(prefix='actual-gap-restore-',dir=root/'restore') as tmp:
        out=Path(tmp);seen=set()
        with tarfile.open(target,'r|gz') as bundle:
            for member in bundle:
                if not member.isfile() or member.name not in index or member.name in seen or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('unexpected archive member')
                seen.add(member.name);p=out/member.name;p.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(member) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
        if seen!=set(index) or inventory(out)!=index:raise ValueError('actual gap restore differs')
    write(str(target)+'.index.json',dict(status='passed',version='reset-alias-gap-raw-restore-v1',archive=str(target),archive_sha256=sha(target),archive_bytes=target.stat().st_size,logical_bytes=sum(v['bytes'] for v in index.values()),
        members=index,actual_restore_and_every_member_hash_checked=True,prior_archive_sha256=sha(prior),original_artifacts_deleted=False,storage_class='local same-disk archive'))
    print('GAP_RAW_RESTORED members='+str(len(index))+' bytes='+str(target.stat().st_size),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);a=p.parse_args();archive(a.root.resolve())
