# ASAP7 M2基础算子首轮独立失败封存

本包保存完整56项F4测试、488行阶段标签及冻结模型的数值评价，不是可发布模型。
grt／synth均8／12操作通过；失败来自逐操作错误可行预测门槛，发布清单为空。
F4及更早测试永久排除后继拟合、验证、算法／裕量选择。原门槛与冻结参数不追改。

便携数值核验：
`python3 -m experiments.arithmetic_dse.model_m2_failure_evidence verify --folder experiments/arithmetic/evidence/step7_m2_primitives_failure_v1`

本机完整外部回放：给上述命令增加`--external`。该模式重新读取全部56项原始报告／SDC／Q-D／银行／core面积／LEC和费用父链，不启动EDA。
便携包不含ODB、AIG二进制或完整物理日志，不将数值回放冒称重新执行SAT证明。
