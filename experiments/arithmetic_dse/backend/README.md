# 四平台典型角后端

当前实现按 `mission/lxy-plan-fix.md` 第一章§3和§10.3执行，平台选择只有 `asap7`、`nangate45`、`sky130hd`、`gf180`。平台身份、I/O、单位和试跑周期在 `../configs/platforms/`；共同综合/物理设置在 `platform.mk`，真实库、层栈、RC和报告路径从ORFS有效环境取得并校验。旧ASAP7专用Make文件和九案例预算公式已退出活动路径，历史核验显式读取冻结快照。

`backend.py` 的单核接口保留ABC和SDC两个目标轴，对外统一ps、fF和µm²。Liberty头、库名/PVT和OpenSTA `report_units`必须一致；ABC原生使用ps/fF。GF180显式采用TC、9t、5v0、5LM_1TM、K=9，ABC负载为13.43fF。其TC通孔RC适配逐一核对所选技术LEF的Via1–Via4默认单孔4.5Ω及Liberty/STA的1Ω单位，在平台原RC脚本之后补齐缺省映射；电源网格分析保持启用。`constraints.sdc`再把ps/fF转成所选Liberty的原生单位，约束时钟、I/O、驱动/负载、reset及valid。重定时和触发器聚类关闭，种子42、2线程、一次一个物理任务。

```bash
python3 -m experiments.arithmetic_dse.backend --help
python3 -m experiments.arithmetic_dse.platform_probe --out build/new-platform-probes --prepare
python3 -m experiments.arithmetic_dse.platform_probe --out build/new-platform-probes --task nangate45-add
```

探针准备会实际生成和运行共同的32位加法及32×32→64乘法核，冻结8个有限任务；新增平台先加法到grt，再乘法到final。连接试跑周期不用于主案例目标或训练标签。失败保留已有阶段，自动重试次数为0。实现缺陷的修正使用有父哈希、原因和新任务ID的显式准入修订，继承整个谱系的调用额度，不覆写原清单、日志或失败目录。`--admission`选择这种修订清单。

每个运行目录保存输入RTL、源快照、有效Make原值、实际生效资产及默认解析来源、库/工具/流程哈希、ABC脚本、映射上下文、逐阶段报告/网表和资源记录。ORFS的`LAYER_PARASITICS_FILE`和`MAKE_TRACKS`缺省规则按其实际脚本解析；不因变量为空便误判平台缺失。面积逐单元核对Liberty和LEF，再按OpenROAD JSON的六位有效数字与汇总值互查。功能、顺序、物理专用和填充面积分列，主面积排除CORE_SPACER，包含tap等物理单元。

synth指标仅为综合STA。grt只按TT/typical setup和完整时序覆盖判断可行，hold始终另报；final读取详细布线提取的SPEF，只有setup/hold≥0、完整覆盖及路由DRC=0才报告可行。所有结果均为`multi_corner_signoff=false`；hold复核带是预声明工程触发值，不能解释成跨工艺噪声底。

预算沿用共享账本、策略v5及进程树清理，发起前预约、结束后按GNU time结算；失败/超时仍收费，未结算预约阻断后续任务。新增叶命令记录平台、准入和任务身份，旧记录保留原字节并在平台分账列为`historical_unattributed`。`budget.stage_plan`核对显式平台/阶段清单的冷链和时间包络，不为未知目标假定缓存或免费覆盖；预算CLI仍明确完整43例/688条主矩阵待分阶段准入。

步骤三当前软件冻结为backend_freeze_v7.json，收尾证据在`../../arithmetic/evidence/step3_platforms_v3/`，物理测量继承不改字节的v6/step3_platforms_v2。离线入口仍为`python3 -m experiments.arithmetic_dse.platform_evidence`。历史后端证据仅证明其原版本；当前四平台接通不代表D已训练、宽算术容量已覆盖或主矩阵已运行。

2026-10-30的P1复核修订：v5的三个ns平台结果因Tcl整数除法把uncertainty/transition写成0，原四平台验收撤回。SDC所有单位除法改用double，并在阶段继续前检查实际生成文件；三个新增平台的小核/完整乘法以新任务ID重验，ASAP7单独核对并继承。该物理修复冻结为v6，结果见规划第四章步骤三§3.9；23份旧错误SDC及收费永久保留，不用于成功、训练或目标标签。

随后P2收尾将静态SDC规则升级为`serialized-sdc-contract-v2`：一条物理行只允许一个受支持命令，拒绝分号、变量/嵌套命令替换、续行和词拼接；`get_ports/get_clocks`只接受固定形状的单个静态名称，`current_design`恰有一个与原RTL顶层匹配的名称且只声明一次。注释中的续行也拒绝。未实现完整Tcl解释器，归档Tcl从不执行；运行时与便携核验共用同一个`verify_sdc`。时钟、uncertainty/transition、I/O、driver/load及四位小数舍入规则保留。收紧后的规则重新接受18份有效SDC，旧v1运行时检查记录原样保留，另记v2重验结果。此次没有新物理调用。

参数依据与实际交接覆盖分别见[参数来源决策](../configs/platform_parameter_decisions_v1.md)、[44项来源表](../configs/platform_parameter_sources_v1.json)及[产物核验覆盖表](handoff_checks.md)。来源表单独哈希，四个有效profile字节未变。来源一致只证明遵守配置，不能证明物理假设已校准。GF180 wire RC仍保留量级/校准来源未闭合风险；4.5Ω检查只覆盖通孔适配，进入GF180训练/正式评价前需完成独立依据或有限对照准入。

阶段交接统一要求核对下一阶段实际消费的文件、有效配置及可观测状态，分列身份和语义检查；缺失、不支持或不一致时在后续昂贵阶段前停止并保留费用。覆盖表明确标注已有检查、本次新增的P2边界检查，以及ABC实际调用自动比对、映射网表LEC、全部wire RC回读等尚未覆盖的内容，不用哈希替代语义证明。
