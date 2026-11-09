"""Accounted local bit-wiring inventory with portable static-graph replay."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse import model_fast_loads as loads
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def wiring_checks():
    # Non-arithmetic wiring fixture: shifted producer bits, explicit truncation,
    # concatenation ordering, and an unrelated source remain distinguishable.
    def node(at,op,width,args=(),kind='none',**kw):
        return dict(id=at,operation=op,width=width,operands=list(args),wiring_kind=kind,
                    constant=False,known_zero_hex=['0'],known_one_hex=['0'],**kw)
    def symbol(at,width):
        return dict(kind='symbol',node=at,width=width,signed=False)
    nodes={0:node(0,'mul',4),1:node(1,'input',4),
           2:node(2,'wire',8,[symbol(0,4)],'zext'),
           3:node(3,'wire',6,[symbol(2,8)],'slice',lo=1,hi=6),
           4:node(4,'wire',8,[symbol(0,4),symbol(1,4)],'concat'),
           5:node(5,'wire',1,[symbol(0,4)],'bit_select',bit=2)}
    expected={2:[(0,0),(0,1),(0,2),(0,3),'0','0','0','0'],
              3:[(0,1),(0,2),(0,3),'0','0','0'],
              4:[(1,0),(1,1),(1,2),(1,3),(0,0),(0,1),(0,2),(0,3)],5:[(0,2)]}
    for at,want in expected.items():
        if loads.bit_origins(nodes,at)!=want:
            raise ValueError('incorrect static bit position or concat ordering')
    nodes[0]['known_zero_hex']=['5'];nodes[0]['known_one_hex']=['8']
    if loads.bit_origins(nodes,0)!=['0',(0,1),'0','1']:
        raise ValueError('known bit positions were lost')
    failures=[]
    for name,at,mutate in (
        ('cycle',2,lambda:nodes[2]['operands'][0].update(node=2)),
        ('dynamic_selection',5,lambda:nodes[5].update(bit=-1)),
        ('slice_width',3,lambda:nodes[3].update(hi=5))):
        original=json.loads(json.dumps(nodes))
        mutate()
        try:loads.bit_origins(nodes,at)
        except ValueError:failures.append(name)
        else:raise ValueError('invalid static wiring accepted')
        nodes={int(k):v for k,v in original.items()}
    return dict(checks=5,negative_checks=failures,physical_measurements=False)


def verify(folder,evidence=None):
    graph=json.loads(gzip.decompress((folder/'static-graphs.json.gz').read_bytes()))
    replay=loads.contexts(graph);saved=read(folder/'loads.json')
    for name,value in replay.items():
        if value!=saved[name]:
            raise ValueError('exact static load inventory does not replay: '+name)
    producer_bits=consumer_bindings=captures=0
    for row in saved['contexts'].values():
        spec=row['features']['producer'];producer_bits+=spec['result_width']
        for consumer in row['features']['consumers']:
            for binding in consumer['bindings']:
                width=consumer['spec'][('lhs_width','rhs_width')[binding['operand_index']]]
                if len(binding['result_bit_map'])!=width:
                    raise ValueError('consumer bit map does not cover actual operand width')
                if any(type(b) is int and not 0<=b<spec['result_width'] for b in binding['result_bit_map']):
                    raise ValueError('consumer map refers to an undemanded producer bit')
                consumer_bindings+=1
        for capture in row['features']['captures']:
            if len(capture['result_bit_map'])!=capture['declared_width']:
                raise ValueError('capture bit map does not cover actual width')
            captures+=1
    proof=dict(status='passed',contexts=saved['local_context_count'],legacy_contexts=saved['legacy_context_count'],
               consumer_bindings=consumer_bindings,capture_maps=captures,**wiring_checks(),PPA_calls=0,
               physical_admission_allowed=False,full_D_ready=False)
    write(folder/'proof.json',proof)
    if evidence:
        evidence.mkdir(parents=True,exist_ok=False)
        for name in ('loads.json','proof.json','static-graphs.json.gz'):
            shutil.copy2(folder/name,evidence/name)
        source_paths=[Path(__file__),Path(loads.__file__),ROOT/'experiments/arithmetic_dse/model_fast_preflight.py',ROOT/'experiments/arithmetic_dse/model_fast_samples.py']
        pool={str(p.relative_to(ROOT)):p.read_text() for p in source_paths}
        (evidence/'sources.json.gz').write_bytes(gzip.compress(json.dumps(pool,sort_keys=True).encode(),mtime=0))
        write(evidence/'manifest.json',dict(files_sha256={p.name:sha(p) for p in evidence.iterdir() if p.is_file()},
              source_sha256={str(p.relative_to(ROOT)):sha(p) for p in source_paths},PPA_calls=0))
    print(json.dumps(proof),flush=True)


def run(out,native,requirements,evidence):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path)
    ctx=dict(target_platform='asap7',admission_id=out.name,task_id='fast-exact-local-load-inventory')
    command=[sys.executable,'-B','-m','experiments.arithmetic_dse.model_fast_loads','--native',str(native),
             '--requirements',str(requirements),'--out',str(out/'inventory')]
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4');commands=[]
    def execute(cmd,name):
        r=ledger.reserve(None,180,4,'fast_exact_local_load_software',cmd,out/name,context=ctx)
        record=run_command(cmd,out,name,180,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
        commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'commands.json',commands)
        print(Path(record['log']).read_text()[-3000:],flush=True)
        if record['exit_code']:raise RuntimeError('local load software failed; costs retained')
    try:
        with ledger.job(ctx):
            execute(command,'inventory')
            index=read(native/'index.json');graphs=[read(native/c['file']) for case in index['cases'] for c in case['candidates']]
            (out/'inventory/static-graphs.json.gz').write_bytes(gzip.compress(json.dumps(graphs,sort_keys=True).encode(),mtime=0))
            execute([sys.executable,'-B',str(Path(__file__)),'verify','--out',str(out/'inventory'),'--evidence',str(evidence)],'verify')
    finally:
        after=read(ledger.path);increment=after['entries'][len(before['entries']):]
        write(out/'resource-increment.json',dict(entries=increment,usage=usage(after['entries']),PPA_calls=0))
    write(evidence/'publication-closure.json',dict(manifest_sha256=sha(evidence/'manifest.json'),entries=increment,usage=usage(after['entries']),PPA_calls=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','verify'));p.add_argument('--out',type=Path,required=True)
    p.add_argument('--native',type=Path);p.add_argument('--requirements',type=Path);p.add_argument('--evidence',type=Path);a=p.parse_args()
    if a.action=='run':
        if not a.native or not a.requirements or not a.evidence:p.error('--native,--requirements,--evidence required')
        run(a.out.resolve(),a.native.resolve(),a.requirements.resolve(),a.evidence.resolve())
    else:verify(a.out.resolve(),a.evidence.resolve() if a.evidence else None)
