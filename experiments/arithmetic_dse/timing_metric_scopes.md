# STA最小周期与整体setup slack的口径

`setup_worst_slack_ps`来自`report_worst_slack -max -digits 6`，是当前阶段实际SDC下的整体最差setup slack，包含已约束的内部、输入／输出及跨时钟路径。setup可行性沿用实际slack非负且时序覆盖完整；hold单独判断。

`minimum_clock_period_ps`来自`report_clock_min_period -include_port_paths`中`core_clk period_min`这一行。所用OpenSTA实现仅考虑launch和capture都属于当前同一时钟对象、同极性、无multicycle的max check／output_delay路径，取`max(period - slack)`。`-include_port_paths`允许满足上述条件的端口路径，并不纳入不同clock对象之间的路径。这里`io_clk`是独立虚拟时钟，周期虽与`core_clk`相同，两者仍是不同对象，因此io_clk→core_clk及core_clk→io_clk路径不进入core_clk的这个最小周期统计。

因此，字段名中的“minimum”不能解读为完整接口满足所有约束的最低周期，也不能用`目标周期 - minimum_clock_period_ps`代替整体setup slack。它是固定STA上下文中的同钟路径诊断，未重新扫描周期、重新缩放I/O延迟或重新优化电路；`io_clk period_min=0/fmax=inf`也不表示完整接口可以无限加速。

| 实现与同一阶段 | 目标周期ps | 整体setup slack ps | core_clk period_min ps | 同钟范围推算slack ps |
| --- | ---: | ---: | ---: | ---: |
| W128指定C复测，grt | 1500 | +0.278111 | 1264.30 | 约+235.70 |
| W64原C探针，grt | 1500 | +215.205627 | 1108.45 | 约+391.55 |
| W64原C探针，synth | 1500 | +289.168793 | 871.71 | 约+628.29 |

最后一列由两位小数的period_min反推，带报告舍入误差，仅代表被该命令纳入的路径范围；没有另外采集这些内部路径的端点报告。不能将W64的grt slack与synth period_min混为同一阶段。

W128实际最差路径是输入`a[32]`（io_clk）到`rtlzz_pipe_148_s1[125]$_SDFFE_PN0P_`寄存器（core_clk）。保存的完整路径报告显示：输入外部延迟300ps、数据到达1708.206299ps；capture时钟含传播延迟后为1738.865112ps，扣20ps setup uncertainty和10.380804ps library setup，required为1708.484375ps，STA报告slack为+0.278111ps。文本显示值相减与报告slack有约0.00004ps的浮点／显示差异。

该路径只有输入外部延迟，没有输出外部延迟；不能按`1500-300-300=900ps`解释它。最差输出路径单独为`z[41]`寄存器（core_clk）到`z[41]`输出（io_clk），其slack为+705.978455ps。输入、内部和输出路径的约束以及传播时钟延迟分别参与STA，不能合并扣除不同路径的外部预算。

**批次准入以同一阶段、同一实际SDC下的整体setup／hold、覆盖及已冻结复核要求为依据；同钟period_min只作分解诊断。** W128这次整体setup余量确实只有+0.278111ps，不能以同钟范围约235.70ps的余量宣称整体裕量充足或自动放行批量。此前“容量完成、当前TT时序满足、批量仍须逐域准入”的结论保持；这里不新增裕量阈值、物理任务或周期调整。

证据与原始报告绑定见[step5_metric_scope_v1](../arithmetic/evidence/step5_metric_scope_v1/README.md)，该包保存源码过滤条件摘录、工具身份、三组报告的独立解析和原证据hash。说明只修正读法，不修改v1/v2的原始manifest、metric、SDC、冻结或收费。
