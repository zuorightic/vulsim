# W2 公共宽 Query、所有者、提供者与 RTL 证据

本包对应[现行W2](../../../../mission/lxy-plan-fix.md#general-model-W2)及[实施§7.101](../../../../mission/lxy-plan-fix.md#workload-common-owners-W2)。它继承[前驱W1/W2包](../workloads_software_v1/README.md)的九例数学合同与有限搜索，接通实际图／级放置／状态→Query v2→唯一算子／G所有者→公共provider→对应RTL。**本轮软件链路验收通过，完整阶段仍为 `cost_uncovered`、`full_D_ready=false`。**

## 实际结果与分母

| 案例 | 声明结构 | 放置／仿真 | 周期 |
| --- | ---: | ---: | ---: |
| MAC32 | 4 | 30 | 2880 |
| Add512→513 | 4 | 28 | 2688 |
| Mul128→256 | 5 | 36 | 3456 |
| Dot16→132 | 9 | 72 | 6912 |
| 四次Horner64 | 9 | 72 | 6912 |
| Barrett64 | 9 | 72 | 6912 |
| Karatsuba256乘加→513 | 9 | 72 | 6912 |
| Montgomery256 | 6 | 48 | 4608 |
| NTT8×64 | 9 | 72 | 6912 |
| 合计 | **64** | **502** | **48192** |

每份RTL实际仿真96周期，独立参考及事务协议沿用前驱，覆盖输入独立写使能、held valid、气泡、最大值、进位／借位、在途reset和L对齐。初次完整owned导出all-v1执行全部502次仿真；加固后的all-v3重新生成全部结构，逐项核对graph、placement、RTL、state、bench相同后继承收据，父收据和摘要单独保留。继承不算第二次仿真，也不增加不同候选数。

本轮每例使用首个已登记数值T检查新所有者及真实参数消费，共64结构；不称正式T全矩阵或完整搜索。前驱132份正式T需求、Montgomery两个100000预算失败及200000有限后继继续保留。

| 软件检查 | 本轮实际分母／结果 |
| --- | --- |
| 唯一所有者 | 121733算子＋5625 G＋12264功能非wire＝139622 |
| 完整观察 | 35305个多消费者算子；38297个carry、1456个selector引脚使用 |
| 精确旧ABI投影 | 52527条；其余保留完整观察并拒绝不相容旧价格 |
| 独立整数检查 | 486932次算子、22500次G替换，全部通过 |
| consumer／capture | 从原始图／位映射重新构建全部观察，与已存v2 Query逐项相同 |
| 旧Query回归 | 最终重建C++对19组6144条真实Query复跑，特征及Core RTL与原输出相同 |
| L=1边界RTL | 4096组向量，动态carry、两个selector及真假支路不同常量掩码通过 |
| C++负例 | 陈旧plan／graph／stage／capture、错误profile、selector投影、静态回退均拒绝；515位G、共享内部值及窄回绕后增宽检查通过 |
| 真实参数消费 | 2694组件诊断估计；公共覆盖0；完整阶段全部明确缺覆盖 |

最后一项只是现有冻结参数的实际消费一致性，不是模型精度检验。5593个G因保守共享输入根检查而拒绝价格；不同输入位段也可能同被拒绝。新模型不得将它们删去后宣布整个域覆盖，也不能直接由根计数授予价格资格。

## 实现与模型边界

- `WorkloadPlan`从真实BEIR、placement及已校验物化状态生成。提供者和发射器重建计划，核对graph／layout／profile／数值T身份。
- v2表达所有数据／carry／selector观察与capture。投影到v1必须不丢边；G消费者明确记为reduction，不能伪装成被替换的内部Add。
- 算子发射调用宽采样共用的标量Core函数；Mux连同掩码转换为`cin ? rhs : lhs`。G独占其内部Add，以保留求和模块替换，提供者不重复叠加成员价格。
- G输入按实际保存的slice／concat别名及位号取数；共享内部结果、可能发生的窄回绕、常量1、非零carry和重复原子不被不安全地融合。
- 相同算子全位宽调用同一共享函数，G共用同一函数。缺模型、新消费者、相关根、功能逻辑及S/shared均显式缺价；state／budget／stage接口不继承静态默认值。

服务输入与输出capture保留原协议；新S层次、完整物理边界及完整阶段资格仍待W3—W6。当前beam仍是按结构计数的有限软件搜索，没有用诊断价选择D。本包0新EDA、0拟合、0新模型源准入、独立标签未读，20个其余算子独立源保持锁定，原公共D与模型失败结论保留。

## 保存内容

- `cases/`、`structures/`：九例源／请求、原图、有限搜索轨迹、placement、state、owners、公共／诊断价格、对应RTL、bench和仿真收据；仅排除可重建的sim.out。
- `inventory-parent.json`与`report-parent.json`：初次完整仿真的原收据，保留原二进制身份。逐放置`simulation-inheritance.json`绑定继承的RTL／状态／bench及日志摘要。
- [models.json](models.json)：仅复制已有冻结参数对象；与前驱模型包逐项核对，没有读取新标签或拟合。
- `v1-regression/`及[v1-regression.json](v1-regression.json)：最终C++的6144项完整结果，回放与前驱原输出逐项比较。
- `owner-edges/`：C++合同日志、L=1实际RTL、独立bench及4096向量仿真日志。
- [manifest.json](manifest.json)、[archives.json](archives.json)：实现源码、压缩档案和每个成员的字节身份。
- [replay.json](replay.json)：本轮实际便携回放；恢复并检查4819个后继成员、3773个前驱成员，重新核对全部所有者、价格、观察及整数语义，均通过。该次回放没有重新启动仿真器。
- `predecessor-sources.tar.gz`：三份已变更的v1冻结C++源码，按原manifest摘要恢复；旧证据／收据／清单不改写。
- `history/`与[provenance.json](provenance.json)：原始失败日志、初次owned源码差异、有效／父产物根及构建身份。all-v2曾因旧main对象与扩大的provider类ABI不匹配而崩溃；旧目录／日志保留，完整常规重建已修复，最终正常构建与有效导出的二进制摘要相同。

压缩数据约75MiB，74个档案均小于10MiB，不包含后端网表、ODB、独立标签或工具二进制。原始产物根为 `/home/zyrv/vulsim-artifacts/W2-boundaries-20261114-v1`，默认回放不依赖该路径。原W1构建目录的可执行文件已在开发中更新，旧收据保留原身份；不把更新后的二进制当作旧二进制。

## 回放与重做

在主仓库根目录执行。默认只用Python及已有特征／模型函数，校验所有档案和源码，重建全部观察／bench，复算实际参数价格、算子及G整数语义；不运行EDA、编译器或仿真器。`--predecessor`将三份旧源码恢复到隔离目录，验证原manifest后运行前驱回放，不绕过其源码检查。

```bash
python3 -B -m experiments.arithmetic_dse.workload_owned_evidence
python3 -B -m experiments.arithmetic_dse.workload_owned_evidence --predecessor
```

安装Icarus后，可从归档重新编译和仿真502份九例RTL及1份边界RTL：

```bash
python3 -B -m experiments.arithmetic_dse.workload_owned_evidence --simulate
```

本轮实际执行的是全部新路径初次仿真、字节相同后继收据继承和无仿真器便携回放；没有把可执行的`--simulate`命令写成又一次已完成的503份复仿真。

重新构建和生成新运行：

```bash
cmake -S rtlzz -B build/workload-owners -DCMAKE_BUILD_TYPE=Release
cmake --build build/workload-owners \
  --target rtlzz-workload arithmetic-workload-owner-test arithmetic-wide-query-test -j2

python3 -B -m experiments.arithmetic_dse.workload_owned \
  --all --binary build/workload-owners/rtlzz-workload \
  --out build/nine-workloads-owned

build/workload-owners/testv2/arithmetic-workload-owner-test build/owner-edges.sv
```

输出目录须不存在，失败保留；生成／验证驱动安装后端PATH哨兵。CLI参数、数学合同及完整软件入口见[WORKLOADS.md](../../WORKLOADS.md)。
