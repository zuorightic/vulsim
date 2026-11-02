# 修订步骤六：有限容量与暂停控制点

准入只有ASAP7指定UDR128_C/F2_C各一次synth→grt及每项两个仅synth条件控制。实际仅2 synth：UDR128触及8GiB，F2综合命令退出0后被旧层次端口读取器误报；原manifest与空metrics保留。后继静态SDC检查通过，未增加STA/grt/自动重试；4控制点均not_run。不能作为训练、目标标签、主矩阵或整体时序可行证据。完整本机归档按artifact_catalog逐成员登记，远程持久留存未确认。

冻结为`experiments/arithmetic/whole_graph_freeze_v1.json`，继承步骤五v3及所有旧冻结。核验：`python3 -m experiments.arithmetic_dse.whole_graph_evidence`；`--verify-external`要求实际读取catalog中的大产物，缺失明确拒绝。本包不代表步骤六全范围或D模型完成。最终保护集合以冻结绑定的index为准，核验摘要先于最终索引的文件数不冒充最终口径。每个新包目标≤5MiB、单文件≤1MiB。
