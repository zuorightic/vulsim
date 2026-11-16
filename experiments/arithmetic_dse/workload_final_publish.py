"""Reviewable evidence snapshots for the staged nine-case experiment."""
import argparse
import base64
import gzip
import hashlib
from pathlib import Path
import shutil

from .sampling_time_contract import ROOT,canonical
from .workload_abcd import read,write,sha
from .workload_final_driver import DEFAULT
from .workload_final_selection import BASE
from .workload_steps45_package import chunk
from .budget import Ledger,usage

EVIDENCE=ROOT/'experiments/arithmetic/evidence/workload_equivalent_steps678_v1'


def refresh(root=DEFAULT,out=EVIDENCE):
    root=Path(root);out=Path(out);out.mkdir(parents=True,exist_ok=True)
    tight=read(root/'software/protocol.json').get('clock_basis')=='unsplit_A'
    for freeze in root.glob('*-selection-freeze.json'):
        for name,h in read(freeze)['files'].items():
            if sha(name)!=h:raise ValueError('complete selection changed after freeze: '+name)
        shutil.copyfile(freeze,out/freeze.name)
    transfer_folder=root/'fourth-worker-transfers'
    transfers=[read(p) for p in sorted(transfer_folder.glob('*.json'))]
    if transfers:
        dest=out/'fourth-worker-transfers';dest.mkdir(exist_ok=True)
        for p in transfer_folder.glob('*.json'):shutil.copyfile(p,dest/p.name)
    batches={};clocks=[];readouts=[];verification=[];failed_runs=[]
    for folder in sorted(root.iterdir()):
        if not folder.is_dir() or not (folder/'admission.json').exists():continue
        a=read(folder/'admission.json');p=read(folder/'progress.json')
        duplicates=0
        for error in p['errors']:
            transferred=next((r for r in transfers if Path(r['batch'])==folder and
                r['task_id']==error['task'] and r['status']=='measured_grt'),None)
            log=folder/'dispatch-logs'/(error['task']+'.log')
            if transferred and log.exists() and 'backend task already claimed; no automatic retry' in log.read_text():duplicates+=1
        batches[folder.name]=dict(role=a['role'],tasks=len(a['tasks']),progress=p,admission_sha256=sha(folder/'admission.json'),
            duplicate_dispatch_rejections=duplicates,other_execution_failures=len(p['errors'])-duplicates)
        for task in a['tasks']:
            run=folder/'runs'/task['id'];manifest=run/'manifest.json'
            clock=folder/'runs'/task['id']/'clock-readout/result.json'
            if a['role']=='clock_calibration' and clock.exists():clocks.append(dict(case=task['case'],probe_T_ps=task['period_ps'],result=read(clock),readout_sha256=sha(clock)))
            if clock.exists():
                manifest=folder/'runs'/task['id']/'manifest.json';m=read(manifest)
                readouts.append(dict(batch=folder.name,task=task['id'],role=a['role'],period_ps=task['period_ps'],
                    result=read(clock),clock_readout_sha256=sha(clock),manifest_sha256=sha(manifest),
                    metrics=m['metrics'],commands=[{k:v for k,v in c.items() if k!='command'} for c in m['commands']]))
            elif manifest.exists() and read(manifest).get('status')!='running':
                m=read(manifest)
                failed_runs.append(dict(batch=folder.name,task=task['id'],status=m['status'],
                    failure_reason=m.get('failure_reason'),failure_stage=m.get('failure_stage'),
                    manifest_sha256=sha(manifest),commands=[{k:v for k,v in c.items() if k!='command'} for c in m['commands']]))
            receipt=run/'verification-receipt.json'
            if receipt.exists():
                r=read(receipt);proof=Path(r['proof'])
                verification.append(dict(batch=folder.name,task=task['id'],receipt=r,proof=read(proof)))
        # Portable physical instructions and exact functional input hashes.
        dest=out/'physical-batches'/folder.name;dest.mkdir(parents=True,exist_ok=True)
        for n in ('admission.json','freeze.json','progress.json'):shutil.copyfile(folder/n,dest/n)
        if (folder/'storage-index.json').exists():shutil.copyfile(folder/'storage-index.json',dest/'storage-index.json')
        if (folder/'dispatch-extension.json').exists():
            shutil.copyfile(folder/'dispatch-extension.json',dest/'dispatch-extension.json')
    write(out/'physical-failures.json',failed_runs)
    write(out/'repair-verification.json',verification)
    diagnostics={}
    if (root/'continuation-start.json').exists():
        folders=sorted(list(root.parent.glob('montgomery-cts-LEC-diagnostic-v*'))+
                       list(root.parent.glob('montgomery-cts-buffer-proof-v*')))
        for folder in folders:
            admission=folder/'admission.json'
            if not admission.exists():continue
            a=read(admission);identity=a.get('id') or a.get('admission_id')
            if not identity:raise ValueError('diagnostic admission identity absent')
            diagnostics[identity]=dict(directory=str(folder),admission_sha256=sha(admission),
                result=read(folder/'result.json') if (folder/'result.json').exists() else None)
            dest=out/'verification-diagnostics'/folder.name;dest.mkdir(parents=True,exist_ok=True)
            for source in folder.iterdir():
                if source.is_file() and source.suffix in ('.json','.py','.txt','.log'):
                    shutil.copyfile(source,dest/source.name)
            controller=folder.parent/(folder.name+'-controller.log')
            if controller.exists():shutil.copyfile(controller,dest/'controller.log')
        write(out/'verification-diagnostics.json',diagnostics)
    selected={}
    for p in (root/'software').glob('*/final-selections.json'):
        x=read(p);selected[p.parent.name]=dict(targets=x['targets_ps'],records=len(x['records']),
            candidates=sum(r['candidates'] for r in x['search']),complete=sum(r['complete'] for r in x['search']))
    parallel={}
    for folder in sorted((root/'parallel-software').glob('*')):
        receipts={p.name:read(p) for p in folder.glob('parallel-*.json')}
        if not receipts:continue
        parallel[folder.name]=receipts
        dest=out/'parallel-software'/folder.name;dest.mkdir(parents=True,exist_ok=True)
        for name in receipts:shutil.copyfile(folder/name,dest/name)
    comparison=read(root/'comparison.json') if (root/'comparison.json').exists() else None
    complete=bool(comparison and comparison['physical_comparison_complete'])
    state=dict(version='steps678-nine-case-status-v1',physical_comparison_complete=complete,model_precision_qualified=False,
        superseded_by_A_over_L_rule=not tight,
        main_measured=comparison['main_measured'] if comparison else 0,required_main_records=76,
        batches=batches,verification_diagnostics=diagnostics,selected=selected,parallel_software=parallel,working_root=str(root),ledger=Ledger().summary(),
        model_response_refitted=False,independent_operator_sources_unlocked=False,application_PPA_for_selection=False)
    write(out/'status.json',state);write(out/'clock-calibration.json',clocks)
    (out/'physical-readouts.json.gz').write_bytes(gzip.compress(canonical(readouts),mtime=0))
    ledger=read(Ledger().path);ids=set(batches)|set(diagnostics)
    entries=[e for e in ledger['entries'] if e.get('admission_id') in ids]
    (out/'backend-ledger-entries.json.gz').write_bytes(gzip.compress(canonical(entries),mtime=0))
    phase_usage={role:usage([e for e in entries if e['admission_id'] in batches and batches[e['admission_id']]['role']==role])
                 for role in ('clock_calibration','final_evaluation')}
    phase_usage['verification_diagnostics']=usage([e for e in entries if e['admission_id'] in diagnostics])
    first=next((i for i,e in enumerate(ledger['entries']) if e.get('admission_id') in ids),len(ledger['entries']))
    write(out/'backend-usage.json',dict(starting_usage=usage(ledger['entries'][:first]),
        new_batches=usage(entries),by_role=phase_usage,cumulative=state['ledger'],
        other_overlapping_usage=usage([e for e in ledger['entries'][first:] if e.get('admission_id') not in ids]),
        pending_entries_reserve_upper_bounds=True,history_reset=False))
    for src,name in [(root/'software/protocol.json','software-protocol.json'),
                     (root/'software/characterization-contract.json','characterization-contract.json'),
                     (root/'software/preselection-shell-coverage.json','shell-coverage.json'),
                     (root/'software/native-ABC-owner-audit.json','native-ABC-owner-audit.json'),
                     (root/'software/all-selected-owner-audit.json','all-selected-owner-audit.json'),
                     (root/'software/selected-replay.json','selected-replay.json'),
                     (root/'continuation-validation.json','continuation-validation.json'),
                     (root/'near-target-repeat-plan.json','near-target-repeat-plan.json'),
                     (root/'near-target-repeat-results.json','near-target-repeat-results.json'),
                     (root/'concurrency-amendment.json','concurrency-amendment.json'),
                     (root/'concurrency-resource-readout.json','concurrency-resource-readout.json'),
                     (root/'fourth-worker-reconciliation.json','fourth-worker-reconciliation.json'),
                     (root/'target-matrix.json','target-matrix.json')]:
        if src.exists():shutil.copyfile(src,out/name)
    if comparison:
        for n in ('comparison.json','comparison.md'):shutil.copyfile(root/n,out/n)
        from .workload_final_tables import tables
        tables(root,out)
    from .workload_final_tables import software_tables
    software_tables(root,out)
    text=['# 第6～8步：九例等效预算版本 ABCD', '',
        f"当前完成统一 grt 实测的主方法记录为 **{state['main_measured']}/76**。本轮{'已完成物理比较' if complete else '正在执行物理比较' if tight else '已被A/L紧凑目标版本替代，不再启动新比较'}；共享模型仍为诊断身份，完整精度资格没有通过。",'',
        '本轮响应参数沿用第1～5步冻结版本。Sub／Compare采用既有train源均衡池化的公共采样H代理，功能消费者绑定实际Boolean-cover节点；原四类边界及响应不变。先按候选路径联合分配本体预算，再反解等效训练T并调用原函数，S／shared／控制及实际ABC保留整机T。超过原6000ps反解区间的请求显式扩展至有限100000ps区间，均属未取得精度资格的外推。','',
        '新增全局依赖路径均衡位置由原生接口验证并物化。静态C仍按原统一表选择；MAC32保留第5步175个完整候选的原数值，其他案例保留每结构的静态路径／状态代表，再增加有限静态／模型压力位置。共同池静态价格归因与正式C分别列出。', '',
        ('用户已确认新目标规则：其余八例以未拆分、L1的A的完整grt RR／IR／RO Tmin为参考；A映射请求按其冻结模型软件周期的1.10倍向上取整至100ps、至少1000ps，统一在测量前登记，分别取1.25×／1.5×[Tmin(A)/L]，向上取整到50ps；取整重合时第二档加50ps。MAC维持500／750／1000ps、L3。参考A只确定目标，不证明所有映射中的最快A，最终A也在各比较T下另测；不再以C或最终D的结果放宽目标。' if tight else
        '旧测时规则：每个非MAC案例冻结静态C探针，按其完整RR／IR／RO阈值T_ref取1.05／1.45倍并向上取整到100ps。此规则已被用户确认的A/L规则替代，仅保留历史身份和开销。'), '',
        '| 批次 | 数据角色 | 任务数 | 原调度完成 | 执行失败 | 重复调度拒绝 | 活动／排队 |','| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for name,b in batches.items():
        p=b['progress'];text.append(f"| {name} | {b['role']} | {b['tasks']} | {len(p['completed'])} | {b['other_execution_failures']} | {b['duplicate_dispatch_rejections']} | {len(p['active'])} |")
    four=(root/'concurrency-amendment.json').exists()
    if four:
        text+=['','按用户追加授权，当前全局物理调度为4任务并行、每工具4线程、8GiB。原三工作进程及冻结测量源码保留，第4个独立进程领取已登记队列中的任务，共用全局四槽及永久任务身份锁。原调度器后来遇到已由第4进程完成的身份会被账本拒绝，拒绝原文和交接收据保留；表中单列为重复调度拒绝，实际完整测量仍按同一任务计一次。共享模型、RTL、T和物理变换不因并发调整变化。见`concurrency-amendment.json`及`fourth-worker-transfers/`。']
    if parallel:
        text+=['','后续独立案例的软件评分可在隔离目录提前执行，继续调用原冻结选择器、同一候选规则及目标；完成后才导入主目录，已开始的串行案例拒绝导入。输入／完成／导入收据位于`parallel-software/`；附加Add512隔离重算仅验证数值一致性，不启动EDA。']
    if any((root/name/'dispatch-extension.json').exists() and read(root/name/'dispatch-extension.json')['verification_override'] for name in batches):
        text+=['','Montgomery256参考A的原grt在CTS修复网表的Kepler等价性检查中超时，原失败、命令和费用保留。另立有限后继，原RTL、参考T、映射和物理变换保持；仅验证调用使用保守充分条件：消去Liberty明确为恒等的缓冲后，逐一核对非缓冲实例逻辑／状态签名、全部输入来源及顶层输出。任何不支持的变化或300秒超时均使原CTS调用失败，不跳过检查、不自动回退。新批次绑定验证器／证明器源码，实际ORFS调用收据见`repair-verification.json`；该方法不是通用SAT证明器。原失败摘要见`physical-failures.json`。']
    text+=['','| 案例 | 探针请求 ps | 完整 Tmin ps | 面积 µm² | hold WNS ps |','| --- | ---: | ---: | ---: | ---: |']
    for c in clocks:
        r=c['result'];text.append(f"| {c['case']} | {c['probe_T_ps']} | {r['full_setup_minimum_period_ps']:.2f} | {r['area_um2']:.2f} | {r['hold_WNS_ps']:.3f} |")
    if tight:
        targets=[read(p) for p in sorted((root/'targets').glob('*.json'))]
        write(out/'frozen-targets-so-far.json',targets)
        text+=['','| 案例 | 未拆分A参考 Tmin ps | L | 已冻结目标 ps |',
            '| --- | ---: | ---: | --- |']
        for t in targets:
            a=f"{t['A_reference_Tmin_ps']:.2f}" if 'A_reference_Tmin_ps' in t else '原确认目标'
            text.append(f"| {t['case']} | {a} | {t['L']} | {' / '.join(map(str,t['targets_ps']))} |")
    text+=['','物理口径为 ASAP7 RVT TT / TC25C0.7V、NLDM、post-CTS grt估计RC；标准单元面积排除filler并包含taps，I/O max=0.2T。完整setup阈值有±0.1ps括号检查；hold与约束覆盖另报，不把grt写成final或多角签核。','',
        f"同RTL／T／工艺／约束身份共享物理任务。每批全新冻结、自动重试0，共享账本保留所有历史开销。每工具4线程、8GiB、全局并发{4 if four else 3}；大型任务综合／grt上限3600／7200秒。物理失败不会补成数值，也不会改选D。",'',
        f"完整工作目录：`{root}`。其中`software/selected/`含逐目标RTL、state、owners、预算／等效T／实际Query、192周期整数／reset／停顿仿真收据；`software/*/scores-T*/`保留候选完整轨迹；各物理批次的`runs/`保留工具命令、环境、固定数据库、原始报告及readout。原停止队列未续跑。",'',
        '复现与核对命令：','', '```bash',
        'VULSIM_WORKLOAD_V10_BINARY=build/workload-v10-20261115/rtlzz-workload python3 -m unittest regression.test_workload_guided_search regression.test_workload_equivalent regression.test_workload_diagnostic regression.test_workload_v10 regression.test_workload_abcd regression.test_workload_final',
        f'python3 -m experiments.arithmetic_dse.workload_final_replay --root {root}/software',
        f"python3 -m experiments.arithmetic_dse.{'workload_tight_continue' if (root/'continuation-start.json').exists() else 'workload_tight_run' if tight else 'workload_final_driver'} report --root {root}",
        f'python3 -m experiments.arithmetic_dse.workload_final_publish --root {root} --evidence {out}',
        '```','',
        '软件验证收据见validation.json。原静态池9例659候选、167567次所有者观察的消费者绑定审计无缺失，27份A／B／C通过原生所有者、整数语义、G和参数绑定检查；新扩展候选仍需原生验证并对最终RTL重新仿真。软件覆盖不授予边界或响应精度资格。','',
        '原§1.8的Add／Mux／G／S失败以及第4步S、shared、嵌入外壳缺口保留。软件正确、模型精度、目标满足和D相对C的收益分别评价；目标未满足或D不优于C均如实报告。']
    if (out/'continuation-validation.json').exists():
        v=read(out/'continuation-validation.json')
        text+=['',f"调度后继及验证适配器的相关回归为{v['tests']}项，全部通过，含错误时钟／函数／复位、未完成A／缺少证明收据及归档损坏等拒绝检查；见`continuation-validation.json`。"]
    if (out/'near-target-repeat-plan.json').exists():
        text+=['','另预登记MAC32的750／1000ps两份D各一次冷启动重复，用于检查接近目标的setup／hold分类是否稳定；不改选、不替换主表、不据此估计通用噪声界。计划见`near-target-repeat-plan.json`；只有存在`near-target-repeat-results.json`时才表示两项复核已执行。']
    archived=[name for name in batches if (root/name/'storage-index.json').exists()]
    if archived:
        text+=['','为保留后续大案例空间，仅对已结清批次的中间ODB做可逆gzip归档。原始字节、路径、大小和SHA256及压缩文件SHA256记在各批次`storage-index.json`，先逐字节回解校验再移除原ODB；RTL、网表、readout和报告仍可直接读取。恢复命令：', '',
            '```bash',f'python3 -m experiments.arithmetic_dse.workload_storage restore --batch {root}/<batch>','```']
    (out/'README.md').write_text('\n'.join(text)+'\n')
    sources={str(p.relative_to(ROOT)):p.read_text() for p in sorted((ROOT/'experiments/arithmetic_dse').glob('*.py'))}
    for name in ('test_workload_final.py','test_workload_buffer_equivalence.py','test_workload_tight_continue.py','test_workload_storage.py'):
        sources['regression/'+name]=(ROOT/'regression'/name).read_text()
    (out/'software-source.json.gz').write_bytes(gzip.compress(canonical(sources),mtime=0))
    if complete:
        files={str(p.relative_to(root/'software')):base64.b64encode(p.read_bytes()).decode()
            for p in (root/'software/selected').rglob('*') if p.is_file()}
        chunk(out,'selected-artifacts',gzip.compress(canonical(dict(version='nine-case-selected-artifacts-v1',files=files)),mtime=0))
    return state


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=DEFAULT);p.add_argument('--evidence',type=Path,default=EVIDENCE)
    a=p.parse_args();print(refresh(a.root,a.evidence))
