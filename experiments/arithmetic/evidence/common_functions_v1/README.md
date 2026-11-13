# 窄算子／G／S通用函数后继证据

**采集与首轮审查已结束，发布验收未通过。** 最新[结果](completed-review/RESULTS.md)与[计数／状态](completed-review/summary.json)记录204个去重点、556项跨语言核对和未通过的原因。以下登记、初轮数字及恢复记录保留各自时间范围。

实施见[§7.87](../../../../mission/lxy-plan-fix.md#common-functions-three-lines)，约束见[配置](../../../arithmetic_dse/configs/common_function_extension_v2.json)。当前持久根为`/home/zyrv/vulsim-artifacts/common-functions-20261112-v4`，`progress.json`为采集状态，`work-status.json`为采集后拟合／核对状态。未发布新生产价格。

`source-registration.json`记录42个新源：operator为10 train／4 validation／4 locked_test，G为7／5／2，S为5／3／2。源ID用于数据职责、哈希和源等权拟合，不进入价格函数。96位消费者、较宽状态字、较大列高度与活动位规模、未见零压缩／补零连接分别代表共同参数域，不依赖MAC32视图。

初始34源均通过64周期功能检查，状态寄存器比较67008次；随后新增的较宽银行与归约、宽消费者及稀疏验证源另有软件证明。`initial-software-proof.json`、`successor-software-proof.json`和`conditional-ABC-recovery-proof.json`保留各自范围，不能把它们拼成完整价格资格。

第一轮30个有效点的诊断见`first-round-diagnostics.json`，当时新validation仅有1500ps，不当多周期或独立质量结论。`first-round-native-parity.json`为同一真实候选的434次Python／C++数值核对，最大特征差约7.4e-13；新精确T在这里仅作软件数值检查，没有读取独立物理标签。

两次S500ps采集在综合后被旧固定ABC身份检查拦下。后继验证实际ABC=SDC及目标脚本，严格比较其他工具／库／流程身份，复用两份已付费综合、首次完成grt，原检查点哈希保持；失败与收费没有改写。另一窄Mul500ps已完成grt后被旧层次读取器拒绝，现复用已发布的闭合逻辑岛方法，只读恢复`clone279`的consumer0归属。`closed-island-report-recovery.json`记录0新synth／0新grt、有效综合标签不变、实际Liberty弧删除拒绝及原物理产物不变；单元名只保留为证据，算法按连接和Liberty功能判定。

采集阶段交错完成Mul／Add三区样本、G几何代表和S规模／负载三周期样本。自动收尾已生成完整train／validation快照、候选参数、同模型跨语言核对、三区覆盖／实际算子响应和G子域误差；独立8源保持锁定。特征／参数／支持／拒绝／预留及实现冻结、独立质量、实际算术S和完整组合资格另行验收。原模型和最终PPA不改，完整D资格保持false。

上述采集与自动收尾现均已完成，完成包在`completed-review/`。其中`diagnostic-candidate.json`仅是诊断候选；`physical-compatibility.json`为204点／408阶段逐点核对，`validation-breakdown.json`分开旧／新及各T／负载，`sampling-review.json`保留两源间距不足，`S-shared-review.json`保留保护漏点与域外shared诊断。`predictor-domain-review.json`仅按实际模型输入检查数值需求，不授予新价格；完整域外拒绝规则尚待。原始数据和完整拟合仍在持久根，摘要不等于完整独立复现包。

本轮T以数值变换进入函数；不使用精确T编号、one-hot和逐T专属系数。“精确T不进入价格”的旧日志措辞应按此修正。

`preflight.json`与`actual-D-logical-input-loads.json`记录新逻辑输入负载特征在505个真实placement上的提取检查，纯位连接、已知位和实际槽variable mask均参与计算；49项原G／D冻结文件保持。该提取检查不授予实际算术S或电容资格。接口与责任见[通用函数说明](../../COMMON_FUNCTIONS.md)。
