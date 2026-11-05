"""Collect capacity pilots, verify them, then train/validation; never launch test."""
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

from .model_m2_collection import ROOT,read,verify_plan,CONFIG,run_directory


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True);args=ap.parse_args()
    folder=args.folder.resolve();p=verify_plan(folder/'plan.json');cfg=read(CONFIG)
    support=ROOT/'build/step7-models-20261102/support.py'
    def state(phase,**details):
        value={'phase':phase,'updated_at':datetime.now(timezone.utc).isoformat(),**details}
        tmp=folder/'progress.tmp';tmp.write_text(json.dumps(value,indent=2)+'\n');os.replace(tmp,folder/'progress.json')
        with (folder/'events.jsonl').open('a') as stream:stream.write(json.dumps(value)+'\n')
        print(json.dumps(value),flush=True)
    def call(arguments,stem,timeout):
        subprocess.run([sys.executable,'-B',str(support),stem,str(timeout),sys.executable,'-B',*arguments],cwd=ROOT,check=True)
    def pending(mode):
        ts=[t for t in p['tasks'] if t['id'] in cfg['capacity_pilots']] if mode=='pilots' else [t for t in p['tasks'] if t['split']==mode]
        missing=[]
        for t in ts:
            d=run_directory(folder,t)
            if d.exists():
                if not (d/'manifest.json').exists() or read(d/'manifest.json')['status']!='completed':raise ValueError('failed M2 task requires diagnosis: '+t['id'])
            else:missing.append(t)
        return missing
    with (folder/'advance.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('M2 advance driver already running')
        try:
            if (p.get('timeout_recovery') or {}).get('rolling_fitting'):
                if not (folder/'capacity-proof.json').exists():
                    state('checking_capacity')
                    call(['-m','experiments.arithmetic_dse.model_m2_collection','capacity','--folder',str(folder)],p['id']+'-capacity',300)
                if (folder/'PAUSE').exists():state('paused',mode='fitting');return
                wave=folder/'waves/fitting-001.json'
                state('collecting',mode='fitting',wave=str(wave),parallel_jobs=4,threads_per_tool=4,rolling_train_validation=True)
                call(['-m','experiments.arithmetic_dse.model_m2_collection','admit','--folder',str(folder),'--mode','fitting',
                      '--limit',str(p['timeout_recovery']['priority_wave_limit']),'--out',str(wave)],p['id']+'-fitting-admit',180)
                subprocess.run([sys.executable,'-B','-m','experiments.arithmetic_dse.model_m2_collection','run','--wave',str(wave)],cwd=ROOT,check=True)
                remaining=[t for t in p['tasks'] if t['split'] in ('train','validation') and not (run_directory(folder,t)/'manifest.json').exists()]
                if remaining:state('paused',mode='fitting');return
                state('fitting_collection_complete',next_step='extract and fit primitives; independent test remains locked',test_launched=False)
                return
            for mode in ('pilots','train','validation'):
                if mode!='pilots' and not (folder/'capacity-proof.json').exists():
                    state('checking_capacity')
                    call(['-m','experiments.arithmetic_dse.model_m2_collection','capacity','--folder',str(folder)],p['id']+'-capacity',300)
                while pending(mode):
                    if (folder/'PAUSE').exists():state('paused',mode=mode);return
                    number=1
                    while (folder/'waves'/f'{mode}-{number:03d}.json').exists():number+=1
                    wave=folder/'waves'/f'{mode}-{number:03d}.json'
                    state('collecting',mode=mode,remaining_at_wave_start=len(pending(mode)),wave=str(wave),parallel_jobs=4,threads_per_tool=4)
                    recovery=p.get('timeout_recovery') or {}
                    recovering=mode=='train' and any(t['id'] in recovery.get('priority_task_ids',[]) for t in pending(mode))
                    limit=recovery.get('priority_wave_limit',2) if recovering else (4 if mode=='pilots' else 24)
                    call(['-m','experiments.arithmetic_dse.model_m2_collection','admit','--folder',str(folder),'--mode',mode,
                          '--limit',str(limit),'--out',str(wave)],p['id']+f'-{mode}-{number:03d}-admit',180)
                    subprocess.run([sys.executable,'-B','-m','experiments.arithmetic_dse.model_m2_collection','run','--wave',str(wave)],cwd=ROOT,check=True)
            state('fitting_collection_complete',next_step='extract and fit primitives; independent test remains locked',test_launched=False)
        except BaseException as error:
            state('stopped_on_error',error=str(error));raise


if __name__=='__main__':main()
