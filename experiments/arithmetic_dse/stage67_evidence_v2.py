"""Seal and replay actual stage-6/7 pilot packets without live EDA or refits."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]


def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')


def package(root,evidence):
    from .operator_collection import measurement_sources
    from .operator_stage4 import archive
    a=read(root/'admission.json');prior=Path(a['parent']);pool={};files={}
    def add(name,path):
        data=Path(path).read_text();pool[name]=data;files[name]=hashlib.sha256(data.encode()).hexdigest()
    names=set(a['sources'])|set(read(Path('/home/zyrv/vulsim-artifacts/operator-conditional-wide-20261110-v1/fit-v2/selection-freeze.json'))['implementation_sources'])
    # The isolated reader imports the whole frozen ownership/path stack. Keep
    # every DSE Python source in the successor pool so import order cannot
    # depend on the live checkout.
    names|={str(p.relative_to(ROOT)) for p in (ROOT/'experiments/arithmetic_dse').glob('*.py')}
    names|={'experiments/arithmetic_dse/stage7_physical_prepare.py','regression/arithmetic_steps123.py','regression/arithmetic_stage67_qualification.py','regression/arithmetic_stage67_joint_software.py'}
    for name in sorted(names):add('source/'+name,ROOT/name)
    add('release/operators.json',a['model']['path']);add('release/binding.json',a['S_binding']['path'])
    add('expected/qualification.json',root/'qualification-v1/proof.json');add('expected/diagnosis.json',root/'analysis-v3/pilot-diagnosis.json')
    for folder in sorted((prior/'software').glob('*/export.json')):add('software/'+folder.parent.name+'/export.json',folder)
    for task in a['tasks']:
        bank=root/'runs'/task['id'];pointer=bank/'physical-directory.json';directory=Path(read(pointer)['path']) if pointer.exists() else bank
        for stage in ('synth','grt'):
            for p in sorted((root/'readout-v1'/task['id']/stage).iterdir()):
                if p.is_file() and p.suffix in ('.json','.tsv'):add('reports/'+task['id']+'/'+stage+'/'+p.name,p)
            add('expected/'+task['id']+'-'+stage+'-labels.json',root/'analysis-v3'/(task['id']+'-'+stage+'-labels.json'))
        for name in ('mapped.json','liberty-pins.json','input.sv','logs/asap7/arithmetic_probe/base/structural_cec/gold-hier.json'):add('physical/'+task['id']+'/'+name,directory/name)
        add('physical/'+task['id']+'/mapped-state.json',bank/'mapped-state.json');add('physical/'+task['id']+'/endpoints.json',task['endpoint_contract'])
        add('physical/'+task['id']+'/source.json',Path(task['input_directory'])/'source.json')
        add('expected/'+task['id']+'-state.json',root/'state-semantics-v2'/(task['id']+'.json'))
    # Actual full raw restore, outside the small evidence pool; no physical run.
    store=root.parent;(store/'restore').mkdir(exist_ok=True)
    receipt=archive(store,[prior,root],'stage67-pilot-20261111-v2.tar.gz')
    write(evidence/'restore-proof.json',{k:v for k,v in receipt.items() if k!='members'}|dict(member_count=len(receipt['members'])))
    raw=json.dumps(pool,sort_keys=True,separators=(',',':')).encode();compressed=gzip.compress(raw,mtime=0);chunks={}
    for i,start in enumerate(range(0,len(compressed),512*1024)):
        p=evidence/f'pool-{i:03d}.gzpart';p.write_bytes(compressed[start:start+512*1024]);chunks[p.name]=sha(p)
    shutil.copy2(Path(__file__),evidence/'replay.py')
    write(evidence/'manifest.json',dict(version='stage67-joint-pilot-pool-v2',chunks=chunks,files=files,payload_sha256=hashlib.sha256(raw).hexdigest(),
        replay_sha256=sha(evidence/'replay.py'),model_sha256=a['model']['sha256'],S_binding_sha256=a['S_binding']['sha256'],physical_stages=4,
        state_semantics_FF_bits=[291,276],independent_joint_tests_unlocked=False,zero_G_joint_qualified=False,full_D_ready=False))
    size=sum(p.stat().st_size for p in evidence.iterdir() if p.is_file())
    if size>5*1024**2 or any(p.stat().st_size>1024**2 for p in evidence.iterdir() if p.is_file()):raise ValueError('small evidence storage limit exceeded')
    print(dict(status='sealed_joint_pilot_packets',restored_members=len(pool),evidence_bytes=size,raw_archive_restored_members=len(receipt['members'])),flush=True)


def replay(evidence):
    manifest=read(evidence/'manifest.json')
    if sha(evidence/'replay.py')!=manifest['replay_sha256']:raise ValueError('replay source changed')
    compressed=b''
    for name,h in manifest['chunks'].items():
        if sha(evidence/name)!=h:raise ValueError('evidence chunk changed')
        compressed+=(evidence/name).read_bytes()
    raw=gzip.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=manifest['payload_sha256']:raise ValueError('evidence payload changed')
    pool=json.loads(raw)
    if set(pool)!=set(manifest['files']):raise ValueError('restored file inventory differs')
    with tempfile.TemporaryDirectory(prefix='stage67-isolated-') as directory:
        root=Path(directory)
        for name,contents in pool.items():
            p=Path(name)
            if p.is_absolute() or '..' in p.parts or hashlib.sha256(contents.encode()).hexdigest()!=manifest['files'][name]:raise ValueError('unsafe or changed restored member')
            destination=root/p;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_text(contents)
        for name in list(sys.modules):
            if name=='experiments' or name.startswith(('experiments.','regression.')) or name=='regression':del sys.modules[name]
        sys.path.insert(0,str(root/'source'))
        from experiments.arithmetic_dse.stage67_analyze_v1 import parse_stage
        from experiments.arithmetic_dse.stage67_state_semantics_v1 import verify as state_verify
        from experiments.arithmetic_dse.stage67_mapped_state_v2 import verify as mapped_verify
        from experiments.arithmetic_dse.operator_condition_model import query
        from experiments.arithmetic_dse.stage7_physical_prepare import compose
        model=read(root/'release/operators.json');diag=read(root/'expected/diagnosis.json');queries=0;covered=0;FF=0;endpoints=0
        if sha(root/'release/operators.json')!=manifest['model_sha256'] or diag['status']!='pilot_quality_failed' or diag['full_D_ready']:raise ValueError('model or failed joint verdict changed')
        for export_path in sorted((root/'software').glob('*/export.json')):
            export=read(export_path)
            for variant in export['variants']:
                for target in variant['targets']:
                    prices=[dict(node=q['trace']['node'],**query(model,q['descriptor'])) for q in target['queries']]
                    queries+=len(prices);covered+=sum(p['status']=='covered' for p in prices)
                    score=compose(export,variant,target,prices)
                    if score.get('joint_qualified',False):raise ValueError('software composition granted joint qualification')
        for point in diag['points']:
            task=point['task'];physical=root/'physical'/task;state=read(physical/'mapped-state.json');contract=read(physical/'endpoints.json')
            actual=mapped_verify(read(physical/'mapped.json'),read(physical/'liberty-pins.json'),contract,read(physical/'source.json'),(physical/'input.sv').read_text())
            if actual!=state:raise ValueError('isolated mapped state replay differs')
            checked=state_verify(physical,state,(physical/'input.sv').read_text(),contract)
            if checked!=read(root/'expected'/(task+'-state.json')):raise ValueError('isolated Boolean state replay differs')
            FF+=checked['checked_FF_bits']
            for stage in ('synth','grt'):
                label=parse_stage(root/'reports'/task/stage);expected=read(root/'expected'/(task+'-'+stage+'-labels.json'));expected.pop('whole_shell_metrics')
                if label!=expected:raise ValueError('isolated physical path/area replay differs')
                endpoints+=label['endpoint_checks']
        if (queries,covered,FF,endpoints)!=(96,78,567,3394):raise ValueError('joint replay denominator differs')
    print(dict(status='passed_isolated_stage67_pilot_replay',physical_stages=4,endpoint_checks=endpoints,Boolean_FF_checks=FF,software_queries=queries,
        covered=covered,zero_G_failure_preserved=True,new_EDA_calls=0,full_D_ready=False),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=('package','replay'));parser.add_argument('--root',type=Path);parser.add_argument('--evidence',type=Path,required=True);args=parser.parse_args()
    if args.action=='package':package(args.root.resolve(),args.evidence.resolve())
    else:replay(args.evidence.resolve())
