"""Nine-worker controller for the user-requested two-depth workload matrix.

Adopt completed predecessor measurements with their actual thread metadata;
transfer only unmeasured/failing work into explicit two-thread admissions.
Software workers never receive application timing/area observations. Failed
attempts and permanent ledger claims are retained, without automatic retries.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from .sampling_time_contract import ROOT
from .workload_abcd import read,write,sha
from . import budget
from . import workload_nine_runtime as runtime
from . import workload_latency_matrix as matrix
from .workload_tight_run import DEFAULT as PARENT
from .workload_dot16_latency import frozen

DEFAULT=runtime.DEFAULT
SOURCE=Path(__file__).resolve()
EVIDENCE=ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths'


def live_json(path):
    """A live predecessor writes JSON directly; incomplete writes are pending."""
    try:
        return read(path)
    except (FileNotFoundError,json.JSONDecodeError):
        return None


def checked_readout(run,T,inherited):
    manifest=live_json(run/'manifest.json'); actual=live_json(run/'clock-readout/result.json')
    if not manifest or manifest.get('status')!='completed' or not actual:
        return None
    try:
        classes=actual['classes']
        if (actual['target_ps']!=T or actual['full_setup_minimum_period_ps']<=0 or
            not classes['threshold_check_-0.1']['slack_ps']<0<=classes['threshold_check_0.1']['slack_ps']):
            return None
        if not inherited:
            outcome=live_json(run/'measurement-outcome.json')
            if (not outcome or outcome.get('status')!='completed' or not outcome.get('ledger_settled') or
                outcome['manifest_sha256']!=sha(run/'manifest.json') or
                outcome['clock_readout_sha256']!=sha(run/'clock-readout/result.json')):
                return None
            if 'verification_receipt_sha256' in outcome:
                if outcome['verification_receipt_sha256']!=sha(run/'verification-receipt.json'):
                    return None
    except (KeyError,FileNotFoundError,TypeError):
        return None
    return actual


def settled_old_measurement(cid,T,rtl_hash):
    for p in PARENT.glob('final-*-methods.json'):
        doc=read(p); batch=Path(doc['physical_batch'])
        for group in doc['records']:
            if group['case']!=cid or group['target']['T_ps']!=T:
                continue
            for m in group['methods'].values():
                if m['rtl_sha256']!=rtl_hash:
                    continue
                run=batch/'runs'/m['task_id']; clock=run/'clock-readout/result.json'
                if checked_readout(run,T,inherited=True):
                    return dict(run=str(run),inherited=True,threads=read(run/'manifest.json')['threads_per_tool'],
                        clock_readout_sha256=sha(clock),original_admission=str(batch/'admission.json'),
                        original_task_id=m['task_id'],scope='retained completed measurement; original thread count reported')
    return None


def old_memory_failure(cid,T,rtl_hash):
    for p in PARENT.glob('final-*/admission.json'):
        for task in read(p)['tasks']:
            if task['case']==cid and task['period_ps']==T and task['rtl_sha256']==rtl_hash:
                manifest=p.parent/'runs'/task['id']/'manifest.json'
                if manifest.exists() and 'memory_limit' in read(manifest).get('failure_reason',''):
                    return manifest
    return None


def register_variant(root,cid,L,cache):
    selection=matrix.ready_selection(root,cid,L)
    if not selection:
        return None
    name=f'{cid}-L{L}'; plan_path=root/'plans'/(name+'.json')
    if plan_path.exists():
        return read(plan_path)
    result=read(selection); tasks=[]; records=[]
    batch=root/'backend'/('matrix-'+name); inputs=[selection,matrix.SOURCE,SOURCE,root/'protocol.json',
        root/'targets'/f'{cid}-L{L}.json']
    for group in result['records']:
        record=dict(case=cid,comparison_L=L,target_ps=group['target']['T_ps'],methods={})
        for method,m in group['methods'].items():
            T=record['target_ps']; key=(m['rtl_sha256'],T)
            measurement=cache.get(key)
            if measurement is None:
                measurement=settled_old_measurement(cid,T,m['rtl_sha256'])
            if measurement is None:
                task_id=f'{cid}-L{L}-T{T}-'+m['rtl_sha256'][:12]
                task=dict(id=task_id,case=cid,rtl=m['rtl'],period_ps=T,
                    simulation_status=m['simulation_status'],simulation_receipt=m['simulation_receipt'],
                    large=cid not in ('mac32','add512'),source_selection_file=str(selection),
                    source_selection_sha256=sha(selection),shared_methods=[])
                failed=old_memory_failure(cid,T,m['rtl_sha256'])
                if failed:
                    task.update(capacity_memory_MiB=16384,memory_failure_manifest=str(failed),
                        recovery='same selected RTL and T; named 16GiB capacity successor; two-thread policy')
                tasks.append(task)
                measurement=dict(run=str(batch/'runs'/task_id),inherited=False,threads=2,
                    batch=str(batch),task_id=task_id)
            cache[key]=measurement
            record['methods'][method]=dict(method=method,L=m['L'],grammar=m['grammar'],
                rtl_sha256=m['rtl_sha256'],rtl=m['rtl'],prediction=m['prediction'],measurement=measurement)
            for p in Path(m['rtl']).parent.iterdir():
                if p.is_file():
                    inputs.append(p)
        records.append(record)
    value=dict(case=cid,L=L,records=records,selection=str(selection),selection_sha256=sha(selection),
        source_sha256=sha(SOURCE),new_unique_tasks=len(tasks),old_results_repriced=False,
        inherited_thread_counts_explicit=True,model_refitted=False)
    frozen(plan_path,value)
    if tasks:
        runtime.admit(batch,tasks,extra_inputs=[*inputs,plan_path])
    return value


def reference(root):
    batch=root/'backend/montgomery-A-reference-9x2'
    if (batch/'admission.json').exists():
        return batch
    original=PARENT/'A-reference-repair-v1'; task=dict(read(original/'admission.json')['tasks'][0])
    failed=original/'runs'/task['id']/'manifest.json'
    task.update(id='montgomery256-A-reference-9x2-capacity',capacity_memory_MiB=16384,
        memory_failure_manifest=str(failed),source_selection_file=str(original/'freeze.json'),
        predecessor_task=task['id'],large=True)
    runtime.admit(batch,[task],role='clock_calibration',extra_inputs=[SOURCE,root/'protocol.json'])
    return batch


def available_memory_MiB():
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith('MemAvailable:'):
            return int(line.split()[1])//1024
    raise ValueError('MemAvailable missing')


def launch_software(root,cid,L):
    logs=root/'software-logs'; logs.mkdir(exist_ok=True); path=logs/f'{cid}-L{L}.log'
    with path.open('w') as stream:
        child=subprocess.Popen([sys.executable,'-u','-m','experiments.arithmetic_dse.workload_latency_matrix',
            'software','--root',str(root),'--case',cid,'--L',str(L)],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    return child,path


def launch_physical(batch,task):
    path=batch/'dispatch-logs'/(task['id']+'.log'); path.parent.mkdir(exist_ok=True)
    with path.open('w') as stream:
        child=subprocess.Popen([sys.executable,'-u','-m','experiments.arithmetic_dse.workload_nine_runtime',
            'task','--root',str(batch),'--task-id',task['id']],cwd=ROOT,stdout=stream,stderr=subprocess.STDOUT)
    progress=read(batch/'progress.json'); progress['active'].append(task['id']); progress['status']='running'
    write(batch/'progress.json',progress)
    return child,path


def physical_done(batch,task,code,log):
    p=read(batch/'progress.json'); p['active'].remove(task['id'])
    if code:
        p['errors'].append(dict(task=task['id'],exit_code=code,reason='physical leaf failed; see '+str(log)))
    else:
        p['completed'].append(task['id'])
    a=read(batch/'admission.json')
    if len(p['completed'])+len(p['errors'])==len(a['tasks']) and not p['active']:
        p['status']='batch_settled'
    write(batch/'progress.json',p)


def collect(root):
    rows=[]
    for plan in sorted((root/'plans').glob('*.json')):
        for group in read(plan)['records']:
            for name,m in group['methods'].items():
                run=Path(m['measurement']['run']); clock=run/'clock-readout/result.json'
                manifest=live_json(run/'manifest.json') or {}
                outcome=live_json(run/'measurement-outcome.json') or {}
                entry=dict(case=group['case'],comparison_L=group['comparison_L'],T_ps=group['target_ps'],
                    method=name,L=m['L'],grammar=m['grammar'],rtl_sha256=m['rtl_sha256'],
                    prediction=m['prediction'],measurement=m['measurement'],
                    status=manifest.get('status','not_started'),failure_reason=manifest.get('failure_reason'))
                actual=checked_readout(run,group['target_ps'],m['measurement']['inherited'])
                if actual:
                    T=actual['full_setup_minimum_period_ps']; area=actual['area_um2']
                    entry.update(status='measured_grt',Tmin_ps=T,area_um2=area,frequency_MHz=1e6/T,
                        setup_met=T<=entry['T_ps'],hold_WNS_ps=actual['hold_WNS_ps'],hold_met=actual['hold_WNS_ps']>=0,
                        measured_threads=manifest['threads_per_tool'],period_error=m['prediction']['critical_required_ps']/T-1,
                        area_error=m['prediction']['total_area_um2']/area-1,clock_readout_sha256=sha(clock))
                elif outcome.get('status')=='failed':
                    entry.update(status='failed',failure_reason=outcome['reason'])
                elif manifest.get('status')=='completed':
                    entry['status']='awaiting_readout_verification'
                rows.append(entry)
    return rows


def publish(root):
    EVIDENCE.mkdir(parents=True,exist_ok=True); rows=collect(root)
    main=[r for r in rows if r['method'] in ('A','B','C','D')]
    state=read(budget.LEDGER); migrated=state['policy_sha256']==sha(runtime.POLICY)
    active=[j for j in state.get('jobs',[]) if j['status'] in ('active','unsettled')]
    progress=read(root/'controller-progress.json') if (root/'controller-progress.json').exists() else {}
    bridge_active=runtime.BRIDGE.exists() and not migrated
    doc=dict(required_main_records=148,main_measured=sum(r['status']=='measured_grt' for r in main),
        required_groups=37,registered_groups=len(main)//4,records=rows,depths=matrix.DEPTHS,
        physical_comparison_complete=len(main)==148 and all(r['status']=='measured_grt' for r in main),
        qualification='diagnostic_only',model_refitted=False,application_PPA_for_selection=False,
        resource_policy_migrated=migrated,resource_bridge_active=bridge_active,parallel_jobs=9,threads_per_tool=2,
        active_physical_jobs=active,ledger_usage=budget.usage(state['entries']),
        controller_progress=progress,source_sha256=sha(SOURCE))
    write(root/'comparison.json',doc); write(EVIDENCE/'comparison.json',doc)
    lines=['# 九案例、每例两种流水级数的 ABCD 比较','',
        f'已登记 {doc["registered_groups"]}/37 组，主方法实测 {doc["main_measured"]}/148。新任务最多9并行，每任务2线程；已完成旧测量保留实际线程数。','',
        '| 案例 | 两档L | 各档目标周期 ps |','| --- | --- | --- |']
    targets=read(root/'target-matrix.json')['rows']
    for cid,depths in matrix.DEPTHS.items():
        values=[]
        for L in depths:
            target=next(t for t in targets if t['case']==cid and t['L']==L)
            values.append(f'L{L}: '+('/'.join(map(str,target['targets_ps'])) if 'targets_ps' in target else '待A参考实测'))
        lines.append('| '+' | '.join([cid,' / '.join(map(str,depths)),'；'.join(values)])+' |')
    lines += ['', '| 案例 | 比较L | T ps | 方法 | 块宽/limb | Tmin ps | 面积 µm² | setup | hold ps | 实际线程 | 状态 |',
        '| --- | ---: | ---: | --- | --- | ---: | ---: | --- | ---: | ---: | --- |']
    for r in rows:
        numbers=([f'{r["Tmin_ps"]:.3f}',f'{r["area_um2"]:.3f}',str(r['setup_met']),f'{r["hold_WNS_ps"]:.3f}',str(r['measured_threads'])]
                 if r['status']=='measured_grt' else ['—']*5)
        lines.append('| '+' | '.join(map(str,[r['case'],r['comparison_L'],r['T_ps'],r['method'],
            '/'.join(map(str,r['grammar'])),*numbers,r['status']]))+' |')
    lines += ['', 'A保持L1；B只在原子运算之间放寄存器；C使用静态表；D先分配本体预算，再换算等效训练T并调用冻结共享模型。',
        '每个新L重新生成位置、状态与G，重新仿真，并独立回放预算查询及核对原生所有者。实际算术级分布另存，不将空传递级称为均衡切分。',
        '已完成的4线程结果保留其身份；新任务使用2线程，报告显式标注线程变化，不把资源改变造成的差异全部归因于L。',
        'Dot16新矩阵只列L4/L5，旧L8保留。MAC原L3三档保持，新增L2两档；其余每个L两档，因此共37组、148条主方法及37条同池归因。',
        'Montgomery原参考的超时、8GiB内存失败保留；同RTL/36000ps的16GiB容量后继成功后才冻结L16/L32周期。',
        f'完整运行目录：`{root}`。失败不自动重试，全部费用和永久任务身份沿用同一账本。']
    (root/'comparison.md').write_text('\n'.join(lines)+'\n'); shutil.copyfile(root/'comparison.md',EVIDENCE/'README.md')
    for p in (root/'protocol.json',root/'target-matrix.json',root/'resource-bridge.json',root/'resource-migration.json'):
        if p.exists():
            shutil.copyfile(p,EVIDENCE/p.name)
    for p in (SOURCE,matrix.SOURCE,runtime.SOURCE,runtime.POLICY):
        shutil.copyfile(p,EVIDENCE/p.name)
    return doc


def run(root):
    root=Path(root).resolve(); matrix.initialize(root); runtime.prepare_policy(); (root/'backend').mkdir(exist_ok=True)
    with (root/'controller.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        previous_progress=read(root/'controller-progress.json') if (root/'controller-progress.json').exists() else {}
        external_software={(r['case'],r['L']) for r in previous_progress.get('software_active',[])}
        reconciliation=root/'orphan-software-reconciliation.json'
        if reconciliation.exists():
            external_software.difference_update((r['case'],r['L']) for r in read(reconciliation)['confirmed_not_running'])
        start=root/'controller-start.json'
        if start.exists():
            # The first controller stopped in the report publisher, before
            # any physical admission. Keep its log/start receipt and adopt
            # its still-running, isolated software children by ready receipt.
            if (root/'resource-migration.json').exists() or any((root/'backend').glob('*/admission.json')):
                raise ValueError('physical controller already attempted; no automatic restart')
            if not (root/'controller-report-fix-successor.json').exists():
                start=root/'controller-report-fix-successor.json'
            elif not (root/'controller-readout-fix-successor.json').exists():
                recovery=read(root/'prephysical-readout-recovery.json')
                if (recovery['status']!='ready' or recovery['source_sha256']!=sha(SOURCE) or
                    recovery['runtime_sha256']!=sha(runtime.SOURCE)):
                    raise ValueError('explicit prephysical readout recovery receipt required')
                start=root/'controller-readout-fix-successor.json'
            else:
                recovery=read(root/'prephysical-overlap-recovery.json')
                if (recovery['status']!='ready' or recovery['source_sha256']!=sha(SOURCE) or
                    recovery['runtime_sha256']!=sha(runtime.SOURCE)):
                    raise ValueError('explicit user-authorized active handoff receipt required')
                start=root/'controller-overlap-successor.json'
        frozen(start,dict(pid=os.getpid(),source_sha256=sha(SOURCE),
            started_epoch=time.time(),automatic_retries=0,user_authorization='九例各两档L；9并行每任务2线程'))
        software_children={}; physical_children={}; software_attempted=set(); physical_attempted=set(); registered=set(); cache={}
        progress=dict(status='draining_previous_wave',
            software_pass=list(previous_progress.get('software_pass',[])),
            software_errors=list(previous_progress.get('software_errors',[])),physical_pass=[],physical_errors=[])
        write(root/'controller-progress.json',progress); migrated=False; bridge_active=False; reference_batch=None; last_signature=None
        while True:
            changed=False
            for key in list(external_software):
                log=root/'software-logs'/f'{key[0]}-L{key[1]}.log'
                if matrix.ready_selection(root,*key):
                    external_software.remove(key); software_attempted.add(key); changed=True
                    progress['software_pass'].append(dict(case=key[0],L=key[1],exit_code=0,log=str(log),
                        adopted_from_retained_controller=True))
                elif log.exists() and 'Traceback (most recent call last)' in log.read_text():
                    external_software.remove(key); software_attempted.add(key); changed=True
                    progress['software_errors'].append(dict(case=key[0],L=key[1],log=str(log),
                        adopted_from_retained_controller=True))
            for key,(child,log) in list(software_children.items()):
                code=child.poll()
                if code is None:
                    continue
                del software_children[key]; changed=True
                target=progress['software_errors' if code else 'software_pass']
                target.append(dict(case=key[0],L=key[1],exit_code=code,log=str(log)))
                print('MATRIX_SOFTWARE_DONE '+str(key)+' '+str(code),flush=True)
            for key,(child,log,batch,task) in list(physical_children.items()):
                code=child.poll()
                if code is None:
                    continue
                del physical_children[key]; physical_done(batch,task,code,log); changed=True
                progress['physical_errors' if code else 'physical_pass'].append(dict(
                    batch=str(batch),task=task['id'],exit_code=code,log=str(log)))
                print('MATRIX_PHYSICAL_DONE '+task['id']+' '+str(code),flush=True)
            # Two software workers leave up to 18 hardware threads to the nine
            # EDA leaves on this 20-logical-CPU host.
            for cid in ('mac32','add512','mul128','dot16','horner64','barrett64','karatsuba256','ntt8x64','montgomery256'):
                for L in matrix.DEPTHS[cid]:
                    key=(cid,L)
                    if len(software_children)+len(external_software)>=2 or key in external_software or key in software_attempted or matrix.ready_selection(root,cid,L):
                        continue
                    if not (root/'targets'/f'{cid}-L{L}.json').exists():
                        continue
                    software_attempted.add(key); software_children[key]=launch_software(root,cid,L); changed=True
                    print('MATRIX_SOFTWARE_START '+str(key),flush=True)
            if not migrated and not physical_children and runtime.old_jobs_settled():
                runtime.migrate(root); migrated=True; progress['status']='running_nine_jobs_two_threads'; changed=True
                print('RESOURCE_MIGRATED 9 jobs x 2 threads; full historical ledger retained',flush=True)
            elif not migrated and not bridge_active:
                runtime.activate_bridge(root); bridge_active=True
                progress['status']='running_nine_slots_with_named_predecessor'; changed=True
                print('RESOURCE_BRIDGE active; old Karatsuba occupies one of nine slots; new leaves use two threads',flush=True)
            if migrated or bridge_active:
                if reference_batch is None:
                    reference_batch=reference(root); changed=True
                reference_task=read(reference_batch/'admission.json')['tasks'][0]
                matrix.freeze_montgomery(root,reference_batch/'runs'/reference_task['id'])
                for cid,depths in matrix.DEPTHS.items():
                    for L in depths:
                        if (cid,L) not in registered and matrix.ready_selection(root,cid,L):
                            register_variant(root,cid,L,cache); registered.add((cid,L)); changed=True
                launch_limit=9-runtime.active_predecessors()
                for batch in [reference_batch,*sorted((root/'backend').glob('matrix-*'))]:
                    if len(physical_children)>=launch_limit or available_memory_MiB()<8192:
                        break
                    a=runtime.verify(batch)
                    for task in a['tasks']:
                        if len(physical_children)>=launch_limit or available_memory_MiB()<8192:
                            break
                        key=(a['id'],task['id'])
                        if key in physical_attempted:
                            continue
                        physical_attempted.add(key); child,log=launch_physical(batch,task)
                        physical_children[key]=(child,log,batch,task); changed=True
                        print('MATRIX_PHYSICAL_START '+task['id']+' threads=2',flush=True)
            write(root/'controller-progress.json',dict(progress,
                software_active=[dict(case=c,L=L,pid=child.pid) for (c,L),(child,_) in software_children.items()],
                physical_active=[dict(batch=k[0],task=k[1],pid=v[0].pid) for k,v in physical_children.items()]))
            signature=(len(registered),len(progress['software_pass']),len(progress['software_errors']),
                len(progress['physical_pass']),len(progress['physical_errors']),migrated,bridge_active)
            if changed or signature!=last_signature:
                doc=publish(root); last_signature=signature
                print(f'MATRIX_STATUS {doc["main_measured"]}/148 registered_groups={doc["registered_groups"]} active={len(physical_children)}',flush=True)
            if migrated and len(registered)==18 and not software_children and not external_software and not physical_children:
                progress['status']='complete' if publish(root)['physical_comparison_complete'] else 'settled_with_retained_failures'
                write(root/'controller-progress.json',progress); return publish(root)
            unresolved_software_errors=[r for r in progress['software_errors']
                if not matrix.ready_selection(root,r['case'],r['L'])]
            if migrated and not software_children and not external_software and not physical_children and unresolved_software_errors:
                progress['status']='retained_software_failure'; write(root/'controller-progress.json',progress); return publish(root)
            # An actual reference failure blocks only Montgomery; complete all
            # independent work first, then report the missing two-depth rows.
            if migrated and reference_batch is not None and not software_children and not external_software and not physical_children:
                p=read(reference_batch/'progress.json')
                ready=sum(matrix.ready_selection(root,c,L) is not None for c,ls in matrix.DEPTHS.items() for L in ls)
                if p['errors'] and ready==len(registered):
                    progress['status']='retained_reference_failure'; write(root/'controller-progress.json',progress); return publish(root)
            time.sleep(10)


if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('action',choices=('run','report'))
    p.add_argument('--root',type=Path,default=DEFAULT); args=p.parse_args()
    result=run(args.root) if args.action=='run' else publish(args.root)
    print({k:result[k] for k in ('main_measured','registered_groups','physical_comparison_complete')})
