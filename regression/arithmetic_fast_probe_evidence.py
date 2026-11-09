"""Accounted raw replay, packaging, isolated verification and tamper checks."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse import model_fast_probe_evidence as evidence
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='fast-probe-isolated-') as td:
        temp=Path(td);local=temp/'evidence';source=temp/'unpacked';shutil.copytree(folder,local);evidence.unpack(local,source)
        code='''import builtins,io,os,runpy,subprocess,sys
from pathlib import Path
source,folder=sys.argv[1:]
def guard(fn):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)) and str(Path(path).resolve()).startswith('/home/zyrv/'):raise RuntimeError('original project/build/tools/Liberty read forbidden')
  return fn(path,*a,**kw)
 return checked
builtins.open=guard(builtins.open);io.open=guard(io.open)
def deny(*a,**kw):raise RuntimeError('raw replay subprocess forbidden')
subprocess.Popen=deny
sys.path.insert(0,source);sys.argv=['sealed','verify','--folder',folder]
runpy.run_module('experiments.arithmetic_dse.model_fast_probe_evidence',run_name='__main__')
'''
        env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        cmd=[sys.executable,'-B','-c',code,str(source/'source'),str(local)]
        result=subprocess.run(cmd,cwd=temp,env=env,capture_output=True,text=True)
        if result.returncode:raise ValueError('isolated diagnosis failed: '+result.stderr[-2500:])
        for name in ('audit.json','replay.json',read(local/'replay.json')['chunks'][0]):
            path=local/name;original=path.read_bytes();changed=bytearray(original);changed[len(changed)//2]^=1;path.write_bytes(changed)
            result=subprocess.run(cmd,cwd=temp,env=env,capture_output=True,text=True);path.write_bytes(original)
            if not result.returncode or 'fast diagnosis evidence identity mismatch' not in result.stderr:raise ValueError('diagnosis tamper accepted')
        print('PASS isolated raw paths/area/FF/SDC replay; original home and subprocesses denied;3 tamper rejections',flush=True)


def run(folder,out,published):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);ctx=dict(target_platform='asap7',admission_id=out.name,task_id='fast-finite-probe-evidence')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4');commands=[]
    with ledger.job(ctx):
        def execute(cmd,name,timeout=600):
            r=ledger.reserve(None,timeout,4,'fast_probe_raw_replay_evidence',cmd,out/name,context=ctx);record=run_command(cmd,out,name,timeout,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            commands.append({**record,'budget_reservation_id':r['id']});write(out/'commands.json',commands)
            if record['exit_code']:raise RuntimeError(name+' failed; see '+record['log'])
            print(name+': '+Path(record['log']).read_text()[-1500:],flush=True)
        execute([sys.executable,'-B','-m','experiments.arithmetic_dse.model_fast_probe_evidence','analyze','--folder',str(folder),'--out',str(out/'audit')],'raw-audit')
        execute([sys.executable,'-B','-m','experiments.arithmetic_dse.model_fast_probe_evidence','seal','--folder',str(folder),'--audit',str(out/'audit/audit.json'),'--out',str(published)],'seal')
        execute([sys.executable,'-B','-m','experiments.arithmetic_dse.model_fast_probe_evidence','verify','--folder',str(published)],'portable')
        execute([sys.executable,'-B','-m','experiments.arithmetic_dse.model_fast_probe_evidence','verify','--folder',str(published),'--external'],'external')
        execute([sys.executable,'-B',str(Path(__file__)),'isolated','--evidence',str(published)],'isolated')
    after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries'])))
    write(published/'publication-closure.json',dict(manifest_sha256=sha(published/'manifest.json'),entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),new_PPA_calls=0))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('run','isolated'));p.add_argument('--folder',type=Path);p.add_argument('--out',type=Path);p.add_argument('--evidence',type=Path,required=True);a=p.parse_args()
    if a.action=='isolated':isolated(a.evidence.resolve())
    elif not a.folder or not a.out:p.error('--folder and --out required')
    else:run(a.folder.resolve(),a.out.resolve(),a.evidence.resolve())
