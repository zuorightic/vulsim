# 任务与现行规划导航

**当前优先：以ASAP7 MAC32产出可复用代价模型与D端论文原型。** 先读[lxy-plan-fix.md第一章§0](lxy-plan-fix.md#mac-prototype-offline-model-plan)，目标选择与后备输出见[§7.54](lxy-plan-fix.md#step7-target-conditioned-fallback-confirmation)，最新采样及分层拟合见[§7.55](lxy-plan-fix.md#step7-three-region-sampling-plan)／[§7.56](lxy-plan-fix.md#step7-layered-operator-state-stage-plan)。用户已确认：小算子模型显式输入SDC并考虑非线性分段；必要时按位宽／位宽组建函数；D接收目标周期T，在固定L／II下，完整时序预测满足T后选择总面积最小的拆分与流水位置。若合格已评估方案均不满足T，则输出预测时序超预算最少、相同时面积较小的后备RTL并标记target_unmet，不算时序成功；缺覆盖方案不能猜价参与。前一速度优先D及其5%等速带保留历史身份，不再作为当前主选择规则。

采样改为按包含被测算子的功能数据路径最小有符号setup slack除以T分三区：r<−10%、−10%≤r≤+10%、r>+10%，每区3点为目标，定位运行在内每源最多13个不同目标，重复目标不重跑。参考落点为−50/−30/−15%、−5/0/+5%、+15/+30/+50%，不要求精确命中，缺区如实报告。ABC=SDC，模型只声明这一联合策略；所有合格目标点保留成对时延／面积标签用于条件模型，近极限5%代表点另作辅助摘要。两端平台／中间敏感是待验证假设，分段可以有跳变，不预先强制单调或连续。

最新实施见[§7.57](lxy-plan-fix.md#step7-target-round1-preparation)：第一轮完成真实消费者／捕获壳、90源／8640次RTL比较、generic FF／常量／直通端口检查、严格读取软件和负控、三区13点纯决策器，以及87源角色／质量协议和3源6点容量方案。[§7.52](lxy-plan-fix.md#step7-fast-prototype-characterization-protocol)的旧诊断保持原身份。新壳物理端点资格、实际EDA采样执行器及容量准入仍待，正式采样／拟合、S绑定／G联合验收和生产D未完成。剩余六步见[§0.11](lxy-plan-fix.md#mac-prototype-remaining-work)。MAC32是首个验证载体，模型、模板和查询按可复用接口设计。

原九例36条闭环后置，四平台／五档整数／43例／688条保留后续总范围，不作为原型全部前置条件。旧固定目标实验、速度优先原型及各自失败保持原身份；当前用户目标T不能由旧1431ps等数值自动填入。I可由独立通过的小算子组合计价替代。

| 阅读入口 | 用途与边界 |
| --- | --- |
| [原始任务lxy.md](lxy.md) | 原研究问题，结合现行确认解释；保持原文 |
| [第一章§0.1–§0.4](lxy-plan-fix.md#mac-prototype-scope) | 原型与通用性边界、现有模型复用、函数特征及三区有限采样；data slack分区不等于算子标签或速度极限 |
| [第一章§0.5–§0.7](lxy-plan-fix.md#mac-prototype-state-stage-models) | S／G／I职责、计费、D端给定目标T的面积选择、论文对照和独立性 |
| [第一章§0.8](lxy-plan-fix.md#mac-prototype-milestones) | P0–P6依赖与交付：已有P0，后续按新采样／标签协议、S和G依赖推进 |
| [第一章§0.9–§0.10](lxy-plan-fix.md#mac-prototype-storage) | 资源／存储／Git规则、合并后的模型与复核入口 |
| [第一章§1–§12](lxy-plan-fix.md) | 通用语义、区域、模板、调度、后端、全任务及版本规则；当前与旧固定目标／速度优先协议的边界见§0 |
| [第四章§7.49](lxy-plan-fix.md#step7-mac-prototype-plan-update) | 历史文档合并记录；当前决策见§7.54–§7.56 |
| [第四章§7.48](lxy-plan-fix.md#step7-general-state-qualified-publication) | 最近已完成的一般状态S限定发布结果；生产价格绑定和完整D仍待 |
| [第四章§7.57](lxy-plan-fix.md#step7-target-round1-preparation) | 第一轮软件、角色／质量／容量方案及证据；不授予新壳物理标签或采样执行许可 |
| [archive/README.md](archive/README.md) | 旧规划追溯，不能从旧“下一步”续作 |

## 当前已有成果与下一步

已有参数化乘法模板、固定C、43例整图／周期基础、四平台后端、局部算子模型及真实数据。较新ASAP7包有12类合格grt组件，含8／16／32位完整／低位乘法和8／16／32／64位加法；其精确目标／形状／capture域不等于任意负载或新周期均覆盖。原始／half／quarter候选、实际阶段和typed状态查询、共享链、验证和Ledger继续复用。

最新S发布见[证据包](../experiments/arithmetic/evidence/step7_general_state_v1/README.md)：新54项独立一次性评价通过，三所有者功能状态／控制面积的grt中位／P95为0.33944%／1.09599%、0.48657%／0.90230%、0.04684%／0.17216%，八类边界72／72。它排除shared clock／physical／root repair，只覆盖登记合成银行及九精确周期，生产绑定仍为false；原失败、参数、50ps reserve及已消费测试封存。不能把不同模型的周期／边界直接拼接，或重复叠加新S与旧native总价。

P0静态部分得到3候选、5248次级分配、44合法视图、19形状／57粗负载描述；§7.52补齐63项精确位映射。软件算术／周期前检及§7.51的10点／20阶段／52路径诊断均保留原身份。正式模型采用节点独立最大时延与同一实现的组合面积，服务／连线／状态／时钟边界分别计费；不能把Q→D中的节点段自动当作节点最大值。

现行配置为[model_target_prototype_v1.json](../experiments/arithmetic_dse/configs/model_target_prototype_v1.json) revision4，首轮协议为[model_target_round1_v1.json](../experiments/arithmetic_dse/configs/model_target_round1_v1.json)，三区执行细则为[model_three_region_scan_v1.json](../experiments/arithmetic_dse/configs/model_three_region_scan_v1.json)。[首轮小证据](../experiments/arithmetic/evidence/step7_target_round1_v2/README.md)保留源、实际功能验证及generic投影回放。下一步完成mapped语义端口／银行别名与实际采样执行器，对3源6目标方案做有限容量准入，取得物理读取资格后重估正式时间／存储并分批采集；随后按“小算子冻结→S复用／必要NNLS及独立边界→G零修正／必要组合残差→独立完整阶段验收→D”推进。选择阶段PPA为0，完整MAC最终PPA及旧已消费test不得用于调参或重选。

## 历史阅读与文档整理

本目录现行入口只保留本导航、原始任务和修订计划。八份重复交接／草案已经合并并删除活动副本，迁移表见[第一章§0.10](lxy-plan-fix.md#model-reuse-and-evidence-index)。冻结证据及源快照中的旧文件名继续解释当时版本，不修改它们的字节或哈希。

计划第二章为旧推进记录，历史正文保持；第三章记录规划修订，第四章记录实际实施与验收。第四章§7.1–§7.48及原模型协议中的“当前／下一步／采集中”均按对应日期解释，不是本轮执行命令。§7.49–§7.52的速度优先／仅近极限表述也按历史决策解释；当前采样／模型／D策略以§0及§7.54–§7.56为准。新工作引用写全文件、章、节号、版本，优先使用稳定锚点。

原冻结／证据不因文档归并而改写，archive仅追溯；现行代码替换建立明确后继。§7.49只记录文档修订；§7.50–§7.52的物理诊断保持not_training；§7.54–§7.56记录现行决定。§7.57完成本轮软件和协议，不启动新物理优化、正式训练或独立模型标签评价。旧10点扫描及其冻结证据仍只解释旧协议。小算子拟合独立节点operator_delay_ps／组合面积；data slack只用于离线取点及联合验证，旧Q→D标签不能直接改名使用。
