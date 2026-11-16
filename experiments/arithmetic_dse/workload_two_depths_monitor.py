"""Observe the frozen matrix; settle only confirmed, stalled tool aborts.

This sidecar changes no selector, admission, RTL, clock, model or backend
source. A fatal allocator/signal diagnostic must remain at the end of the
current leaf log for at least two minutes. Only its uniquely matched runtime
wrapper receives SIGTERM, letting the existing process-tree cleanup and
ledger settlement run. Failed tasks are never resubmitted here.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import signal
import tempfile
import time

from . import workload_latency_matrix as matrix
from . import workload_nine_runtime as runtime
from . import workload_two_depths_run as driver
from .workload_abcd import read, sha

SOURCE=Path(__file__).resolve()
EVIDENCE=driver.EVIDENCE/'operational-review'
FATAL=('malloc_consolidate(): invalid chunk size','double free or corruption',
       'corrupted size vs. prev_size','free(): invalid pointer',
       'malloc(): corrupted top size','Signal 6 received','Signal 11 received')


def atomic_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,delete=False) as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2); stream.write('\n')
        temporary=stream.name
    os.replace(temporary,path)


def fatal_tail(path,now,minimum_age_s=120):
    """Silence alone is not evidence of a tool crash."""
    try:
        stat=path.stat()
        if now-stat.st_mtime<minimum_age_s:
            return None
        with path.open('rb') as stream:
            stream.seek(max(0,stat.st_size-8192)); tail=stream.read().decode(errors='replace')
    except FileNotFoundError:
        return None
    marker=next((s for s in FATAL if s in tail),None)
    if not marker or 'Stack trace:' not in tail:
        return None
    return dict(marker=marker,tail=tail,age_s=now-stat.st_mtime,
                size=stat.st_size,mtime_ns=stat.st_mtime_ns)


def exact_wrapper(argv,batch,task):
    return (len(argv)==9 and Path(argv[0]).name.startswith('python') and
        argv[1:5]==['-u','-m','experiments.arithmetic_dse.workload_nine_runtime','task'] and
        argv[5:]==['--root',str(batch),'--task-id',task])


def wrappers(batch,task,proc=Path('/proc')):
    found=[]
    for p in proc.glob('[0-9]*'):
        try:
            argv=[s.decode() for s in (p/'cmdline').read_bytes().split(b'\0') if s]
            stat=(p/'stat').read_text().rsplit(')',1)[1].split()
            if exact_wrapper(argv,batch,task) and stat[0]!='Z':
                found.append(dict(pid=int(p.name),start=stat[19],argv=argv))
        except (OSError,ValueError,UnicodeDecodeError,IndexError):
            continue
    return found


def settle_confirmed_aborts(root,state,now,proc=Path('/proc')):
    incidents=[]
    jobs={j['id']:j for j in state.get('jobs',[]) if j['status']=='active'}
    for entry in state['entries']:
        if entry['status']!='reserved' or entry.get('job_id') not in jobs:
            continue
        job=jobs[entry['job_id']]; batch=root/'backend'/job['admission_id']
        run=batch/'runs'/job['task_id']; log=Path(entry['output']+'.log')
        if log.parent!=run:
            continue
        fatal=fatal_tail(log,now)
        if not fatal:
            continue
        receipt=root/'monitor-incidents'/(entry['id']+'.json')
        if receipt.exists():
            continue
        admission=runtime.verify(batch)
        task=next((t for t in admission['tasks'] if t['id']==job['task_id']),None)
        if task is None:
            raise ValueError('fatal log has no matching admitted task')
        owners=wrappers(batch,job['task_id'],proc=proc)
        if len(owners)!=1:
            incidents.append(dict(status='manual_reconciliation_required',task=job['task_id'],
                reason='runtime wrapper not uniquely visible',matching_wrappers=owners))
            continue
        owner=owners[0]
        # Revalidate both the unchanged fatal log and the PID/start identity
        # immediately before signalling; never signal an EDA child directly.
        latest=read(runtime.budget.LEDGER)
        current=next(e for e in latest['entries'] if e['id']==entry['id'])
        stat=log.stat(); process=proc/str(owner['pid'])
        argv=[s.decode() for s in (process/'cmdline').read_bytes().split(b'\0') if s]
        fields=(process/'stat').read_text().rsplit(')',1)[1].split()
        if (current['status']!='reserved' or stat.st_size!=fatal['size'] or
            stat.st_mtime_ns!=fatal['mtime_ns'] or fields[19]!=owner['start'] or
            not exact_wrapper(argv,batch,job['task_id'])):
            continue
        incident=dict(status='confirmed_abort_signal_requested',observed_at=datetime.now(timezone.utc).isoformat(),
            task=job['task_id'],job_id=job['id'],reservation_id=entry['id'],raw_log=str(log),
            raw_log_sha256=sha(log),fatal=fatal,wrapper=owner,signal='SIGTERM',
            source_sha256=sha(SOURCE),automatic_retry=False,backend_sources_changed=False)
        atomic_json(receipt,incident)
        os.kill(owner['pid'],signal.SIGTERM)
        incidents.append(incident)
    return incidents


def review(root,state=None):
    state=state or read(runtime.budget.LEDGER); rows=driver.collect(root)
    main=[r for r in rows if r['method'] in ('A','B','C','D')]
    progress=driver.live_json(root/'controller-progress.json') or {}
    active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
    software_active={(r['case'],r['L']) for r in progress.get('software_active',[])}
    variants=[]; receipt_errors=[]
    for cid,depths in matrix.DEPTHS.items():
        for L in depths:
            selected=matrix.ready_selection(root,cid,L)
            part=[r for r in main if r['case']==cid and r['comparison_L']==L]
            variant=matrix.variant_root(root,cid,L); marker=variant/'matrix-software-ready.json'
            target=root/'targets'/f'{cid}-L{L}.json'
            status=('backend_registered' if part else 'software_running' if (cid,L) in software_active
                    else 'software_waiting' if target.exists() else 'awaiting_A_reference')
            if selected and marker.exists():
                m=read(marker); soft=selected.parents[1]
                for path,key in [(selected,'selection_sha256'),(soft/'selected-replay.json','selected_replay_sha256'),
                    (soft/'all-selected-owner-audit.json','owner_audit_sha256'),
                    (soft/'matrix-stage-occupancy.json','occupancy_sha256')]:
                    if sha(path)!=m[key]:
                        receipt_errors.append(dict(case=cid,L=L,path=str(path),reason='software ready receipt hash differs'))
            variants.append(dict(case=cid,L=L,status=status,software_ready=bool(selected),
                main_statuses=dict(Counter(r['status'] for r in part)),
                targets_ps=read(target)['targets_ps'] if target.exists() else None))
    history=[]
    for row in progress.get('software_errors',[]):
        history.append(dict(row,resolved=bool(matrix.ready_selection(root,row['case'],row['L']))))
    now=time.time(); reserved=[]
    for e in state['entries']:
        if e['status']=='reserved':
            elapsed=now-datetime.fromisoformat(e['reserved_at']).timestamp()
            reserved.append(dict(task=e.get('task_id'),stage=e['stage'],elapsed_s=elapsed,
                timeout_s=e['walltime_s'],remaining_s=e['walltime_s']-elapsed))
    failures=[dict(case=r['case'],L=r['comparison_L'],T_ps=r['T_ps'],method=r['method'],
        reason=r['failure_reason'],run=r['measurement']['run']) for r in main if r['status']=='failed']
    free_bytes=__import__('shutil').disk_usage(root).free
    memory=next(int(l.split()[1])//1024 for l in Path('/proc/meminfo').read_text().splitlines() if l.startswith('MemAvailable:'))
    return dict(checked_at=datetime.now(timezone.utc).isoformat(),required_main_records=148,
        main_measured=sum(r['status']=='measured_grt' for r in main),registered_groups=len(main)//4,
        main_statuses=dict(Counter(r['status'] for r in main)),active_jobs=active,
        software_active=progress.get('software_active',[]),variants=variants,
        retained_software_errors=history,software_receipt_errors=receipt_errors,main_failures=failures,
        active_reservations=reserved,memory_available_MiB=memory,disk_free_GiB=free_bytes/1024**3,
        ledger_usage=runtime.budget.usage(state['entries']),source_sha256=sha(SOURCE),
        model_refitted=False,backend_sources_changed=False)


def publish(root,doc):
    for folder in (root/'operational-review',EVIDENCE):
        atomic_json(folder/'latest.json',doc)
        lines=['# 两档流水矩阵运行审查','',doc['checked_at'],'',
            f'主方法实测 {doc["main_measured"]}/148；已登记 {doc["registered_groups"]}/37 组；活动后端 {len(doc["active_jobs"])} 个。','',
            '| 案例 | L | 阶段 | 已实测主方法 |','| --- | ---: | --- | ---: |']
        for v in doc['variants']:
            lines.append(f'| {v["case"]} | {v["L"]} | {v["status"]} | {v["main_statuses"].get("measured_grt",0)} |')
        lines+=['',f'当前主方法失败 {len(doc["main_failures"])} 条；历史软件错误已恢复 '
                f'{sum(r["resolved"] for r in doc["retained_software_errors"])}/{len(doc["retained_software_errors"])} 条。',
                f'可用内存 {doc["memory_available_MiB"]} MiB；磁盘可用 {doc["disk_free_GiB"]:.1f} GiB。',
                '确认工具崩溃且日志停止至少120秒时，仅通知其任务包装器正常清理和结算；不自动重试。']
        (folder/'latest.md').write_text('\n'.join(lines)+'\n')


def watch(root,interval):
    import fcntl
    with (root/'monitor.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        atomic_json(root/'monitor-start.json',dict(pid=os.getpid(),source_sha256=sha(SOURCE),
            started_at=datetime.now(timezone.utc).isoformat(),interval_s=interval,
            user_authorization='审查推进进度，处理异常',automatic_retries=0))
        while True:
            try:
                state=read(runtime.budget.LEDGER)
                incidents=settle_confirmed_aborts(root,state,time.time())
                doc=review(root); doc['new_incidents']=incidents; publish(root,doc)
            except (json.JSONDecodeError,FileNotFoundError,ProcessLookupError) as error:
                # Frozen writers predate this observer and publish some JSON
                # directly. A concurrent partial write is retried next poll.
                print(json.dumps(dict(status='concurrent_publish_pending',reason=str(error))),flush=True)
                time.sleep(interval)
                continue
            print(json.dumps(dict(checked_at=doc['checked_at'],main_measured=doc['main_measured'],
                active=len(doc['active_jobs']),incidents=len(incidents)),ensure_ascii=False),flush=True)
            progress=driver.live_json(root/'controller-progress.json') or {}
            if not doc['active_jobs'] and progress.get('status') in (
                'complete','settled_with_retained_failures','retained_reference_failure','retained_software_failure'):
                return doc
            time.sleep(interval)


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('action',choices=('review','watch'))
    parser.add_argument('--root',type=Path,default=runtime.DEFAULT)
    parser.add_argument('--interval',type=int,default=45); args=parser.parse_args()
    if not 10<=args.interval<=60:
        parser.error('interval must be 10..60 seconds')
    result=watch(args.root.resolve(),args.interval) if args.action=='watch' else review(args.root.resolve())
    if args.action=='review':
        publish(args.root.resolve(),result)
    print(json.dumps({k:result[k] for k in ('checked_at','main_measured','registered_groups')},ensure_ascii=False))
