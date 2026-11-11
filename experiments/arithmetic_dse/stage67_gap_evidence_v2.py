"""Portable evidence for reset failure and successful state-alias qualification.

No external paths are needed for replay. Native numerical outputs are sealed
and compared with Python; full EDA snapshots stay in a restored raw archive.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve gap evidence')
    pool={}
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):pool['source/'+str(p.relative_to(ROOT))]=p.read_text()
    pool['source/regression/arithmetic_steps123.py']=(ROOT/'regression/arithmetic_steps123.py').read_text()
    names=['reset-train-v3/dataset.json','reset-fit-protocol-v2/dataset.json','reset-validation-v3/dataset.json',
        'reset-fit-v1/candidate.json','reset-fit-v1/training.json','reset-fit-v2/candidate.json','reset-fit-v2/training.json','reset-fit-v2/validation.json',
        'reset-parity-v2/queries.json','reset-parity-v2/native-stdout.json','reset-parity-v2/parity.json',
        'shared-alias-qualification-v5/qualification.json','shared-alias-projection-v1.json','shared-load-audit-v1.json','shared-continuation-v1/progress.json',
        'archives/gap-raw-v1.tar.gz.index.json']
    for n in names:pool['data/'+n]=(root/n).read_text()
    for label,folder in [('train',root/'reset-train-v3/readout/train_p16-T500'),('validation',root/'reset-validation-v3/readout/validation_p20-T500')]:
        for name in ('ownership.json','targets.json','endpoints.tsv','worst.tsv','input_service-points.tsv','native_state-points.tsv','external_state-points.tsv'):
            pool['reset-witness/'+label+'/'+name]=(folder/name).read_text()
    from .stage67_mapped_state_v1 import flatten
    for i,t in enumerate(read(root/'shared-probe/admission.json')['tasks']):
        d=root/'shared-probe/runs'/t['id'];pins=read(d/'liberty-pins.json');design=read(d/'mapped.json');models=read(d/'logs/asap7/arithmetic_probe/base/structural_cec/gold-hier.json')['modules']
        prefix='alias-witness/'+str(i)+'/'
        for n in ('mapped.json','liberty-pins.json','mapped-state.json'):pool[prefix+n]=(d/n).read_text()
        pool[prefix+'input.sv']=Path(t['rtl']).read_text();pool[prefix+'contract.json']=Path(t['endpoint_contract']).read_text();pool[prefix+'source.json']=(Path(t['input_directory'])/'source.json').read_text()
        pool[prefix+'logs/asap7/arithmetic_probe/base/structural_cec/gold-hier.json']=json.dumps(dict(modules={n:models[n] for n in {c['type'] for c in flatten(design,pins)[0].values()} if pins[n]['sequential']}))
        pool[prefix+'CEC-proof.json']=(d/'logs/asap7/arithmetic_probe/base/structural_cec/proof.json').read_text()
    evidence.mkdir(parents=True);raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    index={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};p=evidence/'file-index.json.gz';p.write_bytes(gzip.compress(json.dumps(index,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    shutil.copy2(Path(__file__),evidence/'replay.py');write(evidence/'manifest.json',dict(version='reset-alias-gap-evidence-v2',members=len(pool),chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        file_index_sha256=sha(p),replay_sha256=sha(evidence/'replay.py'),reset_status=read(root/'reset-fit-v2/validation.json')['status'],
        aliases='exact Boolean proofs plus CEC receipts; production S/node support unchanged',native_scope='sealed actual C++ outputs compared against Python, binary execution not replayed',full_D_ready=False))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('gap compact evidence limit')
    print('GAP_EVIDENCE_SEALED members='+str(len(pool))+' bytes='+str(sum(sizes)),flush=True)


def close(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)
    return a==b


def reset_witness(folder):
    from experiments.arithmetic_dse.stage67_physical_readout_v4 import table
    from experiments.arithmetic_dse.stage67_analyze_v1 import verify_ownership_packet,path_partition
    owners=read(folder/'ownership.json');verify_ownership_packet(owners);expected=read(folder/'targets.json');actual={k:{} for k in expected}
    for row in table(folder/'endpoints.tsv'):
        if row['endpoint'] in actual[row['owner']]:raise ValueError('duplicate actual reset endpoint')
        actual[row['owner']][row['endpoint']]=float(row['slack'])
    if any(set(actual[k])!=set(v) for k,v in expected.items()):raise ValueError('reset all-endpoint census incomplete')
    for worst in table(folder/'worst.tsv'):
        if float(worst['slack'])!=min(actual[worst['owner']].values()):raise ValueError('reset minimum differs')
        points=[row.split('\t') for row in (folder/worst['points']).read_text().splitlines()];path_partition(points,owners,['rstn'],worst['endpoint'])
    return sum(len(v) for v in actual.values())


def replay(evidence):
    m=read(evidence/'manifest.json')
    if sha(evidence/'replay.py')!=m['replay_sha256'] or sha(evidence/'file-index.json.gz')!=m['file_index_sha256']:raise ValueError('changed replay/index')
    compressed=b''
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('changed gap chunk')
        compressed+=(evidence/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('changed gap payload')
    pool=json.loads(raw);index=json.loads(gzip.decompress((evidence/'file-index.json.gz').read_bytes()))
    if set(pool)!=set(index) or len(pool)!=m['members']:raise ValueError('changed member inventory')
    with tempfile.TemporaryDirectory(prefix='reset-alias-replay-') as tmp:
        root=Path(tmp)
        for n,value in pool.items():
            p=Path(n)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=index[n]:raise ValueError('unsafe/changed member')
            p=root/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(value)
        for n in list(sys.modules):
            if n=='experiments' or n.startswith('experiments.'):del sys.modules[n]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse.stage67_shared_model_v1 import fit_models
        from experiments.arithmetic_dse import stage67_reset_model_v1 as old,stage67_reset_model_v2 as reset
        data=root/'data';train=read(data/'reset-fit-protocol-v2/dataset.json');model=read(data/'reset-fit-v2/candidate.json');validation=read(data/'reset-validation-v3/dataset.json')
        fitted=fit_models([dict(r,labels=dict(reset=r['reset_required_ps'])) for r in train['rows']],dict(reset=reset.TRAIN_FEATURES))['reset']
        if not close(fitted['coefficients'],model['coefficients']):raise ValueError('reset train refit differs')
        guard=max(0.,max(r['reset_required_ps']-reset.predict(model,r['features']['total_FF_bits'],r['features']['reset_one_bits'],r['target_ps'])['point_intrinsic_ps'] for r in train['rows']))+25.
        if not math.isclose(guard,model['upper_guard_ps'],abs_tol=1e-8):raise ValueError('reset frozen guard differs')
        result=reset.evaluate(model,validation);saved=read(data/'reset-fit-v2/validation.json')
        for k,v in result.items():
            if not close(v,saved[k]):raise ValueError('reset validation verdict differs '+k)
        initial=old.evaluate(read(data/'reset-fit-v1/candidate.json'),read(data/'reset-train-v3/dataset.json'))
        if initial['failures']!=['point_error'] or result['failures']!=['point_error']:raise ValueError('failed result hidden')
        for q,a in zip(read(data/'reset-parity-v2/queries.json'),read(data/'reset-parity-v2/native-stdout.json')):
            try:p=reset.predict(model,q['total_FF_bits'],q['reset_one_bits'],q['target_ps'],q['native_depth'])
            except ValueError:
                if a['covered']:raise ValueError('sealed native rejection differs')
                continue
            if not a['covered'] or any(not close(p[k],a[k]) for k in ('point_intrinsic_ps','guard_intrinsic_ps','required_period_ps','violates')):raise ValueError('sealed native prediction differs')
        endpoint_checks=sum(reset_witness(root/'reset-witness'/n) for n in ('train','validation'))
        from experiments.arithmetic_dse.stage67_pure_alias_v2 import verify,semantics
        from experiments.arithmetic_dse.stage67_alias_projection_v1 import project
        counts=[]
        for i in range(2):
            d=root/'alias-witness'/str(i);rtl=(d/'input.sv').read_text();c=read(d/'contract.json');s=verify(read(d/'mapped.json'),read(d/'liberty-pins.json'),c,read(d/'source.json'),rtl)
            if not close(s['words'],read(d/'mapped-state.json')['words']):raise ValueError('actual alias census differs')
            proof=semantics(d,s,rtl,c);projection=project(rtl,c);actual={r['cell'] for w in s['words'] if w['owner']=='native_state' and not w['valid'] for r in w['rows'] if 'cell' in r}
            if projection['native_unique_data_bits']!=len(actual):raise ValueError('prediction-time alias count differs')
            counts.append(dict(logical=s['logical_FF_bit_references'],physical=s['unique_physical_FF_bits'],Boolean=proof['checked_FF_bits']))
        if saved['full_D_ready'] or m['full_D_ready']:raise ValueError('qualification widened')
    print(dict(status='passed_isolated_reset_alias_replay',train=24,validation=9,reset_status=saved['status'],strict_reset_witness_endpoints=endpoint_checks,aliases=counts,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
