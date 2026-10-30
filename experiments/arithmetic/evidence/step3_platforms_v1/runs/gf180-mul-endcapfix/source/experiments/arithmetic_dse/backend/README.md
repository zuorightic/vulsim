# 四平台典型角后端

当前实现按 `mission/lxy-plan-fix.md` 第一章§3和§10.3执行，平台选择只有 `asap7`、`nangate45`、`sky130hd`、`gf180`。平台身份、I/O、单位和试跑周期在 `../configs/platforms/`；共同综合/物理设置在 `platform.mk`，真实库、层栈、RC和报告路径从ORFS有效环境取得并校验。旧ASAP7专用Make文件和九案例预算公式已退出活动路径，历史核验显式读取冻结快照。

`backend.py` 的单核接口保留ABC和SDC两个目标轴，对外统一ps、fF和µm²。Liberty头、库名/PVT和OpenSTA `report_units`必须一致；ABC原生使用ps/fF。GF180显式采用TC、9t、5v0、5LM_1TM、K=9，ABC负载为13.43fF。`constraints.sdc`再把ps/fF转成所选Liberty的原生单位，约束时钟、I/O、驱动/负载、reset及valid。重定时和触发器聚类关闭，种子42、2线程、一次一个物理任务。

```bash
python3 -m experiments.arithmetic_dse.backend --help
python3 -m experiments.arithmetic_dse.platform_probe --out build/new-platform-probes --prepare
python3 -m experiments.arithmetic_dse.platform_probe --out build/new-platform-probes --task nangate45-add
```

探针准备会实际生成和运行共同的32位加法及32×32→64乘法核，冻结8个有限任务；新增平台先加法到grt，再乘法到final。连接试跑周期不用于主案例目标或训练标签。失败保留已有阶段，自动重试次数为0。实现缺陷的修正使用有父哈希、原因和新任务ID的显式准入修订，继承整个谱系的调用额度，不覆写原清单、日志或失败目录。`--admission`选择这种修订清单。

每个运行目录保存输入RTL、源快照、有效Make原值、实际生效资产及默认解析来源、库/工具/流程哈希、ABC脚本、映射上下文、逐阶段报告/网表和资源记录。ORFS的`LAYER_PARASITICS_FILE`和`MAKE_TRACKS`缺省规则按其实际脚本解析；不因变量为空便误判平台缺失。面积逐单元核对Liberty和LEF，再按OpenROAD JSON的六位有效数字与汇总值互查。功能、顺序、物理专用和填充面积分列，主面积排除CORE_SPACER，包含tap等物理单元。

synth指标仅为综合STA。grt只按TT/typical setup和完整时序覆盖判断可行，hold始终另报；final读取详细布线提取的SPEF，只有setup/hold≥0、完整覆盖及路由DRC=0才报告可行。所有结果均为`multi_corner_signoff=false`；hold复核带是预声明工程触发值，不能解释成跨工艺噪声底。

预算沿用共享账本、策略v5及进程树清理，发起前预约、结束后按GNU time结算；失败/超时仍收费，未结算预约阻断后续任务。新增叶命令记录平台、准入和任务身份，旧记录保留原字节并在平台分账列为`historical_unattributed`。`budget.stage_plan`核对显式平台/阶段清单的冷链和时间包络，不为未知目标假定缓存或免费覆盖；预算CLI仍明确完整43例/688条主矩阵待分阶段准入。

步骤三本轮证据和离线核验入口见 `../../arithmetic/evidence/step3_platforms_v1/` 与 `python3 -m experiments.arithmetic_dse.platform_evidence`。历史后端v1–v4证据仅证明其原版本；当前四平台接通不代表D已训练、宽算术容量已覆盖或主矩阵已运行。
