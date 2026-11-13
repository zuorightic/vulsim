# 表示、结构支持与S／G误差归因后继

2026-11-13。本包完成软件合同修复和train／已有后端产物归因，**没有新价格拟合、物理采集或独立测试解锁**。原100点修复候选及失败保持，14个独立源仍锁定，公共D策略未变。完整根为`/home/zyrv/vulsim-artifacts/common-functions-representation-20261113-v1`，配置见[common_representation_v1.json](../../../arithmetic_dse/configs/common_representation_v1.json)，实施见[§7.91](../../../../mission/lxy-plan-fix.md#common-representation-support-attribution)。

## 结构邻域缺陷已单列修复

用户审查的9个train源、结构0／0／0／1／1／1／2／2／2、k=2得到复现：旧版本半径0，三个训练结构均拒绝。新`conditional_function_support_v2`从校准前就按结构去重，尺度、有效k、留出校准和查询均使用同一独特几何集合。按整个结构留出，源／周期复制不影响门禁。只有1／2个不同结构时有明确的有效k规则；anchor不保存价格。

回归覆盖重复结构、复制源／周期、少量独特结构、角色／非法参数、连续T及域外行为。修复后上述三个结构均接受，半径1.05。对封存真实数据保持原特征表示，只替换邻域算法，Add／Mul／G的半径和查询结论均未变化。因此该实现缺陷确实存在，但没有解释本轮真实数据的Add拒绝，不能与输入顺序问题混为一项。详见support-defect-and-impact.json。

旧版本文件及冻结失败包保留原字节；新配置明确引用v2，后继拟合不能继续使用旧的去重口径。

## Add的Query、特征和RTL合同

新增Python `canonical_add`和C++ `normalizeAddQuery`／`normalizedAddFeatures`／`normalizedAddCore`。规范顺序按结果截断后的有效位数、高低落点、声明宽度及mask确定，不使用价格、源ID或实测。完整输入属性随置换移动，外部输入wire身份、位宽和mask仍保持，Core按证书中的`operand_permutation`连接内部两输入；消费者、结果映射和capture不变。没有对两个方向计价后选择较准者。

规范化descriptor与RTL都使用新策略`unsigned-add-normalized-operands-v1`，旧价格函数因策略身份不相容而拒绝。现有公共D发射器继续原策略；新工具是后继绑定接口，不能宣称已对公共D切换。

599项Python／C++规范Query、全部特征及RTL文本核对一致；31个train代表／边界结构执行1984次正反输入随机算术比较，4个train完整采样壳各64周期检查数据、消费者、capture、valid及reset，全部通过。交换输入后的特征／支持变化为0；原validation在500—3000ps内的8个结构拒绝，在新规范表示的结构检查中不再出现。**这不代表旧延迟误差已修复**：没有重新拟合，也没有把旧混合顺序的标签改名为新策略标签。

新的Query必须带输入置换与发射策略身份；原测量只保留自己的RTL／策略资格。若需证明映射相容或端口效应，应先登记train成对实验的源、连接和T，不能直接用规范化特征重训并继承全部旧物理资格。

## S控制源合同及物理归因

`state_control_queries`逐个列出port iv、service valid和每级native valid；显式表示下一级数据使能负载、valid传播负载、自身保持、capture保持及其使能负载。输入valid条件保持与无条件传播有不同特征。它要求调用者给出真实service context，不从银行总量猜测。

45条已有train银行控制锥与新query的跨级／自身保持负载一致；505个实际placement在两个显式软件service context下都可提取，不能因此宣称实际算术／电容模型合格。新合同把不同控制源分开，并没有把S边界资格变成通过。

本轮用27个train物理点的synth／grt报告分解108个控制路径对，逐单元检查Liberty弧并守恒到原标签。代表train银行`repair/S-09ddf99a74e6cef4`、1500ps的native_valid：

| 分量 | synth | grt |
| --- | ---: | ---: |
| 单元数据延迟 | 156.92ps | 435.38ps |
| 数据连线延迟 | 0ps | 88.58ps |
| 边界H | 75.71ps | 178.23ps |
| 合计所需周期分量 | 232.62ps | 702.19ps |

两个grt单元内步分别约122.13ps和98.09ps。证据说明不能只用逻辑fanout或单一银行最大负载解释全部差异，后端缓冲／驱动、互连和边界响应都重要；也不能把约470ps增长全部称为“wire”。input_valid的train RTL还区分we_iv保持、与数据共享使能和无保持；已有路径含hold修复单元与负H，必须保留合法边界分解，不能把Q→D或port→D简单等同组合逻辑延迟。

这些是同源同T的两个阶段快照，最坏路径可能变化；分解文件保留witness变化。当前没有提高reserve，也没有生成新的S点模型。

## G面积归因及后端机制

69个G train点／23源的贡献和残差按零压缩、稀疏、压缩工作分别保存。满秩不等于系数有物理可辨识性：当前NNLS的半加法系数仍为0，稀疏短进位段和压缩区域存在相反误差。5个train代表的10份synth／grt实例普查与独占面积守恒，没有通过移动shared归属来改善数字。

| train代表 | 模型预测 | synth实测 | grt实测 | 阶段差异 |
| --- | ---: | ---: | ---: | --- |
| 原train-6，500ps | 105.546um² | 134.603um² | 157.070um² | 原有综合工作量已低估；buffer／inverter面积19.129→41.334um²，逻辑面积115.474→115.736um² |
| 多段稀疏train代表，500ps | 11.089um² | 8.442um² | 8.398um² | 过估在综合端已存在，物理阶段几乎没有增加 |

原train-5@500ps也从64.808升到72.783um²，而模型52.283um²。不能把所有残差归为OpenROAD，也不能仅改基础综合公式便认为物理增长已解决。synth到grt包含多个物理步骤，表中增量不归因给单一GRT命令。

已定位源码机制：Yosys `alumacc.cc`会按信号序对可交换输入排序；`maccmap.cc`对向量行进行3:2压缩并生成最终`$alu`；`techmap.v`的`$lcu`采用Brent–Kung前缀树。抽象逐列FA／递增计数与实际前缀逻辑并不等价。OpenROAD流程包含placement／CTS及基于估计寄生的design／timing repair，保存的GRT日志确认有repair与buffer插入。源码快照只用于机制解释，不冒充已证明其与已测二进制build完全一致。

下一轮先检验通用的最终进位段／前缀工作量、压缩与最终合并分别受数值T影响的交互项，以及可计算的控制负载／预期物理规模。零修正或已有公式合格即可保留，不默认增加一组修正回归。禁止用实测buffer数／路径步／单元名作为在线特征，也不为每个shape拟合系数。

## 当前停点

软件合同及源身份已冻结在protocol.json；Mul、Add面积、S面积和shared候选保持。先登记下一轮train侧公式／控制源拟合及相容性规则，必要物理对照只服务明确假设；本轮没有启动额外大批采集。只有候选、支持和保护均合格冻结后，才可进入14个独立源。

一项归因软件叶因旧G未保存reference_connections报告而停止，原日志和费用保留；S分解已完成并复用，G后继直接读取已有Liberty和实例／所有权普查完成面积检查，没有启动工具补报告或重复物理测量。费用见resource-closure.json；不含任何新价格资格。
