# ASAP7 通用函数驱动的 D 原型

本包将已发布的小算子函数、真实状态S、冻结共享面积函数与规范化DAG零G组合接入D选择器，按用户决定暂缓reset时序保护。功能reset及流水valid／使能仍发射并验证。范围为`prototype-no-reset-timing-v1`，`prototype_D_selection=true`表示已完成本范围内的真实模型选择与RTL产出；完整独立联合资格仍未授予，`formal_D_selection=false`、`full_D_ready=false`。

从仓库根目录调用：

```bash
python3 -B -m experiments.arithmetic_dse.run_function_d \
  --source-request /home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1/source-request.json \
  --period-ps 1500 --latency 2 \
  --out /home/zyrv/vulsim-artifacts/D-my-run
```

`--out`必须是尚不存在的目录。T是数值输入；当前目标支持区间为500–3000ps，仍须通过节点语义／负载、S和共享特征的联合支持。改变`--period-ps`即可重新计价和选择，不需要添加精确时钟编号或采集候选价格。L包含核心N=L−1级及1级输出capture，输入服务launch另列，II=1；其他L也经实际模型逐候选检查，缺覆盖时拒绝产出，不承诺当前S域之外的流水深度。

生成目录包含：

- `D.sv`：top为`D`的完整RTL，含独立输入写使能／held-valid服务寄存器、核心及无条件输出capture。
- `D_core.sv`：top为`D_core`的核心RTL，保留统一算子层次。
- `selection.json`：全部候选、逐节点函数、实际状态、位连接、S／共享独占面积、阶段时序及选择状态。
- `selected.pipeline.txt`：实际物化的寄存器位置与流水图。
- `source.cpp`、`source.json`、`invocation.json`：源和本次调用身份。

完整模型覆盖时，预测满足T的方案中选总面积最小者；全部超预算时选最大时序违约最小、面积打破并列的后备方案，并标`target_unmet`。任一候选缺价格或枚举不完整则报告`cost_uncovered`、不输出RTL。当前MAC32的44个合法放置来自结构枚举，计价函数不输入视图ID，也不要求固定44。

依赖和消费者SHA见[bundle.json](bundle.json)。`operators`指向相邻的原节点发布，S、服务见证和composition文件沿原冻结字节复制。G=0，节点最大值、S／连线和单次50ps预留依照前序已验证口径消费；未把旧逐节点reserve再次叠加到决策值。

实现入口为`rtlzz-d`，可用`build/step4-rtlzz/rtlzz-d --help`查看原生参数。构建命令：

```bash
cmake -S rtlzz -B build/step4-rtlzz
cmake --build build/step4-rtlzz --target rtlzz-d --parallel 4
```

本交付的Python入口绑定已验证二进制SHA，避免静默消费另一版本实现；完整验证记录见[§7.78](../../../../mission/lxy-plan-fix.md#step8-function-D-output)及其证据。预测可行不等于已经获得该RTL的物理时序通过结果，reset时序与完整独立联合资格保留原状态。
