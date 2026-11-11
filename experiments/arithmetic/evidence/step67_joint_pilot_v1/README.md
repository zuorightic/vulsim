# 第6—7步真实串联pilot与零G联合诊断 v1

**历史封包。** 本包的普通回放曾通过，但隔离入口暴露逻辑归属依赖缺失；失败与本包保持原字节。当前使用[后继v2](../step67_joint_pilot_v2/README.md)，它补齐冻结依赖并通过`python3 -I`回放，节点模型、物理标签及零G失败未改。

本包记录第5步发布函数接入真实S边界提供者后的有限联合验证。发布模型SHA256为`513f2f7693c702c492fec380ed81b385f4691f18bd05aaac6596d27f0340f0d2`，S binding仍为候选复用身份`76dd37094be027dd5e4c6565d63ae037be1b541a88e63e0dfe233fe571ef3542`；未修改节点系数、S系数或reserve。

## 已通过的第6步部分

选取预登记的`combination_validation` serial源的两种寄存器放置，T=1500ps。两项pilot均完成synth→grt；未解锁`locked_joint_test`。保存的mapped网表经过逐位FF、常量位、valid和寄存器别名解析，实际状态语义用独立布尔证明核对reset、enable、hold、update和正沿clock：两种放置分别核对291和276个FF。四个物理阶段的端点／路径读取共3394项端点检查通过。Liberty实际弧删除、方向修改、断线、伪造算术所有者、过期归属证书、变量mask、reset、FF输出极性及enable篡改共28项负控全部拒绝。

这项结果只证明实际状态和端点读取合同在本pilot上成立。它不把有限T=1500ps结果扩展为连续S域资格，也不授予完整S/G或正式D资格。

## 第7步零G结果

发布函数重新消费6个组合验证源、12个placement和500／1500／3000ps。78次节点查询覆盖，18次按冻结支持规则拒绝，拒绝保留给shared、宽移位归约和跨级保存值等缺口，没有让G猜价。

两个serial placement的总面积相对误差为2.7873%和3.7455%，节点级延迟误差在1.4%到13.4%之间。零G完整阶段时序预测没有通过预登记的组合门槛：两个placement的两个阶段均出现过度保守的预测。placement-0的grt setup slack为+638.984619ps、hold为+0.158887ps；placement-1的grt setup slack为+454.747681ps、hold为−0.523505ps。setup和hold分别记录，不能因为setup为正就称完整阶段通过。

误差分解保留在`/home/zyrv/vulsim-artifacts/stage67-joint-20261111-v2/analysis-v3/`。节点独立最大值相加的保守性、节点函数误差和边界／连线／clock项均分别输出。当前证据不足以安全发布G修正；一次结构修正草稿因混淆诊断标签schema而失败，见[g-correction-failure.md](g-correction-failure.md)，没有改动模型或物理结果。下一轮应先定义并验证实际owner之间的边计费合同，再决定最小通用修正，不能把该草稿当作G资格。

## 资源与恢复

本轮实际结算2 synth、2 grt、28 support，叶墙钟150.072966秒、CPU245.57秒，pending=0。完整ODB／网表／CEC／路径读取产物保留在`/home/zyrv/vulsim-artifacts/stage67-joint-20261111-v2`；这是同盘持久目录，不是异机备份。摘要及小型验收文件见[summary.json](summary.json)。第5步模型和第6步S原始证据保持原路径，旧零G失败和后端失败收据均保留。

当前结论是：**第6步实际状态／端点pilot通过；第7步零G联合失败，G尚未发布；`full_D_ready=false`。** locked联合源仍锁定，下一步应针对边界／连线责任做后继协议和最小修正验证。
