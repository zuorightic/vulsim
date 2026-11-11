# 第5步条件小算子函数发布验收 v2

发布入口为[ASAP7条件算子模型](../../models/asap7_conditional_operators_v1/README.md)，模型文件SHA256为`513f2f7693c702c492fec380ed81b385f4691f18bd05aaac6596d27f0340f0d2`。验收状态为`passed_bounded_node_release`：发布500–3000ps连续目标区间、既有联合结构／负载支持域内的无符号Mul／零carry Add函数，允许在D搜索时直接查询。完整S／G、候选排序物理验收和正式D RTL资格尚未授予，`full_D_ready=false`。

## 参数继承与范围

[operators.json](operators.json)继承原`882d432c…ab01d2`候选的全部系数、浅树、分段点、特征、已知位／消费者语义、联合邻域和reserve。唯一预测门禁变更是将请求周期数值支持与用户原先指定的[500,3000]ps发布范围相交：Add旧范围209–3000ps、Mul339–3362ps均明确收窄为500–3000ps，没有扩域或按精确周期建表。新独立的16个请求在原／发布门禁中均接受，没有通过剔除新测试点改善误差。

发布状态字段授予节点函数资格；原物理流程、层次发射和经过独立验证的逻辑归属证书保持，支持规则仍是参数化数值／语义门禁。没有源、形状或44候选白名单。完整支持域的所有笛卡尔组合、其他T／平台／signed语义均未宣称合格。

## 独立物理验收

`operator-ownership-fresh-independent-20261111-v1`的4新完整源、16个固定源／T请求全部完成，0失败、0拒绝。源的精确producer形状及完整连接均未用于原拟合／validation，T=1000ps未用于拟合／选择。[generalization.json](generalization.json)逐源核对未见形状，ID只作证据索引。

[physical-replay.json](physical-replay.json)逐一重读16点×synth／grt共32个物理阶段：重算归属证书、完整端点和独立最大路径，核对FF／银行、算子端口、CTS CEC、存储SDC、线RC及整壳面积守恒。新独立中4个请求实际出现root clone／缓冲器，均在不改规则的情况下恢复，不只验证没有clone的情况。完整原拟合524点／1048阶段标签不变性沿用[归属恢复证据](../step7_operator_ownership_recovery_v2/README.md)，原标签和角色未改。

按完整源等权计算各源相对误差中位数，再报告其median／nearest-rank P95；门槛median≤15%、P95≤35%，延迟／面积分母下限10ps／0.01µm²。每算子2源×4T=8点，精确1000ps各2源，全部通过：

| 算子 | 新独立延迟median／P95 | 新独立面积median／P95 | 1000ps延迟median／P95 | 1000ps面积median／P95 |
| --- | --- | --- | --- | --- |
| Mul | 2.3164%／4.3008% | 2.0122%／2.0562% | 2.6375%／3.4519% | 9.1345%／14.0745% |
| Add | 2.0301%／5.7718% | 4.7442%／5.1987% | 4.3204%／9.7284% | 5.0694%／5.1987% |

[acceptance.json](acceptance.json)保留全部新／旧分母和范围外点。原v2整包failed_independent不改写：原Add归属采集失败和Mul3389ps拒绝均保留，旧完整范围不由新4源改判通过。历史168独立点中154点落在发布周期范围，14点在范围外且逐项列明；这些点不删除或改角色。新／旧test均永久排除后续拟合／选择，不重新挑树、系数、域或reserve。

经验reserve为Add84.942709ps、Mul69.649747ps。历史发布范围内仍有8个Mul独立点超过预测加reserve，Add为0；它是经验预留，不是严格上界。节点发布不以它宣称完整阶段一定满足时钟，相关误差必须进入第6—7步的真实联合验证。

## 跨语言与生产接口

[native-parity.json](native-parity.json)：735个冻结实际数据、域外负控和未见精确T软件向量，Python／C++的覆盖及价格逐项一致，11项负控拒绝。未见精确T软件探测不声称已有该T新物理标签。

`operator-release-consumer`使用真实源码／BEIR／原生合法放置及该发布文件的`ConditionalOperatorCostProvider(Production)`。44种放置×500／1000／1500／3000ps共2752个节点查询全部覆盖，并与Python复算一致；没有候选许可和TEST_ONLY价格。该清单仅作最低MAC32需求回归，不决定函数可查询的新形状。错误模型哈希／profile、范围外T以及用节点函数代替整级／S／G均拒绝；真实S候选没有联合资格时，正式D选择继续cost_uncovered。

## 封存与恢复

本包gzpart保存134个源码／模型／收据成员、32份真实物理packet、证书／标签、真实D查询与价格。执行下列命令会实际恢复临时目录，清除实时Python模块，从封存源码重算物理标签、源等权误差、735个跨语言结果和2752个真实查询：

```bash
python3 -I -B replay.py --evidence .
```

该回放已经在共享Ledger支持叶下通过，不调用EDA或拟合。原首次封包漏推理依赖／恢复目录问题及费用保留在v1。物理浮点求和采用绝对1e-8／相对1e-12比较，模型推理跨语言比较采用绝对1e-8／相对1e-10；结构、集合、证书和角色严格一致。

[restore-proof.json](restore-proof.json)记录实际归档恢复，本包[父恢复收据](parent-archive-restore.json)另核对模型和完整真实D报告归档。原始ODB／网表、CEC与逐点归档完整保留在`/home/zyrv/vulsim-artifacts/operator-ownership-fresh-independent-20261111-v1`，直到用户清理；本机同盘不是异机备份。发布工作完整保留在`/home/zyrv/vulsim-artifacts/operator-condition-release-20261111-v1`。

[independent-response.svg](independent-response.svg)、[PNG](independent-response.png)及[CSV](independent-response.csv)给出相同函数在连续T输入上的预测曲线和16个独立实测点；曲线通过调用发布函数生成，未重新拟合或按点插值。

原新独立物理采集已结清16 synth／16 grt／213 support、1113.994552秒墙钟／1651.99秒CPU；本轮发布只增加support，准确结算见publication-closure.json，费用不与父工作包重复相加。第6／7步联合及第8步完整D生产绑定继续待验。
