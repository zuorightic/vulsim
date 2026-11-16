# 任务导航与阅读边界

**现行规划统一放在[lxy-plan-fix.md第一章](lxy-plan-fix.md#local-request-plan)，已完成前置与W1—W8历史规划放在同文件[第二章](lxy-plan-fix.md#W1-W8-archive)。** 第一章从v10出发，按候选结构和位置联合分配算子／唯一G的本体预算，换算成与原采样外壳同义的等效训练T，再复用共享模型预测完整时序及总面积。预算适配、MAC32固定候选和首轮有限搜索／RTL验证的详细完成记录已[归档](lxy-plan-fix.md#completed-local-request-archive)。2026-11-16审查确认完整评分尚未继续反馈到新位置，并发现G提案路径权重、L相关粒度及状态规模等问题；证据见[§1.10](lxy-plan-fix.md#local-request-document-status)，后继修复按[§1.6](lxy-plan-fix.md#local-request-steps)执行，不能将首轮软件通过说成搜索或模型资格已经完整。现行物理矩阵继续按冻结版本运行：九例各两档L、37组T／L、148条ABCD主方法及37条同池归因，原19组／76条身份保留。

代码从2026-11-15恢复后的v10 test基线出发：主仓库`672df3e`、RTLzz `28a4f1d`，对应用户引用的MAC32／Add512／Mul128后端结果。当前新增独立的软件预算／等效T入口，保留v10默认入口作对照；此前撤下的局部预算、逐模块ABC及采样代码仍在恢复前备份中，没有恢复。原W1—W8及第三至五章中的“下一步／必须／唯一排程”只用于追溯，不自动续跑；模型未达精度、关键源退化和独立／组合资格未通过的事实继续保留。

## 当前入口

2026-11-16追加要求后的主入口是[九例各两档L、9并行／2线程](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/README.md)，具体矩阵见第一章§1.9.6。完整审计快照见[ABCD、后端耗时与未测RTL](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/README.md)：2026-11-16 18:07:23时实测55／148条、setup通过9条（6个独立任务）；18:18:39又新增Horner L4/T1900的A，达到56／148，增量另存。队列继续推进，实时状态以观察器及成功收据为准；原19组与旧并发交接按历史身份解释。

| 文件 | 用途 |
| --- | --- |
| [原始任务](lxy.md) | 复杂算术拆分、自动流水线与ABCD研究目标，原文保留 |
| [第一章：本体预算与等效训练T规划](lxy-plan-fix.md#local-request-plan) | 唯一现行规划；时间语义、模型消费、审查后R1～R7修复、37组／148条共同版本交付 |
| [第1～3步：MAC32软件验收](../experiments/arithmetic/evidence/workload_equivalent_mac32_v1/README.md) | 177条采样合同、90个候选／837次完整评分、实际等效T查询、逐目标身份及完整回放；精度与后端评价另验 |
| [第4～5步：模型回归与首轮新候选](../experiments/arithmetic/evidence/workload_equivalent_steps45_v1/README.md) | 279条组件／6个旧组合回归、175个完整候选、72份RTL新仿真；首轮有限提案完成，不代表完整位置反馈已实现，S／shared和嵌入资格失败保留 |
| [第6～8步：A/L紧凑目标v2](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/README.md) | 未拆分A参考实测、1.25／1.5倍A/L目标、新D拆分与预算／位置搜索及ABCD后端状态；未测不算完成 |
| [Dot16 L4／L5重新拆分](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/dot16-L45/README.md) | 按用户要求新增4／5级对照，逐级检查活跃算术，保留原L8；软件与后端状态独立报告 |
| [运行进度与异常审查](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/latest.md) | 两档L实际推进、已恢复的软件错误、后端失败、资源与独立崩溃监控；只统计已验收读数 |
| [D拆分／位置问题与独立软件反例](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/d-split-placement-review-20261116-v1.md) | 同结构后移反例、G路径权重、Add语法／carry风险、Mul状态膨胀；不替换当前冻结D、不新增PPA |
| [全部ABCD比较与已测逐项](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/abcd-comparison.md) | 37组／148条状态、全部已测面积／完整Tmin／频率／setup／hold／线程／原始读数，旧版本独立索引 |
| [后端耗时与瓶颈](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/backend-bottleneck-analysis.md) | 命令及ORFS子阶段计时；setup修复、CTS内LEC／合法化、pin_access分开归因，未完成阶段另列 |
| [未测ABCD的RTL实现与寄存器](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/unmeasured-rtl.md) | 124条已冻结方法索引；未测33份不同RTL的逐级算术／G与6191个寄存器信号，带图／位置／位掩码／赋值行；未冻结项明确待定 |
| [旧后端存储清理](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/storage-cleanup-20261116-v1.md) | 2026-11-16删除18,919个旧中间ODB／guide，释放54.649GiB；报告、最终DB及当前实验保留，含删除清单与清理后核对 |
| [流水目标周期审查](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/clock-target-review.md) | A/L倍率未显式保证固定边界与不均衡开销；逐例额度和改进建议，未放宽冻结周期 |
| [被替代的C测时v1](../experiments/arithmetic/evidence/workload_equivalent_steps678_v1/README.md) | 原C探针及其实际结果、失败和费用保留；不再用于新目标 |
| [九例ABCD最终评价（第一章§1.9）](lxy-plan-fix.md#local-request-evaluation) | A／B／C／D定义、冻结对照及完成标准；原19组／76条保留，§1.9.6扩展为两档L的37组／148条 |
| [第二章：已完成前置与W1—W8历史规划](lxy-plan-fix.md#W1-W8-archive) | 第1～5步软件、旧19组、Dot16、并发／存储前置记录及原W1—W8正文；形成时的下一步不自动续跑 |
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

原九例物理队列保持用户停止状态：67任务中30完成、9工具失败、4用户中止、24未启动。已有报告与停止／清理记录见[结果归档](../experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/README.md)；先前按用户要求删除的大数据库不在本次恢复中重建。恢复后及本轮第1～5步均未启动EDA或响应拟合。

真实实验历史和最新结清账本保留，不能随代码恢复而回退费用。恢复前所有修改和未跟踪文件已逐文件保存并核对SHA256，主仓库和RTLzz提交均未移动。第6～8步已另行启动新有限物理批次，使用相同累计账本；不续跑原停止队列。第1～5步只进行既有数据职责内的采样审计、回归、软件预测、有限候选生成和RTL功能仿真；第4～5步新增原生显式放置接口和独立验证／搜索入口。65项相关回归全部通过，完整便携回放另有收据；模型资格及九例物理比较未完成。未提交或推送，mission主目录不新增规划文件。
