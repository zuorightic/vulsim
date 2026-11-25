# AutoPipe 模型校准进度

更新于 2026-11-25T14:51:45+08:00。
当前阶段为 **大乘法试测及训练扫描**。

| 工艺 | 算子族 | 正式点位 | 已测 | 已复用 | 试测成功 | 失败 |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| ASAP7 | Add/ADC | 480 | 60 | 0 | 3 | 0 |
| ASAP7 | Sub/SBB | 435 | 60 | 0 | 3 | 0 |
| ASAP7 | Mul | 285 | 72 | 1 | 8 | 1 |
| ASAP7 | Compare | 630 | 88 | 2 | 6 | 0 |
| ASAP7 | Mux | 285 | 30 | 0 | 2 | 0 |
| NANGATE45 | Add/ADC | 480 | 60 | 0 | 3 | 0 |
| NANGATE45 | Sub/SBB | 435 | 59 | 1 | 4 | 0 |
| NANGATE45 | Mul | 285 | 30 | 0 | 7 | 0 |
| NANGATE45 | Compare | 630 | 87 | 3 | 6 | 0 |
| NANGATE45 | Mux | 285 | 30 | 0 | 2 | 0 |

失败列统计尚未恢复的试测和正式点。同一请求的恢复标签通过核验后转入成功计数。
普通任务最多 4 并行，每任务 4 线程、16 GiB。192–384 位乘法最多 2 并行，每任务 8 线程、32 GiB。512 位乘法单任务运行，16 线程、64 GiB。
192–384 位乘法的综合后阶段限时 4 小时，512 位为 8 小时。限时包括布局、CTS、等价性检查和全局布线。

实验记录位于 `/home/zyrv/vulsim-artifacts/autopipe-model-calibration/operators-20261123-v1/progress.json`。

联合拟合候选位于 `/home/zyrv/vulsim-artifacts/autopipe-model-calibration/operators-20261123-v1/fit/`。当前拟合状态为 /home/zyrv/vulsim-artifacts/autopipe-model-calibration/operators-20261123-v1/fit/first-wave。

G、S 和 shared 的扫描计划从算术本体验证结果展开。
