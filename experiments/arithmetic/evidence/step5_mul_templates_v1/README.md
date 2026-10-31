# 修订计划步骤五：参数化Mul与新C

[规划第四章步骤五](../../../../mission/lxy-plan-fix.md#step5-mul-template-acceptance)记录范围和资源。当前冻结为[mul_templates_freeze_v1.json](../../mul_templates_freeze_v1.json)。旧`step5/step5_placement`属于历史split16，不是本次参数化验收。

公共请求的`mul-candidates-v1`按登记的original/half/quarter枚举、资格过滤、去重和K=16进入同一固定成本调度；`mul-template-v1`显式block_width是强制诊断。真实部分积和每个保留进位的归约层为合法组，级号由调度器决定；原子FP保持不可分。候选按冻结C排序键选择，不查询PPA。D推理仍待步骤七。

本包采用源码/账本增量、父快照引用、压缩RTL和报告。报告包括非选中候选的真实图及初始/最终/移动轨迹；非选中图未发射RTL，其空body hash不代表生成成功。最终选中报告才绑定实际RTL。原始/低位、五档和非整齐尺寸、连续/气泡/复位及257位MAC分别由真实trace核对；报告的能力字段不是数值验收的替代。

| 证据 | 内容 |
| --- | --- |
| `report_index.json`、`reports/`、`rtl/` | 实际原生结构、候选、调度及发射RTL；无大段展开/压缩双份 |
| `mul/`、`mac/` | 原始输入/输出trace、模块配置和功能计数；scoreboard独立重算 |
| `sensitivity.json` | 预声明30结构的线性/平方a排序；精确Fraction，d和级号不改，无新增PPA组 |
| `positions.json` | 相同结构至少两种生产cap内位置；真实移动轨迹独立保存 |
| `integration.json`、`regressions.json`、`circt/` | 公共CLI/VUL10000周期、四平台请求、原子FP、CIRCT和原有基础回归 |
| `source_delta/`、`retired_source/` | 新改源码和必要历史旧字节；未改源引用父快照，旧实现不再是公开运行模式 |
| `usage_delta.json`、`commands/` | 全部新收费叶命令、GNU time、失败/预期拒绝及清理；父账本不复制 |
| `portable_checks.*` | 无build/EDA的隔离、哈希重绑语义破坏检查 |

容量小证据单列[step5_mul_capacity_v1](../step5_mul_capacity_v1/README.md)，与软件包分别受索引/hash保护。完整网表/实例表/工具日志在被忽略的本机artifact_store；catalog给出实际字节及hash、成员和可获得状态。本机目录不是已确认的持久远程位置。默认核验只承诺仓库已有语义/功能/度量证据，`--verify-external`取得并逐成员核对大产物，缺失则明确失败，不凭hash宣称完整复现。

```bash
python3 -m experiments.arithmetic_dse.step5_evidence
python3 -m experiments.arithmetic_dse.step5_evidence --verify-external
```

旧冻结、错误结果和收费不覆盖；旧成本/固定split16活动入口已删除，必要历史分析只能经私有冻结源加载。此步未建立D、未启动688条矩阵、未宣称四平台128位容量或物理优化收益。
