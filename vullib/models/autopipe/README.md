# 当前模型资源

本目录是当前模型的唯一发布资源入口，包含 ASAP7 与 Nangate45 工艺参数。后续扩展和优化从这些冻结文件开始，以资源清单及预测回归作为基线。

| 资源 | 用途 |
| --- | --- |
| `asap7/response.json` | ASAP7 算术、G、S/shared、控制及完整诊断计价参数 |
| `asap7/characterization.json` | 本体预算与等效采样周期的转换合同 |
| `nangate45/package.json` | Nangate45 参数子包、profile、阶段和适用范围的绑定入口 |
| `nangate45/arithmetic.json` | 算术与 G 响应；引用同目录树内已绑定的 ASAP7 参考函数 |
| `nangate45/state-shared.json` | 本工艺状态、控制、shared 与实际边界 |
| `nangate45/characterization.json`、`cell-cover.json` | 本工艺采样窗口和功能逻辑单元覆盖 |
| `profiles/` | 目标工艺身份 |
| `fixed_op_width_v1.json` | B/C 抽象静态权重；不是物理模型拟合结果 |
| `workloads.json` | 登记的有限结构语法 |
| `manifest.json` | 发布资源的字节哈希 |

本目录各项共同构成当前模型；参考函数和带历史编号的内部字段不是可删除的旧版本回退。schema、来源与哈希用于兼容和追溯，文档名称统一为当前模型，机器身份保持。

当前参数保留诊断资格、适用域和外推限制。资源用于离线预测，不包含 PDK，也不代替实际物理时序分析。修改参数需要配套更新合同、发布清单和验证，不能通过绕过校验替换文件。

- [生成与测试](../../../doc/autopipe.md)
- [各类模型的拟合与调用](../../../doc/mission/models.md)
- [当前实现](../../../doc/mission/implementation.md)
- [注意事项](../../../doc/mission/pitfalls.md)
