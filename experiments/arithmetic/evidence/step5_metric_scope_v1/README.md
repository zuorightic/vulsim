# 步骤五时序指标口径澄清

本包只解释已保存的STA报告，继承[收尾v2](../step5_mul_closure_v2/README.md)和[指定容量复测v2](../step5_mul_capacity_v2/README.md)，不重跑综合、物理或STA，不更改原指标、SDC、RTL、冻结或费用。说明后继冻结为[mul_templates_freeze_v3.json](../../mul_templates_freeze_v3.json)。

W128 grt整体setup slack为+0.278111ps，确实属于很窄的接口余量；core_clk的period_min=1264.30ps只涵盖所用OpenSTA命令允许的同钟路径，推算约+235.70ps同钟余量不代表完整接口。实际最差路径为io_clk输入`a[32]`→core_clk内部寄存器，只含300ps输入延迟，没有输出延迟；不能用1500−300−300解释该路径。W64 grt的正确同阶段对照是+215.205627ps与1108.45ps；871.71ps来自synth。

完整说明及准入规则见[时序指标口径](../../../arithmetic_dse/timing_metric_scopes.md)和[规划第四章§5.9](../../../../mission/lxy-plan-fix.md#step5-metric-scope-review)。准入继续读取实际同阶段的整体setup／hold与覆盖，不用同钟最小周期代替整体接口时序或自动放行。

| 证据 | 内容 |
| --- | --- |
| `analysis.json` | 三组实际保存报告的独立解析：W128 grt、W64 grt与W64 synth，关键路径及原报告hash |
| `MinPeriodEndVisitor.cc.txt`、`tool_source.json` | 实际工具对应干净源码树的同钟过滤条件摘录、源码／子模块／原运行工具身份；不声称本次重编译或运行STA |
| `preservation.json.gz` | v2原证据与历史冻结的逐文件身份；旧数值全部保留 |
| `source_delta/` | 文档和后继读取器差异；原物理测量按旧源码快照继承 |
| `usage_delta.json`、`resources.json`、`commands/` | 仅support增量与收据，0 synth／grt／final |
| `audit.json` | 保存报告重算、继承v2便携核验及负例结果 |

```bash
python3 -m experiments.arithmetic_dse.metric_scope_evidence
```

本入口无需build目录或EDA工具；原`closure_evidence --verify-external`仍可逐字节核验本机完整产物。原大产物持久远程留存未确认的边界不变。
