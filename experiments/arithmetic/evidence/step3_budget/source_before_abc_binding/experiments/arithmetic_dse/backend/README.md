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

`configs/backend_policy_v3.json` 使用同一套 TT/hold 口径，保留 128 synth / 96 grt / 28 detailed 初始上限。后端入口现在立即共享 `experiments/arithmetic/backend_usage.json`：叶命令启动前通过 flock 和原子写入预约，失败/超时/重试照计次数，环境/报告快照只计时间，外层包装不重复计费。历史 checkpoint 包括本次及之前的调用；克隆后从该消耗继续，不能从零开始。不要删除账本；跨机器推进前必须归档新 checkpoint。未结算预约阻止新物理调用，必须依据命令证据显式处理。线程、内存及单作业超时不能超过冻结策略。

CPU/RSS 每 0.5 秒按跨 session 后代树采样，GNU time 结算叶命令实际 CPU；短命进程可能未被 CPU 采样捕获，事后仍计费，清理也可能有有限超时。累计墙钟使用后端叶命令时间，生成/验证与外层包装时间单列。命令中断缺少 CPU 证据时保留完整 CPU 预约，不自动退款。

`configs/characterization_v2.json` 采用 500/800/1000/1250/1500/2000 ps 六个 synth 目标。500/800 ps 用来观察紧约束，也保留无法满足时序的测量；不是保证可达。两个点面积/最小时钟相同不终止六点，不把一个核推广成模型族目标无关。比较身份中去掉目标字段后，还比较规范化网表（去 Yosys banner、src 属性及空行）与功能/顺序面积。D2/F1 实现后各自做六点，最迟步骤六完成。grt 可预声明稀疏集合；未测阶段/目标仍返回 `uncovered`，所需案例精确目标在搜索前必须补测。案例目标仍从 1500 ps 参考微基准按冻结公式计算一次。

预算检查前移至步骤五之前，使用 `configs/budget_plan_v1.json`，现在即可检查：

```bash
python3 -m experiments.arithmetic_dse.budget --check-plan
```

六点为 114 次初始建库，基础 186 synth / 168 grt。补上历史、案例精确目标补测、步骤四至六原型/大核检查、新模板/边界、详细复核重跑的 synth/grt、重复和重试后，旧额度不足，命令预期返回 blocked/非零。未冻结九个实际周期时，先为全部 19×9 潜在补测预留；已知时可传 `--case-targets` 后跟九个周期。不能把未执行的两点提前退出或缓存当作节省。步骤五前须版本化资助完整剩余计划；当前检查不会自动放宽上限，完整 D 代价库尚未建立。

当前冻结为 `experiments/arithmetic/backend_freeze_v3.json`，本轮便携证据在 `experiments/arithmetic/evidence/step3_budget/`；v1/v2 及原 step3 证据保持历史字节。验证无需 build/工具安装：

```bash
python3 -m experiments.arithmetic_dse.evidence
```
