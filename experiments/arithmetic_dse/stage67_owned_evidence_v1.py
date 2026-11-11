"""Portable successor evidence for exclusive composition and zero-G replay."""
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


def package(root,parent,evidence):
    if evidence.exists():raise ValueError('preserve owned-accounting evidence')
    evidence.mkdir(parents=True);old=read(parent/'manifest.json');data=b''
    for n,h in old['chunks'].items():
        if sha(parent/n)!=h:raise ValueError('prior evidence changed')
        data+=(parent/n).read_bytes()
    raw=gzip.decompress(data)
    if hashlib.sha256(raw).hexdigest()!=old['payload_sha256']:raise ValueError('prior payload changed')
    pool=json.loads(raw)
    def add(name,path):
        value=Path(path).read_text()
        if name in pool and pool[name]!=value:raise ValueError('parent member must not be overwritten '+name)
        pool[name]=value
    names=['experiments/arithmetic_dse/'+n+'.py' for n in ('stage67_accounting_audit_v1','stage67_owned_timing_v1','stage67_owned_validation_v1','stage67_owned_evidence_v1')]
    names+=['regression/arithmetic_owned_timing.py','rtlzz/src/backend/arithmetic_owned_timing.hpp','rtlzz/src/backend/arithmetic_owned_timing.cpp','rtlzz/testv2/arithmetic_owned_timing_consumer.cpp']
    for n in names:add('source/'+n,ROOT/n)
    for name,path in {
        'owned/training-policy.json':root/'derivation/candidate.json',
        'owned/training-audit.json':root/'derivation-v2/training-audit.json',
        'owned/rederived-policy.json':root/'derivation-v2/candidate.json',
        'owned/calibrated-policy.json':root/'validation-initial/candidate-calibrated.json',
        'owned/native-initial.json':root/'native-initial/native.json',
        'owned/native-final.json':root/'native-final/native.json',
        'owned/validation.json':root/'validation-initial/validation.json',
        'owned/parity.json':root/'parity-final/parity.json',
        'owned/semantics.json':root/'semantics/proof.json',
    }.items():add(name,path)
    if (root/'derivation/candidate.json').read_bytes()!=(root/'derivation-v2/candidate.json').read_bytes():raise ValueError('training replay packet altered point policy')
    # Freeze exact source/receipt identities for the native execution; the
    # portable Python replay independently recomputes its numerical outputs.
    receipts={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'build/step67-accounting-20261111').glob('*/commands.json')}
    add('owned/native-controls.json',root/'native-controls/native.json')
    pool['owned/execution-receipts.json']=json.dumps(receipts,indent=2)+'\n'
    from .operator_stage4 import archive
    (root.parent/'restore').mkdir(exist_ok=True)
    receipt=archive(root.parent,[root],'stage67-owned-accounting-20261111-v1.tar.gz')
    write(evidence/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(member_count=len(receipt['members'])))
    payload=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(payload,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        path=evidence/f'pool-{i:03d}.gzpart';path.write_bytes(compressed[start:start+512*1024]);chunks[path.name]=sha(path)
    shutil.copy2(Path(__file__),evidence/'replay.py')
    write(evidence/'manifest.json',dict(version='owned-accounting-evidence-v1',chunks=chunks,files={n:hashlib.sha256(v.encode()).hexdigest() for n,v in pool.items()},
        payload_sha256=hashlib.sha256(payload).hexdigest(),replay_sha256=sha(evidence/'replay.py'),parent_manifest_sha256=sha(parent/'manifest.json'),
        policy_sha256=sha(root/'validation-initial/candidate-calibrated.json'),model_sha256=old['model_sha256'],
        source_sha256={n:sha(ROOT/n) for n in names},zero_G_joint_qualified=False,full_D_ready=False,physical_calls=0))
    sizes=[p.stat().st_size for p in evidence.iterdir() if p.is_file()]
    if sum(sizes)>5*1024**2 or max(sizes)>1024**2:raise ValueError('small evidence size limit exceeded')
    print(dict(status='sealed_owned_accounting_successor',members=len(pool),evidence_bytes=sum(sizes),full_D_ready=False),flush=True)


def replay(evidence):
    manifest=read(evidence/'manifest.json')
    if sha(evidence/'replay.py')!=manifest['replay_sha256']:raise ValueError('replay source changed')
    compressed=b''
    for n,h in manifest['chunks'].items():
        if sha(evidence/n)!=h:raise ValueError('changed pool part')
        compressed+=(evidence/n).read_bytes()
    payload=gzip.decompress(compressed)
    if hashlib.sha256(payload).hexdigest()!=manifest['payload_sha256']:raise ValueError('changed payload')
    pool=json.loads(payload)
    if set(pool)!=set(manifest['files']):raise ValueError('restored member inventory differs')
    with tempfile.TemporaryDirectory(prefix='owned-timing-isolated-') as directory:
        root=Path(directory)
        for name,value in pool.items():
            p=Path(name)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(value.encode()).hexdigest()!=manifest['files'][name]:raise ValueError('unsafe/changed member')
            destination=root/p;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(value)
        for name in list(sys.modules):
            if name in ('experiments','regression') or name.startswith(('experiments.','regression.')):del sys.modules[name]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse.stage67_owned_timing_v1 import compare
        from experiments.arithmetic_dse.stage67_owned_validation_v1 import analyze
        from experiments.arithmetic_dse.stage67_analyze_v1 import parse_stage
        from regression.arithmetic_owned_timing import run as semantics
        owned=root/'owned';p=read(owned/'training-policy.json');audit=read(owned/'training-audit.json');s_groups=defaultdict(lambda:defaultdict(list));w_groups=defaultdict(list)
        if sha(root/'release/operators.json')!=manifest['model_sha256']:raise ValueError('changed qualified node parameters')
        if p!=read(owned/'rederived-policy.json') or not audit['only_train_for_point_parameters']:raise ValueError('point policy not training-only')
        for row in audit['state_rows']:
            if row['role']!='train' or not row['actual_arcs_and_nets_verified']:raise ValueError('nontraining or unverified S point')
            adapter=math.fsum(s['delay_ps'] for s in row['segments'] if s['source_adapter_internal'])
            if not math.isclose(row['target_ps']-row['slack_ps']-adapter,row['value_ps'],abs_tol=1e-8):raise ValueError('training boundary partition differs')
            s_groups[row['boundary_role']][row['source']].append(row['value_ps'])
        for role,groups in s_groups.items():
            if p['boundary_point_ps'][role]!=statistics.median(statistics.median(v) for v in groups.values()):raise ValueError('source-balanced boundary differs')
        for row in audit['arithmetic_wire_rows']:
            if row['role']!='train':raise ValueError('nontraining wire point')
            w_groups[row['source']].append(statistics.median(row['wire_values_ps']))
        if p['inter_arithmetic_wire_point_ps']!=statistics.median(statistics.median(v) for v in w_groups.values()):raise ValueError('source-balanced wire differs')
        old=read(root/'expected/diagnosis.json');endpoints=0
        for point in old['points']:
            for stage in ('synth','grt'):
                task=point['task'];label=parse_stage(root/'reports'/task/stage);expected=read(root/'expected'/(task+'-'+stage+'-labels.json'));expected.pop('whole_shell_metrics')
                if label!=expected:raise ValueError('strict physical ownership/Liberty replay differs')
                endpoints+=label['endpoint_checks']
        compare(owned/'native-final.json',owned/'calibrated-policy.json',root/'release/operators.json',root/'replayed-parity')
        if read(root/'replayed-parity/parity.json')!=read(owned/'parity.json'):raise ValueError('independent native parity replay differs')
        semantics(owned/'native-initial.json',root/'replayed-semantics')
        if read(root/'replayed-semantics/proof.json')!=read(owned/'semantics.json'):raise ValueError('semantic replay differs')
        (root/'labels').mkdir()
        for path in (root/'expected').glob('*-grt-labels.json'):shutil.copy2(path,root/'labels'/path.name)
        analyze(owned/'native-initial.json',owned/'training-policy.json',root/'expected/diagnosis.json',root/'labels',root/'replayed-validation')
        if read(root/'replayed-validation/validation.json')!=read(owned/'validation.json'):raise ValueError('validation decomposition replay differs')
        if sha(root/'replayed-validation/candidate-calibrated.json')!=manifest['policy_sha256']:raise ValueError('reserve calibration identity differs')
        final=read(owned/'native-final.json');controls=read(owned/'native-controls.json');initial=read(owned/'native-initial.json')
        if len(final['negatives'])!=12 or final['negatives']!=controls['negatives']:raise ValueError('native negative receipt inventory differs')
        for first,last in zip(initial['sources'],final['sources'],strict=True):
            for a,b in zip(first['variants'],last['variants'],strict=True):
                for x,y in zip(a['targets'],b['targets'],strict=True):
                    left=x['owned_timing'];right=y['owned_timing']
                    if left['status']!=right['status']:raise ValueError('calibration altered coverage')
                    for k in ('stages','total_area_um2','node_prices','decision_violation_ps'):
                        if left.get(k)!=right.get(k):raise ValueError('unchanged 50ps calibration altered prices')
        if old['status']!='pilot_quality_failed' or read(owned/'validation.json')['zero_G_joint_qualified']:raise ValueError('old failure/qualification changed')
    print(dict(status='passed_isolated_owned_accounting_replay',endpoint_checks=endpoints,training_paths=len(audit['state_rows']),wire_training_points=len(audit['arithmetic_wire_rows']),
        native_requests=36,native_negative_receipts=12,physical_calls=0,old_failure_preserved=True,zero_G_joint_qualified=False,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('package','replay'));p.add_argument('--root',type=Path);p.add_argument('--parent',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='package':package(a.root.resolve(),a.parent.resolve(),a.evidence.resolve())
    else:replay(a.evidence.resolve())
