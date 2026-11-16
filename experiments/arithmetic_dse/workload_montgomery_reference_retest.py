"""One Montgomery A retest, clocked from retained physical-stage evidence.

The frozen nine-worker runtime executes this explicitly admitted successor
inside this process. No source, policy, admission or RTL of existing workers
is changed. A short parent-only dispatch pause makes its initial slot claim
safe alongside the existing controller; all EDA children keep running.
"""
import argparse
from contextlib import contextmanager, ExitStack
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import time
from unittest.mock import patch

from . import workload_reference_A as previous
from . import workload_nine_runtime as runtime
from .budget import BudgetExceeded
from .workload_abcd import read, sha

ROOT=previous.ROOT
SOURCE=Path(__file__).resolve()
VERSION='montgomery-original-A-physical-clock-retest-v1'
TASK='montgomery256-A-reference-T27000'
EVIDENCE=previous.old.EVIDENCE/'montgomery-A-retest-v1'
STAGES=('vulsim_synth_period.rpt','3_global_place.rpt','3_resizer.rpt',
        '3_detailed_place.rpt','4_cts_final.rpt')


def directory(root):
    # Outside backend/matrix-* discovery: the main controller must never
    # mistake this A calibration for a repeated per-target A task.
    return Path(root)/'reference-successors/matrix-montgomery-A-retest-v1'


def timing_basis(run):
    reports=Path(run)/'reports/asap7/arithmetic_probe/base';stages=[]
    for name in STAGES:
        path=reports/name;s=path.read_text()
        periods=re.findall(r'core_clk period_min\s*=\s*([0-9.]+)',s)
        if len(periods)!=1 or not math.isfinite(float(periods[0])) or float(periods[0])<=0:
            raise ValueError('missing or ambiguous retained intermediate clock period: '+str(path))
        slack=re.findall(r'worst slack max\s+(-?[0-9.]+)',s)
        stages.append(dict(stage=name,period_min_ps=float(periods[0]),
            setup_WNS_ps=float(slack[0]) if len(slack)==1 else None,path=str(path),sha256=sha(path)))
    maximum=max(s['period_min_ps'] for s in stages)
    request=math.ceil(1.10*maximum/1000)*1000
    return dict(stages=stages,maximum_intermediate_period_ps=maximum,margin_factor=1.10,
        quantum_ps=1000,request_ps=request,
        definition='Intermediate core-clock periods choose a new mapping request only; not a complete grt Tmin label')


def prepare(root):
    root=Path(root).resolve();folder=directory(root)
    if folder.exists():return verify(folder)
    predecessor=root/'backend/montgomery-A-reference-9x2'
    a=runtime.verify(predecessor);old=dict(a['tasks'][0]);run=predecessor/'runs'/old['id']
    manifest=read(run/'manifest.json');command=read(run/'grt.command.json')
    if (old['case']!='montgomery256' or old['method']!='A' or old['L']!=1 or
            manifest['status']!='failed' or manifest['period_ps']!=36000 or
            not command['timed_out'] or command['cleanup']['remaining_live_pids']):
        raise ValueError('expected settled original-A 36000ps timeout')
    basis=timing_basis(run)
    if basis['request_ps']!=27000:raise ValueError('review a new retest identity if intermediate evidence changes')
    task=dict(old,id=TASK,period_ps=27000,abc_target_ps=27000,threads=2,
        synth_timeout_s=3600,grt_timeout_s=21600,support_timeout_s=300,memory_limit_MiB=16384,
        predecessor_task=old['id'],predecessor_batch=str(predecessor),
        software_reference_period_ps=old['software_reference_period_ps'],
        clock_basis='max retained synth/place/CTS period * 1.10, rounded up to 1000ps')
    used=runtime.NineLedger().summary();limits=read(runtime.POLICY)['resources'];wall=3600+21600+4*300+60
    if (used['synth']+1>limits['max_synthesis_calls'] or used['grt']+1>limits['max_global_route_calls'] or
            used['walltime_s']+wall>limits['max_global_walltime_h']*3600 or
            used['CPU_time_s']+2*wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('single retest envelope is unfunded')
    if shutil.disk_usage(root).free<12*1024**3:raise ValueError('less than 12GiB retained-evidence storage available')
    inputs=[*runtime.measurement_sources(),runtime.SOURCE,runtime.POLICY,SOURCE,previous.SOURCE,
        Path(task['rtl']),Path(task['simulation_receipt']),Path(task['source_selection_file']),
        Path(task['memory_failure_manifest']),predecessor/'admission.json',predecessor/'freeze.json',
        run/'manifest.json',run/'grt.command.json',
        *[Path(s['path']) for s in basis['stages']],
        *[Path(task['verification_override'][k]) for k in ('proxy','prover')]]
    files={str(p.resolve()):sha(p) for p in inputs}
    folder.mkdir(parents=True)
    freeze=dict(version=VERSION,files=files,tasks=[task],role='clock_calibration',
        application_PPA_for_selection=False,selection_frozen_before_measurement=True)
    previous.write(folder/'freeze.json',freeze)
    admission=dict(version=VERSION,id=folder.name,role='clock_calibration',tasks=[task],
        source_sha256=sha(SOURCE),runtime_source_sha256=sha(runtime.SOURCE),
        policy_sha256=sha(runtime.POLICY),freeze_sha256=sha(folder/'freeze.json'),
        user_instruction='请给Montgomery256重新测试A的后端，参考之前的中间数据来设置时序',
        created_at=previous.now(),clock_basis=basis,parallel_jobs=9,threads_per_tool=2,
        memory_limit_MiB=16384,grt_timeout_s=21600,automatic_retries=0,
        call_caps=dict(synth=1,grt=1,support=4),worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,
        starting_usage=used,storage_reserve_GiB=12,old_failures_retained=True,
        cold_synth_and_physical_run=True,qualification='diagnostic_only',
        reason_for_longer_limit='Prior 7200s grt reached 300000 pin-access groups after CTS; setup repair was not its bottleneck')
    previous.write(folder/'admission.json',admission)
    previous.write(folder/'progress.json',dict(status='admitted',at=previous.now(),task=TASK))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for p in (folder/'admission.json',folder/'freeze.json',SOURCE):shutil.copy2(p,EVIDENCE/p.name)
    publish(root)
    return verify(folder)


def verify(folder):
    folder=Path(folder);a=read(folder/'admission.json');f=read(folder/'freeze.json')
    if (a['version']!=VERSION or a['source_sha256']!=sha(SOURCE) or
            a['runtime_source_sha256']!=sha(runtime.SOURCE) or a['policy_sha256']!=sha(runtime.POLICY) or
            a['freeze_sha256']!=sha(folder/'freeze.json') or a['tasks']!=f['tasks'] or len(a['tasks'])!=1):
        raise ValueError('Montgomery retest admission identity changed')
    t=a['tasks'][0]
    if (t['id']!=TASK or t['period_ps']!=27000 or t['abc_target_ps']!=27000 or t['threads']!=2 or
            t['synth_timeout_s']!=3600 or t['grt_timeout_s']!=21600 or t['support_timeout_s']!=300 or
            t['memory_limit_MiB']!=16384 or t['case']!='montgomery256' or t['method']!='A' or t['L']!=1):
        raise ValueError('retest resources, clock or original A differs')
    for name,digest in f['files'].items():
        if sha(name)!=digest:raise ValueError('frozen retest input changed: '+name)
    return a


def unclaimed_children(parent,state):
    claims={(j['admission_id'],j['task_id']) for j in state.get('jobs',[])};pending=[]
    path=Path('/proc')/str(parent['pid'])/'task'/str(parent['pid'])/'children'
    for pid in path.read_text().split():
        info=previous.process_info(int(pid))
        if not info:continue
        argv=info['argv']
        if len(argv)==9 and argv[1:5]==['-u','-m','experiments.arithmetic_dse.workload_nine_runtime','task']:
            key=(Path(argv[6]).name,argv[8])
            if key not in claims:pending.append(info['pid'])
    return pending


@contextmanager
def suspend_dispatch(root,folder):
    controllers=previous.find_processes('experiments.arithmetic_dse.workload_reference_A','run',root)
    if len(controllers)>1:raise ValueError('multiple current dispatchers visible')
    parent=controllers[0] if controllers else None
    if parent and parent['state'] in ('T','t'):raise ValueError('current dispatcher was already paused')
    try:
        if parent:
            previous.signal_exact(parent,signal.SIGSTOP)
            previous.write(folder/'dispatch-pause.json',dict(at=previous.now(),parent=parent,reason='claim one shared slot without racing dispatcher'))
            time.sleep(.3)
        yield parent
    finally:
        if parent:
            previous.signal_exact(parent,signal.SIGCONT)
            previous.write(folder/'dispatch-resume.json',dict(at=previous.now(),parent=parent,EDA_children_signalled=False))


class ReferenceLedger(runtime.TaskLedger):
    @contextmanager
    def job(self,context):
        root=self.batch.parents[1];folder=self.batch
        with ExitStack() as stack:
            while True:
                # Wait without holding or pausing the pipeline dispatcher.
                state=read(self.path);active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
                previous.write(folder/'progress.json',dict(status='waiting_for_slot',at=previous.now(),task=TASK,
                    active_physical_jobs=len(active),automatic_retries=0))
                if len(active)<9 and previous.old.available_memory_MiB()>=16384:
                    with suspend_dispatch(root,folder) as parent:
                        latest=read(self.path)
                        if parent and unclaimed_children(parent,latest):continue
                        try:
                            stack.enter_context(super().job(context))
                        except BudgetExceeded as error:
                            if str(error)!='all backend job slots occupied':raise
                            continue
                    previous.write(folder/'progress.json',dict(status='running',at=previous.now(),task=TASK,job_id=self.job_id))
                    break
                time.sleep(2)
            yield self.job_id


def run(root):
    root=Path(root).resolve();folder=directory(root);a=verify(folder)
    if (folder/'worker-start.json').exists():raise ValueError('worker already attempted; no automatic restart')
    state=read(runtime.budget.LEDGER)
    if ((folder/'runs'/TASK).exists() or any(j['admission_id']==a['id'] for j in state.get('jobs',[]))):
        raise ValueError('preserve prior retest attempt')
    previous.write(folder/'worker-start.json',dict(at=previous.now(),pid=os.getpid(),source_sha256=sha(SOURCE)))
    try:
        # These are process-local bindings. Existing workers retain their
        # original verifier, admissions and time limits.
        with patch.object(runtime,'verify',verify),patch.object(runtime,'TaskLedger',ReferenceLedger):
            runtime.run_task(folder,TASK)
        previous.write(folder/'progress.json',dict(status='completed',at=previous.now(),task=TASK))
    except Exception as error:
        previous.write(folder/'progress.json',dict(status='failed',at=previous.now(),task=TASK,reason=str(error),automatic_retries=0))
        raise
    finally:
        publish(root)
    return publish(root)


def publish(root):
    folder=directory(root);a=read(folder/'admission.json');progress=read(folder/'progress.json')
    run=folder/'runs'/TASK;manifest=previous.old.live_json(run/'manifest.json') or {}
    actual=previous.old.checked_readout(run,27000,inherited=False)
    result=dict(version=VERSION,at=previous.now(),status=progress['status'],request_ps=27000,
        method='A',L=1,RTL_sha256=a['tasks'][0]['rtl_sha256'],run=str(run),progress=progress,
        clock_basis=a['clock_basis'],old_request_ps=36000,old_failures_retained=True,
        parallel_jobs=9,threads_per_tool=2,memory_limit_MiB=16384,synth_timeout_s=3600,grt_timeout_s=21600,
        model_refitted=False,D_reselected=False,new_BCD_targets_frozen=False,
        failure_reason=manifest.get('failure_reason',progress.get('reason')))
    if actual:
        result.update(status='measured_grt',Tmin_ps=actual['full_setup_minimum_period_ps'],area_um2=actual['area_um2'],
            hold_WNS_ps=actual['hold_WNS_ps'],setup_met=actual['full_setup_minimum_period_ps']<=27000,
            frequency_MHz=1e6/actual['full_setup_minimum_period_ps'],
            readout_sha256=sha(run/'clock-readout/result.json'),manifest_sha256=sha(run/'manifest.json'),
            verification_receipt_sha256=sha(run/'verification-receipt.json'))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for dest in (folder,EVIDENCE):previous.write(dest/'result.json',result)
    lines=['# Montgomery256：按中间物理数据重测原始A','',
        f'状态：`{result["status"]}`，更新时间：{result["at"]}。实际运行目录：`{folder}`。','',
        '新SDC／ABC请求均为27000ps，原A保持L1、原RTL及功能收据。请求取已保留synth／placement／CTS的最大中间周期×1.10，向上取整至1000ps。',
        '中间时序只用于选择请求；正式A周期必须由完整grt、实际CTS证明、setup±0.1ps夹逼和账本结算后的读数给出。','',
        '| 中间阶段 | 时钟周期 ps |','| --- | ---: |']
    lines.extend(f'| {s["stage"]} | {s["period_min_ps"]:.2f} |' for s in a['clock_basis']['stages'])
    lines+=['','每工具2线程、16GiB；共享最多9个任务槽位。等待槽位时不暂停BCD，领取槽位时短暂停父调度器以避免抢槽竞争；EDA子进程不收信号。',
        '新综合上限3600秒、grt总上限21600秒（6小时），只运行一次，失败不自动重试。前次7200秒grt超时停在pin_access，延长的是完整物理流程时限。',
        '旧36000ps参考及其三次失败、费用完整保留。当前主表仍保留旧A的失败；新成功读数单独发布，后续可据此登记A参考替换及L16／L32目标，不改已冻结的其他BCD。','',
        '[机器结果](result.json)；[冻结准入与时钟依据](admission.json)。']
    if actual:lines+=['',f'完整实测Tmin={result["Tmin_ps"]:.6f}ps，面积={result["area_um2"]:.6f}µm²，hold WNS={result["hold_WNS_ps"]:.6f}ps。']
    if result['failure_reason']:lines+=['',f'失败：{result["failure_reason"]}。']
    (EVIDENCE/'README.md').write_text('\n'.join(lines)+'\n')
    return result


def start(root):
    root=Path(root).resolve();folder=directory(root);verify(folder)
    if (folder/'launch.json').exists():raise ValueError('retest launch already recorded')
    controllers=previous.find_processes('experiments.arithmetic_dse.workload_reference_A','run',root)
    if len(controllers)!=1:raise ValueError('exactly one current dispatcher must be visible; start on host')
    with (folder/'worker.log').open('a') as log:
        worker=subprocess.Popen([sys.executable,'-u','-m','experiments.arithmetic_dse.workload_montgomery_reference_retest',
            'run','--root',str(root)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    previous.write(folder/'launch.json',dict(at=previous.now(),pid=worker.pid,source_sha256=sha(SOURCE),controller=controllers[0]))
    deadline=time.monotonic()+10
    while time.monotonic()<deadline:
        if (folder/'worker-start.json').exists():return publish(root)
        if worker.poll() is not None:raise RuntimeError('worker exited before ready; inspect worker.log')
        time.sleep(.2)
    raise RuntimeError('worker readiness not yet confirmed; inspect worker.log')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','start','run','status'))
    p.add_argument('--root',type=Path,default=runtime.DEFAULT);args=p.parse_args()
    answer={'prepare':prepare,'start':start,'run':run,'status':publish}[args.action](args.root)
    print(json.dumps(answer,ensure_ascii=False,indent=2))
