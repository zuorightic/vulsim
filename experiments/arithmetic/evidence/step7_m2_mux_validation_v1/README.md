# Mux训练／验证未通过检查点

120个新train／validation任务全部完成，768行合法拟合标签已回放；48个新独立任务仍锁定，没有消费。
首版grt P95为79.0365%，原候选池整类选择后为79.0148%，都超过原75%门槛；synth和面积通过，11类固定资格保持。
本包只回放冻结数值与有限候选池诊断，不冒称独立测试完成、原始大产物便携回放或完整D就绪。

`python3 -m experiments.arithmetic_dse.model_m2_mux_validation_evidence verify --folder experiments/arithmetic/evidence/step7_m2_mux_validation_v1`

增加`--external`从本机原始产物重新提取全部合法train／validation与分路径观测，不启动EDA，不读取旧独立Mux标签。
