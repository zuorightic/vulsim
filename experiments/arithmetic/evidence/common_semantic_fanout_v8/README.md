# W3／W4／W5：语义扇出共享函数与S接口对照 v8

本包完成一次有限train拟合、冻结后的已消费回归、Python／C++消费，以及单独登记的6点S机制实验。**S仍不合格，W3—W5没有整体关闭，公共D没有切换。** 本轮最直接的新发现是：当前S Query省略的reset位分布及相容反相，能使相同Query对应不同的物理R；其中一个valid对照点的共同预测最小最大相对误差为25.41%。

候选／runtime均为 `W345-semantic-fanout-functions-v8`，SHA256 `daec32c0685c41a67fb5435cc29a67e0dd329666d71f1e1e3045cebbf91dad13`。原始数据及临时工具：`/home/zyrv/vulsim-artifacts/W345-semantic-fanout-20261114-v8`。前驱[v7证据](../common_load_pressure_v7/README.md)保持原身份。数值拟合阶段0新EDA；另立机制批次新增6 synth、6 grt、24 support，不能把整轮记为0新EDA。新源均为未来后继的train，未进入已冻结v8。旧验证全部只作已消费回归，0新验证源，20个独立算子源继续锁定。

## 共同函数与训练隔离

从发射前逻辑连接计算负载总量、二阶集中度、有效驱动数量、超过4个逻辑用途的工作量和共享比例。若逻辑负载为l，则集中度为`log2(1+Σl²/Σl)`，有效驱动代理为`log2(1+(Σl)²/Σl²)`；布尔图只计live门输入边和被观察输出，排除常量与死节点，分根和内部驱动。G分别计算串联／融合图及其差，S另计算根负载和重复输入对比例，再与native、reset和数值T交互。这些是逻辑工作代理，不是实际电气负载或修复缓冲数。

保留v7单向依赖：语义状态→共享enable函数→预计压力／松弛代理→valid函数。v7的14份基础上下文及训练摘要逐项复用，本轮没有重拟合enable。13个outer fold仍排除整对reset源及全部T；228条上下文特征和训练摘要重新核对。最终enable价格与上下文函数必须相同；没有S／G循环、实测slack／电容／mapped树、源身份或精确T编号取价。同算子各位宽共享系数，T保持数值输入。

预登记66项有限比较：Add9、Mux6、G面积9／时延6、S36。Add／G按整体、小工作量／稀疏和最差语义源的损失minimax选择；Mux沿原目标；S比较2个link×2个目标×3个alpha×3种形式。完整候选、落选结果和原始预测保存在train-report／train-predictions。S支持域继承v7，训练57/57实现接受，但跨银行留出的完整实现仅33/57；valid／enable78/114路径、input39/57、external33/57，不能授予未知结构资格。

## 训练结果与冻结回归

下表误差为源等权median／P95；LOSO参与选择，仅为训练诊断。raw路径尾部另列。

| 项目 | v8 median / P95 | 结论 |
| --- | --- | --- |
| Add面积18源／53点LOSO | 8.28% / 13.48% | internal_fanout、alpha1入选；最大单源14.72% |
| Mux时延5源LOSO | 14.62% / 19.33% | legal_load_T、alpha10，数值参数同v7 |
| G面积27源LOSO | 3.76% / 13.98% | ks_geometry、alpha0.1，同v7 |
| G时延27源LOSO | 4.56% / 15.81% | carry_topology_context、alpha1，同v7 |
| S enable银行max | 7.83% / 13.95% | 完整继承v7，无新拟合 |
| S valid银行max | 17.94% / 23.13% | root_pair_reset、linear、path、alpha0.1，median失败 |
| S valid逐路径先源聚合 | 12.06% / 17.33% | 不能替代银行或raw尾部 |
| S valid原始114路径 | 8.72% / 36.56% | P95失败；最大65.55% |
| S valid服务分支 | 7.64% / 25.87% | 分支单列 |
| S valid native分支 | 16.48% / 21.62% | median失败 |
| S valid全零4银行逐路径源聚合 | 15.19% / 18.18% | median失败 |
| S valid混合13银行逐路径源聚合 | 12.05% / 15.11% | 不转授全域 |

逐源S成对LOSO（每源跨T聚合）：

| 源 | valid银行max | valid path | enable银行max |
| --- | ---: | ---: | ---: |
| S-ab497c57b8a9bd6d | 6.93% | 8.20% | 6.54% |
| S-d1c86c9df37b5fed | 11.42% | 10.83% | 6.27% |
| S-b06e166f2485558e | 15.07% | 13.31% | 8.79% |
| S-d0fb525b1fcecb5c | 17.94% | 12.54% | 5.31% |
| S-0a68dde9ad49280a | 25.42% | 17.06% | 5.26% |
| S-620a59735d28f0b0 | 20.49% | 14.99% | 7.66% |
| S-82e16205d88fbe35 | 17.47% | 11.86% | 14.67% |
| S-84531c295bbe4a40 | 19.44% | 18.38% | 7.80% |
| new/S-58d75c10e5163b87 | 21.39% | 13.38% | 13.76% |
| new/S-747c4fcf75971c48 | 18.68% | 14.75% | 5.80% |
| new/S-d2b5eb46de2e0a01 | 13.97% | 10.34% | 4.28% |
| new/S-def1d34460b5d530 | 19.02% | 12.05% | 7.83% |
| new/S-f026472f0572933f | 14.79% | 10.31% | 8.65% |
| repair/S-09ddf99a74e6cef4 | 16.48% | 12.06% | 9.36% |
| repair/S-142b114d7d01f2a1 | 22.55% | 15.28% | 8.81% |
| repair/S-a68466a8b3676042 | 14.43% | 9.45% | 11.47% |
| repair/S-aa6ad846d04ce34a | 18.70% | 11.44% | 11.77% |

valid reserve仍用原非负数值T LP根据train残差校准，paired LOSO路径漏点0，excess median／P95为272.94／367.16ps；enable为155.40／327.63ps，与v7相同。没有手工抬reserve；精度失败和保守性同时保留。input／external函数及reserve也同v7。

参数／特征先冻结，消费二进制与评价实现再冻结，随后一次评价原已消费数据，没有据回归换模、改域或调reserve。S同行覆盖集合相同：因素6/6，旧12/15，无新增或丢失覆盖。

| 冻结后回归 | v7 median / P95 | v8 median / P95 |
| --- | --- | --- |
| valid因素银行max | 23.61% / 24.82% | 31.43% / 36.06% |
| valid旧银行max，12/15 | 17.65% / 24.30% | 17.96% / 25.30% |
| Add非train等价32点面积 | 9.11% / 19.40% | 8.35% / 24.08% |
| Add 17+9单源面积 | 22.45% | 29.52% |
| Add 11+7单源面积 | 15.59% | 12.54% |
| Add 47+63带消费者单源面积 | 16.90% | 19.63% |

valid因素新增1个银行／路径保护漏点，不能因训练内保护通过而忽略；因素external_valid另有1个路径漏点，旧external_valid另有1个银行max漏点。旧聚合标签没有逐路径数据，漏点保持null。enable因素6.86%／7.89%、旧7.72%／13.66%，input／external不变。

Mux旧两源仍17.49%／26.56%，96位单源27.56%；G48已消费点面积2.79%／16.87%、时延4.63%／14.22%，G97时延13.51%、G48稀疏16.35%、G56面积32.93%、trainG64面积19.33%保持。新扇出形式未改变Mux／G参数，不能称这部分已有修复。各源、origin、train等价及支持拒绝完整保留。

## S完整Query相同的有限物理对照

另立训练机制协议，选择已有biased 20×32银行S-d0fb525b1fcecb5c和uniform 16×64银行S-620a59735d28f0b0，生成S-aac8767d3e7162b7与S-f3640dcc5b463a0e。旋转根及各word的reset掩码，逐根／逐word保留popcount，重算一致invert；连接、stage word、服务语义、T、发射器均保持。旧／新语义signature不同，完整当前state_structure、所有v8特征和预测在500／1500／3000ps逐项相同。

5632次状态比较和7项非法源测试先通过；去重只读源身份和合同，未读独立标签。准确6点admission、两个1500ps先导及容量闸门后采余下4点。6点全部完成，0失败／重跑，真实综合／grt CEC均通过。新源不进入v8的17银行训练，未来拟合必须与其父源及既有reset pair共用outer fold。

标签保持`R=d+H`：寄存器为`T−slack`；端口H已扣除0.2T，故R为`0.8T−slack`。逐点保存delay、H、R及其变化；13种实际路径×2物理阶段×6实现，共156个新旧路径比较，其中36个grt控制标签、24个银行max比较。

| biased银行对照 | T | 旧R→新R（ps） | 共同预测的点上最小最大相对误差 |
| --- | ---: | ---: | ---: |
| native valid，source_valid_1 | 500 | 261.67 → 439.96 | 25.41% |
| input_valid | 1500 | 96.70 → 134.09 | 16.20% |
| native enable，source_enable_1 | 3000 | 561.60 → 723.12 | 12.57% |

若两标签为a≤b，任何共同预测p的最小max-APE为`(b−a)/(b+a)`，最优p为`2ab/(a+b)`。所以前两测点不能同时达到15%。但它们**不证明全局源聚合median门槛不可能通过**。允许每个T独立选择预测时，该pair等权平均APE的松弛下界为各T的`(1−a/b)/2`均值；biased valid银行为10.01%，也不能偷换为15%全局不可能。uniform对照的valid最差路径下界7.12%、银行4.42%，如实保留差异较小的结果。

这是reset位分布和相容invert的联合train对照，不能称reset位置单因素因果或某条OpenROAD命令的单独因果。它为后继补充语义投影提供依据，禁止按新源hash查价或将实测差值塞回线上。旧v6匹配OpenROAD重缓冲／时序预算源码审计以原摘要继承，没有修改OpenROAD。

## 消费、回放、费用与下一职责

471条特征、471次价格请求Python／C++一致，468次返回诊断价格，3次旧S支持拒绝；22项合同／资格拒绝和缺上下文CLI安全报错通过。新增6项语义／泄漏合同测试与前驱21项测试共27项通过。Python和显式native便携回放通过，数值推理期间禁止文件读取与子进程。

新增156严格路径／744组合弧及156个删除真实Liberty弧负例，继承v6的312路径／1457弧／312负例并绑定v6原始证据身份。新路径绑定各manifest和raw points摘要；软件回放不需ODB或物理工具。v7的14份上下文原文完全一致。6对旧新物理上下文逐项核对：工具、Liberty、流程、mapping_context、SDC、实际T、线程和内存一致，补核收据单列。一次拒绝核对早于前置文件生成而缺文件；另一次补核初版误以为metrics含ABC字段，改从manifest实际mapping_context及阶段profile核对后通过，首轮日志均保留。没有重选模型或重做物理。

本轮6 synth＋6 grt＋24 support、0 final，0物理失败／自动重跑。叶wall／CPU增量716.5905742919895／1607.18s，累计Ledger synth3538／grt3507／final16／support22486、wall364379.1543315831s／CPU743575.33s，pending=0。policy v11／budget v5及最多4物理任务、每任务4线程／8192MiB保持。691源码身份，单档≤10MiB；总大小与检查见checks收据。主仓库与RTLzz未提交／推送。

```bash
python3 -m experiments.arithmetic_dse.semantic_fanout_replay_v8
python3 -m experiments.arithmetic_dse.semantic_fanout_replay_v8 \
  --native build/semantic-fanout-20261114/arithmetic-semantic-fanout-test
python3 -m unittest regression.test_semantic_fanout_v8
```

native可用`cmake -S regression/semantic_fanout_build -B build/semantic-fanout-20261114 -G Ninja -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm -DMLIR_DIR=/usr/lib/llvm-18/lib/cmake/mlir`配置，然后构建`arithmetic-semantic-fanout-test`。上述命令只做软件核对。

summary汇集结果；train-report／predictions保存66项与逐源结果；evaluation--*保存已消费回归及漏点；S-alias--*保存准确admission、软件、父源关系、完整Query同一性及路径下界；physical-receipts、physical-context-audit和settlement保存物理身份、流程相容性与费用；source-and-tools归档实现和临时工具。delivery-freeze只补记测量后证据／回放工具，不修改原数值或执行freeze。

后继先修S语义投影对reset分布及极性的表达，再登记通用数值描述、成对训练和新验证职责；继续保留本轮31.43%回归失败。Add／Mux旧域、G稀疏边界、宽深实际算术S／shared、相关根／多消费者及W6独立／联合资格仍待。正式W7新D、W8九例ABCD继续按冻结资格推进。
