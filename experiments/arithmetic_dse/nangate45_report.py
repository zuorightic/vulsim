"""Compact N3/N4 evidence after the sealed evaluation; no model changes."""
import argparse
from collections import Counter,defaultdict
from pathlib import Path
import math

import numpy as np
from .nangate45_samples import ROOT,read,write,sha,verify
from .nangate45_fit_sealed import metrics


def report(root,out):
    root=Path(root).resolve();out=Path(out).resolve();a=verify(root)
    evaluation=read(root/'evaluation.json');verification=read(root/'verification.json')
    payload=read(root/'frozen-model.json');selection=read(root/'selection.json');rows=read(root/'evaluation-data.json')
    predicted=read(root/'predictions.json');request_diagnostics={}
    for family in ('Mul','Add','G'):
        request_diagnostics[family]={}
        for metric in ('delay_ps','area_um2'):
            selected=[p for p in predicted if p['family']==family and p['metric']==metric and p['role']=='test']
            request_diagnostics[family][metric]=dict(maximum_point_APE=max(p['error_fraction'] for p in selected),
                per_clock={str(t):dict(points=sum(p['target_ps']==t for p in selected),
                    median_APE=float(np.median([p['error_fraction'] for p in selected if p['target_ps']==t])),
                    maximum_APE=max(p['error_fraction'] for p in selected if p['target_ps']==t)) for t in a['clocks_ps']})
    source_counts=Counter(r['source'] for r in rows if r['role']=='train')
    train=[r for r in rows if r['role']=='train'];weights=np.array([1/source_counts[r['source']] for r in train]);weights/=weights.sum()
    global_actual={}
    for metric in ('delay_ps','area_um2'):
        scale=float(np.exp(weights@np.log([r[metric]/r['ASAP7_'+metric] for r in train])))
        global_actual[metric]=dict(scale=scale,by_family={})
        for family in ('Mul','Add','G'):
            rr=[r for r in rows if r['family']==family and r['role']=='test']
            global_actual[metric]['by_family'][family]=metrics(rr,[scale*r['ASAP7_'+metric] for r in rr],metric)
    family_actual_affine={}
    for family in ('Mul','Add','G'):
        family_actual_affine[family]={}
        tr=[r for r in rows if r['family']==family and r['role']=='train']
        count=Counter(r['source'] for r in tr);w=np.array([1/count[r['source']] for r in tr]);w/=w.sum()
        for metric in ('delay_ps','area_um2'):
            y=np.array([r[metric] for r in tr]);ref=np.array([r['ASAP7_'+metric] for r in tr]);x=np.array([ref/y,1/y]).T
            coefficient=np.linalg.lstsq(x*np.sqrt(w)[:,None],np.sqrt(w),rcond=None)[0]
            scale=float(max(0,coefficient[0]));intercept=float(coefficient[1])
            family_actual_affine[family][metric]=dict(scale=scale,intercept=intercept,analysis_only_not_compiler_prices=True,
                roles={role:metrics([r for r in rows if r['family']==family and r['role']==role],
                    [max(1e-9,scale*r['ASAP7_'+metric]+intercept) for r in rows if r['family']==family and r['role']==role],metric) for role in ('train','validation','test')})
    response=[]
    for s in a['sources']:
        rr=sorted([r for r in rows if r['source']==s['id']],key=lambda r:r['target_ps'])
        response.append(dict(source=s['id'],family=s['family'],role=s['role'],historical_role=s['historical_role'],
            points=[dict(T=r['target_ps'],delay_ps=r['delay_ps'],area_um2=r['area_um2'],
                         ASAP7_delay_ps=r['ASAP7_delay_ps'],ASAP7_area_um2=r['ASAP7_area_um2'],
                         measured_delay_ratio=r['delay_ps']/r['ASAP7_delay_ps'],measured_area_ratio=r['area_um2']/r['ASAP7_area_um2']) for r in rr]))
    model_choices={}
    for family in payload['functions']:
        model_choices[family]={}
        for metric,fn in payload['functions'][family].items():
            e=selection[family][metric]
            model_choices[family][metric]=dict(form=fn['form'],time_scale=fn['time_scale'],
                validation=e['candidates'][e['chosen']]['validation'],test=evaluation['stats'][family][metric]['test'])
    compact=dict(version='nangate45-N34-summary-v1',N3='finite paired campaign complete',N4='shared functions fitted, selected, frozen and evaluated',
        arithmetic_test_gates_passed=evaluation['arithmetic_test_gates_passed'],full_D_ready=False,
        sources=len(a['sources']),Nangate45_points=len(a['tasks']),ASAP7_points_reused=len(a['tasks']),new_ASAP7_EDA_calls=0,
        source_counts=dict(Counter(s['role'] for s in a['sources'])),row_counts=dict(Counter(r['role'] for r in rows)),
        test_scope='new-backend holdout labels from historical ASAP7 train sources; no claim of unseen-structure independence',
        old_locked_independent_sources_read=False,request_clocks_ps=a['clocks_ps'],
        profile_sha256=a['profile_sha256'],sampling_layout_overrides=a['sampling_layout_overrides'],
        time_axis_limit='same numerical T paired at 500/1500/3000; selected time scale is function calibration, not an independently measured intrinsic technology speed ratio',
        label_scope=a['labels'],measured_to_measured_global_scale=global_actual,
        measured_to_measured_family_scale=evaluation['paired_actual_scaling'],measured_to_measured_family_affine=family_actual_affine,model_choices=model_choices,
        raw_test_stats=evaluation['stats'],per_request_diagnostics=request_diagnostics,source_responses=response,
        source_group_error_contract=read(root/'statistical-contract.json'),
        numerical_verification=verification['software'],accounting={k:v for k,v in verification['receipts'].items() if k!='labels'},
        R1_R5_modified=False,exact_lookup=False,online_backend_feedback=False,application_PPA_used=False,
        remaining=['N5: S/shared, actual G embedding and small compositions','N6: H_char, equivalent request contract and complete D integration'],
        external_root=str(root),external_evidence=[dict(path=str(root/name),sha256=sha(root/name)) for name in (
            'admission.json','paired-ASAP7-flow-audit.json','N3-analysis-contract.json','statistical-contract.json','feature-contract.json','model-freeze.json','frozen-model.json','selection.json',
            'calibration-data.json','evaluation-data.json','evaluation.json','predictions.json','verification.json')],
        implementation={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'experiments/arithmetic_dse').glob('nangate45_*.py')})
    out.mkdir(parents=True,exist_ok=True);write(out/'summary.json',compact)
    table=['| 共享类型 | 指标 | 冻结形式／时间轴比例 | 验证 median／P95 | 测试 median／P95 | 测试门槛 |',
           '| --- | --- | --- | --- | --- | --- |']
    for family in ('Mul','Add','G'):
        for metric in ('delay_ps','area_um2'):
            d=model_choices[family][metric];v=d['validation'];t=d['test']
            table.append(f'| {family} | {metric} | {d["form"]} / {d["time_scale"]:g} | {100*v["median_APE"]:.2f}% / {100*v["P95_APE"]:.2f}% | {100*t["median_APE"]:.2f}% / {100*t["P95_APE"]:.2f}% | {"通过" if t["passed"] else "未通过"} |')
    readme='''# Nangate45 N3＋N4：小批配对采样与共享函数

本轮只处理 MAC32、Add512、Mul128 所需的小算术与少量归约源。N3 的有限采样、N4 的函数拟合／验证选择／参数冻结／封存测试均已执行；完整 D 包仍待 N5／N6 的 S、shared、G 嵌入、H_char 与采样合同。正式配置继续保持 pending。

20 个逻辑源包括 Mul 6 个、Add／ADC 10 个、G 4 个，每源 SDC＝ABC＝500／1500／3000ps，共 60 个 Nangate45 grt 点，与 60 个已有 ASAP7 点逐一配对。原始 RTL 在三时钟及两平台间逐字节相同；没有新增 ASAP7 后端调用。全部源均来自历史 ASAP7 train，迁移批次将两平台副本共同分为 11 train／4 validation／5 test；同一源的时钟及相应负载变体不跨职责。新后端 test 只证明留出标签上的迁移表现，不能称为 ASAP7 模型未见结构的独立泛化，原锁定独立源未读。

测量标签是独占 producer 的内部最大延迟与组合面积。完整引脚／输出／所有权、CTS 全状态边界等价与 D／clock／top 负控、1000 倍 ns→ps 换算、同路径数据读数和完整面积守恒均有收据。虚拟采样 FF、控制、clock、tap、observer 面积不混入算术组合面积。

Nangate45 的小 shell 不满足默认电源条带最小宽度，因此本批统一采用 `core_side=max(60,ceil(sqrt(synth_area/0.4)))` µm 的正方形 core 和原 5µm margin。除最小 core 外保持 40% 规则，实际 DIE／CORE 及清空自动 CORE_UTILIZATION 的命令保留。S／shared、边界及应用嵌入仍需 N5／N6 验证这一采样差异。接通阶段的 PDN、floorplan 设置、CLK／CK 负控及 tap 分类失败原样保留；沿用已付费综合、post-repair 或 grt checkpoint，未清零／退款费用，也未将失败点当训练标签。

模型依次比较全局比例、类型比例、类型仿射和共享 log 特征 ridge。时延与面积分别选择；请求轴比例仅从预登记的 0.5／1／2 选择，ridge 只取 0.1／1／10。训练源发现宽加法的面积请求响应后，在任何新后端验证／测试标签采集前封存统一的 `log(1+width)*log(T/1500)` 特征；没有精确形状／时钟／案例价格。参数只拟合 train，形式只根据 validation 选择；随后锁定参数再采集／打开 test，测试未回流。时间轴比例只是数值校准参数；本批只有三档同数值 T 的配对测量，不能据此宣称后端固有速度比例或采样边界相同。

统计先取每源各时钟 APE 的 median，再继承原合同的最近秩 source-macro median 与 P95；门槛为 15%／35%，同时保留最大逐源 median≤35% 的保护项。原提案中的插值分位数在验证／测试前通过独立合同修正；没有放宽门槛。

'''+ '\n'.join(table)+'''

测试样本数量较少，所有误差以这里的有限源为界；未覆盖的截断、mask、负载组合和大型 G 继续视为外推，G 成员仍只能由整个归约所有者计价一次。实测对实测缩放与旧函数预测迁移分别列在 [summary.json](summary.json)，不能把旧函数自身误差算作后端比例误差。

仓库只保存小型参数、摘要和代码。[model.json](model.json) 引用已有 ASAP7 响应的 SHA256；加载时校验平台、profile、stage 与引用哈希，数值推理阶段不读取文件、不启动子进程。宽度 12×20、未采样的 1700ps、未知 source／case／instance 元数据及全 120 个冻结预测均有软件复核；平台、profile、阶段、ABC 请求等错配拒绝。插值软件测试不授予该宽度实测资格。

完整 RTL、映射、ODB、报告、Liberty 引脚、路径、训练／验证选择／封存测试和累计账本收据均位于仓库外，路径和哈希见摘要。ASAP7 的现行控制器、已冻结模型、输入和安装均未修改；N1 的 770 个基线文件与 1056 个需求文件再次核对一致。未执行 R1～R5，也未启动三例应用 A／BCD 主表。
'''
    (out/'README.md').write_text(readme)
    return dict(summary=str(out/'summary.json'),readme=str(out/'README.md'),test_gates_passed=compact['arithmetic_test_gates_passed'])


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();print(json.dumps(report(a.root,a.out),indent=2))
