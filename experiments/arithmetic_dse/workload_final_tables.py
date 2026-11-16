"""Evaluation-only CSV and C/D tables; never imported by the selector."""
import csv
import math
import statistics
from pathlib import Path

from .workload_abcd import read,write


def software_tables(root,out):
    """Expose newly selected D implementations before physical jobs finish."""
    root,out=Path(root),Path(out);rows=[]
    for p in sorted((root/'software').glob('*/final-selections.json')):
        selection=read(p)
        for r in selection['records']:
            d=r['methods']['D'];prediction=d['prediction']
            folder=Path(d['rtl']).parent;requests=read(folder/'equivalent-requests.json')
            budgets=list(requests['budgets_ps'].values())
            queries=requests['actual_queries']
            budgeted_queries=[queries[i] for i in requests['budgets_ps']]
            taus=[q['flow_context']['target_period_ps'] if 'flow_context' in q else q['target_ps']
                  for q in budgeted_queries]
            rows.append(dict(case=r['case'],target_ps=r['target']['T_ps'],L=d['L'],grammar=d['grammar'],
                predicted_period_ps=prediction['critical_required_ps'],predicted_area_um2=prediction['total_area_um2'],
                predicted_setup_met=prediction['target_met'],candidates=r['search']['candidates'],
                complete_candidates=r['search']['complete'],budget_range_ps=[min(budgets),max(budgets)],
                equivalent_T_range_ps=[min(taus),max(taus)],allocation_envelope_ps=d.get('allocation_envelope_ps'),
                budgeted_owners=len(budgets),queries_outside_budget_variables=len(queries)-len(budgets),
                same_RTL_as_C=d['rtl_sha256']==r['methods']['C']['rtl_sha256'],
                same_RTL_as_static_control=d['rtl_sha256']==r['methods']['same_policy_static']['rtl_sha256'],
                rtl_sha256=d['rtl_sha256'],functional_status=d['simulation_status']))
    write(out/'software-finalists.json',dict(rows=rows,selected_groups=len(rows),required_groups=19,
        physical_results_used=False,precision_qualified=False,scope='software predictions only'))
    text=['# 新目标下的D软件选择','',
        '这些数值是冻结共享函数的完整预测，实际后端结果另表。目标未满足时按完整违约、面积与稳定规则保留后备；不会因此放宽目标。等效训练T用于函数查询，实际ABC仍使用全局目标。','',
        '| 案例 | T / L | 块宽 / limb | 预测完整周期 ps | 预测总面积 µm² | 预测setup | 完整候选 | 与C同RTL |',
        '| --- | --- | --- | ---: | ---: | --- | ---: | --- |']
    for r in rows:
        text.append(f"| {r['case']} | {r['target_ps']} / {r['L']} | {' / '.join(map(str,r['grammar']))} | {r['predicted_period_ps']:.2f} | {r['predicted_area_um2']:.2f} | {r['predicted_setup_met']} | {r['complete_candidates']} / {r['candidates']} | {r['same_RTL_as_C']} |")
    (out/'software-finalists.md').write_text('\n'.join(text)+'\n')
    return rows


def tables(root,out):
    root,out=Path(root),Path(out);p=root/'comparison.json'
    if not p.exists():return
    doc=read(p);rows=doc['records'];fields=['case','target_ps','L','II','additional_input_service_cycles',
        'method','status','area_um2','Tmin_ps','frequency_MHz','setup_met','hold_WNS_ps','hold_met',
        'timing_coverage_complete','sequential_area_um2','sequential_cells','combinational_and_buffer_area_um2',
        'physical_only_area_um2','period_error','area_error','rtl_sha256','task_id']
    with (out/'comparison.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    groups={}
    for row in rows:groups.setdefault((row['case'],row['target_ps']),{})[row['method']]=row
    def stats(values):
        values=sorted(values);index=.95*(len(values)-1);lo=math.floor(index);hi=math.ceil(index)
        return dict(count=len(values),median=statistics.median(values),
            P95=values[lo]+(values[hi]-values[lo])*(index-lo),maximum=values[-1]) if values else dict(count=0)
    error_summary={}
    for method in ('A','B','C','D'):
        measured=[r for r in rows if r['method']==method and r['status']=='measured_grt'];sources={}
        for r in measured:sources.setdefault(r['case'],[]).append(r)
        error_summary[method]=dict(records=len(measured),sources=len(sources),
            period_APE=stats([abs(r['period_error']) for r in measured]),
            area_APE=stats([abs(r['area_error']) for r in measured]),
            source_mean_period_APE=stats([statistics.mean(abs(r['period_error']) for r in rs) for rs in sources.values()]),
            source_mean_area_APE=stats([statistics.mean(abs(r['area_error']) for r in rs) for rs in sources.values()]),
            false_feasible_setup=[dict(case=r['case'],T_ps=r['target_ps'],predicted_ps=r['prediction']['critical_required_ps'],
                measured_ps=r['Tmin_ps']) for r in measured if r['prediction']['target_met'] and not r['setup_met']])
    write(out/'model-error-summary.json',dict(methods=error_summary,quantile='linear p*(n-1)',
        application_evaluation_only=True,precision_qualification=False,model_refitted=False,
        hold_not_predicted_by_setup_target_met=True))
    pipeline=[];gain_text=['# 相对未拆分A的流水收益','',
        '频率倍数按同一比较目标下的实测 Tmin(A)/Tmin(方法) 计算。该倍数只比较完整setup阈值，hold和覆盖仍须单独满足。A在各实际T下重新映射，不能将不同T的A混作同一个参考。','',
        '| 案例 | 目标 ps | B / A 频率 | C / A 频率 | D / A 频率 | D / C 面积 | D setup / hold |',
        '| --- | ---: | ---: | ---: | ---: | ---: | --- |']
    for (cid,T),methods in groups.items():
        if not all(k in methods and methods[k]['status']=='measured_grt' for k in ('A','B','C','D')):continue
        a=methods['A'];d=methods['D'];ratios={k:a['Tmin_ps']/methods[k]['Tmin_ps'] for k in ('B','C','D')}
        pipeline.append(dict(case=cid,T_ps=T,frequency_ratio_to_A=ratios,
            area_ratio_to_A={k:methods[k]['area_um2']/a['area_um2'] for k in ('A','B','C','D')},
            D_area_ratio_to_C=d['area_um2']/methods['C']['area_um2'],
            D_setup_met=d['setup_met'],D_hold_met=d['hold_met'],D_coverage=bool(d['timing_coverage_complete'])))
        gain_text.append(f"| {cid} | {T} | {ratios['B']:.3f}× | {ratios['C']:.3f}× | {ratios['D']:.3f}× | {pipeline[-1]['D_area_ratio_to_C']:.3f}× | {d['setup_met']} / {d['hold_met']} |")
    (out/'pipeline-gains.md').write_text('\n'.join(gain_text)+'\n')
    write(out/'pipeline-gains.json',dict(complete_groups=len(pipeline),required_groups=19,rows=pipeline,
        D_faster_than_A=sum(r['frequency_ratio_to_A']['D']>1 for r in pipeline),
        D_setup_met=sum(r['D_setup_met'] for r in pipeline),
        D_setup_hold_coverage_met=sum(r['D_setup_met'] and r['D_hold_met'] and r['D_coverage'] for r in pipeline),
        qualification='diagnostic_only'))
    attribution=[];attribution_text=['# 同一候选池中的模型价格归因','',
        'D与same_policy_static使用同一候选池；后者以静态价格及共同完整评分器排序。此处单独比较两者的实际实现，避免把扩大候选覆盖产生的收益都归因于后端模型。','',
        '| 案例 | 目标 ps | 控制 面积 / Tmin | D 面积 / Tmin | D面积降低 | D周期降低 | 控制 setup / hold | D setup / hold |',
        '| --- | ---: | --- | --- | ---: | ---: | --- | --- |']
    for (cid,T),methods in groups.items():
        s,d=methods.get('same_policy_static'),methods.get('D')
        if not s or not d or any(r['status']!='measured_grt' for r in (s,d)):continue
        a=(s['area_um2']-d['area_um2'])/s['area_um2'];t=(s['Tmin_ps']-d['Tmin_ps'])/s['Tmin_ps']
        attribution.append(dict(case=cid,T_ps=T,area_reduction=a,Tmin_reduction=t,
            same_implementation=s['rtl_sha256']==d['rtl_sha256'],
            control_setup=s['setup_met'],control_hold=s['hold_met'],D_setup=d['setup_met'],D_hold=d['hold_met']))
        attribution_text.append(f"| {cid} | {T} | {s['area_um2']:.2f} / {s['Tmin_ps']:.2f} | {d['area_um2']:.2f} / {d['Tmin_ps']:.2f} | {a:+.2%} | {t:+.2%} | {s['setup_met']} / {s['hold_met']} | {d['setup_met']} / {d['hold_met']} |")
    write(out/'model-attribution.json',dict(rows=attribution,required_groups=19,
        D_faster=sum(r['Tmin_reduction']>0 for r in attribution),D_smaller=sum(r['area_reduction']>0 for r in attribution),
        same_implementation=sum(r['same_implementation'] for r in attribution),qualification='diagnostic_only'))
    (out/'model-attribution.md').write_text('\n'.join(attribution_text)+'\n')
    comparisons=[];text=['# 同目标下的 D / C 比较','',
        '相对面积降低率为(C−D)/C，相对Tmin降低率同理。目标、L、II和服务协议相同；只有setup／hold与覆盖均满足时，才将面积降低记为同时满足时序的收益。', '',
        '| 案例 | T ps | C 面积 / Tmin | D 面积 / Tmin | 面积降低 | Tmin降低 | C setup / hold | D setup / hold |',
        '| --- | ---: | --- | --- | ---: | ---: | --- | --- |']
    for (cid,T),methods in groups.items():
        c,d=methods.get('C'),methods.get('D')
        if not c or not d or any(r['status']!='measured_grt' for r in (c,d)):continue
        gain=(c['area_um2']-d['area_um2'])/c['area_um2'];speed=(c['Tmin_ps']-d['Tmin_ps'])/c['Tmin_ps']
        valid=all(r['setup_met'] and r['hold_met'] and r['timing_coverage_complete'] for r in (c,d))
        comparisons.append(dict(case=cid,T_ps=T,area_reduction=gain,Tmin_reduction=speed,
            both_setup_hold_coverage_met=valid,same_implementation=c['rtl_sha256']==d['rtl_sha256'],
            C=dict(area_um2=c['area_um2'],Tmin_ps=c['Tmin_ps'],setup=c['setup_met'],hold=c['hold_met']),
            D=dict(area_um2=d['area_um2'],Tmin_ps=d['Tmin_ps'],setup=d['setup_met'],hold=d['hold_met'])))
        text.append(f"| {cid} | {T} | {c['area_um2']:.2f} / {c['Tmin_ps']:.2f} | {d['area_um2']:.2f} / {d['Tmin_ps']:.2f} | {gain:+.2%} | {speed:+.2%} | {c['setup_met']} / {c['hold_met']} | {d['setup_met']} / {d['hold_met']} |")
    (out/'D-versus-C.md').write_text('\n'.join(text)+'\n')
    write(out/'D-versus-C.json',dict(rows=comparisons,qualified=False,scope='frozen grt implementations at each target',
        area_benefit_with_complete_TT_timing=sum(r['both_setup_hold_coverage_met'] and r['area_reduction']>0 for r in comparisons),
        clock_benefit=sum(r['Tmin_reduction']>0 for r in comparisons)))
    if doc['physical_comparison_complete'] and len(comparisons)==19:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import numpy as np
        x=np.arange(len(comparisons));labels=[r['case']+'\n'+str(r['T_ps'])+' ps' for r in comparisons]
        fig,axes=plt.subplots(2,1,figsize=(17,8),sharex=True,layout='constrained')
        colors=['#2b8c72' if r['both_setup_hold_coverage_met'] else '#bb6655' for r in comparisons]
        axes[0].bar(x,[100*r['area_reduction'] for r in comparisons],color=colors)
        axes[0].set_ylabel('Area reduction vs C (%)');axes[0].axhline(0,color='#666',linewidth=.8)
        axes[1].bar(x,[100*r['Tmin_reduction'] for r in comparisons],color=colors)
        axes[1].set_ylabel('Tmin reduction vs C (%)');axes[1].axhline(0,color='#666',linewidth=.8)
        axes[1].set_xticks(x,labels,rotation=55,ha='right',fontsize=8)
        fig.suptitle('Equivalent-budget D vs static C — ASAP7 TT, post-CTS grt\nGreen: both meet setup/hold/coverage; red: at least one does not. Diagnostic model.')
        for ax in axes:ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        fig.savefig(out/'D-versus-C.png',dpi=180);fig.savefig(out/'D-versus-C.pdf');plt.close(fig)
        fig,axes=plt.subplots(2,1,figsize=(17,8),sharex=True,layout='constrained')
        palette=['#777777','#5085b9','#d99c42','#318a72'];width=.19
        for k,method in enumerate(('A','B','C','D')):
            offset=(k-1.5)*width
            axes[0].bar(x+offset,[1 if method=='A' else r['frequency_ratio_to_A'][method] for r in pipeline],
                width,label=method,color=palette[k])
            axes[1].bar(x+offset,[r['area_ratio_to_A'][method] for r in pipeline],width,color=palette[k])
        axes[0].set_ylabel('Frequency / A');axes[1].set_ylabel('Cell area / A');axes[0].legend(ncol=4)
        axes[1].set_xticks(x,labels,rotation=55,ha='right',fontsize=8)
        for ax in axes:ax.axhline(1,color='#666',linewidth=.8);ax.grid(axis='y',alpha=.2);ax.set_axisbelow(True)
        fig.suptitle('ABCD measured pipeline gains — ASAP7 TT, post-CTS grt\nEach group normalized to its A at the same T; hold and target feasibility reported separately.')
        fig.savefig(out/'ABCD-normalized.png',dpi=180);fig.savefig(out/'ABCD-normalized.pdf');plt.close(fig)
