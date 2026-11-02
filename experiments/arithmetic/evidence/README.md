# 算术证据导航

步骤编号随计划版本变化。现行实施以[规划第一章及第四章](../../../mission/lxy-plan-fix.md)和[算术实验导航](../README.md)为准，不按目录名大小判断新旧。

| 目录 | 适用版本 |
| --- | --- |
| `step1_wide_v1` | 修订计划步骤一宽位宽补验 |
| `step2_v2` | 修订计划步骤二契约/参考/生成补验 |
| `step3_platforms_v1/v2/v3` | 修订计划步骤三；v1原ns结果作废，v2单位修复重跑，v3软件收尾，当前继承链见导航 |
| [step4_interfaces_v1](step4_interfaces_v1/README.md) | 修订计划步骤四原始验收；v1报告和证据冻结保留 |
| [step4_interfaces_v2](step4_interfaces_v2/README.md) | 修订计划步骤四报告类型/导航/存储策略修订；当前软件核验入口 |
| [step4](step4/README.md)、[step4_review](step4_review/README.md) | **旧计划**区域原型及复核；不代表现行步骤四 |
| `step3`、`step3_budget`、`step3_closure` | **旧计划**ASAP7后端/预算/收尾；由后继冻结明确继承，不代表当前四平台/模型已完成 |
| [step5_mul_templates_v1](step5_mul_templates_v1/README.md)、[step5_mul_capacity_v1](step5_mul_capacity_v1/README.md) | 修订计划步骤五软件/新C与有限容量；ASAP7 64位grt通过，128位grt超时，批量待复审 |
| [step5_mul_closure_v2](step5_mul_closure_v2/README.md)、[step5_mul_capacity_v2](step5_mul_capacity_v2/README.md) | 现行步骤五收尾：位置独立判定、129历史图、精确协议及一次指定128位完整后综合链复测；1450.19秒完成grt，具体域仍按批次准入 |
| [step5](step5/README.md)、[step5_placement](step5_placement/README.md) | **旧计划**split16及位置补验；不代表现行参数化步骤五完成 |

已有冻结文件按原路径保留。旧目录新增的README只是导航，不重写当时索引或升级验收范围。后续新包使用[分层存储规则](../../arithmetic_dse/evidence_storage.md)：优先增量快照、按内容引用和压缩；索引与hash不能替代需要重算的实际内容。

[step5_metric_scope_v1](step5_metric_scope_v1/README.md)是后加的时序口径澄清：解释整体setup与core_clk同钟最小周期，继承v2原报告和容量结论，无新增物理／STA。其后继冻结为`mul_templates_freeze_v3.json`。

- **修订步骤六**：[step6_whole_graph_v1](step6_whole_graph_v1/README.md)为43案例整图软件/RTL验收，[step6_capacity_v1](step6_capacity_v1/README.md)保存两项失败容量探针和四项暂停控制点；不作为训练数据、目标标签或主矩阵。冻结为`whole_graph_freeze_v1.json`，继承步骤五v3。

- **步骤六P1与容量后继**：`step6_review_v2`为实际位宽非零证明、原图回放及文档快照修订；`step6_capacity_v2`保留32GiB复测和Yosys线程约束纠正前后的独立准入/实跑。原v1目录保持原字节。默认whole_graph_evidence核验最新后继；物理完成与时序可行分别判断，数据不用于训练或主矩阵。

步骤六当前最终验收为whole_graph_freeze_v2：软件／原生整图和P1安全证明、F2及UDR100ns有限grt容量均有实际证据，旧失败及收费全部保留。两个后继小包含源码增量、逐阶段报告／SDC、资源回执、独立图回放和便携正负例。原UDR两项synth控制仍not_run，不宣称两轴模型覆盖；模型和688主矩阵未完成。
