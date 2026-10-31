# 实际产物核验与阶段交接

每个关键阶段检查下一阶段实际消费的文件、有效配置及工具可观测状态，并与冻结请求核对。**身份哈希与语义核验分列**。缺失、方言不支持或语义不一致时，应在进入后续昂贵阶段前停止，保留失败阶段、原因及已发生费用。以下复用`backend.py`、`platforms.py`、`sdc.py`、`platform_evidence.py`，不另建物理流程或复制完整PDK。

本表描述当前覆盖及缺口。规则是后续扩展必须遵循的交接要求；表中标为缺口的能力没有因写入规则而实现。

| 实际产物 | 生产者 → 消费者 | 身份检查 | 现有语义检查与边界 | 状态/缺口 | 当前失败码 | 证据位置 |
| --- | --- | --- | --- | --- | --- | --- |
| Make有效配置 | ORFS Make → Yosys/OpenROAD | 原始有效环境、config.mk和平台/流程文件哈希 | 平台/corner、覆盖值、ABC driver/load、原生资产缺省解析与白名单路径；库另查PVT | 已有；尚非对每个Make变量逐项建立独立工具侧回读 | `invalid_platform_environment` | manifest的raw_make_environment/effective_environment/asset_resolution，effective-environment.txt、config.mk |
| 选定Liberty/LEF/RC | Make与load脚本 → 综合/STA/物理工具 | 实际环境中的文件及工具哈希；RCX精确别名、GF通孔适配脚本身份 | Liberty PVT/单位、STA report_units、逐master LEF/Liberty面积、GF默认通孔/1ohm单位；加载脚本与日志可追踪 | 已有；RC文件哈希不证明wire系数校准。GF180 wire来源部分闭合；未逐条回读工具内部全部RC值 | preflight为`invalid_platform_environment`；后续为`stage_evidence_rejected` | manifest libraries/files_sha256/tools，reports/*units.rpt、*cells.tsv、原始日志；v3来源摘录与wire风险记录 |
| ABC渲染脚本与调用 | render_abc_script/ORFS Yosys → ABC | 模板、渲染脚本、Make命令/工具身份、ABC target独立保存 | `&nf/upsize/dnsize`绑定-D数值；ABC Liberty归一ps/fF源码及stime日志 | 已有；记录原始综合日志可审查实际调用，但尚无通用机器检查逐项证明日志中的实际脚本与渲染内容同一。不得把声明路径等同执行证明 | preflight为`invalid_platform_environment`；工具退出为`tool_nonzero_exit` | abc_speed.script、mapping_context、synth命令/原始Yosys/ABC日志 |
| 映射网表及接口 | Yosys → floorplan/STA | 1_2_yosys.v的规范化hash、原始RTL hash、顶层请求 | 原输入探针已独立软件/原生功能验证；阶段时序覆盖、SDC全部输入输出端口核对 | 已有；网表hash不是形式等价证明，目前没有逐次映射网表的独立LEC验收 | `stage_evidence_rejected`、`timing_coverage_incomplete` | input.sv、1_2_yosys.v.gz、metrics的mapped_netlist_sha256、probe preparation证据 |
| 实际阶段SDC | write_sdc → 下一物理阶段/快照STA | 阶段SDC文件hash和语义结果绑定；运行/便携均调用verify_sdc | 两时钟、uncertainty/transition、reset/valid/data的I/O、driver/load、覆盖/重复项；v2再约束单命令边界、静态字面量、current_design形状/顶层 | 数值检查已有；**本次新增P2语法边界**。只支持文档化write_sdc方言，不执行归档Tcl | `sdc_contract_mismatch` | 1_synth/5_1_grt/6_final.sdc.gz；manifest sdc_contracts；v7重新核验记录，旧manifest不改 |
| SPEF、阶段报告与指标 | 路由/提取/快照STA → 报告/模型采样 | SPEF/报告/网表身份、阶段和目标轴、源/工具上下文 | final要求提取文件存在并重读、SPEF头/内容hash；时序覆盖、setup/hold分开、DRC=0、逐单元面积与ORFS汇总舍入互查 | 已有；不等于完整SPEF图连通性独立检查、多角签核或模型域已覆盖 | `stage_evidence_rejected`、`timing_coverage_incomplete`；工具失败另记 | 6_final.spef.gz、reports/、route JSON、metrics.json、阶段命令日志 |

命令超时/CPU/内存限制及非零退出仍由现有`BackendCommandError`单列记录。原始异常信息保留在failure_reason；表中通用`stage_evidence_rejected`没有被虚构成更细的已实现错误码。便携核验直接抛出具体的身份/语义拒绝原因，不冒充新的物理运行。

参数来源元数据独立于有效profile：`../configs/platform_parameter_sources_v1.json`逐项绑定原值/单位、来源及适用范围。仅变更来源说明不触发物理重跑。若有效环境改变，必须记录测量/模型域影响并按预算准入；禁止补写旧运行快照来伪造与当前实现一致。
