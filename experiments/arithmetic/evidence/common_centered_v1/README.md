# W3／W4／W5：稳定拟合、实际映射归因与冻结验证

日期：2026-11-14。本包交付共同函数的诊断后继、匹配源码／train检查点归因及12个Add物理点，其中有效新验证9点、交换等价复测3点。**新源验证通过，关键旧子域和S／G仍有失败，未发布公共价格，不能用于正式D选择。** 同一算子跨位宽使用同一组函数参数，T为连续数值输入；没有案例、精确形状或精确T价格路由。

实施及下一边界见[计划§7.102](../../../../mission/lxy-plan-fix.md#W345-centered-mechanism-successor)。完整本机产物和临时工具在`/home/zyrv/vulsim-artifacts/W345-model-repair-20261114-v1`。本包约6.2MB，所有单文件小于10MiB；包括协议、候选、全部train／留一预测、冻结、回归、原失败、源码和工具文本、12点RTL／标签／合同／CEC收据及两批Ledger叶条目，不包含ODB或工具二进制。默认回放不依赖上述绝对路径。

## 规则、实现和数据职责

`protocol.json.gz`在候选试验前固定恒定列容差、有限特征形式、alpha=[0.1,1,10]及整语义源LOSO选择。Add使用53点／18源；Mux只取已有数据的train；G使用81点／27源，零压缩6源单列；S使用13银行／45实现／270控制路径。来源和角色保持。同源变体按完整prospective语义归组，数值T不构成源身份，也不跨LOSO两侧。

train拟合工具将跨度不超过`1e-10*max(1,max|x|)`的列在每个train fold内剔除；[centered_response.py](../../../arithmetic_dse/centered_response.py)消费导出时保留的center、scale和归一化系数。它不再构造巨大raw intercept进行抵消；共线活动列保留并用Ridge正则化，秩和奇异值单列。恒定／近恒定／共线合成数值检查通过。输入valid的最大归一化系数约19.25ps、截距84.06ps，原约10⁹量级抵消消失；这只证明数值条件修复，不能自动证明物理精度。

[共同特征](../../../arithmetic_dse/common_mechanism_features_v1.py)只使用实际Query、逻辑输入列、根输入sink分布和保留reset；[诊断消费入口](../../../arithmetic_dse/common_centered_model_v1.py)继续检查语义／profile／边界／结构邻域，公共调用拒绝。新增C++纯函数与同参数测试有独立入口，未替换旧W2提供者或公共D。

参数、特征与拟合实现先冻结；每批物理发射前登记准确任务和候选身份，诊断消费实现经C++核对后在读取验证标签前冻结。初批9点中13+9与train的9+13交换等价，原登记遗漏了这项去重；其3点已撤销新验证职责，仅作实现复测。原协议、原始角色、原报告及费用全部保留，另存`replacement--role-amendment.json.gz`，用参数／特征／支持／reserve不变的模型登记19+7三个替代点。有效新源各只评价一次，未据验证标签重新选模。已有所有validation只承担回归；其余20个算子独立源未读取、未解锁。

[operator_source_identity_v1.py](../../../arithmetic_dse/operator_source_identity_v1.py)只负责离线数据职责，沿用发射器的Add／ADC操作数交换规则；Sub／SBB保留方向，消费者和capture仍参与源身份。交换去重审计确认Add现有18个train源仍为18个语义组，原train留一分组不需改变。`validation-duties.json.gz`及回放会检查有效新源与train不相交、撤回源确与train等价；该身份不进入价格函数。

## W3：Add新验证通过，窄源回归仍失败

共享面积函数为prospective ALU原语工作量乘正值数值响应；原Add时延及共享Mul参数保持。有限候选中选中较简单的共同响应，进位扩展特征没有因实现出来就被强制采用。

下表均为源内各T平均相对误差，再跨源取median／P95，单位为百分比。

| Add数据职责 | 面积median／P95 | 时延median／P95 | 覆盖及结论 |
| --- | --- | --- | --- |
| train完整源LOSO，选择诊断 | 7.88／12.87 | 继承原时延 | 不能当独立泛化成绩 |
| 3个有效新源、9点一次性validation | **7.03／8.87** | **5.81／8.80** | 9/9覆盖，通过默认门槛 |
| 前轮已消费Add回归（20点） | 8.67／16.09 | 8.84／13.31 | 汇总通过，逐源失败另列 |
| 已消费11+7窄源回归 | **17.71／17.71** | 原时延继承 | 面积失败，不能被汇总掩盖 |
| 已消费12+5窄源回归 | 13.09／13.09 | 原时延继承 | 本候选回归通过；原15.88%失败身份保持 |

有效新验证为19+7完整20位、57+31已知低零并双capture、191+127接320位消费者，各3T=500／1373／3000ps。有限矩阵和职责均在各批测量前确定。旧面积模型在同一批有效新验证为10.08%／10.63%，同样通过，本包不能宣称新模型在所有来源都优于旧模型。13+9的三个复测点面积／时延源平均误差为9.42%／8.31%，不计新源泛化成绩；初批9点原报告封存为已被职责修正替代的结果，不能与有效9点混用。这些点不是13点自适应协议完成证据，也不解锁750／1000／1125／1250ps。

Mux时延稳定化后train LOSO为15.80%／20.67%，仍未过15%门槛。新消费者／相关根／功能逻辑及完整阶段资格没有由本次面积结果转授。

## W4：数值条件已修，native_valid与保护仍未过

S继续用银行最大值和固定逐源辅助目标；新根分布／reset输入可用于各控制来源，未使用实际buffer树或电容。逐源函数、支持及数值T非负LP保护均在train冻结，未手工增加reserve。

| 控制类 | train银行LOSO median／P95 | 已消费2因素银行回归median／P95 | 该回归逐源保护漏点 |
| --- | --- | --- | --- |
| native_valid | **20.30／31.23** | **21.55／26.47** | 0 |
| native_enable | 5.89／13.20 | 6.38／7.47 | 1 |
| input_valid | 9.84／21.86 | 10.33／13.86 | 0 |
| external_valid | 4.92／10.17 | 7.20／8.31 | 1 |

这些因素银行已在前轮消费，本次改善是回归结果，不能称新独立验证。旧5银行的input_valid仍18.07%失败；新诊断支持因reset比例拒绝其中一个银行的3个实现，覆盖12/15，明确列出拒绝，未把旧域重新宣布为全覆盖。旧银行只有聚合标签，逐源保护漏点为**不可测**；原评价程序曾把空集合写成0，`report-corrected.json.gz`保留仅报告修正和原报告SHA，原文件仍在，没有重新选模或改变价格。

270条grt路径均完成同实例cell弧与跨实例wire增量守恒分解；162条还保留相容synth逐源路径，其余缺失不造零。输入valid的synth→grt cell／H变化中位数为+147.43／−131.79ps，说明只拟合完整R会面对明显抵消。native_enable的cell／wire／H增长中位数为+207.75／+98.83／+26.24ps。各项中位数不能相加当成总增长中位数。

标签语义保持：寄存器路径`R=d_comb+H=T−slack`；端口标签已经扣除0.2T输入延迟，因此是`R=T−0.2T−slack`。本包没有把端口标签改为寄存器公式。reset功能检查保留，reset时序仍单列暂缓。

native_valid保护在500／1500／3000ps为261.05／361.80／379.54ps，保守代价和漏点分别保存。宽／深实际算术S、shared物理复用及完整阶段仍待W4／W6，未用FF面积或软件特征可提取替代控制电气资格。

## W5：定位实际前缀与融合差异，保留失败

离线审查实际覆盖68个Add／Mux点及81个G点，149份train综合日志均加载ORFS的`lcu_kogge_stone.v`。旧Boolean几何使用Brent–Kung，只能视为代理，不能再声称重建了当前流程的实际前缀。

| 零压缩train源 | 位宽 | 实际ALU／MACC数 | 1500ps synth→grt时延（ps） |
| --- | ---:| ---:| ---:|
| a4736d1f1d9438c7 | 24 | 0／1 | 266.6→327.4 |
| 4eab470e164ce4a1 | 64 | 0／1 | 316.4→433.3 |
| c9bad07c2b1f226b | 64 | 1／1 | 167.5→193.4 |
| 0ceb763832521a0b | 96 | 0／1 | 355.8→440.3 |
| f5bf5f9e3e7d766b | 40 | 0／1 | 169.9→192.5 |
| 4d624e640e05dfbf | 73 | **2／0** | **446.6→500.1** |

73位源在WREDUCE后首个中间Y由73缩为51位，但后续输入连接未成为相同完整SigSpec；ALUMACC日志没有合并，最终是两个串联ALU。旧G几何先按列重排再统一压缩，遗漏该发射／优化边界，低估并非仅来自布线。`alumacc.cc`的完整SigSpec匹配、用户数和溢出检查、`wreduce.cc`的端口缩窄、`maccmap.cc`与实际LCU均保存源码SHA与日志片段。没有仅凭源码就把全部时延增长归因于某一修复命令。

稳定化模型的六零压缩源LOSO面积median／P95为9.66%／25.48%，时延13.32%／33.45%；**73位单源时延LOSO仍37.33%，全train拟合后的该源仍29.11%，面积仍19.11%**。这些失败继续阻塞发布。通用carry-run特征在整源LOSO中未胜出，保留全部候选而没有给73位增专用系数；未为失败G候选花费新的validation。下一后继需要先对齐实际前缀、发射顺序与不能合并的中间边界，再重新建立共同模型；组合launch、多消费者、相关根及区域间连线资格仍未授予。

## 复现与费用

在仓库根运行默认Python回放；它会禁止数值推理启动子进程，重新检查88个源码、模型／46个证据文件SHA、343次真实参数特征、435次价格及15项跨语言负例对应的Python拒绝，再检查12点物理收据及有效9点／复测3点职责。另有4项畸形数值模型拒绝和交换／方向／负载／消费者的源身份检查。没有调用后端，也没有把诊断候选注册为公共价格。

```bash
python3 -B -m experiments.arithmetic_dse.common_centered_replay_v1
```

需要从源码重建C++检查时，使用独立CMake入口，不修改W2被冻结的CMake文件：

```bash
cmake -S regression/centered_response_build -B build/common-centered-response-20261114 -DCMAKE_BUILD_TYPE=Release
cmake --build build/common-centered-response-20261114 --target arithmetic-centered-response-test -j4
python3 -B -m experiments.arithmetic_dse.common_centered_replay_v1 --native build/common-centered-response-20261114/arithmetic-centered-response-test
```

本轮两种回放均实际通过。旧`common_model_repair_replay`与W2 `workload_owned_evidence`也实际通过；后者重新核对4819个归档成员，未重启RTL仿真器，未增加候选或物理资格。

新物理费用合计12 synth、12 grt、120 support，0失败、0自动物理重跑；累计叶wall增量791.54s、CPU增量1277.63s。其中初批9点为682.24／1155.29s，替代3点为109.30／122.34s，撤销验证职责的费用未删除。共享Ledger结算pending=0及4任务／4线程／8192MiB限制见`settlement.json`，逐叶收据见`ledger-receipts.json.gz`。源码机制审查只读既有train产物，未启动额外EDA。主仓库和RTLzz新增实现／证据尚未提交或推送。
