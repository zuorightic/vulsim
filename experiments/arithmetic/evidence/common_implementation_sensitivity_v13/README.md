# W3／W4／W5：实现敏感性的有限train对照 v13

本轮完成四个已有train父源的8个物理点：每源一次原样复测、一次数学等价的RTL表达变体。**原样复测全部一致；S独立时序语句重排使valid R分别变化+73.85ps、−125.11ps，并反转原reset对照差的符号；Add／G操作数交换全部一致。** 本轮没有拟合模型或发布新价格，W3—W5和W6的未通过结论保留。

现行入口为[任务导航](../../../../mission/README.md)和[§7.112](../../../../mission/lxy-plan-fix.md#W345-implementation-sensitivity-controls)。外部原始产物根：`/home/zyrv/vulsim-artifacts/W345-implementation-sensitivity-20261114-v13`。本目录可在没有该绝对路径、EDA工具和工艺库的克隆中复核紧凑证据；原始ODB／完整网表与日志继续外置。

## 登记范围与数据职责

| 组件 | 已有train父源 | T（ps） | 原样复测 | 等价表达变体 |
| --- | --- | ---: | --- | --- |
| S | S-d0fb525b1fcecb5c | 500 | 完整原RTL字节 | 每个模块内反转独立单目标nonblocking时序语句的次序 |
| S | S-aac8767d3e7162b7 | 500 | 完整原RTL字节 | 同一规则，保留reset／invert／连接／声明／名称／属性 |
| G | new/G-4eab470e164ce4a1 | 1500 | 完整原RTL字节 | `t0+t1+t2`→`t1+t0+t2`，保持原加法结合顺序 |
| Add | operator-3b03a3d382938143 | 500 | 完整原RTL字节 | 11位扩展后的两个加数交换，完整结果不变 |

正式协议、源字节、T、角色、资源及停止条件均在调用工具前登记。先完成四个repeat及严格测量核对，再开放四个variant；max4任务×4线程、8192MiB／工具、synth300s／grt1200s，0自动重试。8点全部完成，0物理失败／重跑。没有新增独立函数、validation或test源，没有消费旧回归挑模，20个独立算子源保持锁定。

所有变体今后若用于训练，须与原父源及所有T共同排除。`fold-bindings.json.gz`补齐真实的继承fold：两份S同属`3e314bd1…578ad7`家族，与已有reset／contrast成员一起隔离。协议里的`parent_group`是源身份，不能误作各自独立的LOSO fold。当前所有新对照均不进入拟合，不复制repeat充当独立观测。

## 结果及机制边界

以下为寄存器valid路径的`R=d+H=T−slack`，不是整级Tmin或整级最高频率。每份银行的逐源valid最大值在这里恰与aggregate native_valid相同；其它控制类、setup／hold及面积另存于完整分析。

| S银行 | 原始／repeat R（ps） | 语句重排R（ps） | R变化（ps） | cell变化（ps） | wire变化（ps） | H变化（ps） |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| d0fb525b1fcecb5c | 261.670334 | 335.516235 | +73.845901（+28.22%） | +66.644989 | +10.629409 | −3.428497 |
| aac8767d3e7162b7 | 439.958973 | 314.848190 | −125.110783（−28.44%） | −57.377349 | −58.704362 | −9.029072 |

两份S的原样复测在synth／grt面积和全部13类／逐源路径R上逐项相同，四源归一化映射网表也逐项相同。重复实现支持旧标签在本次固定环境下可复现，不据一个repeat给全域确定的噪声界。

语句重排后，旧reset对照的grt valid差`439.958973−261.670334=+178.288639ps`变为`314.848190−335.516235=−20.668045ps`。两份variant的synth valid R都为185.645233ps，grt差异主要产生于后续实现。总grt面积却仅分别增加1.458000um²（0.10345%）、0.014580um²（0.00103%），不能由面积几乎不变推出控制时序相近。

这四条native_valid路径的端点均为`native/valid_1…/QN`→`native/valid_2…/D`，没有hold命名单元。第一源原树经过INVx8→BUFx4f→AND2，重排后经过INVx8→BUFx3→BUFx6f→AND2；第二源原树经过INVx8→BUFx3→BUFx6f→AND2，重排后为INVx8→两个BUFx3→AND2。保存每段实际Liberty弧、连线、负载pin及负载master，并保留placement repair日志摘录。H的变化较小，主要变化在cell／wire。这里的命名只描述保存路径，不对每个buffer强行分配某条修复命令。

匹配的OpenROAD仍为`84e3ff1eb2c36302cef42e4f70a69efe4cfbb126`；已保存`fullyRebuffer`的逐load时序预算、缓冲与面积回收机制。该源码与本轮对照支持进一步检查共享树的不同分支预算及发射前连接信息，尚未证明单一因果机制。语句顺序影响未命名内部逻辑、映射身份及后续缓冲实现；归一化网表hash不同也不能单独证明逻辑拓扑不同。

S的52个class／逐源路径比较（包含aggregate与逐源重叠项）中，原样复测绝对相对变化median／P95／max均0；variant为0.3596%／28.2210%／28.4369%。它们用于逐路径诊断，不能当52个独立函数。native_enable仍接近500ps：两源变化−1.139533／+1.407041ps。valid变化不能直接转述为完整阶段频率变化；input_valid另有−1.015900／+21.116700ps，hold／clock职责继续单列。

Add的grt本体面积5.554980um²、时延246.421432ps；G为28.547640um²、433.330109ps。两者原样repeat及操作数交换的synth／grt本体面积、时延和归一化映射网表均相同。这一交换因素没有解释其旧面积误差，不为原失败增加价格资格。v12的额外最坏源门槛与拒绝结果保持；项目默认median≤15%、P95≤35%的门槛也保持，本轮不另加更严格门槛。

本轮变体只作实现敏感性诊断，生产发射器未变。固定发射、固定流程仍得到可复现标签；这些结果不构成“物理标签不可学习”的结论，不用变体替换原标签、取最优值或给D增加实测价。后继应先审计可预测的lowering／共享连接与缓冲分支预算，形成有限、可检验的假设，再登记选模；不能继续仅扩reset比例／alpha网格或抬reserve。

## 等价门禁及保留失败

第一版RTL等价脚本保留了`keep_hierarchy`，top级证明未展开子模块，故意破坏`native.valid_1`的负例竟然通过。该门禁失败阻止了全部物理调用。保存原正例／错误负例日志、两次support收费及失败收据；未将它们报告为通过。

另登记`preflight-v2-admission`：只在证明副本中删除模块／实例的`keep_hierarchy`，断言无子模块残留，完整展开后运行`equiv_make／equiv_simple／equiv_induct`。4份正例全部证明，4份故意改变valid或加法的负例全部拒绝，之后才开始8点物理测量。生产RTL、测量源和原物理协议均未改。4次预期负例的工具非零退出单独计数，与0物理失败区分。

另保留一次纯准备错误：v11候选文件实际名为`nested-candidate.json`，首次准备错用了`candidate.json`，在protocol／admission生成前失败；修正名称并核对部分源字节后继续，0工具重跑。

## 验证、费用与复核

6项新增重写证书测试通过。离线回放核对4源RTL证书、完整等价正负收据、12份物理CEC对（8新＋4继承）、16组stage比较、104项S路径比较、156条保存S路径及156个删除真实Liberty弧的负例；包含原始points／report、cell＋wire守恒、R／H标签及真实net连接。归档411份仓库源身份、452份文本源／工具记录，v10／v11／v12冻结依赖复核未变。

共享Ledger本轮增量：synth8、grt8、final0、support66；工具累计wall586.824249s、CPU1103.210000s，pending0。累计synth3546、grt3515、final16、support22552；wall364965.978581s、CPU744678.540000s。support66含最初失败证明2、修正版证明8和物理采集support56，失败与预期负例均收费。

仓库共享`backend_usage.snapshot.json.gz`及元数据同步到全部29629条累计记录，保留checkpoint前缀和此前尚未导出的历史，不清零账本。导出收据另存`ledger-snapshot-export.json`，便于新克隆继承当前收费；历史证据回放不把未来可增长的共享快照固定为旧版本。

在仓库根目录执行：

```bash
python3 -m unittest regression.test_rtl_sensitivity_v13
python3 -m experiments.arithmetic_dse.implementation_sensitivity_replay_v13
```

回放只读便携证据及仓库代码，不调用EDA、不需要外部产物根或工艺库。完整重新采集有真实费用，须依协议恢复工具／库及路径后另作有限准入，不能直接把归档脚本当自动重跑入口。历史协议中的绝对路径仅作来源追溯。

主要文件：`protocol.json.gz`／`admission.json.gz`登记范围与冻结源；`analysis.json.gz`含全部实现、逐源结果和比较；`mechanism-audit.json.gz`含负载／修复日志线索；`fold-bindings.json.gz`保留家族隔离；`proof-receipts.json.gz`、`path-proof-cases.json.gz`提供证明材料；`settlement.json`记录所有新增收费及累计账本。文件SHA见`identity.json`。
