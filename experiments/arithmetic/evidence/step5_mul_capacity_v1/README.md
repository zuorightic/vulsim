# 步骤五有限容量：ASAP7 64/128位选中C

本包只对应[软件验收后的两个准入探针](../step5_mul_templates_v1/README.md)，任务/RTL/选中报告/profile/SDC/ABC及资源包络在执行前冻结。它不是主案例目标或D模型样本，没有原始/拆分同结构配对PPA，不能用面积/周期差宣称选择收益。

`summary.json`保留每次实际状态/指标/失败，原manifest压缩保留；`W64/W128`含原始RTL、单元表、路径/单位/覆盖/面积/STA及实际SDC，便携检查能重算这些数据。完整网表/实例表/全日志的目录见`artifact_catalog.json`。只读`step5_evidence`会明确标注该层未请求；`--verify-external`必须实际取得归档并核对每个成员。未选定持久远程地址，不能把本机ignored缓存当作已发布交付。

grt使用估算寄生，TT setup与hold分开解释；没有final提取/SPEF、布线DRC或多角签核。若超时/工具失败，保留实耗与已完成阶段，失败grt不能用synth指标代替，受影响规模的物理批量仍需容量复审。
