# 步骤三关闭证据

本目录对应 `backend_freeze_v4.json`。步骤三验收范围为后端接通、原始乘法核试跑、关键路径核查、预声明 SDC 两点物理对照、统一 TT 口径、累计资源管理及可复核证据。实际 D 库、D2/F1 硬件接入、四组主矩阵尚未完成；完整采集清单和预算必须在步骤五批量物理工作前闭合。步骤三关闭不以目标必须产生差异、内部拆分已有收益或整个实验立即得到资助为条件。

- `critical_path/` 仅来自已有报告，无新增 PPA 调用。保留 synth/grt/final 主路径、完整生成 RTL、压缩映射网表和寄存器/操作数/乘积连接证据。综合 `47.352940 + 947.107448 + 9.885993 + 20 = 1024.346381 ps`；组合数据段占主要部分，支持后续评估内部拆分，实际收益待后续实验。ABC 333.21 ps 单列，未证明同路径/口径，不计算误差倍率。
- `study.json`、`admission.json` 是执行前声明及共享账本准入检查；原剩余 99 synth / 89 grt / 23 detailed，声明新增 2 synth / 2 grt，无重试或追加点。固定 ABC1500ps、L2/II1、TT/RVT/NLDM、种子42、利用率40%、密度0.65及全部优化选项；SDC时钟500/2000ps，I/O绝对max300ps、min0。
- `physical_comparison.json` 是汇总；`sdc-500/` 与 `sdc-2000/` 保留原始指标、逐master计数/尺寸、压缩修复日志和物理网表、放置与关键路径，以及共同1500ps SDC的STA报告。两次真实重新综合计费，规范化综合网表一致，实际综合文件也已压缩归档。
- 500/2000ps下 grt 面积分别694.751580/603.101700 µm²、BUF master数1139/461（包含时钟缓冲），共同SDC最小时钟周期1097.06/1291.90ps。结构、面积和共同SDC路径均有差异，证明当前实现/流程在这两套约束下有响应；500ps自身setup为−597.059021ps，仍未达标。共同STA未改变物理网表和放置。两点hold均低于5ps复核带；不宣称多角签核。
- `usage_checkpoint.json` 保留全部历史条目并累计到31 synth / 9 grt / 5 detailed / 97 support。142个叶命令墙钟1619.803582s、CPU2566.69s，无未结算预约；新实验新增2/2/0及8条support，无失败/超时/重试。`CPU_report_index.json`、`CPU_reports/`、`command_records/` 保存新增12条命令的计费证据；旧130条证据由v3冻结链校验。
- `ledger_migration.json` 记录策略/checkpoint迁移，资源上限与v3完全相同。`physical_control_at_execution.py` 是执行时驱动；当前驱动进一步使用既有 `run_command` 包装外层取消清理，包装仍不重复记费。
- `characterization_v3.json`（配置目录）把六点改为候选点集；必需数据是1500ps参考及D实际查询的精确目标/特征/阶段。D2/F1实现可用后做少量代表性预声明探测，再定额外点集，可在步骤四/六推进，不作为步骤三关闭前提。未测目标仍uncovered，ABC和SDC分别参与身份和缓存。
- `budget_check.json` 按修订方案保守预测369 synth / 329 grt / 45 detailed，仍blocked且实际采集清单未冻结。代表性探测计入原型预留，不再额外强制19×6；未知精确目标暂预留19×9，之后按真实清单去重。该数不是实际消耗或最低需要；v3的462/422/45保留为旧方案规划记录，没有自动提高128/96/28上限。
- `backend-regression.log` 为29项通过；`contracts-ordinary.json` 为20202项通过，B/C12文件原哈希保持。`review_summary.json` 是本轮验收结论；`source_v4/`、`index.json`、冻结文件校验实现和证据，历史v1/v2/v3与旧证据不改写。

无需build/EDA安装可运行 `python3 -m experiments.arithmetic_dse.evidence`。实际重跑对照需要原工具安装和生成RTL，使用 `python3 -m experiments.arithmetic_dse.physical_control --out build/new-study`，会再次消耗真实调用；这不是证据校验命令。预算检查 `python3 -m experiments.arithmetic_dse.budget --check-plan` 当前应blocked/非零；关闭步骤三不授权开始步骤五的批量物理工作。
