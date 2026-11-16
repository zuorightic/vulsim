"""One predeclared cold repeat of each near-target MAC32 D result.

Separate evaluation only. Original selections, targets, model parameters and
the 76 main method rows are not replaced by these repeat observations.
"""
import argparse
from pathlib import Path

from .workload_abcd import read, write, sha
from .workload_tight_run import DEFAULT
from .workload_tight_continue import extend_admission, drive
from . import workload_final_backend as physical
from .budget import Ledger


def plan(root):
    original=physical.verify(root/'final-mac32');tasks=[]
    methods=read(root/'final-mac32-methods.json')['records']
    for T in (750,1000):
        method=next(r['methods']['D'] for r in methods if r['target']['T_ps']==T)
        t=dict(next(t for t in original['tasks'] if t['id']==method['task_id']))
        readout=root/'final-mac32/runs'/t['id']/'clock-readout/result.json'
        t.update(id=t['id']+'-repeat',repeat_of=method['task_id'],
            original_clock_readout=str(readout),original_clock_readout_sha256=sha(readout))
        tasks.append(t)
    value=dict(version='tight-MAC-near-target-cold-repeat-v1',targets_ps=[750,1000],tasks=tasks,
        purpose='check near-target setup/hold classification stability',repeat_per_record=1,
        automatic_retries=0,application_PPA_for_model_or_selection=False,
        replace_main_results=False,source_sha256=sha(__file__))
    p=root/'near-target-repeat-plan.json'
    if p.exists() and read(p)!=value:raise ValueError('repeat plan identity changed')
    if not p.exists():write(p,value)
    return value


def run(root):
    value=plan(root)
    if Ledger().summary()['pending']:raise ValueError('main physical wave must settle before repeat admission')
    batch=root/'mac32-tight-near-target-repeat-v1'
    if batch.exists():raise ValueError('repeat already admitted; do not retry automatically')
    physical.admit(batch,value['tasks'],'final_evaluation');extend_admission(batch)
    a=read(batch/'admission.json');f=read(batch/'freeze.json')
    for p in (Path(__file__),root/'near-target-repeat-plan.json'):
        f['files'][str(p)]=sha(p)
    write(batch/'freeze.json',f);a['freeze_sha256']=sha(batch/'freeze.json');write(batch/'admission.json',a)
    drive([batch]);rows=[]
    for task in physical.verify(batch)['tasks']:
        before=read(task['original_clock_readout']);p=batch/'runs'/task['id']/'clock-readout/result.json'
        row=dict(T_ps=task['period_ps'],task=task['id'],original=before,
            original_sha256=task['original_clock_readout_sha256'])
        if p.exists():
            after=read(p);T=task['period_ps']
            row.update(status='measured_grt',repeat=after,repeat_sha256=sha(p),
                delta_Tmin_ps=after['full_setup_minimum_period_ps']-before['full_setup_minimum_period_ps'],
                delta_area_um2=after['area_um2']-before['area_um2'],
                setup_classification_stable=(before['full_setup_minimum_period_ps']<=T)==(after['full_setup_minimum_period_ps']<=T),
                hold_classification_stable=(before['hold_WNS_ps']>=0)==(after['hold_WNS_ps']>=0))
        else:row['status']='failed'
        rows.append(row)
    result=dict(rows=rows,application_PPA_for_model_or_selection=False,main_results_replaced=False,
        only_these_two_fixed_implementations_repeated=True,not_a_general_measurement_noise_bound=True)
    write(root/'near-target-repeat-results.json',result);return result


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['plan','run']);p.add_argument('--root',type=Path,default=DEFAULT)
    a=p.parse_args();print((plan if a.action=='plan' else run)(a.root))
