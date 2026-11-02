# 修订步骤六：实际结构报告

本包保存176份实际编译输出的结构报告和RTL，以及CIRCT/其他三个profile共24份代表报告、43份公开VUL嵌入核报告与实际wrapper。五份shared-helper诊断的旧执行RTL单列，只有源码位置注释差异；实际图、级号、协议及RTL逻辑不变。图与周期证据由同一whole_graph_freeze_v1绑定，不以当前重生成代替历史图。

冻结为`experiments/arithmetic/whole_graph_freeze_v1.json`，继承步骤五v3及所有旧冻结。核验：`python3 -m experiments.arithmetic_dse.whole_graph_evidence`；`--verify-external`要求实际读取catalog中的大产物，缺失明确拒绝。本包不代表步骤六全范围或D模型完成。最终保护集合以冻结绑定的index为准，核验摘要先于最终索引的文件数不冒充最终口径。每个新包目标≤5MiB、单文件≤1MiB。
