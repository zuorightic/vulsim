# 步骤六整图接口与验收范围

现行实现按`mission/lxy-plan-fix.md`第一章§10.6；实际记录在第四章步骤六。冻结为`experiments/arithmetic/whole_graph_freeze_v1.json`。本步完成软件、原生RTL和公共VUL接口验收；有限容量探针留下两个不同的阻塞原因，没有新的grt结果、训练集、目标标签或主矩阵记录。

| 结构 | 当前实现 | 内部切分范围 |
| --- | --- | --- |
| MUL/MAC/DOT2/H_M | 原始Mul、参数化half/quarter，复用步骤五候选及调度 | 仅已登记的分块乘法组 |
| UDR/DIVSEL/MIX/H_D | 同宽无符号Div/Mod、safe divisor、外层零除选择；宽接口至128位 | 原始Div和Mod各自原子，不展开除法器内部 |
| 单独除法、单独取余 | 五档诊断源，复用同一请求/图/流水入口 | 原子 |
| `vularith::UDivRemShared<W>` | 商复用图：Div一次，Mul/Sub生成余数；d=0返回全1商及a余数 | 复用值及Mul模板依实际图调度；没有融合商余硬件或折扣 |
| F1/F2/H_F1 | binary32 RNE、渐进下溢、舍入后tininess、canonical NaN；F2两次独立舍入并按契约聚合flags | 每个完整FP乘法区域原子；串联和旁路通过统一整图调度 |
| 基础选择、比较、位操作、动态移位 | 真实BEIR及固定成本；安全移位包装使全部中间表达式有定义 | 现有合法组，不增加未登记op kind |
| D | 相同请求、区域、图、L/II和报告入口；backend成本请求缺模型明确拒绝 | 推理及模型支持域仍由步骤七实现 |

动态`/`、`%`已贯通S8/S9/S10/S11到现有BEIR操作。BEOPT不得把safe-divisor依赖变成仅在下游选择时成立的局部表达式。整图校验在调度前要求非零常量、已知非零位或匹配的Eq/Ne+Ite安全除数证明，未知来源以`unsafe_divisor`拒绝。物化后不重新把寄存器来源当作组合证明；其合法性继承已经核对的原图和协议。真实C++测试对每个Div/Mod区域注入零除数，并通过同一入口拒绝。

五档整数8/16/32/64/128及12/24/48/96诊断宽度均验证；43例的A为L=1组合基准，B/C沿冻结的逐例L，II均为1。A/B保留原始结构，C沿步骤五正式排序。L指含最终输出捕获的事务延迟；RTLzz内核物化L−1级，公共VUL的IREG接收/查询边沿另列，不能把外围开销并成核内级数。验证包含连续事务、气泡、在途复位、排空、32/64/128多limb复位和256/257位输出。

生成和测试入口（从仓库根执行，输出目录须为新目录）：

```bash
python3 -c 'from experiments.arithmetic_dse.whole_graph import prepare; print(prepare("build/step6-fixtures"))'
cmake --build build/step4-rtlzz --target arithmetic-suite-test -j2
build/step4-rtlzz/testv2/arithmetic-suite-test "$PWD" "$PWD/build/step6-fixtures/jobs.json" "$PWD/build/step6-generated"
python3 regression/arithmetic_whole_graph.py prepare build/step6-fixtures build/step6-generated build/step6-cycles
```

`build_command.json`记录Verilator构建命令，生成程序读取`vectors.txt`、输出`rtl-run.log`，然后运行`regression/arithmetic_whole_graph.py verify`。公共VUL源由`regression/arithmetic_vul_suite.py prepare`生成，`experiments.arithmetic_dse.whole_graph_validation`逐叶计费调用公开生成器和仿真。软件/原生/CIRCT为显式路径；软件组合核通过不能替代RTL流水验收。新运行仍须用统一support计账入口，不复制独立额度。

小证据只读核验：

```bash
python3 -m experiments.arithmetic_dse.whole_graph_evidence
python3 -m experiments.arithmetic_dse.whole_graph_evidence --verify-external
```

默认核验重算176份主验收BEIR、24份代表报告及43份公开VUL嵌入核的成本/候选/分组/安全除数和保存的逐周期trace，不需要编译器、EDA或build目录。C++执行由源码、命令和日志绑定；离线Python核验不冒充重新执行C++。只有五份shared-helper诊断的源码位置注释发生变化；旧执行RTL单独保存，图、级号、协议及可执行RTL文本一致。完整生成/构建文件和失败物理目录另存本机ignored的内容寻址包；`--verify-external`逐成员读取实际字节，缺失明确拒绝。远程持久留存尚未确认。

本轮ASAP7128位UDR（独立Div/Mod）（独立Div和Mod）在8GiB上限被终止；只限制这一结构和阶段，不推断五档除法普遍不可用。串联F2综合命令成功，原单模块端口读取器对core+壳误报重复端口，流程在阶段核验处停止。后继读取器按显式top解析ANSI端口并在综合前预检；静态重核实际SDC通过，未重写旧manifest、补造STA指标或继续grt。四个从属ABC/SDC控制点暂停，未测敏感性保持未覆盖。修正后的后端能力需在后续有限准入中实际验证；本轮无自动重试、换周期或改变固定L。
