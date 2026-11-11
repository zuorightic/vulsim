"""Compact train/consumer/validation successor evidence; no new metrology."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import statistics
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve state/shared package attempt')
    evidence.mkdir(parents=True);pool={}
    def add(name,path):pool[name]=Path(path).read_text()
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):add('source/'+str(p.relative_to(ROOT)),p)
    for n in ('rtlzz/src/backend/arithmetic_factored_timing.cpp','rtlzz/src/backend/arithmetic_factored_timing.hpp',
        'rtlzz/testv2/arithmetic_factored_timing_consumer.cpp','rtlzz/testv2/arithmetic_factored_mac32.cpp','regression/arithmetic_state_shared.py'):
        add('source/'+n,ROOT/n)
    for n,p in {
        'release/policy.json':root/'derivation-v5/candidate.json','release/old-policy.json':Path('/home/zyrv/vulsim-artifacts/stage67-accounting-20261111-v1/validation-initial/candidate-calibrated.json'),
        'release/operators.json':ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json',
        'release/S.json':Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/reused-S.json'),
        'expected/native.json':root/'native-v1/native.json','expected/parity.json':root/'parity-v1/parity.json',
        'expected/validation.json':root/'validation-v1/validation.json','expected/qualification.json':root/'qualification-v1/proof.json',
        'expected/root-witness.json':root/'qualification-v1/witness.json','expected/freeze.json':root/'candidate-freeze.json',
        'expected/mac32-demand.json':root/'mac32-demand-v1/proof.json',
        'expected/negative-controls.json':root/'negative-v1/proof.json',
    }.items():add(n,p)
    audit=read(root/'derivation-v5/training-audit.json')
    compact={k:v for k,v in audit.items() if k!='area_rows'}
    compact['area_rows']=[{k:v for k,v in row.items() if k!='root_proof'}|dict(full_root_proof_sha256=hashlib.sha256(json.dumps(row['root_proof'],sort_keys=True,separators=(',',':')).encode()).hexdigest()) for row in audit['area_rows']]
    pool['training/fit-packet.json']=json.dumps(compact,indent=2,ensure_ascii=False)+'\n'
    packets=read(root/'validation-packets.json');roles=[]
    for record in packets['packets']:
        if sha(record['labels'])!=record['labels_sha256']:raise ValueError('validation input label changed')
        name='validation/'+record['source']+'-'+record['placement']+'.json';add(name,record['labels']);roles.append(dict(record,labels=name))
    pool['validation/packets.json']=json.dumps(dict(packets=roles,independent_tests_read=False),indent=2)+'\n'
    # Exact raw extraction/failed attempts are retained outside the compact
    # tier. Compact replay reproduces fitting from certified train scalars
    # and one full real connectivity witness, not every old training ODB.
    from .operator_stage4 import archive
    (root.parent/'restore').mkdir(exist_ok=True);receipt=archive(root.parent,[root],'stage67-state-shared-20261111-v1.tar.gz')
    write(evidence/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(member_count=len(receipt['members'])))
    raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    shutil.copy2(Path(__file__),evidence/'replay.py');files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};index=evidence/'file-index.json.gz';index.write_bytes(gzip.compress(json.dumps(files,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    freeze=read(root/'candidate-freeze.json')
    write(evidence/'manifest.json',dict(version='state-shared-successor-evidence-v1',chunks=chunks,file_index=dict(name=index.name,sha256=sha(index),members=len(files)),
        payload_sha256=hashlib.sha256(raw).hexdigest(),replay_sha256=sha(evidence/'replay.py'),policy_sha256=sha(root/'derivation-v5/candidate.json'),
        node_model_sha256=sha(ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'),
        source_sha256={n.removeprefix('source/'):files[n] for n in pool if n.startswith('source/')},
        full_training_audit_sha256=sha(root/'derivation-v5/training-audit.json'),freeze_sha256=sha(root/'candidate-freeze.json'),
        validation_status='failed_joint_validation',zero_G_joint_qualified=False,full_D_ready=False,new_physical_calls=0))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('state/shared compact evidence exceeds size limits')
    print(dict(status='sealed_state_shared_successor_evidence',members=len(pool),evidence_bytes=sum(sizes)),flush=True)


def close_numeric(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(close_numeric(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close_numeric(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)
    return a==b


def replay(evidence):
    m=read(evidence/'manifest.json');index=evidence/m['file_index']['name']
    if sha(index)!=m['file_index']['sha256'] or sha(evidence/'replay.py')!=m['replay_sha256']:raise ValueError('changed index or replay')
    files=json.loads(gzip.decompress(index.read_bytes()));compressed=b''
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('changed evidence chunk')
        compressed+=(evidence/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('changed payload')
    pool=json.loads(raw)
    if set(pool)!=set(files) or len(files)!=m['file_index']['members']:raise ValueError('changed restored inventory')
    with tempfile.TemporaryDirectory(prefix='state-shared-isolated-') as directory:
        root=Path(directory)
        for n,value in pool.items():
            p=Path(n)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=files[n]:raise ValueError('unsafe or changed member')
            d=root/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_text(value)
        for n in list(sys.modules):
            if n in ('experiments','regression') or n.startswith(('experiments.','regression.')):del sys.modules[n]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse.stage67_state_shared_train_v1 import fit_shared,trace_roots,primitive_areas
        from experiments.arithmetic_dse.stage67_factored_timing_v1 import compare
        from experiments.arithmetic_dse.stage67_state_shared_validate_v1 import evaluate
        from experiments.arithmetic_dse.model_physical_path_v2 import verify_combinational_arc
        policy=read(root/'release/policy.json');audit=read(root/'training/fit-packet.json');groups=defaultdict(lambda:defaultdict(list))
        if sha(root/'release/policy.json')!=m['policy_sha256'] or sha(root/'release/operators.json')!=m['node_model_sha256'] or audit['validation_labels_read']:raise ValueError('changed frozen dependency or role')
        if any(r['role']!='train' for r in audit['area_rows']+audit['path_rows']):raise ValueError('nontrain fitting row')
        models=fit_shared(audit['area_rows'])
        if not close_numeric(models,policy['shared_area_models']):raise ValueError('fixed NNLS parameter replay differs')
        for row in audit['path_rows']:
            removed=math.fsum(s['delay_ps'] for s in row['segments'] if s['excluded_instrumentation'])
            if not math.isclose(row['full_required_period_ps']-removed,row['value_ps'],abs_tol=1e-8):raise ValueError('boundary ownership sum differs')
            groups[row['boundary_role']][row['source']].append(row['value_ps'])
        for role,values in groups.items():
            if policy['boundary_point_ps'][role]!=statistics.median(statistics.median(v) for v in values.values()):raise ValueError('source-balanced boundary differs')
        if policy['forward_boundary_point_ps']['input_service->native_state']!=policy['boundary_point_ps']['native_state->native_state']:raise ValueError('typed forwarding class differs')
        witness=read(root/'expected/root-witness.json')
        if trace_roots(witness['instances'],witness['liberty'],witness['nets'],witness['owners'])!=witness['expected_root_proof'] or primitive_areas(witness['liberty'])!=audit['primitive_baseline']:raise ValueError('real full root-census witness differs')
        compare(root/'expected/native.json',root/'release/policy.json',root/'release/operators.json',root/'release/S.json',root/'parity')
        if not close_numeric(read(root/'parity/parity.json'),read(root/'expected/parity.json')):raise ValueError('native parity replay differs')
        packets=read(root/'validation/packets.json')
        for r in packets['packets']:r['labels']=str(root/r['labels'])
        write(root/'packets.json',packets)
        evaluate(root/'expected/native.json',root/'release/policy.json',root/'release/operators.json',root/'release/S.json',root/'packets.json',root/'validated')
        if not close_numeric(read(root/'validated/validation.json'),read(root/'expected/validation.json')):raise ValueError('frozen validation replay differs')
        final=read(root/'validated/validation.json')
        if final['failures']!=['root_repair/owner_area_error','shared_clock/owner_area_error'] or final['full_D_ready']:raise ValueError('failed verdict changed')
        demand=read(root/'expected/mac32-demand.json');refusals=sum(v['estimate']['status']!='candidate_covered' for t in demand['targets'] for v in t['views'])
        if refusals!=demand['uncovered'] or demand['full_D_ready']:raise ValueError('actual D coverage record differs')
    print(dict(status='passed_isolated_state_shared_successor_replay',train_area_rows=len(audit['area_rows']),train_paths=len(audit['path_rows']),
        validation_stages=12,requests=36,MAC32_coverage=(demand['covered'],demand['uncovered']),two_joint_failures_preserved=True,new_physical_calls=0,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
