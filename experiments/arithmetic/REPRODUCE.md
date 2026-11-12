# 小算子、S／shared、G 与 D RTL 的复现

当前函数参数和 RTLzz 消费实现都已纳入 Git。新环境请使用包含本研究改动的分支，并拉取 RTLzz 子模块。下列入口支持从源码重新构建、核对实际计价和 RTL 功能，再接受新的数值 T 请求。原始冻结交付入口及模型文件保持原字节。

## 拉取与依赖

```bash
git clone --recurse-submodules https://github.com/zuorightic/vulsim.git
cd vulsim
git submodule update --init --recursive
```

已经从该分支克隆的用户，可在更新主仓库后重新执行子模块初始化命令。审计时的主仓库基线为 `f9075fdc05d2124985dd143c6e5a4a9def10397b`，RTLzz 为 `18c90bf76073de2df8e642485cddfae3818f7672`；本页介绍的便携入口需要同时包含其后续补丁。上游 `meng-cz/vulsim` 不保证包含该研究分支的模型与入口。

Ubuntu 在已配置 LLVM 18 软件源的环境中可安装：

```bash
sudo apt install git gcc g++ make cmake python3 \
    llvm-18-dev clang-18 libclang-18-dev iverilog
```

要求 CMake ≥3.20、Python ≥3.10、LLVM／Clang 18 开发包；功能检查使用 Icarus Verilog 的 `iverilog` 和 `vvp`。本条 D 路径不使用 CIRCT，也不需要 Yosys、OpenROAD 或 PDK。LLVM 软件源的配置见[项目说明](../../README.md#依赖)。

## 重新编译并验收本地程序

在主仓库根目录执行，构建目录必须尚不存在：

```bash
python3 -B -m experiments.arithmetic_dse.portable_fused_d prepare \
    --build-dir build/portable-fused-d --jobs 4
```

它会独立配置 `rtlzz/` 并构建 `rtlzz-fused-d`。此目标由 RTLzz 顶层 CMake 定义，不能用主项目的普通构建目标代替。本地验收包含：

- 检查原始冻结 bundle、六项依赖和消费者源码的 SHA。
- 对 MAC32 的五个 T、另一张纯加法图的 1373ps 调用同一 C++ 选择器，核对选择与数值结果。
- 用独立 Python 实现复算每个候选的节点价格、S、shared、G、位连接和最终排序。
- 对六份实际生成的 RTL 各运行 64 周期，检查独立输入写使能、held valid、气泡、溢出及在途功能 reset。

通过后生成 `build/portable-fused-d/portable-verification.json`。这份本地收据绑定当前可执行文件、源码和模型身份，属于忽略的构建产物。编译器和构建路径改变不要求新二进制与历史二进制逐字节相等，但必须通过上述软件验收。源码／模型／本地程序变更后，`run` 会拒绝旧收据，需另选新目录重新 `prepare`；失败日志也保留，不覆盖重试。

原入口 `experiments.arithmetic_dse.run_fused_d` 仍只接受原交付的二进制 SHA。它记录历史交付身份，新机器应使用本页的独立便携入口。

## 调用函数、选择候选并生成 RTL

```bash
python3 -B -m experiments.arithmetic_dse.portable_fused_d run \
    --build-dir build/portable-fused-d \
    --source-request experiments/arithmetic/examples/fused_d/mac32/request.json \
    --period-ps 1000 --latency 2 --out build/mac32-D-T1000
```

输出包含 `D.sv`、`D_core.sv`、`selection.json`、`selected.pipeline.txt` 和调用身份收据。`selection.json` 包含全部候选的价格、覆盖状态与选择理由。输出目录也须尚不存在。

`run` 的软件枚举／选择默认上限为 300 秒，可用 `--timeout-s` 显式指定不超过 3600 秒的有限上限；复杂图仍受 `--assignment-limit` 及完整覆盖检查约束。超时保留已有诊断目录，不能当作完整覆盖结论。

本例为 `a32*b32+c64`、无符号模 64 位结果、II=1。`--latency 2` 包含外部输出 capture，不包含输入服务 launch。1000ps 应选择 `candidate/quarter/view7`，预测面积约 993.934600um²、带整级预留的数据级最大要求约 919.310706ps。1250ps 应选择 `candidate/half/view5`，即 4 个 16×16 先寄存，第二级移位归约。可将 `--period-ps` 改成域内其他数值，并使用新的输出目录。

另一张图复用同一参数和选择器：

```bash
python3 -B -m experiments.arithmetic_dse.portable_fused_d run \
    --build-dir build/portable-fused-d \
    --source-request experiments/arithmetic/examples/fused_d/sum3/request.json \
    --period-ps 1373 --latency 2 --out build/sum3-D-T1373
```

源码请求使用 `D-source-metadata-v1`，登记 C++ 源码、SHA、顶层函数、valid 端口与输入 reset；源码路径可相对于请求文件。示例源码已随仓库提供，不依赖 `/home/zyrv` 下的产物。在线选择直接查询冻结的小算子函数、实际状态提供者和 G 位列几何函数。示例的 `expected.json` 只参与构建验收，在线价格与排序不读取其中的预期结果。

数值 T 范围为 500–3000ps，实际支持取节点、S、shared 和 G 全部语义／数值规则的交集。域内 T 不等于任意宽度、负载或级数均受支持。缺候选覆盖或枚举不完整时，入口保留拒绝报告，不输出 D RTL。全覆盖但无预测可行解时，按原规则输出最大时序违约最小的结果并标记 `target_unmet`；有预测可行解时选预测面积最小者。

## 无编译器回放已发布证据

```bash
python3 -I -B experiments/arithmetic/evidence/G_reduction_D_v1/replay.py
```

只需 Python 标准库。它验证已提交归档、60 个原始物理标签包、实际 Liberty 弧删除负控、拟合最优性、独立误差、五组 D 选择及另一张图的计价。这条命令复算保存的证据，不生成新的后端实现。

## 文件范围与尚未覆盖的复现

| 内容 | 仓库内的位置与状态 |
| --- | --- |
| 小算子函数 | `models/asap7_conditional_operators_v1/operators.json`，已提交 |
| S 参数与真实状态绑定 | `models/asap7_function_D_prototype_v1/reused-S.json`、`binding.json`，已提交 |
| shared、组合边界和预留策略 | 同目录 `composition.json`，已提交 |
| 服务语义证据 | 同目录 `public-service-witness.sv`，已提交 |
| G 通用归约函数 | `models/asap7_G_reduction_v1/reduction.json`，已提交 |
| 当前 D bundle | `models/asap7_fused_D_prototype_v1/bundle.json`，已提交 |
| C++ 实现 | RTLzz 子模块的 `src/backend/`、`main/arithmetic_fused_d.cpp`，已提交且 gitlink 对应其提交 |
| 便携构建入口和示例 | `../arithmetic_dse/portable_fused_d.py`、`examples/fused_d/`；首次使用需包含本页所属补丁 |
| 最新三级受限 D 专用驱动和完整物理产物 | 位于仓库外 `vulsim-artifacts/MAC32-L3-ABCD-20261112-v1`，本入口没有打包该实验流程 |

三级 MAC32 曾产生 324 个合法放置，其中 290 个可计价、34 个拒绝；受限 D 后端实验是用户另行允许的诊断范围。公共 D 仍要求完整覆盖，因此本页不宣称可以直接复现三级受限选择。4 位乘法叶、扩大 S／shared 规模和 G 稀疏归约域仍是[共同补齐项](../../mission/lxy-eight-workloads-audit.md)。八类大案例也须按其需求域继续补齐。

本入口保留 `prototype-no-reset-timing-v1`、`full_D_ready=false`：功能 reset 已检查，reset 独立时序及完整 S／G 联合资格尚未全部通过。便携验收不改变模型的物理质量结论。

从函数预测生成 RTL，与重新取得后端面积和最小周期是两项不同操作。后者还需要相容的 Yosys／OpenROAD／OpenSTA、ORFS、ASAP7 库、SDC、层次与归约融合策略；保存的报告和回放证据不替代这些工具。历史结果使用 TT、post-CTS global-route 估计寄生，不能承诺任意工具版本得到逐位相同的物理数值。
