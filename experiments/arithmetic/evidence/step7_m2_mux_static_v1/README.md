# ASAP7 Mux静态上下文独立资格与组件发布

冻结参数的一次性P4评价通过，grt组件12／12合格；原F5整体失败保持。
新Mux只独立验收parallel_dynamic_mux、原精确位宽／ABC-SDC及生产单捕获银行。
mixed-control新系数、任意阶段／共享／混合算术／状态／区间及完整D仍未合格。

便携回放：`python3 -m experiments.arithmetic_dse.model_m2_mux_static_evidence verify --folder experiments/arithmetic/evidence/step7_m2_mux_static_v1`

增加`--external`核验本机原始大产物与完整已存CEC，再重新提取合法拟合和P4标签。两种模式均不启动EDA或重训；便携模式不重新执行SAT。240份测量中只消费Mux主标签，共1152行；其他控制标签仅核对原始阶段完整性。11类保持原模型／域／裕量及F5合格收据，原F5封存包仍是其原始证据来源。

可部署组件模型保存于`asap7-primitives.json`；`publication.json`和`capabilities.json`明确发布范围与未完成项。独立P4标签已经消费，永久排除后续拟合、验证和算法／裕量／域选择。Git提交由用户执行。
