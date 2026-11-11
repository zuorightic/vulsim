# MAC32 A/B/C/D实测与最小周期证据

本包交付21条方法记录、19个真实物理实现（17个首次实现＋2个按预登记规则触发的临界复测），以及17个首次实现的完整setup最小周期核验。ASAP7，目标500／1000／1250／1500／3000ps；A为L=1，B／C／D为L=2，全部II=1。主结果是**面积＋同一固定物理实现的最小setup周期／最高频率**，setup达标与hold独立报告。

[全部结果与解释](/home/zyrv/vulsim-artifacts/step9-MAC32-ABCD-20261111-v1/results-v2/RESULTS.md)、[CSV主表](/home/zyrv/vulsim-artifacts/step9-MAC32-ABCD-20261111-v1/results-v2/ABCD.csv)、[JSON结果](/home/zyrv/vulsim-artifacts/step9-MAC32-ABCD-20261111-v1/results-v2/results.json)。

| 按1500ps目标实现 | 面积um² | 最小setup周期ps | 最高setup频率MHz |
| --- | ---: | ---: | ---: |
| A | 698.178 | 1499.796 | 666.757 |
| B | 761.134 | 1360.668 | 734.933 |
| C | 1354.774 | 1498.199 | 667.468 |
| D | 761.134 | 1360.668 | 734.933 |
| 同策略静态成本对照 | 781.473 | 1501.371 | 666.058 |

D在前四个目标与B选择同一RTL；3000ps改变寄存器位置，面积722.016um²、最小setup周期1735.386ps，满足该目标。C的固定静态quarter拆分在本例未得到优于B／D的面积或时序。本轮选择与模型均在PPA前冻结，不根据实测改选或调参。原locked源／模型测试职责未重分配，最终MAC数据不进入模型训练。

最小周期核验使用相同的OpenDB／单元／布局／全局布线寄生，将寄存器间、输入到寄存器、寄存器到输出三类路径的最坏setup计入，保持接口max delay=0.2T、min delay=0及原clock uncertainty。三类最坏slack重现原完整STA；在所求阈值上下0.1ps再次执行STA，全部下侧违约、上侧通过。没有重新综合、调整物理实现或搜索其他RTL。该周期对应各目标下优化得到的固定电路，不声称是整个实现空间的全局最小值。

本轮是TT、post-CTS global route估计寄生；完整setup包含reset，暂缓的是D预测侧reset保护。21条方法记录中有3条负hold，全部21条hold不足5ps，需独立复查，不能因setup通过而称签核通过。A@1500ps和静态成本对照@1500ps的两项复测均与首次面积／setup一致，不替换主表。C的逐节点／逐端点诊断仍有5个长报告超时，后续账本身份尝试在EDA叶启动前停止；这部分不在本包的完整回放范围内。完整PPA／最小周期核验与S/G模型联合资格分别记录，`full_D_ready=false`。

可在任意目录使用标准Python回放：

```bash
python3 -I -B replay.py replay --evidence .
```

隔离回放核对全部21条方法／19个grt面积与完整STA原始报告、17个周期路径分类计算和正负阈值检查、冻结RTL SHA，以及实际CEC／逐位Boolean状态／320周期仿真成功收据；不启动EDA，不访问原工作区。424成员按内容去重存入分块，封存时353157字节，最大分块小于512KiB。后补结算／收尾收据单列。

完整原始产物、全部失败与读取尝试保存在`/home/zyrv/vulsim-artifacts/step9-MAC32-ABCD-20261111-v1/`。原始归档`archives/ABCD-raw-v2.tar.gz`为555383467字节，共85576成员，已将每个成员实际恢复至临时文件并逐项验SHA；同盘归档，未删除原产物。原始归档的完整成员索引和便携包的指定回放范围不同；后补文档／结算不声称位于较早原始归档中。

2026-11-12按用户确认的范围，已将本次ABCD及拆分诊断新增的29个临时Python／回归／C++导出文件逐项归档、实际恢复验SHA后移出仓库，见[清理收据](temporary-tools-cleanup.json)。完整工具源码保存在`/home/zyrv/vulsim-artifacts/ABCD-temporary-tools-20261112-v1/source/`及对应tar.gz；旧阶段9模块命令属于历史记录，需从该快照恢复后才可执行。上述自包含`replay.py`和已发布模型／公共D入口继续保留，清理后隔离回放再次通过，37项冻结D交付文件不变。第4–8步文件依用户确认不在本次清理范围。
