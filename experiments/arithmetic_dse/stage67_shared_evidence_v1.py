"""Compact portable evidence for prospective general shared-function fitting.

The small replay refits train scalars and checks fresh validation, refuses and
native semantic-feature/area parity. Full physical/CEC/state witnesses remain
in a separately restored archive, whose identity is included in the manifest.
"""
import argparse
from collections import Counter
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
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve evidence attempts')
    pool={}
    # Include all Python imports for isolation; no external numeric runtime.
    for d in ('experiments/arithmetic_dse','regression'):
        for p in (ROOT/d).glob('*.py'):pool['source/'+str(p.relative_to(ROOT))]=p.read_text()
    for p in (ROOT/'rtlzz/src/backend').glob('arithmetic_shared_function.*'):pool['source/'+str(p.relative_to(ROOT))]=p.read_text()
    paths={'protocol.json':root/'preparation-v2/protocol.json','sources.json':root/'preparation-v2/sources.json',
        'train.json':root/'train-labels-v1/dataset.json','validation-data.json':root/'validation-labels-v1/dataset.json',
        'candidate.json':root/'fit-v1/candidate.json','freeze.json':root/'fit-v1/freeze-v2.json','validation.json':root/'validation-v1/validation.json',
        'operators.json':ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json',
        'S.json':Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/reused-S.json'),
        'native.json':root/'native-v2/native.json','parity.json':root/'parity-v2/parity.json','demand.json':root/'mac32-v2/proof.json',
        'restore.json':root/'archives/shared-function-raw-v1.tar.gz.index.json','qualification.json':root/'qualification-v1/proof.json'}
    for n,p in paths.items():pool['data/'+n]=p.read_text()
    # A real complete cell-census witness permits owner partition replay;
    # other full witnesses are verified by the actual archive restoration.
    witness=next((root/'train-inherited-labels-v2').glob('*-ownership.json'));pool['data/ownership.json']=witness.read_text()
    evidence.mkdir(parents=True);raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};index=evidence/'file-index.json.gz';index.write_bytes(gzip.compress(json.dumps(files,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    shutil.copy2(Path(__file__),evidence/'replay.py');write(evidence/'manifest.json',dict(version='shared-function-fit-evidence-v1',chunks=chunks,
        payload_sha256=hashlib.sha256(raw).hexdigest(),file_index_sha256=sha(index),members=len(files),replay_sha256=sha(evidence/'replay.py'),
        candidate_sha256=sha(paths['candidate.json']),raw_archive_sha256=read(paths['restore.json'])['archive_sha256'],full_D_ready=False,
        replay_scope='stdlib train refit, parameter/role/feature/domain invariants, fresh validation statistics, native semantic area parity and real owner witness; full metrology in restored raw archive'))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('evidence size limit')
    print(dict(status='sealed_shared_function_evidence',members=len(files),bytes=sum(sizes)),flush=True)


def close(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)
    return a==b


def replay(evidence):
    m=read(evidence/'manifest.json');compressed=b''
    if sha(evidence/'replay.py')!=m['replay_sha256'] or sha(evidence/'file-index.json.gz')!=m['file_index_sha256']:raise ValueError('changed replay/index')
    files=json.loads(gzip.decompress((evidence/'file-index.json.gz').read_bytes()))
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('changed chunk')
        compressed+=(evidence/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('changed payload')
    pool=json.loads(raw)
    if set(pool)!=set(files) or len(files)!=m['members']:raise ValueError('changed inventory')
    with tempfile.TemporaryDirectory(prefix='shared-function-replay-') as tmp:
        root=Path(tmp)
        for n,value in pool.items():
            p=Path(n)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=files[n]:raise ValueError('unsafe/changed file')
            d=root/p;d.parent.mkdir(parents=True,exist_ok=True);d.write_text(value)
        for n in list(sys.modules):
            if n in ('experiments','regression') or n.startswith(('experiments.','regression.')):del sys.modules[n]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse.stage67_shared_model_v1 import fit_models
        from experiments.arithmetic_dse.stage67_shared_model_v2 import predict
        from experiments.arithmetic_dse.stage67_batch1_analyze_v1 import stats
        from experiments.arithmetic_dse.stage67_analyze_v1 import verify_ownership_packet
        policy=read(root/'data/candidate.json');train=read(root/'data/train.json');validation=read(root/'data/validation-data.json');protocol=read(root/'data/protocol.json')
        if sha(root/'data/candidate.json')!=m['candidate_sha256'] or policy['validation_labels_read'] or policy['full_D_ready']:raise ValueError('changed candidate qualification')
        if not close(fit_models(train['rows'],protocol['features']),policy['shared_area_models']):raise ValueError('independent train refit differs')
        if any(r['role']!='train' for r in train['rows']) or any(r['role']!='validation' for r in validation['rows']):raise ValueError('wrong role')
        if {r['source'] for r in train['rows']}&{r['source'] for r in validation['rows']}:raise ValueError('source leakage')
        actual=read(root/'data/validation.json');owners={n:[] for n in protocol['features']};totals=[];refused=[]
        for r in validation['rows']:
            try:a=predict(policy,r['features'],r['target_ps'])
            except ValueError as e:refused.append((r['source'],r['target_ps'],str(e)));continue
            for n,y in r['labels'].items():owners[n].append(abs(a[n]-y)/max(.01,y))
            totals.append(abs(r['features']['predicted_functional_area_um2']+sum(a.values())-r['total_area_um2'])/max(.01,r['total_area_um2']))
        errors={n:stats(v) for n,v in owners.items()};total=stats(totals);failures=[n+'/owner_error' for n,v in errors.items() if v['median']>.15 or v['P95']>.35]
        if total['median']>.15 or total['P95']>.35:failures.append('total_area_error')
        if refused:failures.append('validation_support_refusals')
        if not close(errors,actual['owner_errors']) or not close(total,actual['total_error']) or failures!=actual['failures']:raise ValueError('one-time validation verdict differs')
        witness=read(root/'data/ownership.json');verify_ownership_packet(witness)
        demand=read(root/'data/demand.json');counts=Counter(v['estimate']['status'] for t in demand['targets'] for v in t['views'])
        for t in demand['targets']:
            for v in t['views']:
                d=v['diagnostics'];o=d['owner_features'];ff=d['total_FF_bits'];f=dict(one=1.,total_FF_bits=ff,sqrt_FF_bits=math.sqrt(ff),predicted_functional_area_um2=v['predicted_functional_area_um2'],input_data_bits=o['input_service']['data_bits'],input_ports=o['input_service']['data_signals'],reset_one_bits=sum(x['reset_one_bits'] for x in o.values()),clock_pressure=1500/t['target_ps'])
                a=predict(policy,f,t['target_ps'])
                for name,val in a.items():
                    if not math.isclose(val,v['estimate']['owner_area_um2'][name],abs_tol=1e-8,rel_tol=1e-10):raise ValueError('actual native demand price differs')
        if counts.get('cost_uncovered',0)!=demand['uncovered'] or demand['full_D_ready']:raise ValueError('demand coverage or qualification differs')
    print(dict(status='passed_isolated_general_shared_replay',train_rows=len(train['rows']),validation_rows=len(validation['rows']),validation_failures=failures,
        MAC32_counts=dict(counts),source_identity_is_not_a_feature=True,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
