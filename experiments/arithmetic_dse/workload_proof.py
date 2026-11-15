"""One bounded alternative-solver proof of retained exact CTS repair netlists."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

from .workload_abcd import ROOT,read,write,sha
from .workload_backend_finish import verify as verify_parent
from .model_m2_phase_resume import validate_lec
from .budget import Ledger,POLICY
from .processes import run_command

VERSION='nine-workload-retained-CTS-proof-v1'


def admit(root,task_id,batch):
    _,parent=verify_parent(root);t=next(t for t in parent['tasks'] if t['id']==task_id)
    source=root/'runs'/task_id;m=read(source/'manifest.json');folder=root/'proofs'/batch
    if folder.exists() or m['status']!='failed' or m.get('failure_code')!='timeout':
        raise ValueError('new proof admission requires a retained settled timeout')
    log=source/'logs/asap7/arithmetic_probe/base/4_rsz_lec_check.log';text=log.read_text()
    if 'Starting solver' not in text or 'Circuits are IDENTICAL' in text:raise ValueError('not an unresolved complete LEC')
    counts=[]
    for kind in ('PIs','POs'):
        pair=[re.search(rf'size of {kind} in circuit {i}: (\d+)',text) for i in (0,1)]
        if any(p is None for p in pair) or pair[0][1]!=pair[1][1]:raise ValueError('LEC boundary mismatch')
        counts.append(int(pair[0][1]))
    physical=source/'results/asap7/arithmetic_probe/base'
    before,after=(physical/n for n in ('4_before_rsz_lec.v','4_after_rsz_lec.v'))
    executable=Path('/home/zyrv/OpenROAD-flow-scripts/tools/install/kepler-formal/bin/kepler-formal')
    inputs={str(p):sha(p) for p in (source/'manifest.json',before,after,executable,log)}
    inputs.update({lib['path']:lib['sha256'] for lib in m['libraries']})
    usage=Ledger().summary();limits=read(POLICY)['resources']
    if usage['walltime_s']+600>limits['max_global_walltime_h']*3600 or usage['CPU_time_s']+2400>limits['max_tool_CPU_time_h']*3600:
        raise ValueError('finite proof envelope unfunded')
    folder.mkdir(parents=True);files=[Path(__file__),ROOT/'experiments/arithmetic_dse/model_m2_phase_resume.py']
    sources={}
    for p in files:
        n=p.relative_to(ROOT);dest=folder/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(p,dest);sources[str(n)]=sha(p)
    a=dict(version=VERSION,id=parent['id']+'-'+batch,task_id=task_id,source=str(source),inputs=inputs,sources=sources,
           executable=str(executable),before=str(before),after=str(after),libraries=m['libraries'],
           expected_boundary=dict(primary_inputs=counts[0],primary_outputs=counts[1]),solver='glucose',
           timeout_s=600,threads=4,memory_limit_MiB=8192,call_caps=dict(synth=0,grt=0,support=1),
           automatic_retries=0,application_PPA_feedback=False)
    write(folder/'admission.json',a);return a


def run(root,batch):
    verify_parent(root);folder=root/'proofs'/batch;a=read(folder/'admission.json')
    if a['version']!=VERSION:raise ValueError('wrong proof admission')
    for n,h in a['inputs'].items():
        if sha(n)!=h:raise ValueError('changed exact proof input: '+n)
    for n,h in a['sources'].items():
        if sha(ROOT/n)!=h or sha(folder/'source'/n)!=h:raise ValueError('changed proof implementation')
    log=folder/'solver.log';config=folder/'request.json'
    write(config,dict(format='verilog',verification='lec',input_paths=[a['before'],a['after']],
          liberty_files=[lib['path'] for lib in a['libraries']],solver=a['solver'],log_file=str(log)))
    ledger=Ledger();ctx=dict(target_platform='asap7',admission_id=a['id'],task_id=a['task_id'])
    if any(e.get('admission_id')==a['id'] for e in read(ledger.path)['entries']):raise ValueError('one proof already attempted')
    command=[a['executable'],'--config',str(config)]
    env=dict(os.environ,OMP_NUM_THREADS='4',OPENBLAS_NUM_THREADS='4',QT_QPA_PLATFORM='offscreen')
    with ledger.job(ctx):
        reservation=ledger.reserve(None,600,4,'final_evaluation',command,folder/'solver',context=ctx)
        record=run_command(command,folder,'solver-command',600,env,8192,cpu_limit_s=reservation['CPU_time_s'])
        ledger.finish(reservation,record);write(folder/'command.json',dict(record,budget_reservation_id=reservation['id']))
    proof=dict(status='failed',admission_sha256=sha(folder/'admission.json'),command_exit_code=record['exit_code'],
               before_sha256=sha(a['before']),after_sha256=sha(a['after']),boundary=a['expected_boundary'],
               executable=a['executable'],executable_sha256=sha(a['executable']),libraries=a['libraries'],
               log_path=str(log),log_sha256=sha(log) if log.exists() else None)
    try:
        if record['exit_code']:raise ValueError('bounded retained CTS proof failed')
        validate_lec(log.read_text(),a['expected_boundary']['primary_inputs'],a['expected_boundary']['primary_outputs'])
        proof['status']='passed'
    except Exception as e:proof['failure_reason']=str(e)
    write(folder/'proof.json',proof);return proof


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'))
    p.add_argument('--root',type=Path,required=True);p.add_argument('--batch',required=True);p.add_argument('--task')
    a=p.parse_args();root=a.root.resolve()
    print(admit(root,a.task,a.batch) if a.action=='admit' else run(root,a.batch))
