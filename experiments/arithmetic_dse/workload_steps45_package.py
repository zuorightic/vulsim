"""Portable byte-bound evidence, with large native working files kept outside Git."""
import argparse
import base64
import gzip
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .sampling_time_contract import ROOT,canonical,sha
from .workload_equivalent_run import read,write,compressed
from .workload_reuse_validation import BASE,DEFAULT

CHUNK=3*1024*1024


def chunk(root,stem,raw):
    chunks=[]
    for i,at in enumerate(range(0,len(raw),CHUNK)):
        name=f'{stem}-{i:03d}.gzpart';data=raw[at:at+CHUNK];(root/name).write_bytes(data)
        chunks.append(dict(file=name,bytes=len(data),sha256=sha(data)))
    write(root/(stem+'-manifest.json'),dict(chunks=chunks,bytes=len(raw),sha256=sha(raw)))


def unchunk(root,stem):
    root=Path(root);m=read(root/(stem+'-manifest.json'));parts=[]
    for item in m['chunks']:
        raw=(root/item['file']).read_bytes()
        if len(raw)!=item['bytes'] or sha(raw)!=item['sha256']:raise ValueError('evidence chunk changed')
        parts.append(raw)
    raw=b''.join(parts)
    if len(raw)!=m['bytes'] or sha(raw)!=m['sha256']:raise ValueError('combined evidence changed')
    return raw


def replay_data(root):
    root=Path(root);p=root/'search-replay-inputs.json.gz'
    raw=p.read_bytes() if p.exists() else unchunk(root,'replay-input')
    return json.loads(gzip.decompress(raw)),sha(raw)


def artifact_files(root,rows):
    root=Path(root)
    if (root/'native-artifacts-manifest.json').exists():
        raw=unchunk(root,'native-artifacts');payload=json.loads(gzip.decompress(raw))
        files={name:base64.b64decode(data,validate=True) for name,data in payload['files'].items()}
        # Score files are exactly derivable from the frozen replay rows. Avoid
        # storing the same complete traces twice in a portable payload.
        for row in rows:files['scores/'+row['id']+'.json.gz']=gzip.compress(canonical(row),mtime=0)
        return files
    return {str(p.relative_to(root/'search')):p.read_bytes() for p in (root/'search').rglob('*') if p.is_file()}


def pack(root=DEFAULT,work=None):
    root=Path(root).resolve();work=Path(work or ROOT.parent/'vulsim-artifacts/workload-equivalent-steps45-v1').resolve()
    work.mkdir(exist_ok=False)
    data,identity=replay_data(root);manifest=read(root/'search/manifest.json')
    if identity!=manifest['replay_inputs_sha256']:raise ValueError('replay inputs changed before packaging')
    files={};derived=0
    for name,expected in manifest['files'].items():
        raw=(root/'search'/name).read_bytes()
        if sha(raw)!=expected:raise ValueError('native artifact changed before packaging')
        if name.startswith('scores/'):
            derived+=1;continue
        files[name]=base64.b64encode(raw).decode()
    files['manifest.json']=base64.b64encode((root/'search/manifest.json').read_bytes()).decode()
    chunk(root,'native-artifacts',gzip.compress(canonical(dict(version='steps45-native-portable-v1',files=files)),mtime=0))
    chunk(root,'replay-input',(root/'search-replay-inputs.json.gz').read_bytes())
    sources={str(p.relative_to(ROOT)):p.read_text() for p in sorted((ROOT/'experiments/arithmetic_dse').glob('*.py'))}
    for p in (ROOT/'regression').glob('test_workload*.py'):sources[str(p.relative_to(ROOT))]=p.read_text()
    sources['rtlzz/main/arithmetic_workload.cpp']=(ROOT/'rtlzz/main/arithmetic_workload.cpp').read_text()
    compressed(root/'software-source.json.gz',sources)
    shutil.copyfile(BASE/'diagnostic-model.json',root/'diagnostic-model.json')
    shutil.copyfile(BASE/'characterization-contract.json',root/'characterization-contract.json')
    # Reversible relocation keeps complete failed attempts and successful native
    # working files, while the checked-in archive remains byte-portable.
    for path in sorted(root.glob('search-attempt*')):shutil.move(str(path),work/path.name)
    shutil.move(str(root/'search'),work/'search')
    shutil.move(str(root/'search-replay-inputs.json.gz'),work/'search-replay-inputs.json.gz')
    (root/'search').mkdir()
    for name in ('summary.json','search-events.json','manifest.json','execution-inputs.json','response-receipts.json.gz'):
        shutil.copyfile(work/'search'/name,root/'search'/name)
    for t in (500,750,1000):shutil.copytree(work/'search'/f'T{t}-selected',root/'search'/f'T{t}-selected')
    write(root/'artifact-location.json',dict(version='steps45-portable-evidence-v1',working_root=str(work),
        working_tree_required_for_replay=False,large_files_moved_not_deleted=True,
        artifact_manifest='search/manifest.json',native_pool='native-artifacts-manifest.json',
        replay_input_pool='replay-input-manifest.json',derived_score_files=derived,
        compiler_binary=str(ROOT/'build/workload-v10-20261115/rtlzz-workload'),
        source_sha256=sha((root/'software-source.json.gz').read_bytes())))
    return dict(status='portable_package_complete',working_root=str(work),derived_score_files=derived,
                native_members=len(files),source_files=len(sources))


def restore(root,dest):
    root=Path(root);dest=Path(dest);dest.mkdir(exist_ok=False)
    data,_=replay_data(root);files=artifact_files(root,data['rows'])
    for name,raw in files.items():
        p=dest/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
    return dict(status='native_artifacts_restored',files=len(files),destination=str(dest))


def isolated_replay(root=DEFAULT):
    root=Path(root).resolve();sources=read(root/'software-source.json.gz')
    with tempfile.TemporaryDirectory(prefix='vulsim-steps45-isolated-') as tmp:
        isolated=Path(tmp)
        for name,source in sources.items():
            p=isolated/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(source)
        ev=isolated/'experiments/arithmetic/evidence/workload_equivalent_steps45_v1';ev.mkdir(parents=True)
        for p in root.iterdir():
            if p.is_file():shutil.copyfile(p,ev/p.name)
        shutil.copytree(root/'validation',ev/'validation');shutil.copytree(root/'search',ev/'search')
        shutil.copytree(root/'selected',ev/'selected-reference')
        # Existing modules refer to the previous freeze by a repository-relative
        # path. Supply only its immutable numerical inputs, no old application
        # reports, original native exports, or final application PPA.
        old=ev.parent/'workload_equivalent_mac32_v1';old.mkdir()
        for name in ('diagnostic-model.json','characterization-contract.json'):shutil.copyfile(root/name,old/name)
        script='''import builtins,json,os,subprocess
from pathlib import Path
from unittest.mock import patch
from experiments.arithmetic_dse.workload_reuse_validation import DEFAULT,run
from experiments.arithmetic_dse.workload_guided_search import replay
from experiments.arithmetic_dse.workload_steps45_audit import audit,publish_selection
from experiments.arithmetic_dse.workload_equivalent_run import read
from experiments.arithmetic_dse.sampling_time_contract import sha
original_open=builtins.open;original_os_open=os.open
def check(path):
    if isinstance(path,(str,bytes,os.PathLike)):
        value=os.fsdecode(path)
        if value.startswith('/home/zyrv/vulsim'):raise AssertionError('original workspace/artifacts read: '+value)
def guarded_open(path,*args,**kw):check(path);return original_open(path,*args,**kw)
def guarded_os_open(path,*args,**kw):check(path);return original_os_open(path,*args,**kw)
with patch('builtins.open',guarded_open),patch('io.open',guarded_open),patch('os.open',guarded_os_open),patch('subprocess.Popen',side_effect=AssertionError('subprocess forbidden')):
    expected=read(DEFAULT/'validation/manifest.json')
    run(DEFAULT,output=DEFAULT/'validation-replay')
    actual=read(DEFAULT/'validation-replay/manifest.json')
    if expected!=actual:raise AssertionError('step4 full table replay differs')
    detail={n:sha((DEFAULT/'validation'/n).read_bytes()) for n in ('detail-gates.json.gz','detail-summary.json')}
    audit(DEFAULT)
    if any(sha((DEFAULT/'validation'/n).read_bytes())!=h for n,h in detail.items()):raise AssertionError('supplemental gate replay differs')
    result=replay(DEFAULT)
    publish_selection(DEFAULT)
    selected=read(DEFAULT/'selected/manifest.json')
    if selected!=read(DEFAULT/'selected-reference/manifest.json'):raise AssertionError('common-pool selection identity differs')
    result.update(validation_result_files=len(expected['files']),supplemental_files=len(detail),
        selected_artifacts=len(selected['files']),
        original_workspace_reads_blocked=True,subprocesses_blocked=True,source_restored_from_archive=True)
print(json.dumps(result,sort_keys=True))
'''
        process=subprocess.run([sys.executable,'-B','-c',script],cwd=isolated,text=True,
            stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=1800)
        if process.returncode:
            (root/'isolated-replay-failure.log').write_text(process.stdout)
            raise RuntimeError('isolated replay failed; see isolated-replay-failure.log')
        result=json.loads(process.stdout);write(root/'isolated-replay.json',result)
        return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['pack','restore','replay']);p.add_argument('--root',type=Path,default=DEFAULT)
    p.add_argument('--destination',type=Path);args=p.parse_args()
    value=pack(args.root) if args.action=='pack' else restore(args.root,args.destination) if args.action=='restore' else isolated_replay(args.root)
    print(json.dumps(value,indent=2))
