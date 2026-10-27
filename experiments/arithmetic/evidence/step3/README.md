# 步骤三随仓库证据

本目录保存可在没有 build/、没有 Yosys/OpenROAD 安装的副本中核对的摘要、指纹和源文件快照。当前后端冻结为 `experiments/arithmetic/backend_freeze_v2.json`。验证命令从仓库根目录运行：

```bash
python3 -m experiments.arithmetic_dse.evidence
```

需要同时核对本机原始库/工具时，加 `--verify-external`。默认只核对仓库中保存的文件；manifest 内的绝对路径和 build 路径是来源信息，默认验证不依赖那些目录。ODB、SPEF、完整日志继续保留在本机 build/，没有将“可核对摘要”写成“已包含完整物理运行产物”。

- `metrics_v1.json`、`repeatability_v1.json`、`resources_v1.json`、`manifest_v1.json` 原样保存首次交付结果，适用 v1 的判定和进程组计数口径。
- `metrics_v2.json`、`manifest_v2.json`、`probe_manifest_v2.json` 为复核后完整入口的结果，范围限定为对应 ABC/SDC 目标和 TT 条件。
- `resources_v2.json` 记录新实现的跨 session 后代进程树采样；不能把 v1 的进程组统计与它直接等同。
- `target_probes.json` 保存 1000/1500/2000 ps 三个综合探针、目标上下文及哈希；这一个核的三点面积/最小时钟周期相同，不等于已经建立 D 的全局代价库。
- `reports_v2/` 保存单位、setup/hold、TNS、覆盖和最小时钟周期的少量原始文本。
- `timeout-before.json` 和 `timeout-after-probe.json` 保存外层超时泄漏的复现及修复后探针；后端回归另覆盖最终继承标记实现、内存、取消和孤儿清理。
- `source_v1/` 和 `source_v2/` 保存两版被冻结的实验代码；v1 原冻结中的源码哈希对应历史快照。
- `review_summary.json`、回归结果及 `index.json` 是本次验收和哈希索引。

grt 的 `measured_feasibility=true` 只表示 TT setup/覆盖通过，hold 独立报告。详细布线仍检查 TT setup 和 hold，低于 5 ps 复核带仍标窄裕量。没有多角签核结论。
