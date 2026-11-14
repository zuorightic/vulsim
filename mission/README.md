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

W1本轮登记及W2公共软件链路已完成本轮验收，模型物理资格继续按W3—W6推进。当前完整阶段明确cost_uncovered；S/shared、相关根G、新消费者及功能逻辑不回退静态价格，未按诊断价选择D。已有公共接口、标签、真实S提供者、旧505放置和历史MAC32 ABCD继续复用。W3—W5本轮结果与尚未解决的失败见下段，正式价格、独立及完整阶段按W6冻结依赖；首个集成里程碑仍是MAC32三级L=3、500／750／1000ps的新D与ABCD，然后按共同能力逐例完成八个扩展实验。

**2026-11-14 W3／W4／W5后继：** [§7.102](lxy-plan-fix.md#W345-centered-mechanism-successor)与[可回放证据](../experiments/arithmetic/evidence/common_centered_v1/README.md)已完成train恒定／近恒定列修复、保留中心尺度的Python／C++消费、149个算子／G点及270条S路径机制归因。12个Add物理点全完成、0失败／重跑，其中有效新验证9点、交换等价复测3点：原13+9漏去重，与train的9+13等价，已撤销新验证职责，参数不变补测19+7。有效新验证面积7.03%／8.87%、时延5.81%／8.80%通过；旧11+7面积17.71%回归失败，不能由汇总掩盖。S已消费因素银行native_valid仍21.55%，input_valid10.33%改善但旧银行仍18.07%，保护有漏点。实际流程加载Kogge–Stone，73位G又保留两个串联ALU，旧Brent–Kung／统一压缩代理遗漏这些实现差异，G失败保持。343次特征／435次价格和15项拒绝通过，新旧证据回放通过，独立标签未读、公共D未切换。

**2026-11-14 W3／W4／W5结构后继：** [§7.103](lxy-plan-fix.md#W345-flow-structure-successor)与[新证据包](../experiments/arithmetic/evidence/common_flow_structure_v2/README.md)完成实际Kogge–Stone、G缩宽边界与S分解／极性／word有限试验、真实Python／C++消费及6源18点冻结验证。新Add面积23.79%、新Mux时延median／P95为8.48%／9.46%；新G面积4.26%／8.40%，时延4.82%／16.21%，**新Add面积23.79%、G97时延17.48%、旧Mux时延19.04%及56位G面积32.93%仍失败**，每源另列。6个零压缩train源时延LOSO改善到4.75%／7.30%、73位源4.46%，但64位面积19.33%LOSO仍保留；S native_valid银行LOSO19.57%、逐路径P95 43.71%、因素回归30.10%仍失败。18点全完成、0失败／重跑，源码／证据／费用及无EDA回放已归档，独立标签未读、公共D未切换。

**2026-11-14 W3／W4／W5合法门／分支v5：** [§7.104](lxy-plan-fix.md#W345-legal-cover-branch-successor)与[便携证据](../experiments/arithmetic/evidence/common_branch_load_v5/README.md)核实实际dont-use规则禁用旧参考HAxp5，新增合法单输出门覆盖、Add／Mux数值T响应和服务／native／reset分支。Add非train等价已消费32点面积9.11%／19.40%，但17+9为22.45%、11+7为15.59%、旧带消费者47+63为16.90%；旧Mux两源时延17.49%／26.56%仍失败，96位源27.56%。G合法覆盖候选未胜出，v4参数及G97／G56／train64位失败保持。S native_valid银行LOSO18.93%／27.18%、raw逐路径P95 39.35%、因素回归21.89%仍失败，全零银行26.74%。459条特征／459条实际价格、15项拒绝及无文件读取／无子进程推理回放完成；0新EDA、20独立源未读、公共D未切换。

**2026-11-14 W3／W4／W5重缓冲／成对因素v6：** [§7.105](lxy-plan-fix.md#W345-rebuffer-context-successor)与[便携证据](../experiments/arithmetic/evidence/common_rebuffer_context_v6/README.md)核对OpenROAD实际placement关闭initial sizing并执行fullyRebuffer，保存逐负载时序预算／面积回收源码与train证据。新增4个reset／极性配对train银行、12点全完成，0失败／重跑；17银行／57实现的成对LOSO native_valid银行17.54%、raw逐路径P95 38.14%仍失败，已消费因素回归24.54%较v5退化，另新银行3T被旧支持域拒绝。66项有限比较中Add／Mux／G面积保留原参数；G时延97位源17.48%→13.51%，但48位稀疏源12.76%→16.35%。471特征／471价格请求跨语言一致，其中465提供诊断价格；312真实路径及312删除Liberty弧负例、推理无文件／无子进程回放通过。20独立源未读，公共D未切换。

**2026-11-14 W3／W4／W5单向负载压力v7：** [§7.106](lxy-plan-fix.md#W345-load-pressure-successor)与[便携证据](../experiments/arithmetic/evidence/common_load_pressure_v7/README.md)接通语义结构→共享enable函数→预计压力／松弛代理→valid函数，13 fold逐次排除整个reset pair再拟合上游，228条上下文特征及训练摘要核对通过。enable成对LOSO银行7.83%／13.95%；valid银行17.97%、原始逐路径P95 36.12%仍失败。因素回归24.54%→23.61%，旧银行17.58%→17.65%，enable旧回归略退。S重新按train数值几何推导支持，训练57/57覆盖，但留出完整实现仅33/57，不授予未知银行资格。Add／Mux／G新静态形式未胜出，参数与v6相同；471特征／价格跨语言一致，其中468提供诊断价格，22项拒绝及缺上下文安全报错通过，21项新旧测试和无I/O回放通过。0新EDA，20独立源未读，公共D未切换。

**2026-11-14 W3／W4／W5语义扇出与S接口对照v8：** [§7.107](lxy-plan-fix.md#W345-semantic-fanout-successor)与[便携证据](../experiments/arithmetic/evidence/common_semantic_fanout_v8/README.md)完成逻辑根／内部扇出矩、66项train选择及冻结回归。Add面积LOSO8.28%／13.48%，11+7回归改善至12.54%，但17+9退至29.52%、47+63带消费者退至19.63%；Mux／G参数未变。S valid银行17.94%、raw路径P9536.56%仍失败，因素回归23.61%→31.43%，新增1个保护漏点。单独登记的6点train对照全部完成、0失败／重跑：只重排reset位及相容invert，完整当前Query／特征／预测相同，而biased valid在500ps的R为261.67→439.96ps，任何共同预测至少一侧APE≥25.41%；input_valid另16.20%。结论限该局部对照，不推成全局median不可能。新源不入v8拟合，未来与父源成对留出。471特征／价格、22项拒绝、27项测试和Python／native回放通过；新增156真实路径／156删弧负例，6 synth／6 grt／24 support结清。20独立源未读、公共D不变。

下一步以§7.107逐源失败和接口信息缺失对照为准，补充S对reset分布／相容极性的语义表示，再登记通用数值描述及成对训练；同时保留Add／Mux旧域、G稀疏边界和S回归退化，继续宽深／shared与W6实际算术／完整阶段资格。W7／W8正式ABCD继续按冻结依赖。当前新增实现／证据尚未提交，包含主仓库和RTLzz新C++；若提交，须先在子模块提交并保证可获取，再更新主仓库引用。提交不把诊断候选改为已发布模型。

## 历史与证据阅读

`lxy-plan-fix.md`第一章是唯一现行计划；第二、三章保留更早规划／修订，第四章保留实施／验收并继续追加。原十步第一章已迁入[阶段归档](archive/lxy-ten-step-stage-20261113.md)，原28个显式锚点保留归档跳转，模型和证据链接仍可追溯。历史文字中的“现行／唯一／下一步”、第几步、44视图、L=2、按位宽分组及旧额度只解释当时版本，不能覆盖W1—W8或同算子共享函数要求。

本次阶段切换不改机器协议、参数、数据角色、freeze及已有物理结论。原四平台／五档整数／除法浮点／43例／688条等范围保留历史身份，不作为本轮九例前置。旧已消费测试和最终PPA不回流拟合，软件、组件模型、完整阶段及应用物理效果分别验收。

原十步的主要证据仍从实施记录访问：第1—3步增量验收[§7.65](lxy-plan-fix.md#steps123-incremental-acceptance)、节点限定发布[§7.70](lxy-plan-fix.md#step5-bounded-operator-release)、G融合与新D[§7.81](lxy-plan-fix.md#G-reduction-fusion-successor)、三级MAC32实测[§7.83](lxy-plan-fix.md#MAC32-L3-ABCD-background)、通用块流水[§7.86](lxy-plan-fix.md#common-block-pipeline-first-package)、共享模型修复[§7.96](lxy-plan-fix.md#common-narrow-wide-model-repair)。本次归档及新排程见[§7.98](lxy-plan-fix.md#general-model-plan-migration)。
