# 步骤三预算及六点目标复核证据

本目录对应 `backend_freeze_v3.json`。原 `step3/` 和 v1/v2 冻结文件逐字节保留；这里新增共享预算实现及六点目标协议的证据。

- `historical_usage.json` 导入此前全部已知物理后端叶命令：13 synth、5 grt、4 detailed，包含失败调用。
- `usage_checkpoint.json` 累计到本次结束为 29 synth、7 grt、5 detailed；130 个非重叠叶命令（含环境/快照/生成/验证，89 条 support）共 1385.926145 s 墙钟、2219.01 s GNU time CPU，无待结算预约。外层生成/验证包装不重复计物理调用。
- `checkpoint_operation.json` 记录从历史基线到本次快照的显式归档，没有退款。默认活账本在 `experiments/arithmetic/backend_usage.json`；克隆缺少活账本时从这里的 checkpoint 开始。
- `historical_manifests/` 及 `CPU_reports/` 保存全部历史命令清单和 130 份小型 GNU time 文本。所有调用数量和 CPU 可在没有 build 的情况下核对。大日志、ODB、SPEF 继续留在 build。
- `bound-*/`、`target_probes.json` 保存显式绑定 ABC 目标后的 500/800/1000/1250/1500/2000 ps 六点综合指标、身份与规范化网表哈希。本核六点的面积 572.469120 µm²、最小时钟周期 1024.35 ps、网表相同，只表示这些已测点一致；500/800/1000 ps 的 setup 为负。
- `bound-entrypoint/` 保存绑定目标后的完整入口：软件/原生各 10000 周期验证及 synth/grt/final/OpenRCX，面积 602.620560 µm²，详细布线 DRC=0。`final-counted-entrypoint/` 验证生成/验证 support 也被共享账本计时间。早期 `entrypoint/`、`target-*/`、`final-source-synth/` 及 `source_before_abc_binding/` 保留为修正前记录。
- `budget_check.json` 为当前冷启动保守规划：六点 114，加潜在案例目标补测 171、主评价、D 搜索、详细复核重跑、原型 36、重复 8、重试 16 及历史，共 462 synth / 422 grt / 45 detailed。相对于 128/96/28 不足 334/326/17。这是保守容量场景，不是已经消耗的资源，也不是把新上限设为这些数。实际所需模型族/案例目标冻结后应去重重算，显式资助后才开始步骤五批量物理工作。
- `backend-regression.log` 为 25 项后端契约通过；`contracts-ordinary.json` 为 20202 项普通契约通过，B/C 12 个冻结文件保持原哈希。
- `source_v3/` 为本版源快照；`index.json` 列出本目录所有其余文件的路径、大小和 SHA-256。

执行 `python3 -m experiments.arithmetic_dse.evidence` 无需 build/EDA 安装即可检查源、历史快照、便携报告、CPU 账本和预算公式。`python3 -m experiments.arithmetic_dse.budget --check-plan` 当前应返回 blocked 和非零码，表示完整实验未被原上限资助；不是回归失败。D2/F1 的六点义务已写入协议，实际核接入后执行，当前没有声称已完成这些核或 D 代价库。

ABC 目标传递核查：ORFS 的具名外部 speed 脚本不会自动接收 Yosys `-D`。当前渲染 `abc_speed_target.script`，对 `&nf/upsize/dnsize` 显式指定数值目标，完整脚本哈希与 ABC 实际 `source` 及 `target delay` 诊断摘录保存在 `bound-*/`。ABC 报告抽取逻辑延迟 333.21 ps，小于全部目标，因此六点仍可映射相同；它不等于整个设计 1024.35 ps 的 STA 周期。旧未绑定目标探针仅为历史证据。
