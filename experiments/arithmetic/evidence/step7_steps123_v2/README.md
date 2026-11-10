# 第1—3步完成证据：算子接口、物理可测性与采集协议

本包对应[修订计划第四章§7.59](../../../../mission/lxy-plan-fix.md#step7-steps123-completion)，承接[原生Query与44视图软件闭环](../step7_operator_query_v4/README.md)。用户已确认基础采样、组合验证、最终A／B／C／D及同策略代价对照统一采用`unsigned-op-hierarchy-v1`。本包保存本轮后继接口、真实资格测量和正式采集前的冻结协议，未拟合新模型，未启动正式train／validation／locked_test物理采集。

| 交付 | 已验证内容 | 使用边界 |
| --- | --- | --- |
| 公共编译接口 | request-v2传递body与文件级算子定义；公共A／B／C各144周期，旧接口3786项通过 | 固定成本功能验证；生产后端价格仍未绑定 |
| 独立观测采样壳 | 90个后继壳及58个正式候选源各128周期 | 每个银行独立可见；软件向量不是物理测试标签 |
| 有限物理资格 | 4个not_training点、8阶段，节点独立最大值、through-operator slack、面积守恒、mapped银行／别名／端口证书及CTS CEC | 仅为已测结构的读取资格；四个grt点setup均违约，hold另报 |
| 正式采集协议 | 30 train／14 validation／14 locked_test，每源最多13点；实际执行适配器与6项门禁负控 | 754为全体调用上限；按有限批次另发放行文件，禁止自动跑全表 |

直接可读的冻结文件为[源角色清单](source-manifest.json)、[条件模型与对照协议](protocol.json)、[物理结果](qualification-summary.json)、[容量及存储计划](capacity-plan.json)。基础函数使用语义位宽、需求结果、已知位、消费者／capture连接和目标T等预测前特征；声明填充宽度、共享输入根和剩余级内深度保留在查询追踪中，首轮不作为节点回归输入。未见精确shape可成为语义候选，但当前实际价格始终为`cost_uncovered`，尚无独立通过的函数支持域。

内容池采用UTF-8内容去重和确定性gzip，分块≤512KiB。池内有2376个源码、配置、报告及向量成员，包含完整原始路径表和连接表、实际Liberty pin／function／timing信息、mapped语义投影、公共输入／RTL／报告／执行日志、全部尝试的命令及失败收据。mapped投影保存完整launch／capture单元与连接、算术端口及实际输出driver；完整原JSON单独索引，不声称投影等于完整网表。首次超出小包目标的v1原字节保留在本轮build的`provisional-evidence/`，v2仅改变内容编码与留存，未重跑EDA。

可在仓库中执行以下回放；它们不会运行EDA、SAT、拟合或读取正式模型测试标签。实验工作时仍须通过现有Ledger支持叶包装器计费。

```bash
python3 -B -m experiments.arithmetic_dse.steps123_evidence verify \
  --folder experiments/arithmetic/evidence/step7_steps123_v2

python3 -B -m experiments.arithmetic_dse.steps123_evidence verify \
  --folder experiments/arithmetic/evidence/step7_steps123_v2 --external

python3 -B -m experiments.arithmetic_dse.steps123_evidence isolated \
  --folder experiments/arithmetic/evidence/step7_steps123_v2 \
  --out build/steps123-isolated-NEW-UNIQUE-ID
```

便携回放重算8阶段路径／面积、银行／逻辑位及端口证书，重复8项实际报告破坏检查；重生源角色和需求形状、检查正式采集／测试冻结门禁，重算148壳的整数向量及公共A／B／C保存的周期结果。它核对已执行CTS CEC的结论／负控日志；完整CEC图、AIG、ODB及原始工具需要`--external`才能核验。隔离回放从本包恢复源码，先进入恢复根再安装审计钩子，禁止读取原home／项目／build，PATH为空且回放子进程被禁。上述模式不冒称重新编译或重跑物理实现。

池内external索引记录1984个原始文件的实际路径、逻辑字节、编码、SHA256及打包时可获得状态。大产物目前只在本机ignored工作缓存；持久地址和异机恢复尚未落实。第4步批次仍须落实准确存储清单和恢复方式。按这四个诊断点外推全754点约需30.3—147.6GB工作文件，这只是测得范围的外推，不能当作所有源的容量资格。首批计划最多12个train／validation源目标、3任务×4线程，估计工作空间约4.70GB，保留后续30GiB；不会一次保留全部最坏外推产物而不检查空间。

本轮资源从前包结清的12356条账目之后计算；完整增量、失败及最终pending／active／unsettled状态见`publication-closure.json`。本轮真实新增4 synth／4 grt／0 final，首个成功综合通过有据继承继续使用，没有为修复读取器重综合或重跑已完成grt。所有物理行均为`not_training`，正式新增训练行和模型独立测试行均为0，`full_D_ready=false`。
