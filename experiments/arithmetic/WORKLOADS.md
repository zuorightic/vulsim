# 九案例合同与宽图软件入口

本入口实现现行计划 W1 的语义／有限目标登记，以及 W2 的一轮公共软件贯通。数学合同见 [general_workloads_v1.json](../arithmetic_dse/configs/general_workloads_v1.json)，九份未分级 VUL C++ 源码见 [examples/workloads_v1](examples/workloads_v1)。这些源码由同一个生成器展开数学算法，流水级由 RTLzz 后续分配。

本轮 64 个声明结构／502 个实际放置全部导出并通过 48192 周期仿真；实际需求汇总、19 组针对性诊断、原预算触限与完整图／状态／RTL回放见[软件证据](evidence/workloads_software_v1/README.md)。可直接运行 `python3 -B -m experiments.arithmetic_dse.workload_evidence --reextract` 重提取全部正式T需求，不依赖原始本机产物根。

W2后继已增加公共所有者模式：真实Query v2／算子和G独占归属／公共provider／对应RTL共享同一计划，九例64结构／502放置在新模式通过48192周期；见[后继证据](evidence/workload_owners_v2/README.md)。历史v1包严格绑定旧源码，当前可用 `python3 -B -m experiments.arithmetic_dse.workload_owned_evidence --predecessor` 恢复冻结源码字节后同时核查两代证据，旧清单不改写。

新入口仍是软件与需求交付。原公共 D、49 项生产冻结依赖、模型质量和独立数据职责保持原身份；新代码没有给诊断价格授予发布资格。

## 已确认的首轮合同

以下语义和目标均在本轮逐项向用户确认；II 均为 1。L 包含输出 capture，输入服务 launch 的额外可观测偏移单列。T 是研究请求，允许结果为 target_unmet；不根据最终 PPA 改目标。

| 案例 | 首轮语义 | L | T（ps） |
| --- | --- | ---: | --- |
| MAC32 | a/b 各 32 位、c 为 64 位，结果模 2^64 | 3 | 500、750、1000 |
| Add512 | 两个 512 位无符号数，完整 513 位结果 | 4 | 750、1250 |
| Mul128 | 两个 128 位无符号数，完整 256 位结果 | 4 | 1000、2000 |
| Dot16 | 16 项 64×64 乘积之和，完整 132 位，无反馈／额外累加输入 | 8 | 1000、2000 |
| Horner64 | 四次多项式；x 与五个系数均动态 64 位；逐次乘加回绕 64 位 | 8 | 750、1500 |
| Barrett64 | 动态 m、μ；2^63<m<2^64，a/b<m，μ=floor(2^128/m) 为 65 位；一次修正，规范结果 | 8 | 1000、2000 |
| Karatsuba256 | a/b 为 256 位、动态 c 为 512 位；完整 513 位结果；递归到≤64 位基例，保留中间增宽 | 8 | 1000、2000 |
| Montgomery256 | 8 个 32 位 limb，操作数扫描完全展开；动态奇数 m>1、a/b<m、n′=-m⁻¹ mod 2^32；输出 a·b·2⁻²⁵⁶ mod m | 32 | 1500、3000 |
| NTT8×64 | 固定 Goldilocks p=2^64−2^32+1，ω=7^((p−1)/8) mod p；正向、不缩放、自然序；各输入<p，每蝶形后规范约简 | 16 | 1000、2000 |

NTT 的 twiddle、p、μ为用户明确确认的编译期常量，模乘调用同一 Barrett 数学展开。其余模算参数为动态输入，合法关系由测试向量与参考合同保证；生成的硬件不额外校验参数。512 位回绕加法保留为软件回归变体。

```bash
python3 -B -m experiments.arithmetic_dse.workload_contracts
python3 -B -m experiments.arithmetic_dse.workload_sources \
  --case karatsuba256 --out build/karatsuba-source
```

源码生成不冻结模型、独立源或应用物理结果。应用身份只用于选择数学源和请求，不能进入价格特征。W1 登记不准入新 train/validation/test 源；现有 20 个其余算子独立源继续锁定。

## 公共软件链路

```text
未分级 VUL C++
  → 现有前端和 BEOPT
  → 基于已证明高位零的 Mul 精度规范化
  → 原始算子区域登记／通用块乘法展开
  → 未被保护区域拥有的 Add/Sub/ADC 内部拆分
  → 有限的拓扑级分配
  → 现有 valid/reset／保存链物化
  → 原生诊断 RTL＋实际状态＋宽 Query／G 需求
```

Mul 规范化处理 BEOPT 把“截断再补零”表达为宽掩码的情况：只删去已证明为零的高位，缩窄乘法后显式恢复原结果宽度。它不删除 128 位静态成本门禁，也不给未知高位作零假设。

加法按小端位段计算，每段多保留一位 carry，再送入下一段；减法用声明结果宽度内的 a+~b+1。动态 AddCarry 的首 carry 保留，跨级高位、部分结果和 carry 由现有流水物化器保存／对齐。受保护乘法区域继续使用原合法切组，不拆散其成员。

搜索对同一结构的实际调度单元按拓扑扩展。输入固定在首级、输出固定在末级，纯位连接采用最早依赖级；算术单元可进入各合法级。当前 beam 按每级算术单元数的平方和排序、级向量稳定决胜。它是可审计的软件结构策略，没有 ps/面积意义，不是正式 C/D 的性能选择。

合同登记的结构选择共 64 组：同一图的 Mul 统一选择块宽，未保护 Add/Sub 统一选择 limb 宽。每组 beam=8，八例最多 100000 次部分扩展，Montgomery 的有限后继为 200000 次；原始结构包含在内。Montgomery 首轮两个 100000 次触限记录保留，后继只调整该例软件预算，不改语义、T/L 或价格。逐组报告扩展数、丢弃的部分状态、合法叶、预算触限及失败；beam 丢弃数不冒充未枚举完整候选数。只有小域耗尽时才标记在该连接语法内枚举完整，不称全局最优。MAC32 原 505 放置仍通过原接口单独回归。

## 构建与运行

在主仓库根目录运行。构建使用现有 LLVM/Clang 18 依赖；功能验证需要 Icarus 的 iverilog/vvp，不需要后端工具或 PDK。

```bash
cmake -S rtlzz -B build/workloads-v1 -DCMAKE_BUILD_TYPE=Release
cmake --build build/workloads-v1 \
  --target rtlzz-workload arithmetic-wide-query-test arithmetic-limb-split-test \
    arithmetic-workload-owner-test -j4

python3 -B -m experiments.arithmetic_dse.workload_inventory \
  --case dot16 --binary build/workloads-v1/rtlzz-workload \
  --verify-rtl --out build/dot16-software

python3 -B -m experiments.arithmetic_dse.workload_inventory \
  --all --binary build/workloads-v1/rtlzz-workload \
  --verify-rtl --out build/nine-workloads-software
```

输出目录须不存在，失败保留。每例包含数学源／请求、各结构轨迹、实际放置、原生 RTL、状态及各数值 T 的压缩需求。`--verify-rtl` 检查独立写使能、held valid、气泡、溢出、在途复位及 L 对齐，并把 PATH 中的后端启动入口替换为立即失败的哨兵。

底层 C++ 入口也接受任何符合源元数据合同的输入图，不按案例 ID 分支：

```bash
build/workloads-v1/rtlzz-workload \
  "$PWD" experiments/arithmetic/examples/workloads_v1/add512/request.json \
  4 64 8 100000 build/add512-direct 0 750
```

参数依次为仓库、源码请求、L、加减 limb 宽、beam、扩展上限、新输出目录、Mul 块宽、数值 T，后面可接 `native|owned` 及模型绑定 JSON。块宽／limb 宽 0 表示保留原始结构；默认 native 保留前驱诊断输出。

## 需求、模型和下一边界

需求从真实编译图与物化状态提取：位事实、结果需求、静态位映射、全部数据／carry／selector 连接、同级消费者、capture、跨级保存、并行字数和功能逻辑分别保留。现有宽价格 ABI 可表达的部分调用同一 Python/C++ 特征接口核对；多消费者及 carry/selector 绑定等旧 ABI 缺口显式登记，完整连接仍在 successor_connections 中，不丢边或猜价。

G 仅提出同级可证明等价且成员独占的加法区域。共享内部结果、可能溢出的窄中间和、非零 carry、常量 1 等保留边界／拒绝；原始根和项在独立整数求值下检查等价。区域几何通过不等于新 G 价格、发射边界或联合资格通过。

| 责任项 | 已继承 | 本轮提供的需求／仍缺资格 |
| --- | --- | --- |
| 共享算子 | 原标签、统一窄／宽参数、真实宽特征与诊断函数 | 原始和拆分算子、掩码／尾块／carry／消费者需求；Add 面积、Mux 时延、常量和新连接资格仍待 |
| S | 状态投影、实际物化校验、逐类控制函数 | 1024/2048 位输入、宽字、32 级展开及多输出实际规模；控制时序失败与实际算术资格仍待 |
| shared | 独占共享计费函数 | 实际总 FF、根端口和功能规模；优先验证原参数复用 |
| G | 公共 word/prefix 几何与已有函数 | 宽／多区域候选、非零 carry 和常量／共享边界；零压缩失败与完整阶段资格仍待 |

native保留前驱原生诊断RTL。owned按实际图／放置／状态发现所有者，算子调用与宽采样共用的标量Core发射函数，G用独占的求和表达式模块替换成员Add。计划、提供者和发射器互相检查图／layout／profile／数值T身份；G从真实保存的slice／concat别名解析launch，不假定原始算子必有完整寄存器链。采样源码形式相容的软件检查已完成，完整物理边界资格仍待；服务输入和输出capture保持现有语义，尚未取得新的S/shared联合资格。

```bash
python3 -B -m experiments.arithmetic_dse.workload_owned \
  --all --binary build/workloads-v1/rtlzz-workload \
  --out build/nine-workloads-owned

python3 -B -m experiments.arithmetic_dse.workload_owned_evidence --predecessor
# 安装Icarus后，可从证据重新编译／仿真502份工作负载及1份边界测试
python3 -B -m experiments.arithmetic_dse.workload_owned_evidence --simulate
```

owned逐放置生成 `owners.json`、`costs-public.json`、`costs-diagnostic.json`、状态及RTL。默认只读取已冻结参数对象，不读独立标签、不拟合；同一算子跨位宽使用同一函数。只有完整可表示的观察才投影到v1价格接口；多个消费者、carry／selector、G消费者等不能删边投影。G的组合launch、多capture／消费者和相关输入根保留实际语义并显式拒绝不相容价格，功能非wire逻辑单列缺价。

本轮所有者验证使用每例首个已登记T，共64结构；前驱132份正式T需求仍保留。121733个算子中52527条可作精确v1投影；139622个唯一所有者中2694项取得当前参数的诊断估计、公共覆盖为0。完整阶段明确 `cost_uncovered`，S/shared／阶段预算接口不继承静态默认值。当前不运行模型选择，不授予完整价格覆盖，不替换公共D；这些分母不能写成正式T全矩阵或物理精度通过。

下一步需按 W2/W6 贯通相容的生产提供者和发射边界，保留本轮提取的实际连接；W3—W5 按共同因素修复和扩域，冻结后独立与完整阶段验收。新模型接入时使用同一声明结构／搜索范围比较 C/D，并完成同策略成本替换归因。

完整软件回归：

```bash
build/workloads-v1/testv2/arithmetic-limb-split-test
python3 -B -m experiments.arithmetic_dse.workload_software_validation \
  --binary build/workloads-v1/rtlzz-workload --out build/workloads-software-check
```
