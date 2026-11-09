# 真实消费者／捕获的精确局部位映射 v1

2026-11-09。[当前计划§7.52](../../../../mission/lxy-plan-fix.md#step7-fast-prototype-characterization-protocol)。这是静态需求清单，未启动物理采样、拟合或独立模型测试。

`loads.json`将P0的19种形状／57个粗负载描述展开为63项精确局部上下文：35项消费者绑定、28项捕获位映射。逐位保留Slice／Concat／zext／trunc／assign／bit_select、已知零／一的位置、消费者操作数序号及捕获银行。不同捕获位连接可以具有相同的旧粗描述；六项增量来自这种差别。

预测参数仅包含生产者／消费者语义、位宽、已知位、位映射和银行，案例名、拆分身份、NodeId与hash仅用于静态追溯，不作为预测特征。消费者的其他动态输入按独立launch表达；真实相关性及组合优化仍须后续G验证。

位映射中的整数是生产者结果位号，字符串`0`／`1`是常量，`external`为其他动态来源；`undemanded`明确表示最终结果不使用该位置，不能向已裁剪的生产者索取高进位，也不把不需求位冒充语义已知零。

`static-graphs.json.gz`保留完整三候选typed图；`sources.json.gz`为源快照；`proof.json`记录完整清单回放、5项位连接核验和循环／动态选择／错误slice三项负控。初次高进位前检失败与费用保留在原build／Ledger，后继明确不需求位后通过。

```bash
python3 -B regression/arithmetic_fast_loads.py verify \
  --out experiments/arithmetic/evidence/step7_fast_loads_v1
```

本清单尚未生成真实消费者测量壳，尚未冻结train／validation／锁定test；无新的物理标签或模型参数。下一步是源与FF／端点覆盖前检、数据角色／质量／预算冻结及紧约束容量验证。
