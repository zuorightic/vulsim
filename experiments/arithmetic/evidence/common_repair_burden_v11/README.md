# W3／W4／W5全train归因与嵌套上下文拒绝实验 v11

本轮完成保存路径／物理变化审计，以及一次预登记的12项train对照。选中候选未过预登记门槛，已封存拒绝；没有新增C++价格版，也没有消费旧回归。v10仍是最近的诊断价格，公共D保持原状，W3—W5尚未整体完成。

现行入口：[任务导航](../../../../mission/README.md)、[§7.110实施记录](../../../../mission/lxy-plan-fix.md#W345-repair-burden-nested-audit)。前驱为[v10证据](../common_transition_incidence_v10/README.md)。

## 机制审计与适用边界

19个S银行／63实现的378条grt控制路径全部可恢复；另有270条synth路径，共648条，108条旧逐源synth路径缺失并逐条记录，没有用聚合银行最大路径代替。每条保存raw points／expanded report及SHA、nets／Liberty弧、cell／wire／H／R。

| grt路径类别 | 保存路径 | 含hold命名单元 | hold命名cell占组合delay median／P95 |
| --- | ---: | ---: | ---: |
| native_enable | 126 | 0 | 0.00%／0.00% |
| native_valid | 126 | 0 | 0.00%／0.00% |
| input_valid | 63 | 63 | 63.45%／76.53% |
| external_valid | 63 | 0 | 0.00%／0.00% |

命名规则为 `(^|/)hold\d+$`。它只描述保存实现，不能唯一识别所有buffer的命令来源或排除其他形式的hold修复。上轮局部线索适用于input_valid；native_valid／native_enable没有这些单元，不能把hold修复外推为它们误差的主要原因。native_valid的wire median／P95为7.15／70.10ps，H median109.42ps；native_enable wire91.33／151.03ps，H median107.85ps。不同统计量不能相加成一条路径。

R标签保持：寄存器 `R=d+H=T−slack`，端口 `R=0.8T−slack`。不扣除实测hold延迟。126对实际valid／enable R比值均≤1只作观察，没有据此增加硬约束。

| train族 | 物理点／源 | `(grt−synth)/grt` median | min…max | 保有grt最大路径分解 |
| --- | ---: | ---: | ---: | ---: |
| Add | 53／18 | -1.94% | -14.23%…24.65% | 21/53 |
| Mux | 15／5 | -7.46% | -8.29%…-5.37% | 11/15 |
| G | 81／27 | -0.26% | -46.19%…23.60% | 37/81 |

149点均保存精确原始synth／grt标签文本及SHA；69条保有最大路径分解的记录没有hold命名单元，其余80点未宣称路径已验。synth→grt差异包含重映射、尺寸／缓冲及优化的综合作用，最大路径也可能换路；不能称正的纯repair成本，更不能统一加面积。Add／Mux／G未新增拟合，参数及逐源失败沿用v10。

## 上下文隔离补正

原v7—v10外层fold的enable函数已排除外层完整组，没有外层留出标签泄漏；但下游训练行使用了见过其自身组的上游函数，训练／留出上下文可能存在分布差异。本轮公共模块[nested_control_contexts.py](../../../arithmetic_dse/nested_control_contexts.py)同时排除外层组和训练行自身组。整个parent／reset／contrast家族和全部T一起隔离。

| 使用位置 | 上游enable训练排除 |
| --- | --- |
| 外层o，下游训练行来自r | o与r |
| 外层o的留出行 | o |
| 最终下游训练行来自r | r |
| 部署推理 | 继承冻结all-train函数 |

13完整组复用14个single／all-train上下文，新拟合78个无序pair上下文，共92个。固定上游算法为v9 linear／alpha1／joint_bank_path，无额外上游选模。1764条上游路由／lineage核对与3528条下游上下文数值核对通过。该设施用于离线训练，部署不按源身份或精确T路由。

## 预登记有限比较与拒绝

2种上下文×2种响应形式×3个alpha=12项；旧single方法只作消融、不可选。固定positive_log_linear／path目标；ratio以共享预测enable R为reference，不使用真实上游标签。选择仍用bank／path／service／native／zero／mixed的源等权minimax log-MSE，在nested方法中只选择一次。

| 方法 | 形式 | alpha | 选择损失 | 银行median | raw路径P95 |
| --- | --- | ---: | ---: | ---: | ---: |
| single，仅消融 | v10_direct_R | 0.1 | 0.05791340 | 18.6044% | 41.5581% |
| single，仅消融 | v10_direct_R | 1 | 0.05140496 | 18.4954% | 38.7097% |
| single，仅消融 | v10_direct_R | 10 | 0.05799867 | 18.7243% | 38.4399% |
| single，仅消融 | shared_enable_ratio | 0.1 | 0.06254519 | 18.7327% | 40.8534% |
| single，仅消融 | shared_enable_ratio | 1 | 0.06432543 | 18.9317% | 40.7318% |
| single，仅消融 | shared_enable_ratio | 10 | 0.12064918 | 18.3644% | 47.7286% |
| nested，可选 | v10_direct_R | 0.1 | 0.05947699 | 19.3163% | 41.2412% |
| nested，可选 | v10_direct_R（选中） | 1 | 0.05192463 | 18.4680% | 39.2594% |
| nested，可选 | v10_direct_R | 10 | 0.05727462 | 18.7060% | 37.8842% |
| nested，可选 | shared_enable_ratio | 0.1 | 0.06553848 | 19.2177% | 40.6767% |
| nested，可选 | shared_enable_ratio | 1 | 0.06641452 | 19.1571% | 38.6843% |
| nested，可选 | shared_enable_ratio | 10 | 0.12076469 | 18.1795% | 48.3551% |

| 预登记闸门 | 选中结果 | 结论 |
| --- | ---: | --- |
| 银行源聚合median≤15% | 18.4680% | 失败 |
| raw路径P95≤35% | 39.2594% | 失败 |
| 最大银行源误差≤v10的30.73945% | 30.3728% | 通过 |

**按预登记规则停止：不转选第二候选，不生成新C++价格，不消费旧回归。** 选中候选银行P95为26.2183%，raw路径median／max为9.8852%／81.4581%。v10同行银行median18.4954%、raw P9538.7097%；嵌套修正几乎未改变银行误差、尾部稍差，不能称物理模型已修复。

| train银行 | 选中候选银行源平均APE |
| --- | ---: |
| S-ab497c57b8a9bd6d | 23.7836% |
| S-d1c86c9df37b5fed | 8.2173% |
| S-b06e166f2485558e | 14.8993% |
| S-d0fb525b1fcecb5c | 20.2567% |
| S-aac8767d3e7162b7 | 11.8762% |
| S-0a68dde9ad49280a | 25.2986% |
| S-620a59735d28f0b0 | 18.4480% |
| S-f3640dcc5b463a0e | 16.1656% |
| S-82e16205d88fbe35 | 19.5831% |
| S-84531c295bbe4a40 | 30.3728% |
| new/S-58d75c10e5163b87 | 19.9068% |
| new/S-747c4fcf75971c48 | 25.7567% |
| new/S-d2b5eb46de2e0a01 | 16.5246% |
| new/S-def1d34460b5d530 | 19.2971% |
| new/S-f026472f0572933f | 17.6173% |
| repair/S-09ddf99a74e6cef4 | 18.4680% |
| repair/S-142b114d7d01f2a1 | 23.9386% |
| repair/S-a68466a8b3676042 | 12.6313% |
| repair/S-aa6ad846d04ce34a | 12.8963% |

这些是训练选模诊断，不是新验证或独立成绩。未重新拟合reserve／支持域；v10支持仍train63/63、outer完整33/63、因素6/6、旧9/15。实际算术S／shared、W6完整阶段资格没有由适配器取得。v10的Add17+9面积30.06%、47+63带消费者18.50%、Mux96时延27.56%、G56面积32.93%、train64 G面积19.33%等失败仍在。

## 复核与复现

在完整仓库中运行，不需要原绝对产物目录、ODB或EDA：

```bash
python3 -m experiments.arithmetic_dse.repair_burden_replay_v11
python3 -m unittest regression.test_nested_control_contexts
```

[便携回放代码](../../../arithmetic_dse/repair_burden_replay_v11.py)、[7项隔离测试](../../../../regression/test_nested_control_contexts.py)、[回放收据](replay.json)、[最终检查](checks.json)。7项测试检查外层／自身组标签不变性、家族与全部T隔离、pair对称、final训练／deployment区别、lineage篡改及非法角色／源。

便携回放核648真实路径／648删除实际Liberty弧负例、149个原物理标签点、63个重建语义银行、92个上下文／1764路由、3528下游上下文、12 trial的1512条路径统计及126次冻结候选数值推理，禁止数值推理读文件／启动子进程。未拟合或启动后端。710份仓库源码SHA及归档原文核对。

v10的43项分组测试、477特征／价格和native回放只继承未变707份源码身份及原收据；本轮没有重跑这些组，也没有新的native价格分支。不要把7项新测试和43项继承测试写成一次50项测试。

| 文件 | 内容与职责 |
| --- | --- |
| train-path-audit.json.gz／train-path-proof-cases.json.gz | 648保存路径、原始报告／点、实际弧与连线、108缺失条目 |
| train-operator-audit.json.gz／train-operator-labels.json.gz | 149点物理变化、原标签精确文本／SHA、路径覆盖界限 |
| nested-protocol.json.gz／nested-freeze.json.gz | 预登记12项、门槛、失败后停止规则及不可变数值依赖 |
| nested-inputs.json.gz／nested-contexts.json.gz | 126 enable与126 valid行、每银行一次语义、候选、92上下文 |
| nested-predictions-compact.json.gz | 全部12 trial LOSO、2×14组上下文、选中LOSO、runtime预测 |
| nested-train-report.json.gz／nested-lineage-proof.json.gz | 全trial、逐源指标、失败闸门与隔离收据 |
| inherited-v10-*.json.gz | 未变前驱上下文、身份、检查及回放收据，非新评价 |
| source-and-tools.json.gz／execution-logs.json.gz | 710份仓库源码、外置审计／拟合／包装工具与失败日志 |
| summary.json／identity.json／settlement.json | 结论、逐文件与源码SHA、0物理增量结算 |

原始1.2GiB开发预测文件保留仓库外；compact版去除重复spec／structure／directory／components，保留所有数值f／actual／predicted、source／role／fold／T及原文件SHA。异机回放仅使用包内文件，绝对路径只作来源追溯。所有入仓单文件≤10MiB。归档工具为追溯用途，不要求异机重新运行原拟合脚本。

初次路径审计因旧标签外置、初次算子审计因恢复标签的synth位置解析失败，原日志和当时工具保留；修正只读解析后通过，108条真实缺失继续列出。回放首轮在最终收据dict重复字段处失败，报告代码修正后重跑；没有修改冻结数值、补造标签或重跑物理。

## 资源与下一步

本轮synth／grt／final／support增量均0，无新标签／验证源、无物理失败／重跑；20独立算子源未读。累计Ledger3538／3507／16／22486，wall364379.1543315831s、CPU743575.33s，pending=0。policy v11／budget v5与4物理任务／各4线程8192MiB保持。未提交／推送。

下一轮先登记能被train证据证伪的机制假设和停止条件：native_valid研究共享缓冲、分支负载与setup预算；input_valid单独研究hold／clock。W3分开映射面积与物理变化，W5继续G面积／组合／多消费者。保留嵌套隔离设施，停止沿失败候选扩表或用已消费回归挑模；实际算术S／shared、W6及正式D／ABCD仍待。
