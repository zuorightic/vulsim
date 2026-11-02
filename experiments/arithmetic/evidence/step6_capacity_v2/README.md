# 步骤六32GiB容量后继

本包保留v2六任务、v3仅UDR三任务、v4完成包络与v5单任务时钟放宽的独立准入和结果。原8GiB失败、CPU_limit、综合timeout、1.5ns物理4小时timeout及费用全部保留；Yosys专用线程池缺口与纠正前后测量身份分开。F2原1500ps基准及两个synth控制完成，基准grt setup为负；UDR128在固定原ABC1500ps映射、100ns SDC／固定300ps I/O条件下以1671.486790秒完成新floorplan→grt，setup+21883.324219ps、hold+0.670713ps、覆盖完整，hold待工程复核。两项旧UDR synth控制仍not_run。容量、时序及批次准入分别判断，不向训练、标签或主矩阵扩用。完整原始运行目录按catalog本机留存，远程持久留存尚未确认。

后继冻结为`experiments/arithmetic/whole_graph_freeze_v2.json`；默认入口`python3 -m experiments.arithmetic_dse.whole_graph_evidence`，`--verify-external`要求实际读取大产物字节，缺失明确拒绝。软件C++执行由原源码和收据绑定，离线Python核验不冒充重新编译。最终索引集合以freeze绑定值为准，核验摘要说明其统计时点；每包≤5MiB、单文件≤1MiB。
