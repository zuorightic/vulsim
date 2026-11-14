# W3／W4／W5：共享DAG cut及控制连接，v14

本轮交付纯软件的共享cut工作量代理、4项封存train面积对照，以及S重排前后的缓冲无关连接核查。**没有推进价格：** 新Add／G的全局train门槛通过，但grt median／P95均较v10退化，零压缩G关键域仍失败；没有读取旧回归或20个锁定独立源。S没有新拟合。生产发射器、支持、reserve、v10诊断价格与公共D均未改变。

现行记录：[计划§7.113](../../../../mission/lxy-plan-fix.md#W345-shared-cut-control-connectivity)。外部原始产物根为`/home/zyrv/vulsim-artifacts/W345-cut-cover-20261114-v14`；下面的回放无需该目录或OpenROAD安装。

## 实现及有限规则

[共享cut覆盖器](../../../arithmetic_dse/prospective_cut_cover_v14.py)从语义prospective Boolean DAG出发，使用真实ASAP7 dont-use过滤后的76个单输出门及其truth／pin置换。固定K=4、每节点16 cuts、3次area-flow；允许共享内部逻辑保留为一个独立映射根，同时被另一cut吸收，按所选根唯一计面积。显式输出反相有独立面积，不使用被禁用的HAxp5或不合法多输出门。

该实现借鉴实际ABC `&nf`的cuts／引用计数和面积回收，**未复刻**ABC的`&syn2`／`&if -g -K 6`重写、时序约束、pin电容和sizing。因此得到的是工作量参考，不能直接当映射网表、最优面积或物理预测。源码依据和实际ABC脚本在[source-audit.json.gz](source-audit.json.gz)。OpenROAD逐load预算及重缓冲源码同样只作机制依据，保持只读。

[面积消费](../../../arithmetic_dse/cut_area_model_v14.py)为封存的train诊断函数。Add53点／18源组、G81点／27源组，所有T按完整group共同留出。每族仅两种形式、alpha固定1：direct分别预测synth/reference和grt/reference；factorized预测synth/reference与grt/synth。按grt、synth、ratio三个分量的源等权log-MSE最大值选一次。三分量各自源聚合median≤15%、P95≤35%是全局train闸；逐源和关键域另报，不能由全局成绩授予关键域资格。

- 协议SHA256：`d3d999c2b903a495842a21b32ddd73df70b45f39884923938066da868868bdd2`。
- 候选SHA256：`0a8e402ad1f8c81d8a4d4ac3a125b09f6e30b2c7813fa168a6f717dba08efbe4`。
- 45个不同prospective图、134个train点、4项有限trial，无次选和alpha／cut扩网格。
- v12的拒绝和最大源门槛保持原实验身份；本轮是新的实现／协议，不恢复旧候选。

## 面积结果与未解决失败

所有表格为各源内各T的平均APE，再在源之间聚合。两族均选direct；synth及ratio同时保留，防止误差抵消。

| 量 | Add median／P95／最大源 | G median／P95／最大源 |
| --- | --- | --- |
| v14 grt | 8.6190%／16.9243%／19.8169% | 4.0186%／16.4002%／23.0936% |
| v14 synth | 4.7992%／25.8902%／31.5242% | 5.3035%／33.1197%／52.5358% |
| v14 grt/synth | 5.2552%／17.9008%／22.0727% | 3.6764%／16.2568%／37.5897% |
| v10 grt诊断基线 | 8.4388%／12.6404%／14.2904% | 3.7638%／13.9824%／19.3324% |

v14全局门槛通过，但没有改善v10。零压缩G六源18点的grt为15.2345%／21.5324%，synth为15.2820%／48.9784%，分别仍有median和P95失败。不能用全局G的4.02%代替关键域15.23%，也不能用grt/synth相乘抵消synth最大源52.54%。逐源表、所有4项结果及原始逐T预测在[train-report](train-report.json.gz)、[predictions](predictions.json.gz)和[post-selection-audit](post-selection-audit.json.gz)。

未校准的参考变化也未解释主要缺口：

| train例 | 旧exclusive cover | 新共享cut reference | 实际synth／grt（um²） |
| --- | ---:| ---:| ---:|
| Add6+10→11，T500 | 5.90490 | 5.86116 | 5.70078／5.55498 |
| G64＋低8位＋列24的8位，T1500 | 47.92446 | 45.18342 | 28.98504／28.54764 |

参考值不是拟合价格。合法共享cut表达能力已补齐，但保留prefix图后的局部覆盖仍不足以描述ABC整体重写／平衡。没有按这个结果扩K或重试选模。

## S连接结果

[机制模块](../../../arithmetic_dse/mapped_logic_fingerprint_v14.py)只处理已保存的离线连接，不提供线上价格特征。复用v13两S父源的repeat／variant，在synth和grt共8份网表，从`native/valid_1…/QN`沿实际nets和Liberty弧，到640个数据D和1个valid D。每组两stage的641个sink集合及全部逐sink缓冲无关表达式相同。

| T500源 | repeat→variant grt的buffer／inverter数 | 继承的valid R变化 |
| --- | --- | --- |
| d0fb525b | 21→15 | 261.670334→335.516235ps |
| aac8767d | 15→19 | 439.958973→314.848190ps |

每份前向cone均1604个非buffer／inverter单元，synth buffer／inverter均142。该统计含observer分支，只作同范围比较，不是S面积所有权或电容负载。归一化只消wire buffer、双反相及基本交换；相同结果不声称一般图同构或Boolean等价。结合已证明的v13等价／时序证据，这排除仅由缺失sink数量或本归一化D表达式变化解释重排对照的假设；固定发射仍可复现，不推出标签不可学习。

连接、库函数及所有比较都在[S-logic-audit](S-logic-audit.json.gz)和[可重算输入](S-logic-proof-inputs.json.gz)中。v13物理／路径证明不重新运行，身份与完整家族隔离沿用[前序证据](../common_implementation_sensitivity_v13/README.md)；这些重复／变体没有加入本轮拟合。

## 验证与回放

```bash
cd /path/to/vulsim
python3 -m unittest regression.test_prospective_cut_cover_v14 regression.test_mapped_logic_fingerprint_v14 -v
python3 -m experiments.arithmetic_dse.cut_cover_replay_v14
```

9项新增测试覆盖随机重汇合多输出DAG穷举、真实进位和稀疏尾部、共享cut重叠、pin置换、输出反相及truth／面积／边界／连接负例。回放只需仓库Python和NumPy，不启动EDA或C++：重建45个prospective图，精确核88856个局部cut及45个truth变异负例；重新提取134条Query特征、核134次选中候选推理、重算90个完整源组trial拟合，核8份S连接和8个破坏valid传播负例。计算区同时禁止文件读取与子进程，加载证据与身份检查在计算区外进行。

首版库准备的文件名错误、过严的软件表示断言，以及回放tuple经JSON变为array的比较错误均保留在[准备失败](preparation-failures.json.gz)、[回放修复](replay-recovery.json.gz)和[执行日志](execution-logs.json.gz)。这些修复均没有改训练协议、参数、标签或后端结果。

[source-and-tools](source-and-tools.json.gz)收录仓库源／配置和外置工具的文本及SHA；[identity](identity.json)绑定各证据文件和实现身份。NumPy只用于离线封存trial重算；价格推理不拟合、不启动进程、不读取文件。此处没有Python／C++新价格一致性声明，因为未推进新C++价格。

## 成本与后继边界

[settlement](settlement.json)的before和after完全相同：新增synth／grt／final／support均0，0新标签／验证源，20独立源未读。45个prospective图的提取时间合计17.25s、最大单图2.18s；它是软件耗时，不计为物理调用。共享Ledger、既有费用历史与snapshot均保留。

S支持／reserve／R／H、G时延、Mux、生产发射器及公共D不变，v10仍为最近诊断价格。后继优先检验实际ABC重写／平衡与prospective图的差异，S则检验发射前分支预算／布局代理及其误差；实际宽深算术S／shared、组合／多消费者与W6完整阶段继续待验。
