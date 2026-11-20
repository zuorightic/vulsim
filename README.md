# 泺源微架构建模与模拟平台

## 项目概述

泺源（LuoYuan）微架构建模与模拟平台，是一套用于处理器微架构建模、探索与调试的软件平台。基于新型高层芯片描述语言：可视化微架构语言（Visualized μarch Language，VUL）构建。

基于VUL，泺源平台为新型微架构设计者提供了：

1. 统一化的、结构化的通用微架构行为级设计描述
2. 周期精确的并行模拟，周期行为对齐到最终的RTL实现
3. 内置调试工具和性能统计工具
4. 自动化生成 RTL 代码
5. 多后端适应的复杂算数拆分并流水线功能

## 项目总架构

![项目总架构图](./doc/arch.png "项目总架构图")

## 项目地图

本项目为 Vul 的核心命令行工具链。相关项目目录如下：

| 组成部分 | 类型 | 职责 | 当前状态 | 入口 |
| --- | --- | --- | --- | --- |
| RTLZZ: VULC++-RTL编译器 | 子仓库 | 把VULC++描述的组合逻辑函数编译成verilog | 与主项目同步开发 | [RTLZZ](https://github.com/meng-cz/RTLzz) |
| VUL Tools VSCode 插件 | 独立子项目 | 用于可视化VUL开发的VSCode插件与工具包 | 开发中 | [VUL Tools](https://github.com/meng-cz/vultools) |
| 前端GUI（Demo）| 独立子项目 | 基于PYQT的VUL组件可视化工具Demo | 已停止 | [前端GUI（Demo）](https://github.com/meng-cz/VulSimGUI) |
| NullRVSim模拟器 | 独立子项目 | 基于VUL模拟代码架构的RISC-V微架构性能模拟器 | 开发中 | [NullRVSim](https://github.com/meng-cz/nullrvsim) |
| FASE-RV64系统调用仿真框架 | 独立子项目 | 为类RTL模拟提供微架构无关的多线程系统调用仿真支持 | 开发中 | [FASE-RV64](https://github.com/meng-cz/fase-rv64) |
| 案例项目：RISC-V TPU | 独立子项目 | 基于 VUL 原生设计实现的使用 RISC-V 指令扩展的可编程 TPU 计算核心 | 开发中 | [RISC-V TPU](https://github.com/meng-cz/oootpu-sim) |
| 案例项目：TCA-ADK | 独立子项目 | 张量计算适配评价框架，为后续张量加速器微架构探索与性能模拟提供算子分析和架构需求输入 | 开发中 | [TCA-ADK](https://gitee.com/wei-yanxuan/TCA-ADK) |
| 案例项目：3DCacheSim | 独立子项目 | 面向 Chiplet 多核处理器与 3D 堆叠缓存架构的系统级周期精确模拟框架 | 开发中 | [3DCacheSim](https://gitee.com/x1jia/large-cache-sched-sim) |

VULIDE、自动化测试、IP核库、更多示例项目等正在规划中。

## User Guide

- [1. VulCPP 简介（Get Started）](./doc/userguide/1-intro.md)
- [2. VulCPP header 常量与数据结构定义](./doc/userguide/2-header.md)
- [3. VulCPP 硬件模块定义](./doc/userguide/3-module.md)
- [4. VulCPP Main 模块（Test Harness）定义](./doc/userguide/4-Main.md)
- [5. VulCPP 无符号任意宽度整数类型 Int](./doc/userguide/5-uint.md)
- [6. VulCPP 通用块内存组件 BRAM/ROM](./doc/userguide/6-bram.md)
- [7. VulCPP 通用队列组件 QUEUE](./doc/userguide/7-queue.md)
- [8. VulCPP 阵列化子实例](./doc/userguide/8-arrayization.md)
- [9. VulCPP 波形追踪与调试](./doc/userguide/9-debugging.md)

介绍PPT：[Vul（泺源）项目介绍与工作整理](./doc/LuoYuan20260708-FULL.pdf)

## 依赖

基于 CMake 构建系统，支持 Linux 平台，Windows 下仍需测试。依赖 CMake 3.20 及以上版本，以及 LLVM/Clang 18 的开发包。

安装环境（以 Ubuntu / apt 工具为例，如果发行版仓库已经提供 LLVM 18）：

```bash
sudo apt update
sudo apt install git gcc g++ make cmake \
    llvm-18-dev clang-18 libclang-18-dev
```

如果当前 Ubuntu 版本默认仓库不提供 LLVM 18，可以参考 LLVM 官方 apt 源安装流程：

```bash
sudo apt update
sudo apt install wget gnupg software-properties-common
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 18
sudo apt install llvm-18-dev clang-18 libclang-18-dev
```

安装后可检查版本：

```bash
llvm-config-18 --version
clang-18 --version
```

### 测试环境依赖

两种 RTL 测试均需要 Verilator、C++ 编译器和 make，Python 回归需要 Python 3。Ubuntu 可在前述构建依赖之外安装：

```bash
sudo apt install python3 verilator
```

### CIRCT 后端依赖

在 RTL 生成时，可以选择 CIRCT 后端来获得更优化的 Verilog 输出。依赖 PATH 环境变量中的 `circt-opt` 可执行程序。可使用已有 CIRCT 安装；或下载官方的 [Release 二进制文件 版本号 >= 1.160.0](https://github.com/llvm/circt/releases)；从源码构建请参考 [CIRCT 官方构建说明](https://circt.llvm.org/docs/GettingStarted/)。将 CIRCT 可执行文件目录加入当前 shell 的 `PATH`，例如：

```bash
# 改成实际 CIRCT 构建目录；已安装的版本也可指向其安装前缀
export CIRCT_ROOT=/path/to/circt/build
export PATH="$CIRCT_ROOT/bin:$PATH"

command -v circt-opt
circt-opt --version
verilator --version
```

如需持久生效，可将上述环境设置加入自己的 shell 配置。

VULC++ 的 CIRCT 后端依赖部分 CIRCT pass，在使用不同的 CIRCT 版本时，运行下面这条命令检查相关 pass 是否可用：

```bash
circt-opt --help | grep -E -- 'comb-assume-two-valued|comb-int-range-narrowing|comb-overflow-annotating|comb-balance-mux|lower-seq-compreg-ce|lower-seq-to-sv|lower-comb|hw-legalize-modules|prettify-verilog|export-verilog' | wc -l
```

输出应为 10，表示所需 pass 都可用。

## 构建

初始化 git 目录与 submodule：

```bash
git clone https://github.com/zuorightic/vulsim.git
cd vulsim
git submodule update --init --recursive
```

构建命令如下：

```bash
mkdir build
cd build
cmake ..
make -j8
```

或直接在项目目录下启动构建+测试脚本：

```bash
# 默认：构建工具，运行完整回归
bash regression.sh

# 关闭所有 CIRCT 后端的测试
bash regression.sh --no-circt
```

构建完成后会在 `build` 目录下生成如下文件：
- `vulsimgen`：VulCPP 仿真代码生成工具，用于将 VulCPP 项目转换为可执行的仿真代码
- `vulrtlgen`：VulCPP RTL 代码生成工具，用于将 VulCPP 项目转换为可综合的 RTL 代码
- `vullib`：VulCPP 运行库目录，供生成的仿真/RTL代码使用；默认从当前目录下的 `./vullib` 读取，也可通过 `-l/--lib` 指定
- `userguide`：用户手册文档目录
- `example`：示例代码目录

## 运行示例：

```bash
# 生成仿真代码
./vulsimgen -m example/prodcon/Main.utb
# -m/--main: 必需，指定 Main 测试文件
# -t/--top: 可选，覆盖 Main 中 TOP(...) 声明的顶层模块路径
# -p/--project: 可选，覆盖 Main 中 PROJECT(...) 声明的项目目录
# -l/--lib: 运行库目录（默认 ./vullib）
# -o/--out: 仿真代码输出目录（默认 ./simout）
# -f/--force: 输出目录非空时跳过确认并清空；未指定时会询问
# 可用 -T/--tracefile 或 --trace 配置追踪，用 -B/--breakfile 或 --break 配置断点

# 编译生成的仿真代码 (build.sh 默认使用 g++)
cd simout
source build.sh
# 运行仿真（可执行文件名取 Main 文件的基本名）
./Main

# 一键按默认 build.sh 参数编译并运行，也可直接传递程序参数
./run.sh
```

```bash
# 生成 RTL 代码
./vulrtlgen -t example/prodcon/TopModule.vul
./vulrtlgen -t example/autopipe/mac32/TopModule.vul --auto-pipeline --target-backend asap7 --target-period-ps 1200 -o rtlout-autopipe
# -t/--top: 指定顶层模块文件；也可用 -m/--main 指定带 TOP(...) 的 TestMain 文件
# -p/--project: 项目目录（默认顶层模块文件所在目录）
# -l/--lib: 运行库目录（默认 ./vullib）
# -o/--out: RTL 输出目录（默认 ./rtlout）
# -j: 并行模块生成数（默认 1）
# -r/--release: 不保留中间 C++、调试文件和 TestMain C++ 文件
# --circt: 通过 CIRCT HW/Comb/Seq 后端而不是原生 RTL Emitter 生成质量更好的 RTL
# -f/--force: 输出目录非空时跳过确认并清空；未指定时会询问
ls -lah rtlout

# -m/--main 非 release 模式会生成 Verilator 驱动和一键构建/运行脚本
./vulrtlgen -m example/prodcon/Main.utb
cd rtlout
./run.sh
# 应当输出与运行 vulsimgen 生成的仿真代码相同的结果
```

`--auto-pipeline` 为 `PIPELINE` 块启用模型驱动的算术拆分与流水安排；`--target-backend` 选择目标工艺模型，`--target-period-ps` 指定请求周期，单位为 ps。完整用法见本节末尾的“后端代价模型驱动的拆分与流水线化”。

`vulrtlgen` 至少需要 `-t/--top` 或 `-m/--main` 之一；使用 `-m` 时，TestMain 中的 `TOP(...)` 可提供顶层模块路径。`-r/--release` 会省略中间文件，`--circt` 选择 CIRCT HW/Comb/Seq 后端。
使用 `-m` 且未指定 `-r/--release` 时，输出目录会包含 Verilator C++ 驱动和 `run.sh`。运行脚本需要已安装 Verilator 与 C++ 编译器，并会构建后立即启动仿真。可从任意当前目录调用该脚本，额外参数会传递给仿真程序。Verilator 构建日志和仿真日志分别保存在 `verilator_build.log` 与 `simulation.log`；失败时脚本会显示对应日志并返回失败状态。

### 后端代价模型驱动的拆分与流水线化

`vulrtlgen --auto-pipeline` 使用随仓库提供的冻结后端代价模型，为源码中声明的每个 `PIPELINE` 块生成算术拆分和流水放置候选，预测完整候选的面积与周期，再按 D 方法选择 RTL 并装回原 VUL 模块。它复用 VUL 的输入、输出边界寄存器，以及 valid 和复位逻辑。普通模块逻辑继续由原有生成流程处理。

当前可选模型为 `asap7` 和 `nangate45`。这里的“后端”指用于计价的目标工艺模型；RTL 生成期间查询已冻结的模型参数，无需安装 OpenROAD、ORFS、Yosys 或 PDK。获取实际综合、布局布线后的面积和时序，需要将生成的 RTL 另行送入物理后端。

**准备工具。** 以下命令均在仓库根目录执行，需要前述 LLVM/Clang 18、CMake 等构建依赖，以及 Python 3.10 或更新版本：

```bash
git submodule update --init --recursive
cmake -S . -B build
cmake --build build --target vulrtlgen -j4

# 检查两个后端模型的资源完整性及加载情况
python3 -B -m tools.autopipe check-models
```

首次启用自动模式时，工具会自动编译候选生成所需的 RTLzz 程序，并保存在 `build/autopipe/` 中；后续调用会校验并复用该构建。请保留仓库中的 `rtlzz/`、`vullib/` 和 `tools/autopipe/`。功能仿真还需要 Verilator、C++ 编译器和 make。

**生成 RTL 并选择目标工艺。** 下面以 MAC32 为例，分别使用 ASAP7 和 Nangate45 代价模型，候选粒度采用已登记的 `mac32` 配置：

```bash
./build/vulrtlgen -t example/autopipe/mac32/TopModule.vul \
  --auto-pipeline \
  --target-backend asap7 --target-period-ps 1200 \
  --candidate-profile mac32 \
  -o build/mac32-asap7-autopipe

./build/vulrtlgen -t example/autopipe/mac32/TopModule.vul \
  --auto-pipeline \
  --target-backend nangate45 --target-period-ps 1500 \
  --candidate-profile mac32 \
  -o build/mac32-nangate45-autopipe
```

`--target-period-ps` 是请求周期，数值越小，目标越紧。切换工艺模型或请求周期后，会重新计价、选择候选。上面的周期用于演示调用，最终是否达到请求，以预测报告和后续物理测量为准。

**设置流水级数。** 级数来自 VUL 源码中 `PIPELINE` 的第二个参数。MAC32 示例的 `example/autopipe/mac32/header.uh` 定义为：

```cpp
CONFIG(MAC_LATENCY, 2);
```

`TopModule.vul` 使用这个常量：

```cpp
PIPELINE(mac, MAC_LATENCY,
    IREG(a, Int<32>) { a = 3; },
    IREG(b, Int<32>) { b = 5; },
    IREG(c, Int<64>) { c = 7; },
    IVALID(iv), OREG(y, Int<64>), OVALID(ov)
) {
    y = Int<64>(a) * Int<64>(b) + c;
}
```

需要其他级数时，修改对应的 `CONFIG` 常量或 `PIPELINE` 第二个参数，然后重新生成。`vulrtlgen` 自动模式支持 L=1～256，命令行中的请求周期只影响计价与选择。L 包含输出捕获级；输入服务写入输入寄存器另有一个服务周期，功能和周期检查可参考随附的 `Main.utb`。项目需要通过 `PIPELINE` 声明待处理计算块；支持带 valid 和无 valid 的块。

**选择候选粒度。** 两个入口共用候选配置，支持以下三种用法：

| 用法 | 乘法分块候选／bit | 加减法分段候选／bit | 与 Python 入口的对应关系 |
| --- | --- | --- | --- |
| 省略 `--candidate-profile`，或指定 `generic` | `0,4,8,16` | `0,32,64,128` | 与 `--source-request` 的默认通用配置一致 |
| `--candidate-profile mac32` | `0,4,8,16` | `0` | 与 `--workload mac32` 的默认配置一致 |
| `--candidate-profile add512` | `0` | `0,32,64,128` | 与 `--workload add512` 的默认配置一致 |
| `--candidate-profile mul128` | `0,8,16,32,64` | `0` | 与 `--workload mul128` 的默认配置一致 |

还可选择 `dot16`、`horner64`、`barrett64`、`karatsuba256`、`montgomery256`、`ntt8x64`；这些配置的粒度来自 `vullib/models/autopipe/workloads.json`。profile 只提供候选粒度，输入计算始终来自 `-t` 或 `-m` 指定的 VUL 项目。工具不会根据输入目录名自动推断 profile。

`0` 表示保留该类运算的原结构。两个宽度列表的笛卡尔积构成结构搜索范围，每种结构还会产生流水放置候选。未指定 profile 的通用配置共有 16 种结构组合；经过流水候选生成和 RTL 去重后，实际候选数可以不同。

可用 `--mul-block-widths`、`--add-limb-widths` 覆盖相应列表，宽度不要求为 2 的幂。例如，为 MAC32 加入 24 位乘法分块，为 Add512 加入 96 位加法分段：

```bash
./build/vulrtlgen -t example/autopipe/mac32/TopModule.vul \
  --auto-pipeline --target-backend asap7 --target-period-ps 1200 \
  --mul-block-widths 0,8,16,24,32 --add-limb-widths 0 \
  -o build/mac32-custom-autopipe

./build/vulrtlgen -t example/autopipe/add512/TopModule.vul \
  --auto-pipeline --target-backend asap7 --target-period-ps 1000 \
  --mul-block-widths 0 --add-limb-widths 0,64,96,128 \
  -o build/add512-custom-autopipe
```

每个列表中的数值必须互不重复，两个列表最多组成 16 种结构组合。当前原生乘法拆分支持有效输入位宽不超过 128 bit 的无符号乘法，分块宽度为 2～128 bit；加减法分段支持 1～4096 bit。算子是否实际展开还取决于其有效位宽、常量信息和结构归属，例如段宽大于等于算子宽度时会保留原结构。候选粒度与模型是否能完整计价是两项条件；具体输入、级数和目标周期仍需经过本次生成验证。

**生成并运行功能仿真。** 使用 `-m` 指定随附的测试文件，工具会生成自动选择后的 RTL、Verilator 驱动和运行脚本：

```bash
./build/vulrtlgen -m example/autopipe/mac32/Main.utb \
  --auto-pipeline --target-backend asap7 --target-period-ps 1200 \
  --candidate-profile mac32 \
  -o build/mac32-autopipe-test

./build/mac32-autopipe-test/run.sh
# 成功时输出 AUTOPIPE MAC32 PASS
```

Add512 可将测试文件换成 `example/autopipe/add512/Main.utb`，并使用 `--candidate-profile add512`。其流水级数由该目录 `header.uh` 中的 `ADD_LATENCY` 设置，随附值为 4。

**查看 RTL 和预测报告。** 主 RTL 文件为输出目录下的 `top.sv`。每个 `PIPELINE` 块都有独立的 `*.pipeline_*.cpp.autopipe/` 报告目录；例如上面的 MAC32 仿真命令会生成 `build/mac32-autopipe-test/sim/top.logic.cpp.pipeline_mac.cpp.autopipe/`：

| 文件（相对于每个块的 `.autopipe/` 目录） | 内容 |
| --- | --- |
| `result.json` | 目标工艺、L、请求周期、候选粒度配置、预测面积与周期、选择状态及详细报告路径 |
| `search/selection.json` | 选中完整候选、流水放置、RTL 路径与哈希、模型预测和实际候选数 |
| `search/candidate-pool.json` | 本次使用的结构组合及完整候选记录 |
| `selected-core.sv` | 已适配 VUL 模块命名和接口的选中核心 RTL |
| `search.log` | 首次工具编译、候选准备、计价进度及错误信息 |

```bash
python3 -m json.tool \
  build/mac32-autopipe-test/sim/top.logic.cpp.pipeline_mac.cpp.autopipe/result.json
```

报告的预测范围是对应 `PIPELINE` 计算块及其边界寄存器，其他 VUL 逻辑的面积和时序需另行统计。`selection_status=target_met` 表示模型预测满足请求；`target_unmet` 表示本次有限候选中仍有预测违约，工具仍会输出按冻结规则选中的候选及剩余违约。物理 setup、hold 和面积应以实际后端报告为准。

**搜索预算和常用选项。** 候选更多或输入更复杂时，搜索耗时也会增加。可以减少宽度列表中的组合，或增加单块搜索预算，例如在命令中加入 `--autopipe-timeout 600`。

| 参数 | 作用 |
| --- | --- |
| `--auto-pipeline` | 为源码声明的 `PIPELINE` 块启用 D 方法的模型驱动选择 |
| `--target-backend asap7\|nangate45` | 选择目标工艺的冻结代价模型；启用自动模式时必填 |
| `--target-period-ps <ps>` | 正数请求周期，单位 ps；启用自动模式时必填 |
| `--candidate-profile <名称>` | 使用通用配置或已登记 workload 的候选粒度；默认 `generic` |
| `--mul-block-widths <列表>` | 逗号分隔的乘法分块候选，覆盖 profile 中的对应列表 |
| `--add-limb-widths <列表>` | 逗号分隔的加减法分段候选，覆盖 profile 中的对应列表 |
| `--autopipe-timeout <秒>` | 每个 `PIPELINE` 块的搜索时限，默认 300，可设 1～3600；首次工具编译不计入 |
| `-j <数量>` | 并行生成 VUL 模块的进程数，默认 1；单块候选搜索线程数由内部流程决定 |
| `-r/--release` | 省略中间 C++、调试文件和 TestMain 驱动；生成并运行仿真时保留非 release 模式 |
| `-o <目录>` | 输出目录；使用新的目录可保留之前的 RTL 和报告 |

超时或生成失败时可查看对应块的 `search.log`；搜索已经启动的情况下，还可查看 `search/failure.json` 和保留的候选文件。提高时限或调整粒度后，使用新的输出目录重新生成。自动模式通过原生 RTLzz 生成候选，不能与 `--circt` 或 `--arithmetic-request` 同时使用。

Python 独立入口 `python3 -m tools.autopipe generate` 使用相同的候选配置和模型选择实现；相同计算源、L、请求周期、目标工艺及粒度配置下，两入口的候选选择一致。对照时应使用 VUL 提取的同一份计算源请求，因为独立示例的封装、复位或接口差异也会影响结果。


## 开发文档：

[vullib模块文档](./doc/vullib) 

前期工作链接：
1. [nullrvsim](https://github.com/meng-cz/nullrvsim): 验证VUL模型生成的模拟器框架的正确性和并行效率
2. [FASE](https://github.com/meng-cz/fase-rv64)：对RTL实现的处理器实现系统调用模拟（SE模式），为VUL模型上的SE模式做准备

## “泺源”简介

“泺源”之名，取自济南趵突泉——古泺水的发源地，它是泉城的文化根脉，承载着“源头活水”的含义。

“泺”作为自然源头，代表着创新的起点，就像趵突泉为古泺水注入不竭动能，平台也为处理器研发提供源头性的性能模拟支撑；“源”也代表着处理器设计的源头，强调技术的源头开放、共享协作。“泺源”二字彰显了平台以源头创新驱动芯片技术突破的愿景，成为处理器研发领域的核心引擎。

