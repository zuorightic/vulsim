"""Measurement-only successor fixing the workload runner's double job lease.

The original admission, implementation, optimization commands and all failures
are retained. Unattempted physical tasks use their original finite admission.
Four pilot clock readouts have a distinct, support-only correction admission.
All other readouts remain in the physical task's single live job lease.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

from .workload_abcd import ROOT,read,write,sha
from .workload_backend import ComparisonLedger,verify_freeze,VERSION as ORIGINAL_VERSION
from .budget import Ledger,POLICY
from .platforms import profile

VERSION='nine-workload-measurement-lease-correction-v2'


def verify(root):
    a=read(root/'measurement-correction.json');parent=read(root/'admission.json')
    if (a['version']!=VERSION or sha(root/'admission.json')!=a['parent_admission_sha256']
            or parent['version']!=ORIGINAL_VERSION or sha(POLICY)!=parent['policy_sha256']):
        raise ValueError('measurement correction identity changed')
    verify_freeze(parent['selection_freeze'])
    for name,h in a['sources'].items():
        if sha(ROOT/name)!=h or sha(root/'measurement-correction-source'/name)!=h:
            raise ValueError('measurement correction source changed: '+name)
    for name,h in parent['sources'].items():
        if sha(ROOT/name)!=h or sha(root/'measurement-source'/name)!=h:
            raise ValueError('parent measurement source changed: '+name)
    return a,parent


def admit(root):
    if (root/'measurement-correction.json').exists():raise ValueError('preserve correction admission')
    parent=read(root/'admission.json');verify_freeze(parent['selection_freeze'])
    limits=read(POLICY)['resources'];usage=Ledger().summary()
    extra_wall=120*len(parent['capacity_pilot_task_ids'])
    if (usage['walltime_s']+extra_wall>limits['max_global_walltime_h']*3600
            or usage['CPU_time_s']+4*extra_wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('finite readout correction envelope unfunded')
    files=[Path(__file__),ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl']
    sources={}
    for p in files:
        n=p.relative_to(ROOT);dest=root/'measurement-correction-source'/n
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest);sources[str(n)]=sha(p)
    a=dict(version=VERSION,id=parent['id']+'-clock-lease-v2',
           created_at=datetime.now(timezone.utc).isoformat(),
           parent_admission_sha256=sha(root/'admission.json'),sources=sources,
           correction='one job lease spans physical implementation and fixed-DB readout',
           pilot_readout_task_ids=parent['capacity_pilot_task_ids'],
           extra_call_caps=dict(synth=0,grt=0,support=len(parent['capacity_pilot_task_ids'])),
           extra_leaf_walltime_s=120*len(parent['capacity_pilot_task_ids']),
           automatic_retries=0,model_changed=False,selection_changed=False,RTL_changed=False,
           application_PPA_feedback=False)
    write(root/'measurement-correction.json',a)
    write(root/'backend-corrected-progress.json',dict(status='admitted',completed=[],errors=[],active=[]))
    verify(root);return a


class ClockLedger(Ledger):
    def __init__(self,root,task):super().__init__();self.root,self.task=root,task

    def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
        a,parent=verify(self.root)
        if (stage is not None or timeout_s!=120 or threads!=4 or purpose!='final_evaluation'
                or self.task['id'] not in a['pilot_readout_task_ids']):
            raise ValueError('correction permits only one fixed-DB pilot support readout')
        entries=[e for e in read(self.path)['entries'] if e.get('admission_id')==a['id']]
        if any(e.get('task_id')==self.task['id'] for e in entries) or len(entries)>=a['extra_call_caps']['support']:
            raise ValueError('clock correction already attempted; no automatic retry')
        return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)


def clock(root,task,ledger):
    """Same frozen RR/IR/RO measurement, inside the caller's live job lease."""
    from .processes import run_command
    verify(root);directory=root/'runs'/task['id'];m=read(directory/'manifest.json')
    if m['status']!='completed' or not any(x['stage']=='grt' for x in m['metrics']):
        raise ValueError('fixed-DB readout requires a completed physical implementation')
    result_dir=directory/'results/asap7/arithmetic_probe/base'
    sdc=(result_dir/'5_1_grt.sdc').read_text()
    if any(t in sdc for t in ('set_multicycle_path','set_false_path','set_max_delay','set_clock_groups','set_disable_timing')):
        raise ValueError('unsupported full clock timing exception')
    folder=root/'clock-readout-v2'/task['id'];folder.mkdir(parents=True,exist_ok=False)
    fixed={str(result_dir/n):sha(result_dir/n) for n in ('5_1_grt.odb','5_1_grt.sdc')}
    template=(ROOT/'experiments/arithmetic_dse/reference_assets/workload_minimum_period_v1.tcl').read_text()
    p=profile('asap7');output=folder/'period.tsv'
    for key,value in dict(PERIOD=task['period_ps'],OUTPUT=output,TRANSITION=p['clock_transition_ps'],
                          SETUP=p['setup_uncertainty_ps'],HOLD=p['hold_uncertainty_ps']).items():
        template=template.replace('@'+key+'@',str(value))
    script=folder/'period.tcl';script.write_text(template)
    base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))
    command=base+['run','RUN_SCRIPT='+str(script),'RUN_LOG_NAME_STEM=workload_clock_limit',
                  'VULSIM_EVAL_DB=5_1_grt.odb','VULSIM_EVAL_SDC=5_1_grt.sdc']
    job=next(j for j in read(ledger.path)['jobs'] if j['id']==ledger.job_id)
    ctx={k:job[k] for k in ('target_platform','admission_id','task_id')}
    env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',QT_QPA_PLATFORM='offscreen')
    reservation=ledger.reserve(None,120,4,'final_evaluation',command,folder/'readout',context=ctx)
    record=run_command(command,folder,'readout',120,env,8192,cpu_limit_s=reservation['CPU_time_s'])
    ledger.finish(reservation,record);write(folder/'command.json',dict(record,budget_reservation_id=reservation['id']))
    if record['exit_code']:raise ValueError('fixed-DB clock readout failed: '+record['log'])
    if any(sha(n)!=h for n,h in fixed.items()):raise ValueError('physical checkpoint changed during readout')
    rows={name:dict(slack_ps=float(slack),required_period_ps=float(period)) for name,slack,period in
          (line.split('\t') for line in output.read_text().splitlines()[1:])}
    full=rows['full_setup_threshold'];metric=m['metrics'][-1]
    if abs(full['slack_ps']-metric['setup_worst_slack_ps'])>.005:
        raise ValueError('path classes do not reproduce full setup WNS')
    value=full['required_period_ps']
    write(folder/'result.json',dict(task=task['id'],target_ps=task['period_ps'],
          full_setup_minimum_period_ps=value,maximum_frequency_MHz=1e6/value,
          area_um2=metric['cell_area_um2'],hold_WNS_ps=metric['hold_worst_slack_ps'],
          hold_review_required=metric['hold_review_required'],classes=rows,fixed_inputs=fixed,
          measurement_correction_sha256=sha(root/'measurement-correction.json'),
          scope='same post-CTS grt cells and RC; full RR/IR/RO incl IO=0.2T and reset; hold separate'))
    return task['id']


def run_task(root,task,only_clock=False):
    from .backend import _evaluate
    correction,parent=verify(root)
    if only_clock:
        ledger=ClockLedger(root,task);identity=correction['id']
    else:ledger=ComparisonLedger(root,task);identity=parent['id']
    with ledger.job(dict(target_platform='asap7',admission_id=identity,task_id=task['id'])):
        if not only_clock:
            args=SimpleNamespace(out=root/'runs'/task['id'],platform='asap7',threads=4,
                stage='grt',memory_limit_mib=8192,period_ps=task['period_ps'],period_role='frozen_case_target',
                abc_target_ps=task['abc_target_ps'],io_delay_max_ps=None,budget_purpose='final_evaluation',
                admission_id=parent['id'],task_id=task['id'],sample_contract=None,admission=root/'admission.json',
                resume_synth_from=None,orfs=Path('/home/zyrv/OpenROAD-flow-scripts'),rtl=Path(task['rtl']),
                top='Workload',synth_timeout_s=300,route_timeout_s=1200,selection_freeze=Path(parent['selection_freeze']))
            if _evaluate(args,ledger):raise ValueError(read(args.out/'manifest.json').get('failure_reason','backend failed'))
        return clock(root,task,ledger)


def run(root,task_ids=None,only_clock=False):
    _,parent=verify(root);progress_path=root/'backend-corrected-progress.json'
    progress=read(progress_path)
    tasks=[t for t in parent['tasks'] if task_ids is None or t['id'] in task_ids]
    if task_ids is not None and {t['id'] for t in tasks}!=set(task_ids):raise ValueError('unknown task')
    if only_clock and task_ids is None:raise ValueError('name completed pilot checkpoint readouts explicitly')
    if not only_clock and task_ids is None:
        if not all((root/'clock-readout-v2'/t/'result.json').exists() for t in parent['capacity_pilot_task_ids']):
            raise ValueError('complete capacity pilot implementations and clock readouts first')
    done=set(progress['completed'])|{e['task'] for e in progress['errors']}
    tasks=[t for t in tasks if t['id'] not in done and (only_clock or not (root/'runs'/t['id']).exists())]
    if progress['active']:raise ValueError('correction batch already active')
    progress.update(status='running',active=[t['id'] for t in tasks]);write(progress_path,progress)
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(run_task,root,t,only_clock):t for t in tasks}
        for f in as_completed(futures):
            t=futures[f]
            try:f.result();progress['completed'].append(t['id'])
            except Exception as e:progress['errors'].append(dict(task=t['id'],reason=str(e)))
            progress['active'].remove(t['id']);write(progress_path,progress)
    progress['status']='batch_settled';write(progress_path,progress);return progress


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run','clocks'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--task',action='append');a=p.parse_args()
    root=a.root.resolve()
    print(admit(root) if a.action=='admit' else run(root,a.task,a.action=='clocks'))
