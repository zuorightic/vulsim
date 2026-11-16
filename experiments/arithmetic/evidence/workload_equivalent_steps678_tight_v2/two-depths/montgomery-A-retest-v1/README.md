# Montgomery256：按中间物理数据重测原始A

状态：`failed`，更新时间：2026-11-16T16:18:19.612102+00:00。实际运行目录：`/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/reference-successors/matrix-montgomery-A-retest-v1`。

新SDC／ABC请求均为27000ps，原A保持L1、原RTL及功能收据。请求取已保留synth／placement／CTS的最大中间周期×1.10，向上取整至1000ps。
中间时序只用于选择请求；正式A周期必须由完整grt、实际CTS证明、setup±0.1ps夹逼和账本结算后的读数给出。

| 中间阶段 | 时钟周期 ps |
| --- | ---: |
| vulsim_synth_period.rpt | 20496.48 |
| 3_global_place.rpt | 24030.65 |
| 3_resizer.rpt | 24030.65 |
| 3_detailed_place.rpt | 23703.61 |
| 4_cts_final.rpt | 23796.44 |

每工具2线程、16GiB；共享最多9个任务槽位。等待槽位时不暂停BCD，领取槽位时短暂停父调度器以避免抢槽竞争；EDA子进程不收信号。
新综合上限3600秒、grt总上限21600秒（6小时），只运行一次，失败不自动重试。前次7200秒grt超时停在pin_access，延长的是完整物理流程时限。
旧36000ps参考及其三次失败、费用完整保留。当前主表仍保留旧A的失败；新成功读数单独发布，后续可据此登记A参考替换及L16／L32目标，不改已冻结的其他BCD。

[机器结果](result.json)；[冻结准入与时钟依据](admission.json)。

失败：grt-snapshot: timeout。
