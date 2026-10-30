# 步骤三SDC单位修正与重验

原`backend_freeze_v5.json`四平台验收已撤回：Tcl对整数20/1000、5/1000、100/1000、25/1000执行整数除法，三个ns平台的实际SDC因而把clock uncertainty/transition写成0。旧便携核验只检查报告、平台身份和资源，没有解析实际SDC，不能证明这些约束正确。

本目录随`backend_freeze_v6.json`提供后继证据。`previous_acceptance_audit.json`逐一审计原15次尝试中的30份实际阶段SDC：10个ns平台尝试的23份SDC无效；ASAP7的7份SDC不受影响。原始尝试的状态、报告、SDC、SPEF、源码和计费逐字节保留，作废状态在本后继索引单列，不覆写原manifest，不将作废时序作为训练/评价标签。原6条工具/解析失败也保留。

修正对公共SDC中的周期、setup/hold uncertainty、transition、显式I/O delay及output load全部使用`double`除法。`sdc.py`静态读取实际OpenSTA write_sdc产物，不执行归档Tcl，逐阶段检查两时钟周期、setup/hold不确定度、transition、全部reset/valid/data端口的min/max I/O延迟、驱动和负载；未知约束、例外路径、重复约束和遗漏端口明确拒绝。实际write_sdc默认保留4位小数，因此只允许半个最末小数单位的序列化误差，正约束变为0明确拒绝。GF180的13.43fF在pF序列化为0.0134pF，原值与这项已知精度分别记录；不将其解释为整数截断。

三个受影响平台均以新任务ID重验同一小加法核到grt及同一32×32→64乘法核的synth/grt/final，原profile/RTL/周期保持。每个阶段在继续后续物理阶段前解析其实际SDC，manifest保存语义检查与SDC哈希。ASAP7不新增物理调用，继承经过全部阶段SDC重新核对的`asap7-mul-finalinterface`，该继承显式绑定原v5证据。

`admissions/`是本次独立六任务有限清单，预留6 synth/6 grt/3 final及support，保持原全局策略v5、2线程、单物理任务、8GiB限制；与原完整账本连续结算，失败不退款、不自动重试。`runs/`保存新实际产物，`commands/`保存逐叶命令/日志/GNU time；`resources.json`及before/after账本记录此次和累计资源。生成/功能输入继承原冻结的共同探针及其软件/原生10000周期检查，本次没有编译器/RTL语义改动或重复生成。

`source_v6/`绑定本次活动实现，`previous_source/`只作为被替代的v5源码审计快照；原`step3_platforms_v1/`及全部旧freeze不改字节。当前入口没有旧错误转换模式。

从仓库根目录只读核验，无需build、EDA、Tcl或网络：

```bash
python3 -m experiments.arithmetic_dse.platform_evidence
python3 -m experiments.arithmetic_dse.platform_evidence --verify-external
python3 -m experiments.arithmetic_dse.step2_evidence
python3 -m experiments.arithmetic_dse.placement_evidence
```

第二条额外要求本机原库/工具/流程文件存在且哈希匹配。默认第一条除原有时序、面积、网表、SPEF、DRC和预算核对外，直接读取所有接受阶段的SDC并重算语义；还确认旧ns SDC被拒绝、ASAP7可继承。回归`regression/arithmetic_sdc.py`实际执行当前SDC Tcl源码，覆盖整数环境变量的非整除周期/不确定度/transition/显式与默认I/O delay/负载，并用原归档验证拒绝。隔离副本破坏检查即使重绑文件哈希，也必须拒绝错误SDC。

范围仍为典型角平台接通，`multi_corner_signoff=false`；没有训练D、制定正式43例目标或运行688条主矩阵。修订计划第四章步骤三§3.9是本次有效验收记录，§3.1–§3.8保留为已撤回的原记录。
