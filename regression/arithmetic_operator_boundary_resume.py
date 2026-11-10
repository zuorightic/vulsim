"""Report-only completion of the exact two paid mapped-boundary probes.

The original namespace used folder.name and collided with a historical probes-v1
admission in its support-count guard. Both syntheses succeeded; preserve them.
This continuation has a unique identity, one support leaf and zero EDA rebuilds.
"""
import argparse
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger,usage
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.model_boundary_probe import ASSET,analyze
from experiments.arithmetic_dse.processes import run_command


def run(parent,out):
    out.mkdir(parents=True,exist_ok=False);a=read(parent/'admission.json');before=read(Ledger().path)
    if len(a['tasks'])!=2 or {t['id'] for t in a['tasks']}!={'protected','flat'}:raise ValueError('wrong parent probe scope')
    manifests={};charges=[]
    for task in a['tasks']:
        path=parent/'runs'/task['id'];m=read(path/'manifest.json')
        if m['status']!='completed' or [g['stage'] for g in m['metrics']]!=['synth']:raise ValueError('exact completed synthesis required')
        for command in m['commands']:
            entry=next(e for e in before['entries'] if e['id']==command['budget_reservation_id'])
            if entry['status']!='completed' or entry['admission_sha256']!=sha(parent/'admission.json'):raise ValueError('paid ancestry mismatch')
            charges.append(entry['id'])
        for name,h in m['evidence_sha256'].items():
            if sha(path/name)!=h:raise ValueError('parent physical bytes changed')
        manifests[task['id']]=sha(path/'manifest.json')
    prefix=parent/'runs/flat/reports/asap7/arithmetic_probe/base/boundary_instances.tsv'
    if prefix.exists():raise ValueError('report already exists; do not repeat')
    if sha(ASSET)!=a['source_sha256'][str(ASSET.relative_to(ROOT))]:raise ValueError('original report adapter changed')
    ctx=dict(target_platform='asap7',admission_id='operator-boundary-20261110-census-resume-v1',task_id='flat-paid-synth-census')
    write(out/'admission.json',dict(id=ctx['admission_id'],parent_admission_sha256=sha(parent/'admission.json'),manifests=manifests,paid_parent_leaf_ids=charges,
        support_leaves=1,synth=0,grt=0,final=0,reason='metadata support counter used non-unique folder name; no physical failure; complete only missing report on exact paid checkpoint',
        source_role='not_training',retries=0))
    folder=parent/'runs/flat';m=read(folder/'manifest.json');base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
    command=base+['run','RUN_SCRIPT='+str(ASSET),'RUN_LOG_NAME_STEM=boundary_census','VULSIM_EVAL_DB=1_synth.odb','VULSIM_EVAL_SDC=1_synth.sdc']
    ledger=Ledger();env=os.environ.copy();env.update(OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',YOSYS_MAX_THREADS='4',PYTHONDONTWRITEBYTECODE='1')
    try:
        with ledger.job(ctx):
            r=ledger.reserve(None,120,4,'not_training_paid_synth_report_continuation',command,out/'census',context={**ctx,'admission_sha256':sha(out/'admission.json')})
            record=run_command(command,out,'census',120,env,8192,cpu_limit_s=r['CPU_time_s']);ledger.finish(r,record)
            write(out/'commands.json',[dict(**record,budget_reservation_id=r['id'])])
            if record['exit_code']:raise ValueError('report-only continuation failed')
            for name,h in m['evidence_sha256'].items():
                if sha(folder/name)!=h:raise ValueError('report-only continuation modified original evidence')
            if sha(folder/'manifest.json')!=manifests['flat']:raise ValueError('original manifest changed')
    finally:
        after=read(ledger.path);write(out/'resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),PPA_calls=0))
    analyze(parent)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args();run(args.parent.resolve(),args.out.resolve())
