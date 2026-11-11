"""Closed-island successor; reuse exact saved census/readouts when unchanged."""
import argparse
from pathlib import Path
import shutil
from types import FunctionType,SimpleNamespace

from . import operator_ownership_replay_v1 as parent,model_logical_ownership_v2 as owners
from .model_fast_preflight import read,write,sha


def prepare(out,node_root,previous):
    namespace=dict(parent.prepare.__globals__)
    namespace['SOURCES']=parent.SOURCES+[Path(__file__),Path(owners.__file__)]
    FunctionType(parent.prepare.__code__,namespace)(out,node_root)
    protocol=read(out/'protocol.json');protocol.update(version='operator-ownership-recovery-replay-v2',
        rule='complete root combinational island, including buffer chains, has exactly one external arithmetic owner; no top/state/clock/unknown neighbour',
        reuse_previous=str(previous),reuse_previous_protocol_sha256=sha(previous/'protocol.json'),reuse_previous_progress_sha256=sha(previous/'progress.json'))
    write(out/'protocol.json',protocol)


def run(out):
    protocol=read(out/'protocol.json');previous=Path(protocol['reuse_previous'])
    if sha(previous/'protocol.json')!=protocol['reuse_previous_protocol_sha256'] or sha(previous/'progress.json')!=protocol['reuse_previous_progress_sha256']:
        raise ValueError('parent report replay changed')
    byid={t['id']:t for t in protocol['tasks']};proofs=[]
    def support(root,name,command,timeout):
        census=name.endswith('-census');task_id=name[:-7] if census else name[:-8]
        if task_id not in byid:raise ValueError('unknown report task')
        task=byid[task_id];old=previous/'tasks'/task_id;dest=out/'tasks'/task_id
        if census:
            parent.assert_immutable(task)
            files=list(old.glob('census_*.tsv'))
        else:
            old_members={n:o for n,o in read(old/'certificate.json')['owners'].items() if o in read(Path(task['folder'])/'query-contract.json')['nodes']}
            new_members={n:o for n,o in read(dest/'certificate.json')['owners'].items() if o in read(Path(task['folder'])/'query-contract.json')['nodes']}
            if new_members!=old_members:return parent.stages.support(root,name,command,timeout)
            files=list(old.glob('logical_context_*.tsv'))
        if not files:raise ValueError('missing reusable reports')
        for p in files:shutil.copy2(p,dest/p.name)
        proofs.append(dict(task=task_id,kind='census' if census else 'readout',old_files={str(p):sha(p) for p in files},same_node_membership=True if not census else None))
        write(out/'reuse-proof.json',dict(version='ownership-report-inheritance-v1',inherited=proofs,no_new_optimization=True))
    namespace=dict(parent.run.__globals__);namespace.update(owners=owners,stages=SimpleNamespace(support=support))
    FunctionType(parent.run.__code__,namespace)(out)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--out',type=Path,required=True);p.add_argument('--node-root',type=Path);p.add_argument('--previous',type=Path)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve(),a.node_root.resolve(),a.previous.resolve())
    else:run(a.out.resolve())
