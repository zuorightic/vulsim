# 算术实验：现行规划入口与历史契约

> **后续实施以 [lxy-plan-fix.md 第一章](../../mission/lxy-plan-fix.md) 为准。** 本文下面保留的是旧步骤二至三的说明，其中九案例/36条、旧B/C解析代价、D在线反馈、精确目标查表、旧预算及“尚未实现/已完成”均按当时版本解释。它们不是新四平台、五档整数位宽、43案例/688条及离线训练D的实施规则或验收结果。

目前可继承的是旧基线、ASAP7流程、区域保护、32×32 split16与位置验证方法；新成本、参数化范围、多平台、训练模型及正式矩阵仍按新计划逐项适配验收。已有步骤四/五及位置补验记录见新计划第二章；第三章保留规划修订与迁移，后续步骤实施按用户要求记第四章。[步骤一宽位宽补验](../../mission/lxy-plan-fix.md#step1-wide-acceptance)已完成，其新证据与旧基线分开验收。具体哪些引用可直接迁移、哪些须先改实现，见 [引用迁移审计](../../mission/lxy-plan-fix.md#plan-reference-migration)，统一导航见 [mission/README.md](../../mission/README.md)。

下面的文件和命令用于定位旧实现及复现对应历史结果；描述中的“当前”指该段形成时的版本。尤其 `backend/README.md` 已绑定后端v4历史冻结，不能以其旧额度替代执行代码读取的 `backend_policy_v5.json`；新计划中的容量包络也未自动生效。原导航轮次只补文档；本轮步骤一新增回归与support记账详见第四章，既有运行默认值、物理策略及历史冻结保留。

## 历史说明：步骤二至三

本目录固定算术语义、案例划分和对照规则，供后续算术展开、调度和 ASAP7 评估使用。当前交付是可执行的参考模型与规则原型；尚未实现 C++ CostProvider、区域约束调度、浮点硬件适配或物理搜索。

## 文件与接口

| 文件 | 用途 |
| --- | --- |
| `cases_v1.json` | 六个正式案例、三个保留案例、输入/输出位宽、精确计算定义与建库微基准清单 |
| `freeze_v3.json` | 当前有效冻结：实验模块迁入 `experiments/arithmetic_dse/` 后的 12 文件路径、SHA-256 和回归证据 |
| `freeze_v2.json` | 选择节点输出类型位宽修订的历史冻结；保留迁移前路径、原哈希及原验证证据 |
| `freeze_v1.json` | 首次冻结的历史记录；保留原哈希及原验证证据 |
| `experiments/arithmetic_dse/configs/semantics_v1.json` | 整数、浮点、异常标志、周期/复位契约 |
| `experiments/arithmetic_dse/configs/simple_cost_v1.json` | B/C 抽象代价、评估阶段、位宽规则和确定性选择规则；保留文件名，内容版本为 `simple-cost-v1.1` |
| `experiments/arithmetic_dse/configs/target_rules_v1.json` | 目标周期及固定 L 的制定规则；实际 ps 和资源预算待测量后填写 |
| `experiments/arithmetic_dse/configs/asap7_reference_v1.json` | 用户服务器配置与本机 ORFS 案例的参考设置及待核对项 |
| `experiments/arithmetic_dse/reference.py` | 整数/浮点独立参考；每次调用只求一笔事务的算术结果 |
| `experiments/arithmetic_dse/simple_cost.py` | 冻结前结构检查使用的标量代价原型，不读取 PPA |
| `experiments/arithmetic_dse/contracts.py` | 划分检查、固定 L、目标公式和冻结指纹校验 |
| `regression/arithmetic_contracts.py` | 无物理数据的契约检查，及可选的独立 SoftFloat 对照 |

以上路径除本目录中的文件外均相对于仓库根目录。

实验代码和配置位于 `experiments/arithmetic_dse/`，案例清单、冻结记录及本说明位于 `experiments/arithmetic/`。Python 导入使用 `experiments.arithmetic_dse`；从仓库根目录运行下列命令。

参考接口：`evaluate_case(case_id, inputs) -> outputs`。输入输出均为按声明位宽检查的无符号整数；浮点通过 32 位原始编码传递。拒绝缺少字段、额外字段、负数和越界值，不悄悄替输入做截断。参考模型的整数乘积/和先用 Python 精确整数计算，再按指定位置截断。

也可使用 JSON Lines：

```bash
python3 -m experiments.arithmetic_dse.reference <<'JSON'
{"case":"M1","inputs":{"a":3,"b":7,"c":5}}
{"case":"D1","inputs":{"a":17,"d":0}}
{"case":"F1","inputs":{"a":1065353216,"b":1073741824}}
JSON
```

输出分别为 `y=26`、`q=65535/r=17`、`bits=1073741824/flags=0`。后续 scoreboard 根据显式 L 对齐这些结果；复位丢弃在途历史，valid=false 时不比较数据，但 valid 和异常标志的事务对齐必须正确。

## 语义及案例划分

整数主范围为无符号 16/32 位操作数，完整乘积分别为 32/64 位。输出位宽和中间截断在案例方程中确定。例如 M2 的两个 16×16 乘积先完整保留，再形成 33 位和；H_M1 则明确先保留乘积低 32 位。商余参考使用 `divmod`，除零定义为 `q=全1、r=a`。

硬件除法包装必须先构造 `safe_d=(d==0)?1:d`，Div/Mod 只能读取 safe_d，再将商余结果与被除数、除零标志共同延迟，对齐后选择约定结果。输入复位为全零时，内部算术也必须有定义。这里的包装设计及小位宽穷举验证不替代步骤六对实际 BEIR 和内部复位求值的检查。

浮点只做 binary32 乘法，RNE，支持非规格化数和正负零，不采用 FTZ/DAZ。NaN 统一为 `0x7fc00000`，sNaN 和 0×Inf 设置 invalid。异常位按 `[NV,DZ,OF,UF,NX]` 编码为 `[16,8,4,2,1]`，每操作重新计算；乘法不会设置 DZ。F2 保留两次乘法、两次舍入，输出异常为两次标志的 OR。

下溢按 SoftFloat 的 after-rounding 语义判断：先按 24 位精度、无界指数舍入，再判定是否 tiny，不能仅检查最终编码的指数是否为零。例如 `0x00800000 × 0x3f7fffff` 的结果是 `0x00800000`，标志仍为 UF|NX。参考原型的独立对照检出了这个边界，已在冻结前修正并保留定向向量。

| 划分 | 案例 | 固定 L | 计算结构 |
| --- | --- | --- | --- |
| 正式 | M1 | 2 | 32×32 完整乘法加 64 位偏置，结果模 2^64 |
| 正式 | M2 | 2 | 两路 16×16 乘法形成 33 位和 |
| 正式 | D1 | 2 | 16 位动态无符号商余，含除零包装 |
| 正式 | D2 | 2 | 32 位动态商余，商加偏置并与旁路选择 |
| 正式 | F1 | 2 | 单次 binary32 乘法和异常标志 |
| 正式 | F2 | 3 | 两次 binary32 乘法串联，分别舍入 |
| 保留 | H_M1 | 2 | 32 位截断乘积与受选择控制的加法 |
| 保留 | H_D1 | 3 | 两级动态商余串联，分别包装除零 |
| 保留 | H_F1 | 2 | 浮点乘法与 32 位短旁路选择，旁路选中时标志为零 |

九个案例都定义了参考接口，硬件接入在后续步骤验证。保留案例不用于调整全局模型或搜索规则。微基准只覆盖基本算术/控制/寄存器单元，不使用正式或保留整图的 PPA 建模；D 允许预先冻结预算内的案例局部在线反馈，但不能将该结果回填全局模型。

## 延迟、目标周期和四组对照

L 按 `max(2, 重算术串行深度+1)` 在看主矩阵 PPA 前确定。A 保持原始边界壳 L=1，B/C/D 对同一案例使用相同固定 L，II=1。RTLzz 内部边界数为 L−1；改变 L 必须同步改变 simgen、rtlgen 和测试配置，主实验期间不能由后端自行放宽。

目标周期由该案例预先声明的校准路径单元得到。令 `d_i` 为同一 ASAP7 TT/RVT/NLDM 流程测出的组合单元加互连时延，扣除边界寄存器及重复时钟开销；令 `O` 为统一壳的 clk-to-Q、setup、不确定度及不重复计算的时钟预留：

```text
T_case_ps = ceil(O + 1.10 × max(max(d_i), sum(d_i)/L))
```

该规则同时考虑不可拆原子的参照和可用阶段数，不根据某组的胜负调周期；路径列表只用于制定相同输入约束，不能用其求和代替最终 DAG 调度。`O` 和 `d_i` 必须来自步骤三及建库的真实记录，不能从主/保留案例的 slack 反推或使用服务器旧案例的周期替代。缺测量即保持 pending；没有伪造的 ps 数值。主矩阵开始前还必须冻结真实 SDC 的 I/O/驱动/负载及资源预算。

A/B 关闭操作内部切分。B/C 使用同一抽象规则，C/D 在预算截断前使用同一有序候选配置清单。C 按最大级抽象代价、组合成本加寄存器位数等字典序选优，不读物理目标或实测反馈；D 使用后端模型和规定反馈。浮点/除法未开放内部边界时四组均保持其原子性，结果不能作为该类内部拆分收益的证据。

## B/C 规则原型及冻结边界

成本输入必须是指定阶段的规范化标量描述。条件/索引/进位不当作乘数数据位宽；只有有效的静态 known-zero 信息可缩减位宽。乘法输出位宽取当前 Mul 节点类型，后继 Trunc 不自动改变它。四种乘法示例的抽象 `(d,a)` 分别为 `(21,1024)`、`(21,1024)`、`(18,1024)`、`(18,256)`，全位宽 16/32 乘法的时延比为 6/7。

Ite 固定两数据路。Case 含默认分支，保持优先语义，k 路公式只作抽象近似。Lookup 先按实际 index 截断/掩码降低，再保守统计可达表项；未定义索引拒绝，不能按测试样本或相同表值删项。组内时延按关键路径计算，共享节点面积只计一次；独立 Div/Mod 不能因为操作数相同就按一个实现计费。未知算子拒绝。

选择节点（Ite、Case、Lookup 及按同一路径降低的 ArrayAccess）使用 `w=max(数据备选有效位宽, 输出类型位宽)`。这是一条输出位宽例外：即使 32 位输出的高 24 位已被证明为零，二选一仍按 `(d=1,a=32)` 计费；四路 Case 为 `(2,128)`，八路 Lookup 为 `(3,256)`。普通算术继续按有效数据输入/输出的最大位宽计费，乘法沿用单独的输出类型位宽规则。

节点成本为整数，5% 放宽使用精确比例 105/100。固定候选内通过合法整组移动减少寄存器；不同候选按规则排序。当前 Python 原型验证这些结构契约，尚不把合成的示例调度宣称为 RTLzz 已实现组约束。步骤五仍须对真实编译图验收初始放置、整组移动、边界和寄存器物化。

当前使用 `freeze_v3.json` 固定配置和相关源文件的路径及字节哈希，回归必须校验这份冻结记录。首次冻结前的报告必须显示结构检查通过，并且没有读取用于物理误差审计的 ASAP7 测量。步骤七再并列报告实测比值，不能据此重调本规则。正确性缺陷必须升级版本、说明原因并重跑受影响记录，不能静默改写已冻结内容。

2026-10-26 的独立复核发现 v1 将选择节点的输出类型位宽误用了有效位宽，低估面积并可能改变同延迟候选排序。修订将规则内容升级为 `simple-cost-v1.1`、位宽提取升级为 `effective-width-v2`，未读取 PPA 或调整公式系数。新增 13 项边界/防回退断言后，普通回归 20202 项、含 SoftFloat 回归 40602 项通过，其中独立浮点对照 20400 组。历史 `freeze_v1.json`、原报告及原 manifest 保留，原 12 文件的完整快照位于 `build/step2-selection-width-20261026-5rde1zku/before-v1/`；v1 应对这份历史快照校验。哈希一致证明记录对应的内容可核对，规则是否符合规划还需依靠针对性检查。

选择位宽修订的复现、修复前失败日志、两套结果和 manifest 见 `build/step2-selection-width-20261026-5rde1zku/`，该目录现作为历史证据保存。

随后按目录整理要求，将整个实验模块从 `tools` 迁入 `experiments/arithmetic_dse/`，配置及 SoftFloat C 适配器随模块一起迁移。10 个迁移文件内容逐字节保持一致；回归更新导入及当前冻结版本。`freeze_v3.json` 记录新路径及到 v2 的对应关系，规则内容版本仍为 `simple-cost-v1.1` / `effective-width-v2`。迁移后的普通回归、SoftFloat 对照和参考命令行入口均通过。v2 的原 12 文件及当时的文档快照保存在 `build/step2-directory-move-20261026-qu2qu0yc/before-v2/`；历史 v1/v2 中的旧路径表示当时布局，当前工作区按 v3 校验。

迁移验证与当前 manifest 位于 `build/step2-directory-move-20261026-qu2qu0yc/`。执行 `python3 build/step2-directory-move-20261026-qu2qu0yc/verify_evidence.py` 可核对当前冻结、两代历史快照、报告和 manifest 的哈希关系。

## 参考模型验证与 SoftFloat

```bash
python3 regression/arithmetic_contracts.py

ARITHMETIC_SOFTFLOAT_DIR=/path/to/flat/softfloat \
  python3 regression/arithmetic_contracts.py
```

普通回归只依赖 Python 标准库。SoftFloat 可选对照从用户提供的扁平源目录编译 f32_mul 及必要依赖，利用现有 RNE/after-rounding 实现独立核对结果和五位标志；适配器在每次调用前清空状态，不提供线程安全保证。未提供目录时报告 SoftFloat 未运行，不能写成对照通过。

本机可用来源为 `/home/zyrv/temp/rv64-archsem软著/softfloat`，源文件声明 Release 3d，带本地特化。本步骤使用它做独立参考并记录实际文件哈希；不宣称它是未经修改的上游发布。未将第三方源代码复制到仓库。后续可用规范 SoftFloat 构建替代，需保留同一语义、来源指纹及对照证据。

## 后端配置参考

用户服务器设置的 `CORNER=TC`、`ABC_AREA=0`、利用率 40%、布局密度 0.65、slang、层次优化和 M4/M6、M5/M7 引脚层已记录。旧约束只有 `create_clock`；实际接入需补充 I/O 延迟、驱动/负载、不确定度、reset 处理及 report_units 检查。官方 aes/uart 提供虚拟时钟和 20% I/O 延迟示例，但设计专用时钟延迟不应直接复制。

首版沿用单 VT/RVT、NLDM，禁用重定时和多比特触发器聚类。服务器 NUM_CORES=8 仅是资源参考，当前线程/并发/超时由步骤三试跑决定。以上都是配置准备，未完成 Yosys/ASAP7/OpenROAD 测量，不使用历史 1000/1100/1250 ps 作为新目标。

## 步骤三：已接通的后端入口

2026-10-26 已完成原始全位宽乘法核的原生生成、软件/Verilator 验证、ASAP7 TC/RVT/NLDM 综合、CTS 后全局布线、详细布线和 OpenRCX 提取，并完成步骤三复核修订。前一节描述的是步骤二的配置准备状态；当前流程、单位/面积定义、失败处理和运行参数见 `experiments/arithmetic_dse/backend/README.md`。B/C 的 `freeze_v3.json` 保持原内容，当前后端冻结为 `backend_freeze_v2.json`，策略为 `experiments/arithmetic_dse/configs/backend_policy_v2.json`，v1 保留为历史记录。

```bash
python3 -m experiments.arithmetic_dse.run \
  --out build/asap7-probe-new --stage final --period-ps 1500 --threads 2
```

1500 ps 为资源试跑周期；正式案例的目标仍按步骤二公式在建库后制定。当前主表阶段决定为 CTS 后全局布线寄生估计，详细布线另表复核预定覆盖及临界点。两套完整运行的时序与原始 ORFS 面积一致，单命令入口及错误输入失败定位也已验证。原始证据、manifest、资源及重复比较位于 `build/step3-asap7-20261026-93ltulln/`。

复核修订增加跨 session 后代树清理、目标周期建库维度及 TT 阶段判定范围。grt 只以 TT setup/覆盖判可行，hold 独立报告并使用 5 ps 工程复核带；详细布线仍检查 TT setup/hold，所有记录明确不代表多角签核。关键证据及两版源快照随仓库保存在 `experiments/arithmetic/evidence/step3/`，原始大日志/ODB/SPEF 保留在 build。无需 build 或工具安装即可核对：

```bash
python3 -m experiments.arithmetic_dse.evidence
```

本轮预算复核采用 `backend_freeze_v3.json`：共享物理调用账本立即启用，并导入历史失败与成功调用。六个综合目标改为 500/800/1000/1250/1500/2000 ps，案例矩阵仍为 36 条。两点相同不构成未测目标覆盖。D2/F1 接入后各做六点检查；预算资助检查提前到步骤五之前，包含实际案例目标补测和步骤四至六探针。运行 `python3 -m experiments.arithmetic_dse.budget --check-plan` 可查看当前不足，原上限不会自动放宽。此历史说明对应 [已归档的单平台旧计划](../../mission/archive/lxy-plan-v1-single-platform.md) 第一章§7.1、§7.4及第二章§3.9，以及 `experiments/arithmetic/evidence/step3_budget/`。

步骤三收尾升级为 `backend_freeze_v4.json`，见 `evidence/step3_closure/` 和计划 §3.10：已有关键路径明确经过乘法操作数到乘积的数据锥；预声明500/2000ps SDC对照固定ABC1500ps和绝对I/O300ps，两份实际综合网表一致，grt及共同1500ps SDC下的结构/面积/路径存在响应，500ps自身仍未达标。新增2 synth/2 grt后累计31/9/5，无待结算预约，无上限提高。采集协议v3将普遍六点改为必需参考/精确查询数据与代表性少量探测，D2/F1实现后检查。步骤三验收完成；D库、D2/F1硬件和主矩阵尚未完成，完整清单及预算仍在步骤五前闭合。B/C冻结内容保持。
