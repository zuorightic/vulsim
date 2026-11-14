# W1/W2 九案例合同、实际需求与软件证据

本包对应[现行计划 W1/W2](../../../../mission/lxy-plan-fix.md#general-model-W1)与[公共入口说明](../../WORKLOADS.md)。九例数学语义及首轮有限 T/L 已由用户逐项确认；未分级源码、结构语法和事务参考均已登记。本包交付宽图／内部拆分／有限放置／诊断 RTL 的软件证据。生产提供者、模型相容发射边界与独立／联合资格仍待，`full_D_ready=false`。

## 结果与分母

| 案例 | 声明结构数 | 返回并仿真的放置数 | 仿真周期 |
| --- | ---: | ---: | ---: |
| MAC32 | 4 | 30 | 2880 |
| Add512→513 | 4 | 28 | 2688 |
| Mul128→256 | 5 | 36 | 3456 |
| Dot16→132 | 9 | 72 | 6912 |
| 四次 Horner64 | 9 | 72 | 6912 |
| Barrett64 | 9 | 72 | 6912 |
| Karatsuba256 乘加→513 | 9 | 72 | 6912 |
| Montgomery256 | 6 | 48 | 4608 |
| NTT8×64 | 9 | 72 | 6912 |
| 合计 | **64** | **502** | **48192** |

每个放置检查 96 个周期，包含独立输入写使能、held valid、气泡、最高进位／借位、最大乘积、在途 reset 和输出 L 对齐。模算包含靠近边界的剩余类、Barrett 偶模数及 Montgomery 大小奇模数；Horner 对动态系数直接求多项式，NTT 对照直接 DFT，模乘对照大整数公式。所有 II=1，L 含输出 capture，输入服务额外偏移另报。

[validation.json](validation.json)另记录 **19 组针对性诊断、141 个放置、13536 周期、6144 项真实 Query 的 Python/C++ 特征核对、1472 项 G 整数替换检查**。它包含 L=1、512 位回绕加法、非整 limb 尾段、截断／增宽减法和动态首 carry 等回归；与上表有语义／结构重叠，不能相加宣称不同候选数。[limb-test.txt](limb-test.txt)保存独立 APInt 算术测试的 640 项结果，覆盖至 4096 位。

原 MAC32 接口的 4 结构／505 assignment 枚举仍完整，原始 inventory 压缩保存在 `legacy-505.json.gz`；本包回放检查该枚举轨迹，已有实际消费／RTL证据继续从[通用块流水包](../block_pipeline_common_v1/README.md)访问。

## 可复算内容

- `cases/`：九例原始软件收据、实际数学源／请求／语义与编译日志。
- `structures/`：全部 64 结构的原始图、placement 向量、物化状态、RTL、测试平台、仿真日志和每个正式数值 T 的需求。只排除可由 Icarus 重建的 `sim.out`。
- `diagnostics/`：19 组针对性图／状态／RTL／测试及原生 C++ 特征结果，另含强制预算停止。
- `history/montgomery100k.tar.gz`：原 100000 扩展上限的两个触限及其日志；后继仅把 Montgomery 上限改为 200000，六组均通过，实际最大扩展数 112826。原失败未重写为成功。
- [requirements.json](requirements.json)：从上述实际数据汇总的 W1 算子、S、G需求及旧 ABI 缺口；[provenance.json](provenance.json)保留原始产物根和继承关系；[manifest.json](manifest.json)绑定实现源码、源码合同及证据字节。

压缩档案约 45 MiB，最大单包约 3.1 MiB。原始目录为 `/home/zyrv/vulsim-artifacts/W1W2-software-20261113-v1`；早期 validation-v1～v4、初轮 inventory 和调试产物保留在该目录。本包回放所需的实际数据全部随仓库保存，不依赖该绝对路径。八例收据形成于 Montgomery 预算变更前，保留原全局配置 hash；回放逐项核对嵌入的有效 per-case 配置和源字节与当前合同相等，不伪造后继 hash。

## 回放

W2后继已更新三份本包冻结的C++源码。下面的原始命令适用于本包源码快照；当前工作树请运行 `python3 -B -m experiments.arithmetic_dse.workload_owned_evidence --predecessor`，它按原摘要恢复旧源码后核查本包，同时核查[所有者后继](../workload_owners_v2/README.md)。原manifest和所有收据保持不变，不用当前源码冒充旧版本。

在主仓库根目录执行；默认仅用 Python 标准库与现有算术特征实现，不运行 EDA、编译器或仿真器：

```bash
python3 -B -m experiments.arithmetic_dse.workload_evidence
python3 -B -m experiments.arithmetic_dse.workload_evidence --reextract
```

默认校验全部档案成员与实现身份，重建所有测试平台，对全部 64 结构的已存需求重算九例共同需求，并从 19 组原始图／状态重新提取 Query 和 G，核对已存原生 C++ 特征值及 G 整数等价。`--reextract` 进一步从全部 64 个原始图和状态重提取所有正式 T 的需求；[replay.json](replay.json)为本轮实际完整回放结果。

安装 Icarus 后，可重新编译并仿真全部 502＋141 份测试，而不是仅读取已存 PASS：

```bash
python3 -B -m experiments.arithmetic_dse.workload_evidence --simulate
```

本轮已实际执行该恢复复仿真，643份RTL全部重新编译／运行通过，见[simulation-replay.json](simulation-replay.json)；它是对上面两组放置的再次验证，不增加不同候选分母。

重新构建 RTLzz 并重做前端／拆分／搜索及实时 Python/C++ 检查的命令见[WORKLOADS.md](../../WORKLOADS.md)。所有软件驱动均把 PATH 中的 Yosys／ABC／OpenROAD／OpenSTA 入口替换为立即失败的哨兵；本轮后端启动尝试为 0。

## 对模型工作的实际约束

64 结构的 502 个放置在首个 T 下合计提取 151892 条算子需求，其中 102723 条可由当前宽前驱 ABI 表达；这只是接口计数，不能称完整价格覆盖。其余需求保留全部 `successor_connections`，显式记录多消费者、carry／selector、映射／capture 需求缺口。功能 bitwise 控制逻辑也单列待计价。相同算子跨位宽归于同一个后继提供者；数值范围不构成 shape 白名单或支持资格。

实际规模包括点积 2048 位输入、Karatsuba 513 位结果；Montgomery 最大 native 数据 229536 位／6896 字，单级最多 397 字。共提出 488 个独占 G 区域，几何可表达不授予价格或发射资格。S／shared 验证和宽 G／算子修复应使用这些实际需求，而非只放宽一个位宽常量。

当前 beam 按每级调度单元数平方和排序，只是软件结构策略；T 只进入需求，尚未以面积／时序函数选 C/D。原生诊断 RTL 尚未取得 `unsigned-wide-family-hierarchy-v1` 与 G 的相容层次合同。后续 W2 要贯通生产提供者／发射边界，W3—W6 要修复并冻结共享模型及资格，再按统一搜索范围选择和评价。0 新 EDA、0 拟合、0 新模型源准入、独立标签未读，原公共 D 和原冻结模型保持。
