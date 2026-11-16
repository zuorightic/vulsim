"""Delete only named generated CEC netlist JSONs from five obsolete runs.

Keep final DBs, source RTL, mapped Verilog, proof receipts, reports and logs.
The six JSONs expand the retained netlists; no result or model label is read.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT=Path('/home/zyrv/vulsim')
LIVE=ROOT.parent/'vulsim-artifacts/workload-equivalent-two-depths-v1'
HERE=Path(__file__).resolve().parent
OLD=[ROOT/'build'/n for n in ('step7-MAC-first-20261107','step7-I-exact-20261106',
    'step7-general-state-20261106','step7-general-control-20261106','step7-target-load-20261103')]
NAMES={'gate-flat.json','gold-flat.json','gate-cut.json','gold-cut.json','gate-hier.json','gold-hier.json'}


def read(p):return json.loads(p.read_text())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def stamp(p):
    s=p.lstat()
    return dict(device=s.st_dev,inode=s.st_ino,bytes=s.st_size,blocks=s.st_blocks*512,
        mtime_ns=s.st_mtime_ns,mode=s.st_mode,links=s.st_nlink)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def guard():
    state=read(ROOT/'experiments/arithmetic/backend_usage.json')
    reserved=[e['output'] for e in state['entries'] if e['status']=='reserved' and e.get('output')]
    if any(root==Path(p) or root in Path(p).parents for p in reserved for root in OLD):
        raise ValueError('active backend output in cleanup roots')
    protected=set();manifests=[]
    # Respect all immutable current batches, including reference/resource successors.
    for parent in ('backend','failure-successors','reference-successors'):
        for p in (LIVE/parent).glob('*/freeze.json'):
            protected.update(read(p).get('files',{}));manifests.append(str(p))
    return protected,dict(reserved_outputs=reserved,freeze_manifests=manifests,
        active_jobs=[j for j in state['jobs'] if j['status'] in ('active','unsettled')])


def walk(root):
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[n for n in dirs if not Path(directory,n).is_symlink()]
        yield Path(directory),files


def plan():
    if (HERE/'plan.json').exists():raise ValueError('plan already exists')
    protected,live=guard()
    for root in OLD:
        if root.is_symlink() or not root.is_dir():raise ValueError('invalid old root')
        for directory,files in walk(root):
            for name in files:
                if 'freeze' not in name.lower() or not name.endswith('.json'):continue
                p=directory/name
                if p.is_symlink() or p.stat().st_size>50*1024**2:continue
                try:d=read(p)
                except (ValueError,UnicodeError):continue
                if isinstance(d,dict) and isinstance(d.get('files'),dict):
                    for key in d['files']:
                        q=Path(key);protected.add(str(q if q.is_absolute() else p.parent/q))
    rows=[];kept=0;by_root=Counter()
    with gzip.open(HERE/'retained-evidence-metadata.jsonl.gz','xt') as keep:
        for root in OLD:
            for directory,files in walk(root):
                for name in files:
                    p=directory/name
                    if p.is_symlink():continue
                    s=stamp(p)
                    eligible=(name in NAMES and 'structural_cec' in p.relative_to(root).parts and
                        str(p) not in protected and s['links']==1 and p.resolve()==p and p.is_file())
                    if eligible:
                        rows.append(dict(path=str(p),root=str(root),identity=s,
                            reason='Obsolete CEC expanded netlist cache; retained mapped Verilog and proof/logs.'))
                        by_root[str(root)]+=s['blocks']
                    else:
                        keep.write(json.dumps(dict(path=str(p),identity=s))+'\n');kept+=1
    with gzip.open(HERE/'deletion-plan.jsonl.gz','xt') as out:
        for row in rows:out.write(json.dumps(row)+'\n')
    d=dict(at=datetime.now(timezone.utc).isoformat(),files=len(rows),
        allocated_bytes=sum(r['identity']['blocks'] for r in rows),by_root=dict(by_root),
        roots=list(map(str,OLD)),names=sorted(NAMES),protected_paths=sorted(protected),
        retained_files=kept,plan_sha256=sha(HERE/'deletion-plan.jsonl.gz'),
        retained_sha256=sha(HERE/'retained-evidence-metadata.jsonl.gz'),source_sha256=sha(Path(__file__)),
        live_before=live,free_before=shutil.disk_usage(ROOT).free,
        authorization='User explicitly requests deleting obsolete backend results to free local storage.',
        recovery='Deleted generated CEC cache bytes are not archived; retained netlists and logs remain.')
    write(HERE/'plan.json',d)
    print(json.dumps({k:d[k] for k in ('files','allocated_bytes','by_root','retained_files')},indent=2),flush=True)


def verify_retained():
    count=0
    with gzip.open(HERE/'retained-evidence-metadata.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line)
            if stamp(Path(row['path']))!=row['identity']:raise ValueError('retained evidence changed: '+row['path'])
            count+=1
    return count


def apply():
    if (HERE/'receipt.json').exists() or (HERE/'deleted.jsonl.gz').exists():raise ValueError('cleanup already attempted')
    d=read(HERE/'plan.json');protected,live=guard()
    if d['source_sha256']!=sha(Path(__file__)) or d['plan_sha256']!=sha(HERE/'deletion-plan.jsonl.gz') or d['retained_sha256']!=sha(HERE/'retained-evidence-metadata.jsonl.gz'):
        raise ValueError('cleanup source or manifests changed')
    protected.update(d['protected_paths']);rows=[]
    with gzip.open(HERE/'deletion-plan.jsonl.gz','rt') as stream:
        for line in stream:
            row=json.loads(line);p=Path(row['path']);root=Path(row['root'])
            if (root not in OLD or root not in p.parents or p.name not in NAMES or
                    'structural_cec' not in p.relative_to(root).parts or p.resolve()!=p or
                    str(p) in protected or stamp(p)!=row['identity']):raise ValueError('unsafe cleanup path')
            rows.append(row)
    before=verify_retained()
    with gzip.open(HERE/'deleted.jsonl.gz','xt') as out:
        for row in rows:
            p=Path(row['path'])
            if stamp(p)!=row['identity']:raise ValueError('file changed immediately before unlink')
            p.unlink();out.write(json.dumps(row)+'\n');out.flush()
    after=verify_retained();guard()
    result=dict(at=datetime.now(timezone.utc).isoformat(),deleted_files=len(rows),
        freed_allocated_bytes=sum(r['identity']['blocks'] for r in rows),by_root=d['by_root'],
        retained_checked_before=before,retained_checked_after=after,free_after=shutil.disk_usage(ROOT).free,
        final_DBs_reports_logs_models_and_RTL_untouched=True,live_before=live,
        recovery=d['recovery'],source_sha256=sha(Path(__file__)))
    write(HERE/'receipt.json',result);print(json.dumps(result,ensure_ascii=False,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('plan','apply'));args=parser.parse_args()
    {'plan':plan,'apply':apply}[args.action]()
