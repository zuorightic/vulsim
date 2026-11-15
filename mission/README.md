# 任务导航与阅读边界

**现行规划统一放在[lxy-plan-fix.md第一章](lxy-plan-fix.md#local-request-plan)，W1—W8历史规划正文放在同文件[第二章](lxy-plan-fix.md#W1-W8-archive)。** 第一章从v10出发，先按候选结构和流水位置联合分配算子／唯一G的本体预算，再换算成与采样外壳含义一致的等效训练T，复用共享模型预测并比较完整时序和总面积。第1～3步已完成MAC32固定候选的软件验收，见[实现与证据](../experiments/arithmetic/evidence/workload_equivalent_mac32_v1/README.md)；第4步模型复用验证、新拆分／寄存器位置及九例19组目标的完整A／B／C／D后端对比继续待办。

代码从2026-11-15恢复后的v10 test基线出发：主仓库`672df3e`、RTLzz `28a4f1d`，对应用户引用的MAC32／Add512／Mul128后端结果。当前新增独立的软件预算／等效T入口，保留v10默认入口作对照；此前撤下的局部预算、逐模块ABC及采样代码仍在恢复前备份中，没有恢复。原W1—W8及第三至五章中的“下一步／必须／唯一排程”只用于追溯，不自动续跑；模型未达精度、关键源退化和独立／组合资格未通过的事实继续保留。

## 当前入口

| 文件 | 用途 |
| --- | --- |
| [原始任务](lxy.md) | 复杂算术拆分、自动流水线与ABCD研究目标，原文保留 |
| [第一章：本体预算与等效训练T规划](lxy-plan-fix.md#local-request-plan) | 唯一现行规划；全局T、本体预算、采样边界换算、真实模型消费、联合分配／选择及八步实施 |
| [第1～3步：MAC32软件验收](../experiments/arithmetic/evidence/workload_equivalent_mac32_v1/README.md) | 177条采样合同、90个候选／837次完整评分、实际等效T查询、逐目标身份及完整回放；精度与后端评价另验 |
| [九例ABCD最终评价（第一章§1.9）](lxy-plan-fix.md#local-request-evaluation) | 九例19组正式T／L、A／B／C／D定义、76条方法记录、冻结对照及完成标准 |
| [第二章：W1—W8历史规划正文](lxy-plan-fix.md#W1-W8-archive) | 原工作包、合同、阶段缺口及局部预算后继，已归档 |
| [模型精度与保留问题（第一章§1.8）](lxy-plan-fix.md#v10-model-status) | Add／Mux／G／S的具体失败、支持缺口，以及完整诊断版预测误差 |
| [v10组件模型证据](../experiments/arithmetic/evidence/common_transition_incidence_v10/README.md) | 共享参数、训练诊断、旧验证回归与机制记录 |
| [v10初次软件集成](../experiments/arithmetic/evidence/workload_transition_v10_v1/README.md) | 公共Query、所有者、真实参数消费及当时覆盖 |
| [v10完整诊断版后端表](../experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/comparison.md) | ABCD面积／完整setup Tmin／频率、hold、失败与预测误差 |
| [九例数学源与配置](../experiments/arithmetic/WORKLOADS.md) | v10已有源、语义和软件入口；目标矩阵由第一章§1.9沿用，旧说明中的后继排程不自动执行 |
| [历史实施与验收（第五章）](lxy-plan-fix.md#step1-wide-acceptance) | 原逐轮实施、失败、资格及后v10预算开发记录；章首标明历史阅读边界 |
| [恢复前完整阶段快照](archive/lxy-W1-W8-stage-20261115.md) | 恢复前完整文档的补充快照，W1—W8正文阅读入口仍为第二章 |
| [恢复清单](archive/v10-restore-20261115.json) | 检查点、完整备份、撤下文件、文档身份及验证收据 |
| [其他历史归档](archive/README.md) | 原十步、共同需求／S机制附件和更早单平台阶段 |

## 后端与账本状态

原九例物理队列保持用户停止状态：67任务中30完成、9工具失败、4用户中止、24未启动。已有报告与停止／清理记录见[结果归档](../experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/README.md)；先前按用户要求删除的大数据库不在本次恢复中重建。恢复后没有启动EDA或拟合。

真实实验历史和最新结清账本保留，不能随代码恢复而回退费用。恢复前所有修改和未跟踪文件已逐文件保存并核对SHA256，主仓库和RTLzz提交均未移动。当前第1～3步只进行既有train-only采样收据审计、软件预测与回放，未启动EDA、重新拟合算子响应或原队列，未提交或推送，mission主目录不新增规划文件。
