# 算术实验：现行契约、验证和实施边界

后续实施以 [修订规划第一章](../../mission/lxy-plan-fix.md) 为准，实际验收见该文件第四章。步骤一的五档宽位宽补验已完成；步骤二新增43例参数化定义、独立参考、固定权重和目标/选择协议。步骤二的组合软件验证不代表固定L流水调度、四平台模型或688条物理记录已经完成。

现行入口如下：

| 入口 | 当前作用 |
| --- | --- |
| [cases_v2.json](cases_v2.json) | 32正式＋11保留案例；原始依赖图、端口宽度及训练隔离策略 |
| [contracts.py](../arithmetic_dse/contracts.py) | 核心数值profile、模板参数schema、43例校验、L和目标批次冻结 |
| [reference.py](../arithmetic_dse/reference.py) | 参数化整数及binary32独立参考；原九案例别名不再接受 |
| [case_generator.py](../arithmetic_dse/case_generator.py) | 家族/位宽生成实际VUL组合核和有类型的源码DAG；不是编译器BEIR |
| [fixed_cost.py](../arithmetic_dse/fixed_cost.py) | fixed-op-width-v1的独立d/a、输入位宽取档、最长路径、共享计费和真实Mux网络 |
| [现行配置目录](../arithmetic_dse/configs) | semantics_v2、fixed_op_width_v1、target_rules_v2、arithmetic_interfaces_v1、selection_protocol_v2和cost_sensitivity_v1 |
| [step2_validation.py](../arithmetic_dse/step2_validation.py) | 使用累计账本记录契约、生成、软件和有限原生验证；不启动Yosys/OpenROAD |
| [step2_freeze_v4.json](step2_freeze_v4.json) | 步骤二后继冻结、源码及证据身份、历史依赖与未完成项 |
| [step2_evidence.py](../arithmetic_dse/step2_evidence.py) | 无build、无EDA工具的向量/跟踪/资源核验，显式使用冻结源码 |

从仓库根目录执行参考查询，数值使用按端口位宽检查的无符号整数；binary32以位模式及五位flags表示：

```bash
python3 -m experiments.arithmetic_dse.reference <<'JSON'
{"case":"MAC_32","inputs":{"a":3,"b":7,"c":5}}
{"case":"UDR_16","inputs":{"a":17,"d":0}}
{"case":"F1","inputs":{"a":1065353216,"b":1073741824}}
JSON
```

整数支持8/16/32/64/128位输入，完整乘积和双乘积和分别保留2W及2W+1位；模加减与低位乘积按声明位置截断。商余的独立参考规定d=0时q全1、r=a；源码先令safe_d为1，再选择规定结果。动态移位先把越界移位量替换为0，最终在s≥W时输出0，不能先做宿主越界移位。signed、fixed-point等未登记profile和未知字段明确拒绝。已有binary32 RNE、渐进下溢、tininess-after-rounding、规范NaN及每次独立舍入语义沿用。

完整步骤二验证入口如下，输出目录必须尚不存在：

```bash
python3 -m experiments.arithmetic_dse.step2_validation --output build/step2-recheck
```

该命令验证全部43例的组合软件路径，以及MUL_128、MAC_128、DOT2_128、H_M_128、F2的原生RTL。现有S8仍拒绝动态Div/Mod，相关原生接入及所有案例的固定L/valid/reset验收按步骤六和后续步骤推进；不能把软件通过写成动态商余RTL通过。新增Int无符号`/`、`%`软件求值只支持同宽无符号操作数，原始零除抛出诊断，由共同safe_d包装定义实验结果。它不新增商余内部拆分模板。

独立SoftFloat核对继续使用原环境变量，源目录无效时验证失败，不伪装为跳过：

```bash
ARITHMETIC_SOFTFLOAT_DIR=/path/to/flat/softfloat python3 -m experiments.arithmetic_dse.step2_validation --output build/step2-softfloat-recheck
```

B/C的新表按输入语义位宽向上取档，可靠ZExt来源可剥离；结果256/257位不自动把128位乘数改成表外输入。d/a是独立字段，组合成本按共享节点求和，时延按依赖最长路径计算。Case保留优先级，Lookup按实际可达索引展开成Mux图；未知操作拒绝或先降低。平方Mul组合成本只属于预声明诊断，完整排序诊断在步骤五执行，不能替换主C。Python实现保留为独立可执行契约；步骤四已将同表固定CostProvider和公共请求接入真实核心调度，half/quarter内部拆分、正式C位置选择和D推理仍按步骤五/七落实。

目标规则先冻结共同公式`ceil(H_ref + (3/2)*D_ref/L)`和平台/阶段/参考身份。D_ref使用原始图最长路径，H_ref单独声明并避免重复计入；实际ps值须等各平台参考微基准就绪后逐批冻结。当前回归中的数值均为公式测试的合成输入，没有生成正式目标或训练模型。

小证据核验无需build目录或EDA安装：

```bash
python3 -m experiments.arithmetic_dse.step2_evidence
python3 -m experiments.arithmetic_dse.wide_evidence
```

历史freeze、旧配置和证据只解释原版本。现行契约/参考/回归入口已替换九案例实现；旧simple_cost及依赖旧成本的放置分析仍支撑尚未迁移的步骤五，按[实现迁移清单](../arithmetic_dse/configs/implementation_migration_v1.json)替换。最终交付只保留现行实现和必要基础；被替代的公式、案例入口、命令行开关和脚本须退出活动路径。需要追溯的原字节限定在明确的归档/冻结证据中，不保留永久旧模式或旧案例兼容别名。

[四平台后端](../arithmetic_dse/backend/README.md)及[步骤三物理测量冻结](backend_freeze_v6.json)已按SDC单位修正重验完成32位共同探针接通，包含三个ns平台重跑的小核grt/完整乘法和单独核对后继承的ASAP7。原v5三个ns平台约束错误结果作废，具体更正见规划第四章步骤三§3.9；便携核验为`python3 -m experiments.arithmetic_dse.platform_evidence`。平台进程清理及共享账本沿用必要基础，旧ASAP7专用设置和九案例预算预测函数已退出活动路径；当前v5额度保持不变。预算命令行报告43例/688条新范围及待准入状态，已移除九案例目标列表和一次性旧迁移开关；实际批量清单、平台能力及预算须按规划逐阶段准入。


当前步骤三软件核验冻结已推进到[backend_freeze_v7.json](backend_freeze_v7.json)，收尾记录见[规划第四章§3.10](../../mission/lxy-plan-fix.md#step3-validator-closure)与[step3_platforms_v3说明](evidence/step3_platforms_v3/README.md)。物理结果继承原v6：本次只收紧静态SDC命令边界、补参数来源和交接覆盖，不新增synth/grt/final。v5旧ns结果仍作废；v6原772份证据及全部旧收费保留。GF180 wire RC校准依据尚未闭合，通孔适配验证不扩大成全部wire验证。


[步骤四公共编译接口](../../mission/lxy-plan-fix.md#step4-interface-acceptance)已实际贯通请求、原始Mul/FP原子区域、固定成本及图/物化校验，说明见[RTLzz接口文档](../../rtlzz/src/backend/arithmetic_interfaces.md)。当前后继冻结为[arithmetic_interfaces_freeze_v2.json](arithmetic_interfaces_freeze_v2.json)，[报告类型修订证据](evidence/step4_interfaces_v2/README.md)说明整数计数/历史导航/存储分层；[原v1证据](evidence/step4_interfaces_v1/README.md)保留原字节，便携入口为`python3 -m experiments.arithmetic_dse.interfaces_evidence`。这不是half/quarter内部拆分或D模型完成；旧simple_cost/split16按迁移清单在步骤五退出。步骤三v7物理证据仍按显式旧快照追溯，GF180 wire RC风险未关闭。

证据目录的新旧含义见[总导航](evidence/README.md)。旧`step4/step4_review`已增加历史横幅，原冻结路径不迁移；新包遵循[分层存储规则](../arithmetic_dse/evidence_storage.md)，不重复复制父源码/账本，不仅凭hash宣称完整产物可重算。
