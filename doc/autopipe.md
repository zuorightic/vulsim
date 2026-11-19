# 使用冻结 v10 模型生成 RTL

模型参数位于 `vullib/models/autopipe/`，推理、候选选择、编译入口和软件测试位于 `tools/autopipe/`。示例输入位于 `example/autopipe/`。这些文件足以在新检出中重新编译 RTLzz 并生成 RTL，不需要历史实验目录、服务器脚本、后端数据库、研究账本或本机预编译程序。

ASAP7 使用论文实验中的冻结 v10 完整诊断模型；Nangate45 使用其冻结 N5/N6 参数包。参数、局部本体预算、等效采样周期反解以及完整候选计价和排序保持原实现。R1～R5 修复版未包含在这个发布入口中。迁移过程中只调整了资源路径和外围调用接口，没有重新拟合响应。

## 依赖和编译

从包含本目录的版本拉取仓库，并初始化 RTLzz 子模块：

```bash
git clone --depth 1 --branch master \
  --recurse-submodules https://github.com/zuorightic/vulsim.git
cd vulsim
git submodule update --init --recursive
```

需要 Linux、Python 3.10 或更新版本、CMake 3.20 或更新版本，以及 LLVM/Clang 18 开发包。功能仿真使用 Icarus Verilog。Ubuntu 已配置 LLVM 18 软件源时：

```bash
sudo apt install python3 cmake make g++ llvm-18-dev clang-18 libclang-18-dev iverilog
python3 -B -m tools.autopipe check-models
python3 -B -m tools.autopipe build --jobs 4
```

构建入口从当前 RTLzz 子模块源码生成 `build/autopipe/rtlzz-workload`，并保存编译输入与程序哈希。生成前会核对本地构建收据。修改编译器源码或头文件后，重新运行 `build` 命令即可。使用其他构建位置时，将相同的 `--build-dir` 同时传给 `build` 和 `generate`。

模型与生成入口位于 `master` 主分支。主分支保留既有提交历史，当前文件树已经移除历史实验产物；使用 `--depth 1` 只拉取最新版本，避免下载旧提交中的大文件。需要完整历史时，可在拉取后执行 `git fetch --unshallow`。

此路径不需要 CIRCT、Yosys、OpenROAD、ORFS 或 PDK。它查询已经冻结的离线成本函数；取得新的物理面积和时序报告需要另行运行后端。

## 选择 D 并生成 RTL

在仓库根目录执行：

```bash
python3 -B -m tools.autopipe generate \
  --workload mac32 --platform asap7 \
  --period-ps 950 --latency 2 \
  --out build/mac32-asap7-D --check
```

生成 `build/mac32-asap7-D/D.sv` 和 `selection.json`。RTL 顶层模块名为 `Workload`。输出还保存实际候选、静态代价、预算反解与评分轨迹。`--check` 将生成的 RTL 与独立整数和周期参考进行 96 周期仿真，覆盖复位、独立输入写使能、valid 保持及气泡。

Nangate45 使用相同接口：

```bash
python3 -B -m tools.autopipe generate \
  --workload mac32 --platform nangate45 \
  --period-ps 1500 --latency 2 \
  --out build/mac32-nangate45-D --check
```

`--latency` 为包含输出 capture 的流水级数 L，输入服务 launch 另增加一周期。`--period-ps` 是完整候选的请求周期；算术节点通过保留的本体预算和等效周期算法查询模型。参数包与结果保留 `diagnostic_only`、`full_D_ready=false` 等原有范围标记。

`selection_status=target_met` 表示预测满足请求；`target_unmet` 表示在本次有限候选中仍有预测违约，选择器按冻结规则取违约较小的完整候选。它们均为模型预测，物理 setup/hold 是否满足需要实测。

输出目录必须尚不存在，以免覆盖已有结果。默认软件预算为 300 秒，可用 `--timeout-s` 设置不超过 3600 秒的上限。超时或编译失败会保留 `failure.json` 和已有日志，不把部分搜索冒充完成选择。`--candidate-limit` 默认 256，上限 4096。

## 输入和候选范围

随仓库保留九个数学源：`mac32`、`add512`、`mul128`、`dot16`、`horner64`、`barrett64`、`karatsuba256`、`montgomery256`、`ntt8x64`。它们是重新生成候选的输入，不包含后端产物。复杂源原有的软件稳定性、模型覆盖或求解耗时限制继续存在；提供源文件不等于所有 L/T 均能成功生成。Nangate45 的实证应用范围为 MAC32、Add512、Mul128。

每个已登记源使用 `vullib/models/autopipe/workloads.json` 中的冻结结构语法。可显式指定有限的乘法分块和加减法段宽：

```bash
python3 -B -m tools.autopipe generate \
  --workload mul128 --period-ps 1450 --latency 2 \
  --mul-block-widths 0,32,64 --add-limb-widths 0 \
  --out build/mul128-finite-D --timeout-s 600 --check
```

候选由冻结的原生编译器以及静态平衡、依赖深度和模型压力调度产生；D 沿用冻结的预算、反解和完整代价选择。该入口对当前输入重新运行明示的有限搜索，不读取论文中保存的获胜结果，也不承诺在不同候选池或编译输入下逐字节复现所有历史选中 RTL。模型参数的数值一致性由独立的已保存预测回归检查。

`--method B` 使用不拆分的结构并按简单代价选择放置；`--method C` 在结构语法中按简单代价选择；`--method A --latency 1` 生成未拆分参考。结果中的带实际单位的预测仍来自后端代价模型，C 的抽象分数单独保存在候选记录中。

自定义输入用 `--source-request path/to/request.json` 替代 `--workload`。请求使用示例中的 `source` 元数据结构，包含 C++ 文件路径、文件 SHA-256、顶层函数、valid 端口及 reset 值。相对源码路径相对于请求文件解析；源码采用 `vullib/fixint.hpp` 中的无符号有限位宽类型。修改源码后需同步更新 `generated_source_sha256`。自定义请求可以生成 RTL；`--check` 需要随附的独立数学参考，因此仅用于已登记示例。

## 软件验证

```bash
python3 -B -m unittest discover -s tools/autopipe/tests -v
```

测试保留迁移前的 13 份软件预测，覆盖 ASAP7 八种 workload、Nangate45 三种 workload，以及 C 所选候选。测试逐项比较节点组成后的面积、完整周期和分级结果；在线计价时禁止文件读取和子进程。另检查模型资源修改及平台身份错误会被拒绝。测试输入约 221 KiB，不含后端数据库、实测标签或训练流程。

历史过程文档已迁入 [mission 文档](mission/README.md)。其中的冻结、物理测量与历史脚本引用用于研究追溯，当前模型调用以本页命令为准。
