"""Complete remaining already-admitted diagnostic points with <=3 job slots."""
from concurrent.futures import ThreadPoolExecutor,as_completed
import argparse
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import Ledger,usage
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.model_steps123_qualification import task_run


def run(folder):
    a=read(folder/'admission.json');progress=read(folder/'progress.json');before=read(Ledger().path)
    if progress['completed'] or progress['errors']:raise ValueError('new wave only; preserve predecessor attempts')
    pending=[]
    for task in a['tasks']:
        if task.get('inherit_completed'):
            ref=task['inherit_completed'];p=Path(ref['directory'])
            if sha(p/'grt-labels.json')!=ref['grt_label_sha256'] or sha(p/'synth-labels.json')!=ref['synth_label_sha256']:raise ValueError('inherited complete point differs')
            progress['completed'].append(task['id'])
        else:pending.append(task)
    progress['phase']='running_finite_diagnostics';write(folder/'progress.json',progress)
    try:
        with ThreadPoolExecutor(max_workers=3) as pool:
            futures={pool.submit(task_run,folder,task):task for task in pending}
            for f in as_completed(futures):
                task=futures[f]
                try:f.result();progress['completed'].append(task['id'])
                except Exception as e:progress['errors'].append(dict(task=task['id'],error=str(e)))
                write(folder/'progress.json',progress)
        progress['phase']='finite_qualification_complete' if not progress['errors'] else 'stopped_on_error';write(folder/'progress.json',progress)
    finally:
        after=read(Ledger().path);write(folder/'wave-resource-increment.json',dict(entries=after['entries'][len(before['entries']):],usage=usage(after['entries']),training_rows=0))
    print(progress,flush=True)
    if progress['errors']:raise RuntimeError('diagnostic errors retained; completed checkpoints are not repeated')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);a=p.parse_args();run(a.folder.resolve())
