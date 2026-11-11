"""Archive D outputs and replay numerical selection/RTL fixtures in isolation."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

ROOT=Path(__file__).resolve().parents[2]
BUNDLE=ROOT/'experiments/arithmetic/models/asap7_function_D_prototype_v1'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def archive(root):
    from .stage8_d_output_v1 import verify
    from .operator_stage4 import inventory
    verify(root)
    for n,h in read(root/'delivery-freeze.json')['files'].items():
        if sha(n)!=h:raise ValueError('frozen D delivery changed '+n)
    smoke=read(root/'public-entry-output/selection.json');original=read(root/'outputs/T1500/selection.json')
    for key in ('selected_view','selected_candidate','selected_area_um2','selected_timing_violation_ps'):
        if smoke[key]!=original[key]:raise ValueError('public D entry changed actual selection')
    if sha(root/'public-entry-output/D.sv')!=sha(root/'outputs/T1500/D.sv'):raise ValueError('public D entry changed RTL')
    write(root/'public-entry-proof.json',dict(status='passed_public_entry_reproduction',selected_view=smoke['selected_view'],rtl_sha256=sha(root/'public-entry-output/D.sv'),full_D_ready=False))
    shutil.copytree(BUNDLE,root/'model-bundle');shutil.copy2(ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json',root/'operators.json')
    consumer=root/'consumer';consumer.mkdir();shutil.copy2(ROOT/'build/step4-rtlzz/rtlzz-d',consumer/'rtlzz-d')
    for folder in ('experiments/arithmetic_dse','regression'):
        for p in (ROOT/folder).glob('*.py'):
            if folder=='regression' and p.name not in ('arithmetic_steps123.py','arithmetic_function_d.py'):continue
            dest=root/'final-source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for name in read(BUNDLE/'bundle.json')['consumer_sources']:
        p=ROOT/name;dest=root/'final-source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    shutil.copy2(ROOT/'rtlzz/CMakeLists.txt',root/'final-source/rtlzz/CMakeLists.txt')
    shutil.copytree(ROOT/'build/step8-D-20261111',root/'support-receipts-before-archive')
    members={}
    for path in root.iterdir():
        if path.name in ('archives','restore'):continue
        for p in path.rglob('*') if path.is_dir() else [path]:
            if p.is_file():members[str(p.relative_to(root))]=p
    index={n:dict(sha256=sha(p),bytes=p.stat().st_size) for n,p in members.items()};target=root/'archives/D-output-raw-v1.tar.gz';target.parent.mkdir(exist_ok=True);(root/'restore').mkdir(exist_ok=True)
    with target.open('xb') as raw:
        with gzip.GzipFile(fileobj=raw,mode='wb',mtime=0,compresslevel=1) as compressed:
            with tarfile.open(fileobj=compressed,mode='w|',dereference=True) as bundle:
                for n,p in sorted(members.items()):bundle.add(p,arcname=n,recursive=False)
    with tempfile.TemporaryDirectory(prefix='actual-D-restore-',dir=root/'restore') as tmp:
        out=Path(tmp);seen=set()
        with tarfile.open(target,'r|gz') as bundle:
            for member in bundle:
                if not member.isfile() or member.name not in index or member.name in seen or Path(member.name).is_absolute() or '..' in Path(member.name).parts:raise ValueError('unexpected D archive member')
                seen.add(member.name);p=out/member.name;p.parent.mkdir(parents=True,exist_ok=True)
                with bundle.extractfile(member) as src,p.open('wb') as dst:shutil.copyfileobj(src,dst)
        if seen!=set(index) or inventory(out)!=index:raise ValueError('actual D restore differs')
    write(str(target)+'.index.json',dict(status='passed',members=index,archive_sha256=sha(target),archive_bytes=target.stat().st_size,actual_restore_and_every_member_hash_checked=True,no_artifacts_deleted=True,storage_class='local same-disk archive'))
    print('D_RAW_RESTORED members='+str(len(index))+' bytes='+str(target.stat().st_size),flush=True)


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve D portable evidence')
    pool={}
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):pool['source/'+str(p.relative_to(ROOT))]=p.read_text()
    for name in ['regression/arithmetic_steps123.py','regression/arithmetic_function_d.py',*read(BUNDLE/'bundle.json')['consumer_sources']]:pool['source/'+name]=(ROOT/name).read_text()
    for n in ('source-request.json','source.cpp','admission.json','parity.json','negative.json','partial-domain-negative-v2/proof.json','public-entry-proof.json'):
        pool['data/output/'+n]=(root/n).read_text()
    for p in (root/'outputs').rglob('*'):
        if p.is_file():pool['data/output/'+str(p.relative_to(root))]=p.read_text()
    for p in BUNDLE.iterdir():
        if p.is_file():pool['data/models/asap7_function_D_prototype_v1/'+p.name]=p.read_text()
    pool['data/models/asap7_conditional_operators_v1/operators.json']=(ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json').read_text()
    for n in ('vectors.hex','all.sv','tb.sv','contract.json'):pool['data/expected-simulation/'+n]=(root/'simulation'/n).read_text()
    receipt=read(ROOT/'build/step8-D-20261111/d8-sim-run-01/commands.json');pool['data/simulation-receipt.json']=json.dumps(receipt);pool['data/simulation.log']=Path(receipt[0]['log']).read_text()
    pool['data/raw-restore.json']=(root/'archives/D-output-raw-v1.tar.gz.index.json').read_text()
    evidence.mkdir(parents=True);raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    index={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};p=evidence/'file-index.json.gz';p.write_bytes(gzip.compress(json.dumps(index,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    shutil.copy2(Path(__file__),evidence/'replay.py');write(evidence/'manifest.json',dict(version='function-D-output-evidence-v1',members=len(pool),chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        file_index_sha256=sha(p),replay_sha256=sha(evidence/'replay.py'),original_output_root=str(root),numerical_cases=5,reset_timing_checked=False,full_D_ready=False,
        replay_scope='independent Python functions/DAG/selection and exact RTL fixture regeneration; sealed successful native simulation receipt, no EDA or compiler launch'))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('D compact evidence limit exceeded')
    print('D_EVIDENCE_SEALED members='+str(len(pool))+' bytes='+str(sum(sizes)),flush=True)


def replay(evidence):
    m=read(evidence/'manifest.json')
    if sha(evidence/'replay.py')!=m['replay_sha256'] or sha(evidence/'file-index.json.gz')!=m['file_index_sha256']:raise ValueError('D replay/index changed')
    compressed=b''
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('D chunk changed')
        compressed+=(evidence/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('D payload changed')
    pool=json.loads(raw);index=json.loads(gzip.decompress((evidence/'file-index.json.gz').read_bytes()))
    if set(pool)!=set(index) or len(pool)!=m['members']:raise ValueError('D inventory changed')
    with tempfile.TemporaryDirectory(prefix='function-D-replay-') as tmp:
        root=Path(tmp)
        for n,value in pool.items():
            p=Path(n)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=index[n]:raise ValueError('unsafe/changed D member')
            p=root/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
        for n in list(sys.modules):
            if n in ('experiments','regression') or n.startswith(('experiments.','regression.')):del sys.modules[n]
        sys.path.insert(0,str(root/'source'))
        from regression import arithmetic_function_d as check
        output=root/'data/output';expected=read(output/'parity.json');admission=read(output/'admission.json');base=root/'data/models/asap7_function_D_prototype_v1';bundle=read(base/'bundle.json')
        for n,d in bundle['dependencies'].items():
            if sha((base/d['path']).resolve())!=d['sha256']:raise ValueError('sealed D model changed')
        for n,h in bundle['consumer_sources'].items():
            if sha(root/'source'/n)!=h:raise ValueError('sealed D consumer changed')
        for name,key in [('node','operators'),('S_binding','S_binding'),('composition','composition')]:admission['dependencies'][name]['path']=str((base/bundle['dependencies'][key]['path']).resolve())
        # Paths redirect only to SHA-verified sealed members. No original
        # workspace/model/label path is accessed in the numerical replay.
        check.verify=lambda _:admission
        check.parity(output);actual=read(output/'parity.json')
        for key in ('query_checks','arc_checks','status'):
            if actual[key]!=expected[key]:raise ValueError('D parity totals changed')
        for a,b in zip(actual['cases'],expected['cases'],strict=True):
            for key in ('target_ps','view','candidate','area_um2','violation_ps','status','rtl_sha256'):
                if isinstance(a[key],float):check.close(a[key],b[key])
                elif a[key]!=b[key]:raise ValueError('D selected output changed')
        check.cycles(output);expected_sim=root/'data/expected-simulation'
        for n in ('vectors.hex','all.sv','contract.json'):
            if sha(output/'simulation'/n)!=sha(expected_sim/n):raise ValueError('D RTL fixture changed '+n)
        expected_tb=(expected_sim/'tb.sv').read_text().replace(m['original_output_root'],str(output))
        if expected_tb!=(output/'simulation/tb.sv').read_text():raise ValueError('D simulator contract changed')
        receipt=read(root/'data/simulation-receipt.json')[0]
        if receipt['exit_code'] or 'FUNCTION_D_RTL_PASS targets=5 cycles=256' not in (root/'data/simulation.log').read_text():raise ValueError('missing actual native simulation success')
        partial=read(output/'partial-domain-negative-v2/proof.json')
        if partial['covered']!=32 or partial['uncovered']!=12 or partial['RTL_emitted']:raise ValueError('partial coverage verdict changed')
        if m['full_D_ready'] or m['reset_timing_checked']:raise ValueError('D scope widened')
    print(dict(status='passed_isolated_function_D_replay',cases=5,candidate_evaluations=220,node_queries=actual['query_checks'],arcs=actual['arc_checks'],RTL_fixture_cases=5,reset_timing_checked=False,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('archive','package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path);a=p.parse_args()
    if a.action=='archive':archive(a.root.resolve())
    elif a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
