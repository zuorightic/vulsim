"""Compact train/consumer/validation successor evidence; no new metrology."""
import argparse
from collections import Counter,defaultdict
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
    if evidence.exists():raise ValueError('preserve dependency-complete evidence successor')
    previous=ROOT/'experiments/arithmetic/evidence/step67_state_shared_successor_v2';old=read(previous/'manifest.json');compressed=b''
    for n,h in old['chunks'].items():
        if sha(previous/n)!=h:raise ValueError('parent chunk changed')
        compressed+=(previous/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=old['payload_sha256']:raise ValueError('parent payload changed')
    pool=json.loads(raw)
    for path in (ROOT/'regression/arithmetic_steps123.py',Path(__file__)):
        pool['source/'+str(path.relative_to(ROOT))]=path.read_text()
    evidence.mkdir(parents=True);payload=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(payload,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};index=evidence/'file-index.json.gz';index.write_bytes(gzip.compress(json.dumps(files,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    shutil.copy2(Path(__file__),evidence/'replay.py');shutil.copy2(previous/'restore-proof.json',evidence/'restore-proof.json')
    m=dict(old);m.update(version='state-shared-successor-evidence-v3',chunks=chunks,file_index=dict(name=index.name,sha256=sha(index),members=len(files)),payload_sha256=hashlib.sha256(payload).hexdigest(),replay_sha256=sha(evidence/'replay.py'),
        source_sha256={n.removeprefix('source/'):h for n,h in files.items() if n.startswith('source/')},parent_manifest_sha256=sha(previous/'manifest.json'),initial_missing_import_failure_preserved=True,
        isolated_numeric_runtime='stdlib subset enumeration independently refits fixed NNLS with at most four features',missing_user_site_numpy_failure_preserved=True)
    write(evidence/'manifest.json',m);sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('compact evidence size limit')
    print(dict(status='sealed_dependency_complete_state_shared_evidence',members=len(pool),evidence_bytes=sum(sizes)),flush=True)


def close_numeric(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(close_numeric(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close_numeric(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)
    return a==b


def refit_small_nnls(rows):
    # Independent exhaustive active-set solution for <=4 nonnegative
    # coefficients. Column scaling keeps the small normal equations stable.
    definitions={'shared_clock':['one','total_FF_bits','predicted_functional_area_um2'],
        'shared_physical':['one','predicted_functional_area_um2'],'root_repair':['one','input_data_bits','total_FF_bits','reset_one_bits']}
    def solve(matrix,rhs):
        a=[list(row)+[b] for row,b in zip(matrix,rhs)];n=len(rhs)
        for c in range(n):
            pivot=max(range(c,n),key=lambda i:abs(a[i][c]))
            if abs(a[pivot][c])<1e-14:return None
            a[c],a[pivot]=a[pivot],a[c];scale=a[c][c];a[c]=[v/scale for v in a[c]]
            for i in range(n):
                if i==c:continue
                value=a[i][c];a[i]=[x-value*y for x,y in zip(a[i],a[c])]
        return [row[-1] for row in a]
    result={}
    for owner,names in definitions.items():
        eligible=[r for r in rows if all(n in r['features'] for n in names)];counts=Counter(r['source'] for r in eligible)
        scales=[max(1,max(abs(r['features'][n]) for r in eligible)) for n in names]
        x=[[r['features'][n]/scale for n,scale in zip(names,scales)] for r in eligible];y=[r['labels'][owner] for r in eligible];w=[1/counts[r['source']] for r in eligible]
        g=[[math.fsum(weight*v[i]*v[j] for weight,v in zip(w,x)) for j in range(len(names))] for i in range(len(names))]
        h=[math.fsum(weight*v[i]*z for weight,v,z in zip(w,x,y)) for i in range(len(names))];best=None
        for mask in range(1<<len(names)):
            active=[i for i in range(len(names)) if mask>>i&1];solution=solve([[g[i][j] for j in active] for i in active],[h[i] for i in active]) if active else []
            if solution is None or any(v< -1e-9 for v in solution):continue
            c=[0.]*len(names)
            for i,value in zip(active,solution):c[i]=max(0.,value)
            loss=math.fsum(weight*(math.fsum(a*b for a,b in zip(v,c))-z)**2 for weight,v,z in zip(w,x,y))
            if best is None or loss<best[0]:best=(loss,c)
        coefficients=[v/scale for v,scale in zip(best[1],scales)]
        result[owner]=dict(kind='nonnegative_linear',features=names,coefficients=coefficients,
            numeric_support={n:[min(r['features'][n] for r in eligible),max(r['features'][n] for r in eligible)] for n in names},training_rows=len(eligible),training_sources=len(counts),
            objective='source-balanced train-only squared error; fixed feature set, no validation selection')
    return result


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
        from experiments.arithmetic_dse.stage67_state_shared_train_v1 import trace_roots,primitive_areas
        from experiments.arithmetic_dse.stage67_factored_timing_v1 import compare
        from experiments.arithmetic_dse.stage67_state_shared_validate_v1 import evaluate
        from experiments.arithmetic_dse.model_physical_path_v2 import verify_combinational_arc
        policy=read(root/'release/policy.json');audit=read(root/'training/fit-packet.json');groups=defaultdict(lambda:defaultdict(list))
        if sha(root/'release/policy.json')!=m['policy_sha256'] or sha(root/'release/operators.json')!=m['node_model_sha256'] or audit['validation_labels_read']:raise ValueError('changed frozen dependency or role')
        if any(r['role']!='train' for r in audit['area_rows']+audit['path_rows']):raise ValueError('nontrain fitting row')
        models=refit_small_nnls(audit['area_rows'])
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
