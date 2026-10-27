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

流程状态与时序判定分开：工具成功退出为 `completed`。grt 的 `measured_feasibility` 表示完整覆盖及 TT setup 非负，报告明确标为 `feasibility_scope=TT_setup_only`；hold 始终单列，负值标记风险，0～5 ps 标记需要复核，达到 5 ps 也只表示达到工程复核带。详细布线仍要求 TT setup/hold 非负、提取 SPEF、零路由 DRC；hold<5 ps 继续标记窄裕量。5 ps 不是测得的噪声底，`multi_corner_signoff=false`，TT 通过不能解释为最坏角保证。综合只有 `sta_feasibility`。缺失/失败阶段保持缺失，不能使用更早指标填补。

复核带作用于已含原有 hold 不确定度的报告 slack，不修改 SDC，也不再从该 slack 扣除 5 ps。

每条命令同时记录 GNU time 的 CPU/峰值 RSS 和每 0.5 秒采样的后代进程树 RSS 总和、线程数。`processes.py` 通过 PID/启动时间及继承的运行标记跟踪后代，包括嵌套调用产生的新 session、快速退出父进程留下的孤儿。超时、内存超限或收到 SIGTERM/SIGINT 时，先 TERM，宽限后对存活后代 KILL；即使外层 leader 已退出仍继续清理并记录 `remaining_live_pids`。命令退出却遗留后台后代也记失败。SIGKILL 无法由被杀进程捕获；正常取消应使用 TERM/INT。

内存采样可能漏掉瞬时峰值，RSS 求和也会重复计入共享页，因此两种记录都保留。默认综合 300 秒、从布局到全局布线 1200 秒、详细布线与提取增量 1200 秒，快照 120 秒；后代树 RSS 上限 8192 MiB，不自动重试。

`configs/backend_policy_v2.json`（相对包目录）记录当前阶段/hold 口径、12 个基础详细布线复核点和最多 4 个临界补充点，以及初始资源限制；v1 保留为历史。累计搜索/主矩阵计数器依赖步骤七驱动。`configs/characterization_v1.json` 要求至少 1000/1500/2000 ps 三个建库目标点，模型和缓存显式包含 ABC 目标、SDC 周期及完整流程指纹。首版只接受精确已测目标，区间内未测点也返回未覆盖，禁止外推。案例目标制定统一使用 1500 ps 参考点的微基准，一次计算冻结，补测目标不回改案例周期。

19 类微基准三点至少需要 57 次采样；加 36 条共同评价和 D 搜索预留，综合基础调用达到 129，若全部采集 grt 则基础调用 111，已经超过原初始 128/96 上限。步骤七采集前必须先版本化重算预算，不能自动超限。这里的三点探针只是验证上下文记录，不是已完成的 D 数据库。

面积与最小时钟周期都对应记录的 ABC/SDC 目标和映射后的实现，不能把 1500 ps 条件下的 1221 ps 最小时钟周期当成算子的固有延迟。每次 manifest 的 `mapping_context` 及其哈希保存 ABC 目标、脚本、SDC、库/LEF/RC、流程和工具指纹。

实际验证目录为 `build/step3-asap7-20261026-93ltulln/`：`trial1/2` 保留报告接口适配的初始失败，`trial3/4` 是完整独立运行，`entrypoint/` 验证单命令入口到全局布线，`invalid-evaluation/` 验证错误 RTL 的综合失败，`resources.json` 和 `repeatability.json` 保存资源与重复比较。新的后端契约回归为 `python3 regression/arithmetic_backend.py`，不依赖安装的 PPA 工具。

复核修订的原始运行位于 `build/step3-review-20261026-zz1wa66l/`。关键小型证据、v1/v2 源码快照已归档到 `experiments/arithmetic/evidence/step3/`，当前冻结为 `backend_freeze_v2.json`。普通 clone 在没有 build 或 EDA 安装时可运行 `python3 -m experiments.arithmetic_dse.evidence` 检查仓库内源码、摘要和历史哈希；有原始工具安装时可加 `--verify-external`。归档内的原始路径仅表示来源，不是默认校验的依赖。
