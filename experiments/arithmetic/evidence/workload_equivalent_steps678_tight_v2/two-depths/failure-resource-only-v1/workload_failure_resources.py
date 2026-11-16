"""One bounded resource-only successor; preserve selection T and backend T.

Do not change clocks, prices, candidates, placements or selected RTL. Keep the
rejected changed-clock batch and all original attempts as separate evidence.
"""
import argparse
import fcntl
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
from unittest.mock import patch

from . import workload_failure_relaxation as rejected
from . import workload_reference_A as previous
from . import workload_nine_runtime as runtime
from .workload_backend import measurement_sources

ROOT=previous.ROOT
SOURCE=Path(__file__).resolve()
VERSION='workload-original-clock-resource-successor-v1'
EVIDENCE=previous.old.EVIDENCE/'failure-resource-only-v1'
read=previous.read
sha=previous.sha
write=rejected.write
now=rejected.now
METHODS=('B','C','D','same_policy_static')


def directory(root):
    return Path(root)/'failure-successors/matrix-failure-resource-only-v1'


def check_original(task,selected):
    """A resource successor must preserve both compiler and implementation T."""
    if (task['period_ps']!=task['original_period_ps'] or
            task['abc_target_ps']!=task['period_ps'] or
            task['period_ps']!=selected['T_clk_ps'] or
            task['rtl_sha256']!=selected['rtl_sha256'] or task['L']!=selected['L']):
        raise ValueError('resource-only successor changed clock, RTL or depth')


def prepare(root):
    root=Path(root).resolve();folder=directory(root)
    if (folder/'admission.json').exists():return verify(folder)
    withdrawn=read(rejected.directory(root)/'withdrawal.json')
    if withdrawn['status']!='withdrawn':raise ValueError('withdraw changed-clock batch first')
    snapshot=previous.publish(root)
    failures=[r for r in snapshot['BCD_records']+snapshot['same_policy_static'] if r['status']=='failed']
    if not failures:raise ValueError('no settled failure to retest')
    state=read(runtime.budget.LEDGER);tasks=[];lookup={};aliases={};inputs=set(measurement_sources())
    inputs.update([SOURCE,rejected.SOURCE,previous.SOURCE,runtime.SOURCE,runtime.POLICY,
        rejected.directory(root)/'withdrawal.json'])
    for r in failures:
        run=Path(r['measurement']['run']);old_admission=runtime.verify(run.parents[1])
        claims=[j for j in state['jobs'] if j['admission_id']==old_admission['id'] and j['task_id']==run.name]
        if len(claims)!=1 or claims[0]['status']!='released':raise ValueError('failure not released')
        original=next(t for t in old_admission['tasks'] if t['id']==run.name)
        manifest=read(run/'manifest.json')
        if manifest['status']!='failed':raise ValueError('failure manifest missing')
        plan=read(root/'plans'/f"{r['case']}-L{r['comparison_L']}.json")
        selection=Path(plan['selection'])
        group=next(g for g in read(selection)['records'] if g['target']['T_ps']==r['T_ps'])
        selected=group['methods'][r['method']]
        key=(r['case'],r['comparison_L'],r['T_ps'],original['rtl_sha256'])
        if key not in lookup:
            task=dict(original,id=f"{r['case']}-L{r['comparison_L']}-resource-T{r['T_ps']}-"+original['rtl_sha256'][:12],
                L=selected['L'],threads=2,synth_timeout_s=3600,grt_timeout_s=14400,support_timeout_s=300,
                memory_limit_MiB=8192,original_period_ps=original['period_ps'],
                original_run=str(run),original_failure_reason=r['failure_reason'],
                source_selection_file=str(selection),source_selection_sha256=sha(selection),
                shared_methods=[],selected_methods=[])
            tasks.append(task);lookup[key]=task
        task=lookup[key]
        if (r['case']=='dot16' and r['method']!='B') or 'memory_limit' in r['failure_reason']:
            task['memory_limit_MiB']=16384
        check_original(task,selected)
        task['shared_methods'].append(r['method'])
        task['selected_methods'].append(dict(method=r['method'],selection_file=str(selection),T_ps=r['T_ps']))
        aliases[(r['case'],r['comparison_L'],r['T_ps'],r['method'])]=task['id']
        inputs.update([run/'manifest.json',run/'measurement-outcome.json',run.parents[1]/'admission.json',
            selection,Path(task['rtl']),Path(task['simulation_receipt'])])
        inputs.update(p for p in Path(selected['rtl']).parent.iterdir() if p.is_file())
    groups=[]
    for g in snapshot['comparison_groups']:
        key=(g['case'],g['comparison_L'],g['BCD_target_ps'])
        if not any(k[:3]==key for k in aliases):continue
        methods={}
        for method in METHODS:
            records=snapshot['same_policy_static'] if method=='same_policy_static' else snapshot['BCD_records']
            row=next(r for r in records if (r['case'],r['comparison_L'],r['T_ps'],r['method'])==(*key,method))
            methods[method]=dict(original=row,successor_task=aliases.get((*key,method)))
        groups.append(dict(case=g['case'],L=g['comparison_L'],T_ps=g['BCD_target_ps'],
            A_reference=g['A_reference'],methods=methods))
    used=runtime.NineLedger().summary();limits=read(runtime.POLICY)['resources']
    wall=len(tasks)*(3600+14400+4*300+60)
    if (used['synth']+len(tasks)>limits['max_synthesis_calls'] or used['grt']+len(tasks)>limits['max_global_route_calls'] or
            used['walltime_s']+wall>limits['max_global_walltime_h']*3600 or
            used['CPU_time_s']+2*wall>limits['max_tool_CPU_time_h']*3600):
        raise ValueError('resource successor envelope unfunded')
    folder.mkdir(parents=True,exist_ok=True)
    write(folder/'predecessor-snapshot.json',snapshot);inputs.add(folder/'predecessor-snapshot.json')
    write(folder/'freeze.json',dict(version=VERSION,tasks=tasks,groups=groups,
        files={str(p):sha(p) for p in inputs},selection_frozen_before_measurement=True,
        application_PPA_for_selection=False,clocks_changed=False))
    admission=dict(version=VERSION,id=folder.name,role='final_evaluation',tasks=tasks,
        freeze_sha256=sha(folder/'freeze.json'),source_sha256=sha(SOURCE),runtime_source_sha256=sha(runtime.SOURCE),
        policy_sha256=sha(runtime.POLICY),parallel_jobs=9,threads_per_tool=2,automatic_retries=0,
        authorized_attempts_per_task=1,clocks_changed=False,D_reselected=False,
        original_failed_method_records=len(failures),physical_tasks=len(tasks),
        call_caps=dict(synth=len(tasks),grt=len(tasks),support=4*len(tasks)),
        worst_case_leaf_walltime_s=wall,CPU_envelope_s=2*wall,starting_usage=used,at=now(),
        user_instruction='保持原时钟，只放宽内存与时间；改时钟必须重新生成D，旧变时钟批次撤回',
        qualification='diagnostic_only; original-T resource successor')
    write(folder/'admission.json',admission)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for p in (folder/'admission.json',folder/'freeze.json',SOURCE):shutil.copyfile(p,EVIDENCE/p.name)
    return verify(folder)


def verify(folder):
    folder=Path(folder);a=read(folder/'admission.json');f=read(folder/'freeze.json')
    if (a['version']!=VERSION or a['source_sha256']!=sha(SOURCE) or a['runtime_source_sha256']!=sha(runtime.SOURCE) or
            a['policy_sha256']!=sha(runtime.POLICY) or a['freeze_sha256']!=sha(folder/'freeze.json') or
            a['tasks']!=f['tasks'] or a['clocks_changed'] or f['clocks_changed']):
        raise ValueError('resource successor identity changed')
    for t in a['tasks']:
        if (t['threads']!=2 or t['memory_limit_MiB'] not in (8192,16384) or
                t['synth_timeout_s']!=3600 or t['grt_timeout_s']!=14400 or t['support_timeout_s']!=300):
            raise ValueError('resource successor limits changed')
        for binding in t['selected_methods']:
            group=next(g for g in read(binding['selection_file'])['records'] if g['target']['T_ps']==binding['T_ps'])
            check_original(t,group['methods'][binding['method']])
        if read(Path(t['original_run'])/'manifest.json')['period_ps']!=t['period_ps']:
            raise ValueError('original backend clock differs')
    for name,digest in f['files'].items():
        if sha(name)!=digest:raise ValueError('frozen resource-successor input changed: '+name)
    return a


def task(root,tid):
    folder=directory(root);verify(folder)
    with patch.object(runtime,'verify',verify),patch.object(runtime,'TaskLedger',rejected.SuccessorLedger):
        return runtime.run_task(folder,tid)


def publish(root):
    folder=directory(root);a=read(folder/'admission.json');freeze=read(folder/'freeze.json');groups=[];counts={}
    for g in freeze['groups']:
        methods={}
        for method,binding in g['methods'].items():
            old=binding['original'];tid=binding['successor_task']
            run=folder/'runs'/tid if tid else Path(old['measurement']['run'])
            manifest=previous.old.live_json(run/'manifest.json') or {}
            outcome=previous.old.live_json(run/'measurement-outcome.json') or {}
            actual=previous.old.checked_readout(run,g['T_ps'],old['measurement']['inherited'] if not tid else False)
            status=('measured_grt' if actual else 'failed' if outcome.get('status')=='failed' or manifest.get('status')=='failed'
                else 'running' if manifest else 'queued')
            row=dict(original_status=old['status'],original_run=old['measurement']['run'],
                successor_task=tid,run=str(run),status=status,rtl_sha256=old['rtl_sha256'],prediction=old['prediction'],
                inherited_original_result=not bool(tid),failure_reason=outcome.get('reason',manifest.get('failure_reason')))
            if actual:row.update(Tmin_ps=actual['full_setup_minimum_period_ps'],area_um2=actual['area_um2'],
                hold_WNS_ps=actual['hold_WNS_ps'],setup_met=actual['full_setup_minimum_period_ps']<=g['T_ps'])
            methods[method]=row
            if tid:counts[status]=counts.get(status,0)+1
        groups.append(dict(g,methods=methods))
    doc=dict(version=VERSION,at=now(),groups=groups,successor_statuses=counts,physical_tasks=len(a['tasks']),
        original_failed_method_records=a['original_failed_method_records'],clocks_changed=False,D_reselected=False,
        original_failed_attempts_and_costs_retained=True,qualification='diagnostic_only',
        controller=previous.old.live_json(folder/'controller-progress.json'))
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    for dest in (folder,EVIDENCE):write(dest/'results.json',doc)
    lines=['# 原时钟不变、仅放宽资源的失败重测','',doc['at'],'',
        '保持原选择T、局部预算／模型查询、拆分、寄存器位置、RTL和后端请求；只增加时间或内存。原成功结果复用，原失败与费用保留。A继续引用原参考。',
        '每工具2线程，共享9槽；综合3600秒／grt14400秒；Dot16的C/D/归因16GiB，其余8GiB。每任务一次，不自动重试。','',
        '| 案例 | L | 原选择及后端T ps | A原请求 / Tmin | B Tmin / 面积 | C Tmin / 面积 | D Tmin / 面积 | 同池归因 |',
        '| --- | ---: | ---: | --- | --- | --- | --- | --- |']
    def cell(row):
        suffix='（资源后继）' if row['successor_task'] else '（原结果）'
        return (f"{row['Tmin_ps']:.3f} / {row['area_um2']:.3f}" if row['status']=='measured_grt' else row['status'])+suffix
    for g in groups:
        ar=g['A_reference'];A=f"{ar['reference_request_ps']} / {ar.get('Tmin_ps','—')}"
        lines.append('| '+' | '.join([g['case'],str(g['L']),str(g['T_ps']),A,*[cell(g['methods'][m]) for m in METHODS]])+' |')
    lines+=['','变更目标T时必须先按新T重新执行C/D选择、局部预算、完整评分与RTL验证，再做后端评价。',
        '此前改变后端T但复用原D的批次已撤回，保留为独立诊断，不能计入本表或原目标达标。',
        'NTT L8软件恢复再次−11，未取得ready；本资源重测不再次启动软件重试。',
        '', '[准入](admission.json)；[冻结输入](freeze.json)；[机器结果](results.json)。']
    (EVIDENCE/'README.md').write_text('\n'.join(lines)+'\n');return doc


def run(root):
    root=Path(root).resolve();folder=directory(root);a=verify(folder)
    with (folder/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        attempts=previous.old.live_json(folder/'attempts.json') or {};children={}
        write(folder/'controller-start.json',dict(at=now(),pid=__import__('os').getpid(),source_sha256=sha(SOURCE)))
        while True:
            for tid,child in list(children.items()):
                code=child.poll()
                if code is not None:
                    attempts[tid].update(exit_code=code,finished_at=now());del children[tid];write(folder/'attempts.json',attempts)
            state=read(runtime.budget.LEDGER);claims={j['task_id']:j for j in state['jobs'] if j['admission_id']==a['id']}
            active=[j for j in state['jobs'] if j['status'] in ('active','unsettled')]
            unclaimed=sum(tid not in claims for tid in children)
            queued=[t for t in a['tasks'] if t['id'] not in claims and t['id'] not in attempts]
            if queued and len(active)+unclaimed<9 and shutil.disk_usage(ROOT).free>=14*1024**3:
                t=next((t for t in queued if previous.old.available_memory_MiB()>=t['memory_limit_MiB']),None)
                if t:
                    tid=t['id'];logpath=folder/'dispatch-logs'/f'{tid}.log';logpath.parent.mkdir(exist_ok=True)
                    attempts[tid]=dict(started_at=now(),log=str(logpath));write(folder/'attempts.json',attempts)
                    with logpath.open('a') as log:
                        child=subprocess.Popen([sys.executable,'-u','-m',__package__+'.workload_failure_resources','task',
                            '--root',str(root),'--task-id',tid],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
                    attempts[tid]['pid']=child.pid;children[tid]=child;write(folder/'attempts.json',attempts)
            write(folder/'controller-progress.json',dict(ready=True,at=now(),
                status='running' if queued or children else 'settled',queued=len(queued),worker_processes=len(children),
                global_active_jobs=len(active),clocks_changed=False,automatic_retries=0,source_sha256=sha(SOURCE)))
            publish(root)
            if not queued and not children:return
            time.sleep(5)


def start(root):
    folder=directory(root);verify(folder)
    if (folder/'launch.json').exists():raise ValueError('resource successor already launched')
    with (folder/'controller.log').open('a') as log:
        child=subprocess.Popen([sys.executable,'-u','-m',__package__+'.workload_failure_resources','run',
            '--root',str(root)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    write(folder/'launch.json',dict(at=now(),pid=child.pid,source_sha256=sha(SOURCE)))
    return dict(pid=child.pid,launch=str(folder/'launch.json'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','start','run','task','status'))
    p.add_argument('--root',type=Path,default=runtime.DEFAULT);p.add_argument('--task-id');args=p.parse_args()
    result=task(args.root,args.task_id) if args.action=='task' else dict(prepare=prepare,start=start,run=run,status=publish)[args.action](args.root)
    print(json.dumps(result,ensure_ascii=False))
