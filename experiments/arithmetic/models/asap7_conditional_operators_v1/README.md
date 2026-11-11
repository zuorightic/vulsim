# ASAP7条件小算子函数：第5步发布 v1

**状态：`passed_bounded_node_release`。** [operators.json](operators.json)可直接供Python推理及RTLzz生产节点CostProvider消费，内容SHA256为`513f2f7693c702c492fec380ed81b385f4691f18bd05aaac6596d27f0340f0d2`。这是独立节点时延／组合面积函数；状态、连线、共享和完整阶段时序仍由S及DAG／必要G提供，`full_D_ready=false`。

## 调用范围与输出

平台为ASAP7 TC／RVT／NLDM，ABC=SDC，统一`unsigned-op-hierarchy-v1`发射策略及`arithmetic-logical-ownership-v2-closed-islands`离线物理归属读取。支持无符号Mul和零carry Add，目标周期为连续数值区间**500≤T≤3000ps**。T=1000ps已作为未用于拟合／选择的独立精确周期验证；数值接口支持区间内其他T，并继续检查实际结构／负载的联合支持门禁。

输入为现有`arithmetic-operator-query-v1`：操作、操作数／结果需求位宽、已知位、真实消费者及位连接／截断／capture、共同目标T和流程身份。所有特征都能在D搜索时计算。源名、节点编号、候选编号、44视图编号和实测物理量均不作预测特征。

粗数值包络如下，仅用于解释范围；**不能把各维边界拼成任意可接受的参数组合**。实际查询还须通过原冻结的语义／已知位／负载和联合邻域门禁。

| 算子 | lhs／rhs位宽 | 需求结果位宽 | 延迟／面积函数 | 冻结延迟reserve |
| --- | --- | --- | --- | --- |
| Mul | 各8–32 | 8–64 | 共享线性特征函数／以log2(T)分段的共享函数 | 69.649747ps |
| Add | lhs16–64、rhs24–67 | 25–64 | 共享线性特征函数／共享浅树 | 84.942709ps |

不支持的已知位结构、非零carry、消费者种类／数量、负载邻域或范围外T返回`cost_uncovered`，不回退固定表。500／1500／3000ps不是模型的三个查表键；函数显式消费数值T，乘法面积允许在已拟合分段点跳变。

输出为`operator_delay_ps`、`comb_area_um2`及`delay_reserve_ps`，并给出二者相加的`conservative_operator_delay_ps`。这些输出属于算子本身，不含S、共享物理项或整级预算。reserve来自冻结validation经验误差，不能解释成严格物理上界：历史发布区间内Mul仍有8项独立点超出该经验预留，Add为0；该事实保留在验收报告，完整阶段可行性须后续联合验证。

## Python与RTLzz消费

从仓库根目录执行：

```python
import json
from pathlib import Path
from experiments.arithmetic_dse.operator_condition_model import query

folder = Path("experiments/arithmetic/models/asap7_conditional_operators_v1")
model = json.loads((folder / "operators.json").read_text())
descriptor = json.loads((folder / "example-query-1000ps.json").read_text())
price = query(model, descriptor)  # 无候选许可，按正式节点资格查询
print(price)
```

RTLzz请求使用`arithmetic-request-v2`、`cost_mode=backend-model`、ASAP7 profile、对应T和该文件的绝对路径／SHA256。`ConditionalOperatorCostProvider`默认`Production`可返回节点价格；现有公共factory／placement接口也能读取同一文件。它的`group`、`stateArea`及完整接口方法仍拒绝代替S／G，未合格联合提供者不能借节点发布生成正式D选择。

## 发布验收依据

完整[证据包](../../evidence/step5_conditional_operator_release_v2/README.md)包含32个新物理阶段严格重读、原始FF／端口／CEC／SDC／RC及互斥面积证据、旧524拟合点／1048阶段标签不变性、4个全新源×4T的独立结果、真实参数跨语言核对和隔离恢复回放。

新独立源均为未见精确producer形状，包含非对称乘法、宽加法消费者、移位／补零和已知零位Add。源等权统计的median／P95结果：

| 算子 | 延迟误差 | 面积误差 | 精确1000ps延迟误差 | 精确1000ps面积误差 |
| --- | --- | --- | --- | --- |
| Mul | 2.3164%／4.3008% | 2.0122%／2.0562% | 2.6375%／3.4519% | 9.1345%／14.0745% |
| Add | 2.0301%／5.7718% | 4.7442%／5.1987% | 4.3204%／9.7284% | 5.0694%／5.1987% |

每算子2个完整源、8个独立点，全部16请求接受，0采集失败；门槛为源等权median≤15%／P95≤35%。样本量和实际范围保留，不宣称任意参数／任意物理流程都达到同样误差。

真实MAC32编译图的44个合法放置只作需求／搜索回归：500／1000／1500／3000ps下2752次生产节点查询全部覆盖，并与Python逐项一致，不是预测白名单。T=499／3001／3389ps被拒绝，错误模型哈希／profile被拒绝；S／G联合门禁仍拒绝完整D。另735个实际参数／域外／未见精确T向量的Python／C++覆盖状态和数值一致。

原v2整包`failed_independent`保留：Add原归属采集失败，以及Mul3389ps超出旧339–3362ps数值域的拒绝均没有改写。本发布继承相同系数、树、分段、语义／负载邻域和reserve，仅将发布周期与预先指定的500–3000ps目标范围相交；旧完整周期域没有获得发布资格，也没有用test重拟合。

[release.json](release.json)给出稳定模型身份与证据入口；[独立响应图](../../evidence/step5_conditional_operator_release_v2/independent-response.svg)可查看数值T输入下的模型曲线与实测点。
