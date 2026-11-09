# MAC32条件模型第一轮：软件、源角色与采样协议

2026-11-09。依据[修订计划第四章§7.57](../../../../mission/lxy-plan-fix.md#step7-target-round1-preparation)。本包交付本轮第1—3步的软件与协议准备；没有新物理优化、正式训练或独立物理模型标签评价。

- 需求：原3候选、44合法视图、19形状／63精确上下文，全部保留静态追溯；28项直接捕获、35项真实消费者。
- 源角色：63 train、12 validation、12 locked_test，完整局部图分组；另3个独立not_training容量源。所有目标、阶段和重复继承源角色。locked_test本轮只做功能软件验证，不读取物理标签。
- RTL：90个参数化壳×96周期，共8640次实际Verilator自检；连续输入、气泡、在途复位、无条件捕获通过，无Verilator告警。32项微型乘法独立整数核验另存。
- generic：Yosys无库lowering和check通过，90壳的launch／capture FF、独立银行、已知常量及直通端口投影可回放；没有把FF或mapped数量作为模型特征。
- 读取：独立节点每个动态输出的最大值、through-producer数据最小有符号slack、节点／状态／shared clock／root repair面积互斥。17项破坏拒绝；多输出、最差slack与节点最大值不同的见证、常量边界、层次内时钟buffer、未连接FF互补输出及TSV适配回放通过。全部数值为明确的synthetic_fixture。
- 采样：三区13点纯决策器，67条包含非单调及单区响应的轨迹、精确±10%边界、失败停止和11项错误拒绝通过；全部有效条件标签保留，无自动重试。

[覆盖清单](coverage.json)、[源角色索引](source-index.json)与[3源6目标容量方案](capacity-plan.json)可以直接审阅。完整特征、RTL、向量、状态／阶段静态需求、读取／扫描回放和最小源码运行时保存在两块内容池中，由manifest绑定。采样细则见[model_three_region_scan_v1.json](../../../arithmetic_dse/configs/model_three_region_scan_v1.json)，模型候选与新质量门槛见[model_target_round1_v1.json](../../../arithmetic_dse/configs/model_target_round1_v1.json)。这些门槛是本轮工程预登记，不追改旧模型的门槛或失败。

本包便携模式重生成实际RTL、回放8640个向量参考、generic FF／端口投影及读取／扫描性质。它保留实际自检testbench、命令与日志绑定，不冒充重新执行Verilator。完整约86MiB generic JSON在原build工作缓存；`--external`另核对其实际字节，重算完整generic几何与算术primitive census。物理ODB／CEC不属于本轮新产物。

```bash
python3 -B -m experiments.arithmetic_dse.model_target_round1_evidence verify \
  --folder experiments/arithmetic/evidence/step7_target_round1_v2
python3 -B -m experiments.arithmetic_dse.model_target_round1_evidence verify \
  --folder experiments/arithmetic/evidence/step7_target_round1_v2 --external
```

隔离回放从内容池恢复最小源码与输入，以`python -I -S`执行，PATH为空；审计钩子拒绝原home／项目／build读取和回放子进程。池内容篡改拒绝，原包不改。验收收据和资源结算见`publication-closure.json`。本轮首次RTL构建的消费者实例／信号同名错误及初步v1封包保持原字节和费用，v1移至build下provisional-evidence并登记迁移，不作为当前发布。

下一步是实际EDA执行器及mapped语义端口／FF银行别名解析，并在有限容量任务中核验新壳真实独立节点与through-data覆盖、常量／直通证书、SDC／ABC、工具／库和CEC，再重估正式批次时间与存储。当前`physical_endpoint_qualification=false`、`physical_admission_allowed=false`、`independent_test_allowed=false`、`full_D_ready=false`。纯决策函数、Tcl语法检查和synthetic reader通过均不授予物理标签资格。
