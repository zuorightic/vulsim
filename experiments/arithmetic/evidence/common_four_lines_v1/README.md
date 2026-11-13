# 四线有限后继：完成结果与复现

2026-11-13。本包承接用户确认的软件、算子、S与G同步推进，完整产物根为`/home/zyrv/vulsim-artifacts/common-four-lines-20261113-v1`。10个准确物理点全部完成，10 synth／10 grt、0物理失败／重跑；S只读工作0新物理优化。公共D仍使用原价格，本包保持诊断身份。

| 工作线 | 本轮实际交付 | 验收边界 |
| --- | --- | --- |
| 软件 | operator／G／S统一诊断入口；Python与C++消费同一真实参数，含支持／拒绝；宽G的面积与时延成对特征及相容RTL | 后继Query可表达4096位，原公共D的整图Query、区域发现及生产路由仍未全部接通；诊断通过不授予价格资格 |
| 比较器 | 用可区分ordered／equality的非负数值工作量修正面积；固定train拟合后，旧validation面积源median／P95为3.15%／5.66%，此前18.41%／25.98%；时延参数保留 | 属于已消费validation回归，20个其余独立算子源仍锁定；Add／Sub／Mul参数不重拟合 |
| Mux | 5个旧train源的4608条真实node-maximum路径逐弧核对，30个阶段最差见证均来自selector；补2个不等宽train源×三周期及1个新validation源×1373／1700ps；固定6项数值时延函数 | 旧validation时延median从20.38%降至18.89%，仍失败；新validation时延4.01%，但未改面积函数的误差23.05%；未在该validation上重新选模型 |
| S | 9个train银行／33实现、四阶段264控制锥；132 synth／grt锥的控制sink语义0差异；33银行实现与505 placement×2服务模式，共1043组结构的同参数Python／C++消费通过 | native_valid仍23.44% median、保护348.64ps；不重拟合、不抬reserve、未用validation选特征；实际算术S／完整阶段尚未通过 |
| G | 宽特征与相容RTL；2个永久not_training源通过容量、标签、CEC及原冻结参数复用诊断 | 132位／16加数时延／面积误差14.54%／8.84%；512位／17稀疏项为23.98%／47.66%；正式支持正确拒绝两点，宽G没有发布 |

S全锥摘要的48组跨T对比最早差异均在placed；单独看下一valid FF分支的门深，34组最早在placed变化，14组深度不变。保存日志显示placement阶段包含移除综合buffer和时序驱动repair。该证据定位了后续调查范围，未证明单个命令的因果，也不将mapped深度、实际电容或实测slack加入在线Query。模型仍输出实现的路径要求`d+H`，不改成最快可达实现。

所有价格来自共享数值参数。T通过数值变换参与函数，结构支持只保存无标签的几何锚点；没有按候选、精确形状或精确T存价格。G使用同一冻结参数，外推结果显式为`unqualified_extrapolation`；没有靠删除支持门禁扩大资格。

## 无EDA复核

在仓库根运行：

```bash
python3 -B -m experiments.arithmetic_dse.common_four_lines_replay
```

此入口验证压缩证据和源码摘要，重算operator 174、Mux 31、G 2、S 1043项价格／状态，共1250项，并检查四种公共价格拒绝；无需OpenROAD、Yosys、C++构建或外部产物路径。历史绝对路径仅作来源记录。原49项生产依赖在本轮打包时逐项核对未变。

需要重跑原生数值消费时，先按项目既有LLVM／CMake环境构建`arithmetic-successor-function-test`；从本包的`*-input.json.gz`解压请求，以输入／输出JSON路径调用该二进制。它是诊断测试入口，不能替代公共D完整绑定。

`identity.json`列出各文件摘要，`summary.json`给出结论和资源检查点；`source-and-tools.json.gz`保留本轮临时驱动及各次失败前实现，`physical-labels/`保存10点RTL、标签、合同及CEC身份。完整ODB、布局布线图、原始日志和S中间导出留在仓库外。全包约3.5MiB，无单个10MiB文件。

## 恢复、费用与后继

S首批66次只读导出落在共享cwd，无法逐点绑定，已标无效；后继66次独立目录导出核对DB摘要不变。中间旧admission／task身份在工具前被拒绝，记录保留。G诊断提取初次误读仅train标签拥有的CEC字段，后继改读not_training资格收据并验证原CEC；Mux提取初次误用manifest的S专用data_role，改为核对准确准入、资格收据与标签的角色。其余构建／路径／工作目录软件失败全部保留，没有付费物理重跑或角色重分配。

调用容量已按用户授权显式迁移，保留28129条旧账。准确物理批次使用冻结policy v10；结算后policy v11只修正文档checkpoint字段到实际v5，额度和历史不变。当前容量为synth／grt各8192、累计叶wall／CPU 512／2048小时；4任务×4线程／8192MiB、单任务超时继续执行。费用按累计叶调用结算，不能将其当作日历耗时。

下一轮先审计Mux的存活选择逻辑面积及selector驱动响应；宽G用新的train／validation／独立职责分离“宽进位跨度”和“稀疏／短重叠”因素，不将这两个探针转训练；S继续沿保存的placement前后检查点定位valid分支驱动／负载与H，并验证能在发射前计算的假设。共同窄域发射路由、S实际算术／完整阶段、宽D生产绑定及三区覆盖仍需完成。
