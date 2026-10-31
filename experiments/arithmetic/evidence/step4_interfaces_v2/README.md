# 步骤四报告类型修订：v2增量证据

当前冻结为[arithmetic_interfaces_freeze_v2.json](../../arithmetic_interfaces_freeze_v2.json)，继承[原v1冻结](../../arithmetic_interfaces_freeze_v1.json)及其971份证据，原文件未改。记录见[规划第四章§4.8](../../../../mission/lxy-plan-fix.md#step4-report-type-review)。旧`step4/step4_review`属于旧计划，已新增导航横幅。

`register_bits`在新`arithmetic-structure-report-v2`中为JSON整数，与`register_count`一致；支持uint64完整域。关键字段schema在活动接口配置中，类型检查拒绝字符串、小数/布尔冒充整数、负值、溢出、缺字段及非有限数。v1报告仍由其精确冻结阅读器解释，不重写报告或以类型转换掩盖新报告错误。

本次实际重建独立CLI/测试及VUL生成器，C++3786项检查通过（含uint64最大值纯序列化检查，未生成该数量的物理寄存器）；核对15份实际新报告、四平台请求、VUL桥接和两份真实失败报告，7项类型测试通过。原生与独立CLI的RTL逐字节相同，VUL仅源码注释的输出目录前缀改变，当前body及wrapper身份仍单独保护。所有计算图/调度一致。没有重跑仿真/EDA，数值验证沿用并重算原v1的2282周期trace；不能把它算作新的仿真实验。

| 文件 | 内容与核验 |
| --- | --- |
| `source_delta/` | 只存新改源码；`source_snapshots`逐路径映射未变文件至原v1快照，不再复制239份源 |
| `report_index.json`、`reports/*.json.gz` | 实际新报告与所引用原报告/RTL；压缩报告保留完整节点图，不只留hash |
| `vul-kernel.sv`、`vul-top.sv` | 本次VUL实际产物及字节区间，注释前缀变化与可执行文本分别核对 |
| `failure_index.json`、`failures/` | 当前v2诊断及失败码，不是旧失败覆盖 |
| `checks.json`、`type-tests.log.gz` | 实际命令/类型与图/调度/RTL同一性结果 |
| `usage_delta.json`、`resources.json`、`commands/` | 以旧已结算检查点hash/长度加本次条目恢复账本；每叶GNU time、日志与清理记录 |
| `storage_inventory.json` | 修订前受保护证据的逻辑/文件系统分配字节和构成；不把du当Git pack |
| `portable_checks.py/json` | 无build、空PATH的隔离核验与重绑哈希后的类型反例，记录当次索引；最终集合以新freeze为准 |
| `preservation_checks.py/json` | 旧冻结/证据/记录保留、链接、资源与改动边界审计 |

仓库根目录只读核验：`python3 -m experiments.arithmetic_dse.interfaces_evidence`。新包默认严格读v2；历史v1仅在归档核验路径加载，仍重算成本/调度、共享寄存器和旧trace。`--root PATH`不读取执行目录的类型配置；`--no-parents`只省略更早平台/位置/步骤二的语义重算，不省略原v1报告及trace核验。

[证据存储规则](../../../arithmetic_dse/evidence_storage.md)对后续新包设置5MiB目标/单文件1MiB；当前包用父引用、压缩和增量实践该规则。旧包原样豁免，不以本轮小包体量证明688条主矩阵已可容纳；完整大产物目的地尚未选定、未上传、未迁出原证据。缺少实际内容时不能仅凭索引报完整复现通过。费用精确值见`resources.json`，无物理增量。
