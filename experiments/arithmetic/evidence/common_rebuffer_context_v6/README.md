# W3／W4／W5：OpenROAD 重缓冲机制、成对 reset 训练与 carry 工作量 v6

本包交付有限后继 `W345-rebuffer-context-functions-v6`，保持诊断身份。新增 **4 个训练银行、12 个物理点**，全部完成、零失败、零重跑；训练内登记的 **66 个候选**全部保留。参数与实际 Python／C++执行在旧数据回归前冻结。未读取 20 个锁定算子独立源，公共 D 未切换，W3—W5 未整体完成。

模型／runtime SHA256：`3b4bab0b23935716fb444c3b9e2288ddef3fa7fb3a80ff90245860170fda9ae5`。原始产物及临时工具：`/home/zyrv/vulsim-artifacts/W345-rebuffer-context-20261114-v6`。前驱 [v5](../common_branch_load_v5/README.md) 不变。

## OpenROAD 源码与可辨识对照

`openroad-source-audit.json.gz` 保存源码版本、文件 SHA、行号／原文、匹配的既有 train 日志和工具身份。当前 placement 调用链为 `GPL::executeTimingDriven → Resizer::findResizeSlacks → repairDesign(initial_sizing=false) → fullyRebuffer(nullptr)`（placement parasitics 分支）。早期 `performGainBuffering` 虽存在，不能据此认定本调用执行了早期 sizing。

`Rebuffer::annotateLoadSlacks` 按实际负载路径记录 required 与根 arrival 的差；`fullyRebuffer` 先优化时序，再以正 slack 的四分之一加投影临界时延的 1% 作为面积回收余量。GPL net weight 又取决于本设计内相对 slack。它们说明逻辑 fanout 不是充分输入，但没有证明某一条命令独自造成某个 valid 分支变化。实测 slack／电容／树深／坐标只用于离线解释。

训练对照复用原四个银行的 20×32／16×64 位几何及 biased／uniform 输入连接，生成相反 reset 版本。为保持发射语义，root reset、word reset 和一致的 invert 一起改变；不称为只改变一个物理变量的因果实验。原／新成对银行及其全部 T 在 LOSO 中一起留出。新增四源与 3,686 份既有 contract 元数据核对，860 份带语义签名的合同无重合；未读取独立标签。

下表为其中同几何、同 uniform 根连接、1024 enabled bits、T=1500ps 的两种 reset／极性，都是 **train 观察**。完整锥和标签见 `paired-cone-audit.json.gz`。

| reset／极性 | valid 控制级 | delay ps | H ps | 完整 R ps | 到 valid capture 的映射门深 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 全零 | 0 | 433.70 | 102.40 | 536.10 | 5 |
| 全零 | 1 | 71.39 | 168.10 | 239.49 | 2 |
| 混合 | 0 | 77.46 | 89.86 | 167.32 | 2 |
| 混合 | 1 | 285.69 | 178.31 | 464.00 | 3 |

两条分支的主导关系变化，不能由 FF 总数或 fanout 的单个标量解释。此观察未进入价格查询，也未据此建立该源／T 的专价。

## W3／W5 有限共同形式

新增语义生成的 ripple carry 图及合法单输出门工作量，与 prefix 图保持相同算术语义，9,344 次整数核对通过。它是另一个工作量候选，不是 ABC 已选择 ripple 的声明。窄宽使用同一参数，T 为数值输入。

| 函数 | train 选择 | 源聚合 LOSO median／P95 | 已消费回归与关键限制 |
| --- | --- | --- | --- |
| Add 面积 | 原 v5 legal-pressure，参数完全相同；ripple 未胜出 | 8.41%／13.96% | 排除 train 等价源后 32 点面积 9.11%／19.40%；17+9 仍 22.45%、11+7 15.59%、带消费者 47+63 16.90% |
| Mux 时延 | 原 v5形式及参数不变 | 14.62%／19.33% | 旧两源仍 17.49%／26.56%，96 位源 27.56%；另两个已消费源 11.44%／12.05% |
| G 面积 | 原 KS 形式及参数不变；ripple 未胜出 | 3.76%／13.98% | 48 点 2.79%／16.87%；56 位源 32.93%失败；train64 位源 19.33% |
| G 时延 | 通用 carry topology／word-overlap 交互 | 4.56%／15.81% | 48 点 4.63%／14.22%，v5 同行 4.89%／13.94%；97 位源 17.48%→13.51%，48 位稀疏源 12.76%→16.35%退化 |

G 六个零压缩 train 源的时延 LOSO 为 4.73%／5.70%；全 train 的另外两个时延源仍 20.62%／17.07%，不能由汇总通过豁免。没有增加负 G 修正或按源取价。相关根、组合 launch、多消费者、跨区域连线及完整阶段资格仍缺。

## W4：新训练因素、逐源和尾部

合并后为 **17 银行、57 实现、342 条 S 路径**；native_valid 为 114 条，13 个留出 fold（四对合并、其余独立）。试验原分支形式、reset-polarity load、competing-state context，2 links×2 objectives×3 alpha，共36个S候选；以银行、逐路径、服务／native、全零／混合 reset 的源等权 log-MSE minimax 选择。原分支形式胜出，新上下文没有赢。其它三类 S 函数及 reserve 完全继承。

| native_valid 口径 | median | P95 | 状态 |
| --- | ---: | ---: | --- |
| 银行最大值，成对 LOSO，按源聚合 | 17.54% | 29.19% | 失败 |
| 逐路径，先按源聚合 | 13.03% | 23.14% | 不能代替银行验收 |
| 114 原始路径直接计分 | 10.42% | 38.14% | 尾部失败 |
| 服务分支，按源聚合 | 8.66% | 31.12% | 逐源仍有失败 |
| native 分支，按源聚合 | 17.05% | 23.97% | 失败 |
| 全零 capture，4 银行，逐路径按源聚合 | 17.51% | 30.42% | 失败 |
| 混合 capture，13 银行，逐路径按源聚合 | 12.86% | 15.52% | 不豁免全零／银行／尾部 |

不能将 v5 的13银行普通LOSO与本包17银行成对LOSO直接当作同集改进率。已消费因素银行回归 **24.54%／27.72%**，v5 同行21.89%／27.16%，退化保持；旧银行覆盖12/15，native_valid17.58%／24.20%，v5同行17.86%／23.12%。旧域只有银行聚合标签，逐路径保护无法测量，保持null。

原非负数值T LP校准在 paired LOSO 的114路径无漏点，但 guard excess median／P95 为 **272.90／379.78ps**，保守量不能隐藏。因素回归 native_valid／native_enable／input_valid／external_valid 的逐路径保护漏点为0／0／0／1；旧银行 external_valid 的银行max仍有1漏点。没有手工抬 reserve、改 R 标签或转嫁到 G。

**支持域缺口：** 新全零 `S-d1c86c9df37b5fed` 的500／1500／3000ps均被继承支持判据拒绝，57个训练实现实际价格消费覆盖54个；这些点只参与诊断拟合，未取得运行支持或物理资格。拒绝和训练统计分栏，不扩大旧支持域。宽深实际算术 S、shared 和 W6 独立／联合仍待。

## 冻结、软件和物理检查

- 355条 train／数值1700ps特征与价格请求、116条已消费回归请求，合计471条特征／471条价格请求，Python／C++一致；支持拒绝保留，另15项公共资格／畸形合同跨语言拒绝通过。
- 全部12物理点 CEC、状态保留位数、ABC=SDC数值T、I/O合同、覆盖和面积交叉检查通过。312条synth／grt真实路径、1,457个组合弧及312次删除真实Liberty弧的负例已封装，可脱离ODB回放。
- 新4项针对性测试和前驱11项测试通过。便携回放将所有推理期间的文件读取／子进程启动替换为报错；显式 native 参数只启动软件核对程序。前驱v5回放通过。
- 两项本轮软件工具失误保留：重建原spec时漏还原split；离线锥审计首轮错传area表而非pin/arc表。均在物理后端外修正、无新增EDA，不隐藏失败脚本／记录。

物理新增12 synth＋12 grt＋48 support，0 final、0失败／自动重跑；叶wall／CPU增量 **1497.04／3444.45s**。累计Ledger为synth3532／grt3501／final16／support22462，wall363662.56s／CPU741968.15s，pending=0。policy v11／budget v5、全局4任务、每工具4线程／8192MiB、300／1200s界限不变。674个源码身份、44个核心包文件约11.75MiB，最大文件约3.29MiB，每文件≤10MiB。原始ODB等重产物仍在产物根。

## 复现

从仓库根运行，无需访问原始产物目录或启动物理工具：

```bash
python3 -m experiments.arithmetic_dse.rebuffer_context_replay_v6
python3 -m unittest regression.test_rebuffer_context_v6
```

可选原生核对（需要 LLVM／MLIR 开发环境）：

```bash
cmake -S regression/rebuffer_context_build -B build/rebuffer-context-replay -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/rebuffer-context-replay --target arithmetic-rebuffer-context-test -j 4
python3 -m experiments.arithmetic_dse.rebuffer_context_replay_v6 --native build/rebuffer-context-replay/arithmetic-rebuffer-context-test
```

`identity.json`核对全部核心文件及实际源码；`source-and-tools.json.gz`归档源码／临时采集拟合工具；`physical-receipts.json.gz`保留本轮完整manifest、CEC和72条账本叶收据；`summary.json`、`evaluation--post-regression-audit.json.gz`保存各源／旧域／分支／保护和拒绝。包内回归全属已消费数据，fresh validation=false，20个独立源保持锁定。新公共价格、MAC32新D及九案例正式ABCD尚未启动。
