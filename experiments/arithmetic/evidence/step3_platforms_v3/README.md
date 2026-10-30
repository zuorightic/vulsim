# 步骤三软件收尾证据 v3 / 后端冻结 v7

本次关闭静态SDC命令边界P2并补来源/交接追溯。**没有新增synth、grt或final，没有改变有效平台参数。** P1已在v6修复并真实重跑的物理结果保持；v7是软件和说明的后继冻结。当前执行`python3 -m experiments.arithmetic_dse.platform_evidence`，加`--verify-external`只额外读取本机原始资产hash，不调用EDA。

| 项目 | 状态 | 证据 |
| --- | --- | --- |
| P2同一行current_design/false path绕过 | 关闭；修前passed，修后拒绝 | p2-before.json、sdc_revalidation.json、7项SDC回归 |
| 18份有效SDC与旧数值负例 | 当前严格方言仍接受有效归档；23份旧ns错误SDC仍拒绝 | v7核验、sdc_revalidation.json、继承v6审计 |
| 参数来源 | 44项值/单位/来源/理由/范围/变更影响；有效profile字节不改 | parameter_source_excerpts.json、源码快照中的参数侧表/决策及42项后端回归 |
| 实际产物交接 | 复用已有框架；现有/新增/缺口明确分列 | [交接覆盖表](../../../arithmetic_dse/backend/handoff_checks.md) |
| 767/772 | 767为中间报告计数，772为v6最终索引集合；中间索引hash未记录，无法恢复精确767清单 | evidence_count_explanation.json；原报告和索引不覆写 |
| GF180 wire RC | 来源部分闭合、量级校准未闭合；尚未确认为单位错误；不改系数 | gf180_wire_rc_audit.json、两份本地git提交记录、[决策D5](../../../arithmetic_dse/configs/platform_parameter_decisions_v1.md) |

SDC v2只接受每行一条命令、静态名称及固定get_ports/get_clocks集合，拒绝分号、动态替换、词拼接、续行（含注释续行）。current_design形状/唯一性和原RTL顶层必须匹配。归档Tcl不执行。运行和便携核验复用同一规则，支持方言之外明确拒绝。原v1 manifest和源快照不改成v2记录，v7另列重验。

物理结果继承链为v7 → v6（P1正确约束下的18份有效SDC及原测量）→ v5（身份和作废审计）。v5的10条旧ns尝试/23份错误SDC继续作废；原六次失败及全部费用永久保留。v6最终索引保护772文件，v5索引保护1576文件；本目录index.json只索引此次新增收尾证据和源码，不重新复制这些物理产物。

本目录保存：

- source_v7/当前38份源码、配置、说明和规划快照，previous_source/原v6当前32份源文件。
- 来源摘录包含原文件hash和行号，不复制完整PDK；相关本机资产可选外部hash核验。
- p2-before.json、sdc_revalidation.json及便携隔离破坏检查脚本/结果。破坏只发生在临时副本；即使重绑索引/后继/元数据hash，语义负例仍拒绝。
- usage_before/after.json、resources.json、command_index.json及commands/叶命令、日志、GNU time；实验支持测试计费，普通只读核验不重复计费。
- 最终静态审计和验收摘要的报告。报告中的数量/hash标识当次被检查的索引；若随后归档该报告，集合会增加。**最终集合以backend_freeze_v7.json绑定的index.json哈希为准**，不改旧报告数字迎合新计数。

参数中的uncertainty、假定transition、复核带及试跑目标是声明的工程环境，并非独立物理校准证明。GF180 wire问题在进入训练/正式评价前须闭合来源/单位，或按既有预算单独准入有限估计-提取对照；4.5Ω通孔验收不能扩大为wire已全部正确。当前仅证明冻结上下文下的流程接通，未训练D、未运行688条主矩阵、未新增算术能力或C++调度器接口。

完整处理记录及资源增量见[规划第四章步骤三§3.10](../../../../mission/lxy-plan-fix.md#step3-validator-closure)。
