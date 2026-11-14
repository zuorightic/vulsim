# W3／W4／W5：极性覆盖与控制分支预算 v15

本轮检验ABC正／反相共享是否解释v14面积缺口，并从四个已保存grt检查点只读提取S的逐端点时序／分支负载。**没有推进价格。** 两个固定面积候选全局train门槛通过，但较v10没有改善，零压缩G关键域仍失败。S交付测量与连接证明，没有新的拟合或发射前代理精度声明。

现行记录见[计划§7.114](../../../../mission/lxy-plan-fix.md#W345-polarity-control-budget)。外部原始产物根为`/home/zyrv/vulsim-artifacts/W345-polarity-budget-20261115-v15`；本目录可脱离该目录和OpenROAD安装回放。

## 算术实现与有限对照

[phase_cut_cover_v15.py](../../../arithmetic_dse/phase_cut_cover_v15.py)按`(语义节点, 极性)`分别计引用和选择合法门，允许下游用反相门吸收输入极性。主要依据是匹配ABC `giaNf.c`中的双极性match、反相和引用计数。固定沿用v14的76个合法单输出库门、K=4、每节点16 cuts、三次area-flow；没有扩大cut或alpha网格。输出反相仍显式付费，输出保持原语义。它是逻辑工作量代理，不是实际ABC重写／时序映射。

复用Add53点／18完整组、G81点／27完整组。所有T共同留出，v13重复／变体不进入拟合。每族只有一个固定direct模型，alpha=1；拟合特征列表与v14 direct相同，只替换cut reference及其计数。共两项trial，无形式选择或次选。正的synth/reference和grt/reference函数分别拟合，grt/synth由两者导出；三个分量均检查源聚合median≤15%、P95≤35%，关键域另报。这里继续使用v14的诊断数值消费接口，没有新C++价格或公开资格。

| 量 | Add median／P95／最大源 | G median／P95／最大源 |
| --- | --- | --- |
| v15 grt面积 | 8.4586%／17.5696%／23.6357% | 5.2494%／18.6971%／36.2809% |
| v15 synth面积 | 5.2659%／26.7958%／30.7160% | 7.3658%／33.9961%／71.7398% |
| v15 grt/synth | 5.4731%／17.2134%／21.3171% | 4.2961%／17.4335%／42.7296% |
| v10 grt诊断基线 | 8.4388%／12.6404%／14.2904% | 3.7638%／13.9824%／19.3324% |

以上是源内先平均各T的APE，再在源之间聚合。零压缩G六源18点的grt为15.2705%／32.1250%，synth为16.2918%／63.7561%，ratio为7.3806%／37.2090%，关键域没有取得资格。稀疏G64的未校准reference从v14的45.18342变为45.35838um²，实际synth仍为28.98504um²；按极性共享没有解释主要差距。

45个prospective图提取合计24.16秒、单图最大3.00秒；这是软件工作量。预登记、原始逐T预测和决定分别见[intent](intent.json)、[area-protocol](area-protocol.json.gz)、[area-report](area-report.json.gz)、[area-predictions](area-predictions.json.gz)、[decision](decision.json)。

## S逐分支证据

四个检查点沿用v13两S父源各repeat／variant的train机制职责，均在同一完整排除家族中。只读加载同一grt ODB／SDC／Liberty／RC，重算已有全局布线寄生，不执行综合、优化、布局或布线。每份从native valid出发，取得640个数据D与一个valid D的最差setup路径；原有641个sink边界完全保留。逐段检查实际net和Liberty timing arc，valid R与原记录核对。

对选中路径，端点required由arrival＋slack得到。某分支的预算是端点required减该分支至端点的选中尾部时延，再减root arrival；多个端点经过同一分支时取最紧预算。分支定义为沿路径经过缓冲／反相器后的首个非缓冲输入。它是**以该root为条件、在最终检查点测得的预算**，不是Rebuffer优化当时的内部预算，也不是不限定root的vertexWorstSlackPath。几何量为实例原点的Manhattan距离，不是引脚坐标、布线长度或在线特征。

| 源／实现 | valid R（ps） | 最差数据R（ps） | 首分支引脚电容和（fF） | 分支预算median（ps） |
| --- | ---:| ---:| ---:| ---:|
| d0fb525b repeat | 261.670334 | 499.275524 | 475.959190 | 311.809246 |
| d0fb525b variant | 335.516235 | 498.135991 | 428.396285 | 300.543105 |
| aac8767d repeat | 439.958973 | 497.183309 | 482.533309 | 304.864037 |
| aac8767d variant | 314.848190 | 498.590350 | 463.759258 | 311.592605 |

两组最差数据R只变化−1.14／+1.41ps，valid R变化+73.85／−125.11ps；总首分支引脚电容两组都下降，valid R却方向相反。valid本支的引脚电容四份均为0.483326fF，其端点预算只增加3.43／9.03ps。由此可见，本局部对照不能只由总负载或单个valid负载大小解释；需保留各分支的预算和共享关系。四份最终布局的描述仍不足以证明哪条修复命令造成差异，不能将测得的坐标、电容或预算直接放入线上函数。

核查实现为[control_branch_budget_v15.py](../../../arithmetic_dse/control_branch_budget_v15.py)，完整逐分支表及可重算输入见[S-budget-audit](S-budget-audit.json.gz)、[S-budget-inputs](S-budget-inputs.json.gz)、[S-comparisons](S-comparisons.json)。两父源属于同一排除家族，未把四份实现当作四个独立源拟合新S。

## 失败、恢复与费用

第一次只读pilot因OpenSTA `report_units`不接受Tcl重定向参数失败并停止。新恢复批次改用既有tee输出习惯；第二个pilot在STA规范化名与ODB保留转义括号的实例名关联处失败并停止。最终另登记v3批次，逐实例导出几何、在Python规范化后关联，四份全部完成。两个失败均保留原脚本、准入、资源收据和费用；原批次未执行的任务没有自动重试。各次准入均绑定确切ODB／SDC／库／二进制／脚本，单任务4线程／8192MiB／120秒，串行执行，checkpoint哈希前后不变。

软件准备还保留一个合成测试库缺少原生XNOR导致“应有极性收益”断言失败的记录；补齐相应测试门后通过。数值冻结后仅加强witness校验，拒绝伪造自引用wire及非法极性；cover／枚举／phase_truth的AST未改，原协议、输入和候选未重写，回放重算全部映射，见[verifier-recovery](verifier-recovery.json)。

[settlement](settlement.json)记录本轮新增**6 support（4成功、2失败），0 synth／grt／final**，wall11.108697s、CPU12.14s，pending=0。累计3546 synth／3515 grt／16 final／22558 support，wall364977.087278s、CPU744690.68s。共享Ledger及快照已按全部历史结算更新。没有新独立源，20个算子独立源仍锁定；旧已消费验证未读。

## 便携验证与后继

```bash
cd /path/to/vulsim
python3 -m unittest regression.test_phase_cut_cover_v15 regression.test_control_branch_budget_v15 -v
python3 -m experiments.arithmetic_dse.polarity_budget_replay_v15
```

7项新增测试覆盖随机重汇合图穷举、极性共享、进位／稀疏尾部、引脚相位变换、自引用／非法相位／面积负例，以及分支共享、连线／Liberty弧／时序恒等式／端点／几何负例。回放从语义Query重建45个图，重算134条纯特征和推理、两项固定trial的45个完整组留出拟合，并重验四份S的2564条端点路径及故意破坏的路径。计算区禁止文件读取和子进程；证据加载在计算区外进行。实际数量见[replay](replay.json)与[checks](checks.json)。

源／工具文本与SHA在[source-and-tools](source-and-tools.json.gz)，原始Tcl输出、成功／失败日志及准入在[support-records](support-records.json.gz)，[identity](identity.json)绑定便携输入和当前通用实现。无需外部绝对路径即可回放。

W3／W5后继继续定位整体重写／重平衡与时序驱动映射中的差异，按极性共享本身未解决问题。S后继需先提出可在发射前计算的逐分支预算／共享描述，并对其代理误差作训练家族隔离核验，不能将本轮实测描述变成价格输入。v10保持最近诊断价格，生产发射器、S支持／reserve和公共D不变；实际宽深算术S／shared、G组合／多消费者与W6完整阶段继续待验。
