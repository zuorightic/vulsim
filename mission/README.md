# 任务与现行规划导航

**先导恢复与固定拟合诊断已完成，见[§7.93](lxy-plan-fix.md#common-family-recovery-fit-qualification)及[完成审查](../experiments/arithmetic/evidence/common_family_continuation_v1/RESULTS.md)。** 算子147点（108 train／39 validation）、251项跨语言特征／257项同候选价格／支持核对完成，validation误拒绝0；Add／ADC、Sub／SBB、Mul的时延／面积达本轮门槛，比较面积及Mux时延未过，整包不发布。三区覆盖仍不足，不能由三个保护周期代替；未见连接／1373及1700ps的validation另列。G限定组件4独立源／8请求通过，时延源median／P95为4.13%／4.76%、面积11.22%／19.62%；S native_valid仍23.44% median、保护348.64ps，实际控制修复机制继续待解。10个旧独立源与10个宽域独立源保持锁定，公共D绑定／原49项冻结依赖未改。

**Add／S／G后继与八例共同算子工作已推进，见[§7.92](lxy-plan-fix.md#common-wide-family-extension)及[证据](../experiments/arithmetic/evidence/common_family_extension_v1/README.md)。** 宽后继Query／Core支持显式内部精度、位段和carry／borrow，180项跨语言合同、1920次RTL算术及50壳×32周期通过；7个not_training源／14物理阶段及14项删弧负控合格。新增31 train／12 validation／10 locked_test注册，旧14独立源仍锁定；已启动准确54点先导，12个train及6个validation各500／1500／3000ps，分批最多12项、完成即停，不自动拟合／发布。S的27个旧数据库只读STA、351条路径／2050弧／351删弧通过；逐源后继native_valid误差20.74%、保护332.77ps及另外两类控制漏覆盖仍失败。G前缀面积候选validation median／P95为10.51%／22.13%，前轮新增域median8.12%，126项native核对通过，但独立／完整阶段仍待。公共D／价格及49项冻结文件保持，八例整图尚未测量；后台状态以产物根进度为准。

**表示／支持修复与train后端归因已完成，见[§7.91](lxy-plan-fix.md#common-representation-support-attribution)及[证据](../experiments/arithmetic/evidence/common_representation_v1/README.md)。** 邻域重复结构缺陷独立复现并在v2修复，真实原表示的查询结论未变；Add规范化建立Query／显式输入置换／特征／Core发射的同一新策略，599项跨语言合同、1984次算术及4壳×64周期通过，交换输入的特征／支持变化为0，旧模型拒绝新策略。S逐控制源查询与45实际锥、505放置核对；108个train控制路径对及5个G代表的synth／grt守恒分解完成。新物理采集／系数拟合均0，14个独立源仍锁定；新接口未转授物理资格，公共D价格不改。

**修复补采及完成审查已结束，仍未通过发布，见[§7.90](lxy-plan-fix.md#common-functions-repair-completed-review)及[完整结果](../experiments/arithmetic/evidence/common_functions_repair_v1/completed-review/RESULTS.md)。** 本轮100点（operator64／G18／S18）及2084项同候选数值核对通过，6个Add源三区全部合格，14个独立源仍锁定。Mul复用、Add面积、S面积和shared有进展；Add新连接在500—3000ps的延迟误差22.20%／36.39%、G前轮新增域面积19.26% median、S控制／8点保护漏覆盖仍失败。Add交换左右输入后延迟预测最多差92.65ps、支持也可能变化，后继先审计对称表示和控制源语义。24次Add拒绝中16次为T域外、8次为部署域内结构缺口；Mul两次均为T域外。当前0活动任务，完成审查0新EDA／重拟合，原价格／D绑定保持。下方§7.89启动记录按当时检查点解释。

**三线修复后继已登记并启动有限补采，见[§7.89](lxy-plan-fix.md#common-functions-repair-successor)及[修复证据](../experiments/arithmetic/evidence/common_functions_repair_v1/README.md)。** 先做train残差／shared归属审计，保留Mul参数；Add新增有效位／实际进位和相对消费者负载，G补不同进位段以消除面积特征秩亏，S补逐级控制负载、shared按接口／控制责任修正。26源含20个train／validation和6个新locked_test；旧8个独立源也继续锁定。615项新特征跨语言核对、505个实际placement控制投影通过；每批最多12个准确请求，120仅为容量。当前根`/home/zyrv/vulsim-artifacts/common-functions-repair-20261112-v2`自动收尾只做固定拟合／诊断，不解锁测试或发布；首批槽冲突的5个有效点继承，失败与费用保留，0付费物理重试。上一轮204点的发布失败结论不改。

**三线采集、拟合诊断和首轮审查已结束，发布验收未通过，见[§7.88](lxy-plan-fix.md#common-functions-first-review)及[完整审查](../experiments/arithmetic/evidence/common_functions_v1/completed-review/RESULTS.md)。** 去重204点（Mul/Add144、G36、S24）、556次同候选跨语言核对及204点／408阶段兼容性检查通过，8个locked_test保持锁定。计数为37个前驱＋167条v4记录，后者含1个只读恢复点，不重复加38。Mul和S输入面积改善；Add新宽负载／500ps、G面积、S valid保护及shared仍有失败，正式支持／拒绝规则尚未合格。12／14个算子源满足三区间距，另2源达13点上限但过渡区间距不足。旧S没有ABC=SDC匹配行进入本拟合，复用系数不等于合并旧时序数据。原生产参数和门禁保持；本次审查0新EDA、0重拟合。

**三线后继的登记、恢复及采集历程**保留在[§7.87](lxy-plan-fix.md#common-functions-three-lines)和[证据导航](../experiments/arithmetic/evidence/common_functions_v1/README.md)。当前完整根为`/home/zyrv/vulsim-artifacts/common-functions-20261112-v4`；T以log₂(T)、1/T等数值变换进入函数，禁止的是精确T编号、one-hot和逐T专属系数。

**通用分块流水先导已推进，见[§7.86](lxy-plan-fix.md#common-block-pipeline-first-package)、[接口与复现](../experiments/arithmetic/BLOCK_PIPELINE.md)和[证据](../experiments/arithmetic/evidence/block_pipeline_common_v1/README.md)。** MAC32三级新接口完整生成505放置、保留旧324并新增181个4位方案；5种真正两级内部归约RTL及矩形／截断／改名／多Mul软件验收通过。8个not_training物理资格点覆盖窄算子、稀疏G、大银行和补零／直通输出；旧公式复用偏差已量化，新G合并特征通过跨语言准备，尚无新价格发布。下一步冻结后继训练／验证／独立源与有限方案，补拟合、实际算术状态和S/G联合，再重新D选择；不按MAC32候选采专价。下方初始规划和旧交付按各自检查点解释。

**当前模型的Git范围与新检出复现已核查，见[§7.85](lxy-plan-fix.md#git-model-reproduction-audit)、[复现命令](../experiments/arithmetic/REPRODUCE.md)和[验收证据](../experiments/arithmetic/evidence/git_reproduction_v1/README.md)。** 小算子／S／shared／G、D bundle及相应RTLzz提交均已在Git；新增便携入口解决原冻结二进制绑定和仓库外示例源码问题。干净clone重新编译、224候选复算、六RTL功能、移动目录后1125ps调用及四项拒绝检查通过；三级完整D仍保持324中34项拒绝，不把外部受限驱动打包为正式入口。本轮0新EDA，冻结参数／源码不改，新入口与文档尚待用户提交。

**下一轮共同补齐项已合入[MAC32三级与八类案例审计](lxy-eight-workloads-audit.md#MAC32-three-stage-common-work)。** 以MAC32三级先导衔接八例：通用块宽候选及4位叶、必要窄Add负载、S／shared银行规模、G稀疏／零压缩工作量子域，以及S旧边界／时钟修正的逐项审查。文档给出已有证据、共同需求、有限后继／软件交错顺序和冻结／独立／实际D验收条件；保持函数计价、相容发射和原面积／时序规则，不按候选采价格或强制4位。此次只更新规划，未新增EDA或修改模型。

**三级D的拆分阻碍已定位，见[§7.84](lxy-plan-fix.md#MAC32-L3-split-obstacles)及[诊断](../../vulsim-artifacts/MAC32-L3-ABCD-20261112-v1/SPLIT-BOTTLENECK.md)。** 默认32位乘法只枚举32／16／8位叶，无4位候选；底层允许block_width=4，但当前Mul函数输入从8位开始。已生成的6个8位“三算术级”候选全部缺覆盖：5项shared总FF为644／698／940，超643；另1项G稀疏子区域counter_count=0、列高度2、压缩层数0，未取得资格。16位三算术级有价格，但1000ps乘法首级要求1039.128ps，落后于先暂存输入的half方案。诊断未新增EDA、放宽域或改选；后继应补通用块宽、窄Mul、S/shared规模和G稀疏子域。

**MAC32三级A／B／C／受限D后端对比已完成，见[§7.83](lxy-plan-fix.md#MAC32-L3-ABCD-background)及[实测与D分级](../../vulsim-artifacts/MAC32-L3-ABCD-20261112-v1/RESULTS.md)。** D在500／750／1000ps下分别为1190.807／1057.896／941.008um²、Tmin835.408／837.040／999.524ps；只有1000ps本次TT setup满足，余量仅0.476ps。500／750实际为“16个8×8→17加数归约→输出转发”，1000为“输入暂存→4个16×16→5加数归约”，未形成三个有效算术阶段。相对C三档频率＋27.91／25.88／7.52%、面积−6.35／6.56／14.05%；相对二级新D，500ps反而更慢更大，1000ps改选half后面积较小但频率较低。A保持L=1，B/C/D为L=3、II=1；用户确认的290覆盖／34拒绝受限范围不变。12 synth／12 grt均成功、0重试、pending=0，hold及临界setup如实保留；未用实测调参或重选。另[八类新案例能力审计](lxy-eight-workloads-audit.md)已完成，只读、0新EDA；后续统一展开流水、II=1。

**新D的500／1000ps后端评价已完成，见[§7.82](lxy-plan-fix.md#G-fused-D-two-target-PPA)及[实测主表](../../vulsim-artifacts/G-fused-D-PPA-20261112-v1/RESULTS.md)。** 新入选quarter在500ps目标下为1157.652um²／Tmin808.340ps／1237.103MHz，目标未满足；1000ps下974.294um²／943.527ps／1059.854MHz，目标满足。两档固定数据库完整setup阈值上下0.1ps核验、CEC、面积交叉核对通过，hold分别＋1.012／＋4.890ps、保留不足5ps复查标记。共2 synth／2 grt、0重试／失败，pending=0；按用户通知读取结果，没有新增EDA调用。持久根为`/home/zyrv/vulsim-artifacts/G-fused-D-PPA-20261112-v1`；冻结模型／RTL／D排序未改，完整联合资格保持原状态。

**G归约融合修正及新D RTL已交付，见[§7.81](lxy-plan-fix.md#G-reduction-fusion-successor)、[G函数](../experiments/arithmetic/models/asap7_G_reduction_v1/README.md)、[新D入口](../experiments/arithmetic/models/asap7_fused_D_prototype_v1/README.md)和[便携证据](../experiments/arithmetic/evidence/G_reduction_D_v1/README.md)。** 复用小算子和S，G以位几何／数值T函数整体替换内部Add价格，发射匹配的联合综合区域。36 train／12 validation／8新独立请求通过；独立延迟median／P95为4.1913%／11.2578%，面积8.4554%／15.6727%，0误拒绝。五目标220次候选选择已产出RTL：500ps quarter后备、1000ps quarter预测可行、1250ps half/view5（4×16×16先寄存、第二级移位归约）、1500／3000ps original。50份RTL执行各256周期／8100有效比较，1373ps新纯加法图只有4放置，同模型／规则调用与数值复算通过。1000ps同图同位置两边界实测：归约级1020.399→719.138ps，融合预测707.464ps；整设计Tmin1020.399→1001.295ps、面积939.112→871.315um²。60原始标签包隔离回放、NNLS最优性与旧62冻结文件核对通过。reset时序继续暂缓，完整S／G联合及新ABCD统一评价另列，`full_D_ready=false`；本轮软件容量超额与费用在§7.81单列保留。

**用户手写split16的三档原始VUL后端对照和偏差分析已完成，见[§7.80](lxy-plan-fix.md#manual-split16-raw-vul-diagnosis)、[源码](../experiments/arithmetic/manual_split16/README.md)和[分析](../experiments/arithmetic/evidence/manual_split16_vul_v1/BIAS-ANALYSIS.md)。** 500／1000／1500ps下手写频率1072.063／998.718／908.495MHz，面积944.988／846.369／830.156um²，比同目标D更快、面积更大。最大表观差距在第二级：half预测1349–1490ps，raw实测663–787ps；综合日志证实四加法合并为一个$macc，而D原模板按独立算子保层次并累加。优先修正通用归约区域及其可综合／可查询边界，先做同图同放置边界对照，不调源专价或先重训S；模型尚未修改。1500ps下原D可行且面积更小，未选最快版本符合既定目标。29个本轮临时驱动已归档恢复后从仓库移除，第4–8步与已发布模型／公共D入口保留；后继临时Python均在持久目录tools。

**第9步MAC32的A／B／C／D整设计实测及最小周期已交付，见[§7.79](lxy-plan-fix.md#step9-MAC32-ABCD-measurement)、[完整主表](../../vulsim-artifacts/step9-MAC32-ABCD-20261111-v1/results-v2/RESULTS.md)和[便携证据](../experiments/arithmetic/evidence/step9_MAC32_ABCD_v2/README.md)。** 五目标21条方法去重为17个首次实现，再按事前规则做2个临界复测，共19 synth／19 grt。17个固定OpenDB的完整边界最小setup周期均经阈值上下0.1ps STA核验；D@1500ps面积761.134um²、Tmin1360.668ps，3000ps改位置后722.016um²／1735.386ps。前四档D与B同RTL；C的静态quarter在本例未取得更优面积／时序。同策略静态代价对照1500ps为781.473um²／1501.371ps，两临界复测与首次结果一致。完整setup含reset，3条负hold及全部不足5ps保留；C全节点细查因报告超时另列未完成，不阻断本轮整设计实测，也不转授S/G完整联合资格。85,576成员原始恢复、424成员隔离回放和37项冻结D文件通过；最终PPA未调参／改选，`full_D_ready=false`。

**用户已决定暂缓reset时序资格，先交付D；第8步D原型已产出，见[§7.78](lxy-plan-fix.md#step8-function-D-output)、[调用入口与依赖包](../experiments/arithmetic/models/asap7_function_D_prototype_v1/README.md)及[证据](../experiments/arithmetic/evidence/step8_function_D_output_v1/README.md)。** 真实小算子函数＋实际S＋共享函数／零G对MAC32全部44放置、五个数值T计价并选择，已输出完整D RTL。1500／3000ps预测可行，500／1000／1250ps产出标记`target_unmet`的最近时序后备；五档均选择original结构，1500／3000ps寄存器位置不同。3440节点查询／8055位连接独立复算、五份RTL各256周期／810有效数据、5类负控及公共入口复现通过。功能reset保留并验证，reset时序暂不纳入；本轮0物理PPA调用，`prototype_D_selection=true`，完整独立联合及`full_D_ready`仍保留未通过状态，不再阻断该原型范围的RTL交付。

**第6—7步缺口后继已完成本轮诊断与封存，见[§7.77](lxy-plan-fix.md#step67-reset-shared-gap-successor)及[证据v2](../experiments/arithmetic/evidence/step67_reset_shared_gap_v2/README.md)。** 复用24＋9旧快照取得10263个reset端点，通用函数冻结后validation median／P95为21.8180%／28.1140%，因median>15%保持失败，错误可行／拒绝均0；不在同批validation上调参。共享两位置的2 synth／2 grt已完成，原状态读取停点通过纯位别名与逐位Boolean后继恢复，其中一个位置为205逻辑引用／141物理FF；预测侧等价类与实际状态一致，现行节点／S支持尚未放宽。原始归档恢复、328成员隔离回放及46项冻结文件核对通过。G=0，reset正式保护、共享规范化／相关消费者、剩余物理覆盖与新独立联合仍待，`full_D_ready=false`。

**第6—7步已完成冻结函数的三类／三档完整阶段与配对排序验证，见[§7.76](lxy-plan-fix.md#step67-multiclock-stage-validation)和[证据](../experiments/arithmetic/evidence/step67_multiclock_stage_v1/README.md)。** 复用9点并新增另一放置9 synth／9 grt，共18实现／36阶段；时序点误差median／P95为7.4023%／17.3985%，总面积2.4089%／4.8853%，错误可行0、保守拒绝3。9组排序7组一致、另2组在5%面积并列带，非并列排序错误0，4项负hold保留。独立最大值相加贡献约108–190ps保守性，参数／50ps预留／零G均未改。reset缺独立时序保护、shared三capture负载超冻结Mul域，以及剩余三类完整物理覆盖仍是联合资格缺口；1000ps／locked物理test未解锁，`full_D_ready=false`。

**第6—7步共享通用函数已完成拟合、冻结及新validation，见[§7.75](lxy-plan-fix.md#step67-shared-function-fitting)及[便携证据](../experiments/arithmetic/evidence/step67_shared_function_v1/README.md)。** 24个兼容真实服务／native／capture的train点拟合共享clock／physical／root repair，参数不使用源、shape、候选、placement或精确T编号。9个新validation物理点全部通过：clock／physical／repair的median／P95分别为4.6509%／18.8526%、2.3492%／7.8236%、7.0377%／19.7289%，总面积2.4336%／4.6306%。11源77项Python／C++查询为76覆盖／1真实域外拒绝，MAC32的44候选×7数值T全部308项覆盖，包含1000ps软件调用；400成员隔离回放及11555成员原始归档实际恢复通过。旧失败与费用保留；下一步完成整级多结构／多T验证与新独立联合资格。1000ps物理联合test保持锁定，`full_D_ready=false`。

**第6—7步S／共享train审计与冻结后复验已完成，见[§7.74](lxy-plan-fix.md#step67-state-shared-train-audit)和[证据v3](../experiments/arithmetic/evidence/step67_state_shared_successor_v3/README.md)。** 复用原S及节点train，修正clock负载归属，纯转发改用同类native_data边界，简单共享函数及全状态C++／Python消费已完成。六位置／12阶段点误差median／P95为12.7537%／19.6552%，总面积5.8306%／7.7231%；S-only输入P95降至6.0190%、physical面积通过。root repair median26.1543%和clock P95 42.5219%仍失败；新共享支持域使MAC32三档132项仅81覆盖／51拒绝，原节点覆盖不变。参数未在validation后调整，标准库独立NNLS／隔离回放通过。下一步登记共享需求域和有限后继采样／新validation职责，不反复调本六位置；无新物理调用，1000ps／联合test保持锁定，`full_D_ready=false`。

**第6—7步扩展首批已完成，见[§7.73](lxy-plan-fix.md#step67-combination-validation-batch1)和[证据v2](../experiments/arithmetic/evidence/step67_combination_batch1_v2/README.md)。** parallel／bypass各两位置、1500ps的4实现／8物理阶段，点误差median／P95为10.9599%／19.6552%，总面积9.5567%／11.2255%；整级数值门槛通过，联合资格仍失败。纯转发S输入边界P95为59.8657%，repair／clock／physical独占面积误差未通过，bypass两位置排序相反但处5%并列带。5624动态端点、124常量输出、940逻辑状态引用／924唯一FF及33项负控通过，隔离回放完成；两次工具链停点与费用保留。下一步先用原train审计S纯转发边界及共享项，不追加500／3000ps，不解锁1000ps／联合test，`full_D_ready=false`。

**第6—7步已完成边界／连线／预留计费后继及同快照零G复验，见[§7.72](lxy-plan-fix.md#step67-accounting-successor)和[后继证据](../experiments/arithmetic/evidence/step67_owned_accounting_v1/README.md)。** 训练侧推导S边界点估计及真实算术owner间wire，纯位连接规范化后只对实际责任项计费；点预测、原逐节点guard和单次50ps整级预留分开输出。serial四阶段点误差median／P95降至14.1624%／14.7381%，本pilot数值门槛及两位置排序通过；旧零G失败不改写。36项真实组合请求跨语言一致，18覆盖／18保持拒绝；shared clock面积、其他结构／T及新独立联合资格仍待，第二种放置hold失败保留。无新synth／grt，未解锁联合test，`full_D_ready=false`。

**第5步已完成500–3000ps支持域内的节点函数发布验收，见[§7.70](lxy-plan-fix.md#step5-bounded-operator-release)、[发布模型](../experiments/arithmetic/models/asap7_conditional_operators_v1/README.md)及[独立证据](../experiments/arithmetic/evidence/step5_conditional_operator_release_v2/README.md)。** 4个全新独立源×4T共16项请求全部完成，32个物理阶段严格重读；新独立延迟／面积及精确1000ps误差门槛通过。735项真实参数跨语言核对、44种合法放置在500／1000／1500／3000ps下2752次生产节点查询及隔离恢复回放通过。函数系数、分段、语义／负载联合支持和reserve继承冻结候选，仅将周期数值支持与500–3000ps相交；不是按44视图或三个时钟查价。原v2整包失败及原周期域结论保留，经验reserve不是严格上界。第6—7步已完成首个真实serial两placement、1500ps pilot的状态／端点读取，但零G完整阶段预测失败，见[§7.71](lxy-plan-fix.md#step67-joint-pilot)；`full_D_ready=false`。下列“采集中／待发布”均保留对应历史检查点含义。

**第4—5步已补入并完成保存快照的逻辑归属恢复资格，见[§7.69](lxy-plan-fix.md#operator-logical-ownership-recovery)及[后继证据](../experiments/arithmetic/evidence/step7_operator_ownership_recovery_v2/README.md)。** 四个历史失败阶段的4个clone及1个内部缓冲器已通过唯一所有者证书恢复，端点／最大路径／面积同步重读，46项负控及12个原成功阶段对照通过。全部524拟合点／1048阶段的原标签精确一致，因此继承原函数参数、支持域和reserve。原v2已完成692有效点（524拟合＋168独立）、一次性独立评价和证据回放，数值误差／1000ps检查通过，但保留Add采集失败及Mul3389ps超出冻结周期域的拒绝，整包为failed_independent。4个全新独立源×4T共16项请求已登记并通过软件／恢复检查，新控制器已实际完成首个500ps点并继续运行；新旧结论分开留证，`full_D_ready=false`。

**第4—5步已审计独立采集停点并恢复，见[§7.68](lxy-plan-fix.md#operator-v2-independent-continuation)及[续采证据](../experiments/arithmetic/evidence/step7_operator_independent_continuation_v1/README.md)。** 后端在累计571个有效点（524拟合＋47独立）时，因一个500ps Add测试点出现root多输入复制单元、无法按冻结scope归属而停止；原CEC／银行／端口证书通过，但该点没有grt节点标签。该源保持失败停采，其余17源按原冻结候选和剩余最多16个独立批次继续。参数、域、reserve及97项测量／25项拟合推理文件不变；该采集失败仍计最终独立失败门槛，不因续采而免除。实时进度看持久根的三个状态文件，仍未授予新函数合格或完整D资格。

**第7步已推进到真实RTL与物理验证预登记，见[§7.67](lxy-plan-fix.md#step7-real-physical-preparation)及[准备证据](../experiments/arithmetic/evidence/step7_physical_preparation_v1/README.md)。** 六类验证源及两个新参数独立留出源各物化两种位置，共16份RTL，192周期／份和真实cut路径核对通过；实际端点合同、48项有限容量包络、验收表及报告适配器已建立。当前候选节点函数在132次新查询中接受114次、拒绝18次，相关共享物理基线也保留拒绝；没有猜价、修改冻结函数或启动组合EDA。后台第4—5步已完成524个拟合有效点并冻结候选，正在独立采集，独立资格仍待。第7步逻辑端点尚须在有限物理pilot中解析并验证实际mapped引脚／状态／所有权，S／G联合及正式D仍未授予。

**第4—5步v2工作包已经启动，见[§7.66](lxy-plan-fix.md#operator-v2-work-package)。** 已接通v2提取／拟合／导出及冻结入口；459点诊断的误差、关键负载子域和三档时钟支持域检查通过，仍是未完成采集的诊断身份。补采在494个有效点时遇到一项root组合单元归属失败，证据已核对、保存并归档；该源保持停止，其余10源按原协议继续。18个locked_test在本次推进快照时仍未启动，完整采集／validation／真实模型跨语言与拒绝检查通过后才允许冻结并进入独立评价。最新运行状态见持久产物目录的`progress.json`、`v2-work-status.json`及`v2-evidence-status.json`；文档数字只解释本次检查点。第7步六类组合的零G／寄存器截断软件准备已完成，正式S／G联合与完整D资格仍待。

**第1—3步补做验收检查点保留，见[§7.65](lxy-plan-fix.md#steps123-incremental-acceptance)及[增量证据](../experiments/arithmetic/evidence/step7_steps123_incremental_v1/README.md)。** 需求审计、10项消费者特征、4,666次跨语言核对、后继协议及6点12阶段有限可测性验收通过；24项真实单弧删除负控和1,991文件恢复回放通过。当时累计411点，无物理任务运行；后续进度以本导航首段／§7.66和运行状态为准。原93测量依赖、58源身份、旧候选及S参数保持原字节，第6／8步既有前置继续有效。44候选只作需求／搜索回归集，计价主线始终为通用算子函数＋S＋DAG／必要G。

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
| [第四章§7.66](lxy-plan-fix.md#operator-v2-work-package) | v2有限补采、函数执行入口与中期误差／覆盖诊断、归属停点及自动冻结／独立评价门禁 |
| [第四章§7.67](lxy-plan-fix.md#step7-real-physical-preparation) | 六类真实组合／两种物化位置、状态与端点合同、有限物理矩阵／验收表、实际模型覆盖缺口及准备验收 |
| [第四章§7.68](lxy-plan-fix.md#operator-v2-independent-continuation) | v2独立采集归属停点、真实拒绝审计、冻结续采与一次性评价／证据封存门禁 |
| [第四章§7.69](lxy-plan-fix.md#operator-logical-ownership-recovery) | 第4—5步逻辑归属证书／端点重建、4失败恢复、1048原标签不变及后继新独立职责 |
| [第四章§7.70](lxy-plan-fix.md#step5-bounded-operator-release) | 第5步500–3000ps节点函数发布、16项新独立／735跨语言／2752真实调用、隔离证据与S/G剩余资格 |
| [第四章§7.71](lxy-plan-fix.md#step67-joint-pilot) | 第6—7步真实serial pilot：状态／端点／所有权通过，零G失败、setup／hold分开保留及后继G边计费缺口 |
| [第四章§7.72](lxy-plan-fix.md#step67-accounting-successor) | 边界／真实owner间wire／单次预留后继，零G点误差复验通过；旧失败、hold及完整联合资格边界分别保留 |
| [第四章§7.73](lxy-plan-fix.md#step67-combination-validation-batch1) | parallel／bypass首批真实物理验证；整级数值通过，S纯转发／共享独占面积失败与工具链恢复分别保留 |
| [第四章§7.74](lxy-plan-fix.md#step67-state-shared-train-audit) | S纯转发／physical后继通过有限复验；repair／clock及完整MAC32共享域失败，原参数／角色与各次失败保留 |
| [第四章§7.75](lxy-plan-fix.md#step67-shared-function-fitting) | 通用共享函数需求／源角色／有限采集、恢复、24点拟合冻结、跨语言与连续数值T检查及新validation |
| [第四章§7.76](lxy-plan-fix.md#step67-multiclock-stage-validation) | 冻结模型多T完整路径、三类两放置排序验收与剩余reset／共享负载／独立联合缺口 |
| [archive/README.md](archive/README.md) | 旧规划追溯，不能从旧“下一步”续作 |

## 当前已有成果与下一步

当前小算子函数以[ASAP7条件算子发布v1](../experiments/arithmetic/models/asap7_conditional_operators_v1/README.md)为准，输出独立算子时延与组合面积。模型直接接入已有节点CostProvider，1000ps有独立节点物理证据，其他域内数值T按同一函数和联合支持规则查询。§7.74旧共享失败保留；§7.75完成通用共享函数拟合、新validation及308项实际需求覆盖；§7.76完成三类／三档／两位置完整阶段与排序的有限验收，原节点发布资格不变。下一步按已暴露缺口补reset保护与三capture共享负载的通用资格，完成剩余三类完整物理覆盖，再做新独立联合验收和正式D；1000ps联合物理测试保持锁定，hold独立报告。

已有参数化乘法模板、固定C、43例整图／周期基础、四平台后端、局部算子模型及真实数据。较新ASAP7包有12类合格grt组件，含8／16／32位完整／低位乘法和8／16／32／64位加法；其精确目标／形状／capture域不等于任意负载或新周期均覆盖。原始／half／quarter候选、实际阶段和typed状态查询、共享链、验证和Ledger继续复用。

最新S发布见[证据包](../experiments/arithmetic/evidence/step7_general_state_v1/README.md)：新54项独立一次性评价通过，三所有者功能状态／控制面积的grt中位／P95为0.33944%／1.09599%、0.48657%／0.90230%、0.04684%／0.17216%，八类边界72／72。它排除shared clock／physical／root repair，只覆盖登记合成银行及九精确周期，生产绑定仍为false；原失败、参数、50ps reserve及已消费测试封存。不能把不同模型的周期／边界直接拼接，或重复叠加新S与旧native总价。

P0静态部分得到3候选、5248次级分配、44合法视图、19形状／57粗负载描述；§7.52补齐63项精确位映射。软件算术／周期前检及§7.51的10点／20阶段／52路径诊断均保留原身份。正式模型采用节点独立最大时延与同一实现的组合面积，服务／连线／状态／时钟边界分别计费；不能把Q→D中的节点段自动当作节点最大值。

机器配置revision4及第一轮协议保留当时字节；现行[后继协议](../experiments/arithmetic_dse/configs/operator_collection_protocol_v2.json)revision4冻结30 train／14 validation／14 locked_test，源清单与资源方案见[第1—3步证据](../experiments/arithmetic/evidence/step7_steps123_v2/README.md)。用户已确认[统一保层次策略后继](../experiments/arithmetic_dse/configs/operator_boundary_policy_v2.json)，公共body／模块定义桥接及有限mapped银行／常量／直通／独立端点资格已完成。下一步按真实采样器请求准入最多12个train／validation源目标的小批次，再依耗时／容量及缺区调整后续批次；正式放行文件和完整产物持久恢复仍须落实。不无条件执行原87×13或新58×13全表，TEST_ONLY价格不进入正式D，最终PPA及已消费test不调参／重选。

## 历史阅读与文档整理

本目录现行入口只保留本导航、原始任务和修订计划。八份重复交接／草案已经合并并删除活动副本，迁移表见[第一章§0.10](lxy-plan-fix.md#model-reuse-and-evidence-index)。冻结证据及源快照中的旧文件名继续解释当时版本，不修改它们的字节或哈希。

第一章是现行方法和规范；第二章按A／B／C归档旧技术／执行规划、旧推进及原修订审查；第三章说明结论当前有效性，第四章保留实施验收。旧九步及旧“下一步”不作当前命令，第1—3步完成，第5步节点函数限定发布见§7.70，下一步见第一章§0.11及§0.12第6—7步。第四章§7.1–§7.69及原模型协议中的“当前／下一步／采集中”均按对应日期解释，不是本轮执行命令。§7.49–§7.52的速度优先／仅近极限表述也按历史决策解释；当前采样／模型／D策略以§0及§7.54–§7.56为准。新工作引用写全文件、章、节号、版本，优先使用稳定锚点。

原冻结／证据不因文档归并而改写，archive仅追溯；现行代码替换建立明确后继。§7.49只记录文档修订；§7.50–§7.52的物理诊断保持not_training；§7.54–§7.56记录现行决定。§7.57完成本轮软件和协议，不启动新物理优化、正式训练或独立模型标签评价。旧10点扫描及其冻结证据仍只解释旧协议。小算子拟合独立节点operator_delay_ps／组合面积；data slack只用于离线取点及联合验证，旧Q→D标签不能直接改名使用。
