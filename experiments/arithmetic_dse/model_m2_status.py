"""Read M2 collection status without EDA or recursive filesystem traversal."""
import argparse
from collections import Counter
from datetime import datetime
import fcntl
import json
from pathlib import Path


def mux_status(root,folder):
    def read(path):return json.loads(Path(path).read_text())
    a=read(folder/'admission.json');p=read(folder/'progress.json');driver=False
    if (folder/'advance.lock').exists():
        with (folder/'advance.lock').open('r') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:driver=True
    print(datetime.now().astimezone().isoformat(timespec='seconds'))
    independent=folder.parent/'mux-static-independent-v1';released=(independent/'admission.json').exists();test_progress=None;test_driver=False
    if released:
        test_progress=read(independent/'progress.json')
        if (independent/'advance.lock').exists():
            with (independent/'advance.lock').open('r') as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:test_driver=True
        print('当前：Mux静态上下文独立测试；驱动：'+('运行中' if test_driver else '未运行')+'；状态：'+test_progress['phase'])
        print('训练／验证采集历史：'+p['phase'])
    else:print('当前：Mux训练／验证上下文补充；驱动：'+('运行中' if driver else '未运行')+'；状态：'+p['phase'])
    for split in ('train','validation','test'):
        counts=Counter()
        for t in a['tasks']:
            if t['split']!=split:continue
            directory=independent if released and split=='test' else folder
            path=directory/'runs'/t['id']/'manifest.json';m=read(path) if path.exists() else {}
            status=m.get('status','not_started')
            if status=='completed' and not m.get('mux_collection_version'):status='synth_complete'
            counts[status]+=1
            if status in ('running','synth_complete'):print('任务：',t['id'],'阶段：',m.get('active_stage','preflight'))
        print(f'{split}: 完成 {counts["completed"]}/{sum(counts.values())}；'+str(dict(counts)))
    print('容量先导：',sum(tid in p.get('completed',[]) for tid in a['capacity_pilots']),'/',len(a['capacity_pilots']),
          '；全部成功后继续其余拟合任务。')
    print('其余11类：继承原冻结参数／域及合格独立证据；原F5总体失败保留；仍须12类齐备才发布。')
    print('新独立测试48项：已绑定静态模型的验证／冻结／字节复现放行。' if released else '新独立测试48项：锁定；必须等待Mux验证、参数／裕量冻结和字节复现。')
    fit=next((folder.parent/name/'fit-report.json' for name in ('mux-static-fit-v1','mux-fit-v2','mux-fit-v1') if (folder.parent/name/'fit-report.json').exists()),None)
    report=read(fit) if fit else None
    if report:
        print('当前拟合检查点：',fit.parent.name)
        for stage,value in report['stages'].items():
            delay=value['mux']['delay']['quality'];area=value['mux']['area']['quality']
            print('Mux验证：',stage,'通过' if value['mux_validation_ready'] else '未通过',
                '时延中位/P95',f'{delay["median_relative_error"]:.2%}/{delay["p95_relative_error"]:.2%}',
                '错误可行',f'{delay["false_feasible"]}/{delay["denominator"]}',
                '面积中位/P95',f'{area["median_relative_error"]:.2%}/{area["p95_relative_error"]:.2%}')
    ledger=read(root/'experiments/arithmetic/backend_usage.json');pending=[e for e in ledger['entries'] if e['status']=='reserved']
    for e in pending:print('当前命令：',e.get('task_id','support'),e['stage'] or 'support',Path(e['output']).name)
    print('未结算命令：',len(pending),'；最多4任务，每项4线程／8GiB。')
    if released:
        test_admission=read(independent/'admission.json')
        print('P4独立容量：',sum(tid in test_progress.get('completed',[]) for tid in test_admission['capacity_pilots']),'/',len(test_admission['capacity_pilots']))
        result=folder.parent/'mux-static-independent-result-v1/result.json'
        if result.exists():
            r=read(result)
            for stage,v in r['stages'].items():
                delay=v['delay'];area=v['area']
                print('Mux独立质量：',stage,v['status'],'时延中位/P95',f'{delay["median_relative_error"]:.2%}/{delay["p95_relative_error"]:.2%}',
                      '错误可行',f'{delay["false_feasible"]}/{delay["denominator"]}',
                      '面积中位/P95',f'{area["median_relative_error"]:.2%}/{area["p95_relative_error"]:.2%}')
            print('组合资格：',r['combined_passing_operations'],'/',r['combined_required_operations'],'；完整D仍待阶段／状态／区间和原生选择闭环。')
            publication=folder.parent/'mux-static-publication-v1/publication.json'
            if publication.exists():
                published=read(publication)
                print('组件发布：',published['quality_status'],'；模型文件',len(published['published']),
                      '；Mux仅parallel_dynamic_mux、生产单银行及原精确位宽／目标；混合控制／算术上下文未合格。')
                print('无自动后继实验；P4已消费，不能用于后续拟合／验证／算法／裕量选择。')
        elif test_progress['phase']=='test_collection_complete':print('48项独立采集已完成；下一步为完整原始回放与一次性独立评价。')
        elif test_progress['phase']=='stopped_on_error':print('独立队列停止：',test_progress['errors'])
        elif test_driver:print('独立队列按空位推进；先导／映射依赖会暂时降低并发。')
        return
    if p['phase']=='fitting_collection_complete':
        if report and not report['stages']['grt']['mux_validation_ready']:print('采集／回放／拟合复现已完成，Mux原验证门槛未通过；48个独立任务未启动，等待后继建模方案。')
        else:print('120项拟合侧任务已完成；下一步为原始标签回放、Mux拟合与质量验证，独立测试尚未放行。')
    elif p['phase']=='stopped_on_error':print('已停止新派发；失败证据与费用保留：',p['errors'])
    elif driver:print('队列正在自动推进；容量先导、映射依赖及阶段切换会暂时降低并发。')
    else:print('驱动当前未运行，请检查本状态再进行下一步。')


def main():
    root=Path(__file__).resolve().parents[2];ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--folder',type=Path);a=ap.parse_args();folder=a.folder
    mux=root/'build/step7-m2-models-20261105/mux-context-v1'
    if folder is None and (mux/'admission.json').exists():mux_status(root,mux);return
    if folder is None:folder=root/'build/step7-m2-models-20261104/primitives-v6'
    def read(path):return json.loads(Path(path).read_text())
    p=read(folder/'plan.json');driver=False
    test_root=root/'build/step7-m2-models-20261104'
    test_folder=next((test_root/name for name in ('independent-F5-v2','independent-F5-v1','independent-test-v4','independent-test-v3','independent-test-v2','independent-test-v1')
                      if (test_root/name/'admission.json').exists()),test_root/'independent-test-v1')
    test_label='F5' if test_folder.name.startswith('independent-F5-') else 'F4'
    test_released=(test_folder/'admission.json').exists();test_running=False
    if test_released:
        tp=read(test_folder/'progress.json')
        if (test_folder/'advance.lock').exists():
            with (test_folder/'advance.lock').open('r') as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:test_running=True
        print('当前后继：'+test_label+'独立测试；状态：'+tp['phase']+'；驱动：'+('运行中' if test_running else '未运行'))
    if (folder/'advance.lock').exists():
        with (folder/'advance.lock').open('r') as lock:
            try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:driver=True
    progress=read(folder/'progress.json') if (folder/'progress.json').exists() else {'phase':'not_started'}
    print(datetime.now().astimezone().isoformat(timespec='seconds'));print(('历史v6采集驱动：' if test_released else '驱动：')+('运行中' if driver else '未运行')+'；状态：'+progress['phase'])
    registry=root/'build/step7-m2-models-20261104/supplemental-resumes.json'
    counts={s:Counter() for s in ('train','validation','test')};active=[];task_status={}
    for t in p['tasks']:
        d=Path(t['inherited_run']['directory']) if t.get('inherited_run') else folder/'runs'/t['id'];mp=d/'manifest.json'
        try:
            m=read(mp) if mp.exists() else {};status=m.get('status','starting' if d.exists() else 'not_started')
        except (OSError,json.JSONDecodeError):m={};status='updating'
        counts[t['split']][status]+=1
        task_status[t['id']]=status
        if status in ('running','starting','updating'):active.append((t['id'],m.get('active_stage','preflight')))
    if registry.exists():print('以下为原采集记录；独立续作及移交任务的状态在下方单列。')
    for split,c in counts.items():print(f'{split}: 完成 {c["completed"]}/{sum(c.values())}；'+str(dict(c)))
    wave_path=Path(progress['wave']) if progress.get('wave') else None
    if wave_path and wave_path.is_file():
        wave=read(wave_path);wave_counts=Counter(task_status.get(tid,'unknown') for tid in wave['task_ids'])
        mode=wave['mode'];later=counts.get(mode,Counter())['not_started']-wave_counts['not_started']
        label='原采集批次（保留原尝试记录）' if registry.exists() else '当前批次'
        print(f'{label}：{wave_path.name}，完成 {wave_counts["completed"]}/{len(wave["task_ids"])}；'+str(dict(wave_counts)))
        if mode=='fitting':
            print('原批次的失败及未启动记录保留；独立续作与补充派发见下方。' if registry.exists() else '训练／验证在同一滚动队列中按空位补位；独立test不在本队列。')
        if driver and progress['phase']=='collecting' and later>0:
            print(f'本阶段另有 {later} 个未启动任务在后续批次；本批全部成功后再准入下一批，批内按空位滚动派发。')
    for tid,stage in active:print('任务：',tid,'阶段：',stage)
    recovery=root/'build/step7-m2-models-20261104/cec-recovery-v1'
    recovery_running=False
    if (recovery/'admission.json').exists():
        a=read(recovery/'admission.json');state=read(recovery/'progress.json') if (recovery/'progress.json').exists() else {'phase':'not_started'}
        if (recovery/'advance.lock').exists():
            with (recovery/'advance.lock').open('r') as lock:
                try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                except BlockingIOError:recovery_running=True
        print('结构化证明后继：',recovery.name,'运行中' if recovery_running else '未运行','；状态：',state['phase'])
        effective={s:c.copy() for s,c in counts.items()}
        for item in a['tasks']:
            t=item['task'];mp=recovery/'runs'/t['id']/'manifest.json';m=read(mp) if mp.exists() else {}
            status=m.get('status','not_started');print('检查点续作：',t['id'],status,m.get('active_stage','preflight'),m.get('failure_reason',''))
            effective[t['split']][task_status[t['id']]]-=1;effective[t['split']][status]+=1
        print('以下为合并成功续作后的采集视图；原失败记录保留，拟合前仍须原始证据回放。')
        for split,c in effective.items():
            if split=='test' and test_released:continue
            print(f'{split}: 完成 {c["completed"]}/{sum(c.values())}；'+str({k:v for k,v in c.items() if v}))
        fit=test_root/('primitive-fit-v4' if test_label=='F5' else 'primitive-fit-v2')/'fit-report.json'
        if fit.exists():
            report=read(fit)
            for stage,value in report['stages'].items():print('模型验证：',stage,f'{value["passing_operations"]}/{value["operation_count"]}','通过' if value['validation_ready'] else '未全通过')
    supplemental_running=False
    if registry.exists():
        for location in read(registry)['folders']:
            extra=Path(location);extra_driver=False
            if (extra/'advance.lock').exists():
                with (extra/'advance.lock').open('r') as lock:
                    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                    except BlockingIOError:extra_driver=True
            state=read(extra/'progress.json') if (extra/'progress.json').exists() else {'phase':'not_started'}
            print('历史补充驱动：',extra.name,'运行中' if extra_driver else '未运行','；状态：',state['phase'])
            supplemental_running=supplemental_running or extra_driver
            if (extra/'run/manifest.json').exists():
                resumed=read(extra/'run/manifest.json')
                print('独立续作：',resumed['task_id'],'状态：',resumed['status'],'阶段：',resumed.get('active_stage'),
                      '；原采集中的超时记录保留，成功后由后继验收纳入。')
            if state.get('waiting'):print('补充队列等待：',len(state['waiting']),'项；与其他驱动共用4个完整任务名额。')
    if test_released:
        a=read(test_folder/'admission.json');c=Counter()
        for t in a['tasks']:
            run=Path(t['inherited_run']['directory']) if t.get('inherited_run') else test_folder/'runs'/t['id']
            mp=run/'manifest.json';m=read(mp) if mp.exists() else {};status=m.get('status','not_started')
            # The generic synth-only precursor writes completed before this
            # successor starts grt; that intermediate status is not a full test.
            if status=='completed' and not m.get('test_collection_version'):status='synth_complete'
            c[status]+=1
            if status in ('running','synth_complete'):print('独立测试任务：',t['id'],m.get('active_stage','preflight'))
        print(f'独立test: 完成 {c["completed"]}/56；'+str(dict(c)))
        verdict=test_root/('primitive-F5-independent-v1' if test_label=='F5' else 'primitive-independent-v1')/'result.json'
        if verdict.exists():print('冻结'+test_label+'队列的一次性独立评价已完成；结果见下方，采集完成不等于质量通过。')
        else:print('独立测试只采集冻结'+test_label+'队列；结束后仍须一次性质量评价与发布核验。')
        if a.get('capacity_pilots'):
            print('本轮容量先导：',sum(tid in tp.get('completed',[]) for tid in a['capacity_pilots']),'/',len(a['capacity_pilots']),'；全部成功才继续其他任务。')
        result=test_root/'primitive-independent-v1/result.json'
        if result.exists():
            r=read(result)
            for stage,value in r['stages'].items():print('历史F4独立质量：',stage,f'{value["passing_operations"]}/{value["operation_count"]}',value['status'])
            publication=test_root/'primitive-publication-v1/publication.json'
            if publication.exists():print('历史F4基础算子发布：',len(read(publication)['published']),'；完整D仍须区间／组合／状态与原生接入。')
        if test_label=='F5':
            result=test_root/'primitive-F5-independent-v1/result.json'
            if result.exists():
                r=read(result)
                for stage,value in r['stages'].items():
                    print('当前F5独立质量：',stage,f'{value["passing_operations"]}/{value["operation_count"]}',value['status'])
                    for op,detail in value['operations'].items():
                        if detail['status']!='passed':print('未通过：',op,'时延中位/P95',
                            f'{detail["delay"]["median_relative_error"]:.2%}/{detail["delay"]["p95_relative_error"]:.2%}',
                            '错误可行',f'{detail["delay"]["false_feasible"]}/{detail["delay"]["denominator"]}')
                publication=test_root/'primitive-F5-publication-v1/publication.json'
                if publication.exists():print('当前F5基础算子发布：',len(read(publication)['published']),'；冻结选择和测试结论保持，未修改门槛。')
    u=read(root/'experiments/arithmetic/backend_usage.json');pending=[e for e in u['entries'] if e['status']=='reserved']
    for e in pending:print('当前命令：',e.get('task_id','support'),e['stage'] or 'support',Path(e['output']).name)
    print('未结算命令：',len(pending),'；最多4任务，每任务4线程；'+('独立测试已按冻结选择放行' if test_released else '独立测试暂不启动'))
    if progress['phase']=='fitting_collection_complete':print('训练／验证采集完成，可以请助手继续提取、拟合和质量核验。')
    elif progress['phase'] in ('stopped_on_error','paused'):
        if test_released:print('当前请看上方'+test_label+'独立测试状态；原v6及F3补充超时记录保留。')
        else:print('原采集驱动已停止；后继续作仍在运行。' if supplemental_running or recovery_running else '原采集已停止；请结合后继恢复和模型验证状态查看。',progress.get('error',''))
    elif not driver:print('驱动未运行，尚不能视为完成，请联系助手检查。')
    else:print('仍在自动推进；批次收尾等待、映射依赖、阶段切换或容量核验会使并发数暂时降低。')


if __name__=='__main__':main()
