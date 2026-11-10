# 第1—3步后继证据：逐单元校验实际Liberty组合时序弧

本包修复[§7.59原资格包](../step7_steps123_v2/README.md)中的读取器遗漏，实施记录见[修订计划§7.60](../../../../mission/lxy-plan-fix.md#step7-liberty-arc-reader-fix)。旧证据和四个物理测量点原字节保留；本包是增量后继，使用旧包内相同的原始报告与Liberty元数据，不重新综合、布线、测量或拟合。

缺陷确实存在：独立节点读取器把“不满足普通input→output方向”和“缺Liberty弧”用and连接，合法方向会绕过弧存在性检查。Q→D分解器同样只对output→output步骤查弧。修复后两处共用`verify_combinational_arc`，逐单元步骤必须同时满足：非顺序单元、允许的input／output→output方向，以及明确存在的源pin→目标pin Liberty弧。CON→SN等多输出步骤继续按真实库弧接受；仅修改方向或伪造方向不成立的弧也不能通过。

| 验证 | 结果 |
| --- | --- |
| 原缺陷复现 | 真实mul-load-1500 synth的`core/_08201_`，只删`BUFx2_ASAP7_75t_R`的A→Y弧；旧版独立节点与Q→D读取均接受，完整结果不变 |
| 修复后正向回放 | 4个原not_training点／8阶段通过；标签所有已保存字段逐项不变 |
| 单条真实弧删除负控 | 每阶段独立节点／Q→D分别取真实路径见证，共16项，全部明确因缺实际Liberty弧拒绝 |
| 方向负控 | 即使元数据含A→B／Y→A弧，input→input／output→input仍拒绝，共2项 |
| 旧负控 | 原8项报告、端点、银行等破坏检查继续通过 |
| 隔离与篡改 | 从父包恢复报告、叠加修复源码；禁原home／项目／build，PATH空、禁回放子进程；父包／增量内容篡改均拒绝 |

[修复前复现收据](reproduction.json)和[修复后完整回放收据](verification.json)可直接阅读。`overlay.json.gz`包含变更源码、复现／回放收据及旧8项负控结果，`manifest.json`绑定父包每个文件的hash。旧读取器的缺陷复现使用父包内冻结源码，修复后回放使用增量源码。两者都从同一份保存报告重算，不靠重写旧标签或新测量获取通过。

```bash
python3 -B -m experiments.arithmetic_dse.liberty_arc_evidence verify \
  --folder experiments/arithmetic/evidence/step7_steps123_v3

python3 -B -m experiments.arithmetic_dse.liberty_arc_evidence verify \
  --folder experiments/arithmetic/evidence/step7_steps123_v3 --external

python3 -B -m experiments.arithmetic_dse.liberty_arc_evidence isolated \
  --folder experiments/arithmetic/evidence/step7_steps123_v3 \
  --out build/liberty-arc-isolated-NEW-UNIQUE-ID
```

在实验工作中仍通过共享Ledger支持叶包装器计费。便携模式依赖仓库中的父包实际内容；`--external`额外核验其原始完整文件。包内`publication-closure.json`记录以父包12460条账目为基线的本轮增量及最终结清状态。新增synth／grt／final均0，正式训练／独立测试标签0；四个原grt点setup违约状态不变，`full_D_ready=false`。
