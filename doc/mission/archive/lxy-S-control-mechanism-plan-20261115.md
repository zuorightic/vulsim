# W1—W8阶段归档（2026-11-15）

**状态：已归档，不作为后续执行指令。** 用户要求恢复到`672df3e`／RTLzz `28a4f1d`的v10 test基线。本文保留原规划、进展、失败和验收记录；其中“现行／下一步／必须”只解释形成时的阶段。模型未达精度结论不因归档改变。当前入口见[mission导航](../README.md)，恢复清单见[v10-restore-20261115.json](v10-restore-20261115.json)。

原路径：`mission/lxy-S-control-mechanism-plan.md`。归档调整了相对链接；原始字节、后v10代码及证据保存在恢复前备份，身份见清单。已撤下的预算后继链接指向该本机备份。

---

# S native_valid：保持现有发射的只读机制后继

**新阶段承接：** 本文件保留只读机制包及共同因素后继的登记／证据，后续S／shared工作按[新计划W4](lxy-W1-W8-stage-20261115.md#general-model-W4)推进，冻结独立／实际算术联合按[W6](lxy-W1-W8-stage-20261115.md#general-model-W6)。原十步已归档，本文旧范围和“下一步”只解释相应包，不另成排程；旧只读包0新物理优化的约定不与后继因素测量混记。

日期：2026-11-13。用户已确认按审查修正后的方案推进。本包的train只读控制锥、四阶段归因及统一诊断消费已完成，**0新synth／grt，尚未形成合格的新S价格**。初始登记见[§7.94](lxy-W1-W8-stage-20261115.md#S-control-readonly-mechanism-successor)，执行结果见[§7.95](lxy-W1-W8-stage-20261115.md#common-four-lines-successor)。

## 目标与已有证据

保持当前RTL发射、标签语义和公共D绑定，检查能否用发射前可计算的控制源、负载、使能域、状态规模、数值T及冻结流程信息解释native_valid。mapped树深、单元型号、实际buffer数、电容、布局面积及实测slack只用于离线归因，不进入在线Query或模式选择。

已有train数据为9个银行、33个实现：原9银行×3周期的27点，加上其中2个银行的650／900／1800ps响应6点。原记录中的“27个train银行”按27个实现解释。33点的synth、placement、CTS、grt数据库及synth／grt连接表均已核实存在，实际ABC=SDC。旧validation为5个银行／15个实现，已消费，只保留回归职责；独立职责继续锁定。

复用[§7.93证据](../../experiments/arithmetic/evidence/common_family_continuation_v1/README.md)：两个train银行的12个实现／48条路径已完成cell／wire／H守恒分解。当前native_valid候选validation源median为23.44%、P95为28.10%，保护348.64ps，保持失败。六周期曲线仅支持“实现有明显变化”，不预设所有银行只有两个档位。

控制路径标签保持`R = d_comb + H = T − slack`。后端停止优化已满足约束的路径，不表示标签被截断。实测slack与R的相关性不是独立机制证据；本包不改成“最快可达实现”的标签口径。

## 执行顺序

1. **预登记与复用。** 新建产物根，将临时脚本放在`tools/`。登记准确的source／T／stage／原文件摘要、缺失读数、support资源和停止条件；先使用已有连接表、路径及日志，缺项才调用只读OpenROAD／STA。已有48条分解不重复采集。
2. **接口与标签审计。** 对照`state_control_queries`、`state_control_features`、`state_control_geometry`、`state_control_response_v2`及当前16项拟合基函数，区分字段缺失、已有字段未入拟合和表示能力不足。统一候选的特征版本及消费入口，确认不把新系数传入旧版`aggregate`特征函数。
3. **控制组合锥与阶段归因。** 从实际Q／QN出发，沿合法组合弧和连接，到寄存器数据端截止；包含buffer／inverter、逻辑门、分支、共享及重汇合，分别标记数据使能、valid传播和自身保持。按synth→placement→CTS→grt定位差异最早出现的位置。单元、连线和H继续守恒，比较最差路径见证是否变化；阶段相关不直接宣称单个命令的因果作用。
4. **假设与可计算性。** 检查优化优先级／停止机制、综合映射变化、电气修复、控制分组、空间规模及见证切换。各假设均列“离线证据、发射前输入、反证／证据不足条件”。面积代理必须由冻结的预测函数计算，不能读实测面积，也不能与待拟合S时延形成循环依赖。若需模式函数，模式条件也必须由Query计算。
5. **train内最小候选。** 按完整银行留源，银行的所有T、控制源和路径一起留出，不把33个实现随机拆分。先检查特征秩与相关性，再按预登记规则比较有限候选。保留原基线，不扫描旧validation；使用原定源等权方法及固定保护推导，不手工抬reserve。
6. **可消费性、冻结与回归。** 新特征先核对Python／C++及真实图可提取性；对505个实际placement检查逻辑投影，不将其转授物理资格。冻结候选、特征、支持／拒绝、保护算法和实现身份后，对旧validation回归一次。
7. **交付与分支。** 可行时交付冻结候选及回归结果，再进入对应独立S职责和实际算术／完整阶段验证；没有可行候选时交付证据不足处、已排除假设及最小后继对照清单。不能把“当前解释不了”直接认定为只能改变发射或接受大保护量。

## 验收与停止条件

本包**0新synth／0新grt／0新ABC／0新placement／0新CTS／0物理repair**，原数据库、网表和约束保持摘要不变。只读报告写入新产物目录；STA使用该实现保存的匹配SDC，修改时钟的诊断不能变成新T下重新实现的训练标签。

除源median≤15%、P95≤35%外，分别报告控制源／路径子域、低估尾部、保护幅度、保护漏覆盖、保守程度及支持／拒绝。不能依靠缩域或仍然过大的保护量宣布修复完成。单路径保护漏点不等同于整设计错误可行数。

若需新物理对照，另立明确假设、准确请求和资源的后继，本包仍维持0新物理调用。若需要改变RTL发射、标签语义或研究范围，再由用户决定。只读归因及已授权范围内的软件验证无需逐项再次确认。公共D、原价格、S面积／shared和G组件保留各自既有资格；S候选或软件提取通过不表示完整D通过。

## 最新资源授权

用户本轮明确表示物理调用额度不应阻塞八例实验，优先目标为这几天完成工作。原4096次上限及688次储备不再作为需要再次征求用户选择的固定限制。后续物理工作在准确批次、代表先导及时间估计明确后，显式更新策略／累计账本身份；保留全部历史记录，不清零，不绕过记账。

全局4任务、每工具4线程／8192MiB及现有单任务超时继续执行。调用数扩容不等于放行任意大矩阵；容量先导后按观测耗时安排有限批次，报告日历时间与累计叶时间。四线执行后继已迁移至policy v10（结算后元数据后继v11）／budget v5，保留28129条迁移前记录；synth／grt容量各8192，累计叶wall／CPU容量512／2048小时。S本包仍0新物理优化；Mux与G的10点准确批次单独登记，不将额度当成已准入调用。

## 四线执行后继的实际结果

完整根为`/home/zyrv/vulsim-artifacts/common-four-lines-20261113-v1`。9个train银行／33实现的synth、placed、CTS、grt共264个控制组合锥已检查；132个synth／grt锥中，实际数据使能、valid传播和自身保持的sink数与prospective Query全部一致。所有路径沿实际连接及Liberty弧，mapped深度／单元只保存在离线归因中。

相对500ps的48组source／control／T对比，所审计全锥摘要最早变化均在placed；单独看下一valid FF的分支门深，34组最早在placed变化，14组四阶段门深均不变。对33个实现的保存日志核对后，placement包含移除综合buffer、时序驱动repair及buffer重组。这定位了应继续调查的阶段，没有证明某一条repair命令独自造成时延差异，也没有证明整个synth网表在各T完全相同。`repair/S-09ddf99a74e6cef4`的native分支在1500／3000ps为5级、其余四个T为4级，仍是离线解释，不能将该源或精确T编号作为在线分档条件。

旧`state_control_response.aggregate`只重建早期特征。新`state_control_consumer`诊断入口改为从输入宽度、逐级实际保留word、外部状态、服务语义和数值T计算v3特征，检查模型版本，消费原冻结S参数；公共价格请求继续拒绝。33个train银行实现与505个实际placement×2服务语义，共1043组结构的Python／C++特征和同参数价格一致，另7项身份／范围／公共资格拒绝通过。它解决调用链问题，不改变native_valid 23.44% median、348.64ps保护的失败结论。

本包未重拟合S、未使用validation选特征、未解锁独立源、未提高reserve。现有证据不能可靠地把物理树变化转成发射前模式判定，下一步应针对保存的placement前后检查点进一步分解valid分支的驱动、负载和H，再登记可计算的流程／逻辑负载假设；不把偏差交给G。

两次读取恢复均保留：首批66次只读导出的相对输出落在共享cwd，不能逐点绑定，因此不采用；后继使用每请求独立绝对输出，66次只读导出完成并核对原DB摘要不变。中间两项因旧admission／task身份在调用前被拒绝，独立后继身份恢复；失败费用和报告保留，没有重跑synth／grt。

## 共同函数后继的冻结验证（§7.96）

原只读机制包的0新物理优化约定保持；另立共同函数因素包已完成18点新银行物理测量，不能混记为只读调用。4个train银行改变输入根使用分布、reset极性及状态规模，2个fresh validation银行在模型／消费实现冻结后一次评价。与旧9 train银行／33实现合并后为13银行／45实现、270条控制路径。

后继由逐路径平均改为消费者实际银行最大值损失，保留逐源辅助和整银行LOSO；控制类型、逻辑sink、输入分布、reset及数值T可在发射前计算。冻结的线性／正值函数选择和数值T非负LP保护只用train，未把mapped树或精确T编号送入Query。最后新银行的native_valid／input_valid误差median为31.17%／32.24%，native_enable／external_valid为7.14%／5.74%；逐源保护漏点3／0／1／1（依次native_valid／input_valid／native_enable／external_valid）。旧银行回归native_valid仍23.12%，external_valid另有1个最大值保护漏点。因此仍不合格，不能靠保护函数降低500ps预留宣布修复。

新增505实际placement的根连接／保留reset投影与两服务上下文、最终真实参数的Python／C++一致性已通过；恒定特征的巨大抵消系数触发两次浮点核对失败，稳定求和修复后通过，旧失败保存。后续优先处理train恒定／近恒定列的导出条件，再用保存的placement检查点区分控制组合树、wire与H的残差，不更改标签语义、不抬reserve、不向G转嫁。新候选需要新的验证职责；本轮2个银行已经消费，不能继续反复选模。独立和实际算术S／完整联合资格保持待验。完整结果与无EDA回放见[共同修复证据](../../experiments/arithmetic/evidence/common_model_repair_v1/README.md)。

## W4稳定拟合与cell／wire／H后继（2026-11-14，§7.102）

本轮用户授权W3／W4／W5后，新增共同函数诊断，原只读机制包身份不改。train每fold按相对跨度1e-10剔除恒定／近恒定列，保留center／scale与归一化参数，正则化共线列；C++同参数核对通过。输入valid原约10⁹级抵消已消除，最大归一化系数约19.25ps。参数／特征／支持／reserve冻结后才消费旧validation回归，没有用其选模或提高保护。

银行LOSO中native_valid仍20.30%失败；已消费2因素银行回归native_valid21.55%、input_valid10.33%，native_enable／external_valid6.38%／7.20%。后两类逐源保护各有1个漏点；native_valid虽本次这些银行未漏保护，过大预留和点误差仍在。旧5银行input_valid18.07%失败，新诊断支持还因reset比例拒绝一个银行的3个实现，覆盖12/15；没有重新宣称旧域全覆盖。旧聚合银行没有逐源标签，逐源漏点不可测，不能把空集合记作0；原报告和仅报告修正都封存。

270条grt控制路径已按同实例cell弧与跨实例wire分解并守恒，162条保留相容synth逐源路径，其余缺失不造零。input_valid的synth→grt cell／H变化中位数为+147.43／−131.79ps；native_enable的cell／wire／H为+207.75／+98.83／+26.24ps，各中位数不可相加。这进一步说明数值稳定、完整R点误差和物理机制是不同问题。旧标签H对端口已经扣除0.2T输入延迟：寄存器R=d+H=T−slack，端口R=T−0.2T−slack；本轮未改变发射或标签。

匹配RepairDesign的驱动／下游电容／wire RC修复与RepairTargetCollector的slack筛选只用于离线解释，mapped树、实际电容、坐标或slack没有进入在线特征。宽／深实际算术S、shared物理复用及完整阶段仍未取得资格；新S不发布。12个新增物理点均属W3 Add批次，有效新验证9点、交换等价复测3点，职责纠正及原费用完整保留；W4本轮只复用既有train检查点。详细数据与无EDA回放见[本轮证据](../../experiments/arithmetic/evidence/common_centered_v1/README.md)及[§7.102](lxy-W1-W8-stage-20261115.md#W345-centered-mechanism-successor)。


## W4路径分量、reset极性与word后继（2026-11-14，§7.103）

本次继续复用13个train银行／45实现／270路径，对同一见证分别试R、delay+H、cell+wire+H，并加入来源／capture银行、逻辑reset-zero／reset-one sink、word分布和数值T。真实映射树、电容、坐标与slack仍只用于离线解释。逐源路径相加后再取银行最大值，未改变标签、发射或原LP保护算法。

v2／v3／v4有限train协议和所有失败均保留，native_valid银行median为20.77%、19.33%、19.57%；最终v4银行19.57%／29.87%、逐路径14.55%／43.71%，仍未达标。其余银行LOSO native_enable9.92%／13.70%、input_valid9.11%／27.06%、external_valid6.25%／13.65%，不抵消valid失败。已消费因素银行native_valid回归30.10%／30.55%；保护漏点与旧银行拒绝逐类保存，旧聚合银行逐路径漏点不可测。

没有为失败S新增fresh物理验证，也没有从已消费回归挑回较好的旧参数。宽／深实际算术S、shared和完整阶段仍待；本轮18点新增物理均属另登记的W3／W5验证，不改写原只读包0新优化身份。完整协议、各版参数、路径分解、逐域回归、消费及回放见[§7.103](lxy-W1-W8-stage-20261115.md#W345-flow-structure-successor)与[证据](../../experiments/arithmetic/evidence/common_flow_structure_v2/README.md)。

## W4服务／native及reset分支后继（2026-11-14，§7.104）

v5继续复用13个train银行／45实现／270路径，不改变R／H、发射或reset功能合同。对native_valid90条路径预登记36项有限候选，加入可从实际状态计算的服务／native来源、reset是否含1、负载与数值T交互，按银行max／逐路径／两分支的源等权损失minimax选定；另外三类S参数与reserve不变。新增input_valid的service capture上下文字段供审计，旧字段保留；该字段没有在本轮重新拟合input_valid中使用。

银行LOSO18.93%／27.18%、native分支16.68%／26.06%仍失败；服务分支7.10%／26.39%，全零reset两银行26.74%／28.35%、混合reset十一银行17.29%／26.09%。逐路径先源聚合13.36%／20.85%，直接按90路径的P95仍39.35%，不能用源聚合掩盖尾部。新LP保护只是原规则的train残差校准，漏点／保守量另列，未手工抬reserve。

冻结后已消费因素银行native_valid21.89%／27.16%，较v4改善而仍失败；旧银行覆盖12/15，其native_valid17.86%／23.12%，median较v4退化。因素银行四类逐路径保护漏点native_valid／native_enable／input_valid／external_valid为0／0／0／1，旧聚合银行逐路径漏点仍不可测。全零与混合reset的分支主导变化是现有train事实，尚不能凭2个全零银行认定通用电气因果或充分辨识。

本包0新物理调用，旧validation及v4数据均为回归，未用于v5选择，独立职责继续锁定。准备回归时读取v4已消费归因报告早于二进制冻结的边界单独记载，未宣称fresh或新的盲测。真实Python／C++消费、按源／路径双口径和禁止推理读文件／启动子进程的回放见[§7.104](lxy-W1-W8-stage-20261115.md#W345-legal-cover-branch-successor)与[证据包](../../experiments/arithmetic/evidence/common_branch_load_v5/README.md)。宽／深实际算术S、shared与完整联合保持待验。

## W4 OpenROAD实际重缓冲与成对reset训练（2026-11-14，§7.105）

按用户建议读取匹配OpenROAD源码，确认placement的`findResizeSlacks`传`initial_sizing=false`并在placement寄生分支执行`fullyRebuffer`；早期gain buffering存在不代表此调用执行它。每sink的required／根arrival预算、正slack四分之一与临界时延1%面积回收，以及GPL相对slack权重，均只用于建立可检验的prospective假设，真实slack／树深／电容不进入推理。

另立12点S train批次，复用四旧银行的几何及biased／uniform根连接，生成相反reset和一致invert版本。软件11264状态比较通过，两点先导后有限采集12/12完成，0失败／重跑。新旧pair全部T同时留出，17银行／57实现／342路径，native_valid114路径、13 fold。新增reset-polarity和competing-state形式未胜出，保留原分支形式和重新拟合参数；其余三类函数／reserve不变。全部36候选和失败保留。

native_valid银行成对LOSO17.54%／29.19%、native分支17.05%／23.97%、原始逐路径P95 38.14%仍失败。全零4银行逐路径源聚合17.51%／30.42%；混合13银行12.86%／15.52%，不能代替银行或尾部验收。新全零银行3T还被旧支持域拒绝，价格消费54/57，未扩大支持。不同训练集和留出分组不能直接宣称较v5改善。

1024 enabled-bit、uniform连接、T=1500ps的pair，stage0全零delay／H为433.70／102.40ps，混合77.46／89.86ps，valid分支门深5→2；stage1则71.39／168.10ps变285.69／178.31ps，门深2→3。完整锥与标签存档；它是reset／一致极性的train观察，不证明某条OpenROAD例程的单独因果，也不能按源或T取价。

冻结后已消费因素银行native_valid24.54%／27.72%，较v5同行21.89%／27.16%退化；旧银行覆盖12/15，17.58%／24.20%仍失败。paired LOSO的LP保护无漏点，但excess median／P95为272.90／379.78ps，保守性保留；因素四类逐路径漏点0／0／0／1，旧external_valid银行max另1漏点，旧聚合逐路径仍不可测。没有根据回归换模、手工抬reserve、改标签或向G转嫁。

本轮新增物理12 synth／12 grt／48 support，区别于旧只读包；新独立验证源0，20算子独立源未读，公共D不变。312严格路径／312删除Liberty弧负例可脱离ODB回放，471特征／价格跨语言核对与推理禁止I/O／子进程检查通过。完整证据见[§7.105](lxy-W1-W8-stage-20261115.md#W345-rebuffer-context-successor)与[便携包](../../experiments/arithmetic/evidence/common_rebuffer_context_v6/README.md)。后继优先处理控制分支／局部负载可预测性及支持边界，宽深实际算术S、shared和W6完整联合仍待。


## W4单向enable压力、成对上游隔离与支持后继（2026-11-14，§7.106）

v7只复用17个train银行／57实现／342路径，0新物理。计算顺序固定为语义状态→共享enable函数→预计压力／松弛代理→valid函数；enable上下文与输出价格必须同一函数，Python／C++均拒绝漂移。13个外层fold先排除整个reset pair及全部T，再拟合上游enable，训练／留出valid特征均由该fold函数生成。14次固定基础拟合与36项valid候选分开计数，训练摘要和228条上下文特征重新核对，留出标签没有进入上游拟合。

松弛代理参考v6保留的OpenROAD回收公式，但不是实际target slack，也没有使用实际电容、slack、mapped树或精确T路由。enable成对LOSO银行7.83%／13.95%、最大单源14.67%；valid银行17.97%／29.24%，比v6同行17.54%／29.19%在median上退化；原始114路径P9536.12%比38.14%略降仍失败。服务6.61%／31.17%、native17.62%／24.39%，不能靠逐路径源聚合12.65%／17.87%遮盖银行失败。全零4银行15.25%／25.39%、混合13银行11.80%／14.54%均按逐路径源聚合单列。

S按全部train数值几何重新推导支持并直接消费本版域，不先消费旧价格；57/57训练实现可诊断，但跨银行留出完整实现仅33/57接受，仍缺未知几何资格。depth是明确数值坐标；一个其余坐标都在范围内的三级软件见证被depth独立拒绝。四类控制路径必须完整，缺失类或上下文被拒绝。支持锚点无价格标签，域推导没有使用回归结果。

冻结后的同覆盖回归valid因素23.61%／24.82%，v6同行24.54%／27.72%，仍失败；旧银行12/15为17.65%／24.30%，较17.58%／24.20%略退。enable因素6.86%／7.89%、旧7.72%／13.66%也较v6略退，训练LOSO通过不代表旧域全面改善。valid／enable新reserve沿原LP校准，paired LOSO逐路径漏点0，但excess median／P95为281.47／386.31ps、155.40／327.63ps；没有手工抬reserve。因素external_valid逐路径1漏点、旧external_valid银行max1漏点仍在；旧聚合逐路径漏点为null。

本次交付可回放的单向上下文和隔离合同，没有完成valid物理模型修复。单个enable压力尚不足以解释服务／native主导变化，下一步应研究局部负载及不同sink分支预算的prospective表示，保留本轮负结果。宽深实际算术S、shared及W6联合资格继续待验，20个算子独立源未读取，公共D不变。见[§7.106](lxy-W1-W8-stage-20261115.md#W345-load-pressure-successor)及[便携证据](../../experiments/arithmetic/evidence/common_load_pressure_v7/README.md)。

## W4语义扇出与完整Query信息对照（2026-11-14，§7.107）

v8在逐bit输入连接上增加根负载集中度、有效驱动数、共享对比例及native／reset／数值T交互，完全复用v7的14份enable上下文及13 fold成对隔离。36项valid有限train比较选中root_pair_reset／linear／path／alpha0.1；银行LOSO17.94%／23.13%，raw路径P9536.56%，native16.48%仍失败。冻结后同行因素银行回归23.61%→31.43%，新增1个保护漏点；旧12/15为17.96%，较v7的17.65%也退化。没有据回归改模、改域或抬reserve，公共D不变。

代码核对发现当前S投影仅保留reset popcount，没有保留位分布和相容invert。另登记准确6点train对照，以两个已有mixed银行生成掩码旋转版本，保持逐root／word popcount、根连接、stage words、服务语义、T和发射器。5632状态比较、7项负例先通过；两个先导后6点全部完成，0失败／重跑。新旧语义身份不同，但在500／1500／3000ps的完整当前Query、所有v8特征及预测逐项相同。新标签不进入冻结v8，未来须与父源及既有reset pair合并outer fold。

biased20×32银行的native valid在T500、source_valid_1上，R从261.67变为439.96ps；任何共同预测的最小max相对误差为25.41%。input_valid在T1500为96.70→134.09ps，下界16.20%。因此仅调当前Query上的系数不能同时把这两份RTL的相应测点压到15%。uniform16×64对照的valid最差路径／银行下界7.12%／4.42%，差异较小的结果也保留。

下界为`(b−a)/(b+a)`，只适用于同Query两标签的点上max误差；不能称全局源聚合median门槛已被证明不可能。允许每T独立预测的pair平均APE松弛下界另报，biased valid银行为10.01%。reset位置与一致invert同时改变，不能称位置单因素因果或某条OpenROAD命令的单独因果。寄存器及端口R／H合同保持，逐条保存delay／H／R及新旧差值，不把它们变成线上查价。

新增6 synth／6 grt／24 support与旧只读机制包分别结算；156条真实路径／744弧／156删Liberty弧负例和原始身份可便携回放，v6的312条严格路径及匹配OpenROAD源码审计按原身份继承。下一后继先补语义投影对reset分布／相容极性的表达，再设计共用数值描述及成对训练；继续保留当前回归失败、跨银行支持33/57与宽深／shared／W6联合待验。完整记录见[§7.107](lxy-W1-W8-stage-20261115.md#W345-semantic-fanout-successor)及[便携证据](../../experiments/arithmetic/evidence/common_semantic_fanout_v8/README.md)。

## W4显式reset语义与对照预测不足（2026-11-14，§7.108）

v9补充`retained-affine-state-semantics-v1`：输入／保留word的逐bit reset、相容invert及生命周期，逐bit检查输入根XOR／invert与保留reset一致，并与旧计数／尺寸投影严格核对。缺语义、未知版本或损坏数据直接拒绝，不按popcount猜掩码。它是显式仿射保留银行适配器，尚未证明任意实际算术状态的reset语义，也不授予shared或完整阶段物理资格。标签、发射器及寄存器R=T−slack／端口R=0.8T−slack保持。

数值描述加入负载加权reset、逐word reset／invert转换、相反极性输入对及source／capture转换，原始掩码与源ID不用于取价。v8六机制点现在作为train，与父源及其原reset pair整组三成员共同留出；19银行／63实现／378路径，13 fold及14份固定enable上下文，756条训练／LOSO特征和行摘要核对通过。69项有限选择中S占48项，上游只用排除整组后的enable标签，最终上下文与enable价格函数相同。

valid银行LOSO18.23%／28.43%、raw126路径P9538.36%仍失败；服务8.41%／29.37%、native16.06%／24.21%，全零15.02%／25.99%、混合12.79%／15.23%单列。enable银行8.57%／13.90%，input银行11.66%／31.76%但raw P9535.34%仍超标，external银行4.92%／9.30%。四类LOSO保护漏点0，但enable／valid excess仍229.17／388.34ps、282.49／390.40ps，没有手工抬reserve。训练支持63/63，留出完整实现仅33/63，不能授予未知几何资格。

冻结后因素valid31.43%→24.63%仍失败，input10.38%→9.38%改善，enable6.86%→7.22%、external7.99%→10.28%退化；因素逐类银行／路径保护漏点均0。旧支持从12/15降至9/15，新拒`repair/S-412d31fc43b165cb`三个T的reset_capture_transition_fraction，未按回归拓域。共同9点valid11.33%→13.32%、input10.98%→14.88%均退化，不能用不同覆盖集合声称改善；旧external银行max仍1保护漏点，旧聚合逐路径保持null。

接口已能区分旧完整Query碰撞，但biased valid在T500的实测银行差178.29ps只预测1.52ps；input_valid在T1500实测+37.39ps，预测−0.94ps。uniform valid在T1500实测−37.27ps，预测−6.63ps。结论是表达缺失已补，当前比例／转换描述仍未解释物理变化；不按源补差，不把旧局部下界推广为全局不可能。后继应结合保存的逻辑和匹配OpenROAD共享／重缓冲及预算源码，形成能区分各分支共享和负载的prospective假设，再有限登记；宽深实际算术S／shared、W6联合与正式D继续待验。

本轮0新EDA，v8费用不重复计收；20独立算子源未读、公共D不变。477次特征／价格请求跨语言一致，471有诊断价格、6支持拒绝；32项合同拒绝、35测试及Python／native重放通过，继承156真实路径／156删Liberty弧负例按原身份重验。详细结果、共同覆盖与19银行逐源表见[§7.108](lxy-W1-W8-stage-20261115.md#W345-semantic-reset-successor)及[便携证据](../../experiments/arithmetic/evidence/common_semantic_reset_v9/README.md)。

## W4 reset／极性联合关联与hold修复线索（2026-11-14，§7.109）

v10计算输入根reset、保留结果reset及相容invert的联合关联，加入根内两逻辑相位集中／分裂、reset交叉、degree平方加权偏斜等发射前描述；去掉原始根身份／掩码，根重命名及操作数交换不变。逻辑相位不等于物理rise／fall电容。v9的19银行／63实现／378路径、13个完整parent／reset／contrast fold、14份enable上下文和S支持域完全继承，0上游重拟合，756条特征／lineage重新核对。

S有限24项（valid12、input／external各6）与W3／W5合计45项，link固定继承v9。valid选signed_incidence／positive_log_linear／path／alpha1，银行LOSO18.50%／26.09%、raw P9538.71%仍失败；服务8.94%／26.99%、native17.77%／24.28%。input同形式／link／path、alpha0.1，银行median11.66%→12.77%退化，P9531.76%→23.74%、raw P9535.34%→31.13%改善；enable／external不变。四类LOSO保护漏点0，valid excess288.88／392.75ps、enable229.17／388.34ps依然保守，没有手工抬reserve。

train支持63/63、outer-fold完整33/63、因素6/6及旧9/15不变。冻结后共同覆盖的因素valid24.63%→26.10%、旧valid13.32%→16.48%退化；input因素9.38%→8.60%、旧9点14.88%→7.93%改善。因素逐类银行／路径漏点0，旧external银行max仍1漏点、旧逐路径仍null。biased valid T500实际差178.29ps，本版预测−0.16ps；input T1500实际+37.39ps，本版+11.28ps。不能以input改善覆盖valid失败，也未按回归重选。

匹配OpenROAD revision `84e3ff1eb2c36302cef42e4f70a69efe4cfbb126`，保存Rebuffer／Resizer源码、12条train路径及负载分布。biased valid T500旧cell／wire122.78／17.07ps，新235.56／78.64ps，负载序列2／2／64／1→2／2／65／128／1，当前联合比例仍不足。更关键的新线索来自**冻结后只作解释的hold审计**：匹配RepairHold源码中的buffer延迟／面积选择、违例循环、min／max slack检查和`insertBufferBeforeLoads(...,"hold")`，biased input T1500两见证在synth没有hold命名单元，grt分别5／7个，累计cell增量94.027284／134.417388ps，总组合单元9／11。所有逐段wire只有一个load，仍有不同hold延迟链。flow日志旧171违例端点／646 hold buffers及后续9／9，新187／657及后续6／6保留。

这是继续研究hold／clock／setup预算竞争的依据，不证明全部S残差来自hold，也不将每个实例唯一归到某次命令。此审计没有参与v10特征、拟合或选择；实际hold数量、树、slack和延迟不得作为线上输入。后继先检查train最短逻辑路径、capture共享／hold负担等可计算描述，再有限登记；保持R／H、发射和唯一归属，不手工抬保护或向G转嫁。实际算术S／shared及W6完整联合仍待。

0新EDA／标签／验证源，20独立源未读、公共D不变。43项分组测试、477特征／价格、32项拒绝和Python／native回放通过；156继承路径／156删弧负例重验，12条机制路径另有53弧／12删弧负例及cell＋wire／负载证明，未新增物理点。完整结果见[§7.109](lxy-W1-W8-stage-20261115.md#W345-transition-incidence-successor)及[便携证据](../../experiments/arithmetic/evidence/common_transition_incidence_v10/README.md)。

## W4全train路径、hold适用范围与嵌套隔离（2026-11-14，§7.110）

本轮把上节局部hold观察扩展为19银行／63实现的全部保存train审计：378 grt控制路径完整，270 synth逐源路径可恢复，旧108条synth缺失单列，不用聚合银行max替代。648条路径的原始points／report、实际nets／Liberty弧及cell＋wire、H／R均可便携复核。grt native_valid和native_enable各126条、external_valid63条均无hold命名单元，input_valid63条全部包含；input中hold命名单元占组合delay的median／P95为63.45%／76.53%。命名规则只用于描述保存路径，不推断所有buffer的来源，也不能外推为native_valid失败原因。不能将实测hold数量／延迟从R中扣除或作为线上特征。

native_valid的wire median／P95为7.15／70.10ps，H median109.42ps；native_enable wire91.33／151.03ps、H107.85ps。train中126对实际valid／enable R比值均≤1，仍只是观察，不增加硬性valid≤enable约束。下一步native_valid优先研究共享缓冲、不同分支负载与setup预算，input_valid另研究hold／clock竞争；不能仅凭同在S中就共用一个原因。

另补正多层模型训练方法：原v7—v10外层enable函数排除了完整外层组／全部T，没有外层标签泄漏；但下游训练行的上游预测仍为对其自身组的样本内预测。新增公共嵌套模块，外层o、训练行r的enable函数同时排除o和r，最终训练排除r，部署继承原all-train函数。13个完整parent／reset／contrast组复用14份固定上下文，新增78个无序双组排除函数，共92份；训练lineage与1764路由核对通过。

一次预登记12项train对照后，选中nested direct R／positive_log_linear／path／alpha1。银行median18.4680%、P9526.2183%、最大源30.3728%；raw126路径median9.8852%、P9539.2594%、max81.4581%。预登记银行median15%和raw P9535%两闸失败，最大银行源≤v10的30.73945%闸通过。嵌套相对v10的18.4954%／raw38.7097%几乎未改善且尾部稍差；方法隔离补正不能称物理修复。按规则拒绝候选，无新C++价格、不消费旧回归，也不转选次优形式。

7项新增隔离测试通过；648路径／648删Liberty弧负例、63语义银行、3528下游上下文、12项1512路径统计及126次推理重算通过。v10的43项测试和native回放仅继承未变源码身份，不称本轮重跑。数值freeze及旧参数／支持／reserve／R／H／发射不变，0新EDA／标签／验证源，20独立源未读，公共D不变。下一轮先登记train机制假设及停止条件，实际宽深算术S／shared和W6完整阶段仍待；完整证据见[§7.110](lxy-W1-W8-stage-20261115.md#W345-repair-burden-nested-audit)与[便携包](../../experiments/arithmetic/evidence/common_repair_burden_v11/README.md)。

## W4局部capture共享的有限对照（2026-11-14，§7.111）

新增发射前的capture-bank局部出生表达式／极性／共享统计，保持显式仿射语义校验，原始根身份和掩码不进入价格，kept FF不合并。匹配OpenROAD逐负载slack和per-driver面积回收只作机制依据，不作线上输入或单独因果结论。19银行／63实现和v11的92份嵌套上下文继承，0上游重拟合；本轮S两个形式×三个alpha共6项，与Add／G面积合计18项，在登记协议后一次运行并冻结。

选中local_compact／positive_log_linear／path／alpha1，银行16.9584%／30.1663%、最大源38.8918%；raw126路径10.0232%／36.7364%、max82.4524%。v11银行18.4680%、raw P9539.2594%，median与raw尾部改善，但最大银行30.3728%→38.8918%退化，预登记三闸均失败。biased valid T500实测差178.288639ps仅预测0.496400ps，uniform T1500实测−37.271485ps仅预测−0.009797ps。这些局部矩仍未解释已有对照；按规则拒绝，不转选第二候选或消费旧回归，无新C++价格。

6项新增跨W3／W4测试通过；回放核134面积Query、63语义银行、1764下游上下文、18项1560条统计及134面积／126最终训练上下文／126部署上下文推理。冻结输出S.runtime_train实际为最终训练的out-of-group上下文，另补真正all-train enable部署见证，两者不混称。旧648路径证明与测试／native收据仅按未变源身份继承。旧参数、支持、reserve、R／H及发射不变，0新EDA／标签／验证源、20独立源未读、公共D不变。下一步查映射共享／缓冲分支的不连续和可预测范围，必要时登记少量train对照；实际算术S／shared及W6仍待。见[§7.111](lxy-W1-W8-stage-20261115.md#W345-local-sharing-factorized-area)及[证据](../../experiments/arithmetic/evidence/common_local_sharing_v12/README.md)。

## W4原样复测与等价表达的缓冲分支对照（2026-11-14，§7.112）

本轮登记4个已有train父源的8点实现对照，含两S在T500各一次原样repeat、一次独立nonblocking语句重排；另外Add／G交换用于区分共同映射敏感性。4源原样repeat的synth／grt面积／记录时序／归一化网表全部相同，两S所有13类／逐源路径R逐项相同。旧178.288639ps reset差在本次固定发射／流程下可复现，不应先当随机波动丢弃。

S重排后，d0fb525b银行valid R从261.670334变335.516235ps（+73.845901ps），aac8767d从439.958973变314.848190ps（−125.110783ps），原对照差反转为−20.668045ps；variant synth R均185.645233ps。grt总面积却分别只增0.10345%、0.00103%。对应native_valid端点完全相同、无hold命名单元，Δcell／wire／H分别+66.644989／+10.629409／−3.428497ps和−57.377349／−58.704362／−9.029072ps，保存实际负载、Liberty弧、net连接和placement repair日志。第一源缓冲链从单BUFx4f变BUFx3＋BUFx6f，第二源BUFx3＋BUFx6f变两个BUFx3；主要变化在后续缓冲／单元和wire，不是大幅H变化。

native_enable两源R只变化−1.139533／+1.407041ps，仍接近500ps；input_valid分别−1.015900／+21.116700ps。valid差不直接转述为完整阶段频率。52项class／逐源比较包含aggregate重叠项，variant绝对相对变化median0.3596%、P9528.2210%、max28.4369%，不算独立函数。固定发射的确定性与表达变体的敏感性分开报告，不能推出物理标签不可学习；变体不授予生产支持或作为线上源专属补差，生产发射器未变。

首版RTL等价脚本因keep_hierarchy未展开子模块，故意破坏valid的负例通过，软件门禁挡住全部物理。保留错误证明及2 support收费；另登记完整展开的preflight-v2，断言无剩余子模块，4正证明／4负拒绝后才启动8点物理，0物理失败／重跑。不能仅以工具报告equivalent就省去破坏真实状态／输出的负例。另有一次准备文件名错误在准入前保留，0工具重做。

所有对照为train机制证据，不进入本轮拟合。两个S及所有parent／reset／contrast成员沿既有同一fold联合留出，协议parent_group是源身份，实际fold在fold-bindings单列。6项新增测试、156保存路径／156删真实Liberty弧负例和portable回放通过；8 synth／8 grt／66 support结清，20独立源未读、0新模型／价格、公共D不变。后继先审计发射前lowering／共享连接与匹配fullyRebuffer逐load预算的可预测关系，不能继续只扩reset比例／alpha或手工抬reserve。实际算术S／shared、W6仍待。详见[§7.112](lxy-W1-W8-stage-20261115.md#W345-implementation-sensitivity-controls)及[便携证据](../../experiments/arithmetic/evidence/common_implementation_sensitivity_v13/README.md)。


## W4缓冲无关的逐sink连接核查（2026-11-14，§7.113）

v14复用v13两S父源各repeat／variant在synth和grt的8份保存连接，0新后端／S拟合。从native.valid_1实际Q沿net／Liberty弧追踪到641个寄存器D，比较逐sink的缓冲无关表达式：四组比较的sink集合及全部表达式相同，差异数为0。每个前向cone均1604个非buffer／inverter逻辑单元；synth均142个buffer／inverter，而grt的d0fb525b为21→15，aac8767d为15→19。统计含observer分支，只作同范围连接比较，不是线上特征或S面积归属。

结合v13的valid R变化+73.845901／−125.110783ps，可以排除仅由缺失sink数量或该归一化D表达式变化解释此重排对照的假设。归一化只消wire buffer、双反相及基本交换；结果不声称一般Boolean等价／图同构，也不证明固定发射不可学习。后继需要检验发射前分支预算和布局描述及其代理误差，不能继续只扩reset比例、局部共享矩或alpha网格。实际电容、buffer树、slack、坐标和本审计哈希不得成为线上输入。

8份连接重新回放，并检测8个破坏valid传播的负例；跨W3／W4／W5的9项新增测试通过，0新独立源、20独立源未读、S支持／reserve／R／H／发射及公共D不变。实际算术S／shared和W6仍待。详见[§7.113](lxy-W1-W8-stage-20261115.md#W345-shared-cut-control-connectivity)及[便携证据](../../experiments/arithmetic/evidence/common_cut_cover_v14/README.md)。

## W4逐分支条件预算与实际负载核查（2026-11-15，§7.114）

按新计划W4复用v13两父源的repeat／variant，另登记四份只读grt查询；每份从native valid到640数据D和1个valid D的最差setup路径完整保留。逐段核实际net／Liberty弧，并复现旧valid和最差数据R。首分支是缓冲／反相器后第一个非缓冲输入，预算由选中端点required扣掉尾部时延与root arrival得到；限定root且基于最终检查点，不声称Rebuffer优化时或不限定root的内部预算。实例原点距离也不等于pin位置或线长。

d0fb525b最差数据R499.28→498.14ps，valid261.67→335.52ps；aac8767d最差数据497.18→498.59ps，valid439.96→314.85ps。总首分支引脚电容分别475.96→428.40fF、482.53→463.76fF，两组都降而valid变化方向相反；valid本支电容四份均0.483326fF、端点预算只增3.43／9.03ps。总负载及valid单负载不足以解释这两组对照，应研究逐分支预算／共享的发射前代理，另验其误差。这里没有物理修复因果或新S拟合声明，两父源及所有实现继续同一完整fold，不作为四个独立源。

第一次pilot因report_units输出语法失败，恢复pilot因ODB保留转义括号的名称关联失败，各自停止并保留；最终v3导出完整实例几何后关联，四份全完成。新增6 support（4成功、2失败）、0 synth／grt／final，不混为旧只读包0新调用；按Ledger结算wall11.108697s／CPU12.14s。实际预算／坐标／电容仅作离线审计，S参数／支持／reserve／R／H、生产发射器和公共D不变。旧验证／20独立源未读，宽深实际算术S／shared及W6联合仍待。完整证据和回放见[§7.114](lxy-W1-W8-stage-20261115.md#W345-polarity-control-budget)及[便携包](../../experiments/arithmetic/evidence/common_polarity_budget_v15/README.md)。
