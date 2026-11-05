"""Bounded background collection; stop at the requested acquisition checkpoint."""
import argparse
from datetime import datetime,timezone
import fcntl
import json
import os
from pathlib import Path
import subprocess
import sys

from .model_target_collection import ROOT,read,selected_tasks,run_directory,verify_plan


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--folder',type=Path,required=True)
    ap.add_argument('--mode',choices=('initial','conditional','test'),default='initial')
    ap.add_argument('--screening',type=Path,help='insufficient frozen baseline required for conditional training')
    ap.add_argument('--selection',type=Path,help='validated frozen selection required for independent test')
    args=ap.parse_args();folder=args.folder.resolve();plan=verify_plan(folder/'plan.json')
    support=ROOT/'build/step7-models-20261102/support.py'
    def state(phase,**details):
        data={'phase':phase,'updated_at':datetime.now(timezone.utc).isoformat(),**details}
        tmp=folder/'advance-progress.tmp';tmp.write_text(json.dumps(data,indent=2)+'\n');os.replace(tmp,folder/'advance-progress.json')
        with (folder/'advance-events.jsonl').open('a') as stream:stream.write(json.dumps(data)+'\n')
        print(json.dumps(data),flush=True)
    def pending(mode):
        todo=[]
        for t in selected_tasks(plan,mode):
            d=run_directory(folder,t)
            if d.exists():
                if not (d/'manifest.json').exists() or read(d/'manifest.json')['status']!='completed':
                    raise ValueError('failed/incomplete task; explicit diagnosis required: '+t['id'])
            else:todo.append(t)
        return todo
    with (folder/'advance.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise ValueError('automatic collection already running')
        try:
            if args.mode=='conditional':
                from .model_target_fit import verify_screening
                verify_screening(args.screening,folder/'plan.json')
            elif args.mode=='test':
                from .model_target_fit import verify_selection
                verify_selection(args.selection,folder/'plan.json')
            elif args.screening or args.selection:
                raise ValueError('initial collection does not consume a fitted selection')
            modes=('baseline','validation') if args.mode=='initial' else (args.mode,)
            for mode in modes:
                while pending(mode):
                    if (folder/'PAUSE').exists():state('paused',next_phase=mode);return
                    number=1
                    while (folder/'waves'/f'{mode}-parallel-{number:03d}.json').exists():number+=1
                    wave=folder/'waves'/f'{mode}-parallel-{number:03d}.json'
                    limit=4 if number==1 else 24
                    state('collecting',mode=mode,remaining_at_wave_start=len(pending(mode)),wave=str(wave),parallel_jobs=4,threads_per_tool=4)
                    command=[sys.executable,'-B',str(support),f'{plan["id"]}-{mode}-{number:03d}-admit','180',
                             sys.executable,'-B','-m','experiments.arithmetic_dse.model_target_collection','admit',
                             '--folder',str(folder),'--mode',mode,'--limit',str(limit),'--out',str(wave)]
                    if mode=='conditional':command+=['--screening',str(args.screening.resolve())]
                    if mode=='test':command+=['--selection',str(args.selection.resolve())]
                    subprocess.run(command,cwd=ROOT,check=True)
                    subprocess.run([sys.executable,'-B','-m','experiments.arithmetic_dse.model_target_collection','run',
                                    '--wave',str(wave)],cwd=ROOT,check=True)
                state('phase_complete',mode=mode)
            if args.mode=='initial':
                state('initial_collection_complete',next_step='review/extract/fit; conditional and independent test not launched',
                      baseline_total=80,validation_total=260)
            elif args.mode=='conditional':
                state('conditional_collection_complete',next_step='extract fitting-full, fit and validate; independent test not launched',
                      conditional_total=len(selected_tasks(plan,'conditional')))
            else:
                state('test_collection_complete',next_step='extract, once-only independent evaluation, verify and conditional publication',
                      test_total=len(selected_tasks(plan,'test')))
        except BaseException as error:
            state('stopped_on_error',error=str(error));raise


if __name__=='__main__':main()
