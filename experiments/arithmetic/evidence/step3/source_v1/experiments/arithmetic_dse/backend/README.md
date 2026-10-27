# ASAP7 TT 后端评估

从仓库根目录执行完整试跑：

```bash
python3 -m experiments.arithmetic_dse.run \
  --out build/asap7-probe-new --stage final --period-ps 1500 --threads 2
```

该入口先使用已构建的 `build/vulsimgen` / `build/vulrtlgen` 生成 `experiments/arithmetic/backend_probe/Main.utb`，分别运行软件和原生 Verilator 功能检查，然后进入 ORFS。每次使用新的输出目录。默认 ORFS 为 `/home/zyrv/OpenROAD-flow-scripts`，可用 `--orfs` 指定另一个兼容的源码/工具安装目录。1500 ps 只用于本步骤资源试跑，不是正式案例的目标周期。

对已有的自包含原生 RTL，可以直接执行：

```bash
python3 -m experiments.arithmetic_dse.backend \
  --rtl build/asap7-probe-new/native/sim/top.sv --top MulProbe_sim_top \
  --out build/asap7-candidate-new --period-ps 1500 --stage grt --threads 2
```

`--stage synth` 停在映射及综合 STA，`grt` 包含布局、CTS、全局布线及寄生估计，`final` 继续详细布线、填充和 OpenRCX 提取并读取 SPEF。后者直接请求 ORFS 的 `6_report.log` 目标，避免引入本步骤不需要的 GDS 合并。当前适配器接受单个自包含 RTL 文件、普通 Verilog 顶层标识符及无空白的 Make 路径；不支持的输入会留下明确失败状态。

固定设置在 `asap7.mk` 与 `constraints.sdc`：TC/RVT/NLDM、ABC speed 模式、slang、层次优化、单比特触发器、关闭重定时、固定种子 42。五份实际选中的 TT Liberty 均需为 0.70 V、25°C、ps/fF，平台的温度元数据通过 Make 命令行覆盖为 25°C。真实文件列表、工具版本、Liberty/LEF/RC/映射及流程脚本哈希写入每次运行的 manifest。

SDC 定义实时时钟及同周期虚拟 I/O 时钟，setup/hold 不确定度为 20/5 ps，时钟输入转换时间为 10 ps；I/O 最大延迟为周期的 20%，最小延迟为 0，非时钟输入使用 BUFx2 驱动，输出负载 3.898 fF。同步 `rstn` 与 valid/数据都参与时序分析。没有把复位路径删去，也不修改主案例的 L/II。

每个阶段从对应的 ODB/SDC 重新提取原始单位、setup/hold worst slack、TNS、覆盖检查、关键路径、最小时钟周期及逐 master 面积。面积与 ORFS 的 `design__instance__area__stdcell` 对齐，排除 CORE_SPACER，包含 tap；功能、顺序单元及物理专用单元面积另列。Liberty 和 LEF 单元面积必须匹配。最小时钟周期是含规定边界及时钟约束的 STA 指标，不能称为算术组合路径时延。组合时延的专门定义和微基准审计留在步骤七。

流程状态与时序可行性分开：工具成功退出为 `completed`，`measured_feasibility` 还要求 setup/hold 非负及完整时序覆盖；详细布线阶段还要求提取 SPEF、零路由 DRC。综合只有 `sta_feasibility`，不据此宣称物理可行。失败在 manifest 中保留阶段、命令、退出码、超时和内存标志；后续未完成阶段的指标缺省，不使用前一阶段替代。

每条命令同时记录 GNU time 的 CPU/峰值 RSS 和每 0.5 秒采样的进程组 RSS 总和、线程数。内存采样可能漏掉瞬时峰值，RSS 求和也会重复计入共享页，因此两种原始记录都保留。默认综合 300 秒、从布局到全局布线 1200 秒、详细布线与提取增量 1200 秒，快照 120 秒；进程组 RSS 上限 8192 MiB，超限或超时终止整个组，不自动重试。

`configs/backend_policy_v1.json`（相对包目录）记录主表采用全局布线估计、12 个基础详细布线复核点和最多 4 个临界补充点，以及初始候选、调用和总资源限制。原型已有单作业约束；累计搜索/主矩阵计数器依赖步骤七的搜索驱动。更大的除法/浮点试跑完成后，须在主矩阵前复核这些初始数值，不能将本步骤单个乘法核的耗时外推为全部案例的保证。

实际验证目录为 `build/step3-asap7-20261026-93ltulln/`：`trial1/2` 保留报告接口适配的初始失败，`trial3/4` 是完整独立运行，`entrypoint/` 验证单命令入口到全局布线，`invalid-evaluation/` 验证错误 RTL 的综合失败，`resources.json` 和 `repeatability.json` 保存资源与重复比较。新的后端契约回归为 `python3 regression/arithmetic_backend.py`，不依赖安装的 PPA 工具。
