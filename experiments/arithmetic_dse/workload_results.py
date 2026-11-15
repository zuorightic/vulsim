"""Read frozen workload comparisons; never price, select, or invoke EDA.

The report preserves failed measurements and separates setup feasibility from
hold. A fixed implementation's full interface clock limit comes exclusively
from the bracketed RR/IR/RO readout, not from T-WNS or period_min.
"""
import argparse
import csv
import io
import math
from pathlib import Path

from .workload_abcd import read, write, sha

VERSION = 'nine-workload-diagnostic-results-v1'


def physical_result(root, task, errors, directory=None, clock_path=None):
    directory = directory or root/'runs'/task['id']
    manifest = directory/'manifest.json'
    clock = root/'clock-readout'/task['id']/'result.json'
    corrected_clock = root/'clock-readout-v2'/task['id']/'result.json'
    if corrected_clock.exists(): clock = corrected_clock
    if clock_path is not None: clock=clock_path
    result = dict(task=task['id'], status='not_attempted', target_met=None,
                  full_setup_minimum_period_ps=None, maximum_frequency_MHz=None)
    if not manifest.exists():
        if task['id'] in errors:
            result.update(status='failed_before_manifest', failure_reason=errors[task['id']])
        return result
    m = read(manifest)
    if (directory/'input.sv').exists() and sha(directory/'input.sv') != task['rtl_sha256']:
        raise ValueError('measured RTL differs from frozen selected implementation')
    result.update(status=m['status'], manifest=str(manifest), manifest_sha256=sha(manifest),
                  failure_reason=m.get('failure_reason') or errors.get(task['id']),
                  failure_stage=m.get('failure_stage',m.get('active_stage')) if m['status'] != 'completed' else None,
                  metrics=m.get('metrics', []))
    commands=m.get('commands',[])
    peaks=[c['sampled_process_tree_peak_rss_KiB'] for c in commands if 'sampled_process_tree_peak_rss_KiB' in c]
    result.update(memory_limit_MiB=m.get('memory_limit_MiB'),
                  sampled_process_tree_peak_rss_MiB=max(peaks)/1024 if peaks else None,
                  attempt_leaf_walltime_s=sum(c['walltime_s'] for c in commands) if commands else None)
    grt = next((x for x in m.get('metrics', []) if x['stage'] == 'grt'), None)
    if grt:
        for key in ('cell_area_um2', 'functional_cell_area_um2', 'sequential_area_um2',
                    'sequential_cells', 'physical_only_area_um2', 'setup_worst_slack_ps',
                    'hold_worst_slack_ps', 'setup_tns_ps', 'hold_tns_ps',
                    'timing_coverage_complete', 'hold_feasible_at_TT', 'hold_review_required'):
            result[key] = grt[key]
        result['combinational_functional_area_um2'] = grt['functional_cell_area_um2']-grt['sequential_area_um2']
    if clock.exists():
        c = read(clock)
        if c['task'] != task['id'] or c['target_ps'] != task['period_ps'] or not grt:
            raise ValueError('clock readout does not belong to this measured implementation')
        if m.get('evidence_sha256'):
            for name,digest in c['fixed_inputs'].items():
                relative = str(Path(name).relative_to(directory))
                if m['evidence_sha256'].get(relative) != digest:
                    raise ValueError('clock readout is not bound to measured grt checkpoints')
        classes = c['classes']
        for name in ('register_to_register','input_to_register','register_to_output'):
            coefficient = 1 if name == 'register_to_register' else .8
            expected = task['period_ps']-classes[name]['slack_ps']/coefficient
            if abs(expected-classes[name]['required_period_ps']) > 1e-5:
                raise ValueError('full interface clock equation changed')
        threshold = max(classes[n]['required_period_ps'] for n in
                        ('register_to_register','input_to_register','register_to_output'))
        if (abs(threshold-c['full_setup_minimum_period_ps']) > 1e-5
                or classes['threshold_check_-0.1']['slack_ps'] >= 0
                or classes['threshold_check_0.1']['slack_ps'] < 0
                or not math.isclose(c['maximum_frequency_MHz'],1e6/threshold,rel_tol=1e-10)
                or abs(classes['full_setup_threshold']['slack_ps']-grt['setup_worst_slack_ps']) > .005):
            raise ValueError('missing or inconsistent full interface threshold bracket')
        result.update(status='completed', clock_readout=str(clock), clock_readout_sha256=sha(clock),
                      full_setup_minimum_period_ps=threshold,
                      maximum_frequency_MHz=c['maximum_frequency_MHz'], path_classes=classes,
                      target_met=grt['timing_coverage_complete'] and grt['setup_worst_slack_ps'] >= 0)
        if result.get('failure_reason'):
            result['retained_orchestration_error']=result['failure_reason']
            result['failure_reason']=None
    elif m['status'] == 'completed':
        result['status'] = 'clock_readout_failed' if task['id'] in errors else 'clock_readout_pending'
    return result


def structure(data, original=None):
    directory = Path(data['rtl']).parent
    state = read(directory/'state.json')
    graph_path = directory/'graph.json'
    if not graph_path.exists() and original:
        graph_path = Path(original['folder']).parent/'graph.json'
    graph = read(graph_path)
    slots = state['slots']
    stages = sorted({s['stage'] for s in slots})
    return dict(structure=data['structure'], view=data['view'], graph_nodes=len(graph['nodes']),
                saved_variable_bits=state['features']['state_bits'],
                saved_signals=state['features']['state_signals'],
                state_stage_distribution=[dict(stage=s, words=sum(x['stage']==s for x in slots),
                   variable_bits=sum(x['variable_bits'] for x in slots if x['stage']==s)) for s in stages])


def build(root):
    root = Path(root).resolve()
    methods = read(root/'methods.json'); admission = read(root/'admission.json')
    baselines = {(r['case'],r['target']['T_ps']):r for r in read(root/'baselines.json')['records']}
    if sha(root/'methods.json') != admission['methods_sha256']:
        raise ValueError('comparison method matrix changed')
    progress = read(root/'backend-progress.json')
    waiting=set(progress['active'])
    correction_progress = root/'backend-corrected-progress.json'
    if correction_progress.exists():
        correction=read(correction_progress)
        progress['errors'] += correction['errors'];waiting.update(correction['active'])
    for wave in sorted((root/'waves').glob('*/progress.json')):
        wave_progress=read(wave)
        progress['errors'] += [dict(e,wave=wave.parent.name) for e in wave_progress['errors']]
        waiting.update(wave_progress['active']);waiting.update(wave_progress.get('queued',[]))
    errors = {e['task']:e['reason'] for e in progress['errors']}
    measurements = {t['id']:physical_result(root,t,errors) for t in admission['tasks']}
    for task in waiting:
        if task in measurements and not (root/'runs'/task/'manifest.json').exists():
            measurements[task].update(status='queued',failure_reason=None)
    task_map={t['id']:t for t in admission['tasks']}
    for p in sorted((root/'capacity').glob('*/admission.json'),key=lambda p:read(p)['created_at']):
        cap=read(p);cap_progress=read(p.with_name('progress.json'))
        progress['errors'] += [dict(e,batch=p.parent.name) for e in cap_progress['errors']]
        for t in cap['tasks']:
            if t['id'] not in task_map or t['rtl_sha256']!=task_map[t['id']]['rtl_sha256']:
                raise ValueError('capacity successor changed the selected implementation')
            d=p.parent/'runs'/t['id']
            if not (d/'manifest.json').exists():
                old=measurements[t['id']]
                measurements[t['id']]=dict(task=t['id'],status='successor_pending',target_met=None,
                    full_setup_minimum_period_ps=None,maximum_frequency_MHz=None,
                    previous_attempts=old.get('previous_attempts',[])+[{k:v for k,v in old.items() if k!='previous_attempts'}])
                continue
            newer=physical_result(root,t,{e['task']:e['reason'] for e in cap_progress['errors']},
                                   directory=d,clock_path=d/'clock-readout/result.json')
            old=measurements[t['id']]
            newer['previous_attempts']=old.get('previous_attempts',[])+[
                {k:v for k,v in old.items() if k!='previous_attempts'}]
            newer['capacity_admission_sha256']=sha(p)
            if 'completed_phase' in t:
                newer['checkpoint_resume']={k:t[k] for k in
                    ('completed_phase','checkpoints','source','source_manifest_sha256','successful_CTS_proof')}
            measurements[t['id']]=newer
    ownership = {}
    for t in admission['tasks']:
        for a in t['attribution']:
            key = (a['case'], a['target']['T_ps'], a['method'])
            if key in ownership: raise ValueError('method measured more than once without explicit successor')
            ownership[key] = t['id']
    rows = []; changes = []; attributions = []
    for row in methods['records']:
        group = {}
        for name,data in row['methods'].items():
            task = ownership[(row['case'],row['target']['T_ps'],name)]
            measurement = measurements[task]
            prediction = data.get('prediction')
            r = dict(case=row['case'], T_ps=row['target']['T_ps'], requested_L=row['target']['L'],
                     method=name,L=data['L'],II=data['II'],
                     input_service_additional_cycles=data['input_service_additional_cycles'],
                     rtl_sha256=data['rtl_sha256'],simulation_status=data['simulation_status'],
                     structure=structure(data,baselines[(row['case'],row['target']['T_ps'])].get(name)),
                     prediction=prediction,static_weights=data.get('static'),
                     measurement=measurement)
            if prediction and measurement['status']=='completed':
                r['prediction_error'] = dict(
                    area_signed_fraction=prediction['total_area_um2']/measurement['cell_area_um2']-1,
                    complete_required_signed_fraction=prediction['critical_required_ps']/measurement['full_setup_minimum_period_ps']-1,
                    target_classification_correct=prediction['target_met']==measurement['target_met'])
            rows.append(r);group[name]=r
        def difference(left,right):
            l,r=group[left]['measurement'],group[right]['measurement']
            value=dict(case=row['case'],T_ps=row['target']['T_ps'],left=left,right=right,
                       same_RTL=group[left]['rtl_sha256']==group[right]['rtl_sha256'])
            if l['status']==r['status']=='completed':
                value.update(area_change_fraction=l['cell_area_um2']/r['cell_area_um2']-1,
                             minimum_period_change_fraction=l['full_setup_minimum_period_ps']/r['full_setup_minimum_period_ps']-1,
                             frequency_change_fraction=l['maximum_frequency_MHz']/r['maximum_frequency_MHz']-1)
            else: value['status']='measurement_incomplete'
            return value
        changes.append(difference('D','C'))
        if 'D_static_cal' in group: attributions.append(difference('D','D_static_cal'))
    complete=sum(m['status']=='completed' for m in measurements.values())
    terminal={'completed','failed','failed_before_manifest','clock_readout_failed'}
    settled=sum(m['status'] in terminal for m in measurements.values())
    failed=sum(m['status'] in terminal-{'completed'} for m in measurements.values())
    from .budget import Ledger,usage
    ledger=Ledger();state=read(ledger.path)
    entries=[e for e in state['entries'] if e.get('admission_id','').startswith(admission['id'])]
    cost=dict(usage(entries),failed_leaves=sum(e['status']=='failed' for e in entries),
              admissions=sorted({e['admission_id'] for e in entries}),
              entries=entries,
              scope='all comparison leaves, retained failures, capacity successors and proof support; no outer-wrapper double charge')
    bases=[('pending_reservation' if e['status']=='reserved' else e.get('CPU_accounting','unclassified')) for e in entries]
    cost['CPU_accounting_by_basis']={basis:bases.count(basis) for basis in sorted(set(bases))}
    cost['CPU_missing_evidence_leaves']=bases.count('full_reservation_missing_CPU_evidence')
    cost['CPU_time_scope']='Ledger charge: GNU time when complete; full reserved allowance if CPU evidence is missing; pending leaves retain their allowance.'
    return dict(version=VERSION,qualification=methods['qualification'],model_sha256=methods['model_sha256'],
                selection_freeze_sha256=sha(root/'selection-freeze.json'),
                application_PPA_feedback=False,candidate_PPA_calls=0,
                cases=len({r['case'] for r in rows}),targets=len(methods['records']),method_records=len(rows),
                physical_tasks=len(measurements),completed_physical_tasks=complete,
                settled_physical_tasks=settled,failed_physical_tasks=failed,
                status=('completed' if complete==len(measurements) else
                        'settled_with_failures' if settled==len(measurements) else 'incomplete'),
                setup_scope='ASAP7 TT grt estimated RC; full RR/IR/RO interface, IOmax=0.2T; hold separate',
                prediction_scope='diagnostic model and reserve; no W6 independent qualification',
                rows=rows,D_relative_to_C=changes,same_policy_cost_attribution=attributions,
                measurement_cost=cost,retained_errors=progress['errors'])


def render(report):
    out = ['# 九例诊断版 ABCD 后端结果','',
           '模型身份：`workload-v10-complete-diagnostic-v1`；未取得 W6 独立资格。最终应用实测不反馈拟合或重选。','',
           f"物理任务 {report['completed_physical_tasks']}/{report['physical_tasks']} 完成；"
           f"失败 {report['failed_physical_tasks']}，已结算 {report['settled_physical_tasks']}；"
           f"九例 {report['targets']} 组目标、{report['method_records']} 条方法记录。",'',
           'A 的 L=1；B/C/D 使用确认的 L。所有方法 II=1，输入 service 另加一周期。'
           'Tmin 覆盖 RR/IR/RO，I/O 为 0.2T；频率来自固定 grt 实现。hold 单列。','',
           '| 案例 | T ps | 方法 | L | 结构/视图 | 面积 µm² | Tmin ps | Fmax MHz | setup WNS ps | hold WNS ps | 目标 |',
           '|---|---:|---|---:|---|---:|---:|---:|---:|---:|---|']
    for r in report['rows']:
        m=r['measurement'];s=r['structure']
        def num(k):return f"{m[k]:.2f}" if m.get(k) is not None else '—'
        status=('满足' if m['target_met'] else '未满足') if m['status']=='completed' else m['status']
        out.append(f"| {r['case']} | {r['T_ps']} | {r['method']} | {r['L']} | {s['structure']}/{s['view']} | "
                   + ' | '.join(num(k) for k in ('cell_area_um2','full_setup_minimum_period_ps','maximum_frequency_MHz',
                                                 'setup_worst_slack_ps','hold_worst_slack_ps'))+f' | {status} |')
    out += ['', 'D 相对 C 的变化以负面积／负 Tmin 为改善；相同 RTL 如实保留。','',
            '| 案例 | T ps | 面积变化 | Tmin 变化 | 同 RTL |','|---|---:|---:|---:|---|']
    for r in report['D_relative_to_C']:
        def pct(k):return f"{100*r[k]:+.2f}%" if k in r else '—'
        out.append(f"| {r['case']} | {r['T_ps']} | {pct('area_change_fraction')} | {pct('minimum_period_change_fraction')} | {r['same_RTL']} |")
    out += ['', '同策略代价归因（D 相对 D_static_cal）：','',
            '| 案例 | T ps | 面积变化 | Tmin 变化 | 同 RTL |','|---|---:|---:|---:|---|']
    for r in report['same_policy_cost_attribution']:
        def pct(k):return f"{100*r[k]:+.2f}%" if k in r else '—'
        out.append(f"| {r['case']} | {r['T_ps']} | {pct('area_change_fraction')} | {pct('minimum_period_change_fraction')} | {r['same_RTL']} |")
    out += ['', 'D 的冻结预测与实测（误差为预测/实测−1；只在完整测量后给出）：','',
            '| 案例 | T ps | 预测面积 µm² | 实测面积 µm² | 面积误差 | 预测完整周期 ps | 实测 Tmin ps | 周期误差 | 目标判断一致 |',
            '|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for r in report['rows']:
        if r['method']!='D':continue
        p=r['prediction'];m=r['measurement'];e=r.get('prediction_error',{})
        def actual(k):return f"{m[k]:.2f}" if m.get(k) is not None else '—'
        def error(k):return f"{100*e[k]:+.2f}%" if k in e else '—'
        match=('是' if e['target_classification_correct'] else '否') if e else '—'
        out.append(f"| {r['case']} | {r['T_ps']} | {p['total_area_um2']:.2f} | {actual('cell_area_um2')} | "
                   f"{error('area_signed_fraction')} | {p['critical_required_ps']:.2f} | "
                   f"{actual('full_setup_minimum_period_ps')} | {error('complete_required_signed_fraction')} | {match} |")
    out += ['', '所选 D 的预测分级与状态规模；级间范围来自冻结模型，实测瓶颈类来自固定实现的 RR/IR/RO 时钟阈值。','',
            '| 案例 | T ps | 保存变量位 | 保存信号 | 预测各级 required 最小/最大 ps | 预测最慢级 | 实测瓶颈类 |',
            '|---|---:|---:|---:|---:|---|---|']
    for r in report['rows']:
        if r['method']!='D':continue
        p=r['prediction'];s=r['structure'];m=r['measurement'];stages=p['stages']
        slowest=max(stages,key=lambda x:x['required_ps'])
        span=f"{min(x['required_ps'] for x in stages):.2f}/{slowest['required_ps']:.2f}"
        critical='—'
        if m['status']=='completed':
            names={'register_to_register':'RR','input_to_register':'IR','register_to_output':'RO'}
            classes=m['path_classes'];limit=m['full_setup_minimum_period_ps']
            critical='/'.join(label for name,label in names.items()
                              if abs(classes[name]['required_period_ps']-limit)<1e-5)
        out.append(f"| {r['case']} | {r['T_ps']} | {s['saved_variable_bits']} | {s['saved_signals']} | "
                   f"{span} | {slowest['stage']} | {critical} |")
    cost=report['measurement_cost']
    out += ['', f"本轮账本费用（包含失败、后继与在途预约）：synth {cost['synth']}、grt {cost['grt']}、"
            f"final {cost['final']}、support {cost['support_calls']}；叶墙钟 {cost['walltime_s']:.2f}s、"
            f"CPU {cost['CPU_time_s']:.2f}s；失败 leaf {cost['failed_leaves']}，在途预约 {cost['pending']}。"]
    if cost['CPU_missing_evidence_leaves']:
        out += ['',f"CPU 是账本记账值；{cost['CPU_missing_evidence_leaves']} 项缺少完整 GNU time CPU 收据，"
                '按完整预约保守记账。进程树采样另保留，不将预约值称为实测 CPU。']
    if report['retained_errors']:
        attempts={}
        for row in report['rows']:
            m=row['measurement']
            for attempt in [m]+m.get('previous_attempts',[]):
                if attempt['status'] in ('failed','failed_before_manifest','clock_readout_failed'):
                    attempts[attempt.get('manifest',(attempt['task'],attempt.get('failure_reason')))]=attempt
        if attempts:
            out += ['', '资源／测量失败与已恢复祖先（重复归属只列一次）：','',
                    '| 任务 | 阶段 | 原因 | 采样后代峰值 MiB | 上限 MiB |',
                    '|---|---|---|---:|---:|']
            for m in attempts.values():
                peak=m.get('sampled_process_tree_peak_rss_MiB')
                peak=f'{peak:.2f}' if peak is not None else '—'
                out.append(f"| {m['task']} | {m.get('failure_stage','—')} | {m.get('failure_reason','—')} | {peak} | {m.get('memory_limit_MiB','—')} |")
        out += ['', '保留的工具／读取失败：','']
        out += [f"- `{r['task']}`：{r['reason']}" for r in report['retained_errors']]
    return '\n'.join(out)+'\n'


def save(root):
    report=build(root);root=Path(root)
    write(root/'comparison.json',report)
    (root/'comparison.md').write_text(render(report))
    columns=['case','T_ps','method','L','II','structure','view','task','status','cell_area_um2',
             'full_setup_minimum_period_ps','maximum_frequency_MHz','setup_worst_slack_ps',
             'setup_tns_ps','hold_worst_slack_ps','hold_tns_ps','timing_coverage_complete','target_met']
    columns+=['failure_stage','failure_reason','memory_limit_MiB','sampled_process_tree_peak_rss_MiB','attempt_leaf_walltime_s']
    stream=io.StringIO();writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
    for r in report['rows']:
        m=r['measurement'];s=r['structure']
        writer.writerow({k:(s[k] if k in ('structure','view') else r[k] if k in r else m.get(k)) for k in columns})
    (root/'comparison.csv').write_text(stream.getvalue())
    print({k:report[k] for k in ('status','cases','targets','method_records','completed_physical_tasks','physical_tasks')})
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args();save(args.root)
