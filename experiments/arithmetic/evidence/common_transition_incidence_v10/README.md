# W3／W4／W5逻辑路径负载、reset／极性联合关联与hold机制 v10

本包完成`W345-transition-incidence-functions-v10`的45项有限train比较、数值及执行冻结、Python／C++消费和一次已消费回归。G48稀疏源与input_valid得到局部改善，native_valid仍失败且回归退化；Add／Mux及G面积未变。另从匹配OpenROAD源码和保存train路径中查到hold修复对input_valid setup路径的影响，作为冻结后的解释证据保留。**W3—W5未整体完成，本包未发布给公共D；实际算术S／shared、W6完整阶段和独立资格仍待。**

产物根：`/home/zyrv/vulsim-artifacts/W345-transition-incidence-20261114-v10`。前驱为[v9](../common_semantic_reset_v9/README.md)，本次不改前驱源码、模型、物理产物或证据。新模型与runtime SHA256均为`a1466f0272b55bd20358ea9e3beb84844db8fe8fefe4152e0478224d8f13243d`；协议SHA256为`913caf00536cce547997f22a954d0a4df153c74e720cd96f9804aa605d2a1d31`。

## 可在发射前计算的特征

W3／W5沿live Boolean图计算路径负载工作量：每个逻辑门的代价为`1+log2(1+logical_uses)`，沿输入路径累计最大值；观察输出计入uses，常量和死节点排除。导出路径工作量、工作量／深度、内部峰值uses、共享比例，G同时保留fused与serial及差值，并与数值T压力交互。这是逻辑图代理，不是实际物理电容、坐标、STA或缓冲树。

W4计算输入根reset、保留结果reset和相容invert的联合关联：每根两种逻辑相位的集中／分裂、根内偏斜、结果reset分裂、reset交叉比例、degree平方加权不平衡／one-reset比例及峰值degree。数值输出去掉根身份和原始掩码，满足根重命名、操作数交换不变性。这里的逻辑相位不等于物理rise／fall波形或电容。

继承v9显式仿射银行语义适配器和严格校验；不把它扩称任意实际算术状态。所有位宽共享参数，T为数值输入，不按源、案例、精确形状或精确T路由。线上只用Query和冻结参数，不读文件、不启动子进程、不调用后端。S标签与RTL发射保持：寄存器`R=d+H=T−slack`；端口H已扣0.2T，因此`R=0.8T−slack`。没有负G补偿或手工抬reserve。

## 训练、上下文及支持职责

复用v9全部train：Add53点／18源、Mux15点／5源、G81点／27源，S19银行／63实现／378路径。S仍为13个完整父源／reset／contrast outer fold，每组所有T共同留出。v8六个机制实现已在v9纳入train，本轮没有新增训练源或标签；它们不是新验证。

有限矩阵为Add6＋Mux3＋G面积6＋G时延6＋valid12＋input6＋external6＝45项。valid比较两形式×两目标×三alpha，input／external各两形式×三alpha；各类link固定继承v9。按原源等权minimax损失选定。14份enable上下文、训练行身份及最终enable价格函数完全继承，**上游重拟合0次**；756条实际train／LOSO特征和lineage重新核对，无留出标签混入上游或S／G循环。

S支持域逐字继承v9，没有按回归扩域。最终train63/63实现可诊断，outer-fold完整实现仅33/63接受；这限制未知几何资格。因素回归6/6、旧回归9/15覆盖与v9完全相同。`new/S-71210069d9a20502`三个T仍因`source_reset_one_fraction`拒绝，`repair/S-412d31fc43b165cb`三个T仍因`reset_capture_transition_fraction`拒绝。域外原始预测不混作合格覆盖。

数值先冻结，随后消费者／二进制及评价依赖冻结，再运行一次旧回归；没有根据回归更改特征、支持、参数或保护。20个其余算子独立源继续锁定，本次无fresh validation或W6独立测试。

## train选择结果

以下为源等权median／P95，LOSO用于选择，仅作训练诊断。逐源失败不被汇总豁免。

| 项目 | 入选形式／alpha | LOSO median / P95 |
| --- | --- | --- |
| Add面积 | cone_cut / 1 | 8.44% / 12.64% |
| Mux时延 | legal_load_T / 10 | 14.62% / 19.33% |
| G面积 | ks_geometry / 0.1 | 3.76% / 13.98% |
| G时延 | path_load / 10 | 6.47% / 15.06% |

Add／Mux和G面积的形式及数值参数与v9完全相同。G时延入选路径负载形式；同train的v9为4.56%／15.81%、最大单源20.62%，v10为6.47%／15.06%、最大18.52%。median变差、最差源改善，不能称全面改善；train64位G面积19.33%仍失败。

| S类别 | 入选形式 | 银行max LOSO | raw路径 LOSO |
| --- | --- | --- | --- |
| native_enable | 固定v9函数 | 8.57% / 13.90% | 8.21% / 21.95% |
| native_valid | signed_incidence | 18.50% / 26.09% | 9.73% / 38.71% |
| input_valid | signed_incidence | 12.77% / 23.74% | 11.45% / 31.13% |
| external_valid | v9_selected | 4.92% / 9.30% | 4.19% / 13.90% |

valid使用positive_log_linear／path／alpha1，input使用positive_log_linear／path／alpha0.1。enable与external价格不变。valid银行median18.50%、raw路径P9538.71%仍失败；v9同行18.23%／raw P9538.36%，均略退。input银行median11.66%→12.77%略退，但P9531.76%→23.74%、raw P9535.34%→31.13%改善。valid服务8.94%／26.99%、native17.77%／24.28%，全零4银行14.05%／23.15%、混合15银行12.95%／17.52%按逐路径源聚合另报，不能替代银行及raw尾部。valid单源银行最大30.74%、逐路径源最大24.46%。

| train银行源 | valid银行max | valid逐路径源聚合 | input银行 |
| --- | ---: | ---: | ---: |
| S-ab497c57b8a9bd6d | 21.06% | 16.15% | 23.05% |
| S-d1c86c9df37b5fed | 7.52% | 7.98% | 5.30% |
| S-b06e166f2485558e | 14.78% | 12.37% | 7.87% |
| S-d0fb525b1fcecb5c | 20.44% | 14.69% | 12.96% |
| S-aac8767d3e7162b7 | 12.28% | 13.94% | 23.19% |
| S-0a68dde9ad49280a | 25.57% | 15.73% | 4.73% |
| S-620a59735d28f0b0 | 18.33% | 12.11% | 4.78% |
| S-f3640dcc5b463a0e | 16.49% | 11.35% | 3.48% |
| S-82e16205d88fbe35 | 19.45% | 12.95% | 11.12% |
| S-84531c295bbe4a40 | 30.74% | 24.46% | 12.77% |
| new/S-58d75c10e5163b87 | 19.79% | 12.12% | 21.87% |
| new/S-747c4fcf75971c48 | 25.29% | 18.83% | 22.50% |
| new/S-d2b5eb46de2e0a01 | 16.21% | 10.83% | 9.20% |
| new/S-def1d34460b5d530 | 19.23% | 14.42% | 10.38% |
| new/S-f026472f0572933f | 17.77% | 14.63% | 18.67% |
| repair/S-09ddf99a74e6cef4 | 18.50% | 11.56% | 12.88% |
| repair/S-142b114d7d01f2a1 | 24.16% | 16.96% | 28.67% |
| repair/S-a68466a8b3676042 | 12.56% | 8.26% | 14.35% |
| repair/S-aa6ad846d04ce34a | 13.27% | 8.73% | 4.99% |

保护仍按原非负数值T LP算法从train残差求解。四类LOSO逐路径均无漏点，但保守量很大，不能用保护覆盖代替点估计精度：

| 类别 | 保护漏点／路径 | excess median / P95（ps） |
| --- | --- | --- |
| native_enable | 0 / 126 | 229.17 / 388.34 |
| native_valid | 0 / 126 | 288.88 / 392.75 |
| input_valid | 0 / 63 | 41.47 / 70.76 |
| external_valid | 0 / 63 | 22.85 / 35.74 |

## 冻结后共同覆盖回归

严格比较与v9相同覆盖集合；全部是已消费回归，不能作为新盲测或用于重选。

| 集合／类别 | 共同点数 | v9 median / P95 | v10 median / P95 |
| --- | ---: | --- | --- |
| 因素银行 native_valid | 6 | 24.63% / 25.38% | 26.10% / 27.27% |
| 因素银行 native_enable | 6 | 7.22% / 8.15% | 7.22% / 8.15% |
| 因素银行 input_valid | 6 | 9.38% / 11.58% | 8.60% / 10.49% |
| 因素银行 external_valid | 6 | 10.28% / 13.12% | 10.28% / 13.12% |
| 旧银行共同覆盖 native_valid | 9 | 13.32% / 23.15% | 16.48% / 21.91% |
| 旧银行共同覆盖 native_enable | 9 | 7.49% / 7.92% | 7.49% / 7.92% |
| 旧银行共同覆盖 input_valid | 9 | 14.88% / 28.38% | 7.93% / 12.74% |
| 旧银行共同覆盖 external_valid | 9 | 10.59% / 11.92% | 10.59% / 11.92% |

input旧共同9点14.88%→7.93%改善；valid13.32%→16.48%退化并越过median门槛，因素valid24.63%→26.10%也变差。enable／external不变。因素四类银行／路径保护漏点均0；旧external银行max仍1个漏点，旧聚合标签的逐路径漏点仍为null，不能记0。支持没有新增或丢失点。

Add非train等价32点面积8.65%／23.70%保持；17+9单源30.06%、带消费者47+63单源18.50%仍失败，11+7为11.90%。Add时延保持。Mux96位27.56%、旧两源17.49%／26.56%保持。本轮新增路径特征未胜出，不强行替换旧参数。

G48点／16源时延由v9的4.63%／14.22%变为6.73%／13.22%，median退化而P95下降；最大源16.35%→14.91%。此前失败的48位稀疏源16.35%→4.26%、97位源13.51%→9.20%改善；另有源3.73%→14.91%、4.37%→12.66%退化，完整逐源列于下表。G面积2.79%／16.87%不变，56位32.93%仍失败。不能凭G时延汇总通过宣布组合边界或完整阶段合格。

| G源 | v9时延 | v10时延 | v10面积（不变） |
| --- | ---: | ---: | ---: |
| G-4e90ee927a434fd8 | 4.37% | 12.66% | 0.77% |
| G-cd354cd6595b08da | 3.73% | 14.91% | 2.37% |
| G-cf14a840d1d21211 | 4.90% | 9.76% | 4.26% |
| G-e97dd14f787f6c14 | 13.51% | 9.20% | 8.86% |
| G-ff37f81ebdd8c2ba | 10.71% | 6.73% | 8.09% |
| new/G-0a845622a239af6b | 10.60% | 7.80% | 32.93% |
| new/G-5239d000d3539a9d | 1.50% | 7.24% | 2.94% |
| new/G-83abf372ab2c1ed6 | 16.35% | 4.26% | 10.76% |
| new/G-ba4d43d007946c4a | 1.62% | 2.92% | 1.23% |
| new/G-fd4aefdadf10451e | 3.47% | 3.25% | 0.77% |
| old/validation-0 | 5.55% | 4.95% | 2.24% |
| old/validation-1 | 2.35% | 6.73% | 2.64% |
| old/validation-2 | 1.30% | 8.42% | 2.94% |
| old/validation-3 | 6.83% | 2.39% | 1.98% |
| repair/G-22633ebe36f00ddd | 5.14% | 4.74% | 11.51% |
| repair/G-db5fbd33d7c30fbf | 2.48% | 2.48% | 0.55% |

## 对照差值与OpenROAD机制

新增联合关联仍不足以解释biased valid：T500实测银行R差+178.288639ps，v9预测+1.522176ps，v10预测−0.160597ps。biased input在T1500实测+37.389038ps，v9预测−0.943609ps，v10预测+11.283035ps，方向改善但幅度仍不足。差值只作train诊断，不按源补价。

匹配OpenROAD源码revision `84e3ff1eb2c36302cef42e4f70a69efe4cfbb126`，二进制SHA `c24e4e3a75e223e51e203440992a0364fb8c83a239162238d0772b87a1193f75`。`mechanism-audit.json.gz`保存Rebuffer／Resizer完整原文、SHA、行号及12条train路径的报告、cell／wire、真实负载master分布和原始身份。Rebuffer按transition传播预算和junction cap／slack只提供建模线索，不证明逻辑相位代理等于真实电气机制。

biased valid T500的grt路径，旧cell／wire为122.78／17.07ps，新为235.56／78.64ps；组合单元3→4个，逐段负载2／2／64／1变为2／2／65／128／1。路径delay增长174.36ps、H增长3.93ps，共构成R差178.29ps。当前线上特征没有预测出该变化。

**冻结后的hold解释审计没有参与本版特征、拟合或选模。** `hold-audit.json.gz`保存匹配`RepairHold.cc`原文及148—217、382—462、615—676、715—760行，覆盖延迟／面积选择、违例循环、min／max slack检查及`insertBufferBeforeLoads(...,"hold")`。两个biased input T1500见证在synth均无hold命名单元，grt分别5／7个，总路径组合单元9／11个。hold命名单元cell增量合计94.027284／134.417388ps；路径全部cell为167.893616／207.750060ps，wire为3.465667／3.694062ps。尽管线上逐段wire均仅一个load，仍出现不同hold延迟链。保存flow日志同时记载旧171违例端点／646 hold buffers及后续9／9，新187／657及后续6／6。

这支持继续研究hold修复与clock／setup预算的相互作用，但不证明所有S残差来自hold，也不把每个实例唯一归因到某次命令。不得将实际hold数量、时序树、slack或实测延迟直接加入在线特征。后继应先从train中的最短逻辑路径、capture共享／hold负担等发射前信息提出有限假设并登记，必要时另立有限train对照。

## 软件核验及便携回放

实现为[Python特征](../../../arithmetic_dse/transition_incidence_features_v10.py)、[模型消费](../../../arithmetic_dse/transition_incidence_model_v10.py)、[便携回放](../../../arithmetic_dse/transition_incidence_replay_v10.py)及[RTLzz C++](../../../../rtlzz/src/backend/arithmetic_transition_incidence.cpp)。477条特征／477次真实价格请求跨语言一致，其中471提供诊断价格、6旧S支持拒绝；另32项跨语言合同／资格拒绝和缺上下文CLI正常报错通过。37项新旧测试与单独6项flow_structure测试均通过，共43项，准确分组和命令见归档日志。

前驱v9 Python回放、本包Python及显式native回放均通过；推理期间禁用文件读取和子进程。继承v8六实现的36个grt训练标签仍绑定原manifest／R，156条原严格路径及156个删除实际Liberty弧负例重验。另给12条本轮机制见证保存独立连线／负载证明：53组合弧、12删弧负例、cell＋wire守恒及master负载分布可脱离ODB重验；这些路径与历史物理实现重叠，不宣称新增12个物理点。证明为post-freeze解释，不改冻结replay及模型。

707份仓库源码身份、前驱身份、原始gz证据、临时工具、匹配OpenROAD源码和失败日志归档，单文件≤10MiB。`source-and-tools.json.gz`中`tools/path_proofs.py`恢复后可带`--root`对本目录复核12路径；只读取压缩证据。初次机制脚本未处理顶层端口无斜杠而失败，修正显式port分支后在执行冻结前完成，原失败日志保留。没有EDA重试、回归重做或冻结后调参。

```bash
python3 -m experiments.arithmetic_dse.transition_incidence_replay_v10
cmake -S regression/transition_incidence_build -B build/transition-incidence-20261114 -G Ninja \
  -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm -DMLIR_DIR=/usr/lib/llvm-18/lib/cmake/mlir
cmake --build build/transition-incidence-20261114 --target arithmetic-transition-incidence-test -j 4
python3 -m experiments.arithmetic_dse.transition_incidence_replay_v10 \
  --native build/transition-incidence-20261114/arithmetic-transition-incidence-test
python3 -m unittest regression.test_transition_incidence_v10
```

`summary.json`汇总结果；45项候选／逐点train预测、上下文及支持／保护、逐源和共同覆盖回归、source-duty、数值及执行freeze、源码／工具／日志分别压缩保存。[checks.json](checks.json)、[Python回放](replay.json)和[native回放](native-replay.json)为交付收据，不反馈训练。

## 费用与剩余工作

本轮0新synth／grt／final／support、0新训练标签／验证源、0物理失败或自动重跑；v8六点不重复收费。累计Ledger仍synth3538／grt3507／final16／support22486，叶wall364379.1543315831s／CPU743575.33s、pending=0。policy v11／budget v5、全局4物理任务／每任务4线程8192MiB不变。没有提交／推送。

下一工作重点为hold／setup竞争的可计算模型，保留本轮valid失败和G局部退化；继续处理Add／Mux旧域及G面积／组合边界。宽深实际算术S／shared和W6独立／完整阶段资格仍须单独完成，正式W7新D、W8九例ABCD按冻结资格推进。
