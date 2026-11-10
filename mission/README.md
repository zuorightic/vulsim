# 任务与现行规划导航

**第1—3步补做验收已完成，见[§7.65](lxy-plan-fix.md#steps123-incremental-acceptance)及[增量证据](../experiments/arithmetic/evidence/step7_steps123_incremental_v1/README.md)。** 保留原验收，补齐宽消费者需求审计、10项已知位数值特征及4,666次跨语言／独立位集核对、后继协议／准入门禁和有限物理可测性。复用先前3点，新增3 synth／3 grt；共6点12阶段及24项真实单弧删除负控通过，证据实际恢复1,991文件后重放通过。原93测量依赖、58源身份、旧候选和S参数不变，18个locked_test仍锁定。累计有效原始点411，控制器已完成有界批次，无物理任务运行。第4—5步继续推进，v2拟合、覆盖／拒绝及独立精度验收仍待；第6／8步前置有效，完整联合及正式D资格仍未授予。44候选只作需求／搜索回归集，计价主线始终为通用算子函数＋S＋DAG／必要G。

**当前优先：以ASAP7 MAC32产出可复用代价模型与D端论文原型。** 先读[lxy-plan-fix.md第一章§0](lxy-plan-fix.md#mac-prototype-offline-model-plan)，目标选择与后备输出见[§7.54](lxy-plan-fix.md#step7-target-conditioned-fallback-confirmation)，最新采样及分层拟合见[§7.55](lxy-plan-fix.md#step7-three-region-sampling-plan)／[§7.56](lxy-plan-fix.md#step7-layered-operator-state-stage-plan)。用户已确认：小算子模型显式输入SDC并考虑非线性分段；必要时按位宽／位宽组建函数；D接收目标周期T，在固定L／II下，完整时序预测满足T后选择总面积最小的拆分与流水位置。若合格已评估方案均不满足T，则输出预测时序超预算最少、相同时面积较小的后备RTL并标记target_unmet，不算时序成功；缺覆盖方案不能猜价参与。前一速度优先D及其5%等速带保留历史身份，不再作为当前主选择规则。

采样改为按包含被测算子的功能数据路径最小有符号setup slack除以T分三区：r<−10%、−10%≤r≤+10%、r>+10%，每区3点为目标，定位运行在内每源最多13个不同目标，重复目标不重跑。参考落点为−50/−30/−15%、−5/0/+5%、+15/+30/+50%，不要求精确命中，缺区如实报告。ABC=SDC，模型只声明这一联合策略；所有合格目标点保留成对时延／面积标签用于条件模型，近极限5%代表点另作辅助摘要。两端平台／中间敏感是待验证假设，分段可以有跳变，不预先强制单调或连续。

当前执行以[第一章§0.12最终10步](lxy-plan-fix.md#mac-prototype-final-ten-steps)为准，函数与可测性契约见§0.3.1／§0.3.2；软件开发交错，正式残差／独立评价按冻结依赖推进，零修正通过即可采用，至少一组同策略代价对照为论文必做。最新实施见[§7.59](lxy-plan-fix.md#step7-steps123-completion)：第1—3步完成。承接§7.58的44视图／2064查询闭环，本轮补齐公共保层次RTL交接、4项not_training synth／grt物理标签资格，以及58源的角色／质量／有限执行协议。四项资格点均未满足grt setup，测量有效与时序成功分别报告。下一步为第4步有限train／validation采集；正式采集／拟合、S／G联合价格和生产D尚未完成。

读取器补正见[§7.60](lxy-plan-fix.md#step7-liberty-arc-reader-fix)／[v3后继证据](../experiments/arithmetic/evidence/step7_steps123_v3/README.md)：普通input→output此前能绕过Liberty弧检查，独立节点及Q→D入口现均逐单元严格查方向与实际弧。同8阶段全部保存标签不变，新增16项真实单弧删除及2项方向负控通过，无新物理测量；后续资格绑定修复后的源码与新收据，v2父包原字节保留。

**第4—5步正在执行，见[§7.61](lxy-plan-fix.md#step7-operator-stage45)。** 以冻结58源角色分批采正式train／validation，按实际slack自适应取点；完整新产物保存在`/home/zyrv/vulsim-artifacts/operator-conditional-20261110`并逐批归档恢复。14个locked_test仍锁定，当前未发布新合格条件函数，S／G联合价格和完整D仍待。本文此前“下一步第4步”的表述按§7.59—§7.60检查点解释，实际进度以本段及§7.61为准。

**并行完成第8步的模型消费软件接口，见[§7.62](lxy-plan-fix.md#step8-conditional-consumer-interface)。** 第5步函数文件可直接经公共请求／CostProvider加载；新增真实S/边界提供者接口、公共有限视图评估／选择／物化。TEST_ONLY下5248次结构赋值得到44视图，3目标／2064 Query、18项拒绝检查、三份入选RTL各160周期及原接口3786项兼容性检查通过；[v2证据包](../experiments/arithmetic/evidence/step8_condition_consumer_v2/README.md)收录最终接口，v1保留原检查点。正式节点函数仍须第5步独立验收，完整生产D仍须第6—7步合格S/G提供者；软件成功不转授物理价格资格。后台采集的93个冻结测量文件保持原哈希。

**第6步真实边界提供者已实现并完成有限S复用验证，见[§7.63](lxy-plan-fix.md#step6-real-conditional-boundary-provider)。** `ReusedStateBoundaryProvider` 从真实状态／placement输出三个状态所有者及clock／physical／repair独占面积、逐级launch／capture／wire、valid／控制／旁路检查和完整依赖身份。原S系数不变，先用旧train导出共享基线；实际65–67变量位缺口登记为候选后继。两个新银行×500／1500／3000ps共6点／12阶段验证通过预设复用门限，八类边界48/48；44视图×3T独立重算、18项拒绝及入选RTL周期验证通过。[新证据](../experiments/arithmetic/evidence/step6_real_boundary_v1/README.md)含原始产物归档恢复及可搬移回放。它仍是候选复用：节点测试价格为软件夹具，实际算术状态保留、最终服务／输出边界、G及完整D联合资格仍待；负hold／setup实测不被模型门限通过覆盖。

**10步增量修订已确认。** 保留第1—3步与既有采集合格数据、第6／8步实现；审计宽消费者／位连接／capture／扇出，按后继协议有限补测。第5步联合验收误差、覆盖及拒绝，44候选只作搜索验收集；独立复用保持模型参数、覆盖规则和选择器不变，见[现行10步](lxy-plan-fix.md#mac-prototype-final-ten-steps)。本次文档修订不改变正在运行的采集协议或测试角色。

原九例36条闭环后置，四平台／五档整数／43例／688条保留后续总范围，不作为原型全部前置条件。旧固定目标实验、速度优先原型及各自失败保持原身份；当前用户目标T不能由旧1431ps等数值自动填入。I可由独立通过的小算子组合计价替代。

| 阅读入口 | 用途与边界 |
| --- | --- |
| [原始任务lxy.md](lxy.md) | 原研究问题，结合现行确认解释；保持原文 |
| [第一章§0.1–§0.4](lxy-plan-fix.md#mac-prototype-scope) | 原型与通用性边界、现有模型复用、函数特征及三区有限采样；data slack分区不等于算子标签或速度极限 |
| [第一章§0.5–§0.7](lxy-plan-fix.md#mac-prototype-state-stage-models) | S／G／I职责、计费、D端给定目标T的面积选择、论文对照和独立性 |
| [第一章§0.8](lxy-plan-fix.md#mac-prototype-milestones) | P0–P6仅作依赖／交付分类；第1—3步已完成，当前执行以§0.11及§0.12为准 |
| [第一章§0.9–§0.10](lxy-plan-fix.md#mac-prototype-storage) | 资源／存储／Git规则、合并后的模型与复核入口 |
| [第一章§1—§9](lxy-plan-fix.md#current-scope-and-contract) | 当前范围、语义、接口、模板、标签、模型、评价和交付规范；唯一排程为§0.12 |
| [第四章§7.49](lxy-plan-fix.md#step7-mac-prototype-plan-update) | 历史文档合并记录；当前决策见§7.54–§7.56 |
| [第四章§7.48](lxy-plan-fix.md#step7-general-state-qualified-publication) | 最近已完成的一般状态S限定发布结果；生产价格绑定和完整D仍待 |
| [第四章§7.57](lxy-plan-fix.md#step7-target-round1-preparation) | 第一轮软件、角色／质量／容量方案及证据；不授予新壳物理标签或采样执行许可 |
| [第一章§0.12](lxy-plan-fix.md#mac-prototype-final-ten-steps) | 现行10步：增量需求／负载、精度＋覆盖＋拒绝验收、正式绑定及不变规则复用 |
| [第四章§7.58](lxy-plan-fix.md#step7-native-operator-query-software) | 原生Query／Python一致性、44视图TEST_ONLY软件RTL闭环，以及两项映射边界诊断 |
| [第四章§7.59](lxy-plan-fix.md#step7-steps123-completion) | 第1—3步完成：公共发射、4点8阶段物理资格、58源后继协议及有限批次资源计划 |
| [第四章§7.60](lxy-plan-fix.md#step7-liberty-arc-reader-fix) | 普通组合时序弧漏检修复；同8阶段、16项真实单弧删除及2项方向负控；v3增量后继 |
| [第四章§7.62](lxy-plan-fix.md#step8-conditional-consumer-interface) | 与采集交错完成第8步消费软件接口；44视图／条件函数／S边界／选择／RTL，生产资格仍待 |
| [第四章§7.63](lxy-plan-fix.md#step6-real-conditional-boundary-provider) | 第6步真实S提供者、六点有限复用验证与完整联合价格的剩余边界 |
| [第四章§7.65](lxy-plan-fix.md#steps123-incremental-acceptance) | 修订后第1—3步补做验收：需求／消费者特征、后继协议／门禁、6点12阶段物理回放及便携证据 |
| [archive/README.md](archive/README.md) | 旧规划追溯，不能从旧“下一步”续作 |

## 当前已有成果与下一步

已有参数化乘法模板、固定C、43例整图／周期基础、四平台后端、局部算子模型及真实数据。较新ASAP7包有12类合格grt组件，含8／16／32位完整／低位乘法和8／16／32／64位加法；其精确目标／形状／capture域不等于任意负载或新周期均覆盖。原始／half／quarter候选、实际阶段和typed状态查询、共享链、验证和Ledger继续复用。

最新S发布见[证据包](../experiments/arithmetic/evidence/step7_general_state_v1/README.md)：新54项独立一次性评价通过，三所有者功能状态／控制面积的grt中位／P95为0.33944%／1.09599%、0.48657%／0.90230%、0.04684%／0.17216%，八类边界72／72。它排除shared clock／physical／root repair，只覆盖登记合成银行及九精确周期，生产绑定仍为false；原失败、参数、50ps reserve及已消费测试封存。不能把不同模型的周期／边界直接拼接，或重复叠加新S与旧native总价。

P0静态部分得到3候选、5248次级分配、44合法视图、19形状／57粗负载描述；§7.52补齐63项精确位映射。软件算术／周期前检及§7.51的10点／20阶段／52路径诊断均保留原身份。正式模型采用节点独立最大时延与同一实现的组合面积，服务／连线／状态／时钟边界分别计费；不能把Q→D中的节点段自动当作节点最大值。

机器配置revision4及第一轮协议保留当时字节；现行[后继协议](../experiments/arithmetic_dse/configs/operator_collection_protocol_v2.json)revision4冻结30 train／14 validation／14 locked_test，源清单与资源方案见[第1—3步证据](../experiments/arithmetic/evidence/step7_steps123_v2/README.md)。用户已确认[统一保层次策略后继](../experiments/arithmetic_dse/configs/operator_boundary_policy_v2.json)，公共body／模块定义桥接及有限mapped银行／常量／直通／独立端点资格已完成。下一步按真实采样器请求准入最多12个train／validation源目标的小批次，再依耗时／容量及缺区调整后续批次；正式放行文件和完整产物持久恢复仍须落实。不无条件执行原87×13或新58×13全表，TEST_ONLY价格不进入正式D，最终PPA及已消费test不调参／重选。

## 历史阅读与文档整理

本目录现行入口只保留本导航、原始任务和修订计划。八份重复交接／草案已经合并并删除活动副本，迁移表见[第一章§0.10](lxy-plan-fix.md#model-reuse-and-evidence-index)。冻结证据及源快照中的旧文件名继续解释当时版本，不修改它们的字节或哈希。

第一章是现行方法和规范；第二章按A／B／C归档旧技术／执行规划、旧推进及原修订审查；第三章说明结论当前有效性，第四章保留实施验收。旧九步及旧“下一步”不作当前命令，第1—3步完成，下一步见第一章§0.11和§0.12第4步。第四章§7.1–§7.48及原模型协议中的“当前／下一步／采集中”均按对应日期解释，不是本轮执行命令。§7.49–§7.52的速度优先／仅近极限表述也按历史决策解释；当前采样／模型／D策略以§0及§7.54–§7.56为准。新工作引用写全文件、章、节号、版本，优先使用稳定锚点。

原冻结／证据不因文档归并而改写，archive仅追溯；现行代码替换建立明确后继。§7.49只记录文档修订；§7.50–§7.52的物理诊断保持not_training；§7.54–§7.56记录现行决定。§7.57完成本轮软件和协议，不启动新物理优化、正式训练或独立模型标签评价。旧10点扫描及其冻结证据仍只解释旧协议。小算子拟合独立节点operator_delay_ps／组合面积；data slack只用于离线取点及联合验证，旧Q→D标签不能直接改名使用。
