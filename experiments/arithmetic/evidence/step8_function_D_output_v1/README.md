# 第8步：通用函数驱动的D原型RTL交付

本包对应[§7.78](../../../../mission/lxy-plan-fix.md#step8-function-D-output)。用户明确要求暂缓reset时序问题、先产出D；范围为`prototype-no-reset-timing-v1`。功能reset保留，D原型选择和完整RTL已交付，独立联合及reset时序资格继续保留原状态，`full_D_ready=false`。

公共调用及模型依赖见[模型包说明](../../models/asap7_function_D_prototype_v1/README.md)，实际产物位于[/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1](/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1)。

| T (ps) | 选择 | 预测总面积 (um²) | 最大预测违约 (ps) | RTL |
| --- | --- | ---: | ---: | --- |
| 500 | `target_unmet`，original/view1 | 807.6314 | 794.4752 | [D.sv](/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1/outputs/T500/D.sv) |
| 1000 | `target_unmet`，original/view1 | 762.5312 | 330.5262 | [D.sv](/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1/outputs/T1000/D.sv) |
| 1250 | `target_unmet`，original/view1 | 762.0727 | 91.2976 | [D.sv](/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1/outputs/T1250/D.sv) |
| 1500 | 预测可行，original/view1 | 761.7718 | 0 | [D.sv](/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1/outputs/T1500/D.sv) |
| 3000 | 预测可行，original/view0 | 732.6368 | 0 | [D.sv](/home/zyrv/vulsim-artifacts/step8-D-prototype-20261111-v1/outputs/T3000/D.sv) |

L=2／II=1，L由1级核心和1级输出capture组成，输入服务launch另列。全部44个合法位置均由源重新枚举，original／half／quarter三种结构全部调用相同节点函数、S与规范化DAG组合计价；五档均选择original，未人为要求拆分。1500ps位置有129位native状态，3000ps位置为65位，因此宽松目标下选择了更小的状态／总面积。表中均为模型预测；本轮没有物理PPA调用，不授予这些RTL的实测时序成功。

验收内容：

- 5×44=220项候选评估，3440次节点函数、8055条精确位连接、S／共享所有者及选择排序由Python独立复算通过。
- 五份完整RTL各256周期，合计810次有效数据比较，覆盖连续输入、气泡、独立输入写使能、held-valid、溢出、非零功能reset、在途复位及内部FF保持。
- 目标域外、枚举截断、源身份错误、已存在目录均拒绝发射／覆盖RTL。部分节点域负控中32候选覆盖／12拒绝，完整搜索输出`cost_uncovered`，不静默选子集。
- 原生`rtlzz-d`及简化Python入口产生相同1500ps选择和逐字节相同RTL。
- 新D的37个文件、上游冻结25项模型／推理文件、旧S／节点／原native二进制核对通过。既有生产资格门禁保持原逻辑。

部分域负控首次暴露新选择器将`e.what()`作为非拥有JSON字符串存入记录，异常销毁后产生无效UTF-8。已改为拥有字符串，原失败、失败源码和费用保留；后继正确输出32覆盖／12拒绝。该修复未改模型参数或已覆盖候选的估价路径。

原始归档508成员、24139004字节，已实际恢复并逐文件核对SHA，包含实际可执行文件、完整逐候选报告和仿真见证。便携包342成员，隔离回放重现五档函数／DAG／选择及全部RTL夹具；C++／仿真器的实际成功收据被封存，回放不启动编译器、模拟器或EDA。

```bash
python3 -I -B experiments/arithmetic/evidence/step8_function_D_output_v1/replay.py replay \
  --evidence experiments/arithmetic/evidence/step8_function_D_output_v1
```

费用和最终完整性见[resource-closure.json](resource-closure.json)、[final-integrity.json](final-integrity.json)。封存后收尾收据另列，原目录和失败均保留，未解锁1000ps物理联合test或locked源。
