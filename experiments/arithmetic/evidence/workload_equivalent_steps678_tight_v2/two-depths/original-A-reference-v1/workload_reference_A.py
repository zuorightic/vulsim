"""Reuse one original unsplit A per case; dispatch only frozen B/C/D tasks.

This versioned controller leaves predecessor selectors, runtime, admissions,
clocks, RTL and ledger history intact. A parent-only handoff adopts existing
workers. Exclusive per-target A tasks are excluded before EDA; original A
reference requests and measurements are always reported on their own axes.
"""
import argparse
from collections import Counter, defaultdict
from contextlib import contextmanager
import csv
from datetime import datetime, timezone
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from .sampling_time_contract import ROOT
from .workload_abcd import read, sha
from . import workload_two_depths_run as old
from . import workload_latency_matrix as matrix
from . import workload_nine_runtime as runtime
from . import workload_two_depths_monitor as monitor

SOURCE=Path(__file__).resolve()
VERSION='nine-workloads-original-A-reference-v1'
EVIDENCE=old.EVIDENCE/'original-A-reference-v1'
USER_INSTRUCTION='标出A初版测试设置的时钟与实际周期，不再拿流水T/L目标测A'
BCD=('B','C','D')


def now():
    return datetime.now(timezone.utc).isoformat()


def write(path,value):
    monitor.atomic_json(Path(path),value)


def directory(root):
    return Path(root)/'original-A-reference-v1'


def aliases(root):
    result=defaultdict(set)
    for p in sorted((Path(root)/'plans').glob('*.json')):
        for group in read(p)['records']:
            for method,m in group['methods'].items():
                result[str(Path(m['measurement']['run']).resolve())].add(method)
    return result


def classification(batch,task,owners):
    names=owners.get(str((Path(batch)/'runs'/task['id']).resolve()),set())
    if names=={'A'}:
        return 'excluded_repeated_A'
    if names & {'B','C','D','same_policy_static'}:
        return 'pipeline_or_ablation'
    raise ValueError('task lacks a uniquely explained method ownership: '+task['id'])


def references(root):
    """The original clock-calibration A, without applying a BCD target to it."""
    parent=old.PARENT
    original=read(parent/'A-reference/admission.json')
    tasks={t['case']:t for t in original['tasks']}
    mac=max(read(parent/'final-mac32-methods.json')['records'],key=lambda g:g['target']['T_ps'])
    mac_method=mac['methods']['A']
    answer=[]
    for cid in matrix.DEPTHS:
        if cid=='mac32':
            request=mac['target']['T_ps'];run=parent/'final-mac32/runs'/mac_method['task_id']
            task=mac_method
            origin='Original MAC32 A at the previously declared largest request (1000ps)'
        else:
            task=tasks[cid];request=task['period_ps'];run=parent/'A-reference/runs'/task['id']
            origin='Original unsplit A clock-calibration measurement'
        attempts=[str(run)]
        if cid=='montgomery256':
            repaired=parent/'A-reference-repair-v1'
            if (repaired/'admission.json').exists():
                attempts.extend(str(repaired/'runs'/t['id']) for t in read(repaired/'admission.json')['tasks'])
            successor=Path(root)/'backend/montgomery-A-reference-9x2'
            if (successor/'admission.json').exists():
                attempts.extend(str(successor/'runs'/t['id']) for t in read(successor/'admission.json')['tasks'])
            run=Path(attempts[-1])
        manifest=old.live_json(run/'manifest.json') or {}
        actual=old.checked_readout(run,request,inherited=True)
        item=dict(case=cid,method='A',L=1,reference_request_ps=request,
            status='measured_grt' if actual else manifest.get('status','not_started'),
            run=str(run),original_reference_run=attempts[0],retained_reference_attempts=attempts,
            origin=origin,RTL_sha256=task.get('rtl_sha256',mac_method.get('rtl_sha256')),
            BCD_target_applied_to_A=False,comparison_setup_met=None,
            failure_reason=manifest.get('failure_reason'),new_A_EDA_requested=False)
        if actual:
            item.update(Tmin_ps=actual['full_setup_minimum_period_ps'],area_um2=actual['area_um2'],
                frequency_MHz=1e6/actual['full_setup_minimum_period_ps'],hold_WNS_ps=actual['hold_WNS_ps'],
                setup_met_at_own_request=actual['full_setup_minimum_period_ps']<=request,
                measured_threads=manifest['threads_per_tool'],clock_readout_sha256=sha(run/'clock-readout/result.json'),
                manifest_sha256=sha(run/'manifest.json'))
        answer.append(item)
    return answer


def prepare(root):
    root=Path(root).resolve();folder=directory(root);folder.mkdir(exist_ok=True)
    owners=aliases(root); tasks=[];frozen={}
    for p in sorted((root/'backend').glob('matrix-*/admission.json')):
        a=runtime.verify(p.parent)
        frozen[str(p)]=sha(p);frozen[str(p.parent/'freeze.json')]=sha(p.parent/'freeze.json')
        for t in a['tasks']:
            tasks.append(dict(batch=str(p.parent),task_id=t['id'],case=t['case'],request_ps=t['period_ps'],
                rtl_sha256=t['rtl_sha256'],classification=classification(p.parent,t,owners)))
    for p in (old.SOURCE,runtime.SOURCE,matrix.SOURCE,monitor.SOURCE,runtime.POLICY,root/'protocol.json'):
        frozen[str(p)]=sha(p)
    refs=references(root)
    # Every current unsplit A must have exactly the same RTL as its original A.
    reference_hashes={r['case']:r['RTL_sha256'] for r in refs}
    for p in (root/'plans').glob('*.json'):
        for g in read(p)['records']:
            if 'A' in g['methods'] and g['methods']['A']['rtl_sha256']!=reference_hashes[g['case']]:
                raise ValueError('A reference differs from selected unsplit RTL: '+g['case'])
    proposal=dict(version=VERSION,user_instruction=USER_INSTRUCTION,prepared_at=now(),source_sha256=sha(SOURCE),
        required_groups=37,required_BCD_records=111,required_unique_A_references=9,
        logical_acceptance_records=120,display_ABCD_bindings=148,A_repeated_bindings_are_not_new_measurements=True,
        original_reference_requests={r['case']:r['reference_request_ps'] for r in refs},
        clocks_models_RTL_selectors_and_backend_unchanged=True,threads_per_tool=2,parallel_jobs=9,
        automatic_retries=0,reference_PPA_used_for_D=False,already_admitted_tasks=tasks,
        protected_frozen_files=frozen)
    existing=folder/'protocol-amendment.json'
    if existing.exists():
        prior=read(existing)
        for k in ('source_sha256','original_reference_requests','protected_frozen_files'):
            if prior[k]!=proposal[k]:
                raise ValueError('prepared amendment identity changed: '+k)
        proposal=prior
    else:
        write(existing,proposal)
    write(folder/'A-references.json',refs)
    return proposal


def process_info(pid):
    try:
        p=Path('/proc')/str(pid)
        fields=(p/'stat').read_text().rsplit(')',1)[1].split()
        argv=[v.decode() for v in (p/'cmdline').read_bytes().split(b'\0') if v]
        if fields[0]=='Z':return None
        return dict(pid=int(pid),start=fields[19],state=fields[0],argv=argv,cwd=str((p/'cwd').resolve()))
    except (OSError,UnicodeDecodeError,ValueError,IndexError):
        return None


def matches(info,module,action,root):
    if not info:return False
    argv=info['argv']
    try:
        i=argv.index('-m')
        if argv[i+1:i+3]!=[module,action]:return False
        if '--root' in argv:
            return Path(argv[argv.index('--root')+1]).resolve()==Path(root).resolve()
        # The existing two-depth controller and observer were launched with
        # their documented default, not an explicit --root argument.
        return (module in ('experiments.arithmetic_dse.workload_two_depths_run',
                           'experiments.arithmetic_dse.workload_two_depths_monitor') and
            argv[i+3:]==[] and Path(root).resolve()==old.DEFAULT.resolve() and
            info.get('cwd')==str(ROOT.resolve()))
    except (ValueError,IndexError):
        return False


def find_processes(module,action,root):
    found=[]
    for p in Path('/proc').glob('[0-9]*'):
        info=process_info(int(p.name))
        if matches(info,module,action,root):found.append(info)
    return found


def signal_exact(info,signum):
    current=process_info(info['pid'])
    if not current or current['start']!=info['start'] or current['argv']!=info['argv']:
        raise ValueError('process identity changed before signal')
    os.kill(info['pid'],signum)


def active_A_cancellations(root):
    """Check every owner before sending any cancellation signal."""
    state=read(runtime.budget.LEDGER);owners=aliases(root);planned=[]
    for job in state.get('jobs',[]):
        if job['status'] not in ('active','unsettled') or not job['admission_id'].startswith('matrix-'):
            continue
        batch=Path(root)/'backend'/job['admission_id'];a=runtime.verify(batch)
        task=next(t for t in a['tasks'] if t['id']==job['task_id'])
        if classification(batch,task,owners)!='excluded_repeated_A':continue
        wrappers=monitor.wrappers(batch,task['id'])
        if len(wrappers)!=1:
            latest=read(runtime.budget.LEDGER)
            current=next(j for j in latest['jobs'] if j['id']==job['id'])
            if current['status']=='released':continue  # Finished during inspection.
            raise ValueError('exclusive A wrapper not uniquely visible: '+task['id'])
        info=process_info(wrappers[0]['pid'])
        if not info or not monitor.exact_wrapper(info['argv'],batch,task['id']):
            latest=read(runtime.budget.LEDGER)
            if next(j for j in latest['jobs'] if j['id']==job['id'])['status']=='released':continue
            raise ValueError('exclusive A wrapper identity differs')
        planned.append(dict(job=job,batch=str(batch),task_id=task['id'],wrapper=info,
            signal='SIGTERM',reason=USER_INSTRUCTION,methods=['A']))
    return state,planned


@contextmanager
def paused_parents(infos,folder):
    """Restore dispatch if validation fails before the handoff is committed."""
    paused=[]
    try:
        for info in infos:
            signal_exact(info,signal.SIGSTOP);paused.append(info)
        time.sleep(.2)
        for info in paused:
            current=process_info(info['pid'])
            if not current or current['state'] not in ('T','t'):
                raise ValueError('parent did not stop')
        yield paused
    except BaseException as error:
        resumed=[];resume_errors=[]
        if not (folder/'handoff.json').exists():
            for info in reversed(paused):
                try:
                    signal_exact(info,signal.SIGCONT);resumed.append(info['pid'])
                except (OSError,ValueError) as resume_error:
                    resume_errors.append(str(resume_error))
        write(folder/'handoff-failure.json',dict(at=now(),reason=str(error),
            committed=(folder/'handoff.json').exists(),resumed_predecessor_pids=resumed,
            resume_errors=resume_errors,automatic_retry=False))
        raise


def apply(root):
    root=Path(root).resolve();folder=directory(root);folder.mkdir(exist_ok=True)
    proposal=read(folder/'protocol-amendment.json')
    if proposal['source_sha256']!=sha(SOURCE):raise ValueError('reviewed source changed')
    for name,digest in proposal['protected_frozen_files'].items():
        if sha(name)!=digest:raise ValueError('protected input changed before handoff: '+name)
    if (folder/'handoff.json').exists():raise ValueError('preserve prior handoff; no automatic reapply')
    controllers=find_processes('experiments.arithmetic_dse.workload_two_depths_run','run',root)
    observers=find_processes('experiments.arithmetic_dse.workload_two_depths_monitor','watch',root)
    if len(controllers)!=1 or len(observers)>1:
        raise ValueError('need exactly one visible old controller and at most one monitor; run apply on host')
    old_controller=controllers[0]
    # Pause only the Python parents. Existing EDA and software children continue.
    with paused_parents([old_controller,*observers],folder) as paused:
        state,planned=active_A_cancellations(root)
        for src in (root/'controller-progress.json',root/'comparison.json',root/'comparison.md',
                    old.EVIDENCE/'README.md',monitor.EVIDENCE/'latest.json',monitor.EVIDENCE/'latest.md'):
            if src.exists():
                dest=folder/'predecessor-snapshot'/('evidence-' if old.EVIDENCE in src.parents else 'root-')/src.name
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(src.read_bytes())
        cancelled=[]
        for record in planned:
            info=record['wrapper'];current=process_info(info['pid'])
            if not current:continue  # Wrapper settled after the preflight.
            record['requested_at']=now()
            cancelled.append(record);write(folder/'cancelled-repeated-A.json',cancelled)
            # run_command performs descendant cleanup and actual cost settlement.
            try:
                signal_exact(info,signal.SIGTERM)
            except ProcessLookupError:
                record['finished_before_signal']=True
                write(folder/'cancelled-repeated-A.json',cancelled)
        handoff=dict(version=VERSION,at=now(),user_instruction=USER_INSTRUCTION,
            source_sha256=sha(SOURCE),amendment_sha256=sha(folder/'protocol-amendment.json'),
            paused_parents=paused,adopted_active_jobs=state.get('jobs',[]),
            cancelled_exclusive_A_tasks=[r['task_id'] for r in cancelled],BCD_workers_signalled=False,
            old_frozen_sources_modified=False,old_admissions_modified=False,
            ledger_entries_before=len(state['entries']),active_A_cleanup_must_settle=True)
        write(folder/'handoff.json',handoff)
    log=folder/'controller.log'
    with log.open('a') as f:
        child=subprocess.Popen([sys.executable,'-u','-m','experiments.arithmetic_dse.workload_reference_A',
            'run','--root',str(root)],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=f,stderr=subprocess.STDOUT,
            start_new_session=True)
    write(folder/'controller-launch.json',dict(pid=child.pid,at=now(),log=str(log),source_sha256=sha(SOURCE)))
    deadline=time.monotonic()+35
    while time.monotonic()<deadline:
        progress=old.live_json(folder/'controller-progress.json')
        if progress and progress.get('ready'):
            handoff.update(successor_ready_at=progress['at'],successor_pid=child.pid)
            write(folder/'handoff.json',handoff)
            return dict(status='handoff_complete',successor_pid=child.pid,
                cancelled_A=len(cancelled),BCD_workers_signalled=False,progress=progress)
        if child.poll() is not None:raise RuntimeError('successor exited; inspect '+str(log))
        time.sleep(1)
    raise RuntimeError('successor readiness pending; inspect '+str(log))


def register_variant(root,cid,L):
    """Future ready variants receive no per-target A physical task at all."""
    path=Path(root)/'plans'/f'{cid}-L{L}.json'
    if path.exists():return read(path)
    selection=matrix.ready_selection(root,cid,L)
    if selection is None:return None
    owners=old.collect(root);cache={(r['rtl_sha256'],r['T_ps']):r['measurement'] for r in owners if r['method']!='A'}
    batch=Path(root)/'backend'/f'matrix-{cid}-L{L}';tasks=[];records=[]
    inputs=[selection,matrix.SOURCE,SOURCE,Path(root)/'protocol.json',Path(root)/'targets'/f'{cid}-L{L}.json',
            directory(root)/'protocol-amendment.json']
    for g in read(selection)['records']:
        target=g['target']['T_ps'];record=dict(case=cid,comparison_L=L,target_ps=target,methods={},
            A_reference='original-A-reference-v1/A-references.json#'+cid)
        for name,m in g['methods'].items():
            if name=='A':continue
            if name not in (*BCD,'same_policy_static'):raise ValueError('unknown physical method')
            key=(m['rtl_sha256'],target);measurement=cache.get(key)
            if measurement is None:measurement=old.settled_old_measurement(cid,target,m['rtl_sha256'])
            if measurement is None:
                task_id=f'{cid}-L{L}-T{target}-'+m['rtl_sha256'][:12]
                task=dict(id=task_id,case=cid,rtl=m['rtl'],period_ps=target,
                    simulation_status=m['simulation_status'],simulation_receipt=m['simulation_receipt'],
                    large=cid not in ('mac32','add512'),source_selection_file=str(selection),
                    source_selection_sha256=sha(selection),shared_methods=[])
                failed=old.old_memory_failure(cid,target,m['rtl_sha256'])
                if failed:task.update(capacity_memory_MiB=16384,memory_failure_manifest=str(failed))
                tasks.append(task);measurement=dict(run=str(batch/'runs'/task_id),inherited=False,threads=2,
                    batch=str(batch),task_id=task_id)
            cache[key]=measurement
            record['methods'][name]=dict(method=name,L=m['L'],grammar=m['grammar'],rtl_sha256=m['rtl_sha256'],
                rtl=m['rtl'],prediction=m['prediction'],measurement=measurement)
            inputs.extend(p for p in Path(m['rtl']).parent.iterdir() if p.is_file())
        records.append(record)
    value=dict(case=cid,L=L,records=records,selection=str(selection),selection_sha256=sha(selection),
        source_sha256=sha(SOURCE),new_unique_tasks=len(tasks),A_per_target_physical_tasks=0,
        A_policy=VERSION,old_results_repriced=False,inherited_thread_counts_explicit=True,model_refitted=False)
    write(path,value)
    if tasks:runtime.admit(batch,tasks,extra_inputs=[*inputs,path])
    return value


def publish(root):
    root=Path(root).resolve();folder=directory(root);folder.mkdir(exist_ok=True)
    EVIDENCE.mkdir(parents=True,exist_ok=True)
    refs=references(root);bycase={r['case']:r for r in refs}
    rows=old.collect(root);bcd=[r for r in rows if r['method'] in BCD]
    lookup={(r['case'],r['comparison_L'],r['T_ps'],r['method']):r for r in bcd}
    groups=[];complete_rows=[]
    for target in read(root/'target-matrix.json')['rows']:
        for slot,T in enumerate(target.get('targets_ps',[None,None]),1):
            methods={}
            for name in BCD:
                r=lookup.get((target['case'],target['L'],T,name),dict(case=target['case'],comparison_L=target['L'],
                    T_ps=T,method=name,status='awaiting_A_reference' if T is None else 'software_pending'))
                methods[name]=r;complete_rows.append(r)
            groups.append(dict(case=target['case'],comparison_L=target['L'],BCD_target_ps=T,target_slot=slot,
                A_reference=bycase[target['case']],methods=methods))
    state=read(runtime.budget.LEDGER);active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
    counts=Counter(r['status'] for r in complete_rows)
    doc=dict(version=VERSION,at=now(),operational_status='applied' if (folder/'handoff.json').exists() else 'prepared_preview',
        required_groups=37,required_BCD_records=111,
        required_unique_A_references=9,BCD_measured=counts['measured_grt'],
        A_reference_measured=sum(r['status']=='measured_grt' for r in refs),BCD_statuses=dict(counts),
        A_references=refs,comparison_groups=groups,BCD_records=complete_rows,
        same_policy_static=[r for r in rows if r['method']=='same_policy_static'],
        legacy_per_target_A_records=[r for r in rows if r['method']=='A'],
        physical_comparison_complete=(counts['measured_grt']==111 and all(r['status']=='measured_grt' for r in refs)),
        active_jobs=active,qualification='diagnostic_only',model_refitted=False,old_A_used_for_D_reselection=False,
        source_sha256=sha(SOURCE),parallel_jobs=9,threads_per_tool=2,automatic_retries=0)
    def cell(r):
        return f'{r["Tmin_ps"]:.3f} / {r["area_um2"]:.3f}'+(' ✓' if r['setup_met'] else '') if r['status']=='measured_grt' else r['status']
    lines=['# ABCD比较：A复用原未拆分参考，BCD按流水目标测试','',doc['at'],'',
        f'A参考已实测{doc["A_reference_measured"]}/9；BCD已实测{doc["BCD_measured"]}/111。37组展示重复引用每案例同一份A，不再产生37次A测量要求。',
        'A_request是当时实际SDC/ABC请求，A_Tmin是该固定实现的完整RR/IR/RO实测最小周期；BCD_T是B/C/D的流水目标。A不按BCD_T判断setup，也不将A_Tmin改写成BCD_T。',
        '面积单位µm²，周期单位ps；✓仅表示BCD setup达标，hold与频率单列。工艺／外壳／I/O规则保持；A与BCD映射请求有意不同，比较为原始基线与目标流水实现。','',
        '| 案例 | A实际请求 ps | A实测Tmin ps | A面积µm² | A hold ps | 状态 |','| --- | ---: | ---: | ---: | ---: | --- |']
    for r in refs:
        lines.append('| '+' | '.join([r['case'],str(r['reference_request_ps']),
            f'{r["Tmin_ps"]:.6f}' if 'Tmin_ps' in r else '—',f'{r["area_um2"]:.6f}' if 'area_um2' in r else '—',
            f'{r["hold_WNS_ps"]:.6f}' if 'hold_WNS_ps' in r else '—',r['status']])+' |')
    lines+=['','| 案例 | 比较L | BCD目标 ps | A请求 ps | A实测Tmin/面积 | B实测Tmin/面积 | C实测Tmin/面积 | D实测Tmin/面积 |',
        '| --- | ---: | ---: | ---: | --- | --- | --- | --- |']
    for g in groups:
        a=g['A_reference'];a_text=f'{a["Tmin_ps"]:.3f} / {a["area_um2"]:.3f}' if 'Tmin_ps' in a else a['status']
        lines.append('| '+' | '.join([g['case'],str(g['comparison_L']),str(g['BCD_target_ps']) if g['BCD_target_ps'] else f'待A/档{g["target_slot"]}',
            str(a['reference_request_ps']),a_text,*[cell(g['methods'][n]) for n in BCD]])+' |')
    lines+=['','已测BCD逐项（A单独见上表及JSON，未测值不填预测）：','',
        '| 案例 | L/T | 方法 | Tmin ps | 面积µm² | MHz | setup | hold ps | 实际线程 | 原始读数 |',
        '| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |']
    for r in bcd:
        if r['status']=='measured_grt':lines.append('| '+' | '.join([r['case'],f'{r["comparison_L"]}/{r["T_ps"]}',r['method'],
            f'{r["Tmin_ps"]:.6f}',f'{r["area_um2"]:.6f}',f'{r["frequency_MHz"]:.3f}',str(r['setup_met']),f'{r["hold_WNS_ps"]:.6f}',
            str(r['measured_threads']),f'[readout]({r["measurement"]["run"]}/clock-readout/result.json)'])+' |')
    lines+=['','MAC32复用已预登记的1000ps原A；其余复用初次A-reference。Montgomery保持原36000ps及已有失败，没有用综合值或紧目标A代替。',
        '原紧目标A的已有实测、失败、中止及费用保存在旧快照和JSON的legacy_per_target_A_records中，不删除、不冒充新口径A。',
        'A参考请求不改变此前已冻结的BCD目标、模型、候选选择和RTL；应用PPA没有回流D。当前共享模型仍为诊断身份。',
        '独立原始A表：[A-references.json](A-references.json)；全部当前记录：[comparison.json](comparison.json)；调度：[controller-progress.json](controller-progress.json)。']
    content='\n'.join(lines)+'\n'
    for dest in (folder,EVIDENCE):
        write(dest/'comparison.json',doc);write(dest/'A-references.json',refs)
        (dest/'comparison.md').write_text(content)
        with (dest/'A-references.csv').open('w',newline='') as f:
            fields=['case','reference_request_ps','Tmin_ps','area_um2','frequency_MHz','hold_WNS_ps',
                'measured_threads','status','run','origin']
            w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(refs)
        with (dest/'comparison.csv').open('w',newline='') as f:
            fields=['case','comparison_L','BCD_target_ps','target_slot','method','measurement_request_ps',
                'Tmin_ps','area_um2','frequency_MHz','setup_met_at_own_request','hold_WNS_ps','measured_threads','status','run']
            w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
            for g in groups:
                a=g['A_reference']
                w.writerow(dict(a,comparison_L=g['comparison_L'],BCD_target_ps=g['BCD_target_ps'],
                    target_slot=g['target_slot'],measurement_request_ps=a['reference_request_ps']))
                for n in BCD:
                    r=g['methods'][n]
                    w.writerow(dict(r,comparison_L=g['comparison_L'],BCD_target_ps=g['BCD_target_ps'],
                        target_slot=g['target_slot'],measurement_request_ps=g['BCD_target_ps'],
                        setup_met_at_own_request=r.get('setup_met'),run=r.get('measurement',{}).get('run')))
    # The old controller/observer are paused; this navigation now names the active version.
    if (folder/'handoff.json').exists():
        (old.EVIDENCE/'README.md').write_text('# 九例两档L当前入口\n\n'
            '按用户修订：A每案例复用原始参考，表中保留其实际请求和实测Tmin；不再按流水目标重测A。\n\n'
            '[现行ABCD完整表](original-A-reference-v1/comparison.md)；[A参考与调度修订](original-A-reference-v1/README.md)。\n\n'
            '原148条逐目标口径及已发生结果按旧版本归档，BCD的冻结目标／RTL／流程保持。\n')
    return doc


def run(root,interval=10):
    root=Path(root).resolve();folder=directory(root);handoff=read(folder/'handoff.json')
    if handoff['source_sha256']!=sha(SOURCE):raise ValueError('handoff source changed')
    with (folder/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        attempts_path=folder/'dispatch-attempts.json'
        attempts=old.live_json(attempts_path) or {};children={};verified=set()
        write(folder/'controller-start.json',dict(pid=os.getpid(),at=now(),source_sha256=sha(SOURCE),
            automatic_retries=0,user_instruction=USER_INSTRUCTION))
        while True:
            for key,(child,log) in list(children.items()):
                code=child.poll()
                if code is not None:
                    attempts[key].update(exit_code=code,finished_at=now());del children[key]
                    write(attempts_path,attempts)
            for cid,depths in matrix.DEPTHS.items():
                for L in depths:
                    if matrix.ready_selection(root,cid,L):register_variant(root,cid,L)
            state=read(runtime.budget.LEDGER)
            monitor.settle_confirmed_aborts(root,state,time.time())
            state=read(runtime.budget.LEDGER);claims={(j['admission_id'],j['task_id']):j for j in state.get('jobs',[])}
            active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
            owners=aliases(root);excluded=[];queued=[]
            for p in sorted((root/'backend').glob('matrix-*/admission.json')):
                batch=p.parent
                if str(batch) not in verified:runtime.verify(batch);verified.add(str(batch))
                a=read(p)
                for t in a['tasks']:
                    key=(a['id'],t['id']);journal='/'.join(key)
                    if classification(batch,t,owners)=='excluded_repeated_A':
                        excluded.append(dict(batch=str(batch),task_id=t['id'],reason=USER_INSTRUCTION));continue
                    if key in claims or journal in attempts:continue
                    # A retained run without a ledger claim requires reconciliation,
                    # never an implicit retry of that directory.
                    if (batch/'runs'/t['id']/'manifest.json').exists():continue
                    queued.append((batch,t,journal))
            unclaimed_children=sum(tuple(key.split('/',1)) not in claims for key in children)
            slots=9-len(active)-unclaimed_children
            for batch,t,journal in queued[:max(0,slots)]:
                if old.available_memory_MiB()<8192:break
                log=folder/'dispatch-logs'/(t['id']+'.log');log.parent.mkdir(exist_ok=True)
                attempts[journal]=dict(task_id=t['id'],batch=str(batch),started_at=now(),log=str(log))
                write(attempts_path,attempts)
                with log.open('w') as f:
                    child=subprocess.Popen([sys.executable,'-u','-m','experiments.arithmetic_dse.workload_nine_runtime',
                        'task','--root',str(batch),'--task-id',t['id']],cwd=ROOT,stdin=subprocess.DEVNULL,
                        stdout=f,stderr=subprocess.STDOUT)
                attempts[journal]['pid']=child.pid;children[journal]=(child,log);write(attempts_path,attempts)
            write(folder/'dispatch-exclusions.json',dict(at=now(),tasks=excluded,new_A_EDA_calls=0))
            result=publish(root)
            software_active=[]
            for info in find_processes('experiments.arithmetic_dse.workload_latency_matrix','software',root):
                argv=info['argv'];cid=argv[argv.index('--case')+1];L=int(argv[argv.index('--L')+1])
                if not matrix.ready_selection(root,cid,L):software_active.append(dict(case=cid,L=L,pid=info['pid']))
            progress=dict(ready=True,at=now(),status='running_BCD_with_original_A_reference',
                BCD_measured=result['BCD_measured'],required_BCD_records=111,
                A_reference_measured=result['A_reference_measured'],required_A_references=9,
                excluded_unique_A_tasks=len(excluded),active_jobs=result['active_jobs'],
                new_workers=[dict(task=k,**v) for k,v in attempts.items() if k in children],
                software_active=software_active,
                source_sha256=sha(SOURCE),automatic_retries=0)
            write(folder/'controller-progress.json',progress);write(EVIDENCE/'controller-progress.json',progress)
            print(json.dumps({k:progress[k] for k in ('at','BCD_measured','A_reference_measured','excluded_unique_A_tasks')},ensure_ascii=False),flush=True)
            ready_count=sum(matrix.ready_selection(root,c,L) is not None for c,ls in matrix.DEPTHS.items() for L in ls)
            if not result['active_jobs'] and not children and not queued and ready_count==16:
                progress['status']='BCD_settled_with_retained_Montgomery_reference_failure'
                write(folder/'controller-progress.json',progress);write(EVIDENCE/'controller-progress.json',progress)
                return result
            if not result['active_jobs'] and not children and not queued and not software_active and ready_count<16:
                progress['status']='settled_with_retained_software_or_reference_failure'
                write(folder/'controller-progress.json',progress);write(EVIDENCE/'controller-progress.json',progress)
                return result
            if result['physical_comparison_complete'] and not children:return result
            time.sleep(interval)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','apply','run','report'))
    p.add_argument('--root',type=Path,default=old.DEFAULT);args=p.parse_args()
    result={'prepare':prepare,'apply':apply,'run':run,'report':publish}[args.action](args.root)
    if args.action in ('prepare','report'):
        print(json.dumps({k:result[k] for k in result if k in ('version','required_BCD_records','required_unique_A_references',
            'A_reference_measured','BCD_measured','physical_comparison_complete')},ensure_ascii=False))
    elif args.action=='apply':print(json.dumps(result,ensure_ascii=False,indent=2))
