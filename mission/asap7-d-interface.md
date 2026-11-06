# ASAP7已发布组件接入D端的接口工作

当前结果为[§7.48一般状态S限定发布](lxy-plan-fix.md#step7-general-state-qualified-publication)：新54独立原门槛一次性评价通过，ASAP7 grt三所有者功能状态／控制面积及八类状态边界发布；grt边界72／72、最小覆盖余量37.372788ps。原面积／六类边界参数、九目标／50ps保持，首轮失败及所有已消费测试封存。便携／完整external／隔离／篡改、冻结训练精确复现及本组件Git视图通过，当前无本实验后台EDA。[新模型与能力清单](../experiments/arithmetic/evidence/step7_general_state_v1/README.md)是生产适配的冻结输入，production_price_binding_qualified=false；尚未修改现有C++工厂或将新S价格接入旧组合包。下一步做真实service／native／external查询／所有权／条件上界绑定，并补G／I及完整D／RTL／正式36条。复现与范围见[S交接](asap7-general-state-handoff.md)，下文旧“当前”为其历史检查点。

2026-11-05。承接[lxy-plan-fix.md第四章§7.30](lxy-plan-fix.md#step7-m2-mux-static-independent-verdict)。用户要求本轮模型发布并检查Git后，先补接口、接入D端。本文件登记接口与资格依赖；§7.31已完成生产组件消费、实际cut／capture查询及D诊断。[§7.34](lxy-plan-fix.md#step7-m2-state-boundary-independent-verdict)的状态银行36个新独立test及冻结参数一次性评价已通过，grt状态／边界有界组件发布；原生state绑定与联合阶段／目标资格仍待完成，不能据JSON发布直接放行完整D。

当前可用组件为`experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json`：ASAP7 grt的12类基础／原子操作，11类继承原参数／域／裕量及F5合格证据，动态Mux使用20维静态上下文。Mux的新独立资格仅覆盖2／3／4个独立同宽动态Mux的并行森林、生产单捕获银行和原精确位宽／ABC-SDC条件。完整D、混合算术／控制、one-Mux阶段、共享输入／选择端及状态／组合尚未因此合格。

新增`experiments/arithmetic/evidence/step7_m2_state_boundary_v1/asap7-state-boundary.json`（SHA256 0cf99c9944f40aad7f4d4a2a9bb91afcbaf26048ad64d3e6131d5fcafc3bf904）：仅ASAP7 grt受限合成valid_chain状态银行、ABC1500ps／精确SDC40500、1500、375ps／IO0.2T。状态总面积含state／control、时钟／井接触及未归属repair，排除post-capture observer；与整阶段算术面积须明确所有权。状态银行边界开销910.766404ps，375ps可能无正数据预算，且该边界未授予联合算术／正式I/O资格。下一步应从真实PipelineV2导出完整数据／valid／enable状态、复位每位值与变量位宽，匹配该特征及拓扑域；超域拒绝，不把实际数据银行强行归到合成家族。原组件／新状态包的共同物理身份已经核对，旧stage_correction仍不能继承。

[§7.35](lxy-plan-fix.md#step7-native-state-query-and-successor)已实现StateCostQuery的实际投影／物化导出，覆盖九个公共VUL原始核及3个补充图；掩码、typed特征、逐位复位、实际RTL使能与5项负例通过。外部输出capture须显式请求，VUL输入／service外壳状态另有所有者，未默认为已计费。原生首级使能在内核接口是输入valid，后级为前一级valid；与v1全部寄存控制／按字轮转域不同。故接口保持qualified_price=false，未接通未合格价格或删除原拒绝。用户确认后已预登记原生协议合成银行后继，先采108个拟合侧任务、36独立锁定；合格后再完成价格绑定。整阶段协议需求见[草案](asap7-stage-topologies-draft.md)，不把它视为采样准入。

[§7.36](lxy-plan-fix.md#step7-native-state-validation-freeze)现已完成原生协议108任务的原始／费用回放及验证冻结：面积synth中位2.7173%／P95 16.5356%，grt为5.2353%／32.4129%，原门槛通过；input／register开销冻结且字节复现后，才另行准入36项新独立测试。原生状态价格仍等待该新独立资格与真实银行覆盖绑定，不能将训练／验证通过或结构导出直接写成D已可用。

[§7.37](lxy-plan-fix.md#step7-native-state-independent-publication)已完成36项新独立状态测试、冻结参数一次性评价及后继发布：grt状态面积中位6.0347%／P95 18.9229%，三个目标input／register边界覆盖全通过。新文件为`experiments/arithmetic/evidence/step7_native_state_v1/asap7-native-state.json`，SHA256 ce280fb25047038d0a9ff80084d744191419546d72072864f316ec7c4a8d9bff。schema arithmetic-native-state-qualified-v1，只覆盖原生协议合成银行及原精确条件，production_price_binding_qualified=false。下一步应显式识别这个后继组件、核对StateCostQuery的实际银行域并绑定原生数值，不能把该文件直接替换primitive bundle或给旧stateArea数量接口默认放行；联合算术／正式边界、外围状态、全候选／位置和阶段模型仍需资格。

[§7.38](lxy-plan-fix.md#step7-native-state-production-binding)现已完成**生产组合清单与受限状态价格消费**：新schema显式引用两份不变发布，typed StateCostQuery按真实图／协议／placement重新构造，175次价格与Python数值差0、168次实际物化、35项拒绝及旧回归通过。旧scalar数量接口仍拒绝；pipeline增加typed状态计价／最终核对钩子，但当前完整D预检仍因联合算术／service边界未资格而拒绝，不能称完整调度已通过。九个公共原始核＋3诊断实际银行均被当前保守复位模式域拒绝，九例银行覆盖0／9；例如0x80000035并未因公式只用两个数量特征而放行。接下来须补实际语义复位及共享／相关状态、外围／联合边界，再与受限整阶段／真实区间资格共同验收。证据与复现见[状态价格绑定包](../experiments/arithmetic/evidence/step7_native_state_binding_v1/README.md)，full_D_ready=false，无后台EDA。

[§7.39](lxy-plan-fix.md#step7-all-candidate-static-requirements)已完成九例全部21生产候选的静态需求审计：旧生产图hash／顺序及当前真实C一致、独立K16检查通过，108个去重合法放置视图／582非法提案、每候选最终C实际物化状态核对完成。累积诊断列出复位之外的相关来源、无完整数据链、非旧离散字宽／掩码和18通道，实际中间字到66位；140种阶段需求描述、34组实际／42组保守区间及17类目标参考键已登记。新[联合需求配置](../experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v1.json)冻结需求与计费责任，但原始归属提取、源／任务／划分／容量／预算准入和数值目标尚待完成，physical_admission_allowed=false。后继见[交接](asap7-d-requirements-handoff.md)，当前无后台EDA；108个C诊断视图不冒称未来D轨迹穷举。

[§7.40](lxy-plan-fix.md#step7-reference-cohort-admission)承接参考前置：17源软件协议／状态几何、九项标签读取负控和三个综合检查点的完整续作暂存回放通过，已按专用准入采集17个参考微基准。三个grt容量先导通过后最多4任务×4线程；前三个综合直接复用，旧读取／续作元数据失败及费用保留。固定ABC1500ps／SDC40500ps／IO0.2T，仅用于参考，不拟合或自动冻结目标。真实外部输出无条件捕获与内部valid使能捕获已分开，旧受限external-capture查询不能替代公共VUL外壳；联合资格仍待完整核验。当前监看及恢复链见[参考交接](asap7-reference-handoff.md)，上文“无后台”属于各自历史检查点。

[§7.41](lxy-plan-fix.md#step7-reference-raw-audit)现已完成17／17参考、34阶段／272路径和完整原始／便携／external／隔离／篡改核验；后台已退出。原始D_ref和H_ref汇总数值提案可审阅，统一H_ref规则待用户确认，数值目标未冻结。当前状态以本段及[参考交接](asap7-reference-handoff.md)为准，§7.40采集中为历史状态；完整D／正式36条未放行。

[§7.42](lxy-plan-fix.md#step7-m2-numerical-target-freeze)已在用户确认后按原生产公式冻结九例正式目标，完整external／隔离／篡改核验通过，PPA0；[目标文件](../experiments/arithmetic_dse/configs/model_asap7_m2_targets_v1.json)及[联合需求v2](../experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v2.json)明确绑定九个精确上下文。上段H_ref待确认／目标未冻结为§7.41历史状态；当前进入S／G／I合成源前检和完整采样准入准备，新目标模型资格仍为false，无后台。

[§7.43](lxy-plan-fix.md#step7-general-state-fitting-admission)已完成S一般状态24源前检与完整216项预登记；后继六个容量点通过，当前4×4线程采162 train／validation，54 test锁定。service valid写使能保持、native valid推进和external无条件捕获分别核验，实际FF／唯一归属／九路径／SDC存储与CTS CEC在先导成立。原四份综合诊断／失败及费用保持；当前后台和版本入口见[S交接](asap7-general-state-handoff.md)。尚未拟合或发布S，G／I／完整D消费者仍待资格。

[§7.44](lxy-plan-fix.md#step7-general-state-validation-freeze)现已完成S的108 train／54 validation及162任务／324阶段／2916路径完整原始回放，972收费叶／34772文件hash核验通过。三所有者分项面积原门槛通过，参数／域／逐目标路径边界冻结并四文件字节复现；grt验证中位／P95为input_service 0.23707%／0.56572%、native_state 0.17054%／1.75095%、external_state 0.04248%／0.16485%。这些是功能状态／控制面积，排除shared clock／physical／repair，不是整阶段PPA。原54 test已另行准入，两个自身容量点通过后4×4线程独立采集；上段未拟合／test锁定为§7.43历史停点。采完完整回放并按冻结参数一次性评价；S发布／生产绑定、G／I与完整D仍待。

当前实现状态（2026-11-06，现行S独立通过／有界发布见§7.48，验证冻结历史见§7.47，采集准入历史见§7.46，首轮独立失败见§7.45，验证冻结历史见§7.44，源前检见§7.43，目标冻结见§7.42，参考验收见§7.41，静态需求见§7.39，受限组件消费见§7.38；历史资格见§7.31、§7.35–§7.37）：

| 工作 | 已完成 | 仍待完成 |
| --- | --- | --- |
| 模型包入口 | primitive＋native_state旧生产组合清单通过；一般状态S新grt组件独立合格并发布 | 新S schema／组件清单／工厂适配；完整阶段、真实区间、联合边界及共同目标交集 |
| 实际阶段查询 | stageCostQuery、逻辑capture／共享链、原子出口、nodeInStage；按完整放置重算，无NodeId-only上下文缓存 | 已有范围外上下文的独立资格 |
| 状态消费 | 旧typed原生查询／受限消费／实际物化核对；一般状态S新独立三面积分项及八状态边界通过、grt发布，原面积和六边界参数保持 | 新S的C++ service／native／external特征／协议／所有权／价格绑定；G联合资格及全部候选／位置覆盖 |
| 调度计价 | evaluate阶段重查、双Mux绑定；typed状态和最终物化核对钩子已加入 | 当前预检仍拒绝联合边界；初始／试移／最终完整阶段、状态及总面积未验收 |
| D选择／轨迹 | 公共VUL加载新包；九例21候选保留有序cost_uncovered及组件缺口；PPA0 | 缺少必需模型时不选D；合格完整候选的选择／RTL闭环 |
| 九例需求审计 | 21个生产候选、108个去重合法C放置视图、累积状态／阶段／区间需求及17参考键；生产图／顺序／K16一致 | 未来D新位置逐查询覆盖及正式选择／RTL |
| 目标参考 | 17项参考核验与九例正式目标冻结；S后继在九精确目标独立通过并发布grt组件，首轮失败保持 | G／I合成源前检、任务／容量／预算及独立资格；各组件共同目标／控制／边界域覆盖 |
| 周期与36条 | 旧模型／流水线／reset／valid回归通过 | 新D连续事务／气泡／复位／L-II及36条正式PPA |

本轮父模型字节保持。旧state／boundary／stage模型不能仅凭profile相同就拼到新价格上，尤其stage_correction依赖原节点价格及已验收组合；须核对并资格验证共同物理身份、目标、控制和拓扑域。下一轮先围绕这些缺口复用可用证据、建立必要后继；不把11类全部重训。

用户已确认阶段组合采用**受限阶段拓扑独立建模**：原12类组件保持，另以合成微基准登记阶段拓扑／连接／输入相关性／出口和捕获边界，独立拟合整阶段Q-D与组合面积，不以旧节点价格加总或旧stage_correction代替。初始放置、试移、最终放置须使用同一完整阶段查询；整阶段价格拥有该阶段全部组合逻辑，组件查询只用于其明确分支或诊断，不能重复收费。状态／控制／时钟和边界另有明确所有者；其独立资格不能自动转授任意算术组合。未覆盖拓扑拒绝，正式／保留整图不进入训练，原已消费测试不复用。独立阶段采样协议、生成器及具体任务数尚未冻结，不能将本方法选择写成已取得阶段资格。

## 1. 建立生产模型包适配及组件身份核验

§7.38已完成primitive＋native_state有界组合部分；本节后续要求仍适用于完整阶段／区间／联合边界后继。

原`rtlzz/src/backend/arithmetic_model.cpp`的`ModelCostProvider`读取`arithmetic-backend-model-v1`／12维普通schema，并直接要求state_model、boundary_model及stage_correction。本轮发布是版本化组件包，不能只改version字段或直接替换旧文件。实现应显式识别各组件schema，绑定包内容哈希、profile、库／物理阶段、ABC、SDC、I/O和各联合支持域，保留现有普通模型的有效入口。

新增适配器或版本化组合清单引用发布组件；仅在普通、Mux、状态、边界、阶段和区间的物理身份及目标域有交集时组合。某个组件已发布不自动补出其他字段。生产查询缺组件、缺上下文或域不匹配时返回可定位的cost_uncovered，不能退回固定表、TEST_ONLY、0价格或普通Mul替代区间。

验收：真实发布包可读取、数值与冻结JSON一致；未发布、错profile／哈希／阶段／目标及未知schema均拒绝。此步无需重新拟合或调用PPA。

## 2. 让代价查询接收真实候选阶段与逻辑捕获边界

原`node(Program, NodeId)`及按NodeId缓存不足以表达Mux上下文；本轮新增nodeInStage及实际cut入口。同一个节点在初始放置、试移及最终放置中的同阶段邻居和捕获槽可能变化。应在CostProvider层提供明确的阶段查询对象，包含候选图版本、阶段成员、输入边界、逻辑capture槽／银行、输出／live-through、复位／valid协议和目标条件。

复用`arithmetic_mux_context.hpp`的语义计数；由PipelineV2实际寄存器切口构造BEIR阶段投影和`MuxStaticCapture`，而非用案例名、整图操作数或后端DFF推测。跨阶段输入须保留原始符号来源、类型与已知位属性；投影不能使真实共享输入看起来互相独立。捕获／对齐／共享链也不能重复算作独立银行。

缓存键至少包含模型／profile／目标身份、图及阶段成员、边界和capture指纹、被查询节点。整组试移后失效相应缓存，最终放置重新核对实际cut。原12维操作仍走其原模型分支，不误用20维Mux输入。

验收：原生特征与Python一致；重命名／成员重排数值不变；实际移动后上下文刷新；共享／关联／缺capture和域外拓扑拒绝。当前合格域可用纯并行Mux小图验证生产路径。

## 3. 在实际阶段上计算时延、组合面积及状态开销

修改`pipeline.cpp`中初始放置、试放、整组移动和最终报告的代价入口，使它们使用同一阶段查询和资格判定。现有stageDelay／stageArea只在末端修正标量base，并不足以更新此前按节点计算的上下文相关关键路径；应从阶段内依赖关系重新计算Q-D组合路径，并一致处理扇出、原子区域和模板区间。

明确时延、组合面积、状态位和控制／边界的计费所有者。FP完整原子区域及Div／Mod仍保持首版原子性；模板成员延后由真实half／quarter区间定价，不能同时按叶节点和区间收费。多出口／live-through／对齐／valid／复位须由对应合格状态及边界模型计费。没有资格的阶段组合先报告未覆盖，不用部件时延求和冒充合格整阶段模型。

验收：初始／移动／最终三处对同cut的价格一致；无重复计费、缓存污染或缺失价格；所有模型查询使用ps／um²，选择期间PPA调用为0。

## 4. 接通候选选择、覆盖报告与查询轨迹

公共源码→VUL／BEIR→PipelineV2→original／half／quarter三候选→预算／初始放置／整组移动→选择→RTL使用同一模型身份。C/D候选范围、顺序和K=16保持；选择只读冻结离线参数，最终实测不能触发重选。

记录每候选的模型包／组件身份、阶段cut、特征、原子／区间／状态归属、预测时延／面积、L／II、预算及拒绝原因。区分cost_uncovered、已覆盖但预测不可行、功能错误和工具失败。若某候选缺必需模型，保留为未覆盖；只有规定候选域具备所需资格后，才能声明九例正式D支持完成。不得通过只剩原始候选参与比较来宣称拆分选择闭环已验收。

验收：合格小图通过生产选择链；缺组件的小图在具体阶段给出可复现的拒绝轨迹；PPA计数为0，不要求选择拆分或D胜C。

## 5. 用九例真实图导出剩余资格需求

§7.39已完成静态阶段的21候选／108视图需求导出；§7.41完成参考／原始回放、§7.42完成H_ref确认及数值目标冻结，随后落实S／G／I合成前检与采样资格。这里未来D位置的覆盖要求仍有效。

接口可先实现并暴露真实缺口，再围绕缺口登记微基准。对MAC_32、DOT2_16、UDR_16、DIVSEL_32、F1、F2、H_M_32、H_D_32、H_F1的所有规定候选运行无PPA覆盖审计，导出精确的操作／位宽／目标、阶段连接、Mux上下文、状态／控制、输出及模板区间需求。

已知缺口包括真实half／quarter区间后继（旧41／42失败不变）、混合／单Mux及共享上下文、双模板与外部算术组合、多出口及对齐状态、正式目标与边界／时钟域交集。先检查可继承的合格原模型，再对真正缺口做预登记训练／验证／新独立资格；不把正式／保留整图PPA当作训练，已消费P4／F4／F5标签永久隔离。模型参数未改且域匹配的11类无需随接口工作全部重训。

## 6. 完成RTL周期验收，再冻结九例36条后端任务

以公共源码和参考驱动生产D，核对连续事务、气泡、在途复位、排空、多出口／bits／flags对齐及L／II；核对最终RTL的阶段与查询记录。先取得各必需模型资格和上述周期闭环，再冻结36条的数值目标、资源／容量／存储及步骤九复核范围，启动A/B/C/D实测。

本接口阶段的交付是生产模型读取、阶段cut与特征绑定、原生查询、放置／移动／选择轨迹、合格域小图验收及九例缺口表。九例全部支持完成还依赖第5项的资格；接口补通不会自动扩大本轮模型的发布范围。当前四平台总范围和688条矩阵继续保留，未由此放行。
