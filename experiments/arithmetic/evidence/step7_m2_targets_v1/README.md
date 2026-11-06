# ASAP7九例正式数值目标冻结

2026-11-06，用户明确确认“采用上述分离口径”。承接不可变的step7_reference_v1参考证据及其target-proposal.json，按既定target_rules_v2冻结九例目标；实施记录为fix第四章§7.42。参考模型、失败、原提案和所有独立结论保持原字节。

H_ref取各案例必需参考标签中data joint overhead的最大值，包含捕获后缀及不重复的时钟／setup／skew／uncertainty，不包含launch Q至最后core输出的数据分量。其他enable／valid／input／external完整路径保留为40500ps参考条件下的最低周期诊断，不并入D_ref、不调整目标。没有另加数值reserve。D_ref为原始未展开DAG的最长依赖路径；按未舍入有理数计算：

```text
T_target = ceil(H_ref + (3/2) × D_ref / L) ps
```

| 案例 | L | D_ref ps（显示值） | H_ref ps（显示值） | 冻结目标 ps |
| --- | ---: | ---: | ---: | ---: |
| MAC_32 | 2 | 1699.297 | 156.011 | 1431 |
| DOT2_16 | 2 | 1333.010 | 118.962 | 1119 |
| UDR_16 | 2 | 5844.408 | 143.812 | 4528 |
| DIVSEL_32 | 2 | 15700.820 | 136.776 | 11913 |
| F1 | 2 | 4000.652 | 139.575 | 3141 |
| F2 | 3 | 8033.724 | 144.224 | 4162 |
| H_M_32 | 2 | 1476.304 | 145.680 | 1253 |
| H_D_32 | 3 | 29518.693 | 136.776 | 14897 |
| H_F1 | 2 | 4327.120 | 139.575 | 3385 |

活动目标文件为`experiments/arithmetic_dse/configs/model_asap7_m2_targets_v1.json`，SHA256 `6dd49589bae6e6be0be8d35bdd16259064a1f84a2910129249421c4bc458763e`。冻结源调用真实`contracts.freeze_target_batch`／`target_period_ps`，production batch SHA256为`211307811c67998d3f0cddd08eafe24f4fc6c96986e495375c96148ba20ebe71`；目标同时绑定完整原始case定义及hash、L、参考identity／源manifest、critical path、H最大值来源、精确数据预算及rho_ref。

本包约0.35MiB。inputs.json保留完整输入，source目录保留三个生产者，targets.json与活动配置字节一致。manifest SHA256为`708decbc3b98714879e516d2ff2950701265e647ea5184ebe7324735e6b33576`。默认从冻结源重新生成九例定义并调用生产目标公式，不读取build、EDA或活账本：

```bash
python3 -B -m experiments.arithmetic_dse.model_m2_targets verify \
  --folder experiments/arithmetic/evidence/step7_m2_targets_v1
```

加`--external`还核对本机活动目标与原参考证据身份；隔离及篡改核验：

```bash
python3 -B -m experiments.arithmetic_dse.model_m2_targets isolated \
  --folder experiments/arithmetic/evidence/step7_m2_targets_v1
```

完整external通过；禁读原`/home/zyrv/`树、PATH空、禁回放子进程的副本通过；MAC_32目标被修改1ps时拒绝。核验收据、后继需求源和全局结清前缀见verification.json。冻结阶段新增support5、PPA0，无物理调用或重拟合。

S／G／I后继需求为`configs/model_asap7_m2_joint_requirements_v2.json`，SHA256 `49d8578a2c793b631e221ac8ff6fdd84bd6448e3146fe406055f3ba4813ef3db`；它显式继承不变v1需求及本次目标hash，登记九个ABC1500／精确SDC／IO0.2T上下文与剩余合成源／划分／容量／预算门禁。目标数值冻结不授予现有模型在新周期上的资格，physical_admission_allowed=false、model_target_domains_qualified=false、full_D_ready=false，正式36条及688条均未准入。

本目标表是固定评价条件，不是时序保证。原子UDR等可以在既定L下不可行，后续保留实际模型和STA结论，不逐例改周期、L或公式。下一步完成S一般状态、G受限整阶段／联合边界、I真实区间的合成源前检和预登记，再按具体容量／预算启动采集。
