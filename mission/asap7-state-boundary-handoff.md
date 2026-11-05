# ASAP7状态／边界独立通过与组件发布交接

更新：2026-11-05T16:39:09+08:00。当前结果见[lxy-plan-fix.md第四章§7.34](lxy-plan-fix.md#step7-m2-state-boundary-independent-verdict)，采集／冻结与失败父链见§7.32–§7.33。ASAP7九例36条仍是当前交付目标，完整D尚未完成。

**72 train／36 validation／36新独立test均已完成。** 原始／Liberty／实际FF／SDC／RC／CTS完整CEC／费用回放后，对冻结参数执行一次独立评价，原门槛全部通过。

| 阶段 | 独立面积中位误差 | 独立面积P95 | 边界最小余量 |
| --- | --- | --- | --- |
| synth | 2.454918% | 6.146589% | 73.544834ps |
| grt | 6.401676% | 8.624627% | 105.182022ps |

原面积门槛中位20%／P95 50%不变；三个精确SDC下的冻结边界均覆盖独立最大H＋最大控制Q-D。冻结开销仍为synth334.157489ps／grt910.766404ps，50ps reserve、全部参数／支持域和SDC均未修改。375ps可能没有正数据预算，setup违例／负hold原始行保留，统计通过不表示所有银行物理可行。

发布文件：[asap7-state-boundary.json](../experiments/arithmetic/evidence/step7_m2_state_boundary_v1/asap7-state-boundary.json)，SHA256 `0cf99c9944f40aad7f4d4a2a9bb91afcbaf26048ad64d3e6131d5fcafc3bf904`。只发布ASAP7 grt受限合成valid_chain状态银行和原ABC1500ps／精确SDC40500、1500、375ps／IO0.2T；synth为通过的诊断。原12类组件字节不变。新模型拥有state／control、clock／tap及未归属repair面积，排除post-capture observer，后续整阶段不得重复计费。

[证据包说明](../experiments/arithmetic/evidence/step7_m2_state_boundary_v1/README.md)及publication／capabilities明确资格范围。便携核验：

```bash
python3 -B -m experiments.arithmetic_dse.model_m2_state_evidence verify \
  --folder experiments/arithmetic/evidence/step7_m2_state_boundary_v1
```

加`--external`核验本机原始大产物、Liberty和完整已存CTS状态图／CEC及收费祖先。144测量／288阶段／864路径的两种回放均通过；实际Git可见源副本禁读原build／工具／活账本、PATH为空且禁子进程时亦通过，压缩池字节篡改被拒绝。证据包约23.40MiB，没有ODB／对象／波形。verification.json绑定实际核验命令、文件及结清账本前缀。

唯一选择冻结仍为`f1f1d08c452e8a01062740cc41b4890d03d48c8cb725354fb895a8093283b7a9`；一次性独立verdict为`3dc22b0ec19f2cac3b299e1929a1fc0e6c1e1d5aff6372cbb3812455c13ccc62`。36项独立标签已消费，永久排除后续拟合、验证、算法／裕量／域选择；证据verify只回算原结论，不重新评价或选模。

原采集v1–v3的TAPCELL／单比特端口／日志同名失败及费用保留。v3曾覆盖两份v2支持command.json副本，实际覆盖字节、原成功manifest／日志／资源／账本与另付费失败记录均明确封存，不恢复、冒充或退款，物理结果不受该支持副本写入影响，详见拟合数据中的support_sidecar_reconciliations。

当前没有后台EDA或自动后继采样。旧独立状态入口仍可查询36／36完成：

```bash
python3 -B -m experiments.arithmetic_dse.model_m2_state_test status \
  --folder build/step7-state-boundary-20261105-independent-v1
```

后继顺序：先核对真实PipelineV2状态银行的typed位数／信号数、逐位复位、valid控制及共同目标域，取得原生state绑定；按用户确认方案冻结受限合成阶段拓扑的独立整阶段协议／资格，再补真实half／quarter区间、所需上下文和正式边界／目标，最终完成有效D选择与RTL周期闭环。不能把旧stateArea数量调用直接视作新模型资格，也不能从大小上限推断任意native银行支持。未覆盖继续拒绝，11类未变组件不重训。

全历史结清：synth1445／grt1423／final16／support5589，累计叶墙钟191682.702s／CPU437660.21s；pending／active／unsettled均0。full_D_ready=false、full_step7_complete=false，九例36条与688条未完成。未git add／commit／push。
