# 四平台典型角后端

当前实现按 `mission/lxy-plan-fix.md` 第一章§3和§10.3执行，平台选择只有 `asap7`、`nangate45`、`sky130hd`、`gf180`。平台身份、I/O、单位和试跑周期在 `../configs/platforms/`；共同综合/物理设置在 `platform.mk`，真实库、层栈、RC和报告路径从ORFS有效环境取得并校验。旧ASAP7专用Make文件和九案例预算公式已退出活动路径，历史核验显式读取冻结快照。

步骤七正在建立四平台离线模型，采样／标签／拟合与发布边界见[模型协议](../model_protocol.md)及[规划第四章步骤七](../../../mission/lxy-plan-fix.md#step7-offline-model-acceptance)。当前四平台孤立Mul／Add／AddCarry模型已完成两轮拟合与独立测试；完整阶段模型仍需质量、图域及原生验收，不能把下面的后端接通成功等同正式D就绪。历史profile和测量按各自冻结快照核验。

`backend.py` 的单核接口保留ABC和SDC两个目标轴，对外统一ps、fF和µm²。Liberty头、库名/PVT和OpenSTA `report_units`必须一致；ABC原生使用ps/fF。GF180显式采用TC、9t、5v0、5LM_1TM、K=9，ABC负载为13.43fF。其TC通孔RC适配逐一核对所选技术LEF的Via1–Via4默认单孔4.5Ω及Liberty/STA的1Ω单位，在平台原RC脚本之后补齐缺省映射；电源网格分析保持启用。`constraints.sdc`再把ps/fF转成所选Liberty的原生单位，约束时钟、I/O、驱动/负载、reset及valid。重定时和触发器聚类关闭，种子42、2线程、一次一个物理任务。

```bash
python3 -m experiments.arithmetic_dse.backend --help
python3 -m experiments.arithmetic_dse.platform_probe --out build/new-platform-probes --prepare
python3 -m experiments.arithmetic_dse.platform_probe --out build/new-platform-probes --task nangate45-add
```

探针准备会实际生成和运行共同的32位加法及32×32→64乘法核，冻结8个有限任务；新增平台先加法到grt，再乘法到final。连接试跑周期不用于主案例目标或训练标签。失败保留已有阶段，自动重试次数为0。实现缺陷的修正使用有父哈希、原因和新任务ID的显式准入修订，继承整个谱系的调用额度，不覆写原清单、日志或失败目录。`--admission`选择这种修订清单。

每个运行目录保存输入RTL、源快照、有效Make原值、实际生效资产及默认解析来源、库/工具/流程哈希、ABC脚本、映射上下文、逐阶段报告/网表和资源记录。ORFS的`LAYER_PARASITICS_FILE`和`MAKE_TRACKS`缺省规则按其实际脚本解析；不因变量为空便误判平台缺失。面积逐单元核对Liberty和LEF，再按OpenROAD JSON的六位有效数字与汇总值互查。功能、顺序、物理专用和填充面积分列，主面积排除CORE_SPACER，包含tap等物理单元。

synth指标仅为综合STA。grt只按TT/typical setup和完整时序覆盖判断可行，hold始终另报；final读取详细布线提取的SPEF，只有setup/hold≥0、完整覆盖及路由DRC=0才报告可行。所有结果均为`multi_corner_signoff=false`；hold复核带是预声明工程触发值，不能解释成跨工艺噪声底。

预算沿用唯一共享账本及进程树清理，以`budget.POLICY`所指版本和清单绑定的哈希为准。步骤七已通过带完整账本前缀的新checkpoint迁移到v6，不重置旧消耗。发起前预约、结束后按GNU time结算；失败/超时仍收费，未结算预约阻断后续任务。新增叶命令记录平台、准入和任务身份，旧记录保留原字节并在平台分账列为`historical_unattributed`。`budget.stage_plan`核对显式平台/阶段清单的冷链和时间包络，不为未知目标假定缓存或免费覆盖；预算CLI仍明确完整43例/688条主矩阵待分阶段准入。

步骤三当前软件冻结为backend_freeze_v7.json，收尾证据在`../../arithmetic/evidence/step3_platforms_v3/`，物理测量继承不改字节的v6/step3_platforms_v2。离线入口仍为`python3 -m experiments.arithmetic_dse.platform_evidence`。历史后端证据仅证明其原版本；当前四平台接通不代表D已训练、宽算术容量已覆盖或主矩阵已运行。

2026-10-30的P1复核修订：v5的三个ns平台结果因Tcl整数除法把uncertainty/transition写成0，原四平台验收撤回。SDC所有单位除法改用double，并在阶段继续前检查实际生成文件；三个新增平台的小核/完整乘法以新任务ID重验，ASAP7单独核对并继承。该物理修复冻结为v6，结果见规划第四章步骤三§3.9；23份旧错误SDC及收费永久保留，不用于成功、训练或目标标签。

随后P2收尾将静态SDC规则升级为`serialized-sdc-contract-v2`：一条物理行只允许一个受支持命令，拒绝分号、变量/嵌套命令替换、续行和词拼接；`get_ports/get_clocks`只接受固定形状的单个静态名称，`current_design`恰有一个与原RTL顶层匹配的名称且只声明一次。注释中的续行也拒绝。未实现完整Tcl解释器，归档Tcl从不执行；运行时与便携核验共用同一个`verify_sdc`。时钟、uncertainty/transition、I/O、driver/load及四位小数舍入规则保留。收紧后的规则重新接受18份有效SDC，旧v1运行时检查记录原样保留，另记v2重验结果。此次没有新物理调用。

参数依据与实际交接覆盖分别见[参数来源决策](../configs/platform_parameter_decisions_v1.md)、[44项来源表](../configs/platform_parameter_sources_v1.json)及[产物核验覆盖表](handoff_checks.md)。来源表单独哈希，四个有效profile字节未变。来源一致只证明遵守配置，不能证明物理假设已校准。GF180 wire RC仍保留量级/校准来源未闭合风险；4.5Ω检查只覆盖通孔适配，进入GF180训练/正式评价前需完成独立依据或有限对照准入。

上段记录步骤三v7的身份和风险状态。步骤七的新GF180 profile另用实际冻结routed ODB／OpenRCX线段，按net分组拟合并独立核对Metal2–Metal5电阻；不推断旧系数必然差1000倍。新R为0.3250285054／0.3250333829／0.3250270822／0.0931998971 Ω/µm；C和4.5Ω通孔不变，Metal5独立测试仅1段的限制保留。四平台新profile显式采用100%的CTS修复缓冲上限，以免小型短路径夹具在20%默认上限提前停止；运行目录中实际helper、有效环境和调用哈希可核对，ORFS安装不变。这两项属于已版本化的物理条件修订，旧结果不混入新域标签。阶段wire RC新增实际STA回读检查；比例往返容差1e-7，不代表所有电容／物理假设均已校准。

阶段交接统一要求核对下一阶段实际消费的文件、有效配置及可观测状态，分列身份和语义检查；缺失、不支持或不一致时在后续昂贵阶段前停止并保留费用。覆盖表明确标注已有检查、本次新增的P2边界检查，以及ABC实际调用自动比对、映射网表LEC、全部wire RC回读等尚未覆盖的内容，不用哈希替代语义证明。

## 步骤六层次RTL接口读取

当前运行时在综合前从输入RTL的显式`--top`读取ANSI接口，逐阶段SDC覆盖复用同一端口集合。子模块端口不混入顶层，逗号连续声明沿用方向和范围；动态/参数化、non-ANSI及其他未支持形状明确拒绝，不执行归档RTL。便携核验以冻结任务top调用同一`rtl_ports`。旧单模块调用保持仅允许一个模块的限定，不能省略top后猜测层次。

步骤六F2探针曾综合成功后被旧读取器误报重复端口；原manifest和费用保留，后继静态核对其实际SDC通过，但未继续grt/STA或增加重试。UDR128另因综合进程树RSS触及8GiB而终止。两项不得混为算术功能错误或已完成物理容量；后续物理运行按有限准入重新登记。

## 步骤六32GiB复测和Yosys线程池

用户2026-11-02要求补跑延期任务并提高内存，采用新有限准入的32GiB任务级例外，原v5累计次数/墙钟/CPU总额不变。旧8GiB结果和每次失败费用保留。Yosys当前线程池读取`YOSYS_MAX_THREADS`，仅设置NUM_CORES或OMP_NUM_THREADS不足以限制它；现行入口向子进程及实际Make命令显式传入该值，回读有效环境并纳入mapping_context身份。原Yosys未受专用限制的容量尝试只能按实际条件解释，不能追认两线程。

v2为原六任务的一次32GiB复测；UDR触发CPU_limit后暂停其控制点，F2实际完成grt与两个控制。v3是已定位线程约束缺口后仅UDR三任务的独立纠正准入，显式限制Yosys池，原RTL/约束不变；没有自动循环重试或追加original/final。完整后综合→grt与单独5_1_grt时间分列，时序读取整体setup/hold/覆盖，period_min仍为同钟诊断。

UDR后继v4完成综合、在1.5ns条件下物理4小时timeout；v5依用户指定将SDC放宽为100ns，ABC目标保留1500ps、I/O max固定300ps。`clock_relaxation.py`仅允许这一命名任务复用身份匹配的映射网表，生成全新SDC/ODB并从floorplan执行；禁止复制旧布局/CTS/grt或改成final。v5完整链1671.486790秒完成，原失败、映射时间和新实耗分别保留。两线程指工具worker请求及专用配置，进程树线程峰值还含其他线程，不能当作OS硬线程上限。旧步骤三/五Yosys未设置专用变量的环境身份继续保留。
