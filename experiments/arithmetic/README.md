# 算术实验：现行契约、验证和实施边界

**当前模型的 Git 与复现入口：** 小算子、S／shared、G 参数、D bundle 和相应 RTLzz 子模块实现均已提交；从新检出构建并生成 D RTL 请按[复现说明](REPRODUCE.md)使用便携入口。它保留原冻结二进制入口，另以实际数值复算与 RTL 功能验收绑定本地重编译程序。最新三级受限 D 驱动／完整物理产物在仓库外，公共入口仍保持完整覆盖要求；以下记录按各自版本解释。

**A／B／C／D整设计实测及最小周期已交付：** [§7.79](../../mission/lxy-plan-fix.md#step9-MAC32-ABCD-measurement)和[证据v2](evidence/step9_MAC32_ABCD_v2/README.md)完成五目标21方法、19 synth／19 grt。17个固定物理实现的完整setup最小周期经三类边界和阈值上下0.1ps STA核验；D@1500ps为761.134um²／1360.668ps，3000ps改变寄存器位置后为722.016um²／1735.386ps。前四档D与B同RTL，C静态quarter在本例未优于B／D；同策略静态成本1500ps对照为781.473um²／1501.371ps，临界复测一致。完整setup含reset，3负hold及全部不足5ps保留；C逐节点细查因长报告超时未完成，不阻断整设计PPA／周期交付，完整联合模型资格仍待。85,576成员实际恢复、424成员隔离回放和37项冻结D文件通过，最终PPA未调参／改选。

**D原型已产出：** 按用户决定暂缓reset时序资格，已交付[通用函数D入口与依赖包](models/asap7_function_D_prototype_v1/README.md)、五档T的完整D RTL及[复现证据](evidence/step8_function_D_output_v1/README.md)，见[§7.78](../../mission/lxy-plan-fix.md#step8-function-D-output)。1500／3000ps预测可行，500／1000／1250ps输出最近时序后备；五档均为真实函数选择，功能reset及周期验证通过，无新物理PPA。原节点／S／共享冻结和完整联合未通过身份保留；原型交付不再等待reset，`full_D_ready=false`仍指完整资格。

**最新缺口后继：** [§7.77](../../mission/lxy-plan-fix.md#step67-reset-shared-gap-successor)及[证据v2](evidence/step67_reset_shared_gap_v2/README.md)完成reset的24 train／9 validation旧快照读取与通用函数冻结；validation median21.8180%未过15%，保留失败，未授予正式保护。共享两位置可测性、205→141 FF的纯位别名恢复、CEC及预测侧等价类核对通过；新负载／相关消费者和S去重计价仍待资格。节点／S／共享面积冻结不变，G=0，独立联合test保持锁定，正式D未绑定。

**完整阶段与排序最新结果：** [§7.76](../../mission/lxy-plan-fix.md#step67-multiclock-stage-validation)与[证据](evidence/step67_multiclock_stage_v1/README.md)完成18实现／36阶段的三类／三档／两放置验证，时序median／P95为7.4023%／17.3985%、总面积2.4089%／4.8853%，错误可行0。9组排序7组一致、2组处5%面积并列带；3保守拒绝与4负hold保留。继续零G，冻结参数不变；reset独立保护、shared三capture负载及剩余三类完整物理覆盖／新独立联合仍待，正式D关闭。

**当前共享函数拟合：** [规划§7.75](../../mission/lxy-plan-fix.md#step67-shared-function-fitting)完成24点兼容服务结构的train拟合与冻结，9项新validation全部通过：clock／physical／repair的median／P95为4.6509%／18.8526%、2.3492%／7.8236%、7.0377%／19.7289%，总面积2.4336%／4.6306%。MAC32的44候选在7个数值T下308项完整计价覆盖；Python／C++的76覆盖／1真实拒绝、改名／行序／独立NNLS核对通过。旧失败和费用保留；本包不逐候选采价格，完整阶段时序及新独立S／G／正式D资格仍待。

**最新S／共享后继：** [train审计与复验v3](evidence/step67_state_shared_successor_v3/README.md)改善纯转发S输入和shared physical，六位置／12阶段点误差median／P95为12.7537%／19.6552%，总面积5.8306%／7.7231%。repair median26.1543%／clock P95 42.5219%仍失败，MAC32三档132请求仅81覆盖／51因共享域拒绝；原节点函数不变，正式D未绑定。新参数仅用原train，冻结后没有调参，无新EDA，见[§7.74](../../mission/lxy-plan-fix.md#step67-state-shared-train-audit)。

**最新组合首批结果：** [parallel／bypass验证v2](evidence/step67_combination_batch1_v2/README.md)完成4实现／8阶段，整级点误差median／P95为10.9599%／19.6552%，总面积9.5567%／11.2255%。纯转发S输入边界和repair／clock／physical独占面积保持失败，完整联合及正式D仍待；原参数、50ps预留、失败和联合test锁定不变。下一步先审计原train中的这些责任项，见[§7.73](../../mission/lxy-plan-fix.md#step67-combination-validation-batch1)。

**当前MAC32原型第5步已发布限定支持域的小算子函数：** [ASAP7条件Mul／Add模型v1](models/asap7_conditional_operators_v1/README.md)，证据见[发布验收v2](evidence/step5_conditional_operator_release_v2/README.md)及[规划§7.70](../../mission/lxy-plan-fix.md#step5-bounded-operator-release)。函数以结构、位宽、位连接／负载、capture及数值T为输入，发布目标区间500–3000ps，仍受语义／联合支持规则约束。新独立16项、735项Python／C++核对和2752次真实图生产节点查询通过；44放置仅作需求／搜索回归。S／G完整阶段及正式D资格仍待，原失败与原数据保留。下文较早步骤编号和状态按对应计划／冻结版本解释。

第6—7步已完成[真实serial pilot与隔离证据](evidence/step67_joint_pilot_v2/README.md)：两种原生寄存器放置、1500ps的2 synth／2 grt，567个FF状态函数及3394个端点检查通过。零G完整阶段预测过于保守，联合资格未通过；面积、节点误差、独立最大值相加和S／wire边界误差分别保留。locked联合源保持锁定，完整D仍为false，当前记录见[§7.71](../../mission/lxy-plan-fix.md#step67-joint-pilot)。

其[计费后继](evidence/step67_owned_accounting_v1/README.md)已按训练侧证据分开S完整边界、真实算术owner间wire及单次整级reserve；纯位连接规范化保留位映射、扇出及寄存器截断。同一serial四阶段零G点误差median／P95为14.1624%／14.7381%，36项真实C++／Python组合请求一致（18候选覆盖、18拒绝），见[§7.72](../../mission/lxy-plan-fix.md#step67-accounting-successor)。旧失败与原reserve保持；该结果不授予其他结构／T、新独立联合、shared clock或hold资格，无新EDA，完整D仍关闭。

后续实施以 [修订规划第一章](../../mission/lxy-plan-fix.md) 为准，实际验收见该文件第四章。步骤一的五档宽位宽补验已完成；步骤二新增43例参数化定义、独立参考、固定权重和目标/选择协议。步骤二的组合软件验证不代表固定L流水调度、四平台模型或688条物理记录已经完成。

现行入口如下：

| 入口 | 当前作用 |
| --- | --- |
| [models/asap7_conditional_operators_v1](models/asap7_conditional_operators_v1/README.md) | 第5步发布的独立算子时延／组合面积函数及1000ps查询示例；不含S／G或完整D资格 |
| [cases_v2.json](cases_v2.json) | 32正式＋11保留案例；原始依赖图、端口宽度及训练隔离策略 |
| [contracts.py](../arithmetic_dse/contracts.py) | 核心数值profile、模板参数schema、43例校验、L和目标批次冻结 |
| [reference.py](../arithmetic_dse/reference.py) | 参数化整数及binary32独立参考；原九案例别名不再接受 |
| [case_generator.py](../arithmetic_dse/case_generator.py) | 家族/位宽生成实际VUL组合核和有类型的源码DAG；不是编译器BEIR |
| [fixed_cost.py](../arithmetic_dse/fixed_cost.py) | fixed-op-width-v1的独立d/a、输入位宽取档、最长路径、共享计费和真实Mux网络 |
| [现行配置目录](../arithmetic_dse/configs) | semantics_v2、fixed_op_width_v1、target_rules_v2、arithmetic_interfaces_v1、selection_protocol_v2和cost_sensitivity_v1 |
| [step2_validation.py](../arithmetic_dse/step2_validation.py) | 使用累计账本记录契约、生成、软件和有限原生验证；不启动Yosys/OpenROAD |
| [step2_freeze_v4.json](step2_freeze_v4.json) | 步骤二后继冻结、源码及证据身份、历史依赖与未完成项 |
| [step2_evidence.py](../arithmetic_dse/step2_evidence.py) | 无build、无EDA工具的向量/跟踪/资源核验，显式使用冻结源码 |

从仓库根目录执行参考查询，数值使用按端口位宽检查的无符号整数；binary32以位模式及五位flags表示：

```bash
python3 -m experiments.arithmetic_dse.reference <<'JSON'
{"case":"MAC_32","inputs":{"a":3,"b":7,"c":5}}
{"case":"UDR_16","inputs":{"a":17,"d":0}}
{"case":"F1","inputs":{"a":1065353216,"b":1073741824}}
JSON
```

整数支持8/16/32/64/128位输入，完整乘积和双乘积和分别保留2W及2W+1位；模加减与低位乘积按声明位置截断。商余的独立参考规定d=0时q全1、r=a；源码先令safe_d为1，再选择规定结果。动态移位先把越界移位量替换为0，最终在s≥W时输出0，不能先做宿主越界移位。signed、fixed-point等未登记profile和未知字段明确拒绝。已有binary32 RNE、渐进下溢、tininess-after-rounding、规范NaN及每次独立舍入语义沿用。

完整步骤二验证入口如下，输出目录必须尚不存在：

```bash
python3 -m experiments.arithmetic_dse.step2_validation --output build/step2-recheck
```

该命令验证全部43例的组合软件路径，以及MUL_128、MAC_128、DOT2_128、H_M_128、F2的原生RTL；它本身不承担全部流水验收。步骤六现已贯通S8至BEIR的动态Div/Mod和全43例固定L/valid/reset验收，见下方整图入口。Int无符号`/`、`%`只支持同宽无符号操作数，原始零除抛出诊断，由共同safe_d包装定义实验结果；整图预检拒绝未证明非零的除数。Div/Mod内部仍为原子。

独立SoftFloat核对继续使用原环境变量，源目录无效时验证失败，不伪装为跳过：

```bash
ARITHMETIC_SOFTFLOAT_DIR=/path/to/flat/softfloat python3 -m experiments.arithmetic_dse.step2_validation --output build/step2-softfloat-recheck
```

B/C的新表按输入语义位宽向上取档，可靠ZExt来源可剥离；结果256/257位不自动把128位乘数改成表外输入。d/a是独立字段，组合成本按共享节点求和，时延按依赖最长路径计算。Case保留优先级，Lookup按实际可达索引展开成Mux图；未知操作拒绝或先降低。平方Mul组合成本只属于预声明诊断，完整排序诊断在步骤五执行，不能替换主C。Python实现保留为独立可执行契约；步骤四已将同表固定CostProvider和公共请求接入真实核心调度，half/quarter内部拆分、正式C位置选择和D推理仍按步骤五/七落实。

目标规则先冻结共同公式`ceil(H_ref + (3/2)*D_ref/L)`和平台/阶段/参考身份。D_ref使用原始图最长路径，H_ref单独声明并避免重复计入；实际ps值须等各平台参考微基准就绪后逐批冻结。当前回归中的数值均为公式测试的合成输入，没有生成正式目标或训练模型。

小证据核验无需build目录或EDA安装：

```bash
python3 -m experiments.arithmetic_dse.step2_evidence
python3 -m experiments.arithmetic_dse.wide_evidence
```

历史freeze、旧配置和证据只解释原版本。现行契约/参考/回归入口已替换九案例实现；步骤五已按[实现迁移清单](../arithmetic_dse/configs/implementation_migration_v1.json)移除旧simple_cost及其活动位置分析，历史核验限定从原快照读取。最终交付只保留现行实现和必要基础；被替代的公式、案例入口、命令行开关和脚本须退出活动路径。需要追溯的原字节限定在明确的归档/冻结证据中，不保留永久旧模式或旧案例兼容别名。

[四平台后端](../arithmetic_dse/backend/README.md)及[步骤三物理测量冻结](backend_freeze_v6.json)已按SDC单位修正重验完成32位共同探针接通，包含三个ns平台重跑的小核grt/完整乘法和单独核对后继承的ASAP7。原v5三个ns平台约束错误结果作废，具体更正见规划第四章步骤三§3.9；便携核验为`python3 -m experiments.arithmetic_dse.platform_evidence`。平台进程清理及共享账本沿用必要基础，旧ASAP7专用设置和九案例预算预测函数已退出活动路径；当前v5额度保持不变。预算命令行报告43例/688条新范围及待准入状态，已移除九案例目标列表和一次性旧迁移开关；实际批量清单、平台能力及预算须按规划逐阶段准入。


当前步骤三软件核验冻结已推进到[backend_freeze_v7.json](backend_freeze_v7.json)，收尾记录见[规划第四章§3.10](../../mission/lxy-plan-fix.md#step3-validator-closure)与[step3_platforms_v3说明](evidence/step3_platforms_v3/README.md)。物理结果继承原v6：本次只收紧静态SDC命令边界、补参数来源和交接覆盖，不新增synth/grt/final。v5旧ns结果仍作废；v6原772份证据及全部旧收费保留。GF180 wire RC校准依据尚未闭合，通孔适配验证不扩大成全部wire验证。


[步骤四公共编译接口](../../mission/lxy-plan-fix.md#step4-interface-acceptance)已实际贯通请求、原始Mul/FP原子区域、固定成本及图/物化校验，说明见[RTLzz接口文档](../../rtlzz/src/backend/arithmetic_interfaces.md)。当前后继冻结为[arithmetic_interfaces_freeze_v2.json](arithmetic_interfaces_freeze_v2.json)，[报告类型修订证据](evidence/step4_interfaces_v2/README.md)说明整数计数/历史导航/存储分层；[原v1证据](evidence/step4_interfaces_v1/README.md)保留原字节，便携入口为`python3 -m experiments.arithmetic_dse.interfaces_evidence`。这不是half/quarter内部拆分或D模型完成；旧simple_cost/split16按迁移清单在步骤五退出。步骤三v7物理证据仍按显式旧快照追溯，GF180 wire RC风险未关闭。

证据目录的新旧含义见[总导航](evidence/README.md)。旧`step4/step4_review`已增加历史横幅，原冻结路径不迁移；新包遵循[分层存储规则](../arithmetic_dse/evidence_storage.md)，不重复复制父源码/账本，不仅凭hash宣称完整产物可重算。


[新步骤五](../../mission/lxy-plan-fix.md#step5-mul-template-acceptance)已用参数化`mul-block-tree-v1`替代活动split16/旧成本路径，公共请求`mul-candidates-v1`执行正式C，`mul-template-v1`仅作强制诊断。五档及非整齐尺寸的完整/低位/共享实例、MAC最高进位、真实内部寄存器和位置/敏感性已验证，D仍未实现。说明见[编译器模板接口](../../rtlzz/src/backend/mul_templates.md)，冻结为[mul_templates_freeze_v1.json](mul_templates_freeze_v1.json)，只读核验`python3 -m experiments.arithmetic_dse.step5_evidence`。ASAP7 64位容量grt通过，128位grt在1200秒上限终止，原失败/费用保留，不准入该规模物理批量；没有主矩阵结果或原始/拆分PPA收益声明。大产物目录与默认/完整核验层级见[步骤五小证据](evidence/step5_mul_templates_v1/README.md)。旧冻结继续通过显式快照重算，旧公式只存在于历史namespace，旧公开选项及实验入口已退出。

步骤五当前后继冻结为[mul_templates_freeze_v2.json](mul_templates_freeze_v2.json)，[收尾证据](evidence/step5_mul_closure_v2/README.md)与[指定容量复测](evidence/step5_mul_capacity_v2/README.md)补齐独立位置可行性／生产130位偏好、129报告／219区域历史图回放、部分积坐标移位证书及精确数值v2。旧v1证据及1200秒失败不改；同一128位C电路的唯一新任务在3600秒上限内以1450.19秒完成完整后综合→grt，当前setup/hold满足，未做original对照或final。批次仍按具体容量域、时序及实时预算复审，不统一放行128位。当前核验用`python3 -m experiments.arithmetic_dse.closure_evidence`，`--verify-external`要求实际取得大产物；原v1读取入口继续限定核验原版本。

[步骤五时序口径说明](../arithmetic_dse/timing_metric_scopes.md)与[说明冻结v3](mul_templates_freeze_v3.json)澄清整体setup slack及core_clk同钟period_min的范围，原v1／v2物理数值不改。W128 grt的整体+0.278111ps仍为准入判断的真实窄余量，1264.30ps不能用来宣称完整接口裕量充足；W64的871.71ps来自synth。补充核验为`python3 -m experiments.arithmetic_dse.metric_scope_evidence`，本次只读既有报告，没有新增EDA或STA。

[步骤六整图接口](../arithmetic_dse/whole_graph.md)已验收43正式/保留案例的129个A/B/C实现及47个宽度/商余诊断；包含安全商余、移位、正式binary32串联/旁路与flags、宽复位和公共VUL路径。当前[整图冻结](whole_graph_freeze_v1.json)继承步骤五v3，核验入口`python3 -m experiments.arithmetic_dse.whole_graph_evidence`，小证据见[step6_whole_graph_v1](evidence/step6_whole_graph_v1/README.md)。ASAP7128位UDR（独立Div/Mod）综合触及8GiB；F2综合命令成功但原接口解析器误报，已修软件并静态重核SDC，grt尚未测。四个从属条件控制点暂停；本步未放行相关训练/主矩阵，也未实现除法/FP内部展开或D模型。后续可继续步骤七已满足容量及预算条件的局部域，其余范围保留未完成原因。

步骤六当前修订见[规划§6.6](../../mission/lxy-plan-fix.md#step6-width-proof-review)和[后继冻结v2](whole_graph_freeze_v2.json)：P1证明按实际保留低位传播，合法异宽Ite保留；真实C++与便携入口均回放原176图/186个Div/Mod通过，新生成176份报告/RTL逐字节不变。默认核验入口保持不变，使用最新后继；可编辑规划/导航改动只报告漂移，原快照仍保护。32GiB物理复测及Yosys线程控制缺口分别记账，不将原始失败、CPU_limit纠正尝试或时序不满足隐藏。

步骤六最终后继验收完成，见规划第四章§6.9和whole_graph_freeze_v2。F2实际完成原1500ps grt但setup未满足；UDR128复用原映射、100ns／固定300ps I/O诊断完成完整后综合→grt，1671.49秒，setup+21.883ns、hold+0.671ps、覆盖完整，hold仍待工程复核。v1的未测状态保留为历史，当前结果均可在后继小证据中离线重算，完整大产物按本机catalog核验。Div/Mod与FP内部仍原子，正式目标及D模型留给步骤七；不把容量诊断改作训练或目标标签。
