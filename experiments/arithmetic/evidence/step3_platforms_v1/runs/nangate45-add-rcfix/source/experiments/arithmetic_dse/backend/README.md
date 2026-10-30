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

当前策略为 `configs/backend_policy_v4.json`，保留 128 synth / 96 grt / 28 detailed、12h墙钟/48h CPU 额度及 TT/hold 口径。所有物理及生成/验证叶命令使用共享账本 `experiments/arithmetic/backend_usage.json`；snapshot、环境和验证仅计时间。外层包装不重复计费，失败/超时/重复调用照计，未结算预约不自动退款。当前 checkpoint 为 `experiments/arithmetic/evidence/step3_closure/usage_checkpoint.json`，克隆从归档消耗继续。CPU/RSS按0.5s采样，GNU time结算实际CPU，清理可能有有限超额。

`configs/characterization_v3.json` 把500/800/1000/1250/1500/2000ps保留为候选点集，已完成的乘法六点历史数据继续保留；后续不普遍要求19个模型族各测六点。必需数据为1500ps参考，以及D实际查询的精确ABC/SDC目标、实现特征和阶段；代表性乘法/除法/浮点先做预声明少量探测，再决定额外点集。D2/F1实际实现后可在步骤四/六检查，不阻止步骤三关闭。未测上下文仍uncovered，两个轴均保留，不使用相邻点一致性来创建覆盖。

`--period-ps` 指定SDC周期，`--abc-target-ps` 可独立固定ABC目标（默认跟随周期）；`--io-delay-max-ps` 可固定I/O绝对最大延迟，省略时保留原20%周期规则。每份身份记录分别保存ABC、SDC和I/O策略。原ORFS具名speed脚本不自动接收Yosys `-D`；隔离 `flow-scripts` 中的 `abc_speed_target.script` 显式传给 `&nf/upsize/dnsize`，外部ORFS无改动。

本轮预声明对照固定ABC1500ps、I/O max300ps、L2/II1及物理参数，仅改变SDC时钟500/2000ps。两次新目录综合真实计2 synth，实际映射网表一致；之后2 grt，以及共同1500ps SDC重新STA（仅支持时间）。网表、master尺寸/缓冲数量、放置、路径、修复日志及共同SDC指标随证据保留，不能只凭各自slack判断响应。共同STA没有再次优化物理实现。控制入口：

```bash
python3 -m experiments.arithmetic_dse.physical_control --out build/new-physical-study
```

该命令重跑真实工具并计费。只校验证据请使用：

```bash
python3 -m experiments.arithmetic_dse.evidence
```

当前冻结 `experiments/arithmetic/backend_freeze_v4.json` 和 `experiments/arithmetic/evidence/step3_closure/` 包括旧关键路径核查、受控物理对照、账本和验收摘要。先前v1/v2/v3及所有历史证据保持不变。步骤三不要求完成D库、D2/F1硬件或主矩阵，也不要求完整预算立即闭合。

完整采集清单与资源预算仍须在步骤五批量物理工作前冻结闭合，配置为 `budget_plan_v2.json`；代表性探测包含在原型预留里。当前保守场景369/329/45且清单未冻结，预期blocked；旧462/422/45保留为原方案规划记录，两者都不是实际消耗/最低需要/授权新上限：

```bash
python3 -m experiments.arithmetic_dse.budget --check-plan
```
