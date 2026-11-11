"""Finite new-source recovery; inherited successes never rerun or relabel.

Only the two repaired input-consuming sources are admitted. Once measured,
their six rows join the eighteen original successful source/T rows under the
prospective successor protocol. Old six census failures stay in denominator.
"""
import argparse
import inspect
from pathlib import Path
from .model_fast_preflight import read,write,sha
from . import stage67_shared_collect_v1 as base
from .stage67_shared_prepare_v2 import RENAMES


def admit(root,preparation):
    text=inspect.getsource(base.admit)
    text=text.replace("if row['role']!=role:continue", "if row['role']!=role or row['source'] not in ('train_r24_disjoint','train_r32_disjoint'):continue")
    text=text.replace("if len(tasks)!=(24 if role=='train' else 9)","if len(tasks)!=6")
    if text==inspect.getsource(base.admit):raise ValueError('recovery admission callsite drift')
    ns=dict(base.admit.__globals__);exec(compile(text,__file__,'exec'),ns);ns['admit'](root,preparation,'train')


def merge(original,repaired,protocol,out):
    if out.exists():raise ValueError('preserve merged data')
    a=read(original);b=read(repaired);p=read(protocol)
    if len(a['rows'])!=18 or len(b['rows'])!=6 or len(a['excluded_failed_requests'])!=6:raise ValueError('exact inherited/repaired source split differs')
    rows=a['rows']+b['rows'];expected={(x['source'],x['target_ps']) for x in p['train_requests']}
    if {(r['source'],r['target_ps']) for r in rows}!=expected or len(rows)!=len(expected) or any(r['role']!='train' for r in rows):raise ValueError('successor source/role coverage differs')
    write(out,dict(version='shared-compatible-merged-train-v1',rows=rows,protocol_sha256=sha(protocol),inherited_rows=18,new_rows=6,
        parent_datasets=[dict(path=str(n),sha256=sha(n)) for n in (original,repaired)],old_failed_requests=a['excluded_failed_requests'],
        old_failed_requests_removed_from_history=False,old_successful_snapshots_remeasured=False,full_D_ready=False))
    print('SHARED_SUCCESSOR_TRAIN_MERGED rows=24 inherited=18 new=6 old_failures=6',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','merge'));p.add_argument('--root',type=Path);p.add_argument('--preparation',type=Path)
    for n in ('original','repaired','protocol','out'):p.add_argument('--'+n,type=Path)
    a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.preparation.resolve())
    else:merge(a.original.resolve(),a.repaired.resolve(),a.protocol.resolve(),a.out.resolve())
