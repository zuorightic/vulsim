# 任务导航与阅读边界

**现行规划统一放在[lxy-plan-fix.md第一章](lxy-plan-fix.md#local-request-plan)：将当前已冻结的D迁移至Nangate45，仅验证MAC32、Add512、Mul128三例；ASAP7九例按原冻结身份及最新授权结清。** 迁移沿用候选／位置策略、预算／等效T、排序与RTL流程，按[N1～N8](lxy-plan-fix.md#local-request-steps)先检验缩放，再对失败部分校准或重拟合。Nangate45与ASAP7使用相同的离线共享函数建模方式，同类跨位宽共享参数，编译期只用图／请求特征与冻结模型，禁止精确实测查表及在线后端反馈，详见[§1.13](lxy-plan-fix.md#nangate45-migration-contract)。

R1～R5（含R1a）算法修复及原审查要求已移入[第二章暂缓归档](lxy-plan-fix.md#deferred-D-algorithm-repairs)，以后有时间再处理，不作为迁移前置，不设置另一D称谓。已有软件产物见[已完成前置归档](lxy-plan-fix.md#completed-local-request-archive)。已知限制和模型失败保留[诊断身份](lxy-plan-fix.md#local-request-document-status)，流程可运行不等于精度或完整资格通过。

ASAP7现行物理矩阵仍为九例各两档L、37组T／L，复用9份A参考、验收111条BCD及37条归因；A单列初版请求／Tmin，原19组／76条身份保留。Nangate45仅三例：MAC32取L2／L3，Add512、Mul128取L2／L4，每L两个T，共12组目标、3份A＋36条BCD主记录，另存12条软件同池归因，不为归因强制增加独立物理任务。本后端A／T另行定标，拟合只覆盖三例实际需求，不复用ASAP7实测值，不复刻九例全矩阵。

代码从2026-11-15恢复后的v10 test基线出发：主仓库`672df3e`、RTLzz `28a4f1d`，对应用户引用的MAC32／Add512／Mul128后端结果。当前新增独立的软件预算／等效T入口，保留v10默认入口作对照；此前撤下的局部预算、逐模块ABC及采样代码仍在恢复前备份中，没有恢复。原W1—W8及第三至五章中的“下一步／必须／唯一排程”只用于追溯，不自动续跑；模型未达精度、关键源退化和独立／组合资格未通过的事实继续保留。

## 当前入口

2026-11-17已按用户“G算作通过”授权完成[N5／N6小组合与完整评分接入](lxy-plan-fix.md#nangate45-N56-complete)：11源／22个Nangate45 grt点、S／shared及本后端H_char冻结、六种案例／L的900个所有者与44份完整评分快照回放、9项身份负控和六份192周期RTL验证均完成。[独立模型配置](../experiments/arithmetic_dse/configs/nangate45_frozen_d_n56_v1.json)可供有限三例实验使用，推理为离线共享函数，禁用文件I/O与子进程检查通过。[小型模型与证据](../experiments/arithmetic/evidence/nangate45_n56_v1/README.md)保留全局T输入基线，并补做同一已消费留出组合的局部预算／tau评价：完整周期验证2.99%／24.83%、测试5.09%／23.00%，总面积验证2.04%／3.39%、测试0.99%／2.15%的median／P95均通过；参数不变、无新后端或独立测试宣称。root_repair面积、验证Add本体及G嵌入仍有未过项，五类应用状态规模外推，保持诊断资格。原G本体放行不扩展为新分项放行。完整产物在`/home/zyrv/vulsim-artifacts/nangate45-n56-20261117-v4/`，22 synth／22 grt／169 support全部结清，原ASAP7在运任务与冻结输入保持；未启动N7应用A／BCD，R1～R5继续暂缓。

2026-11-17 23:44～23:46完成ASAP7九例进度核验，完整表及耗时估计见`/home/zyrv/vulsim-artifacts/old-D-progress-20261117-six-by-three-v1/`：9份A已冻结，111条BCD为78实测、2错误、5运行、26排队，现行软件全部ready。修复3线程执行器覆盖历史账本策略身份导致的零EDA启动拒绝，33项启动保留日志后恢复排队；当前父PID2000512，已验证两个新任务实际以3线程进入综合，四个旧任务继续2线程，共六并行。另有10条归因与26条BCD一同等待，实际待启动36任务。当前队列结清估计18～30小时，保守预留36～48小时；不保证全部物理成功或时序达标。Karatsuba L8／1400ps C本轮达到6小时grt时限，作为当前第二条错误保留；原Mul128 L4／1200ps C内存错误保留。

2026-11-17 22:52按用户要求保持ASAP7旧D最多六并行，将交接时尚未启动的38个后端任务改为每工具3线程；六个在途任务继续使用原2线程，完成后自然补位。有效控制器为`/home/zyrv/vulsim-artifacts/old-D-six-by-three-20261117-v1/threads3.py run`，PID1965588，实时入口为同目录`status.json`；22:54运行核验通过，旧D活动六个、全局活动七个。Dot16 L5／1700ps B／C的30／0.50设置保留，D继续引用已有同设置实测；RTL、时钟、时限及其它物理条件保持。准入、零EDA预检和进程核验见该目录，资源调整记录见第一章§1.12.11。

2026-11-17 22:09按用户要求将Dot16 L5／1700ps这一行的BCD统一为利用率30、density 0.50：B／C直接更新原排队任务配置并保留编号，D使用已完成的1698.698819ps／37692.784620µm²、hold WNS+21.244867ps结果，主表行内注明设置。最新完整对比位于`/home/zyrv/vulsim-artifacts/old-D-progress-20261117-matched-dot16-v1/`；当前有效控制器为`/home/zyrv/vulsim-artifacts/dot16-L5-T1700-BCD-core30-density050-20261117-v1/cohort.py`，同目录`status.json`为实时入口。六并行／每工具2线程及其它实验条件保持，说明与验收见第一章§1.12.10。

2026-11-17 21:45～21:47完成ASAP7九例只读进度审查，结果快照位于`/home/zyrv/vulsim-artifacts/old-D-progress-20261117-2145-v1/`：9份A参考可用，现行111条BCD为75条实测、2条错误、5条主记录后端运行、29条主记录排队，软件等待为0；相较20:47新增Dot16 L4／1700ps B／D及2100ps B。1700ps旧D的Tmin为1575.183617ps，但hold WNS为−3.530620ps，不能记为完整时序收敛。六个活动后端由五条BCD和一条same_policy_static归因组成，每工具2线程；其它平台不在本次审查范围。

2026-11-17 20:57按用户追加授权将旧D后端从5增至6并行，每工具仍2线程、全局共享9槽，详见第一章§1.12.9。有效控制器为`/home/zyrv/vulsim-artifacts/old-D-six-backends-20261117-v1/six.py`，实时状态见同目录`status.json`，旧early-BC／repair／revision目录同步更新。新增第六槽已启动Karatsuba L8／1750ps B；原五个后端任务身份保持，B／C提前入队及去重继续生效，RTL／时钟／模型／物理条件不变。20:58核验六条活动后端均为每工具2线程；现行七项软件任务均已ready，含刚完成的NTT L16。

2026-11-17 20:28按用户追加授权启用B／C逐方法提前准入，详见第一章§1.12.8。Montgomery L32／1000ps与NTT L16／2200ps各自B、C共四条已验收并正式排队，后续整组准入引用同一任务避免重复；Montgomery L16两档已按原流程准入。有效控制器为`/home/zyrv/vulsim-artifacts/old-D-early-bc-20261117-v1/early.py`，实时状态见同目录`status.json`；旧D最多5并行／每工具2线程／全局9槽保持，两条在途求解和全部EDA子任务保留，Nangate45不受本次交接影响。

20:47补充核验：Montgomery L32两档软件已完成，1200ps的B／C也已准入，提前任务合计六条；实际整组准入已引用四条Montgomery B／C而未重复提交。旧D软件仅剩NTT L16在途，2400ps评分到46／48，2200ps B／C已独立排队。ASAP7现行111条BCD为72条实测、2条错误、5条后端运行、28条后端排队、4条待软件验收；完整37组对比与本轮审查位于`/home/zyrv/vulsim-artifacts/old-D-progress-20261117-2006-v1/`。按用户要求，本次后续审查仅覆盖ASAP7九例。

2026-11-17已完成[N4三档请求补采与时延校准](lxy-plan-fix.md#nangate45-pressure-refit)：30个新Nangate45有效点为12训练／9验证／9封存测试，参数冻结后采集新test；尝试校准Add／ADC与G时延，实际更新Add；G因旧验证16.60%未通过而保持首批函数，其余四个函数保持。Add新增封存测试为9.81%／17.96%，旧测试开发回归为4.73%／9.28%；不宣称完整模型通过。旧test仅作已消费回归，新producer按负载／时钟归组；首批ADC128单／双bank跨职责说明已勘误，原数值保留。大G三次接通失败与一个成功诊断保留且不用于拟合，v4改用较小G128五项重叠源、恢复原采样设置。[模型／误差／费用证据](../experiments/arithmetic/evidence/nangate45_pressure_refit_v1/README.md)在仓库中，完整产物在`/home/zyrv/vulsim-artifacts/nangate45-refit-20261117-v4/`。ASAP7在运实验及第二章以后归档保持，完整D仍待N5／N6，未执行N7应用A／BCD。

2026-11-17 18:06按用户追加授权将旧D重任务从3增至5并行（新增2个），每工具2线程、全局9槽。Dot16 L5／1700ps扩核心D补测与Dot16 L4／1700ps B已实际启动。独立补充调度器、授权及有效状态在`/home/zyrv/vulsim-artifacts/old-D-five-backends-20261117-v1`，详见第一章§1.12.7；原父控制器继续生成／准入，既有软件及EDA保持运行，原合同3并行只作历史。

2026-11-17 17:38已按用户授权将Dot16 L5／1700ps旧D局部拥塞补测接入共享资源等待队列，详见第一章§1.12.6。仅调整核心利用率40→30、布局密度0.65→0.50，旧D电路／请求／ABC目标保持；全局9槽、旧D重任务最多3个、每工具2线程及单任务16GiB。独立产物为`/home/zyrv/vulsim-artifacts/dot16-L5-T1700-core30-density050-20261117-v1`；状态随同目录`status.json`更新，结果作为物理条件诊断保留，不覆盖原失败及原条件ABCD主表。

2026-11-17已执行[N3＋N4](lxy-plan-fix.md#nangate45-N34-complete)：20源／60个Nangate45 grt点与已有ASAP7点配对，11／4／5源分为训练／验证／测试，完成共享函数拟合、验证选模、参数冻结及封存评价；算术模型仍有未通过的验证或测试指标，保留诊断资格，具体逐源误差和未通过项见[证据](../experiments/arithmetic/evidence/nangate45_n34_v1/README.md)。模型以离线函数复用／校准ASAP7响应，没有精确查表或在线反馈；完整D仍待N5／N6的S／shared、G嵌入及H_char，N5～N8尚未执行。ASAP7冻结代码、模型及在运任务保持；完整产物位于仓库外。

2026-11-17已按用户授权完成[N1＋N2](lxy-plan-fix.md#nangate45-N12-complete)：冻结实际D及六种案例／L需求，独立平台／模型入口和回归通过；加法、乘法、小乘加三个Nangate45连接探针均完成grt。完整产物在仓库外，[仓库证据](../experiments/arithmetic/evidence/nangate45_n12_v1/README.md)只保留小型摘要与哈希索引；ASAP7冻结输入及在运调度不改动。N3＋N4后续进展见上条，完整D模型仍待N5／N6离线验证与接入，连接探针不计作A／BCD主表。范围保持MAC32 L2／L3、Add512与Mul128 L2／L4，每L两个T，最终3份A＋36条BCD及12条软件归因；逐级列出活跃算术和传递级，补验必要中间级边界。采样／拟合只补三例所需，完成三例不自动扩展；R1～R5继续归档暂缓。以下ASAP7记录及授权安排继续有效。

2026-11-17最新用户修订见第一章§1.12.5：Karatsuba L4保留2300／2750ps并复用旧RTL，失败项关闭后端LEC补跑；L8保留1400ps、1150ps改为1750ps重新生成。4350／4750与2150／2300的软件排队已取消。NTT L16 C保留800／950ps，资源后继grt放宽为8小时，2200／2400ps额外软件实验继续排队。15:54完成执行器策略快照路径修复交接，有效控制器为`/home/zyrv/vulsim-artifacts/old-D-user-revision-startup-fix-20261117-v1/repair.py`，该目录及原`old-D-user-revision-20261117-v1`目录的`status.json`同步更新；五个零EDA叶的启动失败保留，并建立同RTL／T／资源设置的具名后继排队。四项在途软件与五项物理任务保留，原冻结输入及其它任务不变，不恢复旧v2或旧revision父控制器。

2026-11-17最新执行：用户要求统一使用旧D，补齐未生成的Montgomery，并对修复过重的Mul128／Dot16／Karatsuba／NTT L16放宽请求后重新生成、验收并送后端；软件错误如NTT L8暂不处理。入口见第一章§1.12.4及`/home/zyrv/vulsim-artifacts/old-D-clock-successor-20261117-v2/README.md`。8个软件任务／16组请求，原A参考复用；全局后端9槽／每工具2线程，本轮内存重任务最多3个同时运行，Dot16／Montgomery每任务16GiB、其余8GiB，软件按可用内存逐步放行。R1～R5算法修复已归档暂缓，原目标及在途物理任务保留。

2026-11-16最新A政策见[A复用原始参考与调度修订](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/original-A-reference-v1/README.md)，主表见[当前37组ABCD对比](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/original-A-reference-v1/comparison.md)。A单列原请求／实测Tmin，BCD仍按§1.9.6冻结的两档L与目标运行，9并行／2线程保持。当前进度分别统计A参考`/9`与BCD`/111`；具体交接状态以新入口及handoff收据为准。

[上轮ABCD、耗时与未测RTL审计](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/README.md)保留18:07的55／148及18:18的56／148原数值；它们是逐目标重测A的旧口径快照，不能继续当作当前完成分母。历史原始报告、失败和费用保持。

| 文件 | 用途 |
| --- | --- |
| [原始任务](lxy.md) | 复杂算术拆分、自动流水线与ABCD研究目标，原文保留 |
| [第一章：冻结D迁移至Nangate45三例验证](lxy-plan-fix.md#local-request-plan) | 唯一现行规划；MAC32／Add512／Mul128，MAC32 L2／L3、Add512与Mul128 L2／L4，每L两个T；N1～N8按三例范围执行；ASAP7九例合同保留 |
| [Nangate45三例模型与迁移合同](lxy-plan-fix.md#nangate45-migration-contract) | 仅拟合三例所需共享函数与S／shared／G，12组目标、3份A＋36条BCD及12条软件归因；禁止精确查表与在线反馈 |
| [Nangate45 N1＋N2完成证据](../experiments/arithmetic/evidence/nangate45_n12_v1/README.md) | 实际D冻结、六类需求、平台参数审计、六份D预算回放／新入口RTL仿真、三个grt连接探针及共享账本收据；大产物在仓库外，正式模型待校准 |
| [Nangate45 N3＋N4配对与函数证据](../experiments/arithmetic/evidence/nangate45_n34_v1/README.md) | 20源／60点配对、实测缩放与预测迁移分开评价、六项离线共享响应、封存误差／资格及软件与费用审计；完整D仍待N5／N6 |
| [Nangate45三档请求补采与时延校准](../experiments/arithmetic/evidence/nangate45_pressure_refit_v1/README.md) | 12训练／9验证／9封存测试，Add／ADC与G时延校准、旧留出已消费回归、职责勘误及费用；其余四个函数保持，完整D仍待N5／N6 |
| [Nangate45 N5／N6小组合与完整评分接入](../experiments/arithmetic/evidence/nangate45_n56_v1/README.md) | 11源／22点、S／shared与同路径H_char、900所有者／44评分回放、六份RTL验证及有限模型包；完整组合指标通过，分项失败和状态外推保留，N7／N8未执行 |
| [暂缓的R1～R5算法修复](lxy-plan-fix.md#deferred-D-algorithm-repairs) | 含R1a、原实现要求、修复表和完整审查证据，以后有时间再处理，不作为迁移前置 |
| [第1～3步：MAC32软件验收](../experiments/arithmetic/evidence/workload_equivalent_mac32_v1/README.md) | 177条采样合同、90个候选／837次完整评分、实际等效T查询、逐目标身份及完整回放；精度与后端评价另验 |
| [第4～5步：模型回归与首轮新候选](../experiments/arithmetic/evidence/workload_equivalent_steps45_v1/README.md) | 279条组件／6个旧组合回归、175个完整候选、72份RTL新仿真；首轮有限提案完成，不代表完整位置反馈已实现，S／shared和嵌入资格失败保留 |
| [第6～8步：A/L紧凑目标v2](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/README.md) | 未拆分A参考实测、1.25／1.5倍A/L目标、冻结D拆分与预算／位置搜索及ABCD后端状态；未测不算完成 |
| [Dot16 L4／L5重新拆分](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/dot16-L45/README.md) | 按用户要求新增4／5级对照，逐级检查活跃算术，保留原L8；软件与后端状态独立报告 |
| [Montgomery256 A重新测试：27ns](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/montgomery-A-retest-v1/README.md) | 用户追加授权；按旧综合／布局／CTS最大周期留10%余量并取整，2线程／16GiB／grt最多6小时，共享9槽，原36000ps失败保留 |
| [当前A参考、BCD结果与调度](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/original-A-reference-v1/README.md) | 每例只引用原A；单列原请求与Tmin，统计9份A参考及111条BCD，保留旧费用，未发射重复A排除 |
| [旧口径运行进度与异常审查](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/latest.md) | 两档L实际推进、已恢复的软件错误、后端失败、资源与独立崩溃监控；只统计已验收读数 |
| [D拆分／位置问题与独立软件反例](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/d-split-placement-review-20261116-v1.md) | 同结构后移反例、G路径权重、Add语法／carry风险、Mul状态膨胀；不替换当前冻结D、不新增PPA |
| [本轮进度、ABCD与D常零位计价审查](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-d-review-20261116-v2/README.md) | 21:40的50／111条BCD及8／9份A快照；31份D／864候选核对、Mul常零位状态特征、Horner可行性排序反转、NTT L8异常退出 |
| [本轮全部ABCD快照：11月17日00:18](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-abcd-20261117-v1/README.md) | 合并原T资源后继；A为8/9、BCD为65/111，37组完整比较与排队／错误；NTT L8再次−11、Montgomery主grt完成但snapshot超时，撤回改时钟批次排除 |
| [原时钟资源后继：失败重测](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/failure-resource-only-v1/README.md) | 当前有效重测；保持原选择T／后端T和RTL，25物理任务对应26条失败记录，只放宽grt到4小时及Dot16容量；原成功复用，原失败与费用保留 |
| [已撤回：固定RTL改时钟诊断](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/failure-relaxation-v1/README.md) | 已停止，不计ABCD主对比；9组新时钟未重新生成D，1物理完成、1运行取消、其余未领槽；保留费用与撤回收据。NTT恢复再次−11，未ready |
| [上轮ABCD历史比较与已测逐项](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/abcd-comparison.md) | 旧口径37组／148条状态、当时已测面积／完整Tmin／频率／setup／hold／线程／原始读数，旧版本独立索引 |
| [后端耗时与瓶颈](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/backend-bottleneck-analysis.md) | 命令及ORFS子阶段计时；setup修复、CTS内LEC／合法化、pin_access分开归因，未完成阶段另列 |
| [未测ABCD的RTL实现与寄存器](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/progress-ppa-rtl-20261116-v1/unmeasured-rtl.md) | 124条已冻结方法索引；未测33份不同RTL的逐级算术／G与6191个寄存器信号，带图／位置／位掩码／赋值行；未冻结项明确待定 |
| [旧ASAP7中间数据库清理：v3](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/storage-cleanup-20261117-v3.md) | 2026-11-17删除182个已完成旧任务的早期ODB、释放13.279GiB；Nangate45完整排除，2724个保留文件元数据及最终DB哈希核验通过，在运任务和报告保留 |
| [本轮旧CEC缓存清理](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/storage-cleanup-20261117-v1.md) | 2026-11-17删除9090个旧展开网表缓存、释放72.925GiB；最终DB／网表／报告／模型及当前任务保留，452806个其余文件元数据核对一致 |
| [旧后端存储清理](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/operational-review/storage-cleanup-20261116-v1.md) | 2026-11-16删除18,919个旧中间ODB／guide，释放54.649GiB；报告、最终DB及当前实验保留，含删除清单与清理后核对 |
| [流水目标周期审查](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/clock-target-review.md) | A/L倍率未显式保证固定边界与不均衡开销；逐例额度和改进建议，未放宽冻结周期 |
| [被替代的C测时v1](../experiments/arithmetic/evidence/workload_equivalent_steps678_v1/README.md) | 原C探针及其实际结果、失败和费用保留；不再用于新目标 |
| [九例ABCD最终评价（第一章§1.9）](lxy-plan-fix.md#local-request-evaluation) | A／B／C／D定义、冻结对照及完成标准；原19组／76条保留，§1.9.6扩展两档L，§1.9.7改为37组展示、9份A参考＋111条BCD |
| [第二章：暂缓修复、已完成前置与W1—W8历史规划](lxy-plan-fix.md#W1-W8-archive) | R1～R5暂缓修复与审查原文、第1～5步软件、旧19组及历史规划；形成时的下一步不自动续跑 |
| [模型精度与保留问题（第一章§1.8）](lxy-plan-fix.md#v10-model-status) | Add／Mux／G／S的具体失败、支持缺口，以及完整诊断版预测误差 |
| [v10组件模型证据](../experiments/arithmetic/evidence/common_transition_incidence_v10/README.md) | 共享参数、训练诊断、旧验证回归与机制记录 |
| [v10初次软件集成](../experiments/arithmetic/evidence/workload_transition_v10_v1/README.md) | 公共Query、所有者、真实参数消费及当时覆盖 |
| [v10完整诊断版后端表](../experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/comparison.md) | ABCD面积／完整setup Tmin／频率、hold、失败与预测误差 |
| [九例数学源与配置](../experiments/arithmetic/WORKLOADS.md) | v10已有源、语义和软件入口；ASAP7目标见第一章§1.9，Nangate45另定标；旧后继排程不自动执行 |
| [历史实施与验收（第五章）](lxy-plan-fix.md#step1-wide-acceptance) | 原逐轮实施、失败、资格及后v10预算开发记录；章首标明历史阅读边界 |
| [恢复前完整阶段快照](archive/lxy-W1-W8-stage-20261115.md) | 恢复前完整文档的补充快照，W1—W8正文阅读入口仍为第二章 |
| [恢复清单](archive/v10-restore-20261115.json) | 检查点、完整备份、撤下文件、文档身份及验证收据 |
| [其他历史归档](archive/README.md) | 原十步、共同需求／S机制附件和更早单平台阶段 |

## 后端与账本状态

原九例物理队列保持用户停止状态：67任务中30完成、9工具失败、4用户中止、24未启动。已有报告与停止／清理记录见[结果归档](../experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/README.md)；先前按用户要求删除的大数据库不在本次恢复中重建。恢复后及本轮第1～5步均未启动EDA或响应拟合。

真实实验历史和最新结清账本保留，不能随代码恢复而回退费用。恢复前所有修改和未跟踪文件已逐文件保存并核对SHA256，主仓库和RTLzz提交均未移动。第6～8步已另行启动新有限物理批次，使用相同累计账本；不续跑原停止队列。第1～5步只进行既有数据职责内的采样审计、回归、软件预测、有限候选生成和RTL功能仿真；第4～5步新增原生显式放置接口和独立验证／搜索入口。65项相关回归全部通过，完整便携回放另有收据；模型资格及九例物理比较未完成。未提交或推送，mission主目录不新增规划文件。
