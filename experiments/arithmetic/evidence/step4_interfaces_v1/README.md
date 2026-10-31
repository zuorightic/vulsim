# 步骤四：公共编译请求、区域保护和固定成本证据

[当前冻结](../../arithmetic_interfaces_freeze_v1.json)对应[规划第四章步骤四](../../../../mission/lxy-plan-fix.md#step4-interface-acceptance)。它绑定本目录最终`index.json`的hash及239份当前源码/配置，继承平台v7、位置、Mul、区域、步骤二及宽位宽等原冻结。历史冻结、原证据和收费条目保留原字节；当前编译器有修改，旧验收显式使用快照，不用旧hash宣称当前源码通过。

从仓库根目录运行：

```bash
python3 -m experiments.arithmetic_dse.interfaces_evidence
```

该命令不调用编译器、EDA或Tcl，不依赖build。`--root PATH`审计指定副本；`--no-parents`跳过父版本的语义重算，仍检查全部父冻结身份和本步证据。重新运行生成/仿真回归会增加support实耗；只读核验不启动实验叶命令。

## 实际范围

- 同一公共请求贯通CompileOptions、PipelineV2、VUL bridge及两个CLI；严格核对平台、profile/表/模型身份、L/II和语义/候选版本。
- 原始无符号Mul按8/16/32/64/128及12/24/48/96位登记真实原子区域；binary32 RNE仍用既有真实位操作展开并保持原子。
- native-beir-contract-v1在各编译边界检查操作、类型、引用、区域/组和物化；Case与受限显式Lookup真正降低为可调度Ite图。
- 实际核心调度使用步骤二冻结表的固定CostProvider；初始、移动及最终检查共用组约束。固定抽象成本独立于物理周期。
- half/quarter内部展开与正式C结构/位置选择仍属步骤五；离线D模型推理属步骤七。当前模型请求明确拒绝，没有回退或物理查询。没有新增主矩阵记录、训练或synth/grt/final。

## 目录与可重算内容

| 证据 | 实际内容及核验边界 |
| --- | --- |
| `source_v1/`、`previous_source/` | 239份当前源/配置；改动前源字节供后继解析历史冻结。base提交仅表示开始点，修改后身份以精确hash为准 |
| `accepted/regression.json` | 最终C++3729项断言、18项Python成本交叉核对、真实native/CIRCT及四平台请求/八类拒绝 |
| `report_index.json` | 25份结构报告，共2201节点/47区域；核对节点成本、Mul计费来源、区域最长路径/唯一组合和、原子级号、共享寄存器位数/链数 |
| `accepted/generated/`、`circt-generated/` | 同一请求的实际RTL和报告；图/调度hash一致。RTL临时路径注释可能不同，分别记录真实hash |
| `accepted/vectors.txt.gz`、`rtl-run.log.gz` | 2282周期原始输入和实际Verilator输出；独立Python参考重算valid、整数、FP value/flags、复位和气泡/保持 |
| `accepted/vul-native/`、`vul-software/` | 两条路径分别生成/构建并完成10000周期自校验；源码、脚本与日志保留。嵌入核以真实wrapper字节区间及body hash核对，未保存完整逐事务trace，不冒充独立trace重算 |
| `disabled/` | CIRCT关闭时完整软件/native执行、明确SKIP；早于最终3项估计器边界断言及报告细化，实际native RTL字节与最终验收相同，变体单独留存 |
| `baselines/` | pipeline/reset/valid及55项区域检查；两边无区域兼容、单方清空拒绝等既有基础 |
| `execution_source_variants/`、执行源清单 | 内容寻址保存支持命令/最终及关闭模式执行时的源码。早期开发命令未有完整源清单，明确标为development_only，不能用于最终验收 |
| `commands/`、`command_index.json` | 本步每条收费叶命令的执行记录、日志、GNU time，含开发失败和预期拒绝 |
| `resources.json`、前后账本 | 精确墙钟/CPU、pending及完整账本前缀；全局策略不改、物理增量0 |
| `portable_checks.py/json` | 无build、PATH空的隔离复制及9类破坏检查；语义负例重绑相关哈希后仍拒绝 |
| `static_checks.py/json` | 历史文件/章节、改动范围、语法/文档/资源与后继身份审计 |

核验器检查源码/快照/索引、节点和引用身份、固定表精确身份、成本和调度；执行数值验证来自保存的真实trace，不由编译报告中的能力布尔值推导。报告区分generated、内部可切分、独立数值验证、C选择、D覆盖/选择和物理评价，不能把单Mul登记当成已内部切分。

独立周期检查包括valid22820项、有效数据/flags34713项、复位126项、气泡/保持13083项和组合FP/整数6846项。CIRCT关闭时再次执行的是同一2282周期向量，不记成4564个不同向量。独立fixture的L=3/N=2含显式外围输出捕获；VUL共同探针核内L=2，service/valid外围壳观测tick+3，分别记录。

## 隔离与失败保留

隔离副本无build且PATH为空，完整父链通过；改源码、Mul成本、引用宽度、原子FP级号、模板参数、伪造D成功、复位/时钟protocol和乘积bit255共9类负例均拒绝。除源码绑定负例外，已重绑对应图/调度/证据hash，避免仅凭hash不一致冒充语义检查。`portable_checks.json`记录当次索引hash；该测试先于加入自身结果与最终文档，最终受保护文件集合由当前freeze绑定的index精确定义。

`nonzero_commands.json`保留6条开发失败和40条预期拒绝（8类请求在不同验证轮次执行）。开发修正包括LLVM JSON所有权、测试自管valid误赋、辅助端口/合法Mux缩放误报及wrapper timescale/构建入口。最终通过使用新任务目录与实际执行源身份。早期失败源清单缺失如实登记，不补造执行身份。

本步新增132 support、墙钟501.819654秒、实际CPU672.15秒、物理0；累计52 synth /29 grt /14 final /575 support，墙钟4740.883971秒、CPU7116.89秒、pending0。所有调用在原预算内；未放宽周期、自动改变L或用早期阶段替代失败final。步骤三P1/P2成果与GF180 wire RC待核风险继承，不由本步重新解释。
