"""Paid admission checks and non-launching negative controls for finite probes."""
import argparse
import copy
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse import model_fast_probe as probe
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha


def guards(folder,out):
    a=probe.verify(folder);before=read(probe.Ledger().path);task=a['tasks'][0];rejected=[]
    tests=[('changed_clock',dict(task,period_ps=999), 'synth',300,4),
           ('training_role',dict(task,source_role='train'),'synth',300,4),
           ('wrong_threads',task,'synth',300,2),('unregistered_stage',task,'final',1200,4),
           ('excess_synth_timeout',task,'synth',301,4)]
    for name,changed,stage,timeout,threads in tests:
        ledger=probe.FastLedger(folder,changed)
        try:ledger.reserve(stage,timeout,threads,'negative_no_launch',['never-executed'],out/name,context={})
        except ValueError:rejected.append(name)
        else:raise ValueError('admission guard unexpectedly reserved a physical leaf')
    after=read(probe.Ledger().path)
    if before['entries']!=after['entries']:raise ValueError('negative controls reserved or modified any leaf')
    result=dict(status='passed',admission_sha256=sha(folder/'admission.json'),rejected=rejected,
        physical_reservations_added=0,source_role='not_training',model_fit_allowed=False)
    write(out/'guards.json',result);print(json.dumps(result),flush=True)


def prepare(out,folder,proof,parent=None):
    from experiments.arithmetic_dse.budget import Ledger,usage
    from experiments.arithmetic_dse.processes import run_command
    out.mkdir(parents=True,exist_ok=False);ledger=Ledger();before=read(ledger.path);ctx=dict(target_platform='asap7',admission_id=out.name,task_id='fast-finite-probe-admission')
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4');commands=[]
    with ledger.job(ctx):
        def execute(cmd,name):
            reservation=ledger.reserve(None,300,4,'fast_probe_admission_and_guards',cmd,out/name,context=ctx);record=run_command(cmd,out,name,300,env,8192,cpu_limit_s=reservation['CPU_time_s']);ledger.finish(reservation,record)
            commands.append({**record,'budget_reservation_id':reservation['id']});write(out/'commands.json',commands)
            if record['exit_code']:raise RuntimeError(name+' failed: '+record['log'])
            print(name+': '+Path(record['log']).read_text()[-1200:],flush=True)
        if parent:
            execute([sys.executable,'-B',str(ROOT/'regression/arithmetic_fast_measurement.py'),'reader-successor','--parent',str(parent),'--out',str(out/'reader-successor')],'reader-successor')
            proof=out/'reader-successor/proof.json'
        execute([sys.executable,'-B','-m','experiments.arithmetic_dse.model_fast_probe','prepare','--folder',str(folder),'--proof',str(proof)]+(['--parent',str(parent)] if parent else []),'prepare')
        execute([sys.executable,'-B',str(Path(__file__)),'guards','--folder',str(folder),'--out',str(out)],'guards')
    after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries'])))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','guards'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--proof',type=Path);p.add_argument('--parent',type=Path);a=p.parse_args()
    if a.action=='guards':guards(a.folder.resolve(),a.out.resolve())
    elif not a.proof:p.error('--proof required')
    else:prepare(a.out.resolve(),a.folder.resolve(),a.proof.resolve(),a.parent.resolve() if a.parent else None)
