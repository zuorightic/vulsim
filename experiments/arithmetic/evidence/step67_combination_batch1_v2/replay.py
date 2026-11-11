"""Seal and independently replay batch1 physical packets without live EDA."""
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
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve compact successor')
    previous=ROOT/'experiments/arithmetic/evidence/step67_combination_batch1_v1'
    m=read(previous/'manifest.json');compressed=b''
    for n,h in m['chunks'].items():
        if sha(previous/n)!=h:raise ValueError('changed first attempt chunk')
        compressed+=(previous/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('changed first attempt payload')
    pool=json.loads(raw);name='source/'+str(Path(__file__).relative_to(ROOT));pool[name]=Path(__file__).read_text()
    evidence.mkdir(parents=True);payload=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();parts={};compressed=gzip.compress(payload,mtime=0)
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        path=evidence/f'pool-{i:03d}.gzpart';path.write_bytes(compressed[start:start+512*1024]);parts[path.name]=sha(path)
    files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};index=evidence/'file-index.json.gz';index.write_bytes(gzip.compress(json.dumps(files,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    shutil.copy2(Path(__file__),evidence/'replay.py');shutil.copy2(previous/'restore-proof.json',evidence/'restore-proof.json')
    sources={n.removeprefix('source/'):hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items() if n.startswith('source/')}
    manifest={k:v for k,v in m.items() if k not in ('files','chunks','payload_sha256','replay_sha256','source_sha256')}
    manifest.update(version='stage67-batch1-portable-v2',chunks=parts,payload_sha256=hashlib.sha256(payload).hexdigest(),replay_sha256=sha(evidence/'replay.py'),source_sha256=sources,
        file_index=dict(name=index.name,sha256=sha(index),members=len(files)),parent_manifest_sha256=sha(previous/'manifest.json'),first_attempt_size_failure_preserved=True)
    write(evidence/'manifest.json',manifest);sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('compact evidence still exceeds storage limit')
    print(dict(status='sealed_compact_batch1_successor',members=len(pool),evidence_bytes=sum(sizes),new_EDA_calls=0),flush=True)


def equal(a,b):
    if isinstance(a,dict):
        keys=set(a)-{'raw_reports_prefix'}
        return isinstance(b,dict) and keys==set(b)-{'raw_reports_prefix'} and all(equal(a[k],b[k]) for k in keys)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-12)
    return a==b


def replay(evidence):
    m=read(evidence/'manifest.json')
    index=evidence/m['file_index']['name']
    if sha(index)!=m['file_index']['sha256']:raise ValueError('changed compressed file index')
    m['files']=json.loads(gzip.decompress(index.read_bytes()))
    if len(m['files'])!=m['file_index']['members']:raise ValueError('changed file index count')
    if sha(evidence/'replay.py')!=m['replay_sha256']:raise ValueError('changed replay source')
    compressed=b''
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('changed evidence chunk')
        compressed+=(evidence/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('changed payload')
    pool=json.loads(raw)
    if set(pool)!=set(m['files']):raise ValueError('changed restored inventory')
    with tempfile.TemporaryDirectory(prefix='batch1-isolated-') as directory:
        root=Path(directory)
        for name,value in pool.items():
            p=Path(name)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=m['files'][name]:raise ValueError('unsafe or changed restored member')
            dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(value)
        for name in list(sys.modules):
            if name in ('experiments','regression') or name.startswith(('experiments.','regression.')):del sys.modules[name]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse.stage67_parse_v2 import parse_stage
        from experiments.arithmetic_dse.stage67_state_semantics_v1 import verify as semantics
        from experiments.arithmetic_dse.stage67_mapped_state_v3 import verify as census
        from experiments.arithmetic_dse.stage67_batch1_analyze_v1 import compare
        from experiments.arithmetic_dse.model_m2_live_cec_v4 import check_result
        from experiments.arithmetic_dse.stage67_owned_timing_v1 import estimate
        from experiments.arithmetic_dse.operator_condition_model import query
        batch=root/'batch';a=read(batch/'admission.json');endpoints=0;logical=0;physical=0;constants=0;negative_CEC=0
        if sha(root/'release/operators.json')!=m['model_sha256'] or sha(root/'release/timing.json')!=m['timing_policy_sha256'] or sha(root/'release/S-binding.json')!=m['S_binding_sha256']:raise ValueError('frozen model dependency changed')
        policy=read(root/'release/timing.json');model=read(root/'release/operators.json')
        for task in a['tasks']:
            d=batch/'runs'/task['id'];inputs=batch/'inputs'/task['id'];contract=read(inputs/'endpoints.json');state=read(d/'mapped-state.json');rtl=(d/'input.sv').read_text()
            computed=census(read(d/'mapped.json'),read(d/'liberty-pins.json'),contract,read(inputs/'source.json'),rtl)
            if not equal(computed['words'],state['words']) or computed['owner_FF_bits']!=state['owner_FF_bits']:raise ValueError('state/alias census differs')
            proof=semantics(d,state,rtl,contract)
            if not equal(proof,read(root/'expected'/(task['id']+'-state.json'))):raise ValueError('state Boolean proof differs')
            logical+=proof['checked_FF_bits'];physical+=sum(state['owner_FF_bits'].values())
            cec=d/'logs/asap7/arithmetic_probe/base/structural_cec';p=read(cec/'proof.json')
            if p['status']!='passed' or sha(d/'results/asap7/arithmetic_probe/base/4_before_rsz_lec.v')!=p['before_sha256'] or sha(d/'results/asap7/arithmetic_probe/base/4_after_rsz_lec.v')!=p['after_sha256']:raise ValueError('saved exact CEC pair differs')
            check_result((cec/'cec.log').read_text(),True)
            for name in p['negative_controls']:check_result((cec/('negative-'+name+'.log')).read_text(),False);negative_CEC+=1
            prediction=read(inputs/'prediction.json');oracle=estimate(prediction['graph'],dict(cuts=prediction['cuts'],state=prediction['state']),dict(target_ps=1500,queries=prediction['queries']),policy,model)
            if oracle['status']!='candidate_covered':raise ValueError('frozen node/timing coverage differs')
            for left,right in zip(oracle['stages'],prediction['owned_timing']['stages'],strict=True):
                if not equal(left['captures'],right['captures']):raise ValueError('premeasurement stage prices differ')
            for stage in ('synth','grt'):
                label=parse_stage(batch/'readout-v2'/task['id']/stage);expected=read(root/'expected'/(task['id']+'-'+stage+'-labels.json'));expected.pop('whole_shell_metrics')
                if not equal(label,expected):raise ValueError('strict physical label differs')
                endpoints+=label['endpoint_checks'];constants+=label['proven_constant_output_bits']
            task['input_directory']=str(inputs);task['endpoint_contract']=str(inputs/'endpoints.json');task['rtl']=str(inputs/'input.sv')
        a['timing_policy']['path']=str(root/'release/timing.json');write(batch/'admission.json',a)
        compare(batch,root/'analysis')
        if not equal(read(root/'analysis/validation.json'),read(root/'expected/validation.json')):raise ValueError('full validation/ranking/owner replay differs')
        verdict=read(root/'analysis/validation.json')
        if not verdict['joint_validation_failures'] or verdict['full_D_ready'] or verdict['reserve_recalibrated']:raise ValueError('joint failure or reserve identity changed')
    print(dict(status='passed_isolated_batch1_replay',physical_stages=8,endpoint_checks=endpoints,constant_output_checks=constants,
        logical_FF_references=logical,unique_physical_FF_bits=physical,CEC_negative_logs=negative_CEC,new_EDA_calls=0,
        joint_failures_preserved=True,zero_G_joint_qualified=False,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
