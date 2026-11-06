# 四平台离线模型协议 v1

本实现对应 `mission/lxy-plan-fix.md` 第一章 §7.2–§7.6、§10.7。本文保留各版本协议的实施顺序；最新状态以该计划第四章§7.31的原生组件接入与D覆盖诊断为准；组件独立验收／发布见§7.30，旧12维验证失败见§7.28、原F5独立结论见§7.26，旧段落的启动检查点不是当前待办。模型是否就绪由冻结的训练、验证、独立测试及结构域证据决定。单独生成 JSON、人工测试系数通过、物理探针成功都不等于正式 D 已就绪。

`configs/characterization_v5.json` 固定平台参考映射点、分组、算法候选、误差门槛与选择顺序。`model_collection.py` 产生独立 RTL 微基准和逐任务准入；`model_samples.py` 静态渲染允许的寄存器边界，读取同一阶段真实 Q→D 到达差与原始路径点；`model_training.py` 拟合并导出数值系数或有限树。任何 formal/holdout/旧容量诊断 PPA 均不进入数据集。每个完整源 bundle、所有目标变体及其 synth/grt 标签保留同一个分组，不能按行随机拆分。

算术微基准具有独立 `core` 层次。启动寄存器的复位/使能逻辑在 Q 之前；捕获寄存器无复位、无使能，算术时延不含 clk→Q、setup、时钟树和捕获控制 Mux。面积按实际 `core` 内唯一非顺序单元计数，启动/捕获 DFF、控制、时钟及未分配的物理开销另存。每个实际捕获 DFF 都核对数量；`keep` 标注和名义扇出不是实现证据。单银行可以规范化为 `y*`，多银行可以保留 `dst*`，边界声明用受限静态选择列表；禁止动态 Tcl、执行归档脚本或按名字猜测缺失图。

SDC、库、映射目标、工具线程控制、物理流程均属于测量身份。四平台新 profile 显式登记 `timing_repair_max_buffer_percent=100`，实际 helper 脚本、有效环境及工具调用均须保留。这是 CTS 对大量短边界路径的有界容量修订，不改变时钟、uncertainty、transition、I/O、driver、load；此前默认 20% 的结果保留原条件。GF180 新 wire R 使用独立 RCX/几何线段拟合，属于另外一项物理条件修订；不能用旧 profile 的结果冒充新域。

`model_features.py` 和原生 `arithmetic_model.cpp` 共用十二维数值特征：两个输入宽度、结果宽度、最大输入宽度的 log2、输入宽度积、直接用户数量、两个输入已知零位数、ABC 目标、SDC 周期，以及最大输入宽度与结果宽度积、保留的部分积位项数。宽度、位数和数量为 JSON integer；模型参数、时延 ps、面积 µm² 使用有限数值。模型只消费预测前能够得到的 BEIR/请求特征；不得使用最终单元数、实测关键路径作为输入。当前条件明确列出操作、结果形状、输入宽度及 ABC/SDC 联合关系；不以独立最小最大值构造未经验证的矩形，不自动覆盖所有常量模式或新模板。

算法比较包含每操作常数/线性、正则化回归及最大深度 2/3/4 的树。预处理折回导出的原始尺度系数；编译器不依赖 sklearn，不运行 Python、训练、Yosys 或 OpenROAD。先用训练数据拟合，验证集质量门槛通过后选算法和正向低估裕量，再写出 `selection-freeze.json`，最后由独立 `test` 命令按原门槛评估一次。测试结果不回调选择。面积不强制转为整数；C 的抽象整数成本保持独立。纯线性/树推理一致性不替代特征提取、域和预算的一致性。

孤立算子误差通过后，状态与阶段模型还需独立新合成图验收。v2正向残差在验证集失败；v3非负基础缩放／截距／操作数／结果位数修正在验证集通过，却在独立DOT3图上超过错误可行预测门槛，四份包均保留为`failed`。不能据其误差中位数合格发布模型。历史`configs/model_calibration_v5.json`预声明不同宽度和混合拓扑的训练、验证及新独立测试；用训练拟合，验证集最大低估比×1.05决定裕量，选择冻结后才采集／读取测试，原DOT3失败标签不回填。未完成状态／阶段验证的文件标记`isolated_labels_passed`或未就绪，原生消费者只接受`quality_status=passed`。

阶段成本使用已冻结的单算子／组合图预测，实际逐stage汇总原始面积后再修正，不能把整个图的面积缩放误用一次。节点数／结果位数上限另有图域约束：该轮局部阶段域只验收独立输入的单出口Mul/Add树、单节点动态AddCarry，最多4个乘法，不接受共享中间节点、多出口森林或任意新DAG。原生初始放置、候选移动、最终校验和独立报告读取均检查真实stage成员；搜索中未找到完整覆盖的位置，不改称`predicted_infeasible`。这项保守限制属于当前搜索／支持域，尚未证明所有合法位置可搜索到。

模型还明确区分普通动态数据与已知零／已知一、字面量、常量进位及相关操作数。未训练模式明确拒绝，不能只凭位宽进入模型。额外元数据采用布尔值，数值系数仍使用相同十二维特征；它们是资格条件，不是事后观测特征。

D 的单位统一为 ps/µm²。目标周期分别扣除输入 I/O 比例、clk→Q/setup/控制及声明时钟预留，得到路径数据预算；每个实际阶段重算成本。初始放置、整组局部移动、最终验证使用同一 provider，局部上限为相应初始数据路径的 1.05 倍与用户绝对预算的较小值。未覆盖的阶段形状不能计零；固定结构位置优化不宣称全位置空间最优。

C/D 使用相同的有序 original/half/quarter 候选和 K=16；C 保留原整数抽象排序，D 对预测可行候选按预测总面积、预测最大级时延、寄存器位数、candidate_id 排序。无覆盖、有限搜索未找到、原子组超过预算分别报告；仅在所有已评估候选均有适用模型且原子组下界超限时给出限定范围的 `predicted_infeasible`。选择阶段的后端调用数为零。候选报告的 `D_covered` 与最终入选的 `D_selected` 分开，不将所有候选标成已选中。

公共入口仍为 `ArithmeticRequest` / `CompileOptions` / PipelineV2 / VUL：`cost_mode=backend-model`、显式 `model_bundle` 及其 SHA256、目标平台 profile 及 SHA256、L/II、目标周期。模型缺失、哈希/平台错配、质量未就绪或域外输入明确拒绝，不回退为 C。真实模型的四平台编译、原生/Python 推理、位置证据及周期 RTL 验证属于单独验收，人工测试包以 `TEST_ONLY_` 标识且不发布为训练成果。

完整日志、ODB、SPEF 和训练中间文件暂存本机 ignored `build/`；便携包保存压缩标签、必要原始路径/实例、源/任务身份、划分、算法/质量报告和索引哈希。远端持久留存尚未确认。步骤七的局部域不能替代五档整数、宽商余、binary32 或步骤八 688 条实测；尚未覆盖的项目必须单列。

首轮v1的四平台Mul面积高分位误差失败保留。v2新增静态结果几何特征与相对误差加权拟合，原160行测试数据封存；只使用原训练/验证640行，另在拟合前冻结六扇出独立测试。所有24个平台/阶段/操作范围的新独立测试通过，尚需状态/阶段与编译器验收。

物理状态面积消费的`model_state_bits`只计算尚未被证明为常量的保存位及相同规则的外部输出边界；`register_bits`继续是逻辑寄存器链位数。固定C仍按逻辑保存位收费。新D状态模型限制保存位/信号规模、数据字宽、复位/使能协议；未知大字宽或纯控制状态不自动套用线性模型。

当前数值架构见`model_calibration_fit_v6.json`：单算子stage使用独立拟合的single-operation predictor，多操作stage使用局部图修正，均由实际成员图识别。v5统一修正在验证失败；v6独立测试四平台grt通过，Sky130HD synth的delay P95失败保留。该架构不默认具有独立组时延下界的单调性，生产入口明确关闭这种下界证明；有限调度搜索失败不能包装成预测不可行。人工fixture仍只验机制，实际训练模型需另通过原生推理与RTL周期检查。

`model_context_qualification_v1.json`预声明单捕获银行、固定ABC及SDC R／1.25R／1.5R的后续检查，使用冻结v6数值参数、原独立测试家族，不再拟合。`model_boundary_qualification_v1.json`要求固定预算覆盖实测H和控制路径；不能由组合误差达标推断边界预算也已覆盖。新资格数据标记`not_training=true`，拟合入口明确拒绝消费。通过后只发布声明域的grt包，Sky synth失败及其原整包保留。

原生模板区间按`model_mul_intervals_v2.json`采集，`test_read_after_fit_only`现在由程序执行。该准入的采集器默认只选train／validation；显式test任务、直接backend入口和`model_mul_interval_fit extract --splits test`均须给出`--selection-freeze`。门禁校验同一准入／采样协议、实际训练数据及其完整源任务覆盖、冻结候选字节和grt验证就绪状态；缺失、错配、混入测试行或候选验证失败均在启动物理命令／读取测试标签之前拒绝。`fit`记录实际训练数据路径／哈希，该检查点当时待实现的独立评价／发布入口已在后文及计划第四章§7.11完成，首轮grt38／42失败；不能手动把`awaiting_independent_test`改为passed。

区间证据由`model_interval_package`从已有产物打包：38份真实typed图、实际输入RTL／边界契约、逐项RTL观测值、四平台TEST_ONLY三候选报告及其模型进入Git小包。默认核验重建402个区间、静态特征／位映射和RTL整数观测，并重算机制报告成本与排序；`--verify-external`另读取独立的区间原始归档，重新解析实际阶段、SDC、Q→D路径、唯一core面积与映射后DFF数量。最初5个v1探针保留为排除拟合的历史，不因归档核验通过而成为训练标签。旧原始归档保持原字节。

尚未发布正式freeze时，可用`python3 -m experiments.arithmetic_dse.model_evidence --freeze build/step7-models-20261102/candidate-offline-model-freeze-v1.json`核验该历史候选，追加`--verify-external`检查本机完整产物。显式候选与正式freeze执行相同的源码／父链校验，不跳过哈希或历史绑定；当前源码变更后使用匹配后继或归档代码回放，不能把旧命令列为当前源码必然通过的入口。候选核验不表示全步骤七已完成。

2026-11-03区间续作：恢复原ASAP7 v2清单的train／validation，独立test仍须等待验证通过及选择冻结。非恒定区间预测使用显式的八维区间特征表，普通算子的十二维特征表保持原边界；原实现将两者混用，常数TEST_ONLY包没有触发该错误。本轮同时补充实际SDC／阶段报告／Q→D点回放、完整任务／区间／阶段及位宽覆盖检查。新的拟合数据登记实际准入路径，选择冻结保存实际训练源码、验证报告、基础模型哈希、Python／numpy／sklearn版本、线程环境及seed。旧数据与旧冻结按其原始字节解释，新增字段不追写旧包。

区间独立评价入口为`model_mul_interval_evaluation`。`test`只消费已冻结并验证就绪的候选，用选择目录中的独占消费记录阻止更换输出目录后重复测试；`verify`只重算既有测试；`publish`只导出通过原门槛的grt范围，保持全部数值系数、裕量、基础模型与支持域不变，synth失败另行保留。`reproduce`只重新读取冻结train／validation及基础模型，要求候选与验证报告字节一致，不读取独立test标签。逐区间原门槛仍为准，另报整体误差、错误可行预测和保守拒绝；half／quarter排序只比较同位宽、同结果语义的完整模板区间，属于固定R下的诊断，不冒充含状态开销的整流水候选PPA排名。

新增`model_interval_successor`用于建立后继证据包，引用父包字节池并单独保存新原始归档；`prepare`之后先结算support，再`seal`资源前缀。便携核验重算冻结裕量、独立测试和发布状态，external另读取实际测量产物。后继尚未seal时，旧候选绑定的是旧源码检查点；当前源码修改后的验收须使用对应后继，不能跳过失配或覆盖旧候选。具体实际执行和完成范围见现行计划第四章§7.11。

2026-11-03目标／负载后继启动见现行计划第四章§7.14及`model_mul_interval_target_load_v1.json`，其v3独立失败结论见§7.17。首轮固定R区间独立测试已失败封存，24点时钟诊断也保持not_training。新采样固定ASAP7 ABC=1500ps，使用正式I/O=0.2×T、真实捕获银行及多个SDC条件；参考尺度只从原train标签生成，不能使用原失败测试或当前被预测电路的后验Tmin。源码按完整bundle／位宽与其目标变体分组，新独立测试声明为已暴露位宽上的新负载／目标上下文。

`model_target_collection`把完整设计与逐批物理准入分开；先采80个宽松训练及260个验证任务，基线不足才放行预登记的317个条件训练任务。235个新独立测试由验证就绪、数据完整和参数冻结门禁保护。该启动检查点只采基线，后继80＋260＋235任务已在计划第四章§7.16–§7.17全部完成并失败封存，不能把任务表或软件检查写成模型通过。已完成的原始报告、实际银行、SDC、Q→D、唯一core面积和共享账本wave身份逐项回放，工具／库／流程的静态身份也必须一致。

新目标区间使用独立的十九维特征schema：原八维几何特征、三维静态负载特征、SDC及冻结参考尺度／压力相关项。它与普通算子的十二维schema分开。简单基线只拟合共同宽松条件；条件候选允许目标响应。先应用验证／训练内系数交叉检查得到的保守裕量，再判定候选是否合格；冻结参考在交叉检查中保持可用，因此不将该检查称为未见位宽证据。测试不选择算法、裕量或支持域。逐区间原门槛保留，同时报告实际目标下的局部可行性和整体接口状态。

原生新增`arithmetic-mul-group-interval-target-load-v1`消费路径，并保留旧区间schema。新局部模型与既有普通算子／状态／边界模型组合时，必须有显式`joint_model_context`并检查目标域交集；不能因局部区间可查询便默许完整D扩域。非恒定TEST_ONLY模型的1740次查询／独立Python重算及旧四平台81项入口检查已通过，本段记录入口实施时点；实际采集、拟合／冻结及独立评价后已失败封存，尚未形成可进入正式原生D的合格区间模型。后继证据入口`model_target_evidence`保存原始文本、源快照、数据角色、参数冻结、测试／发布及外部产物索引；没有实际验收收据前不宣称便携或全步骤七完成。

2026-11-03并行交接以第四章§7.15为准：`backend_policy_v9.json`允许最多四个完整物理任务、每工具四线程；`model_mul_interval_target_load_v3.json`保持原样本、目标、划分及质量门槛。明确继承43个已完成的两线程baseline训练任务，按原manifest／wave／父计划绑定并保留原字段；新训练、全部验证和独立测试均为四线程。静态身份核验仅对该已登记的训练线程差异归一到四线程部署身份，其余工具／库／物理脚本／ABC／profile仍须一致。此处理不声称数值普遍不变：四个not_training线程对照的40行阶段标签实测一致，最终资格仍由原门槛及四线程独立测试决定。完整D使用的普通算子／状态／边界模型还须另行核验相同执行条件。

该轮后台设计为自动采完80个baseline＋260个validation后停止（现已完成退出），状态为`initial_collection_complete`，交由用户监看并在下一轮继续提取／拟合。317个条件训练仍需基线不足，235个独立测试仍需验证就绪及参数冻结；该采集服务不跨过这些后续阶段；后继状态见下文，旧服务不再活动。只读监看入口为`model_target_status.py`，不递归扫描build；完整任务锁、原子账本和依赖调度均已检查，真实四任务并行对照已完成。

2026-11-04后继状态见第四章§7.16：80＋260首批任务全部完成，3276行train／validation标签回放通过，简单基线在synth／grt均42／42类通过原验证门槛。参数、算法、支持域和验证／交叉检查裕量已冻结；重拟合候选及验证报告字节相同。按预登记规则跳过317个条件训练任务，冻结selection后采集235个新独立test任务，现已全部完成。该服务以4任务×4线程运行、写`test_collection_complete`后退出；一次性评价与发布判定已在§7.17完成，结果拒绝发布。新驱动入口只增加阶段边界和冻结转发，不改变原collection producer、拟合协议或质量门槛。

后继实际结果及当前范围以第四章§7.17–§7.19为准：上一轮目标／负载区间独立测试grt41／42，因quarter/low/1/1时延中位误差超限拒绝发布，完整失败已封存。用户确认先做ASAP7九例36条闭环，本轮`model_asap7_m2_primitives_v1.json`只采其基础算子／完整原子标签，固定ABC及正式I/O，train F1/F3、validation F2、deferred test F4；按原普通模型质量门槛执行，不实施后验门槛放宽。224任务中的168个train／validation原v3已因两份DivRem32紧目标LEC求解超时停止（74 train完成、2失败，其余未启动），56个test必须等待合格冻结选择，当前入口拒绝提前launch／extract。采样源、映射复用、原始标签、实际银行及共享ledger按后继计划绑定；完整组合／状态域和36条PPA另行准入。

2026-11-04按用户授权建立`primitives-v4`时限后继，绑定`model_asap7_m2_timeout_recovery_v1.json`及未改字节的v3父链。原74份成功测量含跨祖先继承的三个t0，均保留原manifest／wave及源快照身份；两份1200秒失败不覆写。仅六个train／validation DivRem32、4500／1500ps任务改为3600秒后综合→grt上限，先单独执行两份失败的有界新尝试，完成后续采；无自动重试，不改电路、LEC、SDC、ABC、I/O或原质量门槛。其他任务仍1200秒、test继续锁定，测试不从拟合侧例外自动继承资源资格。每波按实际时限增加墙钟／CPU预约并保留后续资源；后继没有放行正式36条评价。

2026-11-04用户进一步确认继续原40.5／13.5／4.5／1.5ns周期表（算术／控制原网格同样保留），不实施提出的保守改钟草案；该草案未启动物理任务，已撤出活动后端。`primitives-v5`继承v4的75份成功结果并仅恢复一次人工取消的4.5ns点；`model_asap7_m2_original_grid_resume_v1.json`绑定取消收据和原manifest，不追改父证据。原六点3600秒例外保留，其他资源、质量门槛、映射复用与独立test门禁不变。负synth裕量不自动跳过后续阶段；完整成功的负setup标签与时序违约共同保留，未完成阶段不伪造标签。模型尚未拟合／发布，具体状态见计划第四章§7.20。

2026-11-04阶段续作后继见第四章§7.21及`model_asap7_m2_phase_resume_v1.json`。v5的98份成功测量继承，4.5ns点保存的前／后网表用于完整LEC重启（Glucose7200秒）；从真实布局检查点重放CTS，只有生成网表逐字节匹配已证明输入、边界完整且证明／库／工具／费用绑定有效才复用证明。LEC与剩余物理叶分开计时、同一完整任务名额；不把祖先耗时拼为新冷启动实耗。新任务仅增加LEC前观测ODB／SDC。全部70个未完train／validation在同一有界滚动队列派发，仍不读test。原时钟、分组和质量门槛不变；阶段证明和新原始产物仍须实际完成，才有对应标签及后继验收。

F3修复后独立续作见第四章§7.22与`model_asap7_m2_postrepair_resume_v1.json`：在保持运行中的v6生产源码不变的条件下，单独绑定F3的失败manifest／修复后ODB／完整454 PI与649 PO网表；Glucose7200秒，通过且从ODB导出网表匹配后继续原CTS尾部及grt。另四份从未启动的validation仍使用原v6 backend准入及映射依赖，由共享4任务名额协调器派发。主计划失败字节不覆盖，成功续作需要版本化数据继承和原始回放才纳入拟合；独立test不启动。


2026-11-04当前后继见第四章§7.23。三项CTS后LEC超时已通过实际Liberty／完整top及寄存器Q-D-CLK边界的Yosys／ABC结构化CEC、三类变异反例及精确检查点绑定后完成grt；原失败及费用保留。168个拟合任务、1464行标签已回放。基础算子统一模型grt9／12失败保留；在独立测试前登记的精确输入／结果位宽分段后继与统一模型比较，保持原算法族、正向残差P95加1.5ps裕量及应用裕量后的原误差／错误可行门槛，synth／grt12／12验证通过，重拟合字节一致。生产域仍只列已采样位宽／结果形状／ABC-SDC点及单捕获银行，不自动增加插值、组合、状态或区间域。

`primitive-fit-v2/selection-freeze.json`冻结后才放行原56个F4独立测试。新独立入口保留原拟合producer硬锁，以显式新准入和单次消费记录绑定冻结选择；t0只映射一次，其余目标复用映射网表并重建SDC／ODB。CTS内结构化CEC及负控归外层grt叶收费。测试v1的有效ABC文本漏识别、v2的继承综合命令读取停止均保留，v3继承四份已完成test并继续其余52项，模型字节完全不变。原消费记录、采样周期、ABC／I/O及质量门槛不追写；独立评价／发布尚未完成。当前状态与服务以计划§7.23及`model_m2_status.py`为准。


2026-11-05实际后继见第四章§7.24–§7.25。原56个F4已完整回放，synth／grt各8／12类通过，均因逐操作错误可行门槛拒绝发布；实际目标局部0／244不替代预登记预算检查。失败便携包`step7_m2_primitives_failure_v1`已做数值与本机完整外部回放，所有F4标签永久排除后继拟合／验证／算法／裕量选择。用户确认原门槛保持，先改善保守校准再用新独立测试。

后继v3／v4只消费原train F1／F3与validation F2。按完整训练捕获／源上下文交叉拟合，尺度为max(1,验证实际／原预测,训练上下文交叉拟合实际／原预测)×1.05，再加1.5ps；面积继承独立测试前v2固定选择。v3 grt11／12验证通过，mux过度保守失败保留；v4在已登记精确位宽／结果／SDC点内比较条件分段，不插值或扩目标域，synth／grt12／12验证通过、重拟合字节一致。验证就绪仍不是独立通过或完整D就绪。

新F5协议为56个新真实银行／源上下文，同原宽度及四档目标、ABC1500ps／IO0.2T；14源、五银行、最大静态捕获1605位。原四银行producer保持，五银行labels-v2独立版本化。通用综合前缀后同ODB增加一次付费标签快照，初始观测保留，映射每源只做t0。五个具体结构／阶段容量先导均完成，8GiB／300秒synth／1200秒grt及共享4任务×4线程保持。后台只采F5，完成后仍需一次性独立评价／发布，不读取测试反馈调参。


F5实际运行在15份成功后遇到两个寄存器x1→x2的驱动提升，旧state-model字节比较保守拒绝。§7.25追加的状态图后继只把证明比较限定到真实Liberty原语／边沿／极性／引脚／参数／连接，忽略非功能名称及area／capacitance；功能属性和不匹配仍拒绝，实际时序／面积照常计入x2单元。完整1620／2610边界的真实pair与5项状态差异检查通过。`independent-F5-v2`继承15份成功结果并从修复后ODB恢复该点，旧producer／失败／费用及冻结v4数值保持；当前服务与入口见现行计划§7.25，尚待完整独立评价。


2026-11-05 F5完整独立结果见第四章§7.26：56／56采集、完整原始报告／费用／LEC回放完成，冻结v4一次性评价synth12／12、grt11／12，发布为空。唯一失败grt mux的时延P95为98.5734%超过75%，中位12.0600%、错误可行5／264（1.8939%）及面积通过。整体grt时延中位／P95为9.8302%／46.5997%，不能用总体统计或实际目标局部0／244救回失败类。F5数值不得回填后继拟合、验证、算法／裕量或支持域选择；本轮参数、门槛、目标与分组封存。

`model_m2_f5_evaluate.py`读取五银行labels-v2、目标条件v4预测、15份成功继承和CTS检查点祖先，并按实际schema核验顺序逻辑证明；原始观测注记仅在精确祖先绑定时继承，实际目标标签独立核验。新评价器检查及224测量／448阶段／1952行便携原始回放、完整外部核验、无build／EDA／账本副本和篡改拒绝均通过。证据入口`model_m2_f5_evidence`及`step7_m2_F5_v1`保留全部冻结数值／来源，尚不构成通过质量门槛的发布模型、完整D或全步骤七关闭。后台已退出，无待运行队列。


2026-11-05用户明确选择只补Mux并继承其余11类未改参数／域的合格独立证据，仍须12类全部合格才发布；原F5总体failed不追改。新`model_asap7_m2_mux_context_v1.json`冻结42个实际源bundle、48 train／72 validation／48 locked test：独立并行Mux数量分别2／3／4，同源全部目标及阶段随split；原六种宽度／四档周期／ABC1500ps／IO0.2T及门槛保持。新test声明已暴露宽度／负载上的新源／并行结构上下文，非未见宽度或更大负载外推。原F4／F5和更早独立Mux标签永久排除新拟合、验证、算法／裕量和域选择。

`model_m2_mux_labels.py`在全输入／银行Q-D基础上加select、data_a、data_b诊断，旧冻结读取器不改。预测仍只用已有12维静态特征，不用映射缓冲／实测路径作为查询输入。11类继承数值／裕量／域和独立收据在新采集前绑定为inherited11.json，Mux标签不在其中，不进入新拟合。后继最终发布必须明确两代证据及全部12类资格，不能以11类继承宣称原整包或完整D通过。

两个具体P2／P3的64位三银行拟合容量点已完成并核验真实输入分路径及银行，最大峰值434.71MiB；P4 test仍锁定并须其自身容量资格。当前后台只以4任务×4线程滚动采120个train／validation，采完退出等待原始数据回放、拟合／冻结／字节复现；48新test不自动放行。完整资源包络和预算／磁盘预留、失败保持及无重试均按计划§7.27实际准入执行。当前尚无新的Mux模型或合格12类发布包。


2026-11-05 Mux-only120个拟合侧任务已完成，768行合法主标签／624组诊断及原始物理／LEC／资源父链回放通过。两版预登记候选选择均字节复现，后继synth通过、grt中位6.015%／P95为79.0148%，P95未过75%，面积与错误可行4／2640通过。48项P4独立测试继续锁定未消费，11类固定资格保持。有限候选池及同特征不同源上下文诊断只读取合法train／validation，未读旧独立Mux数值；数值和本机外部重提取封存为step7_m2_mux_validation_v1。

下一步若增加Mux专用、预测前可计算的静态结构／状态特征，需先明确版本化输入语义、VUL／PipelineV2可取得性及原支持域，不能把实际缓冲数／单元数／STA作为推理输入。该契约变更待用户确认；其他11类的系数、裕量、域及独立资格无需重训。当前不降低门槛，不提前消费48独立任务，不按已见测试缩域。


2026-11-05用户已确认Mux专用静态上下文。后继schema arithmetic-mux-static-features-v1只为Mux在原12维之外增加8个编译前语义上下文量，普通11类参数／域／资格保持。寄存器边界内的独立控制森林按真实语义输入／逻辑capture和成员计数，不用占位端口、sample ID或映射／STA数据；Python标签契约重建与原生BEIR阶段投影在48个实际拟合源中一致。新Mux验证synth／grt均通过（grt中位6.0471%、P95为70.0097%、错误可行6／2640），面积原值保持，重拟合字节一致。选择c180eac32a2fd38fc7f8273bc0eb18f4789e76a13d79221e9af7a35f1c748fc3冻结后才放行原48个P4源；全部物理条件及门槛保持。

Mux显式查询适配默认拒绝缺上下文／未独立合格／profile或精确目标错配；384行／192上下文原生候选数值与Python一致，PPA0。当前只完成特征和数值适配，不表示生产CostProvider阶段绑定或完整D已通过。P4测试前已经明示新独立资格仅覆盖parallel_dynamic_mux；旧mixed-control对新系数仍仅train／validation，生产查询需要独立资格，不能从纯Mux测试推断任意组合。其他11类照原域继承，mixed/arithmetic、阶段／状态、区间和正式目标仍待后续。该48项队列已全部完成，其冻结参数的一次性评价／发布见下文；原F4／F5独立Mux不回填。


2026-11-05后继独立结果见第四章§7.30：原48个P4任务全部完成，完整回放384主标签及384组分路径后，只对冻结选择c180eac32a2fd38fc7f8273bc0eb18f4789e76a13d79221e9af7a35f1c748fc3评价一次。synth时延中位／P95为1.6208%／3.0494%，grt为8.2758%／54.9834%；grt错误可行25／2112＝1.1837%、实际目标局部0／192、面积P95为0.7844%，原门槛全部通过。verify只重算既有结论，不重选参数。原192份拟合测量及768主标签亦已回放，已发布Python入口96条单银行查询一致且PPA0，缺上下文／错profile／目标／未合格／混合上下文拒绝。

12／12为合成组件资格：11类原模型／裕量／域及F5合格收据保持，新Mux仅parallel_dynamic_mux、2／3／4独立同宽动态Mux、生产单银行、原精确位宽／ABC-SDC和IO0.2T。P4资格限制在测量前冻结；其新标签已消费，永久排除后续拟合／验证／算法／裕量／支持域选择。原F5整体failed与publication[]保持。新发布模型SHA256为f49990d5aa68045a7127636e074d07f4140404b8b007c19b8f8b70bd16524e15，证据入口model_m2_mux_static_evidence及step7_m2_mux_static_v1；不覆盖旧offline_model_freeze。

生产原生ModelCostProvider仍须版本化组件适配与真实阶段／capture绑定，不能把新包改名成旧schema。下一轮按mission/asap7-d-interface.md补接口、用合格域小图检查放置／整组移动／选择／RTL，再审计九例实际所需的状态／组合、混合Mux、真实区间和正式目标资格。D选择PPA0、C/D候选及K不变，不要求必须选拆分或胜C；当前full_D_ready=false、九例36条未完成。


2026-11-05原生接入见第四章§7.31。公开请求接受asap7-m2-primitives-static-composite-qualified-v1；makeCostProvider选择PublishedPrimitiveCostProvider，按固定包hash、profile、ABC1500、IO0.2T、12类质量及逐操作精确联合域消费，不转换成旧模型格式。原12维组件与20维Mux分别预测，线性／树、切片和冻结裕量与Python一致。原发布及旧冻结字节不改。

新增StageCostQuery从完整候选放置重建live成员、共享跨阶段链和外部capture银行，保留原子FP出口身份、输入相关性／已知位及有效控制；nodeInStage校验实际cut及逻辑负载后查询。完整放置evaluate接入重查入口，试移不复用NodeId-only上下文缓存；实际PipelineV2双Mux阶段的2次查询通过。仍无合格state／boundary／stage组合，初始放置和完整D阶段计价不可由组件标签自动放行；生产路径明确拒绝缺失资格。

新回归436次12类／登记域查询与Python最大差0，14项拒绝及上下文4→2变化通过；原四平台250项及pipeline／reset／valid含CIRCT通过。九例公共VUL实际经vulrtlgen→新D请求→原有序策略共21候选，全部cost_uncovered，首缺state模型；完整拒绝轨迹及各组件的已知宽度／目标信息落盘，不将未覆盖写成predicted_infeasible。1500ps仅接口诊断，非正式目标资格，PPA0、无新拟合和测量。新证据model_m2_native_evidence／step7_m2_native_integration_v1明确full_D_ready=false，下一步补共同状态／边界／组合、真实区间及所需控制／上下文／正式目标资格。


2026-11-05状态／边界后继协议及后台见第四章§7.32、model_asap7_m2_state_boundary_v1.json与build/step7-state-boundary-20261105/admission.json。48个新合成银行登记72 train／36 validation／36 locked test，ABC1500ps、精确SDC40500／1500／375ps、IO0.2T、4线程；旧2线程状态公式只作数值基线，旧阶段修正不直接继承。软件v2真实5银行×80周期／12800向量检查通过。两个训练容量先导后最多4任务×4线程；后台仅采108拟合侧任务，36 test仍须拟合／验证／冻结／字节复现后另准入。面积原门槛median20%／P95 50%和边界50ps reserve保持，独立资格先限valid_chain；状态银行边界不自动授予算术组合／正式目标资格。已发布12类参数／裕量／域不变。

阶段组合方法已由用户确认：对受限合成阶段拓扑另建独立整阶段Q-D／组合面积模型及新独立资格，保留已有组件；不走逐个扩大内部节点上下文再拟合残差的路线。具体拓扑／域／源分组／资源协议仍待事前冻结；不使用正式／保留整图或已消费测试回填，未覆盖图拒绝。整阶段价与节点组件不重复收费，state／boundary所有权分开；当前没有完整D或36条资格。

状态采集v1的两个先导物理命令及CTS CEC成功，但后处理误将CORE_WELLTAP当作未知逻辑而停止，原失败／费用／源码保留。现行model_m2_state_collection_v2只修正profile允许的物理单元分类，并在收费support叶核对原始hash／路径／面积／SDC／RC／CEC和费用后继承两个先导，物理重跑0；逻辑未知master负控通过，面积保留井接触开销，实际FF数量严格核对。当前准入为build/step7-state-boundary-20261105-v2/admission.json、服务vulsim-asap7-m2-state-boundary-v2-20261105.service；两个先导容量证书通过，4任务滚动采集已开始。当前状态入口为`python3 -B -m experiments.arithmetic_dse.model_m2_state_collection_v2 status --folder build/step7-state-boundary-20261105-v2`。原协议／生成器／任务／角色／门槛不变，36 test仍锁定。

15:27后的现行采集入口为model_m2_state_collection_v4及build/step7-state-boundary-20261105-v4。v2的1位源综合成功后因[0:0]端口被Yosys标量化而触发SDC名称核验，v3仅修正单比特端口归一化；v3回放继承日志同名触发两条support失败、PPA新增0，v4用独立叶日志并保留全部失败父链。单比特约束正／负检查、多位端口保持、保存映射／嵌套路径重定位及5份完整递归费用／CEC回放通过。当前继承5份完整结果，1位t0从原ABC映射重建SDC／ODB接续，不重跑Yosys／ABC，物理封装调用仍收费。4任务×4线程滚动采108个拟合侧任务，36 test锁定，协议／生成器／特征／SDC／质量门槛及12类父模型不变。监看命令为`python3 -B -m experiments.arithmetic_dse.model_m2_state_collection_v4 status --folder build/step7-state-boundary-20261105-v4`，旧v1–v3为解析／支持失败历史。

16:16后继见第四章§7.33：状态银行train72／72、validation36／36完成，完整108任务／216阶段行／648路径及549收费叶命令回放通过，并从原Liberty重建单元面积／sequential表。v3日志别名故障实际覆盖两份v2支持command.json副本，本轮以观察字节hash、保持的原manifest／成功日志／GNU time／账本及另付费v3失败全链明确追溯；数据集support_sidecar_reconciliations保留事实，不原位还原、退款或冒充原副本，物理结果未被该支持副本写入影响。

状态面积仍比较原四类候选，训练非负系数，validation按原20%／50%门槛和归一化MAE等选择：synth中位0.783863%／P95 5.310108%、grt为1.623251%／7.128407%。input／register边界按合法train／validation最大H＋最大控制Q-D＋原50ps冻结，分别334.157489／910.766404ps；只覆盖状态银行，375ps下可无正预算，不能宣称任意阶段或正式目标支持。candidate／validation／selection两次字节一致，选择f1f1d08c452e8a01062740cc41b4890d03d48c8cb725354fb895a8093283b7a9。

冻结后另准入原36个独立test，当前服务vulsim-asap7-m2-state-independent-20261105.service、目录build/step7-state-boundary-20261105-independent-v1；入口`python3 -B -m experiments.arithmetic_dse.model_m2_state_test status --folder build/step7-state-boundary-20261105-independent-v1`。65位独立容量点通过后最多4×4线程，采完停止，不自动评价／拟合／发布。评价预先冻结为完整原始回放后一次性使用原面积门槛及每精确目标的独立最大H＋最大控制Q-D覆盖；不调参数／裕量或读取test选择。原12类／正式目标保持，状态独立资格／native绑定、阶段拓扑模型、区间与完整D尚待完成。

2026-11-05后继见第四章§7.34：36／36独立state任务全部完成，原始／Liberty／FF／SDC／RC／CTS CEC／费用回放后对冻结选择f1f1d08c452e8a01062740cc41b4890d03d48c8cb725354fb895a8093283b7a9评价一次，通过原门槛。状态总面积独立synth中位2.454918%／P95 6.146589%、grt为6.401676%／8.624627%；三个精确目标的边界覆盖全通过，grt最小余量105.182022ps，input／register仍910.766404ps，未改50ps reserve或目标／域。独立标签已消费，永久排除后续拟合／验证／算法／裕量／域选择。

新增grt有界组件experiments/arithmetic/evidence/step7_m2_state_boundary_v1/asap7-state-boundary.json，SHA256 0cf99c9944f40aad7f4d4a2a9bb91afcbaf26048ad64d3e6131d5fcafc3bf904；仅受限合成valid_chain银行和原精确ABC／SDC／IO，synth只保留通过诊断。面积含state／control及clock／tap／未归属repair，排除observer，禁止与整阶段算术面积重复收费。原12类模型字节保持；native状态／复位／control绑定、联合算术／正式边界、阶段组合与真实区间仍需资格，full_D_ready=false。375ps可能无正数据预算，目标违例／负hold行仍保留，误差通过不改写物理可行性。

model_m2_state_evidence的144测量／288阶段／864路径便携和完整external回放通过；实际Git可见源副本禁读原build／工具／活账本、PATH为空并禁子进程时亦通过，压缩池篡改拒绝。支持副本覆盖的实际字节／成功及失败全链保留，不原位恢复或退款。新包约23.40MiB，verification绑定四条实际核验与结清账本前缀；当前无后台EDA／自动后继采样，未提交Git，步骤七／完整D／九例36条仍未完成。

2026-11-05现行后继见第四章§7.35：新原生StateCostQuery从完整放置／实际物化寄存器导出typed状态、变量掩码／逐位reset及每级valid使能，九个公共VUL原始核＋3诊断的投影／物化与实际RTL、5负例通过，PPA0。外部输出capture显式请求，输入service外壳不隐含计费。原生首级是内核输入valid，后级按前级valid，同cut共享；原v1全部寄存控制／word-level轮转拓扑不能仅凭同名valid_chain授予native资格。FP还需5／4的已知零孔洞，价格仍未放行，旧发布字节／资格不改。

用户已明确确认按原生协议补合成银行后继。model_asap7_native_state_v1.json登记48新源／144任务，72 train／36 validation／36 locked test，ABC1500ps、精确SDC40500／1500／375ps、IO0.2T；旧独立标签永久隔离，旧发布参数仅作不可改基线。包含2／3级、非均匀生存期与均匀大银行、零孔洞／高零填充和新复位上下文，不复制正式／保留整图训练。原20%／50%面积门槛与50ps reserve不变，PI-D与Q-D分开读取，input H扣一次0.2T；不继承其他周期、连续目标或正式边界。

新状态接口checks-v5及6合成银行×80周期／8240状态检查／258个当前iv与旧valid不同周期的软件proof通过。两个train容量先导data1746＋valid3／data377＋valid3均通过完整物理／四标签／CEC，峰值595.723／410.527MiB。当前服务vulsim-asap7-native-state-20261105.service，目录build/step7-native-state-20261105/collection-v1，最多4任务×4线程／8GiB，只采108拟合侧任务；采完停止，不自动拟合／独立／发布，无自动重试。状态命令为`python3 -B -m experiments.arithmetic_dse.model_native_state_collection status --folder build/step7-native-state-20261105/collection-v1`。完整144任务与后续额度均已按原共享账本准入；原“无后台”只属§7.34检查点。整阶段需求仅为mission/asap7-stage-topologies-draft.md草案，未准入新EDA，完整D／九例36条仍未完成。

2026-11-05后继见第四章§7.36：原生train72／72、validation36／36全部完成，108任务／216阶段／864路径及576收费叶命令、Liberty／FF／SDC／RC／完整CTS CEC回放通过，原始hash19446份。新model_native_state_fit按原四候选和20%／50%门槛选择，状态面积验证synth中位2.717283%／P95 16.535639%，grt为5.235279%／32.412883%。新typed grt候选未过门槛，旧固定基线也保留；按既定归一化MAE选择bits/signals，不宣称每项均优于旧模型，不用旧独立数值调参。

input／register开销synth均316.470119ps、grt均803.206085ps，按分开的注册H＋Q-D和已扣一次0.2T的输入H＋P-D及原50ps reserve冻结。candidate／validation／selection两次字节一致，选择SHA256 1c066bdfda97f8842d24abbb58c74c625caba3c456434cf35ddff1b111b975d0；质量仍awaiting_independent_test，原生生产价格和联合算术／正式边界尚未放行。旧状态v1参数／910.766404ps及原12类保持。

冻结后另准入原预登记36项新原生独立test，当前目录build/step7-native-state-20261105/independent-v1、服务vulsim-asap7-native-state-independent-20261105.service。独立角色／选择／源／线程在每个收费叶前核验，源码在首次test前冻结；外来任务及输入边界不足的纯数值负控拒绝。独立容量点真实data461＋valid3、峰值403.531MiB通过，最多4任务×4线程滚动采集，完成后停止，不自动评价／拟合／发布。当前入口为`python3 -B -m experiments.arithmetic_dse.model_native_state_test status --folder build/step7-native-state-20261105/independent-v1`。完整36项后原始回放、独占一次性评价原面积门槛及每目标input／register独立覆盖，不后验改reserve或域；此处36项不是正式ABCD36条，full_D_ready=false。

2026-11-05当前结果见第四章§7.37：新原生独立36／36已完成，完整原始／Liberty／FF／SDC／RC／Q-D及PI-D／CTS CEC／费用回放后，对冻结选择1c066bdfda97f8842d24abbb58c74c625caba3c456434cf35ddff1b111b975d0评价一次。状态总面积synth独立中位3.755745%／P95 17.635903%，grt为6.034688%／18.922855%，原20%／50%通过；input／register覆盖三个精确目标均通过，grt最小余量183.134460ps。参数、域、803.206085ps边界及50ps reserve均未改；新标签永久排除后继拟合／验证／选模／裕量／域选择。

新增grt后继experiments/arithmetic/evidence/step7_native_state_v1/asap7-native-state.json，schema arithmetic-native-state-qualified-v1，SHA256 ce280fb25047038d0a9ff80084d744191419546d72072864f316ec7c4a8d9bff。仅原生协议合成银行及原精确ABC／SDC／IO；旧12类和旧状态银行保持。真实查询结构／RTL已核验，不等于生产价格已接通：production_price_binding_qualified=false，外围状态／联合算术与正式目标／整阶段／区间／完整D仍待资格。

model_native_state_evidence的144银行／288阶段／1152路径及12原生结构便携、完整external、隔离Git视图（禁原build／工具／活账本、PATH空、禁子进程）回放通过，压缩池篡改拒绝。新包约20.52MiB，verification绑定实际四条核验和全历史结清前缀，旧失败费用不退款；当前无后台EDA或未结算任务。原§7.36采集中仅为历史检查点，未提交Git，正式九例ABCD36条和完整步骤七未完成。


生产组件消费后继（2026-11-05，fix第四章§7.38）：`arithmetic-component-manifest-v1`以components_passed引用不变的primitive及native-state发布，核对内容／profile／父链和共同measurement身份；不把组件域取并集。typed状态查询从真实图／协议／完整placement重新构造，数量公式之外仍检查mask／reset／enable／独立通道／寿命／容量／capture所有权。当前消费者复位子域保守限于采样的零／全一／交替／每三位一位，任意语义复位尚不放行；九例原始银行目前0／9。此范围限制来自预登记采样上下文，不从已消费测试选择新域；原模型参数／发布域／测试结论保持。175次消费价格及旧回归通过只证明有界组件绑定，联合算术／service边界、相关状态、全候选／位置、整阶段／真实区间及完整D仍未资格，formal36未开始。证据及复现见 `experiments/arithmetic/evidence/step7_native_state_binding_v1/README.md`。


全候选静态需求后继（2026-11-05，fix第四章§7.39）：生产与审计共用候选registry／资格／去重／K16，21个有序图与旧报告及当前C一致；108个不同合法C视图、582非法提案和每候选实际状态物化核对通过。诊断累积多个域条件，不因第一个复位拒绝遗漏相关源／无完整链／移位补零／非齐整宽度至66位／18通道。140种阶段需求描述、34组实际及42组保守区间、17类目标参考键和唯一计费责任已登记于model_asap7_m2_joint_requirements_v1.json。该配置是静态需求冻结，physical_admission_allowed=false；原始单元／路径归属提取、合成源／完整任务／划分／容量／预算准入与数值目标尚未完成。未来D位置仍逐查询校验，不能把108个C视图写成穷举。未读正式PPA或独立标签做选择，无新拟合／PPA，原模型及失败封存保持。证据复现入口为experiments/arithmetic/evidence/step7_d_requirements_v1/README.md，默认消费冻结生产者，活动源码可按后继演进。


目标参考后继（2026-11-06，fix第四章§7.40）：model_asap7_m2_reference_v1.json明确17个单原子微基准仅作参考，排除模型拟合与独立模型测试。固定ABC1500ps／SDC40500ps／IO0.2T，不按后验Tmin调目标。软件17×144周期／19728状态检查、未映射几何及九项标签负控通过；真实输入service独立使能、内部前级valid捕获及公共外部无条件捕获分别实现。Q-D保留完整路径，数据分量止于最后core输出，捕获后缀与时钟／setup／skew／uncertainty分开；输入IO仅扣一次。OpenDB连接与Liberty pin／函数决定互斥面积所有者，未知功能单元拒绝，不将observer或共享clock重复计费。

首轮三个综合成功后因名称转义／根常量读取失败；v2只读续作因缺原生综合面积JSON停止，均未重综合或执行grt。v2读取器及v3收集器以明确祖先hash继承三个综合及1_synth.json，不伪造新命令收据；完整暂存回放通过后才启动collection-v3。三个grt容量先导通过，当前最多4任务×4线程／8GiB采余下14项；共享Ledger、失败／费用保持、无自动重试。专用参考准入不更改旧需求文件的physical_admission_allowed=false，不转授S／G／I／正式36条资格。采完退出，不自动拟合／独立／数值目标冻结；完整原始回放及D_ref／H_ref仍待后续，full_D_ready=false。

参考验收后继（2026-11-06，fix第四章§7.41）：17／17采完、34阶段／272路径及108实际付费叶／4151文件完整回放通过；Liberty area／FF／pin／函数、单元唯一归属／SDC／RC／完整CTS CEC成立。前三份综合复用，17 synth／17 grt／74 support叶不含外围前检／封存费用；六个读取／续作失败保留。ite_u16 grt hold为−0.321049ps，setup标签有效与hold未通过分开报告，未据此重采／改目标。

step7_reference_v1约6.4MiB，便携原始标签／DAG回放、完整本机external和隔离／篡改通过。首次external冻结源树缺活账本失败保留，v2只显式指定真实Ledger后通过，不改旧证据或重采。数值目标仍未冻结：target-proposal.json提出每案例取必需data joint H最大值，控制／input／external完整路径另报参考上下文诊断，不重复并入D_ref、无新增reserve，沿原ceil(H_ref+1.5D_ref/L)。现行多标签H_ref汇总尚无明确登记，提案待用户按grilling确认后再版本化冻结；没有用该提案准入S／G／I。当前无后台／未结算工作，full_D_ready=false、formal_36_complete=false，旧模型及已消费测试保持。

正式目标后继（2026-11-06，fix第四章§7.42）：用户明确“采用上述分离口径”，新policy保留data joint H最大值、其他完整路径另报诊断及零额外reserve。真实contracts.freeze_target_batch／target_period_ps按未舍入参考和完整原始图／固定L冻结九例周期1431／1119／4528／11913／3141／4162／1253／14897／3385ps；model_asap7_m2_targets_v1.json同时绑定case／reference／规则hash、精确预算／rho_ref，原参考及提案字节保持。step7_m2_targets_v1约0.35MiB，生产公式／完整external／隔离／目标篡改拒绝通过，新增support5、PPA0。

联合需求v2显式继承v1及正式目标，R完成，S／G／I绑定九个ABC1500ps／精确SDC／IO0.2T上下文，仍待合成源／完整划分／时钟采样网格／协议与归属前检／具体容量预算。numerical_targets_frozen=true不转授模型资格，model_target_domains_qualified=false、physical_admission_allowed=false、full_D_ready=false；无新EDA或正式36条。不得使用近邻周期价格、旧独立测试、state银行总开销或整图后验PPA补资格，也不因预测／实测不可行调整冻结目标或L。

一般状态S后继（2026-11-06，fix第四章§7.43）：model_asap7_general_state_v2.json登记24个独立合成源×九冻结目标，共108 train／54 validation／54 locked test，整个源及所有目标／阶段同split，已暴露宽度的新复位／掩码／相关源／生存期上下文。三种service写使能（包括input-valid保持）、native前级valid数据使能／逐拍valid、external无条件捕获分别核验；30种声明宽度至66位、18通道、一般复位及不完整链。共享注册根经不同两输入XOR／排列／反相产生相关来源，adapter及observer单列；任意算术来源相关性仍需G。原native总价只作不变诊断基线，不能作为联合分项。

最终24源×128周期／93696状态检查、错误external valid门控的实际RTL负控与通用几何通过。collection-v1四个综合成功、grt0，因两份IO序列化差与两份缺native_valid路径停止；导出未用状态口的裁剪／相关位共享已核验，原诊断／费用保留不拟合。v2显式全状态观察／keep及不同两输入相关位，需要新综合；不覆盖v1或重测原模型／R参考。sdc_storage_v3只扩充准确binary32秒IO存储再十进制舍入，四份实际SDC／14项破坏约束负控通过；不改原sdc.py、时钟／I/O政策、门槛或目标。

collection-v2另行具体准入全部216任务、136800s墙钟／547200sCPU／54GiB及后续预留，六个train容量点完整两阶段／实际FF／互斥归属／九路径／SDC／RC／CTS CEC通过（grt约51.75–73.57s，峰值最高569.82MiB）。当前vulsim-general-state-r2-20261106.service最多4任务×4线程／8GiB只采162拟合侧任务，54独立锁定，无自动重试／拟合／独立／发布。原面积中位20%／P95 50%及50ps reserve保持，采完原始回放／验证冻结后再另准入新test。G／I／完整D／正式36条未放行；状态与版本父链见mission/asap7-general-state-handoff.md，运行中不宣称全局结清。

一般状态S验证冻结后继（2026-11-06，fix第四章§7.44）：108 train／54 validation完成，18个源／162任务／324阶段／2916路径完整回放，972收费叶／34772文件hash核验通过，旧四失败综合诊断不继承数值标签，提取时54 test运行目录不存在。拟合执行定义model_asap7_general_state_fit_v1.json及源在提取前登记。三个train-only NNLS候选比较bits／signals、typed-state和逐精确SDC的typed-state，无截距／后验面积裕量；每阶段整组选三所有者模型，各自原面积中位20%／P95 50%先通过，再比较归一化总绝对误差、序列化大小和稳定名称。synth／grt均选择per_owner_NNLS_typed_state，功能状态／控制分项与shared_clock／shared_physical／root_boundary_repair严格区分；原native总价只作不变域外诊断。精确周期面积明细只报告，不事后新增门槛。

grt验证中位／P95为input_service 0.23707%／0.56572%、native_state 0.17054%／1.75095%、external_state 0.04248%／0.16485%，并非整阶段PPA误差。每阶段／九精确周期／八非birth路径类边界冻结为max(0,max训练验证H)＋max训练验证delay＋50ps，分别保存最大值见证，输入IO仅扣一次；birth适配器路径只诊断，不转授任意算术相关性或G联合资格。fit-v1／fit-v2的四份结果逐字节一致，candidate SHA256为5300b9a7076a9bc583ba5f1bc651cd65904bfaf1dbcb71042576774a85fb89da，selection-freeze SHA256为16dba85ab9237c6be1a7d8416f00d2571e03d4de32808fb37158fd297696a834，候选仍为awaiting_independent_test／production_price_binding_qualified=false。

独立后继model_general_state_test.py在测试前绑定提取／评价实现及50份源；independent-v1/admission.json SHA256为16f9d0cfe72f5e09c984ddfe6fce019b83c495139f4d37887d9ab488fd92b745。只放行原六个test源×九目标、54新synth／54新grt；每收费叶绑定selection-freeze，错角色／错周期／改candidate拒绝。test-04-t0／t8自身完整容量通过后最多4任务×4线程／8GiB，总CPUQuota1600%、MemoryMax36GiB、TasksMax512；墙钟／CPU包络36000／144000s、存储13.5GiB并保留后续额度。服务vulsim-general-state-independent-20261106.service采完停止，无自动重试／评价／拟合／发布；旧拟合驱动的54 test锁保持，不能由其续跑。

采完独立原始／收费祖先回放后严格一次性评价：各所有者／阶段原面积中位20%／P95 50%保持，每精确周期／非birth路径最大H＋delay须不超过冻结边界，不据test调reserve。写test-consumed.json后永久排除后续拟合／验证／算法／裕量／域选择；只有全部grt门槛通过才有组件发布资格，后续另做实际生产所有权／查询绑定及便携／external／隔离／篡改核验。S尚未发布，G／I、完整D和正式36条未放行，当前状态／命令见mission/asap7-general-state-handoff.md；所有旧失败及费用保持，运行中不宣称全局结清。

一般状态S首轮独立结论（2026-11-06，fix第四章§7.45）：54／54完成、错误0，108阶段／972路径、324收费叶及11658文件hash完整核验。一次性评价synth通过，grt三个功能状态／控制面积分项均通过原20%／50%：中位／P95分别input_service 0.32954%／1.21461%、native_state 0.28542%／1.71838%、external_state 0.02239%／0.16256%。grt控制边界69／72，1431ps native_enable超14.537323ps、4528ps native_valid超60.583038ps、11913ps native_valid超2.266129ps，整体失败、发布为空。原50ps reserve／参数／域／九目标不改，test-consumed.json将原54项永久排除后续拟合／验证／算法／裕量／域选择。相近的大银行在validation中已有覆盖，不能将本轮归因简化为缺大位宽或时钟数值错误；原始控制buffer分支与负载上下文差异按诊断保留。

216银行／432阶段／3888路径与四份旧失败综合诊断、1308收费收据的原始便携／完整external／隔离／篡改核验通过。约106MiB全原始包原字节保存在build/step7-general-state-20261106/failure-raw-archive-v1，Git使用另立约1.54MiB的step7_general_state_failure_v2数值封存。小包便携模式重生成语义特征、重算固定验证／边界／独立结论和付费核验收据，不宣称独立包含所有物理原始报告；external读取大归档完成完整物理回放，存储迁移／manifest hash保持可追溯。支持启动入口的失败及计费上下文前置拒绝保持，没有退款或新增物理重测。

控制边界后继（2026-11-06，fix第四章§7.46）：用户明确选择保留面积参数，只补控制边界。model_asap7_general_control_v1.json（SHA256 51cbbfc436de2c689907374f7b02d2ce588bf76e4ad3d4ed99490b5f38bd7193）绑定原candidate／selection／162拟合数据／失败verdict／test-consumption；新准入SHA256 14cc02d03991d5d8d83f080c865c7a51b350d34e373be03fba50976c3e36be00，46份源及原面积冻结副本守卫通过。只允许native_enable／native_valid新模型；三个面积系数与六类其他非birth边界不变，继承配置中的旧面积候选不启用，area_refit_permitted=false。最终仍同时检查全部面积分项和八类非birth边界，不能把分项合格当作S已发布。

新24源×九个原冻结周期＝108 train／54 validation／54 locked test，新盐值控制reset／两输入相关来源和每级寿命／使能负载；整个源全部目标／阶段同split，与全部旧源语义签名分离。独立性为已见宽度上的新控制负载／复位／来源／寿命上下文，不宣称未见位宽或任意算术相关性。24×128周期／86784真实状态检查、544个service-valid保持区分周期、15867次invalid external捕获检查、错误门控RTL负控、通用FF几何及各split全部30宽度通过。新训练源最大使能位负载552、native data位779；容量仍由四个具体物理先导授予，不由静态上限外推。

两个控制路径的候选与规则在采前登记：跨九个已登记周期的train最大值基线、静态控制负载NNLS、带九个精确周期指示的NNLS。特征仅取语义使能位负载及sqrt／log、词分支数、valid目标数、原生状态／复位one位、输入／external位数；NNLS上界校正为train最大正残差，另加原50ps工程reserve。每阶段整组选两路径模型，全部旧／新validation覆盖优先，再按平均预测上界、序列化大小和登记顺序选择；原54 consumed test不得试新算法、校正或选择域。拟合实现／执行、字节复现和新54 test准入仍待采后完成。

原162 train／validation按完整身份复用，不重跑或制造新物理命令；新全216任务预留136800s墙钟／547200sCPU／54GiB及后续额度，当前服务vulsim-general-control-20261106.service只采新162拟合任务，54新test锁定。train-04／10在1119／14897ps四个完整容量先导后，最多4任务×4线程／8GiB，总CPUQuota1600%、MemoryMax36GiB、TasksMax512、Restart=no；采完停止，无自动拟合／测试／发布或重试。失败保留、共用原Ledger；当前命令和检查点见mission/asap7-general-state-handoff.md。S后继资格／生产消费、G／I、完整D／正式36条仍未完成。

控制边界后继验证冻结（2026-11-06，fix第四章§7.47）：新108 train／54 validation完成、错误0，原新54 test仍锁定。model_general_control_fit.py及model_asap7_general_control_fit_v1.json在原始提取前快照登记；原162测量逐原始标签／身份复用并完整回放，新162任务加入，合计36个拟合侧语义源／324测量／648阶段／5832路径，1944收费叶及69199文件hash核验通过，PPA0。实际Liberty面积／FF／pin／函数、状态几何／唯一归属、SDC存储v3／RC、原生面积JSON、完整已存CTS CEC及计费祖先一致；合并数据SHA256为cda58a769d49dd1ea61a957cedadcf9a79d776ebfb64bcfa572712c08a243500。旧54 consumed与新54 locked独立物理标签不进入拟合／选择。

三个面积模型原参数、六类保留边界的九精确周期完整参数均保持；面积在原／新／合并验证分别通过原20%／50%，六类保留边界合并验证全覆盖、synth／grt最小余量均50ps。新增54项validation的grt功能状态／控制面积中位／P95为input_service 0.20269%／2.96235%、native_state 0.56409%／1.71520%、external_state 0.04634%／0.24574%；这些不含共享clock／physical／repair，非整阶段PPA。

仅两控制路径按预登记候选／顺序、train-only系数及最大正残差校正比较；原50ps reserve保持，validation仅用于覆盖和平均上界／序列化大小／顺序选择。synth选择train_NNLS_semantic_control_load，最小控制验证余量40.969143ps；grt选择train_NNLS_semantic_control_load_exact_clock，最小余量97.135391ps，平均预测控制上界641.948721ps，跨周期最大值基线718.770218ps。这是验证选择量，不是独立泛化或整图收益；九个精确目标／ABC1500ps／IO0.2T保持，不插值或转授任意算术相关性／G联合边界。

fit-v1／fit-v2的candidate、validation、selection-freeze三文件逐字节一致；candidate SHA256为ed506072834b9744ff8a817b1e071a92d71e3ee080db6edc48781e2723696a17，selection-freeze SHA256为b27fced59c3a61b2fbcebd37cc52346c4fa2f523305b56acaaa9680e059852e3。regression/arithmetic_general_control_fit.py核对1728次实际验证行上的冻结独立查询、原面积／六类参数不变，以及错误周期／负值／非有限值和validation／test校正拒绝。条件上界反例拒绝“所需时延较小但超过自身预测上界”的样本，独立评价必须逐样本检查，不能只取最大所需时延样本。

model_general_control_test.py在测试前绑定53份生产／拟合／评价／回归源；独立准入SHA256为f7dbf878b7041a17f04dc9a08850b783ab303a930657ef54e00e397007c25265。错角色／错周期／错线程数／改candidate均拒绝，逐收费叶绑定selection-freeze，守卫无额外物理预约。新服务vulsim-general-control-independent-20261106.service先采test-04-t0／t8两个自身容量点，再最多4任务×4线程／8GiB，总CPUQuota1600%、MemoryMax36GiB、TasksMax512、Restart=no；54新synth／54新grt加support包络36000s墙钟／144000sCPU／13.5GiB，并保留后续额度。采完停止，无自动评价／拟合／发布／重试。

采完完整独立原始／收费祖先核验后，按冻结函数一次性评价全部三个面积分项与逐样本／精确周期／八类非birth边界，原门槛／50ps不改。写test-consumed.json后新标签永久排除后续拟合／验证／算法／裕量／域选择；只有全部grt门槛通过才发布有据S范围并另做生产绑定／发布核验。候选仍为awaiting_independent_test，production_price_binding_qualified=false、full_D_ready=false，旧首轮失败不改写；G／I、完整D／正式36条仍待，当前状态见mission/asap7-general-state-handoff.md。

一般状态S新独立通过与限定发布（2026-11-06，fix第四章§7.48）：新54／54全部完成、错误0，108阶段／972路径、324收费叶及11658文件hash原始核验通过。冻结参数一次性评价synth／grt均通过三面积原20%／50%门槛和八类状态边界72／72。grt功能状态／控制面积中位／P95为input_service 0.33944%／1.09599%、native_state 0.48657%／0.90230%、external_state 0.04684%／0.17216%；synth为0.09759%／0.12805%、0.37001%／0.88684%、0.05966%／0.06477%。grt全体状态路径最小上界覆盖余量37.372788ps（4162ps external_data保留边界），两控制路径最小68.873866ps；synth最小44.471734ps。此为上界覆盖余量，非目标setup slack，面积非整阶段PPA。原三面积系数、六类边界参数、九目标／ABC1500ps／IO0.2T／50ps reserve均不变，test-consumed.json将新54标签永久排除未来拟合／验证／算法／裕量／域选择，首轮失败与旧已消费标签保持。

step7_general_state_v1/asap7-general-state.json（schema arithmetic-general-state-qualified-v1，SHA256 1b61a68d80b704532ff38483a034ec2c03de921448095deb6acdcbbb00be383d）仅发布ASAP7 grt合成原生银行三所有者功能状态／控制面积、六类原精确周期边界及native_enable／native_valid冻结语义控制上界函数。一般复位／已知零位／部分寿命／service使能／无条件external捕获限定在登记合成域，来源相关性只含两输入XOR／排列／反相；shared clock／physical／root repair、adapter／observer不在分项面积中，不得与未来G或旧native总价重复收费。production_price_binding_qualified=false、full_D_ready=false、formal_36_complete=false；发布不自动更新C++工厂、旧组件清单或全部真实银行／候选／位置资格。

原162拟合、新162拟合及新54独立，共378银行／756阶段／6804路径、2268测量收费叶封存于build/step7-general-control-20261106/release-raw-archive-v1，37个32MiB内容池分块、144400007字节。完整原始便携回放、实际Liberty／工具／完整已存CTS CEC external、原树读取禁止的隔离／篡改均通过，不执行新EDA／SAT。Git小包2594036字节，包含固定数据／源／发布／收据，便携模式重生语义特征并重算固定验证／选择／独立结论，external另读原始大归档，二者范围不混称。

model_general_control_evidence_v2为当前发布／复现入口。verify、retrain、verify --external和isolated全部通过；retrain只用冻结train／validation重算三个控制候选的全部NNLS系数／校正及选择，精确比较，不用独立标签拟合。由于NumPy／SciPy在用户Python包目录，v2以明确数值运行库声明允许该安装目录／元数据并核对冻结版本，仍禁止原项目／build／账本及其他原home读取、PATH为空且禁回放子进程；不改原数值生产者或原始归档。隔离数值／训练复现、文档／模型／能力清单篡改负控通过。实际Git可纳入的13发布文件与manifest字节一致，最大单文件1493018字节，大归档被build忽略；此为本组件Git视图，不是全项目步骤九。发布manifest SHA256 a05f864ed99407fbb30747043e1dc8e153284bedae27ca103e84a48e043571f4，原始归档manifest SHA256 b227bf5a4955dfa7cf3f71d7746316a66d9ab89d747ecc3793dc1d9caaa3d2ac。

本轮原始核验／发布／复现／Git视图新增12 support、synth／grt／final增量0，原失败／费用不退款；结清前缀2042 synth／2016 grt／16 final／8047 support、12121 entries，叶墙钟232268.820083s／CPU509320.29s、pending／active／unsettled0，无本实验后台EDA。S下一步为实际C++ service／native／external特征／所有权／价格／条件边界绑定，并补G联合阶段、I真实区间及完整D选择／RTL／正式36条；完整四平台步骤七及688条未关闭，未git add／commit／push。
