# 窄算子、归约几何与状态负载后继

**2026-11-13恢复与固定拟合诊断已完成，见[本轮证据](evidence/common_family_continuation_v1/README.md)及[完成审查](evidence/common_family_continuation_v1/RESULTS.md)。** 算子147点通过251项特征／257项同参数核对，validation误拒绝0；Add／ADC、Sub／SBB、Mul达本轮精度门槛，比较面积及Mux时延未过，三区覆盖仍待，整包不发布。截断需求先裁掉无用逻辑，沿同一物理标签重提取。G前缀限定组件已通过4源／8请求的一次性独立验收，见[模型](models/asap7_G_prefix_v1/README.md)；S同银行响应及cell／wire／H归因完成，native_valid仍不合格。公共D／旧价格保持，下方各轮“最新”按当时检查点解释。

**表示修复后继已冻结软件身份，价格尚未重新拟合。** [新配置](../arithmetic_dse/configs/common_representation_v1.json)明确采用`conditional_function_support_v2`统一结构去重；`canonical_add`及原生`normalizeAddQuery`／`normalizedAddCore`把置换、Query、特征和发射绑定到新策略；`state_control_queries`分别描述服务保持与每级valid源。599项规范化合同、1984次算术、4壳×64周期及控制源投影通过，S／G已有train物理归因完成，详见[证据](evidence/common_representation_v1/README.md)。旧失败和源码字节保持，不能将旧混合顺序标签自动作为新发射策略标签，也不能由这些软件检查开放公共D价格。

**最新状态：修复后继100点采集、固定拟合及完成审查已结束，当前仍未通过发布。** 见[完整结果](evidence/common_functions_repair_v1/completed-review/RESULTS.md)和[§7.90](../../mission/lxy-plan-fix.md#common-functions-repair-completed-review)。2084项同候选数值核对通过，Mul参数保持，Add面积和shared改善；Add时延／输入顺序敏感性、G前轮稀疏域面积、S控制及8点保护漏覆盖仍须后继。14个独立源保持锁定，正式价格未改。下方“正在执行”及204点首轮状态保留为历史检查点，当前以本段为准。

本后继继续使用小算子函数＋S／shared＋G，首个需求图为MAC32三级，模型输入为操作和位宽、已知位、结果需求、消费者位连接、逻辑负载、状态规模及数值T。原生产模型和支持域保持；当前采集与候选拟合不能直接授予新的D价格。

**修复后继正在执行。** [新配置](../arithmetic_dse/configs/common_function_repair_v1.json)及[§7.89](../../mission/lxy-plan-fix.md#common-functions-repair-successor)承接下述首轮失败。新增`operator_interval_features`、`state_control_features`、`shared_interface_features`和`conditional_function_support`；Mul系数保留，Add按活跃位／真实进位列和消费者位置／负载建函数，G补多进位起点的可辨识变化。新特征615次跨语言核对和505个实际控制投影通过；尚无新价格资格。

支持算法的anchor仅保存train结构特征，用于范围／邻域拒绝，不保存延迟、面积或精确T。T在连续范围内输入同一数值函数，anchor不选择系数。结构支持、精度、S／shared和完整阶段必须分别验收，不能通过缩域隐藏validation误差。新S的`launch_valid_logical_load`统计向下一级数据使能及valid的输出负载，输入服务自身的保持反馈另外核对；银行连通验证不能自动授予实际算术或电容资格。

**当前状态：采集、拟合诊断与首轮审查完成，发布验收未通过。** 去重204点、同一候选556项跨语言核对通过；[首轮结果](evidence/common_functions_v1/completed-review/RESULTS.md)分开旧／新validation、各T／负载、G稀疏、S边界及shared。8个独立源继续锁定，原参数／支持域保持。

T本身是模型的数值输入。禁止的是精确T编号、one-hot类别和逐T专属系数，允许log₂(T)、1/T及数值压力与工作量的组合；保护点身份和实测slack不作为推理特征。

约束见[配置](../arithmetic_dse/configs/common_function_extension_v2.json)，执行记录见[§7.87](../../mission/lxy-plan-fix.md#common-functions-three-lines)，[紧凑证据](evidence/common_functions_v1/README.md)保留角色登记、初轮数值核对和读取器接续。临时控制脚本在`/home/zyrv/vulsim-artifacts/common-functions-20261112-v4/tools`。

## 可复用接口

| 部分 | 输入及变换 | 当前状态 |
| --- | --- | --- |
| `common_operator_features.features(query)` | 原OperatorQuery及位／负载特征，增加位宽对数、1500/T和算术工作量×压力 | 从现有查询直接计算；新全局共享ridge候选，未发布价格 |
| `common_function_sampling.decide(history, source, role)` | 固定保护点后使用真实slack比例提议周期；沿用每源最多13点和三区间距规则 | 只负责离线测量，不参与推理；新750／1000／1125／1250ps独立职责受保护 |
| `reduction_merge_features.features(width, terms, T)` | 位列压缩后，统计全加法／半加法／递增／直通列、carry段及跨度 | 共享非负几何函数的基函数；无形状ID和逐T系数 |
| `common_state_features.input_load_features(widths, sinks)` | 对变量输入位统计逻辑使用数、最大位负载、负载对数与平方根之和 | 编译前的逻辑负载代理，不能当实际映射电容 |
| `common_state_features.bank_features(spec, T)` | 三状态所有者的位／字／reset／enable，加逻辑负载与数值T | 大银行的S复用／残差和边界诊断 |
| `common_state_graph_loads.features(graph, placement, state_query)` | 用真实图、纯位连接、实际寄存器槽和第一级使用点计算相同负载代理 | 为D消费准备；须有匹配且已物化的状态查询，不授予算术状态物理资格 |

S先保留native／external面积函数，检查input service残差；控制和边界用语义路径类别及数值特征。shared的clock／physical／root repair仍要独占计费，功能面积输入来自参数预测和语义逻辑计数，不来自实测整图面积。出生适配器与observer有明确归属，不能由G补偿。

## 数值消费准备

RTLzz新增`commonOperatorFeatures`、`logicalInputLoadFeatures`和`commonNumericalPrediction`，只负责数值特征／系数运算。测试入口的构建命令为：

```bash
cmake -S rtlzz -B build/common-functions -DCMAKE_BUILD_TYPE=Release
cmake --build build/common-functions --target arithmetic-common-function-test -j4
```

查询向量中的`descriptor`由原OperatorQuery表达，或通过`input_widths`／`sink_inputs`表达逻辑负载；可附同一候选的`model`，核对真实参数推理。该入口不会让原CostProvider绕过资格门禁。首个真实候选已通过434项Python／C++核对，后继多周期拟合结束后会对新的同一份参数再次核对。

真实图的服务输出负载提取已对505个实际placement检查，使用输入已知位、纯位连接和寄存器槽的variable mask；首级64个4×4且无同级Add时，算术输入使用512次、c的首级捕获64次，最大单输入位负载8。该数值是结构参考验证，提取函数不按块宽或案例名分支；它仍是逻辑负载代理，实际算术状态及映射电容相容性另验。

## 本轮执行与后续验收

42个源包括34个train／validation和8个locked_test。242个请求为容量上限，每批最多12个准确源／角色／T请求再检查Ledger和资源。算子先测1500／500／3000ps，再自适应补紧、适合、松区；G与S先覆盖这三档。缺区与实际算子响应分别报告，完整路径slack覆盖不能代替算子响应检查。

本轮自动提取、拟合、C++核对及采样响应／G关键子域／shared诊断均已结束。204点由37个前驱有效点加167条v4完成记录组成，后者包含只读恢复点；242仍仅是容量上限。12／14个算子源满足三区间距，另外2个在13点上限停止，保留不足和全部有效标签。旧S固定ABC1500ps的SDC列表没有1500ps，因而本轮实际复用了S面积系数，没有旧S时序行加入条件拟合。

当前候选缺正式支持／拒绝规则，G面积、S部分valid保护和shared未通过；真实小Add有效位／重叠及高移位落点仍有训练范围缺口。诊断封存不等于发布冻结。后继解决失败项及覆盖后，候选、误差、支持／拒绝和预留及实现身份一起冻结，才能解锁新独立源。旧测试、资格源和最终PPA永久不拟合；原始失败和已付费物理检查点的只读恢复保留证据。实际算术状态、完整组合及最终D绑定仍按相应资格单独验收。
