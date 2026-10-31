# 新步骤五收尾：检查器与精确证据协议v2

本包对应[规划第四章§5.8](../../../../mission/lxy-plan-fix.md#step5-closure-review)，后继冻结为[mul_templates_freeze_v2.json](../../mul_templates_freeze_v2.json)。原[软件v1](../step5_mul_templates_v1/README.md)与[容量v1](../step5_mul_capacity_v1/README.md)保留原字节；本包不把旧错误或超时改写为成功。

位置可行性根据真实生产cap独立重算，不信任归档标志。当前10个声明位置中4个可行，最大级d均为2、组合a均为22，寄存器位数分别为130、144、162、146，生产采用130位／12个寄存器。仅枚举第一个Mul的三组，另一Mul及其余节点固定；该比较不证明全位置空间的全局最优。外层C的340个候选评分及真实移动轨迹单独重算，生产调度算法未改。

| 文件 | 内容与实际核验边界 |
| --- | --- |
| `positions_v2.json` | 完整生产级号图、10个位置成本、上下文、cap与生产偏好；核验时重算数值与布尔标志 |
| `sensitivity_v2.json` | 30结构／10上下文的精确有理数排序，选择变化0；不是步骤七训练或步骤八输入 |
| `historical_replay_inputs.json` | 绑定原v1的129份实际压缩报告及解压后输入hash；不重新生成替代图 |
| `historical_replay.json` | 真实C++入口回放129报告／219区域；拒绝0、无法重建0，5类变异拒绝及可读诊断 |
| `software_checks.json`、`software_validation.json` | 新生成图／调度／RTL／候选与原图一致，24504原生检查、3786公共接口、3383 CIRCT；保存trace独立重放，不算新增RTL仿真轮次 |
| `portable_checks.json` | 无build、无EDA、无完整artifact store的隔离核验和重绑hash后的语义反例 |
| `preservation.json.gz` | 原冻结及原证据载荷的逐文件保护清单；后加导航不伪称旧索引成员 |
| `resources.json`、`usage_delta.json`、`commands/` | 原账本前缀＋全部新增收费，包含开发失败、一次grt、support、GNU time及进程清理 |
| `source_delta/`、`procedures/` | 改变源码与读取／归档过程；未改源码引用精确父快照 |

块坐标与移位证书用于165个`mul-block-tree-v1`区域；其余54个区域由各自登记契约验证，不硬套分块规则。原v2报告未保存的PortRead文字由端口映射恢复，split policy由登记模板ID确定，facts由保存图重算；未猜测或补造块坐标、位宽、常量及分组。读取器明确限于此次实际scalar档案，缺字段或无法恢复的数组边界会报无法重建。便携Python静态证书独立重算块覆盖，C++执行由收费命令、源码与输出作为回放证据保留；无二进制的clone不会宣称现场重跑C++。

精确数值读取规则见[analysis_protocol.md](../../../arithmetic_dse/analysis_protocol.md)和[exact_analysis_v2.json](../../../arithmetic_dse/configs/exact_analysis_v2.json)。整数拒绝bool、float和数字字符串；成本使用规范约分的numerator／denominator对象，解析为Fraction后比较。旧v1字符串仅由原冻结分析器在历史入口核验。

```bash
python3 -m experiments.arithmetic_dse.closure_evidence
python3 -m experiments.arithmetic_dse.closure_evidence --verify-external
```

指定单次容量复测独立见[容量v2](../step5_mul_capacity_v2/README.md)。默认入口只核验仓库小证据；`--verify-external`需要实际取得本机catalog中的全部大产物，缺失报artifact_unavailable。持久远程保留尚未确认，ignored目录不是已发布交付。没有新增original、synth、final、D训练或主矩阵。
