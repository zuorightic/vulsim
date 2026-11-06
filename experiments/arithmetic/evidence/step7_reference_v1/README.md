# ASAP7九例D：17项原子参考与原始标签证据

2026-11-06，承接fix第四章§7.40，完成记录见§7.41。17项参考已全部采集、完整回放并结清；本包约6.4MiB，原始34个阶段／272条路径可便携重提取。本批是microbenchmark_reference_only，排除模型拟合和独立模型测试；尚未冻结数值目标、发布新预测模型或放行完整D／正式36条。

固定ABC1500ps、SDC40500ps、I/O0.2T，17个源／设置／角色和三个容量先导均在采集前登记。输入service独立使能、内部前级valid捕获和外部无条件捕获分别实现。原始路径保存完整Q-D，将launch Q至最后core输出的数据分量与捕获后缀、时钟／setup／skew／uncertainty分开；input IO只扣一次。全部物理单元按实际OpenDB连接／Liberty pin和函数唯一归属，未知功能单元拒绝，不把observer或shared clock重复计价。

完整原始回放通过17项／34阶段／272路径、108个实际付费叶命令、4151份文件hash，包括SDC／RC、重建Liberty状态／pin表和完整CTS CEC。首轮三个成功综合直接复用，唯一源综合总数17、grt17；v1名称转义／根常量读取停止和v2缺原生综合JSON的三个停止均保留，无物理重试或退款。108个叶命令中support74，实际合计墙钟968.631850s、CPU1333.54s；外围前检／审计／封存费用另在共享账本中保留，不将此数字冒充本轮全部成本。

17项在40500ps参考条件下setup均非负且覆盖完整。`ite_u16` grt hold为−0.321049ps，其余grt hold非负；多个点低于5ps复核带，均在raw-audit.json中保留。参考标签验收证明setup数据／边界分解有效，不宣称hold通过或多角签核，不据该hold结果修改参考设置／正式目标。

复现原始标签、归属、状态数量、SDC／RC及DAG最长路径：

```bash
python3 -B -m experiments.arithmetic_dse.model_reference_evidence verify \
  --folder experiments/arithmetic/evidence/step7_reference_v1
```

完整本机外部复核（还核对实际工具／Liberty、完整CTS CEC及所有原始祖先）：

```bash
python3 -B -m experiments.arithmetic_dse.model_reference_evidence_v2 \
  --folder experiments/arithmetic/evidence/step7_reference_v1 --external
```

隔离副本及篡改拒绝：

```bash
python3 -B -m experiments.arithmetic_dse.model_reference_evidence isolated \
  --folder experiments/arithmetic/evidence/step7_reference_v1
```

默认按冻结生产者重算，不要求活动源未来保持旧字节；源池224份、原始池1278份、收据池359份。便携回放重算完整原始标签和所列静态条件，**不重新运行EDA或完整CTS CEC**；后者由完整external核验覆盖。isolated禁读原`/home/zyrv/`树、PATH为空、禁止回放子进程仍通过，raw pool字节篡改拒绝。

首次external尝试错误地在解包的冻结源树下寻找活账本，失败及费用保留于verification-receipts.json.gz。v2外部核验器仅显式绑定真实Ledger路径，完整external随后通过；v1包和源不改，未重采任何数据。实际核验收据／v2源hash／全局结清前缀见verification.json。包manifest SHA256为`276f8a40cbf4876e0a871a76a7f3691a80bbc0be3d86ffdf88757891cd445979`。

target-proposal.json为**待用户确认的统一H_ref口径提案**：各案例取所需参考的数据路径joint overhead最大值，不额外新增裕量；控制／input／external全路径另报参考上下文最低周期诊断，不加到D_ref。保留原ceil(H_ref+1.5D_ref/L)；不是已冻结数值目标，也不赋予新周期的模型资格。

| 案例 | L | D_ref ps | 提案H_ref ps | 提案目标 ps |
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

D_ref按原始依赖图最长路径精确有理数计算，表中只显示三位小数；所有目标用未舍入值向上取整。它是参考路径估计，不是“自然周期”、预测保证或整图实测。UDR等原子重操作可能在既定L和公式下不可行，后续保留真实结论。

后续先确认并版本化冻结H_ref及目标，再登记S一般状态、G受限整阶段／联合边界、I真实half／quarter区间，完成其共同目标域独立资格。旧发布及已消费测试全部保持，未改且域匹配的11类不重训。D生产选择／RTL和正式36条仍待完成，选择PPA0。
