# v10 接入 W6／W7／W8 的九案例诊断试跑

按用户 2026-11-15“用 v10 来接入 W6/W7/W8 试试”的要求，本包将冻结的 v10 接入真实工作负载所有者／状态／RTL入口，完成九例全部 **19 组 T/L、132 个结构请求、1034 个候选视图**的导出、数值对照和功能核验。候选视图按目标计数，同一 RTL 在不同 T 下可以重复出现。**完整阶段仍全部缺价，本轮没有选出新的 D，也没有生成新 ABCD 物理成绩。** 本包把阻塞落到实际请求和候选，不能据此关闭 W6—W8 的正式验收。

外部原始产物为 `/home/zyrv/vulsim-artifacts/W678-v10-integration-20261115-v1`。模型使用 [v10 runtime](../common_transition_incidence_v10/README.md)，SHA256 固定为 `a1466f0272b55bd20358ea9e3beb84844db8fe8fefe4152e0478224d8f13243d`；参数、支持、reserve 及旧失败均未修改。源语义、II=1、L 含输出 capture、额外输入服务偏移及有限矩阵全部继承 [W1 合同](../../../arithmetic_dse/configs/general_workloads_v1.json)。应用图没有转作训练或独立测试。

## 接入内容

[C++ WorkloadCostProvider](../../../../rtlzz/src/backend/arithmetic_workload_provider.cpp)新增 `workload-transition-v10-bindings-v1`，严格校验嵌入 runtime 的原始字节 SHA 和工艺 profile。Add／ADC 使用 v10；Mux 时延使用 v10、面积使用该包冻结依赖中的 semantic operator；Mul／Sub／比较等仍由同一包的冻结 semantic operator 提供。G 接入 v10 的 G 函数。这个分工预先写入 [contract.json](contract.json)，拒绝后不尝试旧价格、不混入静态权重。

实际图、placement、所有者、G terms、消费者、capture、state/reset/enable、模型绑定及发射器逐项核验。公共模式拒绝所有诊断价。v10 S 的 `retained-affine-state-semantics-v1` 没有真实算术银行适配，本轮保留实际 `native-state-query-v1`，逐级列出数据字／变量位和明确缺价，不伪造仿射 birth、invert 或 sink incidence。状态计数含 core 和显式输出 capture；输入服务状态另有责任，不能把该计数当所有 S/shared 已计价。

[试跑入口](../../../arithmetic_dse/workload_v10.py)对每个目标重新经过公共编译／拆分／有预算调度／状态物化／RTL生成。搜索配置、返回 placement 和发射 RTL 与 W2 一致，T 只作为新的数值成本／SDC请求；这还是有界提案集，尚无完整模型排序。没有把启发式候选生成改称 D 选择，也没有全局最优声明。[选择收据](summary.json)在全部完整阶段缺价时返回 `cost_uncovered`、`selected=null`、`target_met=null`，不冒充 `target_unmet`。

## 全部目标结果

下表均为该例所有正式目标的合计。组件分母只含唯一算子、G 区域和功能逻辑所有者；常量／wire不另收费，G 内部 Add 不重复收费。“组件齐价”仍缺 S/shared 和完整数据／控制路径。

| 案例 | T（ps）／L | 视图 | 组件诊断有价／全部 | 组件齐价视图 |
| --- | --- | ---: | ---: | ---: |
| MAC32 | 500、750、1000／3 | 90 | 60／2985 | 9 |
| Add512→513 | 750、1250／4 | 56 | 8／504 | 8 |
| Mul128→256 | 1000、2000／4 | 72 | 42／9092 | 8 |
| Dot16→132 | 1000、2000／8 | 144 | 1754／32592 | 0 |
| 四次 Horner64 | 750、1500／8 | 144 | 194／5308 | 0 |
| Barrett64 | 1000、2000／8 | 144 | 234／7456 | 0 |
| Karatsuba256 乘加 | 1000、2000／8 | 144 | 236／42994 | 0 |
| Montgomery256 | 1500、3000／32 | 96 | 2544／120556 | 0 |
| NTT8×64 | 1000、2000／16 | 144 | 336／58752 | 0 |
| 合计 | 19 组目标 | 1034 | 5408／280239 | 25 |

完整阶段 **0／10766** 有价；每个视图的 L 级均保留输出 capture。25 个算术组件齐价视图来自每档 MAC32 的 3 个原始结构放置，以及每档 Add512、Mul128 的 4 个原始结构放置，具体身份见[gaps.json](gaps.json)。它们可先用来隔离实际算术 S/shared；不能删除其他 1009 个候选后宣称完成 D。

MAC32 的 4 位块结构确实进入搜索。[三档结构见证](w7-four-bit-witness.json)中的`structure-1/view-7`，逻辑 stage0 有 64 个 4×4 Mul，stage1 有 16 个 G，stage2 有 1 个 G，保留“部分积→部分归约→最终归约”；它的算子／G 消费边界仍缺价，未强制选中。粗结构和转发竞争方案同样保留。

作为数值消费的例子，Add512 原始结构在 T750 时的 **Add 本体**预测为 724.7160 ps、711.2919 µm²，T1250 时为 735.2241 ps、642.6125 µm²。它说明真实数值 T 已进入函数；这些数值不含完整 S/shared，不能据此判定 750 ps 可行或当作整机面积。没有读取这批应用的新后端标签。

## 缺价归因和后继顺序

274831 个缺价所有者分为四组，原始逐原因分母保存在 summary 和各例压缩收据中：

| 缺口 | 次数 | 责任 |
| --- | ---: | --- |
| v2 实际观察不能无损投影到 v1 | 138740 | carry/selector 79506、G 消费者空 spec 51688、消费者数量上限 7546；不能删观察或改连线来套模型 |
| 已可投影，但既有语义／支持门禁拒绝 | 100170 | capture 位需求 35744、相关算子根 40393、剩余级上下文 17039、known-one 4934、alias／常量消简 1944、数值结构范围 116 |
| G 边界未覆盖 | 11393 | 相关根 11329、其余 launch／capture／消费者边界 64；实际 G 正价格为 0，接通函数不等于 G 已覆盖 |
| 独立功能逻辑没有提供者 | 24528 | 保留实际非 wire 逻辑，不以零成本代替 |

下一项集成工作应先冻结真实算术 S/shared／完整数据和控制路径适配，用上述组件齐价的小集合区分状态误差与算术误差；再将 v2 的 carry/selector、G 消费者、capture 和功能逻辑需求接到相容模型。相关根要区分真实位依赖与过度保守的根集合，并用相容测量验证，不在本轮静默放行。W3—W5 的既有精度失败继续保留；这轮没有通过调参数、扩大支持、加 reserve 或引入实测整图价格来掩盖接口问题。

## 软件核验、回放与费用

新执行 **22 组、2112 周期**事务仿真通过：每例每个目标的首个结构／视图，另含每档 MAC32 的 4 位首视图。其余 **1012 组、97152 周期**在 RTL、bench、图、placement、reset、enable 和 capture 全部一致后继承 W2 记录；state 只允许 `sdc_period_ps` 改变。合计 99264 周期、105620 个结果检查，其中继承部分没有冒充本轮新执行。另在本轮运行 977272 个独立标量整数检查、45572 个 G 替换整数检查，并检查多消费者、carry/selector、唯一归属和真实发射相容性。

22 项测试通过，含 8 项原 v10 特征回归、14 项集成／数值指纹／原生绑定保护；模型包字节、profile 或版本被改动时，真实 C++入口拒绝。原有 workload owner 合同检查通过。第一次尝试从子项目构建目录调用工作负载 target 时 target 不存在，改用独立 RTLzz CMake 工程完成；一次无参数调用 wide-query 辅助工具正常报 usage，这次不计入通过的测试。

首次便携回放发现 LLVM 的整数值 double 序列化为 `3`，Python 为 `3.0`，数值相同却有不同 JSON 字节指纹。原失败包和日志保存在外部 `portable-v1-json-representation-failed*`。修复只将整数值浮点数规范化为整数，新增 `3.0000000000000004` 必须保持不同的负例；原模型字节 SHA、参数、候选、价格和 RTL 均不变，未重跑19组候选导出、事务仿真或EDA。

[便携回放器](../../../arithmetic_dse/workload_v10_replay.py)从 W2 已归档源图／所有者／状态重建 19 组查询，核对本轮实际导出指纹、全部所有者和 C++数值收据；模型计算区禁止文件读取和子进程。每个压缩收据、W2 archive manifest 和模型都有 SHA 绑定，无需外部原始产物树或新的独立标签。`manifest.json` 绑定数据收据，`source.json.gz`保留通用实现，`checks.json`及`replay.json`记录最终核验。

最终回放通过，重算2795个不同诊断查询并核对全部280239条所有者收据。另一次在全程屏蔽外部产物目录、禁止子进程的环境中通过，外部访问尝试为0；记录见[replay.json](replay.json)及[checks.json](checks.json)。模型计算区的全部文件读取也被独立禁止。新增文档／检查／历史日志另由`delivery.json`绑定，首轮失败不抹除。

```bash
cmake -S rtlzz -B build/workload-v10 -G Ninja -DCMAKE_BUILD_TYPE=Release \
  -DLLVM_DIR=/usr/lib/llvm-18/lib/cmake/llvm -DClang_DIR=/usr/lib/llvm-18/lib/cmake/clang
cmake --build build/workload-v10 \
  --target rtlzz-workload arithmetic-workload-owner-test arithmetic-wide-query-test -j 2

# 便携价格／覆盖回放，不运行 EDA 或仿真。
python3 -B -m experiments.arithmetic_dse.workload_v10_replay

# 若要重新执行完整软件试跑，先从仓库压缩证据恢复 W2 功能父目录。
python3 -B -m experiments.arithmetic_dse.workload_v10_replay \
  --restore-parent build/w2-functional-parent
python3 -B -m experiments.arithmetic_dse.workload_v10 \
  --binary build/workload-v10/rtlzz-workload --parent build/w2-functional-parent \
  --out build/nine-workloads-v10

VULSIM_WORKLOAD_V10_BINARY="$PWD/build/workload-v10/rtlzz-workload" \
  python3 -B -m unittest regression.test_workload_v10 regression.test_transition_incidence_v10
```

本轮新 synth／grt／final／physical support 均为 0，候选 PPA 调用 0；没有新拟合、独立源解锁或付费物理重跑。累计 Ledger 继续为 synth3546／grt3515／final16／support22558、wall364977.087278s／CPU744690.68s、pending=0。主仓库与 RTLzz 改动保留待审查，未提交／推送；本诊断包不发布为公共 D。
