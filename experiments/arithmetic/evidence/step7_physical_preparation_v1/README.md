# 第7步真实组合物理验证准备 v1

本包完成真实组合源码、公共寄存器物化RTL、逻辑测量端点合同、有限物理矩阵和验收表。当前结论为`passed_real_RTL_preparation_only`；未运行新的synth／grt，不授予S／G联合或正式D资格。

完整产物保留在`/home/zyrv/vulsim-artifacts/stage7-physical-preparation-20261110-v5`，至用户明确清理。它是本机持久目录，不是异机备份。`archive/preparation.tar.gz`已实际恢复，201成员、3,549,150原始字节的大小和SHA256逐项相同，见[恢复收据](restore-proof.json)。v1–v4开发停止目录保留；成功物理阶段没有重跑。

## 已固定的真实结构

每源固定两种合法placement，L=2／II=1，公共输入service另记1周期。选择placement仅看拓扑和合法性，不读取价格或物理结果；它们用于比较同图的寄存器位置。所有算术边界由公共`emitSystemVerilogWithArithmeticBoundaries`发射，内部状态由`materializeSchedule`生成。

| 完整源角色 | 结构 | 实际核对重点 |
| --- | --- | --- |
| combination_validation | serial：Mul8×8→Add32负载→Add64 | 同级串联、两种切分、窄值保存 |
| combination_validation | parallel：Mul8×8与Mul16×16→Add | 并行取最大、共同归约、分支在不同级 |
| combination_validation | shared：p及p+(p映射左移9位) | 一个乘法、多次使用、独立product输出，节点面积只计一次 |
| combination_validation | wide_reduction：p映射左移40位、q映射左移32位→Add64 | 补零、重叠进位、结果截断；避免非重叠Add被优化成拼接 |
| combination_validation | bypass：Mul8×8→Add64，另保留product和29bit旁路 | 算术与非算术捕获、旁路对齐 |
| combination_validation | cross_stage_saved_value：q=p+c；y=q+p | 原p跨级并再次使用、中间结果保存、寄存器阻断前级延迟 |
| locked_joint_test | serial与cross_stage_saved_value的12bit参数版本 | 新参数的独立物理联合评价，标签仍未采集 |

两种固定切分优先分别为“第一算术节点之后”和“最后算术节点之前”；两节点图的第二种放置将两节点都放在前级。BEIR的节点编号不视为拓扑顺序。完整源、图、placement、RTL、状态layout、cut和端点SHA见[结构清单](structures.json)。原六类toy oracle证据保留，此处使用真实编译结果。

测量壳遵循现有S：每个输入端口独立写使能、valid可保持、同步低有效复位、external无条件捕获。所有数据出口均逐字比较，保留各输出的独立可观测性。壳不手工插入native寄存器。

## 验证与当前覆盖

[准备验收收据](proof.json)包含16份RTL×192周期的独立整数参考、连续输入／气泡、独立写使能、途中复位、native数据保持和valid推进检查；51项真实cut捕获路径枚举与DAG核对、39项多路径核对以及96项重复节点／缺节点／缺所有者／伪造cut／缺连线／缺capture负控通过。oracle中的人为费用仅用于软件验证，真实候选价格另见[覆盖诊断](coverage-diagnostic.json)。

候选节点函数SHA为`882d432c1bf1e3c06fcdf677977210b41af46ba171d8dd014c248edb60ab01d2`，冻结但仍等待独立评价；本轮仅以`allow_candidate=True`作诊断。132次真实节点查询中114次接受、18次拒绝：capture数量3次、联合语义／时钟邻域3次、lhs已知零位数量6次、rhs位宽6次。缺口保留在全部分母中，不以新例调参、不改冻结覆盖规则、不将G作为兜底。

serial、parallel、bypass以及两个独立源的两种placement在三档时钟能得到候选完整组合价格。其余18个结构／T请求被拒绝。实际S提供者的拒绝原因是共享物理基线依赖的节点面积超域；这不等于已证明S状态系数错误，也不说明这些结构的实际S边界合格。S参数SHA仍为`1b61a68d80b704532ff38483a034ec2c03de921448095deb6acdcbbb00be383d`。活动测量97文件、节点拟合／推理25文件逐一核对不变，见[依赖核对](unchanged-dependencies.json)。

## 物理测量合同与验收口径

[预登记协议](protocol.json)固定6个validation源和2个locked联合源，每源2种放置×500／1500／3000ps，共48项容量包络；它不是自动执行准入。1000ps继续保留独立精确T职责，本轮未生成或验证该周期的组合价格，三档检查也不授予连续目标域资格。独立源所有目标／放置保持同一角色，必须在完整联合参数、reserve、支持域和选择规则冻结后才能采其标签。

首个pilot包络为serial与cross_stage_saved_value的两个放置、1500ps，最多4 synth／4 grt，无自动重试。当前cross_stage_saved_value有节点覆盖缺口，仍保持阻塞；将来可以先给已覆盖的serial两项生成准确的有限准入。节点函数独立质量通过前，本包不启动组合后端测量。实际执行还需冻结环境、ABC=SDC、SDC／RC／库、布局／时钟策略、准确源／T／端点／资源和保留目录，并重新绑定合格函数文件身份；无需重新生成相同的RTL。

每份`*-endpoints.json`登记真实native寄存器名／origin／stage／enable／reset／变量mask、算子instance scope、输入service和external capture及逐级launch／capture／edge。映射后的Q／D和节点边界引脚必须从实际网表、Liberty和物理连接解析，不能猜名字。综合后先做CEC、变量位／常量／独立FF／状态银行核对和互斥所有权核对，再准入grt。无法归属的多输入root复制单元严格拒绝。

新增`reference_assets/stage7_readout_v1.tcl`是报告适配器：逐动态捕获端点报告完整路径，同时分别读取独立节点最大值，前后比较完整路径和边界slew。它要求实际mapped pin请求，尚未在本批物理快照上执行或取得读取资格。后续须完成mapped请求解析及有限pilot资格；本包不把逻辑端点合同当作物理引脚资格。实际路径每个cell step继续由严格Liberty弧／方向和net连接读取器核对。

[验收表](acceptance-table.json)已逐项建行，全部物理结果为`null/not_measured`。延迟、面积各自按完整源等权报告median／P95，门限分别为15%／35%，每路径类别P95为50%；分母下限10ps／0.01µm²。未覆盖、工具失败及缺端点均报告，不能只对成功子集宣称整包通过。必须同时完成：

- 状态实际保留、端点完整、CEC及所有者互斥／总面积守恒等硬门槛。
- 三状态所有者与clock／physical／root repair各计一次；算子按唯一节点计数，连线按有向edge计数，G初始为零。
- 全壳最坏、算术through最坏和独立节点最大值保留各自见证；实测slack不作为额外延迟。逐级重启到达时间，不跨寄存器累加前级算术延迟。
- 错误可行预测为0；保守拒绝的数量、比例和超预算ps独列。setup以0ps为界，5ps只作复核标记，不豁免负setup；hold另报。
- 同源／同T／同L-II的两种放置按共同选择规则比较。面积5%以内、违约5ps以内列并列区，所有非并列配对排序须一致；缺覆盖的配对单列未验收。

误差按“基础函数与实际节点→独立节点最大值相加的保守性→S／连线／IO／时钟边界→重复或漏计→其余稳定且影响选择的残差”分解。只有前项核对完成后，才决定是否引入G修正；零修正通过即可采用。

## 执行与资源

入口为`python3 -B -m experiments.arithmetic_dse.stage7_physical_prepare {init,export,products}`和`regression/arithmetic_stage7_physical.py`；公共导出工具为`build/step4-rtlzz/testv2/arithmetic-stage7-export`。每次实验叶使用`regression/arithmetic_steps123.py leaf`共享Ledger，外层`export`控制器不重复计费。

[资源结算](resources.json)：本轮0 synth／0 grt／0 detailed，28 support，73.637931秒叶墙钟／221.95秒CPU，本轮pending=0。包含4项开发命令失败及后继修正；预算系统拒绝的同名support任务没有启动叶命令，原目录保留。仍保留后续688 synth／688 grt／86400秒叶墙钟／172800秒CPU／30GiB预算职责。本轮没有提高总额度，也没有读取旧或正在采集的独立物理测试标签。
