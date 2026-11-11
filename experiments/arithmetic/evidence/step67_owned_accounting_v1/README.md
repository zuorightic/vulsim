# 第6—7步：互斥计费后继与零G复验

本包对应[规划§7.72](../../../../mission/lxy-plan-fix.md#step67-accounting-successor)。本轮修正边界／连线／预留的组合口径，沿用原小算子发布函数、S面积系数和非算术guard；不新增物理测量。原[pilot失败证据](../step67_joint_pilot_v2/README.md)、原逐节点reserve及全部test角色保留。

训练侧648条S路径／24源组导出完整边界点值：input_service→native 236.6864775ps、native→native 147.7647705ps、native→external 155.316833ps。原节点train中110个含真实算术owner间wire的点／11源组导出0.091858ps线值，均按完整源等权中位数。原88.034302ps单条S data／control wire最大值不再逐BEIR语法边叠加。状态相邻wire归S完整边界；纯位连接本身不收单元时延，位映射、操作数、capture、扇出及寄存器边界保留。

| 1500ps验证阶段 | 原含预留总值ps | 零G点值ps | 单次50ps预留后ps | 实测T−slack ps | 点误差 |
| --- | ---: | ---: | ---: | ---: | ---: |
| placement-0／s0 | 1229.623488 | 803.759033 | 853.759033 | 756.241394 | 6.2834% |
| placement-0／s1 | 1499.314616 | 987.912824 | 1037.912824 | 861.015381 | 14.7381% |
| placement-1／s0 | 1881.112596 | 1194.328687 | 1244.328687 | 1045.252319 | 14.2622% |
| placement-1／s1 | 882.770194 | 632.287857 | 682.287857 | 554.334534 | 14.0625% |

点误差median／P95为14.1624%／14.7381%，通过此pilot的15%／35%数值门槛。决策值含预留后的距离另报19.7955%／23.0823%，不当作点预测精度。校准规则事前固定为“validation最大正阶段残差＋50ps”，四阶段正残差为0，所以仍为50ps，只加一次；它是候选经验预留，未获独立安全资格。原逐节点guard对照完整保存。时延和面积在两位置间的排序均与实测一致，面积预测保持原字节含义和数值。

点计费后继用原S／节点train导出；两个serial位置仅为combination_validation，用于复验和整级reserve候选校准。未读取联合locked_test，未改节点支持域。36项真实C++编译图／位置／T请求与独立Python一致：18候选覆盖，18保留原拒绝；96个底层节点查询78覆盖、18拒绝。shared／wide_reduction／cross_stage_saved_value的节点联合负载缺口不能用G兜底。

实测路径的节点、S／clock／相邻wire、算术间wire分解严格守恒；节点函数误差和独立最大值相加的保守性另列。shared clock面积仍未合格，placement-1的hold −0.523505ps仍失败。当前只有一个完整源、一个物理T、四阶段，不能推广为连续目标域或完整联合合格；本T两位置setup均满足，尚未检验实测违约样本上的错误setup可行预测。`zero_G_joint_qualified=false`、`full_D_ready=false`，本包不发布正式D价格。

软件证据包含12项真实C++拒绝检查、真实同宽Assign→Cast不变性、12个真实cut插入76个冗余别名、移位／补零／截断、共享扇出／capture、寄存器重启以及6项非法位图负控。C++原生执行结果由收据与封存输出保护；便携回放独立计算其位连接和价格，不在隔离回放时重新编译C++。

从仓库根目录执行，输出不依赖实时源码或EDA安装：

```bash
python3 -I -B experiments/arithmetic/evidence/step67_owned_accounting_v1/replay.py replay \
  --evidence experiments/arithmetic/evidence/step67_owned_accounting_v1
```

[manifest.json](manifest.json)封存4182个成员，含原物理packet、原失败、原模型、新计费参数、训练审计、真实图、候选校准和后继源码。隔离回放已通过3394端点重读、训练点分区／源等权重算、Python／C++结果、语义正负控和完整阶段误差分解。训练审计可重算648条路径的分区和统计，但小包不重新访问全部原S训练ODB；实际Liberty／net验证及SHA来自训练提取叶任务，完整原训练产物继续按其原归档留存。

完整本轮产物保留于`/home/zyrv/vulsim-artifacts/stage67-accounting-20261111-v1`；[restore-proof.json](restore-proof.json)记录15个产物成员实际归档恢复及逐文件校验。原pilot完整物理产物、所有失败和本轮build收据均保留；同盘恢复不是异机备份。封包后补入的README、最终完整性和费用结算在本目录另存，不冒充已进入较早归档。

最终候选SHA256为`1489c9caf94f1c9c676c5f5b439d09baefb77495154e6b7cfdb36d0262a59b07`。[integrity.json](integrity.json)已核对25项原冻结推理源、8项新实现源、节点发布、原S绑定／参数及后续保留额度。

本轮费用见[resource-closure.json](resource-closure.json)：0 synth／0 grt／0 detailed、17 support、135.085524秒墙钟／271.66秒CPU，pending=0。按`build/step67-accounting-20261111`全部commands的reservation精确选取，包含初次未配置新目标的build失败，不重收父pilot物理费。后续688 synth／688 grt／86400秒墙钟／172800秒CPU／30GiB保留额度通过核对。未git add／commit／push。
