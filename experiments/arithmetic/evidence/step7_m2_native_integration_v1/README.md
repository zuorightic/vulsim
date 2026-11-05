# ASAP7发布组件接入原生D入口

本包证明已发布12类grt组件的生产原生读取、实际阶段／逻辑捕获边界查询、数值一致性及D候选覆盖诊断。模型参数／裕量／域未改；原发布模型SHA256为f49990d5aa68045a7127636e074d07f4140404b8b007c19b8f8b70bd16524e15。原独立资格及历史失败仍由父发布包保留。

436次原生查询覆盖12类及登记条件，与Python数值最大差0；14项拒绝检查、同节点4→2个Mux上下文变化、公共C++源码产生的真实PipelineV2双Mux阶段绑定均通过。原四平台250项检查及pipeline／reset／valid（含CIRCT）回归通过。

九例公共VUL→PipelineV2→新模型工厂→D入口实际产生21个按原顺序的候选尝试，均明确cost_uncovered，首个共同缺口为状态模型；三候选乘法中half／quarter另保留真实区间缺口。报告不把未覆盖改为预测不可行，不输出虚构D RTL，不代表36条实测。1500ps只用于接口诊断，未资格为正式九例目标；PPA调用0，无新拟合或标签消费。

便携核验：

```bash
python3 -m experiments.arithmetic_dse.model_m2_native_evidence verify --out experiments/arithmetic/evidence/step7_m2_native_integration_v1
```

增加`--external`核对当前原生源文件及父模型身份；两个模式都不运行编译器／EDA、训练或SAT。native目录保存436查询、3候选拒绝、实际双Mux阶段查询及C控制RTL；public-nine保存九例完整诊断，public-source保存相同公共VUL源码。source保存本次实际C++／Python实现快照，capabilities.json列明完成范围，verification.json另绑定Git副本与资源结算。

重跑接口回归：

```bash
python3 regression/arithmetic_published_primitives.py run --out build/asap7-native-new-run --circt-bin /path/to/circt/bin
```

重跑公共VUL覆盖诊断需要先构建vulrtlgen，再运行model_m2_native_coverage并给`--sources experiments/arithmetic/evidence/step7_m2_native_integration_v1/public-source`和新的`--out`目录。该命令预期保留九例未覆盖结果；不是正式案例PPA采样入口。

生产包仍缺少合格状态、边界和阶段组合模型，混合／单Mux与共享上下文、真实half／quarter区间及正式目标也未自动扩域。full_D_ready=false，九例D选择及RTL周期闭环、36条PPA均未完成。不要仅给JSON补默认字段或因旧模型profile相同就复用旧stage修正。
