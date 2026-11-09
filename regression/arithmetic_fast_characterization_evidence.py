"""Small source-bound software/reader evidence with isolated raw-path replay."""
import argparse
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def seal(software,node_probes,out):
    from experiments.arithmetic_dse import model_fast_scan,model_fast_path,model_fast_node_probe
    out.mkdir(parents=True,exist_ok=False)
    sources={}
    for name in ('regression/arithmetic_fast_characterization.py','regression/arithmetic_fast_characterization_evidence.py',
                 'experiments/arithmetic_dse/model_fast_scan.py','experiments/arithmetic_dse/model_fast_path.py',
                 'experiments/arithmetic_dse/model_fast_node_probe.py','experiments/arithmetic_dse/model_fast_preflight.py',
                 'experiments/arithmetic_dse/budget.py','experiments/arithmetic_dse/processes.py',
                 'experiments/arithmetic_dse/configs/model_fast_scan_v1.json',
                 'experiments/arithmetic_dse/configs/model_fast_scan_v2.json',
                 'experiments/arithmetic_dse/reference_assets/fast_node_probe.tcl',
                 'experiments/arithmetic_dse/reference_assets/snapshot.tcl'):
        p=ROOT/name;sources[name]=dict(text=p.read_text(),sha256=sha(p))
    frozen=read(software/'manifest.json')
    if any(sha(ROOT/name)!=h for name,h in frozen['sources'].items()):
        raise ValueError('software producer changed since execution')
    plan=read(node_probes/'readback-plan.json')
    if any(sha(ROOT/name)!=h for name,h in plan['sources'].items()):
        raise ValueError('node readback producer changed since execution')
    cases=[]
    for row in read(node_probes/'results.json'):
        folder=node_probes/row['task_id']
        names=('node_before_reference_paths.tsv','node_after_reference_paths.tsv','node_boundaries.tsv',
               'node_slews_after.tsv','node_points.tsv','node_node.tsv','node_node.rpt')
        cases.append(dict(task_id=row['task_id'],result=row,files={n:(folder/n).read_text() for n in names},
                          original_reference_paths=(folder/'node_before_reference_paths.tsv').read_text()))
    bundle=dict(version='fast-characterization-evidence-v1',source_pool=sources,
                software_proof=read(software/'verification/proof.json'),
                path_witnesses=json.loads(gzip.decompress((software/'verification/path-witnesses.json.gz').read_bytes())),
                node_readbacks=cases,node_plan=plan,source_role='software_and_not_training_diagnosis',
                PPA_calls=0,physical_admission_allowed=False,full_D_ready=False)
    (out/'replay.json.gz').write_bytes(gzip.compress(json.dumps(bundle,sort_keys=True,separators=(',',':')).encode(),mtime=0))
    write(out/'summary.json',dict(version=bundle['version'],raw_paths=len(bundle['path_witnesses']),node_readbacks=len(cases),
          source_role=bundle['source_role'],scan_checks=bundle['software_proof']['scan'],PPA_calls=0,
          operator_maximum_coverage_qualified=False,full_D_ready=False))
    write(out/'manifest.json',dict(version=bundle['version'],files_sha256={p.name:sha(p) for p in out.iterdir() if p.is_file()},
          source_sha256={n:r['sha256'] for n,r in sources.items()},software_manifest_sha256=sha(software/'manifest.json'),
          node_plan_sha256=sha(node_probes/'readback-plan.json')))
    print(json.dumps(dict(status='sealed',raw_paths=len(bundle['path_witnesses']),node_readbacks=len(cases),bytes=sum(p.stat().st_size for p in out.iterdir()))),flush=True)


def unpack(folder,destination):
    manifest=read(folder/'manifest.json')
    for name,h in manifest['files_sha256'].items():
        if Path(name).name!=name or sha(folder/name)!=h:
            raise ValueError('characterization evidence identity mismatch')
    bundle=json.loads(gzip.decompress((folder/'replay.json.gz').read_bytes()))
    for name,row in bundle['source_pool'].items():
        p=Path(name)
        if p.is_absolute() or '..' in p.parts or hashlib.sha256(row['text'].encode()).hexdigest()!=row['sha256'] or manifest['source_sha256'][name]!=row['sha256']:
            raise ValueError('characterization source identity mismatch')
        target=destination/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(row['text'])
    return bundle


def portable(folder):
    from experiments.arithmetic_dse import model_fast_path,model_fast_node_probe
    from regression.arithmetic_fast_characterization import scan_checks,path_checks
    with tempfile.TemporaryDirectory(prefix='fast-characterization-replay-') as td:
        temp=Path(td);bundle=unpack(folder,temp/'source')
        normalize=lambda value:json.loads(json.dumps(value))
        if normalize(scan_checks())!=bundle['software_proof']['scan'] or normalize(path_checks())!=bundle['software_proof']['paths']:
            raise ValueError('software decisions no longer replay')
        for row in bundle['path_witnesses']:
            replay=model_fast_path.decompose(**row['replay_input'])
            if replay!=row['decomposition'] or row['source_role']!='not_training':
                raise ValueError('exclusive physical path ownership does not replay')
        for row in bundle['node_readbacks']:
            folder=temp/row['task_id'];folder.mkdir()
            for name,text in row['files'].items():
                if Path(name).name!=name:
                    raise ValueError('invalid readback member')
                (folder/name).write_text(text)
            original=temp/'original'/row['task_id'];(original/'reports/asap7/arithmetic_probe/base').mkdir(parents=True)
            (original/'reports/asap7/arithmetic_probe/base/vulsim_grt_reference_paths.tsv').write_text(row['original_reference_paths'])
            result=model_fast_node_probe.verify(folder,original);result['task_id']=row['task_id']
            if result!=row['result']:
                raise ValueError('internal node readback does not replay')
    print('PASS bounded scan, raw physical path ownership,4 internal node probes; no tools/build/ledger needed',flush=True)


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='fast-characterization-isolated-') as td:
        temp=Path(td);local=temp/'evidence';shutil.copytree(folder,local);unpack(local,temp/'source')
        code='''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
source,folder=sys.argv[1:]
def guard(fn):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):raise RuntimeError('original home/project/build/tools/ledger read forbidden')
  return fn(path,*a,**kw)
 return checked
builtins.open=guard(builtins.open);io.open=guard(io.open)
def deny(*a,**kw):raise RuntimeError('replay subprocess forbidden')
subprocess.Popen=deny
sys.path.insert(0,source);sys.argv=['sealed','portable','--evidence',folder]
runpy.run_path(str(Path(source)/'regression/arithmetic_fast_characterization_evidence.py'),run_name='__main__')
'''
        env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        cmd=[sys.executable,'-B','-c',code,str(temp/'source'),str(local)]
        result=subprocess.run(cmd,cwd=temp,env=env,capture_output=True,text=True)
        if result.returncode:
            raise ValueError('isolated characterization replay failed: '+result.stderr[-3000:])
        for name in ('replay.json.gz','summary.json'):
            p=local/name;raw=p.read_bytes();changed=bytearray(raw);changed[len(changed)//2]^=1;p.write_bytes(changed)
            result=subprocess.run(cmd,cwd=temp,env=env,capture_output=True,text=True);p.write_bytes(raw)
            if result.returncode==0 or 'characterization evidence identity mismatch' not in result.stderr:
                raise ValueError('characterization tamper accepted')
    print('PASS isolated replay with original home and subprocesses denied;2 tamper rejections',flush=True)


def run(software,node_probes,out,evidence):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);commands=[]
    ctx=dict(target_platform='asap7',admission_id=out.name,task_id='fast-characterization-evidence')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4')
    try:
        with ledger.job(ctx):
            def execute(cmd,name):
                r=ledger.reserve(None,180,4,'fast_characterization_evidence',cmd,out/name,context=ctx)
                record=run_command(cmd,out,name,180,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
                commands.append(dict(**record,budget_reservation_id=r['id']));write(out/'commands.json',commands)
                print(Path(record['log']).read_text()[-2200:],flush=True)
                if record['exit_code']:
                    raise RuntimeError('characterization evidence failed; costs retained')
            base=[sys.executable,'-B',str(Path(__file__))]
            execute(base+['seal','--software',str(software),'--node-probes',str(node_probes),'--evidence',str(evidence)],'seal')
            execute(base+['portable','--evidence',str(evidence)],'portable')
            execute(base+['isolated','--evidence',str(evidence)],'isolated')
    finally:
        after=read(ledger.path)
        write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))
    write(evidence/'publication-closure.json',dict(manifest_sha256=sha(evidence/'manifest.json'),
          entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('run','seal','portable','isolated'))
    parser.add_argument('--software',type=Path);parser.add_argument('--node-probes',type=Path);parser.add_argument('--out',type=Path)
    parser.add_argument('--evidence',type=Path,required=True);args=parser.parse_args()
    if args.action in ('run','seal') and (not args.software or not args.node_probes):
        parser.error('--software and --node-probes required')
    if args.action=='run':
        if not args.out:
            parser.error('--out required')
        run(args.software.resolve(),args.node_probes.resolve(),args.out.resolve(),args.evidence.resolve())
    elif args.action=='seal':seal(args.software.resolve(),args.node_probes.resolve(),args.evidence.resolve())
    elif args.action=='portable':portable(args.evidence.resolve())
    else:isolated(args.evidence.resolve())
