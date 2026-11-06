# 任务与现行规划导航

当前优先交付已由用户确认为[ASAP7 M2九例36条完整闭环](asap7-m2-closure.md)，完成该范围的步骤七模型／原生选择、步骤八实测及步骤九复现审计后，再由用户决定扩展拆分范围还是平台；不预先安排扩展次序。决策与当前实施见[第四章§7.17](lxy-plan-fix.md#step7-asap7-m2-priority)。原四平台／五档／43例／688条保留后续总范围，不作为九例阶段交付的全部前置条件。

**当前结果入口为[§7.48：一般状态S新独立通过与限定组件发布](lxy-plan-fix.md#step7-general-state-qualified-publication)。** 新54独立全部完成，原始回放及冻结参数一次性评价通过，synth／grt八类状态边界均72／72；grt最小覆盖余量37.372788ps，三面积分项中位／P95为0.33944%／1.09599%、0.48657%／0.90230%、0.04684%／0.17216%，原20%／50%门槛保持。原三面积系数、六类边界、九目标及50ps reserve不改，全部已消费测试永久封存。[约2.47MiB发布包](../experiments/arithmetic/evidence/step7_general_state_v1/README.md)只发布ASAP7 grt合成原生银行的功能状态／控制面积和状态边界；完整378银行／756阶段／6804路径归档在build。便携／完整external／隔离／篡改、冻结训练精确复现及本组件Git视图通过，当前无本实验后台EDA／未结算任务。范围、复现及后续见[一般状态S交接](asap7-general-state-handoff.md)；生产状态价格绑定、G／I及完整D／正式36条仍未放行。

[§7.42正式目标冻结](lxy-plan-fix.md#step7-m2-numerical-target-freeze)保持：用户确认H_ref按必需data路径joint overhead最大值汇总，其他完整路径另报诊断；原公式冻结九例周期1431／1119／4528／11913／3141／4162／1253／14897／3385ps。[约0.35MiB冻结证据](../experiments/arithmetic/evidence/step7_m2_targets_v1/README.md)的生产公式／external／隔离／篡改核验通过。G受限整阶段／联合边界、I真实区间及C++完整消费者仍待后续，不由S组件发布转授资格。

[§7.41](lxy-plan-fix.md#step7-reference-raw-audit)的17／17参考采集及原始封存保持：34阶段／272路径、108付费叶及4151文件核验，前三项综合复用；原始标签／归属／SDC／RC便携回放、完整本机工具／Liberty／CTS CEC、隔离与篡改通过，[参考证据](../experiments/arithmetic/evidence/step7_reference_v1/README.md)约6.4MiB。原target-proposal保持当时待确认状态，本轮由后继冻结承接，不覆盖旧证据。17项参考不是正式ABCD36条。

[§7.40](lxy-plan-fix.md#step7-reference-cohort-admission)保留软件／标签前检和参考准入：17源×144周期／19728状态检查及九项读取负控通过，固定ABC1500ps／SDC40500ps／IO0.2T，最多4任务×4线程／每任务8GiB。真实公共VUL内部valid使能与外部无条件捕获已分开，旧读取／续作元数据失败及费用保持。[参考交接](asap7-reference-handoff.md)包含恢复父链及采后依赖；没有自动拟合、独立模型测试或目标冻结。

[§7.39：九例全部候选静态需求与计费规则冻结](lxy-plan-fix.md#step7-all-candidate-static-requirements)保持。生产与诊断共用候选枚举／分组，九例21个有序候选与旧生产图hash一致，另与当前真实C核对；K=16独立顺序检查通过。已完成108个去重合法放置视图、582次非法提案、每候选C最终实际物化状态及140种阶段需求描述的审计。[证据及复现](../experiments/arithmetic/evidence/step7_d_requirements_v1/README.md)约0.70MiB，便携／external／隔离及篡改核验通过，无新PPA或拟合。

静态诊断已列出一般语义复位、相关来源、无完整数据链、非旧离散字宽／掩码、移位补零及18通道等同时缺口。实际中间状态到66位，34组实际／42组保守区间需求保持。原[联合需求v1](../experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json)及目标绑定v2均保留原字节；v2的physical_admission_allowed=false是共同需求范围，S组件仅由§7.46–§7.48具体源／目标／容量准入与独立验收授予范围内资格，不转授G／I或正式矩阵。**下一步完善实际C++ service／native／external状态特征／所有权／条件上界价格绑定，并推进G／I合成资格；完整初始／试移／最终统一查询、D选择／RTL及正式36条仍待。** [静态需求交接](asap7-d-requirements-handoff.md)保留旧检查点，当前状态以顶部S入口为准。

[§7.38](lxy-plan-fix.md#step7-native-state-production-binding)的生产primitive＋native_state组合清单和受限状态价格消费保持：175次查询／168次实际物化与Python差0，35项拒绝及旧回归通过；[绑定证据](../experiments/arithmetic/evidence/step7_native_state_binding_v1/README.md)保持。完整D仍待实际状态、外围／联合边界、受限整阶段、真实区间、正式目标、完整初始／移动／选择与RTL资格；九例正式36条尚未开始。

[§7.37](lxy-plan-fix.md#step7-native-state-independent-publication)保留原生协议72 train／36 validation／36新独立测试及冻结参数一次性评价通过结果：grt状态面积中位6.0347%／P95 18.9229%，原20%／50%门槛不变，边界最小余量183.134460ps。原[状态发布包](../experiments/arithmetic/evidence/step7_native_state_v1/README.md)及全部原参数／域／803.206085ps边界／50ps reserve不变；144银行／288阶段／1152路径和12原生结构的发布核验保持。其production_price_binding_qualified=false是历史检查点，本轮受限消费资格另由后继记录，不改旧发布；新独立标签永久排除后继拟合／验证／调参／域选择。

[§7.35](lxy-plan-fix.md#step7-native-state-query-and-successor)保留九公共VUL原始核＋3诊断的真实状态查询、使能拓扑差异和用户确认后继路线；6银行×80周期／8240状态检查通过。整阶段需求见[草案](asap7-stage-topologies-draft.md)，尚未冻结采样或启动该部分后端。原§7.35的“36 test锁定”是当时检查点，§7.36在验证／冻结／复现后才另放行，不追改旧角色。

[§7.34：状态／边界独立通过与有界组件发布](lxy-plan-fix.md#step7-m2-state-boundary-independent-verdict)保持原结论：72 train／36 validation／36独立test全部完成，冻结参数一次性评价通过；状态总面积synth中位2.4549%／P95 6.1466%，grt为6.4017%／8.6246%，边界最小裕量105.1820ps。参数／支持域／50ps reserve未改，原12类组件保持。144份银行的便携／完整external／隔离副本／篡改核验已完成；旧失败及支持副本追溯保留。

发布及复现入口为[状态／边界证据包](../experiments/arithmetic/evidence/step7_m2_state_boundary_v1/README.md)，grt组件只覆盖原受限合成银行及精确条件；不能据“valid_chain”标签直接继承到任意原生拓扑。该独立标签已消费、永久排除后继拟合／验证／调参／域选择；新批次不回填它。联合算术／正式边界、受限整阶段价格、真实区间及有效D选择／RTL仍待完成，full_D_ready=false，九例36条未完成。旧“无后台”是§7.34发布收尾检查点；§7.35的新队列亦已完成并由§7.37发布，当前§7.38无后台EDA。

[§7.31：ASAP7发布组件接入原生D入口与九例覆盖诊断](lxy-plan-fix.md#step7-m2-native-component-integration)已完成生产模型工厂、实际阶段／capture查询及候选失败轨迹。436次12类原生查询与Python最大数值差0，14项拒绝和同节点上下文刷新通过；真实PipelineV2双Mux阶段绑定通过。原四平台250项模型检查及pipeline／reset／valid（含CIRCT）回归通过。[接口证据](../experiments/arithmetic/evidence/step7_m2_native_integration_v1/README.md)约1.64MiB，父发布模型／参数／裕量／域保持。

九例公共VUL经实际生成器进入新D入口，共21个按原政策顺序的候选尝试；全部明确cost_uncovered，共同首缺为合格状态模型，另保留控制模式和真实区间等缺口。PPA0、无新拟合／测量；1500ps仅接口诊断，不是正式目标资格。生产组件消费已接通，完整阶段计价／初始放置／移动／D选择及新D的RTL周期闭环仍需资格，不把这21条诊断写成36条完成。下一步优先补状态／边界／阶段组合与实际支持域，详见[接口清单](asap7-d-interface.md)。

[§7.30](lxy-plan-fix.md#step7-m2-mux-static-independent-verdict)记录上一版独立验收与组件发布。 原48个P4独立任务全部完成，完整原始回放后按冻结选择一次性评价通过，grt组件资格12／12；其余11类完整模型、裕量、域及F5合格证据保持，原F5整体失败不改写。本轮没有降低门槛、回调目标或重训已合格11类。

Mux独立synth时延中位／P95为1.6208%／3.0494%，grt为8.2758%／54.9834%；grt错误可行25／2112＝1.1837%、实际目标局部0／192，面积P95为0.7844%，均通过原门槛。48任务／384主标签及分路径、原192份拟合测量／768主标签的原始回放成立，验证／测试分离和冻结参数保持。[发布与证据入口](../experiments/arithmetic/evidence/step7_m2_mux_static_v1/README.md)包含可部署组件模型、范围及能力清单；状态命令仍为`python3 experiments/arithmetic_dse/model_m2_status.py`。后台已结束，没有自动后继采样。

新Mux资格仅覆盖parallel_dynamic_mux家族、2／3／4个独立同宽动态Mux、生产单银行及原精确位宽／ABC-SDC；该限制在P4测量前已登记。mixed-control新系数仍只有训练／验证，one-Mux、共享／混合算术、任意阶段及正式目标不能据本轮扩域。原生BEIR特征和候选数值核对、已发布Python查询及域外拒绝已完成，生产CostProvider阶段绑定、状态／组合、真实区间及完整D仍待后继。生产组件接口现已在§7.31接入，完整D所需资格和后续接口边界见[ASAP7 D端接口清单](asap7-d-interface.md)；九例36条尚未完成，Git由用户提交。

旧12维候选的79.0148%验证P95及48项锁定时的有限池诊断已保存在[§7.28数值检查点](../experiments/arithmetic/evidence/step7_m2_mux_validation_v1/README.md)，没有修改或回填F4／F5独立Mux数值。§7.29记录验证／冻结／原P4放行，§7.30已完成该48项独立评价并发布有据范围；旧失败和父链保持，不表示完整D／九例36条完成。

最近已完成的结果见[§7.26](lxy-plan-fix.md#step7-m2-F5-independent-verdict)：F5完整56／56，原模型独立synth12／12、grt11／12，Mux时延P95为98.573%超过75%，发布为空。488行F5标签和1464行原拟合标签的原始回放、便携／完整外部、无build／EDA／账本副本和篡改核验均通过，[封存包](../experiments/arithmetic/evidence/step7_m2_F5_v1/README.md)保持原结论。其余11类本次只继承该合格组件的固定数值／域与独立收据，未改写F5整包失败或单独宣称11类已构成完整D。区间后继、组合／状态、正式目标及九例36条仍待完成；Git仍由用户后续提交。

[§7.16后继模型](lxy-plan-fix.md#step7-baseline-validation-test)的80个训练＋260个验证＋235个新独立测试已全部采集。3276行训练／验证标签、1680行测试标签回放完成；基线验证synth／grt均42／42通过、重拟合字节一致，但独立测试grt41／42、synth38／42，发布清单为空。grt唯一失败是quarter/low/1/1的时延误差中位数34.2549%超过30%，并非该类错误可行门槛；原参数、门槛及已消费测试封存，不能直接改裕量重测。当前235任务后台已正常退出、账本已结算。九例模型／接口缺口审计已生成，后续采样围绕其实际必需域推进。§7.10七项保留为最终缺口，当前优先顺序由§7.17及九例清单解释；完整步骤七及688条矩阵未完成。

[第四章步骤七](lxy-plan-fix.md#step7-offline-model-acceptance)已增加逐节状态索引，历史检查点与当前入口分别说明。§7.1–§7.8完成四平台局部grt模型、12个目标上下文及有限真实原生推理／RTL周期验收，Sky130HD synth失败保留；§7.9–§7.11完成首轮67任务／588行区间数据及独立评价，grt38／42，因逐区间错误可行门槛拒绝发布，失败与父链核验已封存；§7.12的固定R负载v1批量未执行，已由§7.13的24点时钟诊断及§7.14–§7.17目标／负载后继替代，不再从旧提案续跑。24点诊断均not_training，后继575任务独立结果见上文。四平台TEST_ONLY三候选只证明机制，完整九例D联合覆盖及全任务扩域尚未完成；参数／wire RC身份与步骤三旧快照分开，详见[模型协议](../experiments/arithmetic_dse/model_protocol.md)。

后续算术拆分、代价模型和流水线工作按 [lxy-plan-fix.md 第一章](lxy-plan-fix.md) 推进。先读第一章§2“既有成果如何迁移”、§10“九个步骤”和§10.10“阶段里程碑”；[第四章步骤一](lxy-plan-fix.md#step1-wide-acceptance)的宽位宽补验及[第四章步骤二](lxy-plan-fix.md#step2-revised-acceptance)的新契约/静态表/43例生成补验已完成对应范围。[第四章步骤三](lxy-plan-fix.md#step3-platform-acceptance)的原v5验收因SDC整数除法缺陷撤回；[§3.9的v6修订](lxy-plan-fix.md#step3-sdc-correction)已修复、核对实际SDC并重跑三个ns平台后重新通过。[§3.10的v7收尾](lxy-plan-fix.md#step3-validator-closure)已关闭SDC命令边界P2并补来源/交接规则，物理结果继承v6，GF180 wire RC校准仍登记待核。[第四章步骤四](lxy-plan-fix.md#step4-interface-acceptance)已完成本步公共请求/原始Mul与FP区域/固定成本及保护验收；half/quarter内部展开和D模型仍未完成。[§4.8报告类型修订](lxy-plan-fix.md#step4-report-type-review)将计数改为JSON整数，并补历史证据横幅及存储分层；v1原证据保留。[第四章步骤五](lxy-plan-fix.md#step5-mul-template-acceptance)已完成参数化Mul/新C软件与有限容量验收；ASAP7 64位grt通过，128位grt超时保留，受影响物理批量待复审。步骤六整图接入的后继状态见下方独立记录。

[步骤五收尾§5.8](lxy-plan-fix.md#step5-closure-review)为当前后继状态：位置核验、部分积覆盖／129份实际历史图回放和精确数值协议已补齐；相同双128位C实现的一次3600秒容量复测在1450.19秒完成完整后综合→grt，当前目标时序满足。原1200秒超时及费用保留，具体批次仍须按容量域和实时预算准入，不把单探针外推全部128位或A/B/C/D。核验入口为`experiments.arithmetic_dse.closure_evidence`，冻结v2继承v1。

[步骤五§5.9时序口径澄清](lxy-plan-fix.md#step5-metric-scope-review)补充当前报告读法：core_clk最小周期只统计符合OpenSTA筛选的同钟路径，整体setup slack还包含io_clk↔core_clk接口路径；批次准入读取后者及hold／覆盖，不能由前者推定整体裕量。说明冻结v3继承原v2数值，无新增EDA。

[第四章步骤六](lxy-plan-fix.md#step6-whole-graph-acceptance)完成43案例A/B/C及47诊断的整图、宽复位和RTL周期验收。ASAP7指定UDR128综合触及8GiB，F2综合命令成功但原层次端口读取器误报，软件修补后实际SDC静态核验通过；grt及四个从属控制点未完成。整图冻结v1保留失败/费用，不放行相关物理批量；D模型和其他容量域仍待步骤七及后续准入。

[步骤六§6.6复核修订](lxy-plan-fix.md#step6-width-proof-review)修复非零除数证明忽略Ite截断的P1，真实C++14例及176报告/186节点回放通过。原有电路未变，用户标题编辑保留；可编辑叙述文档读取受保护快照并报告漂移，源码/成本配置仍严格核验。当前后继whole_graph_freeze_v2保留全部旧失败和费用，本步最终验收见第四章§6.9。

[步骤六§6.7时钟复审](lxy-plan-fix.md#step6-clock-relaxation)记录UDR128原1.5ns长时间CTS修复和4小时timeout，以及100ns新诊断的正常完成：固定原1500ps ABC映射／300ps I/O、全新SDC／ODB和完整floorplan→grt，1671.49秒完成，setup+21.883ns、hold+0.671ps，覆盖完整、hold低于复核带。步骤六已按整图／安全／有限容量范围验收；§6.8说明原子案例不证明内部拆分收益。D模型、批量覆盖及688条正式评价仍待步骤七／八。

| 文档 | 作用 | 阅读边界 |
| --- | --- | --- |
| [lxy.md](lxy.md) | 原始任务要求 | 结合已确认范围及修订计划解释 |
| [lxy-plan-fix.md](lxy-plan-fix.md)第一章 | 现行范围、方法、步骤、准入和最终验收依据 | 四平台、整数8/16/32/64/128位、binary32、43案例/688条；阶段通过不等于全范围完成 |
| 同文件第二章：旧计划推进记录 | 原步骤一至五及位置补验的历史正文，章标题已改名标识 | 只证明旧版本；文中未限定版本的§号仍按旧计划解释 |
| 同文件第三章 | 新规划修订与引用迁移的已有记录 | 保留既有内容；后续步骤实施按用户要求改记第四章 |
| 同文件第四章 | 修订计划各步骤的实际实施与验收 | 步骤一、二补验已完成；步骤三物理测量以§3.9的v6单位修复重验为准，当前软件/静态核验以§3.10的v7为准，原v5三个ns结果作废；步骤四见其独立记录，仅验收原始Mul/原子FP和公共固定成本路径；分别列明软件/原生、组合/流水及后端阶段边界，不能当作后续模板/模型或全任务通过 |
| [archive/lxy-plan-v1-single-platform.md](archive/lxy-plan-v1-single-platform.md) | 已归档的单平台旧计划及原推进记录 | 保留原字节用于追溯；后续任务不从其未完成步骤接着执行 |
| [算术实验README](../experiments/arithmetic/README.md) | 实验目录入口及旧契约说明 | 先读顶部的现行规划与历史边界提示 |

引用迁移的逐项对照见 [修订计划第三章§2](lxy-plan-fix.md#plan-reference-migration)。处理分三类：

1. **入口或同义原则**：可更新到fix第一章相应章节，不由此宣称新增范围通过；如L/II、共享链、连续事务和区域不变量等原则，保留原实现适用范围。
2. **成本、案例、目标、模型或范围已变**：先实现对应新版本并验收，再引用fix作为满足新规则的证据。仅把文件名/节号替换掉不会使旧行为符合新契约。
3. **历史规则和证据**：保留旧引用、版本和哈希；可在非冻结入口解释它对应fix第二章的哪段历史，不能把历史结果改写成fix第一章验收。

`experiments/arithmetic_dse/backend/README.md`、`experiments/arithmetic/regions_v1.md`、`mul_split_v1.md`、`placement_v1.md`及证据目录中的说明已进入相关冻结。源码和回归里的旧规则注释也可能随源文件被哈希保护。现行实现可按新计划第一章§11原位替换并建立后继freeze；历史核验显式消费原快照，不能以旧哈希为由永久保留旧活动入口。用户要求最终清理被替代实现，临时依赖及退出条件见 `experiments/arithmetic_dse/configs/implementation_migration_v1.json`。

新工作引用写全“文件＋章＋节号＋标题＋适用实现/配置版本”；需要精确定位时再附当时行号。fix各章都有重复节号，单写“§7.2”或“步骤五完成”容易误读。优先使用章节标题或稳定锚点，行号只作辅助，文档增补后应重新核对。

一次推进记录至少说明：对应fix第一章哪项要求、继承的旧版本、实际修改及验收范围、仍未完成项、资源和证据来源。新计划已写出、新文档已链接、旧回归通过，均不能单独作为新契约通过的依据。

本导航及引用审计不修改编译器、实验配置、预算或历史冻结，不授权物理调用，也不表示M1或后续阶段已经验收。

步骤六Git交付追加见第四章§6.10及[交付复核包](../experiments/arithmetic/evidence/step6_git_delivery_v1/README.md)：17份父链历史manifest已通过局部忽略规则放行并定向暂存，按实际Git可纳入文件集合、无根build／大产物且PATH为空的副本核验通过。原v2冻结不变。
