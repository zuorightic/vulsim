"""Compact whole-stage/ranking evidence with one complete physical witness.

Replays model inference, bit recurrence, observed scalar stage/bank judgments,
ranking and a real strict timing packet. Full other packets, state and CEC
witnesses remain in the separately restored original-artifact archive.
"""
import argparse
from collections import Counter
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import sys
import tempfile
from types import FunctionType

ROOT=Path(__file__).resolve().parents[2]
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).parent.mkdir(parents=True,exist_ok=True);Path(p).write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n')


def package(root,evidence):
    if evidence.exists():raise ValueError('preserve compact evidence attempts')
    from .stage67_multiclock_v1 import PARENT,NODE,BINDING,POLICY_PATH,FREEZE
    pool={}
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):pool['source/'+str(p.relative_to(ROOT))]=p.read_text()
    pool['source/regression/arithmetic_steps123.py']=(ROOT/'regression/arithmetic_steps123.py').read_text()
    native=read(PARENT/'native-v2/native.json');native['sources']=[s for s in native['sources'] if s['role']=='validation']
    native['sources']+=read(root/'paired-native/native.json')['sources']
    for s in native['sources']:
        for v in s['variants']:v['targets']=[t for t in v['targets'] if t['target_ps'] in (500,1500,3000)]
    pool['data/native.json']=json.dumps(native,indent=2)
    paths={'operators.json':NODE,'binding.json':BINDING,'reused-S.json':BINDING.parent/'reused-S.json','policy.json':POLICY_PATH,'freeze.json':FREEZE,
        'primary.json':root/'analysis-v1/validation.json','alternate.json':root/'paired-readout/analysis-v1/validation.json','combined.json':root/'combined-v1/validation.json',
        'reader-qualification.json':root/'reader-qualification.json','control-primary.json':root/'control-audit-primary.json','control-alternate.json':root/'control-audit-alternate.json',
        'remaining-domain.json':root/'remaining-domain-audit.json','restore.json':root/'archives/multiclock-raw-v1.tar.gz.index.json'}
    for n,p in paths.items():pool['data/'+n]=p.read_text()
    packets=[]
    for report in (root,root/'paired-readout'):
        for t in read(report/'admission.json')['tasks']:
            original=read(report/'analysis-v1'/(t['id']+'-grt-labels.json'))
            actual={n:original[n] for n in ('nodes','owner_area_um2','owner_FF_bits','total_area_um2','endpoint_checks','proven_constant_output_bits','whole_shell_metrics')}
            actual['functional_paths']=[]
            for p in original['functional_paths']:
                if p['path_class'] not in ('native_data','external_data'):continue
                v={n:p[n] for n in ('word','stage','path_class','slack_ps','node_order','node_delay_ps','end')}
                v['segments']=[{n:s[n] for n in ('kind','owner','delay_ps')} for s in p['segments']];actual['functional_paths'].append(v)
            packets.append(dict(task=t['id'],source=t['source'],placement=t['placement'],target_ps=t['period_ps'],actual=actual,full_certified_label_sha256=sha(report/'analysis-v1'/(t['id']+'-grt-labels.json'))))
    pool['data/compact-labels.json']=json.dumps(packets,separators=(',',':'))
    witness=root/'readout-v1/validation_p20-T500/grt'
    for p in witness.rglob('*'):
        if p.is_file():pool['witness/'+str(p.relative_to(witness))]=p.read_text()
    for name in ('validation_p20','validation_r28_disjoint','validation_c24'):
        pool['data/previous/preparation-v2/sources/'+name+'/request.json']=(PARENT/'preparation-v2/sources'/name/'request.json').read_text()
        pool['data/first/paired-software/sources/'+name+'/request.json']=(root/'paired-software/sources'/name/'request.json').read_text()
    pool['data/first/analysis-v1/validation.json']=paths['primary.json'].read_text()
    pool['data/second/analysis-v1/validation.json']=paths['alternate.json'].read_text()
    evidence.mkdir(parents=True);raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    index={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()};p=evidence/'file-index.json.gz';p.write_bytes(gzip.compress(json.dumps(index,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    shutil.copy2(Path(__file__),evidence/'replay.py');write(evidence/'manifest.json',dict(version='multiclock-stage-evidence-v1',members=len(pool),chunks=chunks,payload_sha256=hashlib.sha256(raw).hexdigest(),
        file_index_sha256=sha(p),replay_sha256=sha(evidence/'replay.py'),policy_sha256=sha(POLICY_PATH),raw_archive_sha256=read(paths['restore.json'])['archive_sha256'],
        physical_replay_scope='one complete strict grt packet; all others use certified compact scalar/decomposition labels tied to raw archive',
        independent_tests_unlocked=False,full_D_ready=False))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('compact evidence size limit')
    print(dict(status='sealed_multiclock_stage_evidence',members=len(pool),bytes=sum(sizes)),flush=True)


def close(a,b):
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(close(a[k],b[k]) for k in a)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(close(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-10)
    return a==b


def replay(evidence):
    m=read(evidence/'manifest.json')
    if sha(evidence/'replay.py')!=m['replay_sha256'] or sha(evidence/'file-index.json.gz')!=m['file_index_sha256']:raise ValueError('changed index/replay')
    compressed=b''
    for n,h in m['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('changed chunk')
        compressed+=(evidence/n).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=m['payload_sha256']:raise ValueError('changed payload')
    pool=json.loads(raw);index=json.loads(gzip.decompress((evidence/'file-index.json.gz').read_bytes()))
    if set(pool)!=set(index) or len(pool)!=m['members']:raise ValueError('changed inventory')
    with tempfile.TemporaryDirectory(prefix='stage-multiclock-replay-') as tmp:
        root=Path(tmp)
        for n,value in pool.items():
            p=Path(n)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=index[n]:raise ValueError('unsafe/changed member')
            out=root/p;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(value)
        for n in list(sys.modules):
            if n in ('experiments','regression') or n.startswith(('experiments.','regression.')):del sys.modules[n]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse import stage67_shared_model_v1 as shared,stage67_shared_model_v2 as shared2,stage67_shared_timing_check_v1 as timing
        from experiments.arithmetic_dse import stage67_multiclock_v1 as stage,stage67_paired_validation_v1 as paired
        from experiments.arithmetic_dse.stage67_parse_v2 import parse_stage
        native=read(root/'data/native.json');policy=read(root/'data/policy.json')
        if sha(root/'data/policy.json')!=m['policy_sha256']:raise ValueError('changed frozen policy')
        # These two frozen consumers read only the exact sealed dependencies;
        # explicit legacy absolute S paths redirect to the sealed S bytes.
        def portable_read(path):
            p=Path(path)
            if str(p)=='/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/reused-S.json':p=root/'data/reused-S.json'
            if not p.is_relative_to(root):raise ValueError('unsealed external read '+str(p))
            return read(p)
        ns=dict(shared.parity.__globals__);ns.update(NODE=root/'data/operators.json',read=portable_read,linear=shared2.linear,predict=shared2.predict)
        FunctionType(shared.parity.__code__,ns)(root/'data/native.json',root/'data/policy.json',root/'parity')
        timing.NODE=root/'data/operators.json';timing.BINDING=root/'data/binding.json'
        timing.compare(root/'data/native.json',root/'data/policy.json',root/'timing')
        packets=read(root/'data/compact-labels.json');actual_points=read(root/'data/combined.json')['points'];bank_checks=0
        for packet in packets:
            s=next(s for s in native['sources'] if s['source']==packet['source'] and s['variants'][0]['id']==packet['placement']);v=s['variants'][0]
            t=next(t for t in v['targets'] if t['target_ps']==packet['target_ps']);v=stage.complete_variant(v['graph'],v)
            pred=dict(graph=v['graph'],cuts=v['cuts'],state=v['state'],queries=t['queries'],owned_timing=t['owned_timing'])
            rows=stage.banks(pred,packet['actual'],policy,packet['target_ps']);expected=next(p for p in actual_points if p['task']==packet['task'])
            if not close(rows,expected['banks']):raise ValueError('certified bank calculation differs')
            bank_checks+=len(rows)
            for r in expected['stages']:
                measured=max(b['observed_required_ps'] for b in rows if b['stage']==r['stage']);p=t['owned_timing']['stages'][r['stage']]
                predicted=max([c['point_required_period_ps'] for c in p['captures']]+[b['point_required_ps'] for b in rows if b['stage']==r['stage']])
                if not math.isclose(measured,r['observed_required_ps'],abs_tol=1e-8) or not math.isclose(predicted,r['point_required_ps'],abs_tol=1e-8):raise ValueError('whole-stage max differs')
        stage.PARENT=root/'data/previous';paired.combined(root/'data/first',root/'data/second',root/'combined')
        if not close(read(root/'combined/validation.json'),read(root/'data/combined.json')):raise ValueError('paired verdict/ranking differs')
        real=parse_stage(root/'witness')
        if real['endpoint_checks']!=967 or len(real['nodes'])!=3:raise ValueError('real strict witness differs')
        result=read(root/'combined/validation.json')
        if result['full_D_ready'] or result['independent_tests_unlocked']:raise ValueError('qualification widened')
    print(dict(status='passed_isolated_multiclock_stage_replay',cases=len(packets),stages=result['complete_stage_error']['count'],bank_checks=bank_checks,
        strict_actual_endpoints=real['endpoint_checks'],failures=result['failures'],ranking_pairs=len(result['ranking']),full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
