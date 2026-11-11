# 第6—7步 reset 与共享状态缺口后继

本包对应[规划§7.77](../../../../mission/lxy-plan-fix.md#step67-reset-shared-gap-successor)。共享状态可测性及预测侧纯位投影通过；reset v2 未通过验证，不授予正式S／G联合或D资格。通用节点、S和共享面积函数维持原冻结字节，G=0，1000ps物理联合test及locked源保持锁定。

| 项目 | 实际结果 |
| --- | --- |
| reset读取 | 复用24个train＋9个validation快照，7569＋2694个实际唯一FF-D端点，72＋27条严格Liberty最坏路径；无新synth／grt |
| reset v1 | train median／P95为16.1413%／36.3824%，未通过，候选与失败保留 |
| reset v2 | train为6.9240%／23.5659%；冻结后validation为21.8180%／28.1140%，median超过15%，判`failed_reset_validation` |
| 支持／可行 | validation域内拒绝0、错误可行0；它们不抵消点误差失败 |
| Python／C++ | 66个实际函数请求一致，含7个数值T和10项域外拒绝；1000ps仅软件查询 |
| shared placement-0 | 205个逻辑FF引用／141个唯一物理FF／32个别名组；全部205项reset／hold／update／clock Boolean检查、6项负控、grt及CEC通过 |
| shared placement-1 | 183个逻辑引用／183个唯一FF；grt及CEC通过 |
| 预测侧投影 | 不输入mapped FF名；按纯位更新、stage、enable及reset构造等价类，两位置均与实际成员一致；2项不同生命周期负控阻止合并 |
| 原始归档 | 2854个成员，36356545字节，实际恢复并逐文件验SHA通过 |
| 隔离回放 | 328个封存成员，重拟合、guard、失败判断、66项native输出、422个真实reset端点和两个状态证明均重现 |

reset v2使用同一组数值参数：

`d_point = 94.071716461 + 4.582845254*sqrt(F) + 4.585217202*sqrt(R) + 126.924573*(1-500/T)`。

`d_guard = d_point + 124.237934270`，其中guard为最大正train残差加固定25ps；按原输入reset到达0.2T的约束与0.8T比较。F、R分别为语义FF位数和变量位reset-one数量，支持限制及T∈[500,3000]保存在冻结候选中。该公式属于验证失败候选，不能用于正式D。源／shape／候选／placement／精确T编号没有进入函数或支持白名单。

共享测量没有将3个逻辑capture直接改价为3个独立bank。placement-0中的同生命周期纯位别名在综合后合并，节省64个真实FF；placement-1还涉及同一结果绑定消费者双输入的相关性。节点查询规范化、S独占计费和相关消费者的支持仍需后继资格。两实测总面积243.704700／269.919540um²仅属可测性探针，不构成整级时序或正式候选排序验收。

原始持久根：[stage67-gap-20261111-v1](/home/zyrv/vulsim-artifacts/stage67-gap-20261111-v1)。旧物理快照沿已恢复的共享函数归档SHA引用，不重跑、不重复收费。原始目录、两个reset报告适配停点、共享读取及负控脚本停点、初次封包缺依赖失败均保留。v1小包的隔离回放因缺少`regression/arithmetic_steps123.py`停止；本v2补齐依赖，模型与标签未变。

在标准库隔离环境运行：

```bash
python3 -I -B experiments/arithmetic/evidence/step67_reset_shared_gap_v2/replay.py replay \
  --evidence experiments/arithmetic/evidence/step67_reset_shared_gap_v2
```

回放不访问原始绝对路径。C++部分重读并比对已封存的真实native输出，未在回放中执行二进制；原二进制与源码SHA由冻结和最终完整性检查绑定。完整EDA和CEC原始见证在已恢复的大归档，便携包内保留两个真实状态及Liberty序列逻辑见证。

最终费用及完整性见[resource-closure.json](resource-closure.json)和[final-integrity.json](final-integrity.json)。封存后收尾的收据另列，不声称包含于更早原始归档中。后续688 synth／688 grt、86400秒墙钟／172800秒CPU／30GiB保留继续有效。
