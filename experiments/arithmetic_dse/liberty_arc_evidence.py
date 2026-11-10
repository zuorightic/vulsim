"""Successor overlay for strict Liberty arc checks on the same eight stages."""
import argparse
import ast
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
from types import FunctionType,ModuleType

ROOT=Path(__file__).resolve().parents[2]
RUN=ROOT/'build/step7-liberty-arc-fix-20261110'
PARENT=Path('experiments/arithmetic/evidence/step7_steps123_v2')
OVERLAY=('experiments/arithmetic_dse/model_physical_labels_v2.py',
    'experiments/arithmetic_dse/model_physical_path_v2.py',
    'regression/arithmetic_liberty_arc_contract.py',
    'experiments/arithmetic_dse/liberty_arc_evidence.py')


def read(path):return json.loads(Path(path).read_text())
def write(path,value):Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def encode(value):return json.dumps(value,sort_keys=True,separators=(',',':')).encode()
def digest(data):return hashlib.sha256(data).hexdigest()
def sha(path):return digest(Path(path).read_bytes())


def load(folder,parent):
    m=read(folder/'manifest.json')
    for name,h in m['parent_files_sha256'].items():
        if Path(name).name!=name or sha(parent/name)!=h:raise ValueError('frozen parent evidence changed '+name)
    data=(folder/'overlay.json.gz').read_bytes()
    if digest(data)!=m['overlay_sha256']:raise ValueError('successor overlay changed')
    for name,h in m['review_sha256'].items():
        if sha(folder/name)!=h:raise ValueError('review receipt changed')
    pool=json.loads(gzip.decompress(data))
    for name,text in pool['sources'].items():
        if digest(text.encode())!=m['source_sha256'][name]:raise ValueError('overlay source differs')
    return m,pool


def pack(folder):
    from .steps123_evidence import load as load_parent
    parent=ROOT/PARENT;_,parent_pool=load_parent(parent)
    sources={name:(ROOT/name).read_text() for name in OVERLAY}
    for name,text in sources.items():ast.parse(text,filename=name)
    old=read(RUN/'reproduce-v1/results/source-sha256.json')
    # The pre-fix readers really are the original publication's bytes.
    for name in OVERLAY[:2]:
        if old[name]!=parent_pool['files'][name]:raise ValueError('reproduction did not use parent readers')
    pool=dict(sources=sources,reproduction=read(RUN/'reproduce-v1/results/proof.json'),
        pre_fix_sources_sha256=old,verification=read(RUN/'readback-v1/results/proof.json'),
        original_eight_checks=read(RUN/'readback-v1/results/original-eight-checks/proof.json'),
        ancestry=dict(parent=str(PARENT),qualification='same four not_training targets and eight saved synth/grt reports',
            no_new_measurements=True))
    data=gzip.compress(encode(pool),mtime=0);folder.mkdir(parents=True,exist_ok=False)
    (folder/'overlay.json.gz').write_bytes(data)
    for name,value in [('verification.json',pool['verification']),('reproduction.json',pool['reproduction'])]:write(folder/name,value)
    write(folder/'manifest.json',dict(version='steps123-liberty-arc-successor-v1',parent=str(PARENT),
        parent_files_sha256={p.name:sha(p) for p in parent.iterdir() if p.is_file()},
        overlay_sha256=digest(data),source_sha256={name:digest(text.encode()) for name,text in sources.items()},
        review_sha256={name:sha(folder/name) for name in ('verification.json','reproduction.json')},
        scope='strict ordinary/output-output cell arc validation; eight original stages, no new EDA or fitted models',
        new_EDA_calls=0,formal_training_rows=0,full_D_ready=False))
    print(dict(status='packed',overlay_bytes=len(data),parent_bytes_reused=True),flush=True)


def old_acceptance(tree,parent_pool,proof):
    """Recompute the recorded defect using exact frozen pre-fix reader bytes."""
    from regression import arithmetic_liberty_arc_contract as contract
    from . import model_qualification_labels as adapter
    modules={}
    for name in ('model_physical_path_v2','model_physical_labels_v2'):
        relative='experiments/arithmetic_dse/'+name+'.py'
        text=parent_pool['blobs'][parent_pool['files'][relative]]
        mod=ModuleType('frozen_'+name);mod.__package__='experiments.arithmetic_dse'
        exec(compile(text,relative,'exec'),mod.__dict__);modules[name]=mod
    modules['model_physical_labels_v2'].timing=modules['model_physical_path_v2']
    ns=dict(adapter.extract.__globals__);ns['parent']=modules['model_physical_labels_v2']
    extract=FunctionType(adapter.extract.__code__,ns)
    ns=dict(contract.through_data.__globals__);ns['timing']=modules['model_physical_path_v2']
    through=FunctionType(contract.through_data.__code__,ns)
    raw,c=contract.packet(tree/'qualification/runs/mul-load-1500','synth')
    for row in proof['single_arc_mutations']:
        w=contract.witness(raw,row['path_kind'])
        if any(row[k]!=v for k,v in w.items()):raise ValueError('pre-fix real buffer witness changed')
        if w['master']!='BUFx2_ASAP7_75t_R' or w['arc']!=['A','Y']:raise ValueError('expected exact A-to-Y reproduction witness')
        broken=contract.remove_arc(raw,w)
        if row['path_kind']=='independent_node':
            if extract(broken,c['nodes'],c['banks'])!=extract(raw,c['nodes'],c['banks']):raise ValueError('old node label acceptance did not reproduce')
        elif through(broken,c)!=through(raw,c):raise ValueError('old Q-to-D acceptance did not reproduce')


def verify(folder,parent,external=False):
    from .steps123_evidence import load as load_parent,restore
    from regression.arithmetic_liberty_arc_contract import check
    m,pool=load(folder,parent);_,previous=load_parent(parent)
    for name,h in m['source_sha256'].items():
        if sha(ROOT/name)!=h:raise ValueError('active successor source differs '+name)
    with tempfile.TemporaryDirectory(prefix='liberty-arc-replay-') as name:
        tree=Path(name);restore(previous,tree)
        old_acceptance(tree,previous,pool['reproduction'])
        # check() uses the verified successor imports and only restored reports.
        proof=check(tree/'qualification',tree/'strict-readback')
        if proof!=pool['verification']:raise ValueError('successor eight-stage proof differs')
        if read(tree/'strict-readback/original-eight-checks/proof.json')!=pool['original_eight_checks']:raise ValueError('original negative checks differ')
        if pool['original_eight_checks']!=json.loads(previous['blobs'][previous['files']['proofs/physical-readback-v1.json']]):raise ValueError('old positive/negative results changed')
    if external:
        for name,meta in previous['external'].items():
            path=Path(name)
            if not path.is_file() or path.stat().st_size!=meta['bytes'] or sha(path)!=meta['sha256']:raise ValueError('original full artifact unavailable/changed '+name)
    result=dict(status='passed',pre_fix_acceptance_reproduced=True,stages=8,all_saved_label_fields_unchanged=True,
        original_negative_checks=8,missing_ordinary_arc_negatives=16,invalid_direction_negatives=2,
        external_parent_artifacts_checked=external,new_EDA_calls=0,new_training_rows=0,full_D_ready=False)
    print(json.dumps(result),flush=True);return result


def isolated(folder,parent,out):
    from .steps123_evidence import load as load_parent,restore
    m,pool=load(folder,parent);_,previous=load_parent(parent)
    out.mkdir(parents=True,exist_ok=False);tree=out/'tree';tree.mkdir();restore(previous,tree)
    for name,text in pool['sources'].items():
        p=tree/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
    shutil.copytree(parent,tree/PARENT);shutil.copytree(folder,tree/'evidence')
    script=tree/'isolate.py';script.write_text('''import os,sys
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root));os.chdir(root)
def audit(event,args):
    if event in ('subprocess.Popen','os.system','os.posix_spawn'):raise RuntimeError('replay subprocess forbidden')
    if event=='open' and isinstance(args[0],(str,bytes)):
        p=Path(os.fsdecode(args[0])).resolve()
        if str(p).startswith('/home/') and not p.is_relative_to(root):raise RuntimeError('original home/project/build forbidden')
sys.addaudithook(audit)
from experiments.arithmetic_dse.liberty_arc_evidence import verify,PARENT
verify(root/'evidence',root/PARENT)
''')
    from .processes import run_command
    env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1')
    record=run_command([sys.executable,'-I','-S',str(script)],out,'isolated',180,env,8192)
    if record['exit_code']:raise ValueError('isolated successor replay failed '+record['log'])
    for kind,path in [('overlay',tree/'evidence/overlay.json.gz'),('parent',tree/PARENT/'pool-000.gzpart')]:
        data=path.read_bytes();changed=bytearray(data);changed[len(changed)//2]^=1;path.write_bytes(changed)
        try:load(tree/'evidence',tree/PARENT)
        except ValueError:pass
        else:raise ValueError('tampered '+kind+' accepted')
        finally:path.write_bytes(data)
    proof=dict(status='passed',original_home_project_build_denied=True,PATH_empty=True,replay_subprocess_denied=True,
        parent_and_overlay_tamper_rejected=True)
    write(out/'proof.json',proof);print(json.dumps(proof),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('pack','verify','isolated'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--parent',type=Path,default=ROOT/PARENT);p.add_argument('--out',type=Path);p.add_argument('--external',action='store_true');a=p.parse_args()
    if a.action=='pack':pack(a.folder.resolve())
    elif a.action=='isolated':isolated(a.folder.resolve(),a.parent.resolve(),a.out.resolve())
    else:verify(a.folder.resolve(),a.parent.resolve(),a.external)
