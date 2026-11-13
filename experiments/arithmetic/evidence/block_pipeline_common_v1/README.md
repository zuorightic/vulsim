# 通用分块流水先导证据 v1

本包记录通用候选、真实需求、状态／归约后继准备及有限物理标签资格。主文档见[通用分块流水说明](../../BLOCK_PIPELINE.md)，实施见[§7.86](../../../../mission/lxy-plan-fix.md#common-block-pipeline-first-package)。不发布新价格，不转授完整D资格。

软件验收保留原324放置并新增181个4位放置；30张结构图各132组独立整数参考、224份RTL各64周期／8832次有效比较通过。最后40份代表RTL另有1560次有效比较，包含5种真正跨两级的4位乘法内部归约切分。见`legacy-equivalence.json`、`software-acceptance.json`和`actual-three-stage-RTL.json`。`strict-stage-counts.json`分开“三个非空算术级”和“首级仅Mul”，不能把33个笼统非空方案全称为目标式分级。

矩形、截断、其他位宽、改名和多Mul复用同一接口；多Mul三级在4096预算处明确不完整，同图二级6结构／448放置完整通过。6项策略／预算拒绝、4个大银行25344个寄存器比较／7个非法规格拒绝通过。新最终合并几何103项跨语言及源编号不变性检查通过，旧几何字段保持原值。

全部物理点在标签读取前登记为`not_training`，固定T=1500ps，共8 synth／8 grt、0 detailed、0物理重试：

| 家族 | 请求数 | 标签资格范围 |
| --- | ---: | --- |
| 4×4 Mul直接／移位宽Add负载，8×16窄Add | 3 | 节点最大值、独占面积、FF／端点及实际Liberty弧 |
| 稀疏零压缩／低压缩归约 | 2 | 全区域测量，不生成内部Add独立标签 |
| 96个16位字／24个72位字的大银行 | 2 | 实测native3074／3458 FF、三所有者和九类路径，不等于实际算术图／连续T已合格 |
| 64位补零／直通／算术输出混合归约 | 1 | 43零位／4直通／17算术输出；24输入位、21动态捕获位，另有valid FF |

`local-qualification.json`和`sparse-output-qualification.json`共12阶段严格回放及12项实际经过Liberty弧删除负控；`state-qualification.json`为4阶段银行／边界回放及4项FF数量负控。setup／hold原值保留，标签资格不代表目标时钟或签核通过。

父公式诊断见`local-parent-diagnostics.json`和`state-parent-diagnostics.json`，只作域外复用诊断，不供D、不拟合、不当新独立质量。4位Mul延迟高估约32–34%，稀疏G面积高估约82%／155%；大银行native面积误差约0.20%／0.31%、external约0.76%／0.12%，input service低估约18.14%／21.35%。支持域保持拒绝，未按源补价。

完整根为`/home/zyrv/vulsim-artifacts/block-pipeline-20261112-v1`。`raw-archive.json`记录归档SHA、字节数和成员数；逐成员解码验SHA后才清理本轮112份中间ODB。综合／最终ODB、原始报告／标签／CEC输入及失败日志保留；恢复全部检查点需使用归档。本小包的JSON收据不能代替完整原始回放。

源码身份见`source-freeze.json`，原G拟合18项／D交付31项冻结核对通过。C++显式构造、诊断Query缺默认字段和新构建目标未重新配置的三个软件失败及费用保留，修复未重跑物理实现。资源见`resource-closure.json`。未git add／commit／push。

本轮完成需求／候选软件部分及第3项资格先导。准确的后继训练源／职责、拟合、S负载与数值T修正、实际算术状态／S/G联合、新独立验收及新D价格绑定仍待；reset时序按用户决定单列。
