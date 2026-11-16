"""Explicit one-attempt successors for retained workload failures.

Frozen implementations are remeasured at common relaxed clocks. Original
selections and predictions retain their original request identities. Existing
runtime/controller/policy sources are used unchanged; all leaves share its
kernel-locked nine-slot ledger. NTT's unfinished software gets one diagnostic
retry with a larger stack and faulthandler, retaining cached candidates.
"""
import argparse
from contextlib import contextmanager, ExitStack
import csv
import datetime
import faulthandler
import fcntl
import json
import math
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

from . import workload_reference_A as previous
from . import workload_montgomery_reference_retest as montgomery
from . import workload_nine_runtime as runtime
from .budget import BudgetExceeded
from .workload_abcd import read,sha
from .workload_backend import measurement_sources

ROOT=previous.ROOT
SOURCE=Path(__file__).resolve()
VERSION='workload-explicit-failure-relaxation-v2'
EVIDENCE=previous.old.EVIDENCE/'failure-relaxation-v1'
BASE_VERIFY=runtime.verify
METHODS=('B','C','D','same_policy_static')
STAGES=('vulsim_synth_period.rpt','3_global_place.rpt','3_resizer.rpt',
        '3_detailed_place.rpt','4_cts_final.rpt')


def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()


def write(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_name(p.name+f'.{os.getpid()}.tmp')
    tmp.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n');os.replace(tmp,p)


def directory(root): return Path(root)/'failure-successors/matrix-failure-relaxation-v2'


def timing_basis(run):
    reports=Path(run)/'reports/asap7/arithmetic_probe/base';rows=[]
    for name in STAGES:
        p=reports/name
        if not p.exists(): continue
        matches=re.findall(r'core_clk period_min\s*=\s*([0-9.]+)',p.read_text(errors='replace'))
        if len(matches)!=1 or not math.isfinite(float(matches[0])) or float(matches[0])<=0:
            raise ValueError('ambiguous intermediate period: '+str(p))
        rows.append(dict(path=str(p),sha256=sha(p),period_ps=float(matches[0])))
    if not rows: raise ValueError('no retained timing basis: '+str(run))
    return rows


def relaxed_targets(periods,old_targets):
    base=max([*periods,*old_targets]);count=len(set(old_targets))
    if count not in (1,2): raise ValueError('finite one/two-slot successor required')
    values=[math.ceil(f*base/50)*50 for f in (1.10,1.20)[:count]]
    if len(values)==2: values[1]=max(values[1],values[0]+50)
    if not all(v>max(old_targets) for v in values): raise ValueError('clock was not relaxed')
    return values


def prepare(root):
    root=Path(root).resolve();folder=directory(root)
    if (folder/'admission.json').exists(): return verify(folder)
    snapshot=previous.publish(root)
    failed=[r for r in snapshot['BCD_records']+snapshot['same_policy_static'] if r['status']=='failed']
    if not failed: raise ValueError('no retained workload failure')
    families={};evidence=[];inputs=set(measurement_sources()+[runtime.SOURCE,runtime.POLICY,SOURCE,
        previous.SOURCE,montgomery.SOURCE,previous.matrix.SOURCE])
    state=read(runtime.budget.LEDGER)
    for r in failed:
        run=Path(r['measurement']['run']);key=(r['case'],r['comparison_L'])
        a=BASE_VERIFY(run.parents[1]);manifest=read(run/'manifest.json')
        claims=[j for j in state.get('jobs',[]) if j['admission_id']==a['id'] and j['task_id']==run.name]
        if len(claims)!=1 or claims[0]['status']!='released' or manifest['status']!='failed':
            raise ValueError('failed predecessor not settled: '+str(run))
        row=dict(case=r['case'],L=r['comparison_L'],T_ps=r['T_ps'],method=r['method'],
            reason=r['failure_reason'],run=str(run),manifest_sha256=sha(run/'manifest.json'),
            stages=timing_basis(run))
        evidence.append(row);families.setdefault(key,[]).append(row)
        inputs.add(run/'manifest.json');inputs.add(run.parents[1]/'admission.json')
        inputs.update(Path(s['path']) for s in row['stages'])
    tasks=[];groups=[];lookup={}
    for (cid,L),failures in sorted(families.items()):
        plan=read(root/'plans'/f'{cid}-L{L}.json');selection=Path(plan['selection']);inputs.add(selection)
        original=read(selection)['records'];old_targets=sorted({f['T_ps'] for f in failures})
        # Attribution is measured under the primary methods' request; a slow
        # ablation must not silently set a looser B/C/D target.
        primary=[f for f in failures if f['method'] in ('B','C','D')]
        if not primary: primary=failures
        requests=relaxed_targets([s['period_ps'] for f in primary for s in f['stages']],old_targets)
        for oldT,T in zip(old_targets,requests):
            selected=next(g for g in original if g['target']['T_ps']==oldT);aliases={}
            for method in METHODS:
                m=selected['methods'][method];rtl=Path(m['rtl']);sim=Path(m['simulation_receipt'])
                if m['simulation_status']!='passed' or read(sim)['status']!='passed' or read(sim)['rtl_sha256']!=sha(rtl):
                    raise ValueError('functional receipt mismatch')
                identity=(cid,L,T,sha(rtl))
                if identity not in lookup:
                    tid=f'{cid}-L{L}-relaxed-T{T}-'+sha(rtl)[:12]
                    # 16GiB is explicitly authorized here for Dot16's measured
                    # near-limit C/D/static designs; B stayed below 6GiB.
                    memory=16384 if cid=='dot16' and method!='B' else 8192
                    task=dict(id=tid,case=cid,L=L,rtl=str(rtl),rtl_sha256=sha(rtl),period_ps=T,abc_target_ps=T,
                        threads=2,memory_limit_MiB=memory,synth_timeout_s=3600,grt_timeout_s=14400,
                        support_timeout_s=300,large=True,simulation_status='passed',simulation_receipt=str(sim),
                        source_selection_file=str(selection),source_selection_sha256=sha(selection),
                        original_selection_T_ps=oldT,shared_methods=[],original_prediction_retargeted=False)
                    lookup[identity]=task;tasks.append(task)
                task=lookup[identity];task['shared_methods'].append(method)
                aliases[method]=dict(task_id=task['id'],rtl_sha256=sha(rtl),grammar=m['grammar'],
                    original_selection_T_ps=oldT,original_prediction=m['prediction'])
                inputs.update([rtl,sim])
            groups.append(dict(case=cid,L=L,old_target_ps=oldT,request_ps=T,methods=aliases,
                clock_basis='ceil50(max retained primary-BCD failed synth/place/CTS periods and old requests * factor); static attribution does not set BCD clock',
                factor=1.10 if oldT==old_targets[0] else 1.20,
                original_A_reference=next(a for a in snapshot['A_references'] if a['case']==cid)))
    used=runtime.NineLedger().summary();limits=read(runtime.POLICY)['resources']
    wall=sum(t['synth_timeout_s']+t['grt_timeout_s']+4*t['support_timeout_s']+60 for t in tasks)
    if (used['synth']+len(tasks)>limits['max_synthesis_calls'] or used['grt']+len(tasks)>limits['max_global_route_calls'] or
        used['walltime_s']+wall>limits['max_global_walltime_h']*3600 or
        used['CPU_time_s']+2*wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('finite relaxed batch envelope unfunded')
    folder.mkdir(parents=True,exist_ok=True)
    write(folder/'predecessor-snapshot.json',snapshot)
    write(folder/'clock-basis.json',dict(failures=evidence,groups=groups))
    inputs.update([folder/'predecessor-snapshot.json',folder/'clock-basis.json'])
    freeze=dict(version=VERSION,tasks=tasks,groups=groups,files={str(p):sha(p) for p in inputs},
        selection_frozen_before_measurement=True,application_PPA_for_selection=False)
    write(folder/'freeze.json',freeze)
    admission=dict(version=VERSION,id=folder.name,role='final_evaluation',tasks=tasks,
        freeze_sha256=sha(folder/'freeze.json'),source_sha256=sha(SOURCE),runtime_source_sha256=sha(runtime.SOURCE),
        policy_sha256=sha(runtime.POLICY),parallel_jobs=9,threads_per_tool=2,automatic_retries=0,
        authorized_attempts_per_task=1,starting_usage=used,worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,
        call_caps=dict(synth=len(tasks),grt=len(tasks),support=4*len(tasks)),created_at=now(),
        user_instruction='请记录要修复的问题，补进第一章的内容。失败的实验请放宽条件重跑',
        qualification='diagnostic_only; changed-clock fixed-implementation evaluation, not new D optimization',
        original_failed_records=len(evidence),logical_methods=len(groups)*4,storage_reserve_GiB=12)
    write(folder/'admission.json',admission)
    for p in (folder/'admission.json',folder/'freeze.json',folder/'clock-basis.json',SOURCE):
        EVIDENCE.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,EVIDENCE/p.name)
    return verify(folder)


def verify(folder):
    folder=Path(folder);a=read(folder/'admission.json');f=read(folder/'freeze.json')
    if (a['version']!=VERSION or a['source_sha256']!=sha(SOURCE) or a['runtime_source_sha256']!=sha(runtime.SOURCE) or
        a['policy_sha256']!=sha(runtime.POLICY) or a['freeze_sha256']!=sha(folder/'freeze.json') or a['tasks']!=f['tasks']):
        raise ValueError('relaxed successor identity changed')
    for t in a['tasks']:
        if (t['threads']!=2 or t['memory_limit_MiB'] not in (8192,16384) or t['synth_timeout_s']!=3600 or
            t['grt_timeout_s']!=14400 or t['support_timeout_s']!=300 or t['abc_target_ps']!=t['period_ps']):
            raise ValueError('relaxed successor resource/clock mismatch')
    for name,digest in f['files'].items():
        if sha(name)!=digest: raise ValueError('frozen relaxed input changed: '+name)
    return a


class SuccessorLedger(runtime.TaskLedger):
    @contextmanager
    def job(self,context):
        t=self.task;folder=self.batch;root=folder.parents[1]
        with ExitStack() as stack:
            while True:
                state=read(self.path);active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
                free=shutil.disk_usage(ROOT).free
                write(folder/'worker-status'/f'{t["id"]}.json',dict(status='waiting_for_slot',at=now(),
                    active_jobs=len(active),available_memory_MiB=previous.old.available_memory_MiB(),free_bytes=free))
                if len(active)<9 and previous.old.available_memory_MiB()>=t['memory_limit_MiB'] and free>=14*1024**3:
                    with montgomery.suspend_dispatch(root,folder) as parent:
                        if parent and montgomery.unclaimed_children(parent,read(self.path)): continue
                        try: stack.enter_context(super().job(context))
                        except BudgetExceeded as error:
                            if str(error)!='all backend job slots occupied': raise
                            continue
                    write(folder/'worker-status'/f'{t["id"]}.json',dict(status='running',at=now(),job_id=self.job_id))
                    break
                time.sleep(3)
            yield self.job_id


def task(root,tid):
    folder=directory(root);verify(folder)
    with patch.object(runtime,'verify',verify),patch.object(runtime,'TaskLedger',SuccessorLedger):
        return runtime.run_task(folder,tid)


def software(root):
    root=Path(root);folder=directory(root);status=folder/'ntt-software-result.json'
    if status.exists(): raise ValueError('software retry already attempted')
    log=root/'software-logs/ntt8x64-L8.log'
    original=dict(log=str(log),sha256=sha(log),bytes=log.stat().st_size)
    faulthandler.enable(all_threads=True);faulthandler.dump_traceback_later(600,repeat=True)
    old_stack=resource.getrlimit(resource.RLIMIT_STACK)
    stack=64*1024**2
    if old_stack[1]!=resource.RLIM_INFINITY: stack=min(stack,old_stack[1])
    resource.setrlimit(resource.RLIMIT_STACK,(stack,old_stack[1]))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    resource.setrlimit(resource.RLIMIT_CPU,(14400,14400))
    resource.setrlimit(resource.RLIMIT_AS,(16*1024**3,16*1024**3))
    write(status,dict(status='running',at=now(),pid=os.getpid(),stack_before=old_stack,stack_bytes=stack,
        address_space_limit_GiB=16,CPU_limit_s=14400,wall_limit_s=21600,original_failure_log=original,
        original_exit=-11,attempts=1,cached_candidates_retained=True,new_model_fits=0))
    try:
        result=previous.matrix.software(root,'ntt8x64',8)
        write(status,dict(read(status),status='completed',at=now(),selection=str(result),selection_sha256=sha(result)))
    except BaseException as error:
        write(status,dict(read(status),status='failed',at=now(),reason=str(error)))
        raise
    finally:
        faulthandler.cancel_dump_traceback_later()


def ensure_ntt_dispatch(root,folder):
    if previous.matrix.ready_selection(root,'ntt8x64',8) is None: return
    controllers=previous.find_processes('experiments.arithmetic_dse.workload_reference_A','run',root)
    if len(controllers)>1: raise ValueError('multiple original dispatchers')
    receipt=folder/'ntt-backend-controller.json'
    if controllers or receipt.exists(): return
    # The original dispatcher may have naturally settled while the software
    # retry was running. Its existing attempt journal prevents duplicate EDA.
    with (folder/'resumed-original-controller.log').open('a') as log:
        child=subprocess.Popen([sys.executable,'-u','-m','experiments.arithmetic_dse.workload_reference_A',
            'run','--root',str(root)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
            start_new_session=True)
    write(receipt,dict(at=now(),pid=child.pid,reason='NTT software ready after original dispatcher settled',
        original_attempt_journal_preserved=True,automatic_task_retries=0))


def publish(root):
    folder=directory(root);a=read(folder/'admission.json');freeze=read(folder/'freeze.json');groups=[];counts={}
    for g in freeze['groups']:
        methods={}
        for method,alias in g['methods'].items():
            run=folder/'runs'/alias['task_id'];manifest=previous.old.live_json(run/'manifest.json') or {}
            outcome=previous.old.live_json(run/'measurement-outcome.json') or {}
            actual=previous.old.checked_readout(run,g['request_ps'],inherited=False)
            state='measured_grt' if actual else 'failed' if outcome.get('status')=='failed' or manifest.get('status')=='failed' else 'running' if manifest else 'queued'
            r=dict(alias,status=state,run=str(run),failure_reason=outcome.get('reason',manifest.get('failure_reason')))
            if actual:r.update(Tmin_ps=actual['full_setup_minimum_period_ps'],area_um2=actual['area_um2'],
                hold_WNS_ps=actual['hold_WNS_ps'],setup_met=actual['full_setup_minimum_period_ps']<=g['request_ps'])
            methods[method]=r;counts[state]=counts.get(state,0)+1
        groups.append(dict(g,methods=methods))
    doc=dict(version=VERSION,at=now(),groups=groups,statuses=counts,physical_tasks=len(a['tasks']),
        logical_method_records=len(groups)*4,original_failures_retained=True,original_matrix_modified=False,
        model_refitted=False,D_reselected=False,parallel_jobs=9,threads_per_tool=2,
        ntt_software=previous.old.live_json(folder/'ntt-software-result.json'),
        controller=previous.old.live_json(folder/'controller-progress.json'))
    for dest in (folder,EVIDENCE):write(dest/'results.json',doc)
    lines=['# 失败实验宽松条件后继','',doc['at'],'',
        '用户授权的单次重测；原主矩阵、失败和费用保留。固定原RTL及寄存器位置，在新统一请求下测B/C/D及同池归因；原模型预测仍属原T，未重新优化D。A继续引用原参考，不按流水T重测。','',
        '综合上限3600秒、完整grt上限14400秒、每工具2线程；共享原9槽及累计账本。Dot16的C/D/归因使用16GiB，其他8GiB；保留至少12GiB存储，发射阈值14GiB。每任务一次，后继失败不自动重试。','',
        '| 案例 | L | 原T ps | 新请求 ps | B Tmin/面积 | C Tmin/面积 | D Tmin/面积 | 同池归因 |',
        '| --- | ---: | ---: | ---: | --- | --- | --- | --- |']
    def cell(r):return f'{r["Tmin_ps"]:.3f} / {r["area_um2"]:.3f}'+(' ✓' if r['setup_met'] else '') if r['status']=='measured_grt' else r['status']
    for g in groups:lines.append('| '+' | '.join([g['case'],str(g['L']),str(g['old_target_ps']),str(g['request_ps']),*[cell(g['methods'][m]) for m in METHODS]])+' |')
    lines+=['','新时钟依据为主BCD失败现场已有synth/place/CTS的最大core-clock周期与原请求的最大值，首档乘1.10、次档乘1.20，向上取整到50ps；同池静态归因不决定主方法的时钟。中间周期仅决定新请求，不是完整实测Tmin。',
        'NTT L8另作一次软件恢复：栈增至64MiB、地址空间16GiB、CPU4小时／墙钟6小时、faulthandler；保留原−11日志及既有候选。成功仍需完整回放及ready收据，之后由原控制器登记原目标BCD，不强行写入本宽松时钟表。',
        '', '[准入](admission.json)；[时钟依据](clock-basis.json)；[机器状态](results.json)。']
    (EVIDENCE/'README.md').write_text('\n'.join(lines)+'\n')
    with (EVIDENCE/'results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['case','L','old_target_ps','request_ps','method','status','Tmin_ps','area_um2','hold_WNS_ps','setup_met','run'],extrasaction='ignore');w.writeheader()
        for g in groups:
            for m,r in g['methods'].items():w.writerow(dict(g,**r,method=m))
    return doc


def run(root):
    root=Path(root).resolve();folder=directory(root);a=verify(folder)
    with (folder/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        attempts=previous.old.live_json(folder/'attempts.json') or {};children={}
        write(folder/'controller-start.json',dict(pid=os.getpid(),at=now(),source_sha256=sha(SOURCE)))
        if not (folder/'ntt-software-launch.json').exists() and previous.matrix.ready_selection(root,'ntt8x64',8) is None:
            env=dict(os.environ,OMP_NUM_THREADS='1',OPENBLAS_NUM_THREADS='1',PYTHONFAULTHANDLER='1')
            with (folder/'ntt-software.log').open('a') as log:
                child=subprocess.Popen([sys.executable,'-u','-m',__package__+'.workload_failure_relaxation','software',
                    '--root',str(root)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,
                    start_new_session=True,env=env)
            write(folder/'ntt-software-launch.json',dict(pid=child.pid,at=now(),wall_deadline=time.time()+21600))
            software_child=child
        else:software_child=None
        while True:
            for tid,child in list(children.items()):
                code=child.poll()
                if code is not None:
                    attempts[tid].update(exit_code=code,finished_at=now());del children[tid];write(folder/'attempts.json',attempts)
            if software_child is not None:
                code=software_child.poll()
                if code is not None:
                    old=previous.old.live_json(folder/'ntt-software-result.json') or {}
                    write(folder/'ntt-software-result.json',dict(old,status='completed' if code==0 else 'failed',exit_code=code,finished_at=now()))
                    software_child=None
                elif time.time()>read(folder/'ntt-software-launch.json')['wall_deadline']:
                    previous.signal_exact(previous.process_info(software_child.pid),__import__('signal').SIGTERM)
            ensure_ntt_dispatch(root,folder)
            state=read(runtime.budget.LEDGER);claims={j['task_id']:j for j in state.get('jobs',[]) if j['admission_id']==a['id']}
            active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
            unclaimed=sum(tid not in claims for tid in children)
            queued=[t for t in a['tasks'] if t['id'] not in claims and t['id'] not in attempts]
            # A waiting worker makes the actual atomic slot claim. Dispatch
            # only one new waiter per cycle; it coordinates with the old parent.
            if queued and len(active)+unclaimed<9 and shutil.disk_usage(ROOT).free>=14*1024**3:
                t=next((t for t in queued if previous.old.available_memory_MiB()>=t['memory_limit_MiB']),None)
                if t:
                    tid=t['id'];logpath=folder/'dispatch-logs'/f'{tid}.log';logpath.parent.mkdir(exist_ok=True)
                    attempts[tid]=dict(started_at=now(),log=str(logpath));write(folder/'attempts.json',attempts)
                    with logpath.open('a') as log:
                        child=subprocess.Popen([sys.executable,'-u','-m',__package__+'.workload_failure_relaxation','task',
                            '--root',str(root),'--task-id',tid],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                    attempts[tid]['pid']=child.pid;children[tid]=child;write(folder/'attempts.json',attempts)
            write(folder/'controller-progress.json',dict(ready=True,status='running' if queued or children or software_child else 'settled',
                at=now(),queued=len(queued),worker_processes=len(children),global_active_jobs=len(active),
                free_bytes=shutil.disk_usage(ROOT).free,software_worker=software_child.pid if software_child else None,
                automatic_retries=0,source_sha256=sha(SOURCE)))
            publish(root)
            if not queued and not children and software_child is None:return publish(root)
            time.sleep(5)


def start(root):
    root=Path(root).resolve();folder=directory(root);verify(folder)
    if (folder/'launch.json').exists():raise ValueError('successor already launched; retain prior attempt')
    with (folder/'controller.log').open('a') as log:
        child=subprocess.Popen([sys.executable,'-u','-m',__package__+'.workload_failure_relaxation','run','--root',str(root)],
            cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(folder/'launch.json',dict(at=now(),pid=child.pid,source_sha256=sha(SOURCE)))
    deadline=time.monotonic()+15
    while time.monotonic()<deadline:
        if (folder/'controller-progress.json').exists():return publish(root)
        if child.poll() is not None:raise RuntimeError('successor exited before ready; inspect controller.log')
        time.sleep(.2)
    raise RuntimeError('successor readiness pending; inspect controller.log')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','start','run','task','software','status'))
    p.add_argument('--root',type=Path,default=runtime.DEFAULT);p.add_argument('--task-id');args=p.parse_args()
    result=task(args.root,args.task_id) if args.action=='task' else {'prepare':prepare,'start':start,'run':run,'software':software,'status':publish}[args.action](args.root)
    if args.action not in ('run','software'):print(json.dumps(result,ensure_ascii=False,indent=2))
