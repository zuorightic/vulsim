# W3／W4／W5局部银行共享与映射／物理面积拆分 v12

本轮完成两项机制假设的18项预登记train对照，三个选中候选均未通过门槛，已封存拒绝。没有转选第二候选、生成新C++价格版或消费旧回归。最近诊断价格仍为v10，v11和v12均不授予正式价格资格。

现行入口：[任务导航](../../../../mission/README.md)、[§7.111](../../../../mission/lxy-plan-fix.md#W345-local-sharing-factorized-area)。[前驱v11](../common_repair_burden_v11/README.md)的拒绝结果保持。

## 假设与实现

**S：捕获银行局部描述。** [local_bank_features_v12.py](../../../arithmetic_dse/local_bank_features_v12.py)仅从已验证的显式仿射语义计算当前capture bank的出生／保持比例、出生数据表达式等价类、原始／reset归一化后的别名比例、局部根极性集中度和分裂比例。出生表达式只用于计数，原始根ID、掩码和source不进入数值模型；kept FF保持彼此独立。仍限于仿射银行适配器，不代表任意算术S。

匹配OpenROAD `Rebuffer.cc`的SHA及源码原文已归档。`fullyRebuffer`逐负载注记slack、建立timing tree，再对每个driver的target slack回收面积，支持研究局部co-load，但不证明任何当前误差由该例程单独造成。线上没有实际电容、slack、buffer树或物理面积。hold观察的适用范围继续按v11，不外推到native_valid。

**W3／W5：两个可分验的面积函数。** [factorized_area_v12.py](../../../arithmetic_dse/factorized_area_v12.py)计算预测综合面积×预测grt/synth比例。映射函数用共享逻辑工作量作reference并拟合synth标签；物理函数直接拟合保存train的grt/synth正比值，输入只有语义特征和数值T，不输入真实或拟合的上游面积。因此没有训练行样本内上游预测作下游特征的问题。比例可小于1，对应真实面积回收；没有对G时延／区域残差增加负偏移。

**固定范围。** 53个Add点／18源、81个G点／27源；S仍19银行／63实现／126条native_valid路径。S继承v11的92个完整parent／reset／contrast嵌套上下文，新增上游拟合0。S两个形式、Add和G各两个形式，alpha均0.1／1／10，共18项；每个组件按登记损失只选择一次。S用bank／path／service／native／zero／mixed源等权minimax log-MSE；面积用grt／synth／比例三部分源等权minimax log-MSE。不能后见挑更好的单项median或换第二候选。

## 结果与门槛

| 组件 | 选中形式／alpha | median | P95 | 最大源误差 | gate结果 |
| --- | --- | ---: | ---: | ---: | --- |
| Add | compact_mapping／10 | 7.8348% | 14.1457% | 15.1463% | 拒绝 |
| G | compact_mapping／1 | 5.0716% | 16.5525% | 19.6244% | 拒绝 |
| S | local_compact／1 | 16.9584% | 30.1663% | 38.8918% | 拒绝 |

面积的登记门槛为median≤15%、P95≤35%，并额外要求每个源平均APE≤15%；后者用于保留逐源失败，是本轮候选推进条件，不改写项目总体median／P95合同。Add虽仅超出0.1463个百分点，也不放宽阈值。S要求银行median≤15%、raw路径P95≤35%、最大银行源误差≤v11的30.3728%。S三项均失败，raw P9536.7364%、max82.4524%。

| 组件 | 前驱同train median／P95／max | 本轮变化及限制 |
| --- | --- | --- |
| Add | 8.4388%／12.6404%／14.2904% | median改善，P95及最大源退化；未取得候选推进资格 |
| G | 3.7638%／13.9824%／19.3324% | median、P95及最大源均退化；三部分误差仍可互相抵消 |
| S | 18.4680%／26.2183%／30.3728% | median与raw尾部改善，最大银行显著退化；仍未解释关键物理对照 |

S前驱为v11嵌套方案；面积前驱为v10。旧验证未重读或重评，这些均为train选择诊断。biased valid T500实际银行差+178.288639ps，本轮仅预测+0.496400ps；uniform valid T1500实际−37.271485ps，仅预测−0.009797ps。局部共享统计能表达更多差异，仍不足以解释现有反例。

| 面积分量 | Add median／max | G median／max |
| --- | ---: | ---: |
| mapping | 5.1284%／24.2032% | 3.0455%／36.3373% |
| physical_ratio | 5.3119%／15.0988% | 3.6389%／48.0827% |

映射与物理比例必须分别验，不能只看乘积。G物理比例最坏源48.08%、映射最坏源36.34%，产品部分抵消；该形式没有消除已知问题。全部18项如下：

| 组件 | 形式 | alpha | 选择损失 | grt／银行median | grt最大源／S raw P95 |
| --- | --- | ---: | ---: | ---: | ---: |
| Add | compact_mapping | 0.1 | 0.01294051 | 8.6446% | 17.5310% |
| Add | compact_mapping | 1 | 0.01273221 | 9.1605% | 13.4406% |
| Add | compact_mapping | 10 | 0.01152279 | 7.8348% | 15.1463% |
| Add | incumbent_geometry_mapping | 0.1 | 0.01210546 | 7.1468% | 18.8820% |
| Add | incumbent_geometry_mapping | 1 | 0.01384708 | 8.8964% | 17.6343% |
| Add | incumbent_geometry_mapping | 10 | 0.01183453 | 8.8709% | 13.9220% |
| G | compact_mapping | 0.1 | 0.01408326 | 6.4472% | 24.8316% |
| G | compact_mapping | 1 | 0.01210098 | 5.0716% | 19.6244% |
| G | compact_mapping | 10 | 0.01218189 | 4.6401% | 20.7909% |
| G | incumbent_geometry_mapping | 0.1 | 0.01445287 | 3.8334% | 19.3783% |
| G | incumbent_geometry_mapping | 1 | 0.01453093 | 3.9493% | 19.7902% |
| G | incumbent_geometry_mapping | 10 | 0.01691849 | 4.7909% | 25.5885% |
| S | local_compact | 0.1 | 0.05701258 | 18.8747% | 35.8745% |
| S | local_compact | 1 | 0.05363511 | 16.9584% | 36.7364% |
| S | local_compact | 10 | 0.08248647 | 17.5963% | 40.4324% |
| S | v10_plus_local | 0.1 | 0.07421549 | 20.9024% | 45.6273% |
| S | v10_plus_local | 1 | 0.05399777 | 18.8620% | 40.0995% |
| S | v10_plus_local | 10 | 0.05505126 | 18.6502% | 38.4133% |

逐源失败（完整逐源数据见train-report）：

| 组件 | train源 | 选中候选源平均APE |
| --- | --- | ---: |
| Add | operator-3b03a3d382938143 | 15.1463% |
| G | G-4d624e640e05dfbf | 15.9913% |
| G | new/G-a4736d1f1d9438c7 | 16.7930% |
| G | repair/G-f5bf5f9e3e7d766b | 19.6244% |
| S | S-ab497c57b8a9bd6d | 21.6359% |
| S | S-b06e166f2485558e | 16.2720% |
| S | S-d0fb525b1fcecb5c | 17.3771% |
| S | S-aac8767d3e7162b7 | 16.4724% |
| S | S-0a68dde9ad49280a | 25.9139% |
| S | S-620a59735d28f0b0 | 18.3742% |
| S | S-82e16205d88fbe35 | 19.8956% |
| S | S-84531c295bbe4a40 | 29.1968% |
| S | new/S-58d75c10e5163b87 | 24.6464% |
| S | new/S-747c4fcf75971c48 | 25.5790% |
| S | new/S-d2b5eb46de2e0a01 | 15.3579% |
| S | new/S-def1d34460b5d530 | 16.8873% |
| S | new/S-f026472f0572933f | 15.0636% |
| S | repair/S-09ddf99a74e6cef4 | 16.9584% |
| S | repair/S-142b114d7d01f2a1 | 38.8918% |

## 复核与上下文边界

```bash
python3 -m experiments.arithmetic_dse.local_sharing_replay_v12
python3 -m unittest regression.test_local_bank_v12
```

[回放实现](../../../arithmetic_dse/local_sharing_replay_v12.py)、[测试](../../../../regression/test_local_bank_v12.py)、[回放收据](replay.json)、[最终检查](checks.json)。6项新增测试检查极性归一化、kept FF独立、后级出生不影响前级、根重命名／word重排、矛盾语义拒绝，以及面积推理无实测值／文件／子进程。

回放重建134个面积Query的特征、63个语义银行和1764条嵌套下游上下文，重算18项的1560条逐trial统计及一次选择／门槛；核134次面积推理、126次最终训练上下文推理、126次真正部署上下文推理，714份仓库源码SHA及归档原文。数值推理禁止文件读取／子进程，回放不拟合也不调用后端。v11的648条路径／删弧证明及7项测试、v10的43项测试／native收据按未改源码身份继承，未称本轮重跑。

**冻结输出命名修正。** 原始predictions中S.runtime_train实际使用最终训练的out-of-group上下文，不能称部署推理。保持原拟合文件／数值freeze不变，在deployment-cases中另外生成all-train enable上下文的126个部署见证并核对；两种上下文分别计数，不能混用其数值或资格。

| 文件 | 内容 |
| --- | --- |
| protocol／freeze／candidate.json.gz | 18项预登记、固定门槛、数值冻结和被拒绝候选 |
| train-inputs／predictions／train-report.json.gz | 134面积点、14组S上下文、全trial预测与逐源结果 |
| deployment-cases／post-freeze-audit.json.gz | 真正部署上下文见证、对照差值及逐组件失败 |
| source-audit.json.gz | 匹配OpenROAD Rebuffer完整源码、SHA及解释范围 |
| inherited-v11-*.json.gz | 前驱身份／收据、语义银行、92上下文和149点原审计 |
| source-and-tools／execution-logs.json.gz | 714份仓库源、外置工具、测试及失败日志 |
| summary／identity／settlement.json | 结论、文件／源码SHA、零物理增量账本 |

入仓单文件≤10MiB；异机回放仅用仓库与包内文件，无需原绝对产物路径或EDA。拟合与数值依赖保持冻结，没有因回归修改参数／支持／reserve／标签／发射器。审计补核初版把旧files字典按列表遍历而失败，修正只读解析后通过，原日志保留；没有重新拟合或重跑物理。

## 资源与后继

新增synth／grt／final／support均0，新增标签／验证源0；20独立算子源未读。Ledger仍3538／3507／16／22486、wall364379.1543315831s／CPU743575.33s、pending=0，policy v11／budget v5保持。未提交／推送，公共D未变，实际算术S／shared及W6完整阶段仍待。

本轮否定了“这些局部矩足够解释valid对照”和“简单面积两段拟合足够稳定改善”的假设。下一步先查有效映射共享／缓冲分支的不连续来源及可预测范围，必要时登记少量train对照检验实现敏感性；不继续在已失败形式上扩alpha网格或用旧回归换候选。
