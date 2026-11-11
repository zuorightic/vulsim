# 显式两级16位分块乘加

本例按用户要求手写流水边界，计算`y=(a*b+c) mod2^64`。a／b为32位无符号，c为64位。

- 第一级：a／b各拆成高低16位，计算4个16×16→32部分积；保存部分积、c和valid。
- 第二级：将部分积扩展至64位、常量移位16／32位，做平衡归约并加c；保存y和valid。

代码使用`REGISTER`和`TICK_IMPL`确定两级，不调用D选择器或自动PIPELINE调度。输入服务寄存器、独立输入写使能、held-valid、非零reset、第二级无条件capture与此前MAC32一致。L=2不包括输入服务寄存器周期，II=1。

通过项目已有公共入口生成原始RTL并运行原生仿真：

```bash
build/vulrtlgen -m experiments/arithmetic/manual_split16/Main.utb \
  -o build/manual-split16-example -f
bash build/manual-split16-example/run.sh
```

`Main.utb`检查320周期／262次valid数据，包含连续事务、气泡、独立写使能、held-valid、溢出、非零reset和在途复位。原始生成RTL在`generated/sim/top.sv`，没有手工修改RTL或通过D重排。

2026-11-12已完成500／1000／1500ps三档ASAP7后端测量，共3 synth／3 grt，0 detailed；与此前同目标A/B/C/D的[频率／面积完整对照](../evidence/manual_split16_vul_v1/COMPARISON.md)及[结果证据](../evidence/manual_split16_vul_v1/README.md)保留。

| 优化目标ps | 本例最高setup频率MHz | 面积um² | 最小setup周期ps |
| ---: | ---: | ---: | ---: |
| 500 | 1072.063 | 944.988 | 932.781 |
| 1000 | 998.718 | 846.369 | 1001.284 |
| 1500 | 908.495 | 830.156 | 1100.722 |

共同ASAP7 profile、库、种子42、密度0.65、ABC=SDC及I/Omax=0.2T与此前实验一致。本例采用VUL原始RTL的算术联合综合；此前A/B/C/D保留算子层次，故本次是用户指定手写实现的诊断对照，不单独归因于成本模型。频率为TT全局布线估计寄生下的setup频率，hold另存结果。旧模型、D选择和训练／测试角色均不变。

完整生成目录、三档后端快照、临时驱动与原始归档位于`/home/zyrv/vulsim-artifacts/manual-split16-vul-20261112-v1/`；本轮临时Python仅留在该持久目录，不加入仓库。用户确认清理的旧ABCD临时工具另外归档于`/home/zyrv/vulsim-artifacts/ABCD-temporary-tools-20261112-v1/`。
