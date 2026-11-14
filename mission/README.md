# 任务导航与阅读边界

**当前执行：[通用模型扩展、自动拆分与九案例ABCD计划](lxy-plan-fix.md#general-model-expansion-plan)，工作包为W1—W8。** 用户已将目标从MAC32原型十步，推进到扩展／纠正可复用代价模型，使MAC32及八个扩展案例都能自动拆分、选择流水位置、生成RTL并统一跑ABCD后端对比。原十步和配套原型规范已[归档](archive/lxy-ten-step-stage-20261113.md)，尚未通过的子域和联合资格迁入新计划，未改判完成。

主线保持：**基础算子共享函数→S状态／边界与shared→G区域／DAG组合→候选总时序／面积→自动拆分及寄存器位置→RTL→冻结后的后端评价。** 同算子的不同位宽共用参数，T是数值输入；D选择中不调用Yosys／ABC／OpenROAD／OpenSTA，不读候选实测价格，不按案例／精确形状／精确T查价。离线可结合匹配源码和物理产物研究机制，再用发射前可计算特征拟合与验证。

## 现行入口

| 文件／章节 | 用途与边界 |
| --- | --- |
| [原始任务lxy.md](lxy.md) | 原研究问题与ABCD归因要求；原文保持 |
| [现行计划：目标与九案例合同](lxy-plan-fix.md#general-model-expansion-plan) | MAC32＋512位Add、128位Mul、16lane点积、Horner、Barrett、Karatsuba、Montgomery、8点NTT；首轮语义和有限T／L已逐项确认 |
| [模型、选择及数据合同](lxy-plan-fix.md#general-model-fixed-contract) | 同算子同模型、S／shared／G唯一归属、D排序、拒绝、数据与质量门槛 |
| [W1—W8唯一排程](lxy-plan-fix.md#general-model-work-packages) | 需求、宽软件／拆分、算子、S、G、独立／联合、MAC32闭环、八例／复用；软件与模型工作交错 |
| [ABCD与同策略代价归因](lxy-plan-fix.md#general-model-experiment-protocol) | 公平比较、冻结后测量、完整setup Tmin／频率、hold、覆盖和费用；最终PPA不反馈重选 |
| [起点状态与里程碑](lxy-plan-fix.md#general-model-status-and-milestones) | 当前失败、最近可验收交付及并行顺序；不从历史“下一步”续作 |
| [资源／Git／变更](lxy-plan-fix.md#general-model-resources-and-delivery) | 延续共享Ledger与现行并发，准确有限批次，临时工具外置，配套RTLzz子模块 |
| [共同需求细目](lxy-eight-workloads-audit.md) | 九案例共同特征、逐例缺口、生产绑定快照与后继证据；作为需求附件，不另排一套步骤 |
| [S机制记录](lxy-S-control-mechanism-plan.md) | 旧只读归因及S因素后继的实际证据；后续按W4，不把旧0新EDA范围扩大解释 |
| [归档导航](archive/README.md) | 原十步与更早规划，只作追溯 |

**版本与顺序：** [共同模型先审计／开发，应用滚动接入，最终统一冻结](lxy-plan-fix.md#general-model-shared-version-rollout)。阶段试跑可先交付；最终九例主表须在同一冻结模型包／选择器下重新选择，不为每例维护专用S／G。共同版本扩域要回归已有声明域，旧验证／测试不能反复用于选模。

## 当前起点与下一交付

[§7.96及本轮证据](../experiments/arithmetic/evidence/common_model_repair_v1/README.md)记录72个物理点完成、0物理重跑，1427次真实参数价格／162次G特征及505实际placement消费检查通过。窄／宽Mul已使用一套共享参数并保持有限验证精度；Add最后留出时延5.41%通过而面积15.88%失败；G宽域改善，零压缩短重叠train仍时延30.37%／面积21.80%；S新银行native_valid／input_valid仍31.17%／32.24%，保护也有漏点。**当前新价格未发布，公共D和原49项冻结依赖不改，20个其余算子独立源继续锁定。**

**2026-11-14 W1/W2软件交付：** 九例数学语义及首轮有限T／L已由用户逐项确认，[机器合同与未分级源码](../experiments/arithmetic/WORKLOADS.md)已登记。公共前端→通用乘法块展开／保进位加减拆分→有限beam→状态物化→诊断RTL贯通九例，64声明结构／502实际放置／48192周期全部通过；19组针对性诊断另完成6144次真实宽Query跨语言核对与1472次G整数替换检查。实际共同需求、原预算失败、完整压缩图／状态／RTL及无EDA回放见[证据](../experiments/arithmetic/evidence/workloads_software_v1/README.md)与[§7.100](lxy-plan-fix.md#nine-workload-W1W2-software)。Montgomery两个100000扩展触限保留，200000有限后继六组全部通过。

**2026-11-14 W2公共所有者／提供者／RTL后继：** [§7.101](lxy-plan-fix.md#workload-common-owners-W2)与[可回放证据](../experiments/arithmetic/evidence/workload_owners_v2/README.md)接通实际图／级放置／状态→宽Query v2→唯一算子／G所有者→公共provider→相同所有者RTL。九例64结构／502放置在新路径完成48192周期仿真；加固后的提供者重新导出并逐项核对RTL／状态／bench完全相同后继承收据。486932次算子整数求值、22500次G替换、6144条历史Query／Core回归和4096组L=1多角色向量通过。121733个算子、5625个G及12264个功能所有者均保留实际边界；多消费者／carry／selector不能被删去以迁就旧模型。

W1本轮登记及W2公共软件链路已完成本轮验收，模型物理资格继续按W3—W6推进。当前完整阶段明确cost_uncovered；S/shared、相关根G、新消费者及功能逻辑不回退静态价格，未按诊断价选择D。已有公共接口、标签、真实S提供者、旧505放置和历史MAC32 ABCD继续复用。下一项结合实际需求推进W3—W5的train数值条件与源码机制归因，正式价格、独立及完整阶段按W6冻结依赖；首个集成里程碑仍是MAC32三级L=3、500／750／1000ps的新D与ABCD，然后按共同能力逐例完成八个扩展实验。

本轮改动仍未提交，包含主仓库和RTLzz子模块新增C++。若提交，须先在子模块提交并保证对应提交可获取，再更新主仓库引用。提交不能把诊断候选改为已发布模型，原模型修复核查见[§7.97](lxy-plan-fix.md#source-guided-common-model-repair)。

## 历史与证据阅读

`lxy-plan-fix.md`第一章是唯一现行计划；第二、三章保留更早规划／修订，第四章保留实施／验收并继续追加。原十步第一章已迁入[阶段归档](archive/lxy-ten-step-stage-20261113.md)，原28个显式锚点保留归档跳转，模型和证据链接仍可追溯。历史文字中的“现行／唯一／下一步”、第几步、44视图、L=2、按位宽分组及旧额度只解释当时版本，不能覆盖W1—W8或同算子共享函数要求。

本次阶段切换不改机器协议、参数、数据角色、freeze及已有物理结论。原四平台／五档整数／除法浮点／43例／688条等范围保留历史身份，不作为本轮九例前置。旧已消费测试和最终PPA不回流拟合，软件、组件模型、完整阶段及应用物理效果分别验收。

原十步的主要证据仍从实施记录访问：第1—3步增量验收[§7.65](lxy-plan-fix.md#steps123-incremental-acceptance)、节点限定发布[§7.70](lxy-plan-fix.md#step5-bounded-operator-release)、G融合与新D[§7.81](lxy-plan-fix.md#G-reduction-fusion-successor)、三级MAC32实测[§7.83](lxy-plan-fix.md#MAC32-L3-ABCD-background)、通用块流水[§7.86](lxy-plan-fix.md#common-block-pipeline-first-package)、共享模型修复[§7.96](lxy-plan-fix.md#common-narrow-wide-model-repair)。本次归档及新排程见[§7.98](lxy-plan-fix.md#general-model-plan-migration)。
