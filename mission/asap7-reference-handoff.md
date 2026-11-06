# ASAP7九例D：目标参考采集交接

2026-11-06。当前S发布及后续见[§7.48交接](asap7-general-state-handoff.md)：首轮162拟合／54独立全部完成，面积合格、控制边界69／72拒绝发布；原54 test永久封存。用户确认保持面积参数另补控制边界，§7.47完成原／新324测量回放／验证冻结，§7.48完成新54独立并发布有据grt S组件，原面积与六类边界不变；本实验当前无后台EDA，生产绑定和联合G／I资格仍待。本文保留参考／目标的[fix第四章§7.42](lxy-plan-fix.md#step7-m2-numerical-target-freeze)：用户已确认分离口径，九例正式数值目标及其生产公式／external／隔离／篡改核验完成，[目标证据](../experiments/arithmetic/evidence/step7_m2_targets_v1/README.md)约0.35MiB。17项参考原始封存见[§7.41](lxy-plan-fix.md#step7-reference-raw-audit)，准入／恢复见[§7.40](lxy-plan-fix.md#step7-reference-cohort-admission)，承接[§7.39全部候选需求](asap7-d-requirements-handoff.md)。17项独立原子参考及完整回放证据保持，参考队列已结算；下文资源数字为对应参考／目标检查点。原参考服务为`vulsim-reference-r3-20261106.service`，目录为`build/step7-reference-20261106/collection-v3`。这17项不是模型train／validation／test，也不是九例正式A/B/C/D的36条。

## 已完成队列与状态入口

三个容量先导`div_u32`、`f32_mul_rne`、`add_u64`完成完整综合→grt、两阶段原始标签／面积归属／SDC／RC及CTS CEC检查后，自动放行余下14项；现已17／17完成，错误0。先导grt分别约61.58／75.68／39.08秒，进程树采样峰值约506.04／557.52／403.55MiB。准入只覆盖此次明确列出的17个单原子参考外壳，不转授整阶段、状态后继或更宽算术域。

```bash
cd /home/zyrv/vulsim
python3 -B -m experiments.arithmetic_dse.model_reference_collection_v3 status \
  --folder build/step7-reference-20261106/collection-v3
```

最多4任务并行，每任务请求4线程、内存限额8GiB；服务总CPU配额1600%、内存上限36GiB。所有叶命令共用原Ledger；任务间和阶段切换时并发可低于4。综合上限300秒、grt1200秒、每次只读快照120秒，无自动重试。发生错误后停止放入新任务，已运行任务结算后退出；全部采完后也退出，**不自动拟合、放行独立模型测试或冻结数值目标**。

## 参考设置与协议

[参考配置](../experiments/arithmetic_dse/configs/model_asap7_m2_reference_v1.json)的SHA256为`69839acf53024dcbb5cc78389ea761396067a7679c764a2719f58c8f1f393594`。17个源逐一绑定§7.39的17个参考键，固定ABC1500ps、SDC40500ps、I/O=0.2T，采用预先登记的统一宽松参考设置。保留实测违例／失败，不按后验Tmin回调目标；40500ps仅为本批参考采集条件，尚非九例正式目标或其他模型的扩域资格。

真实公共VUL的三类状态协议已分开：输入／service寄存器分别有使能；内核原生数据寄存器由前一级valid使能；**公共外部输出数据捕获无条件更新**。参考源分别实现这三类所有者，valid逐拍推进。旧受限状态查询中的显式外部capture请求是其自身消费条件，不能据此推断真实公共VUL外壳也使用valid使能。完整D原本就未获联合／外围资格，本批没有修改旧发布字节或追改旧结论。

安全Div／Mod的零除数改为1发生在launch Q之前，非零偶数除数原样保留，算术核仍是原子Div／Mod。binary32沿用已核验的完整AtomicFp，逻辑37位结果中的恒零除零flag单独重建，捕获银行为36个变量payload位加valid；Div／FP不进行额外内部拆分。

原始标签保留完整Q→D路径，再拆分launch Q至最后core输出的数据分量、捕获侧布线／hold／reset后缀，以及时钟／setup／skew／uncertainty。八类路径分别覆盖数据、native enable、valid、external data／valid及input data／enable／valid；输入路径仅扣一次0.2T。OpenDB连接和实际Liberty时序／功能pin共同决定归属；input_service、arithmetic、native_state、external_state、observer、shared_clock、shared_physical及root_boundary_repair互斥，未知功能／时序单元拒绝，不默认零价。

## 已完成前检与恢复链

软件前检`build/step7-reference-20261106/preflight-v4/software/proof.json`通过：17源×144周期、19728个完整状态检查，124个保留偶数除数周期、1343个区分控制协议周期；通用未映射Yosys状态几何通过。旧TRAIN数据库只用于只读STA API／归属提取前检，不充当新参考数值。标签读取器九项负控通过，包括clock pin误作D、漏归属／重归属、错误路径差值及负捕获后缀；另已核对I/O仅扣一次。这些fixture明确为合成数据。

首个`collection-v1`的三个综合工具命令均成功，随后读取器因OpenDB／STA方括号转义和FP根层常量驱动归属停止，未执行grt。`model_reference_labels_v2.py`仅对实际转义名称建立无碰撞对应，并从Liberty纯常量函数识别根常量；未知功能逻辑仍拒绝。三个实际综合快照的24条路径、面积归属及FF数量回放通过，名称碰撞负控通过。

`collection-v2`复用同三个综合检查点，三次只读快照后因续作目录缺原ORFS的`1_synth.json`面积交叉核对元数据而停止，亦未重综合或运行grt。后继`model_reference_collection_v3.py`补继承原生综合JSON，先对三个完整暂存目录重新解析、核对面积／八类路径及原始hash，预检通过后才启动当前队列。祖先命令不伪装成新命令；续作清单显式保留checkpoint来源、hash和原付费收据。

| 准入 | admission.json SHA256 | 状态 |
| --- | --- | --- |
| collection-v1 | `393da9721a33b1fde85f3e217432725383879706aa6bf1881b0ebdfadd7f309b` | 三个综合已付费成功；读取失败保留 |
| collection-v2 | `925b15d2bad7d7b4ea55a9acf002920d1fbf86d4637a3263b27b4f59e3c19030` | 三个只读快照；缺续作元数据失败保留 |
| collection-v3 | `0fcbb7a1e7a296d9cf2b781dd106ac93e1a5fc313f66928c94a5f3b36ad9df75` | 当前恢复队列；三个旧综合复用，14个新综合＋17个grt |

已准入生产者及配置不得原位修改；如需修补，另立后继并保留全部失败／费用。本轮唯一源的综合总数仍计划为17，恢复不会要求前三个重综合。

## 已完成原始回放与下一依赖

1. **已完成**17项原始报告、完整付费祖先链、实际FF／单元唯一归属、八类路径与SDC／RC／CTS CEC核验；34阶段／272路径、108实际付费叶命令及4151份原始文件回放通过。六个读取／续作失败保留；证据包便携／完整external／隔离／篡改通过。ite_u16 grt hold为−0.321049ps，setup有效与hold未通过分开保留，不重采或调目标。
2. **已完成**原始DAG最长路径D_ref、用户确认H_ref统一分离汇总及九例目标冻结。原[target-proposal.json](../experiments/arithmetic/evidence/step7_reference_v1/target-proposal.json)保持；后继[正式目标](../experiments/arithmetic_dse/configs/model_asap7_m2_targets_v1.json)SHA256为`6dd49589bae6e6be0be8d35bdd16259064a1f84a2910129249421c4bc458763e`，numeric_targets_frozen=true。没有用803.206085ps旧银行开销、预测价格或整图后验PPA替代；其他控制／input／external完整路径仍是参考上下文诊断。
3. S已按§7.43–§7.44完成源前检、162 train／validation原始回放／验证／冻结及字节复现，首轮54独立已完成并因控制边界失败拒绝发布／永久封存；§7.46保留面积参数，只补控制边界后继，§7.47完成原／新324测量回放及验证冻结，§7.48完成新54独立一次性评价与限定grt S发布；生产状态查询／所有权／价格绑定和联合G／I仍待。G／I仍须按[联合需求v2](../experiments/arithmetic_dse/configs/model_asap7_m2_joint_requirements_v2.json)登记受限合成整阶段／联合边界和真实half／quarter区间源、完整train／validation／锁定test、目标网格与容量／预算；完成前检和具体准入后再采集。共同需求配置physical_admission_allowed=false保持，S只由专门后继准入放行；已消费测试永久隔离，原已合格且域匹配的11类组件保持。
4. 并行完善C++计费所有权、部分阶段安全界和初始／试移／最终统一查询，再验收D选择／RTL与正式36条。选择时PPA0、C/D顺序及K16保持。

§7.42全局结清前缀为1606 synth／1584 grt／16 final／6254 support，9460 entries，叶墙钟199046.901518s／CPU448543.74s，pending／active／unsettled均0；此后新增费用按Ledger累加。§7.41完整原始回放后最初external因冻结源树缺活账本而失败，v2只显式绑定外部Ledger后通过，失败及费用在原verification.json和补充收据中保持；未重采物理数据。

九例数值目标现已冻结；新目标域的模型资格、完整D及正式36条仍待完成，完整步骤七与688条未关闭。Git由用户操作。
