# 原生OperatorQuery、44视图软件闭环与有限映射边界探针

2026-11-10。当前记录见[修订计划§7.58](../../../../mission/lxy-plan-fix.md#step7-native-operator-query-software)。这是软件与接口线的一次交付，加两项not_training、仅综合阶段的边界诊断；没有正式训练标签、模型拟合或生产D资格。

- 同一公共生成源码重新经PipelineV2及生产候选展开，重验3候选／44结构合法视图，全部使用共享生产物化路径生成寄存器／valid／reset和实际RTL。
- 新OperatorQuery从真实BEIR、当前placement、结果位需求、已知位及精确消费者／capture映射提取76项数值特征；NodeId只在trace内。3个明确的TEST_ONLY目标50／150／1500ps共2064次查询与独立Python重算一致。
- 非恒定测试价格配合DAG零修正、实际S状态投影及显式测试边界／shared价格，实现可行时最小面积和target_unmet后备。仅是软件fixture，不是新拟合模型或已合格完整路径预算；生产模式拒绝该价格。
- 44份物化RTL各160周期，共7040个view-cycle，4136次valid数据比较通过；连续事务、气泡、在途复位、valid推进及流水延迟均受实际自检。4个额外非齐整／低结果／补零／动态carry参数图、名字／NodeId改变不影响数值特征、共享producer双capture和有符号拒绝另通过。
- 原pipeline、valid、reset及参数化Mul回归通过（Mul 24504项）。CIRCT本机缺工具，按现有开关明确SKIP，原生检查继续。
- 用户已确认首版统一保留算子层次。[共同策略](../../../arithmetic_dse/configs/operator_boundary_policy_v1.json)为`unsigned-op-hierarchy-v1`；新增原生发射入口支持组合图与物化流水图，按真实无符号Mul／Add／AddCarry逐节点产生keep_hierarchy子模块。44视图保层次RTL重新完成同样周期检查。公共VUL body／模块定义桥接以及实际mapped／grt资格仍待，不由RTL语法属性直接授予。
- 两项真实ASAP7 synth-only探针使用相同软件已验收的Mul32→Add消费者壳，差异只在module keep_hierarchy属性；相同ABC=SDC=1500ps。保留层次时core／consumer仍可按声明范围识别，自由flatten后这些范围消失。完整单元面积分别630.27882／612.37458µm²，setup分别+131.704422／+73.120285ps，只解释综合STA。
- 保留层次也没有自动取得标签资格：实际launch／capture顺序单元为123／66，与generic预期不一致；银行、常量和位别名需再核对。没有按消失的边界猜节点面积，也没有把这些诊断转为训练标签。

`summary.json`可直接审阅，分块池保存新接口／实现源、原始typed图、查询／分数、实际44份SV、自检向量／testbench／marker、额外参数检查、两项原始映射连接／实例表／综合报告及工具身份。便携回放重算Python特征、DAG／S fixture分项、候选排序、向量参考及边界计数；保留实际原生执行命令和日志绑定，不冒称重新编译C++或重跑RTL工具。

```bash
python3 -B -m experiments.arithmetic_dse.operator_query_evidence verify \
  --folder experiments/arithmetic/evidence/step7_operator_query_v4
```

隔离回放从池恢复源码／输入，以`python -I -S`、空PATH执行，拒绝原home／项目／build读取和回放子进程，池篡改拒绝。实际大ODB／工具完整目录留在ignored build工作缓存，不以hash代替可恢复产物。

早期构建JSON复制／局部变量名错误、首次新增CMake目标未重新配置、两项原回归的运行目录／CIRCT环境错误均保留实际日志与费用。边界探针两次综合均成功；第二份census被历史`probes-v1`名称碰撞的support计数守卫停止，唯一命名的后继只读取原成功检查点，新增综合为0，原manifest和冻结结果保持。上述恢复不消除原费用或扩大任务阶段。

初次隔离在完成数值回放后的临时目录清理中，把dir_fd相对打开误解为原项目路径而停止；后继在安装审计钩子前显式进入恢复源码根，不放宽原home／项目／build禁止。初步v1—v3内容包保持原字节迁入本轮build的provisional-evidence，当前只发布v4，其池还保存实际公共生成源码和执行前源冻结，避免只剩输入文件hash。

`publication-closure.json`记录共享账本结算。`candidate_PPA_calls=0`只针对软件候选选择；本轮另有2次真实诊断synth，grt／final为0。当前`full_D_ready=false`、`production_binding_implemented=false`。下一步先确认共同边界策略、映射银行及独立节点端点，再冻结最小正式源集与后继采集协议；不从这两项诊断启动批量训练。
