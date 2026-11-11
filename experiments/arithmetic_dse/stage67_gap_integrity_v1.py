"""Final immutable-model, physical-state and evidence checks for the gap pack."""
import argparse
from pathlib import Path
from .model_fast_preflight import read,write,sha
from . import stage67_reset_v1 as reset

ROOT=Path(__file__).resolve().parents[2]


def run(root,evidence,out):
    if out.exists():raise ValueError('preserve final gap integrity')
    for name in ('reset-train-v3','reset-validation-v3'):reset.verify(root/name)
    identities={}
    for p in (root/'reset-fit-v1/freeze.json',root/'reset-fit-v2/freeze.json',Path('/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1/fit-v1/freeze-v2.json')):
        for n,h in read(p)['files'].items():
            if sha(n)!=h:raise ValueError('frozen function drift '+n)
            identities[n]=h
    old=read(Path('/home/zyrv/vulsim-artifacts/stage67-state-shared-20261111-v1/candidate-freeze.json'))
    for n,h in old['sources'].items():
        if sha(ROOT/n)!=h:raise ValueError('old frozen consumer changed '+n)
        identities[str(ROOT/n)]=h
    binary=ROOT/'build/step4-rtlzz/testv2/arithmetic-factored-timing-consumer'
    if sha(binary)!=old['binary_sha256']:raise ValueError('old native binary drift')
    for name in ('shared-probe','shared-continuation-v1'):
        a=read(root/name/'admission.json')
        for n,h in a['sources'].items():
            if sha(ROOT/n)!=h or sha(root/name/'source'/n)!=h:raise ValueError('probe/continuation producer drift '+n)
    if read(root/'reset-fit-v2/validation.json')['status']!='failed_reset_validation':raise ValueError('failed validation overwritten')
    if read(root/'shared-continuation-v1/progress.json')['phase']!='physical_continuation_complete':raise ValueError('physical continuation unsettled')
    archive=root/'archives/gap-raw-v1.tar.gz';index=read(str(archive)+'.index.json')
    if sha(archive)!=index['archive_sha256'] or not index['actual_restore_and_every_member_hash_checked']:raise ValueError('raw archive changed')
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('evidence size budget')
    write(out,dict(status='passed_final_reset_alias_integrity',frozen_files=identities,old_native_binary_sha256=sha(binary),raw_archive_sha256=sha(archive),
        raw_members=len(index['members']),portable_bytes=sum(sizes),portable_manifest_sha256=sha(evidence/'manifest.json'),
        reset_release_qualified=False,shared_normalized_model_qualified=False,independent_tests_unlocked=False,full_D_ready=False))
    print('GAP_IMMUTABLE_INTEGRITY_PASS frozen_files='+str(len(identities))+' raw_members='+str(len(index['members'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('root','evidence','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.root.resolve(),a.evidence.resolve(),a.out.resolve())
