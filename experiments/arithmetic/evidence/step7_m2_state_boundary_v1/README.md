# ASAP7状态银行／边界独立资格

72 train／36 validation／36新独立test，全部原始采集和冻结参数评价通过。
grt状态总面积独立误差中位6.401676%、P95 8.624627%；synth诊断为2.454918%／6.146589%。
原面积门槛20%／50%及边界冻结规则保持；grt三个精确SDC的边界覆盖全部通过，最小裕量105.182022ps。

发布asap7-state-boundary.json只含grt，控制家族valid_chain、受限合成状态银行、ABC1500ps／精确SDC40500、1500、375ps／IO0.2T。
面积包含状态／控制和时钟／物理／未归属repair，排除独立post-capture observer；不能再计为算术面积。
375ps可能没有正的数据预算，质量通过不表示任意该目标阶段可行。
原生state绑定、算术阶段／正式I/O边界、整阶段模型和完整D尚未取得资格。

便携核验：`python3 -B -m experiments.arithmetic_dse.model_m2_state_evidence verify --folder experiments/arithmetic/evidence/step7_m2_state_boundary_v1`

加`--external`核对本机原始大产物、Liberty、完整已存CTS状态图／CEC与费用。
便携模式重提取144份银行的原始文本数值并重算既有结论，不执行SAT、训练或EDA，不依赖build或外部工具。
两种模式都不重新消费独立测试或重选模型。独立标签已消费，永久排除后继拟合／验证／算法、裕量或域选择。

v1–v3失败及费用保持；v3日志别名覆盖两份v2支持命令副本的实际字节、原成功manifest／日志／资源／账本及另付费失败链均明确保留，见fitting-data中的support_sidecar_reconciliations。
旧发布组件和原冻结字节不覆盖。Git由用户提交。
