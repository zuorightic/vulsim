# W3／W4／W5：显式reset语义与逻辑切面共享函数 v9

本包补齐S Query对逐位reset及相容invert的表达，接通Python／C++严格校验和共享函数消费，并完成一次预登记的有限train选择及冻结回归。**接口丢信息的问题已修正；当前数值描述仍不能解释关键物理差异，S仍不合格，W3—W5没有整体关闭。** 公共D未切换，实际算术S／shared及完整阶段资格仍待W6。

模型／runtime为`W345-semantic-reset-functions-v9`，SHA256 `d22f6ece4e340002c2de819eff9deb432b0d8bfc10c3567dd6333e89ae64fa41`；特征为`semantic-reset-cone-features-v9`。原始根为`/home/zyrv/vulsim-artifacts/W345-semantic-reset-20261114-v9`。前驱[v8证据](../common_semantic_fanout_v8/README.md)及其freeze保持不变。本轮0新EDA、0新验证源；v8的6个机制点现在明确作为train，所有旧验证只作已消费回归，20个独立算子源继续锁定。

## S语义接口及适用边界

`state_structure`在旧投影外增加`reset_semantics`，版本为`retained-affine-state-semantics-v1`：逐输入word的reset位列表，逐保留word的reset／invert位列表、出生／终止级和external标记。发射前逐bit验证一或两个不同根的XOR及invert与保留reset一致；输入reset计数、级word尺寸／reset计数、外部宽度／生命周期必须与旧投影完全相符。未知版本、缺语义、布尔伪装整数、位宽／生命周期不符和不一致reset均拒绝，不按popcount猜掩码，也不自动给旧缺字段Query升级。

这是当前**显式仿射保留银行适配器**的语义合同，不是任意实际算术状态的通用reset证明。实际算术状态及shared没有由这次接口修复取得物理资格。数值价格只消费可计算的负载加权reset比例、逐word reset／invert转换率、相反极性输入对与共享比例、来源／capture转换及native／数值T交互；原始掩码、源ID和精确T身份不作为价格路由。R／H标签与RTL发射器不变：寄存器`R=d+H=T−slack`，端口H已扣0.2T，故`R=0.8T−slack`。

W3／W5另从live逻辑Boolean图计算位列依赖跨度、最大切面跨边数、局部门比例及G串联／融合切面差；排除常量、死节点和全局cin伪列。这些是逻辑图代理，不是物理坐标、实际电容或缓冲树预测。所有位宽共享同一组参数，T保持数值输入。

## 训练职责与有限选择

沿用v8算子／G训练：Add53点、Mux15点、G81点。S合并v8六个机制实现后为19银行／63实现／378控制路径，enable／valid各126，input／external各63。两个新增银行分别与其父源、父源既有reset pair合为同一outer fold，仍为13 fold；整组所有T共同留出，不把机制对照充作独立验证。

单向计算顺序为语义结构→共享enable函数→预计压力／松弛代理→valid函数。上游算法固定linear／alpha1／joint_bank_path，旧31特征加4个reset数值描述；13个outer fold及最终all-train共14次固定拟合。每fold先排除整组，再拟合enable并生成下游训练／留出特征。最终上下文必须与实际enable价格函数完全相同。756条train／LOSO特征、训练行摘要、排除来源及最终函数身份重新核对，没有S／G循环或留出标签进入上游。

登记69项有限比较：Add6、Mux3、G面积6／时延6，valid24、input12、external12；14次固定上游拟合另计。valid比较2形式×2link×2目标×3alpha，其余两类各12项。全部候选／失败和逐点预测归档，没有根据冻结回归挑参数或调支持。train支持沿原distinct-geometry规则重推，k=2、radius factor=1.05，旧坐标加3项reset描述，不用标签拓域。训练63/63实现接受，但outer-fold完整实现仅33/63接受，enable／valid各84/126路径、input36/63、external33/63；精度仍按全部训练源照报，拒绝明细保留。

## 训练结果

下表为源等权median／P95；LOSO参与选择，只是训练诊断。S银行取实际消费者所用的各路径预测最大值，raw路径尾部另列。

| 项目 | 入选形式 / alpha | LOSO median / P95 |
| --- | --- | --- |
| Add面积 | cone_cut / 1 | 8.44% / 12.64% |
| Mux时延 | legal_load_T / 10 | 14.62% / 19.33% |
| G面积 | ks_geometry / 0.1 | 3.76% / 13.98% |
| G时延 | carry_topology_context / 1 | 4.56% / 15.81% |

Add入选cone_cut／alpha1；Mux与G的形式及数值参数与v8相同，新增G切面形式没有胜出。G的train64位面积19.33%及两个时延源20.62%／17.07%失败保持，不以总体合格代替逐源结果。

| S类别 | 入选规则 | 银行max LOSO | raw路径 LOSO |
| --- | --- | --- | --- |
| native_enable | 固定上游算法，linear / alpha1 | 8.57% / 13.90% | 8.21% / 21.95% |
| native_valid | polarity_runs / positive_log_linear / path / alpha1 | 18.23% / 28.43% | 9.63% / 38.36% |
| input_valid | polarity_load / positive_log_linear / path / alpha10 | 11.66% / 31.76% | 12.42% / 35.34% |
| external_valid | polarity_load / linear / path / alpha1 | 4.92% / 9.30% | 4.19% / 13.90% |

valid银行最大单源35.62%、raw路径最大88.13%；逐路径先源聚合13.16%／17.89%，服务8.41%／29.37%、native16.06%／24.21%，全零4银行15.02%／25.99%、混合15银行12.79%／15.23%，不能替代银行及raw尾部。input的源聚合通过，但raw P95仍35.34%。v8为17银行而v9为19银行，且两组fold合并，不能直接把两版train指标当同样本改善。

逐源S成组LOSO（各源跨T聚合）：

| 源 | valid银行max | valid逐路径 | enable银行max |
| --- | ---: | ---: | ---: |
| S-ab497c57b8a9bd6d | 24.20% | 13.16% | 5.44% |
| S-d1c86c9df37b5fed | 9.41% | 8.81% | 8.61% |
| S-b06e166f2485558e | 18.23% | 13.24% | 8.11% |
| S-d0fb525b1fcecb5c | 19.23% | 13.54% | 7.46% |
| S-aac8767d3e7162b7 | 11.72% | 12.35% | 4.70% |
| S-0a68dde9ad49280a | 27.63% | 16.81% | 5.39% |
| S-620a59735d28f0b0 | 20.20% | 13.75% | 7.81% |
| S-f3640dcc5b463a0e | 16.05% | 12.63% | 9.97% |
| S-82e16205d88fbe35 | 21.21% | 12.79% | 14.30% |
| S-84531c295bbe4a40 | 35.62% | 27.61% | 8.94% |
| new/S-58d75c10e5163b87 | 19.54% | 14.03% | 13.85% |
| new/S-747c4fcf75971c48 | 24.38% | 15.73% | 6.67% |
| new/S-d2b5eb46de2e0a01 | 15.73% | 10.29% | 2.69% |
| new/S-def1d34460b5d530 | 16.96% | 15.01% | 8.57% |
| new/S-f026472f0572933f | 16.06% | 13.59% | 11.74% |
| repair/S-09ddf99a74e6cef4 | 18.26% | 12.53% | 8.60% |
| repair/S-142b114d7d01f2a1 | 17.52% | 12.30% | 8.43% |
| repair/S-a68466a8b3676042 | 13.69% | 11.05% | 12.68% |
| repair/S-aa6ad846d04ce34a | 13.58% | 8.16% | 11.67% |

reserve仍按原非负数值T LP校准，未手工抬高。所有类LOSO逐路径漏点0，但excess仍较大：

| 类别 | 保护漏点 / 路径 | excess median / P95（ps） |
| --- | --- | --- |
| native_enable | 0 / 126 | 229.17 / 388.34 |
| native_valid | 0 / 126 | 282.49 / 390.40 |
| input_valid | 0 / 63 | 39.67 / 64.33 |
| external_valid | 0 / 63 | 22.85 / 35.74 |

## 冻结后的已消费回归

数值参数／特征先冻结，消费者、二进制及评价依赖再冻结，随后一次消费旧回归；没有新盲测。因素银行覆盖仍6/6，但旧银行覆盖从v8的12/15降为9/15：原`new/S-71210069d9a20502`三个T继续因`source_reset_one_fraction`拒绝，`repair/S-412d31fc43b165cb`三个T新增因`reset_capture_transition_fraction`拒绝。没有据回归扩大支持。

以下严格比较共同覆盖的同一组点，不能用v8旧12点17.96%直接对比v9的9点13.32%来声称改善：

| 类别／集合 | 共同点数 | v8 median / P95 | v9 median / P95 |
| --- | ---: | --- | --- |
| 因素银行 native_valid | 6 | 31.43% / 36.06% | 24.63% / 25.38% |
| 因素银行 native_enable | 6 | 6.86% / 7.89% | 7.22% / 8.15% |
| 因素银行 input_valid | 6 | 10.38% / 14.21% | 9.38% / 11.58% |
| 因素银行 external_valid | 6 | 7.99% / 9.73% | 10.28% / 13.12% |
| 旧银行共同覆盖 native_valid | 9 | 11.33% / 24.02% | 13.32% / 23.15% |
| 旧银行共同覆盖 native_enable | 9 | 7.49% / 7.90% | 7.49% / 7.92% |
| 旧银行共同覆盖 input_valid | 9 | 10.98% / 20.83% | 14.88% / 28.38% |
| 旧银行共同覆盖 external_valid | 9 | 8.55% / 13.10% | 10.59% / 11.92% |

因素valid虽改善至24.63%仍失败；enable及external略退。共同旧9点valid、input median均退化。完整旧15点只作域外原始数值诊断的valid median仍20.55%，不能删除被拒银行后宣称旧域修复。因素四类银行／路径保护漏点均0；旧external银行max仍1个漏点，旧聚合标签的逐路径保护漏点为null，不能记0。

Add非train等价32点面积8.35%／24.08%→8.65%／23.70%，median稍退、尾部稍降；17+9单源29.52%→30.06%退化，47+63带消费者19.63%→18.50%改善仍失败，11+7为12.54%→11.90%。Add delay继承不变。Mux96位时延27.56%、旧两源17.49%／26.56%保持。G48稀疏时延16.35%、G56面积32.93%、G97时延13.51%均同v8；没有负G修正或逐源价格路由。

## 接口能区分对照，数值模型仍不能解释差值

v8两组完整Query碰撞在v9不再相同，相关入选数值特征也能不同。但这只解决表达，尚未解决精度：

| train银行对照 | T | 实测银行R差（ps） | v9预测银行R差（ps） |
| --- | ---: | ---: | ---: |
| biased20×32，native_valid | 500 | +178.288639 | +1.522176 |
| biased20×32，input_valid | 1500 | +37.389038 | −0.943609 |
| uniform16×64，native_valid | 1500 | −37.271485 | −6.629080 |

第二项连方向都未解释。不能称S已修复，也不能按源身份或把实测差值加入预测。v8的25.41%局部共同预测下界保留其旧接口职责；新接口消除相同Query前提后，该下界不约束v9，但当前误差仍由实际结果直接显示。v8下界本来也不证明全局源median不可能。逐类、各T、实际与预测差值完整保存在train-post-selection-audit。

## 实现、核验与可复现证据

新通用实现为[Python特征](../../../arithmetic_dse/semantic_reset_features_v9.py)、[模型消费](../../../arithmetic_dse/semantic_reset_model_v9.py)、[便携回放](../../../arithmetic_dse/semantic_reset_replay_v9.py)及[RTLzz C++](../../../../rtlzz/src/backend/arithmetic_semantic_reset.cpp)。总计477次特征核对／477次真实价格请求Python与C++一致，其中471返回诊断价格，6旧S请求按支持域拒绝。32项跨语言合同／资格拒绝包含缺失／损坏语义；缺上下文feature CLI正常报错。新增8项与前驱27项共35测试通过。前驱v8回放、新Python及显式native回放均通过；数值推理期间禁止文件读取和子进程。

v8六实现中的36个grt控制标签逐一绑定原manifest和实际路径R；继承156严格路径与156个删除真实Liberty弧负例，重新核验。v8源身份和物理收据按原gz字节摘要继承，原v6／v7／v8证据不改。699份仓库源码身份及临时工具文本归档，每个文件≤10MiB，可脱离原artifact绝对路径做软件回放。

```bash
python3 -m experiments.arithmetic_dse.semantic_reset_replay_v9
cmake -S regression/semantic_reset_build -B build/semantic-reset-20261114 -G Ninja \
  -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm -DMLIR_DIR=/usr/lib/llvm-18/lib/cmake/mlir
cmake --build build/semantic-reset-20261114 --target arithmetic-semantic-reset-test -j 4
python3 -m experiments.arithmetic_dse.semantic_reset_replay_v9 \
  --native build/semantic-reset-20261114/arithmetic-semantic-reset-test
python3 -m unittest regression.test_semantic_reset_v9
```

以上只做软件核验，不调用物理工具。完整35项测试另含前驱semantic_fanout、load_pressure、rebuffer_context、branch_load的回归，准确日志归档。登记脚本准备阶段曾错误假定external函数存在`functions['R']`，实际为cell／wire／H分量；登记前改为合并各分量特征。另一次fit早于协议文件生成而失败，保留`fit-before-registration-first-attempt.log`；协议生成后只完成一次数值拟合。未据回归追加试验或重选模型。

`summary.json`汇集结果；train-report／predictions保留69项试验；train-post-selection-audit保留上下文、支持、逐路径保护和对照；evaluation--report／post-regression-audit保存逐源回归、共同覆盖及丢失源；source-duty-audit保存职责；freeze／execution-freeze保存原数值及执行身份；source-and-tools保存源代码及临时工具；execution-logs保留失败及核验日志。最终[checks.json](checks.json)、[Python回放](replay.json)与[native回放](native-replay.json)为交付核验收据，不反馈数值拟合。

## 费用与后继

本轮synth／grt／final／support均0新增，0物理失败／自动重跑；v8六点费用不重复计收。Ledger仍synth3538／grt3507／final16／support22486，叶wall364379.1543315831s／CPU743575.33s、pending=0。policy v11／budget v5、全局4物理任务／每任务4线程8192MiB保持。未提交／推送。

下一职责是利用已保留的逻辑和匹配OpenROAD重缓冲／预算源码证据，解释reset／相容invert如何改变各控制分支的可用共享与电气负载，再登记可在发射前计算的描述和有限训练；不能继续只增总体比例后宣称物理机制已解释。Add／Mux旧域、G稀疏／组合边界及宽深实际算术S／shared仍待；W6须在冻结依赖下完成独立及完整阶段资格，W7／W8正式D与九例ABCD继续按该资格推进。
