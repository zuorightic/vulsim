# 手写两级split16的VUL原始RTL后端测试

用户指定的500／1000／1500ps三档均已完成，共3 synth／3 grt，0 detailed，0自动重试。源码见[Top.vul](../../manual_split16/Top.vul)与[用法及周期检查](../../manual_split16/README.md)，公共vulrtlgen生成的原始RTL为[Top.generated.sv](Top.generated.sv)。没有手写或修改生成后的RTL，也没有通过D自动重新放置寄存器。

第一级保存4个16×16→32部分积、c和valid；第二级执行常量移位、平衡加法及最终加c。与此前BCD相同，L=2不含输入服务寄存器周期，II=1；独立输入写使能、held-valid、非零reset和无条件输出capture保留。原生RTL的320周期／262次valid数据检查通过，包含气泡、溢出和在途复位。

每格为**最高setup频率MHz／面积um²**；完整数据见[对照表](COMPARISON.md)、[CSV](comparison.csv)和[JSON](comparison.json)。

| 目标T(ps) | A | B | C | D | 手写split16 |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 500 | 707.702／754.646 | 879.955／824.295 | 704.820／1583.009 | 879.955／824.295 | 1072.063／944.988 |
| 1000 | 701.403／753.451 | 862.032／802.162 | 705.622／1471.370 | 862.032／802.162 | 998.718／846.369 |
| 1500 | 666.757／698.178 | 734.933／761.134 | 667.468／1354.774 | 734.933／761.134 | 908.495／830.156 |

同目标下相对D，手写版本频率提高21.83%／15.86%／23.62%，面积增加14.64%／5.51%／9.07%。A为L=1，其余L=2。共同ASAP7库／profile、种子42、密度0.65、ABC=SDC、I/Omax=0.2T一致；本次VUL原始RTL允许算术联合综合，此前ABCD保留算子层次，属于需要保留的对照差异。不能把改进全部归因于成本模型或仅归因于流水位置。旧模型、D输出及训练／测试角色不变。

频率来自TT、post-CTS global route估计寄生；固定OpenDB上的RR／IR／RO三类路径重现完整setup，最小周期上下0.1ps STA分别违约／通过。hold保留在comparison.json／csv及原始报告中，频率不代表多角或详细布线签核。

`raw-reports.json.gz`封存3点的实际manifest／metrics、原始面积与STA报告及最小周期检查；不包含新的临时Python。完整源、生成产物、工具与日志在`/home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/`。完整原始归档718成员／49994684字节，已逐项实际恢复验SHA，索引见该目录`archives/manual-split16-raw.tar.gz.index.json`；本包保存[恢复收据](raw-restore.json)。

费用见[结算](final-accounting.json)：3 synth／3 grt／0 detailed、19 support，叶墙钟364.425445秒、CPU719.52秒，pending=0，0收费失败；保留后续预算。后补文档与结算单列，不声称位于较早原始归档中。
