# 第6～8步：九例等效预算版本 ABCD

当前完成统一 grt 实测的主方法记录为 **24/76**。本轮正在执行物理比较；共享模型仍为诊断身份，完整精度资格没有通过。

本轮响应参数沿用第1～5步冻结版本。Sub／Compare采用既有train源均衡池化的公共采样H代理，功能消费者绑定实际Boolean-cover节点；原四类边界及响应不变。先按候选路径联合分配本体预算，再反解等效训练T并调用原函数，S／shared／控制及实际ABC保留整机T。超过原6000ps反解区间的请求显式扩展至有限100000ps区间，均属未取得精度资格的外推。

新增全局依赖路径均衡位置由原生接口验证并物化。静态C仍按原统一表选择；MAC32保留第5步175个完整候选的原数值，其他案例保留每结构的静态路径／状态代表，再增加有限静态／模型压力位置。共同池静态价格归因与正式C分别列出。

用户已确认新目标规则：其余八例以未拆分、L1的A的完整grt RR／IR／RO Tmin为参考；A映射请求按其冻结模型软件周期的1.10倍向上取整至100ps、至少1000ps，统一在测量前登记，分别取1.25×／1.5×[Tmin(A)/L]，向上取整到50ps；取整重合时第二档加50ps。MAC维持500／750／1000ps、L3。参考A只确定目标，不证明所有映射中的最快A，最终A也在各比较T下另测；不再以C或最终D的结果放宽目标。

| 批次 | 数据角色 | 任务数 | 完成 | 失败 | 活动／排队 |
| --- | --- | ---: | ---: | ---: | ---: |
| A-reference | clock_calibration | 8 | 7 | 1 | 0 |
| A-reference-repair-v1 | clock_calibration | 1 | 0 | 1 | 0 |
| final-add512 | final_evaluation | 6 | 6 | 0 | 0 |
| final-barrett64 | final_evaluation | 10 | 0 | 0 | 10 |
| final-horner64 | final_evaluation | 10 | 0 | 0 | 10 |
| final-karatsuba256 | final_evaluation | 10 | 0 | 0 | 10 |
| final-mac32 | final_evaluation | 15 | 15 | 0 | 0 |
| final-mul128 | final_evaluation | 8 | 6 | 2 | 0 |

后续独立案例的软件评分可在隔离目录提前执行，继续调用原冻结选择器、同一候选规则及目标；完成后才导入主目录，已开始的串行案例拒绝导入。输入／完成／导入收据位于`parallel-software/`；附加Add512隔离重算仅验证数值一致性，不启动EDA。

Montgomery256参考A的原grt在CTS修复网表的Kepler等价性检查中超时，原失败、命令和费用保留。另立有限后继，原RTL、参考T、映射和物理变换保持；仅验证调用使用保守充分条件：消去Liberty明确为恒等的缓冲后，逐一核对非缓冲实例逻辑／状态签名、全部输入来源及顶层输出。任何不支持的变化或300秒超时均使原CTS调用失败，不跳过检查、不自动回退。新批次绑定验证器／证明器源码，实际ORFS调用收据见`repair-verification.json`；该方法不是通用SAT证明器。原失败摘要见`physical-failures.json`。

| 案例 | 探针请求 ps | 完整 Tmin ps | 面积 µm² | hold WNS ps |
| --- | ---: | ---: | ---: | ---: |
| add512 | 1100 | 1059.68 | 2133.39 | 0.272 |
| mul128 | 2000 | 1884.84 | 7225.60 | 0.193 |
| dot16 | 2700 | 2705.13 | 33186.75 | 1.880 |
| horner64 | 7600 | 5981.93 | 4147.27 | 1.691 |
| barrett64 | 6000 | 5603.33 | 7497.33 | -4.240 |
| karatsuba256 | 9700 | 7201.31 | 21206.92 | 11.165 |
| ntt8x64 | 9700 | 9734.20 | 11182.52 | 13.048 |

| 案例 | 未拆分A参考 Tmin ps | L | 已冻结目标 ps |
| --- | ---: | ---: | --- |
| add512 | 1059.68 | 4 | 350 / 400 |
| barrett64 | 5603.33 | 8 | 900 / 1100 |
| dot16 | 2705.13 | 8 | 450 / 550 |
| horner64 | 5981.93 | 8 | 950 / 1150 |
| karatsuba256 | 7201.31 | 8 | 1150 / 1400 |
| mac32 | 原确认目标 | 3 | 500 / 750 / 1000 |
| mul128 | 1884.84 | 4 | 600 / 750 |
| ntt8x64 | 9734.20 | 16 | 800 / 950 |

物理口径为 ASAP7 RVT TT / TC25C0.7V、NLDM、post-CTS grt估计RC；标准单元面积排除filler并包含taps，I/O max=0.2T。完整setup阈值有±0.1ps括号检查；hold与约束覆盖另报，不把grt写成final或多角签核。

同RTL／T／工艺／约束身份共享物理任务。每批全新冻结、自动重试0，共享账本保留所有历史开销。每工具4线程、8GiB、并发3；大型任务综合／grt上限3600／7200秒。物理失败不会补成数值，也不会改选D。

完整工作目录：`/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A`。其中`software/selected/`含逐目标RTL、state、owners、预算／等效T／实际Query、192周期整数／reset／停顿仿真收据；`software/*/scores-T*/`保留候选完整轨迹；各物理批次的`runs/`保留工具命令、环境、固定数据库、原始报告及readout。原停止队列未续跑。

复现与核对命令：

```bash
VULSIM_WORKLOAD_V10_BINARY=build/workload-v10-20261115/rtlzz-workload python3 -m unittest regression.test_workload_guided_search regression.test_workload_equivalent regression.test_workload_diagnostic regression.test_workload_v10 regression.test_workload_abcd regression.test_workload_final
python3 -m experiments.arithmetic_dse.workload_final_replay --root /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/software
python3 -m experiments.arithmetic_dse.workload_tight_continue report --root /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A
python3 -m experiments.arithmetic_dse.workload_final_publish --root /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A --evidence /home/zyrv/vulsim/experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2
```

软件验证收据见validation.json。原静态池9例659候选、167567次所有者观察的消费者绑定审计无缺失，27份A／B／C通过原生所有者、整数语义、G和参数绑定检查；新扩展候选仍需原生验证并对最终RTL重新仿真。软件覆盖不授予边界或响应精度资格。

原§1.8的Add／Mux／G／S失败以及第4步S、shared、嵌入外壳缺口保留。软件正确、模型精度、目标满足和D相对C的收益分别评价；目标未满足或D不优于C均如实报告。

调度后继及验证适配器的相关回归为95项，全部通过，含错误时钟／函数／复位、未完成A／缺少证明收据及归档损坏等拒绝检查；见`continuation-validation.json`。

另预登记MAC32的750／1000ps两份D各一次冷启动重复，用于检查接近目标的setup／hold分类是否稳定；不改选、不替换主表、不据此估计通用噪声界。计划见`near-target-repeat-plan.json`；只有存在`near-target-repeat-results.json`时才表示两项复核已执行。

为保留后续大案例空间，仅对已结清批次的中间ODB做可逆gzip归档。原始字节、路径、大小和SHA256及压缩文件SHA256记在各批次`storage-index.json`，先逐字节回解校验再移除原ODB；RTL、网表、readout和报告仍可直接读取。恢复命令：

```bash
python3 -m experiments.arithmetic_dse.workload_storage restore --batch /home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/<batch>
```
