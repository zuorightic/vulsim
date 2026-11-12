# G归约融合D原型 v1

此后继包复用已发布小算子、S及shared函数，用G通用归约区域函数替换同级内部Add加总，并发射允许区域联合综合的RTL。D从源码重新编译、提取实际Query并计价；不读取候选价格表或最终PPA。

```
python3 -B -m experiments.arithmetic_dse.run_fused_d \
  --source-request /path/to/source-request.json \
  --period-ps 1000 --latency 2 --out /path/to/new-output
```

`--latency`包含外部capture、不包含输入服务launch。源请求与旧`run_function_d`格式相同，给出C++路径／SHA、顶层函数、valid端口及输入reset；可以使用相对于请求文件的C++路径。默认二进制为`build/G-reduction-20261112/rtlzz-fused-d`。重新构建时使用LLVM／Clang18和`cmake -S rtlzz -B build/G-reduction-20261112 -DCMAKE_BUILD_TYPE=Release`、`cmake --build build/G-reduction-20261112 --target rtlzz-fused-d -j4`；公共入口核对参数、消费者源码及已验证二进制身份，其他构建需重新完成软件数值／RTL核对后绑定。

选择规则保持：完整覆盖时，有预测可行解取最小总面积；全部违约取最大时序违约最小、面积打破并列。枚举截断或任一候选缺覆盖均不发射RTL。目标T在支持域内按数值计算，1000、1250、1373ps均有调用／验证证据。面积为S三所有者＋未融合节点＋唯一G区域＋重算shared，整级50ps只加一次；内部Add价格可以缺覆盖，不会拦截已由G完整负责的区域。

| 目标T ps | 选择 | 预测面积um² | 含50ps的数据级要求ps | 状态 |
| ---: | --- | ---: | ---: | --- |
| 1000 | candidate/quarter/view7 | 993.935 | 919.311 | predicted_feasible_selected |
| 1250 | candidate/half/view5 | 840.078 | 1049.899 | predicted_feasible_selected |
| 1500 | candidate/original/view1 | 761.772 | 1349.670 | predicted_feasible_selected |
| 3000 | candidate/original/view0 | 732.637 | 1870.773 | predicted_feasible_selected |
| 500 | candidate/quarter/view7 | 1055.538 | 887.185 | target_unmet |

这些是模型选择结果；预测数据级要求不是重新跑后端得到的最小时钟。非算术路径另外按原S保护检查。当前MAC的44个放置仅为有限搜索集；同一包在三输入加法图／1373ps产生4放置的完整选择和RTL，模型及选择规则不变。

5份入选RTL、44放置及新纯加法图各256周期通过；独立复算220候选及区域替换／S／shared／排序，7项拒绝检查通过。`selection.json`保留完整Query、域拒绝、分项价格、区域位连接和发射合同，`D.sv`含完整服务／core／capture，`D_core.sv`可单独检查归约区域；功能reset与独立写使能保持。用户暂缓reset时序资格，报告仍为`prototype-no-reset-timing-v1`；完整联合与`formal_D_selection`／`full_D_ready`仍为false。

实际交付根：`/home/zyrv/vulsim-artifacts/G-reduction-20261112-v1/outputs/`，各T目录包含RTL与轨迹。可搬移数值／原始标签回放见[证据](../../evidence/G_reduction_D_v1/README.md)，G函数见[模型说明](../asap7_G_reduction_v1/README.md)。旧D包、旧二进制和既有失败结论保留；本包没有覆盖旧37文件或25文件冻结。
