# 算术区域接入 v1（步骤四）

本版提供 binary32 乘法的最小区域接入；浮点区域没有合法内部切分点。用于建立完整操作边界、核对语义并保护后续调度，不构成 D 代价库或性能收益证据。

## 接口与实现来源

```cpp
#include <arithmetic.hpp>
Int<37> packed = vularith::F32MulRNE(a, b);  // a、b 均为 Int<32> 位模式
Int<32> bits = Int<32>(packed);
Int<5> flags = Int<5>(packed >> 32);
```

`packed[31:0]` 是结果位模式，`packed[36:32]` 为单操作异常标志，按 invalid/divide-by-zero/overflow/underflow/inexact 的 16/8/4/2/1 编码。仅支持 binary32、RNE、tininess-after-rounding、canonical NaN `0x7fc00000`；乘法不产生 divide-by-zero。支持正负零、无穷、qNaN/sNaN、非规格化数、舍入、上溢与下溢，不使用宿主浮点计算。标志不跨操作自动累积，串联时每个出口保留自己的标志。

`vullib/arithmetic.hpp` 的 `F32MulRNEBody` 是 SoftFloat Release 3d `f32_mul`/`roundPackToF32` 算法的定宽位向量适配，保留原三条款 BSD 许可。归一化采用 23 次有界移位，指数使用偏置编码；舍入、jam 位和特殊值处理均落实为普通 Int 运算。既有 Python 参考 `experiments/arithmetic_dse/reference.py` 使用精确整数和显式舍入，是独立核对实现；它没有被翻译成 RTL 模板。可选 SoftFloat 共享库是第二套参考，来源文件指纹在回归报告中。

VUL 生成器在软件/RTL 的生成源码及运行库复制清单中提供本头文件。用户项目通过 `vularith::F32MulRNE` 调用语义接口；`F32MulRNEBody` 是内部模板入口。原生 RTL 和复位求值只接收展开后的普通 BEIR，不使用 `Call` 黑盒。

## 选定路线：优化前保护语义身份，再展开并隔离优化

v1 仅登记 `vularith::F32MulRNE` 这一编译器支持的语义 API，尚未实现任意整数图或外部算术库的通用结构识别。普通 helper 展开成复杂逻辑后，不会自动获得完整算术区域身份。

区域识别入口与区域元数据、优化隔离、调度约束分开。步骤五可以直接识别 BEIR 中的 Mul 操作并建立区域或子组，复用现有基础设施；内部合法切分及成本适配仍需扩展并单独验收。更换浮点实现时，若保留相同语义 API，可以替换展开模板而保留前端登记名字；模板版本及相应验证、缓存身份仍需更新。新增操作的接入方式由其实现路线决定。

采用 §5.1 的优化前保护路线。前端只把限定名 `vularith::F32MulRNE` 识别成保留语义 API，规范化为内部 API token；S11 按顶层函数及语义发生序号产生 `function/fp32_mul_rne/ordinal`。该身份在正常 BEOPT 前建立，既不是源码行号，也不是节点编号或临时名。同一 helper 两次内联会产生两次语义发生。

首轮正常 BEOPT 将每次操作作为受保护的 marker；marker 不参与 CSE。随后在既定接入点，编译普通位向量实现体，将每个 marker 展开成独立拥有的成员。公开输出仍是区域外的别名，区域内保留独立语义出口锚点。模板展开按实例分配节点；不存在先允许跨区域共享、再把共享内部节点改叫入口的步骤。

区域建立后的 BEOPT 使用显式导入/导出端口将图分成外部组件和各区域组件，分别运行**完整正常优化**，再按映射组装。区域内允许 CSE、常量折叠、结构化简和 DCE；不同区域内部节点不会合并。输入边界和字面常量可共享。出口锚点作为观察根保留，即使其值折叠成字面常量。元数据输入随别名替换更新；压缩编号显式更新输入、输出、成员，删除没有替换的边界会报错。节点克隆/组装同时规范化符号名并清理过期节点谱系，调试位置保留，不参与区域身份判断。

对使用同类算术区域的案例，A/B/C/D 使用相同版本的保护与隔离优化策略。跨组件符号依赖被转成独立输入端口，跨组件的符号值与静态事实传播可能受接口隔离限制；字面常量仍能参与区域内化简。此处描述优化范围限制，其物理影响方向和幅度尚未测量。候选比较在相同条件下解释，结果记录复用区域已有的 `sharing_policy`、`template_version` 和语义版本，不新增实验组。

每个区域记录 id、原算子、语义版本、模板版本、共享策略、输入操作数、出口及全部成员、合法切分组。模板版本为 `softfloat3d-bitvector-mul-v1`，共享策略为 `semantic-marker-and-isolated-BEOPT-v1`。本版恢复性复制次数为零；每实例的正常模板展开成员数单列于报告，不能当作物理面积增量。

## 校验、拒绝与原子调度

校验覆盖成员唯一、区域不重叠、输入/出口完整、节点类型与引用有效、完整图 DAG 以及区域收缩后的 DAG。内部成员经区域外路径重新进入区域，也会因收缩环被拒绝。非出口内部节点不能被外部消费者使用，不能把内部共享直接重命名为输入。

原子调度将区域收缩成调度单元，保留内部节点的拓扑次序。初始调度和减寄存器局部移动均以整个单元为粒度；区域时延按真实入口到出口的最长依赖路径求值，不能累加所有成员时延。评估器拒绝同一区域成员分属不同级；物化后重新检查元数据、源值对齐及寄存器账目。区域输入更新为该计算级实际使用的延迟节点。

`legal_cut_groups=[]`，因此 A/B/C/D 的所有调用者都受同一原子不变量约束。回归在四种延迟权重设置下分别验证；这里使用既有调度器的延迟权重测试共同不变量，不将其称为 B/C v1 成本适配。完整四组选择器、候选枚举、真实 BEIR→成本适配和 C/D 合法子组尚属步骤五，不能将这里的共同原子校验写成主矩阵已经完成。任何非空内部切分声明都明确拒绝。

该路线不依赖普通整数图的启发式浮点识别，也没有“识别失败后继续单节点调度”的回退。损坏或无法维护的区域直接编译失败。六类最低用例均成功接入，无未完成的识别/恢复案例。

## 回归与证据

运行环境需要 LLVM/Clang 18、CMake、C++20 编译器和 Verilator。默认启用 CIRCT，要求 PATH 中存在 `circt-opt`；缺少工具时明确报错。`VUL_REGRESSION_CIRCT=0` 与总入口 `regression.sh --no-circt` 一致：继续执行区域、软件、原生 RTL 和相关原生单测，仅跳过 CIRCT 专属检查，并输出 SKIP 及原因；即使工具存在也不会执行 CIRCT。

```bash
python3 regression/arithmetic_regions.py
VUL_REGRESSION_CIRCT=0 python3 regression/arithmetic_regions.py
python3 regression/arithmetic_regions.py --softfloat /path/to/flat/softfloat
python3 -m experiments.arithmetic_dse.regions_evidence
```

默认以 `-j2` 构建根项目及独立 RTLzz 测试，报告和大 RTL 留在 `build/step4-regions`；`--output` 可更换证据产物目录，`--skip-build` 使用已构建工具。回归固定 seed 20261027，组合/三内级流水 RTL 共用六类操作图：单操作、串联、并联、共享输入、完全相同的双操作、常量输入。参考核对同时比较结果与五位标志，覆盖 22 个边界位模式的笛卡尔积及 20,000 个随机输入；C++ 模板执行和生成 RTL 都与精确整数参考核对，可另与 SoftFloat 对照。

内部 CSE 专项先验证普通 BEOPT 会合并两个相同区域中的内部表达式，再验证隔离优化在每个区域内合并、跨区域保持独立；真实双浮点图也验证解除保护后会产生内部合并。编号反转、名称/调试信息变更、重复优化、别名替换、常量出口及损坏边界均单独检查。

VUL 端到端夹具在 `regression/arithmetic_regions/vul`，外部 LATENCY=4，软件、原生及 CIRCT 均检查连续事务、气泡与复位。原生 RTL 的窄 Add/Sub 结果使用显式尺寸转换，支持优化后操作数宽于结果的合法 BEIR，并通过严格 Verilator 警告检查。

可移植的小报告、成员映射、回归摘要及资源摘要在 `experiments/arithmetic/evidence/step4`；原始 `arithmetic_regions_freeze_v1.json` 与证据保留；复核修订由 `arithmetic_regions_freeze_v2.json` 固定当前代码、修复和三种 CIRCT 模式的证据，v1 源码在 `evidence/step4_review/source_v1` 保存。报告分别记录已执行/跳过的路径、原因及区域已有的共享策略和模板版本。核验无需 build 或 EDA。B/C `freeze_v3.json`、后端 `backend_freeze_v4.json` 及旧证据保持原冻结。

## 后续边界

本轮不启动物理测量。软件构建/生成/功能仿真由本轮命令清单记录，按现有账本的 leaf-backend 范围不计为物理后端支持调用；未调用 Yosys、OpenROAD 或任何物理阶段。累计物理账本及未结算预约检查随证据保存。

步骤五继续实现组约束与乘法内部拆分；本版只有完整区域单元。步骤六继续 D2 安全商余、F1/F2 的正式边界案例和实际实现后的代表性物理探测。独立浮点回归是有限验证，不是全输入形式证明。完整预算闭合、实际采集清单、D 代价库和主矩阵仍未完成；步骤五的批量物理工作前必须满足既有预算硬门槛，原 caps 不变。
