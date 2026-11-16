# 第6～8步：九例等效预算版本 ABCD

当前完成统一 grt 实测的主方法记录为 **0/76**。本轮已被A/L紧凑目标版本替代，不再启动新比较；共享模型仍为诊断身份，完整精度资格没有通过。

本轮响应参数沿用第1～5步冻结版本。Sub／Compare采用既有train源均衡池化的公共采样H代理，功能消费者绑定实际Boolean-cover节点；原四类边界及响应不变。先按候选路径联合分配本体预算，再反解等效训练T并调用原函数，S／shared／控制及实际ABC保留整机T。超过原6000ps反解区间的请求显式扩展至有限100000ps区间，均属未取得精度资格的外推。

新增全局依赖路径均衡位置由原生接口验证并物化。静态C仍按原统一表选择；MAC32保留第5步175个完整候选的原数值，其他案例保留每结构的静态路径／状态代表，再增加有限静态／模型压力位置。共同池静态价格归因与正式C分别列出。

旧测时规则：每个非MAC案例冻结静态C探针，按其完整RR／IR／RO阈值T_ref取1.05／1.45倍并向上取整到100ps。此规则已被用户确认的A/L规则替代，仅保留历史身份和开销。

| 批次 | 数据角色 | 任务数 | 完成 | 失败 | 活动／排队 |
| --- | --- | ---: | ---: | ---: | ---: |
| calibration-add512 | clock_calibration | 1 | 1 | 0 | 0 |
| calibration-first-five | clock_calibration | 5 | 4 | 1 | 0 |

| 案例 | 探针请求 ps | 完整 Tmin ps | 面积 µm² | hold WNS ps |
| --- | ---: | ---: | ---: | ---: |
| add512 | 1100 | 1093.51 | 3072.56 | 0.075 |
| mul128 | 1900 | 1897.39 | 16123.96 | 1.186 |
| dot16 | 2000 | 2109.40 | 46167.16 | -0.442 |
| horner64 | 1100 | 1098.18 | 6499.82 | 1.990 |
| barrett64 | 2300 | 2299.90 | 11347.07 | 15.672 |

物理口径为 ASAP7 RVT TT / TC25C0.7V、NLDM、post-CTS grt估计RC；标准单元面积排除filler并包含taps，I/O max=0.2T。完整setup阈值有±0.1ps括号检查；hold与约束覆盖另报，不把grt写成final或多角签核。

同RTL／T／工艺／约束身份共享物理任务。每批全新冻结、自动重试0，共享账本保留所有历史开销。每工具4线程、8GiB、并发3；大型任务综合／grt上限3600／7200秒。物理失败不会补成数值，也不会改选D。

完整工作目录：`/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-v1`。其中`software/selected/`含逐目标RTL、state、owners、预算／等效T／实际Query、192周期整数／reset／停顿仿真收据；`software/*/scores-T*/`保留候选完整轨迹；各物理批次的`runs/`保留工具命令、环境、固定数据库、原始报告及readout。原停止队列未续跑。

复现与核对命令：

```bash
VULSIM_WORKLOAD_V10_BINARY=build/workload-v10-20261115/rtlzz-workload python3 -m unittest regression.test_workload_guided_search regression.test_workload_equivalent regression.test_workload_diagnostic regression.test_workload_v10 regression.test_workload_abcd regression.test_workload_final
python3 -m experiments.arithmetic_dse.workload_final_replay --root /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-v1/software
python3 -m experiments.arithmetic_dse.workload_final_driver report --root /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-v1
python3 -m experiments.arithmetic_dse.workload_final_publish --root /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-v1 --evidence /home/zyrv/vulsim/experiments/arithmetic/evidence/workload_equivalent_steps678_v1
```

软件验证收据见validation.json。原静态池9例659候选、167567次所有者观察的消费者绑定审计无缺失，27份A／B／C通过原生所有者、整数语义、G和参数绑定检查；新扩展候选仍需原生验证并对最终RTL重新仿真。软件覆盖不授予边界或响应精度资格。

原§1.8的Add／Mux／G／S失败以及第4步S、shared、嵌入外壳缺口保留。软件正确、模型精度、目标满足和D相对C的收益分别评价；目标未满足或D不优于C均如实报告。
