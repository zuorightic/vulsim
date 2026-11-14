# W3／W4／W5：单向预测负载压力与冻结回归 v7

本包冻结 `W345-load-pressure-functions-v7`，交付可回放的共享函数、Python／C++消费者、跨银行上下文隔离、支持域与逐源失败证据。**S仍不合格，W3—W5未整体关闭；公共D没有切换。** 本次0新EDA、0新验证源，所有旧验证只作已消费回归，20个算子独立源继续锁定。

候选／runtime SHA256：`1191e27d6a0b626537a4ef51cbafc7df3196039326ac9cab9a33757dc256be41`。原始产物与临时工具：`/home/zyrv/vulsim-artifacts/W345-load-pressure-20261114-v7`。前驱为[v6重缓冲包](../common_rebuffer_context_v6/README.md)，物理观察及费用保持原职责。

## 本次实际变化

W4新增明确的单向依赖：`语义结构 → native_enable共享函数 → 预计时序压力／松弛代理 → native_valid共享函数`。先用冻结算法拟合enable，再拟合valid；最终enable上下文与对外enable价格函数必须逐项相同，消费者拒绝两者漂移。上下文不用实测slack、mapped树、电容、实例身份或候选价格。该依赖没有S／G循环。

在13个外层fold中，每次先排除整个旧／新reset配对银行及全部T，再拟合enable基础函数；valid的训练和留出特征均使用该fold的基础函数。最终基础函数只用17个train银行重拟合。14次基础拟合是固定依赖，36项valid候选才是超参比较。228条选中valid训练／LOSO特征均按其对应基础函数重新计算核对；训练行摘要及pair隔离可独立回放。

上下文包括 `log2(1+R_enable/T)` 及reset／native交互，并试用 `(.25·max(0,T−R_enable)+.01·R_enable)/T` 的松弛代理。后者参考v6保存的OpenROAD面积回收机制，但不是OpenROAD真实target slack，不能称物理树预测或因果证明。每个算子仍全宽共享参数，T保持连续数值输入。

S诊断支持域重新按全部17个train银行的**数值几何**推导，使用原distinct-geometry算法（k=2，radius factor=1.05），坐标含FF、sink、enable load、输入根最大负载、reset比例及state depth；无价格标签、源ID或精确T路由。S消费者直接检查语义和本版支持域，不先消费旧S价格。训练点覆盖从v6的54/57变为57/57，但跨银行留出完整实现仅33/57通过支持：native_valid 78/114路径、native_enable 78/114、input_valid 39/57、external_valid 33/57。**完整训练覆盖不代表未知银行资格。** 下列LOSO精度按全部登记训练源报告，不删除支持拒绝行来改善误差。

W3／W5新增进位单操作数尾段、进位可达长度、稀疏间隔、prefix／ripple合法门工作量比及G串联／融合面积比。预登记66项有限比较为Add9、Mux3、G18、S36；Add与G按整体、小工作量／零压缩及所有源最差损失的minimax选择，Mux保留原规则。**Add、Mux、G面积及G时延的入选参数全部与v6相同。** 新静态形式没有胜出，完整负结果保留，不凭机制名称强行换模。

## 训练内结果与失败

误差为源等权median／P95，原始逐路径口径单列。LOSO参与训练内选择，不是新的独立测试。

| 项目 | v7 median / P95 | 解释 |
| --- | --- | --- |
| Add面积，18源／53点LOSO | 8.41% / 13.96% | 参数同v6；仍有单源15.61% |
| Mux时延，5源／15点LOSO | 14.62% / 19.33% | 参数同v6；两源19.45%／18.84% |
| G面积，27源／81点LOSO | 3.76% / 13.98% | 零压缩12.96%／18.02%，64位源19.33% |
| G时延，27源／81点LOSO | 4.56% / 15.81% | 两train源20.62%／17.07% |
| S enable银行max，成对LOSO | 7.83% / 13.95% | 最大单源14.67%；仅训练诊断 |
| S valid银行max，成对LOSO | 17.97% / 29.24% | v6同行17.54%／29.19%，median退化 |
| S valid逐路径先源聚合 | 12.65% / 17.87% | 不能代替银行max或原始尾部 |
| S valid原始114条路径 | 8.02% / 36.12% | v6 P95 38.14%；本版仍失败，max94.06% |
| S valid服务分支 | 6.61% / 31.17% | 单源最高47.08% |
| S valid native分支 | 17.62% / 24.39% | median失败 |
| S valid全零reset，4银行逐路径源聚合 | 15.25% / 25.39% | median失败 |
| S valid混合reset，13银行逐路径源聚合 | 11.80% / 14.54% | 不转授全域 |

逐源S成对LOSO表（每源跨T聚合；valid path列先在源内聚合路径）：

| 源 | valid银行max | valid path | enable银行max |
| --- | ---: | ---: | ---: |
| S-ab497c57b8a9bd6d | 24.35% | 13.74% | 6.54% |
| S-d1c86c9df37b5fed | 10.14% | 10.74% | 6.27% |
| S-b06e166f2485558e | 19.09% | 14.94% | 8.79% |
| S-d0fb525b1fcecb5c | 17.97% | 13.66% | 5.31% |
| S-0a68dde9ad49280a | 27.19% | 15.56% | 5.26% |
| S-620a59735d28f0b0 | 18.98% | 14.47% | 7.66% |
| S-82e16205d88fbe35 | 17.62% | 11.80% | 14.67% |
| S-84531c295bbe4a40 | 37.42% | 27.13% | 7.80% |
| new/S-58d75c10e5163b87 | 19.05% | 12.65% | 13.76% |
| new/S-747c4fcf75971c48 | 24.55% | 14.64% | 5.80% |
| new/S-d2b5eb46de2e0a01 | 16.01% | 11.49% | 4.28% |
| new/S-def1d34460b5d530 | 17.98% | 11.23% | 7.83% |
| new/S-f026472f0572933f | 14.90% | 9.92% | 8.65% |
| repair/S-09ddf99a74e6cef4 | 17.89% | 13.96% | 9.36% |
| repair/S-142b114d7d01f2a1 | 16.64% | 10.95% | 8.81% |
| repair/S-a68466a8b3676042 | 14.15% | 10.38% | 11.47% |
| repair/S-aa6ad846d04ce34a | 17.83% | 10.95% | 11.77% |

S两类新reserve沿原非负数值T LP由paired LOSO残差校准，没有手工抬高。训练留出valid／enable逐路径保护漏点均0；guard excess原始median／P95分别为281.47／386.31ps、155.40／327.63ps，明显保守。input_valid与external_valid参数／reserve继承，单列保留旧漏点。精度失败不因保护覆盖而改判。

## 冻结后的已消费回归

数值参数／特征先冻结，消费者／本地二进制和评价实现再冻结，随后评价一次v6相同行。没有用结果修改模型、支持或reserve。v7与v6的S回归覆盖集合逐点相同：因素6/6、旧银行12/15；没有新增／丢失覆盖，下面可以直接比较。

| S回归 | v6 median / P95 | v7 median / P95 |
| --- | --- | --- |
| valid因素银行max | 24.54% / 27.72% | 23.61% / 24.82% |
| valid旧银行max，12/15 | 17.58% / 24.20% | 17.65% / 24.30% |
| enable因素银行max | 6.24% / 7.50% | 6.86% / 7.89% |
| enable旧银行max，12/15 | 6.56% / 12.30% | 7.72% / 13.66% |

valid因素回归略降仍失败，旧银行略退；enable两组也略退，不能把训练LOSO通过当作旧域全面改善。因素四类逐路径保护漏点valid／enable／input_valid／external_valid为0／0／0／1，旧external_valid另有银行max漏点；旧数据只有聚合标签，逐路径漏点保持null。

Add排除1个交换等价train源后32点／12源面积9.11%／19.40%；17+9为22.45%、11+7为15.59%、旧47+63接消费者16.90%仍失败。Mux旧两源17.49%／26.56%，96位源27.56%；另两已消费源11.44%／12.05%。G48已消费点面积2.79%／16.87%、时延4.63%／14.22%，97位源13.51%、48位稀疏源16.35%、56位面积32.93%及train64位面积19.33%保持。以上均非v7新增改进；逐源／origin／非train等价及source-duty报告完整保存。

## 软件检查、费用与回放

355条训练／1700ps数值时钟请求，加116条回归请求，共471条特征和471条真实价格请求，Python／C++一致；468条提供诊断价格，3条旧S支持拒绝。22项跨语言合同／资格拒绝（原21项＋冻结后深度见证1项）通过；另CLI缺上下文请求正常报错，无空指针崩溃。深度见证的其他全部支持坐标仍在范围内，单独因state depth拒绝；该纯软件负例不改变冻结模型或域。新6项合同测试与前驱15项测试通过。推理禁用文件读取与子进程的回放通过；显式native回放只运行指定的软件测试程序。

继承v6的312条严格路径、1457个组合弧和312个删除真实Liberty弧负例，核对原始摘要并重新验证；没有重新跑物理。保留OpenROAD源码审计原文、匹配身份与原职责。一次软件核对在评价文件写完前启动而缺文件，保留首轮日志，待同一次评价完成后核对通过；没有重做评价或物理。初版深度见证的另一路径类负载越界，完整坐标检查拒绝该见证；后继选择全部其他坐标相容的训练结构，参数／支持不变，原失败与证据打包缺前置收据的停止日志均保留。

本轮synth／grt／final／support均0新增，0物理失败／重跑，Ledger pending=0。累计synth3532／grt3501／final16／support22462，叶wall363662.5637572911s／CPU741968.15s，policy v11／budget v5不变。680个源码身份、单文件均≤10MiB；具体包大小与检查见收据。主仓库与RTLzz实现未提交／推送。

```bash
python3 -m experiments.arithmetic_dse.load_pressure_replay_v7
python3 -m experiments.arithmetic_dse.load_pressure_replay_v7 \
  --native build/load-pressure-20261114/arithmetic-load-pressure-test
python3 -m unittest regression.test_load_pressure_v7
```

native程序可在LLVM／MLIR18环境用`cmake -S regression/load_pressure_build -B build/load-pressure-20261114 -G Ninja -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm -DMLIR_DIR=/usr/lib/llvm-18/lib/cmake/mlir`配置，再构建`arithmetic-load-pressure-test`。同参数消费者与完整S上游语义检查都来自归档源码；不包含价格数据库或在线后端调用。

`summary.json`汇集结果；`protocol`／`freeze`／`execution-freeze`保存顺序与依赖；`context-crossfit`／`train-post-selection-audit`保存基础函数、隔离、支持拒绝及保护；`train-report`／`train-predictions`保存全部66项及逐源预测；`evaluation--*`保存已消费标签职责和原始失败；`source-and-tools`保存源码与临时工具原文；`settlement.json`保存0新增物理结算。压缩JSON可用gzip读取。

后继仍需处理valid服务／native分支主导变化及局部负载可预测性；不能用单个enable压力标量替代全部负载预算。Add／Mux旧域、G稀疏边界、宽深实际算术S／shared、相关根与多消费者、W6独立和完整阶段联合仍待。正式W7新D及W8九例ABCD继续依资格推进。
