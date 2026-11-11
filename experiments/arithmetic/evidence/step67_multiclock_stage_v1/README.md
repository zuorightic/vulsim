# 冻结通用函数的多结构、多T完整阶段与配对排序验证

对应[规划§7.76](../../../../mission/lxy-plan-fix.md#step67-multiclock-stage-validation)。复用已发布节点函数、S及[共享函数冻结后继](../step67_shared_function_v1/README.md)，参数、数值支持和50ps整级预留不变，G为0。源ID和placement ID只作职责／计费／追溯标识。

三个validation源分别是20位三乘并行、28位双乘宽归约、24位串联。先复用9个已有成功点的原始synth／grt快照，完整读取通过后，再按预先结构规则把early／first切分对调，物化第二种放置。三个新RTL各192周期、21项数值T的真实Python／C++价格与126负控通过后，登记并执行9 synth／9 grt；全部成功，未自动重试。所有源保持validation职责，不称作独立test，不解锁1000ps或locked源。

| 项目 | 样本量 | median误差 | P95误差 | 结果 |
| --- | ---: | ---: | ---: | --- |
| 完整阶段点时序 | 36阶段 | 7.4023% | 17.3985% | 通过15%／35% |
| 完整总面积 | 18实现 | 2.4089% | 4.8853% | 通过15%／35% |
| shared clock | 18实现 | 5.7373% | 18.8526% | 通过15%／35% |
| shared physical | 18实现 | 2.5179% | 7.8236% | 通过15%／35% |
| root repair | 18实现 | 7.7238% | 19.7289% | 通过15%／35% |
| S-only input→native | 18银行 | 4.5538% | 40.7895% | 通过50%分类门槛 |
| S-only native→external | 18银行 | 5.4165% | 17.3985% | 通过50%分类门槛 |

错误可行预测0，保守拒绝3，负hold4项均保留。9组相同源／T／L=2／II=1的两位置排序有7组完全一致。串联1500ps、归约1500ps的顺序不同，但实测面积差4.4017%、2.1543%，均在预登记5%并列带内；非并列排序错误0。这里的验收通过不等于每组都选中了实测绝对最小面积。

共读取36个物理快照，grt有15021个动态端点、42个常量输出，5019个逻辑FF检查及CEC通过。逐单元实际Liberty弧、方向、连接、面积归属、probe前后不变、SDC数值T与RC核对通过。967端点的真实500ps快照含5类读取负控，单弧删除保留该master的其他合法弧。首次负控脚本误把弧pair列表当作字典，失败和费用保留，读取器未改变。

**仍有明确的资格边界：**

- reset路径均有正setup裕量，但现有S提供者未单列reset时序保护。当前两位置的reset最小setup slack分别为+196.177582ps、+198.459366ps，不能据此宣称通用reset保护已合格。
- 新16位旁路和跨级保存值源的节点查询分别12／12、18／18覆盖；shared节点负载12项中6项因capture_banks=3超过冻结Mul上限2而拒绝。严格导出停点保留，后继只作结构／Query诊断，没有放宽模型或为这三类新增物理测量。
- 完整六类物理范围、新独立联合和正式D尚未完成，`zero_G_joint_qualified=false`、`full_D_ready=false`。本批三类／三档支持继续采用零G，不增加用于抵消误差的G回归。

3项保守拒绝的后补分解见[conservative-audit.json](conservative-audit.json)。基础函数误差约−28至+1ps，独立节点最大值相加的保守性约108–190ps，另外加单次50ps预留；S／邻接连线／clock边界差异另列。这项分解只读已经归档的真实路径，没有改参数或新增物理点。

隔离回放命令：

```bash
python3 -I -B experiments/arithmetic/evidence/step67_multiclock_stage_v1/replay.py replay \
  --evidence experiments/arithmetic/evidence/step67_multiclock_stage_v1
```

小包解包1390成员、逐文件验SHA，重算18项真实模型价格／108负控、213条位映射连接／117个capture、72个物理银行与36阶段、9组排序和最终结论，并严格重读一个完整967动态端点的grt见证。其他完整物理端点／状态／CEC资格由收费读取及原始归档承担；小包对其使用绑定原始标签SHA的紧凑分解，不重开全部ODB。

完整产物在`/home/zyrv/vulsim-artifacts/stage67-multiclock-20261111-v1`。`archives/multiclock-raw-v1.tar.gz`为232525804字节、39187成员，已经实际恢复逐文件验SHA；复用9点的原始快照由上一份已验证共享函数归档的SHA链追溯，不重复归档或收费。原目录未删除，本机同盘归档不防同盘故障。后补保守性分解和最终费用另存，不冒充进入较早归档。

最初封存叶使用了早先工作包已认领的全局任务名，Ledger在启动前拒绝，未执行归档或产生新物理费用；更换唯一任务身份后完成归档。所有有费用的失败保留，见最终[resource-closure.json](resource-closure.json)。节点、S、共享系数和各次冻结实现保持原字节，未git add／commit／push。

最终9 synth／9 grt／0 detailed、132 support，1905.081606秒叶墙钟／4124.98秒CPU，pending=0；便携包连最终收据约4.29MB、单文件≤512KiB。后续688／688调用、86400秒墙钟／172800秒CPU／30GiB保留核对通过。25项冻结模型／推理文件、旧5项源码／native二进制及原始快照保持原SHA，详见[final-integrity.json](final-integrity.json)。
