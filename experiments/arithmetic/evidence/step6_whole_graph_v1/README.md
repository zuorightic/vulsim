# 修订步骤六：整图软件与RTL验收

本包存176实现清单、源码增量、独立参考/周期trace、全部新收费及命令收据。实际BEIR/RTL在相邻step6_graphs_v1包；两项失败物理与4项暂停控制点在step6_capacity_v1。默认入口重算图/调度/固定成本/选择/安全除数和全部保存trace，无需build/EDA；C++执行只以绑定源码及实际收据证明。

冻结为`experiments/arithmetic/whole_graph_freeze_v1.json`，继承步骤五v3及所有旧冻结。核验：`python3 -m experiments.arithmetic_dse.whole_graph_evidence`；`--verify-external`要求实际读取catalog中的大产物，缺失明确拒绝。本包不代表步骤六全范围或D模型完成。最终保护集合以冻结绑定的index为准，核验摘要先于最终索引的文件数不冒充最终口径。每个新包目标≤5MiB、单文件≤1MiB。
