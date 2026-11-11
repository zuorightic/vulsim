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
    if evidence.exists():raise ValueError('preserve batch evidence attempt')
    evidence.mkdir(parents=True);a=read(root/'admission.json');pool={}
    def add(name,path):pool[name]=Path(path).read_text()
    for p in (ROOT/'experiments/arithmetic_dse').glob('*.py'):add('source/'+str(p.relative_to(ROOT)),p)
    for p in (ROOT/'experiments/arithmetic_dse/configs/platforms').glob('*.json'):add('source/'+str(p.relative_to(ROOT)),p)
    for name in ('regression/arithmetic_stage67_batch1.py','regression/arithmetic_steps123.py'):add('source/'+name,ROOT/name)
    add('batch/admission.json',root/'admission.json');add('batch/demand-audit.json',root/'demand-audit.json')
    add('release/timing.json',a['timing_policy']['path']);add('release/operators.json',a['model']['path']);add('release/S-binding.json',a['S_binding']['path'])
    add('expected/validation.json',root/'analysis-v2/validation.json');add('expected/qualification.json',root/'qualification-v1/proof.json')
    for task in a['tasks']:
        d=root/'runs'/task['id'];prefix='batch/runs/'+task['id']+'/'
        for name in ('mapped.json','liberty-pins.json','liberty_cells.json','mapped-state.json','input.sv'):add(prefix+name,d/name)
        for p in (d/'reports/asap7/arithmetic_probe/base').glob('vulsim_*'):
            if p.is_file():add(prefix+'reports/asap7/arithmetic_probe/base/'+p.name,p)
        for name in ('1_synth.sdc','5_1_grt.sdc','4_before_rsz_lec.v','4_after_rsz_lec.v'):add(prefix+'results/asap7/arithmetic_probe/base/'+name,d/'results/asap7/arithmetic_probe/base'/name)
        for name in ('1_synth.json','5_1_grt.json'):add(prefix+'logs/asap7/arithmetic_probe/base/'+name,d/'logs/asap7/arithmetic_probe/base'/name)
        cec=d/'logs/asap7/arithmetic_probe/base/structural_cec'
        for name in ('gold-hier.json','proof.json','cec.log'):
            add(prefix+'logs/asap7/arithmetic_probe/base/structural_cec/'+name,cec/name)
        for name in read(cec/'proof.json')['negative_controls']:add(prefix+'logs/asap7/arithmetic_probe/base/structural_cec/negative-'+name+'.log',cec/('negative-'+name+'.log'))
        for p in Path(task['input_directory']).iterdir():
            if p.is_file():add('batch/inputs/'+task['id']+'/'+p.name,p)
        for stage in ('synth','grt'):
            for p in (root/'readout-v2'/task['id']/stage).iterdir():
                if p.is_file() and p.suffix in ('.json','.tsv'):add('batch/readout-v2/'+task['id']+'/'+stage+'/'+p.name,p)
            add('expected/'+task['id']+'-'+stage+'-labels.json',root/'analysis-v2'/(task['id']+'-'+stage+'-labels.json'))
        add('expected/'+task['id']+'-state.json',root/'state-semantics-v3'/(task['id']+'.json'))
    from .operator_stage4 import archive
    previous=Path(a['parent']);oldest=Path(read(previous/'admission.json')['parent']);(root.parent/'restore').mkdir(exist_ok=True)
    receipt=archive(root.parent,[oldest,previous,root,Path('/home/zyrv/vulsim-artifacts/stage67-batch1-cec-recovery-20261111-v1'),Path('/home/zyrv/vulsim-artifacts/stage67-bypass-alias-proof-20261111-v1')],'stage67-batch1-20261111-v1.tar.gz')
    write(evidence/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(member_count=len(receipt['members'])))
    raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    shutil.copy2(Path(__file__),evidence/'replay.py');sources={name.removeprefix('source/'):hashlib.sha256(value.encode()).hexdigest() for name,value in pool.items() if name.startswith('source/')}
    write(evidence/'manifest.json',dict(version='stage67-batch1-portable-v1',chunks=chunks,files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()},
        payload_sha256=hashlib.sha256(raw).hexdigest(),replay_sha256=sha(evidence/'replay.py'),source_sha256=sources,physical_stages=8,
        model_sha256=a['model']['sha256'],S_binding_sha256=a['S_binding']['sha256'],timing_policy_sha256=a['timing_policy']['sha256'],
        physical_measurements=4,failed_parent_grt_retained=True,independent_tests_unlocked=False,zero_G_joint_qualified=False,full_D_ready=False))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('small evidence size limit exceeded')
    print(dict(status='sealed_batch1_evidence',members=len(pool),evidence_bytes=sum(sizes),raw_archive_members=len(receipt['members'])),flush=True)


def equal(a,b):
    if isinstance(a,dict):
        keys=set(a)-{'raw_reports_prefix'}
        return isinstance(b,dict) and keys==set(b)-{'raw_reports_prefix'} and all(equal(a[k],b[k]) for k in keys)
    if isinstance(a,list):return isinstance(b,list) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    if isinstance(a,(int,float)) and not isinstance(a,bool):return isinstance(b,(int,float)) and math.isclose(a,b,abs_tol=1e-8,rel_tol=1e-12)
    return a==b


def replay(evidence):
    m=read(evidence/'manifest.json')
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
