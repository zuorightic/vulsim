# 第4—5步：物理逻辑归属恢复及后继独立验证准备

用户于2026-11-11授权按“恢复逻辑归属、同步重建端点和路径”处理层次外复制单元，并明确记入第4—5步。当前恢复资格为`passed_saved_snapshot_qualification`；原v2独立测试继续原冻结规则，失败记录未被抹去。修复后全新独立验证另行登记，不能把已查看的旧test复核当成新独立验收。

## 修复规则与实现

`model_logical_ownership_v1.py`先验证单个root组合单元的全部实际驱动和负载都属于唯一算子；三项历史失败可直接恢复。另一个validation快照的root逻辑经过顶层缓冲器，因此v1继续拒绝。显式后继`model_logical_ownership_v2.py`验证完整root组合逻辑／缓冲器连通子图：外部邻居只能属于一个声明算子，各net有唯一驱动及实际负载，不触及顶层BTerm、状态、时钟、未知所有者或未连接net，Liberty功能和完整引脚census必须存在。跨节点／状态／顶层或归属不唯一时继续拒绝。

规则没有clone名称、master型号、源或形状白名单。归属由同一物理阶段的完整OpenDB引脚／连接／BTerm／clock census产生明确`instance→owner`证书；读取时重新计算证书，拒绝调用者伪造归属。证书和实际master／单元清单共同约束新Tcl报告。

`context_readout_logical_v1.tcl`用同一份显式单元归属表重建真实物理端点及独立输出最大路径，并保留探针前后完整功能路径／slew不变检查。Python标签读取、独占面积和Q→D路径分解统一使用证书。内部采用可逆、无碰撞的**证明用名称映射**复用原严格读取器，输出路径还原实际物理引脚；ODB／网表／net名完全不改，不把复制单元塞给S／G或重复计费。

`model_logical_labels_v1.py`提供带强制证书的真实快照读取接口；`model_logical_stage_v1.py`把census／端点／标签接入阶段采集，`model_logical_qualification_v1.py`继续使用原综合、布局布线、FF／端口、SDC／RC、面积及CEC资格链，只替换标签入口。新增报告叶使用同一任务Ledger，不开嵌套任务或重复计费。[实际保存阶段的采集接口检查](collector-interface.json)已通过，全部标量、节点、所有者和路径结果与恢复验证一致。

## 保存快照的真实恢复结果

| 原失败源／T | 恢复的物理单元 | 唯一逻辑所有者 | 重建端点移除的假边界 |
| --- | --- | --- | --- |
| `s68decd5321da7cf0`／463ps，train | `clone454` | producer | 13个输入／4个输出 |
| `s98757fe1b49b8a81`／491ps，train | `clone514` | producer | 13个输入／4个输出 |
| `se5bec7ce105a27d8`／873ps，validation | `clone480`、`rebuffer697` | consumer0 | 11个输入／4个输出 |
| `s32e03528a3472a5c`／500ps，旧locked_test | `clone283` | consumer0 | 9个输入／3个输出 |

四项恢复均重读实际节点最大值和完整路径，不只是改面积归属。每个物理阶段与原整壳面积守恒，FF／银行、端口、存储SDC、线RC和实际CTS CEC均核对通过；所有原源、history、ODB／SDC／网表、旧路径和标签文件逐项SHA不变。旧冻结版本的拒绝和首败停源记录保持原身份，恢复标签保存在新目录且不自动变成原协议的合格训练／独立点。

[资格收据](qualification.json)包含4失败阶段恢复和12个原成功synth／grt对照，后者标量、节点、独占所有者面积及路径分解精确相同。46项负控通过：跨算子／状态负载、顶层暴露、时钟、未连接／缺引脚／缺Liberty、伪造证书，以及16阶段逐一删除实际经过的Liberty时序弧。随机改变root实例名仍能恢复，确认未依赖clone名称。

[完整拟合标签重放](all-fitting-labels.json)进一步核对了全部524点／1048个synth／grt标签：节点、标量、各所有者面积和路径分解全部保持一致；未读取其余独立测试标签。因而本次修复可以继承原冻结参数、支持域和reserve，不必为了修复读取器重跑后端或重新拟合。被恢复的旧失败点不在本版本中悄悄加入训练。模型SHA仍为`882d432c1bf1e3c06fcdf677977210b41af46ba171d8dd014c248edb60ab01d2`。

## 后继的新独立职责

完整源均为原74源以外的新身份，全部保持locked_test，各自四个固定目标500／1000／1500／3000ps，共16请求；不重用旧test作拟合／validation。结构为：

| 源 | 被测算子 | 消费者 |
| --- | --- | --- |
| `s31f15ef3e3ea74bf` | Mul10×14→24 | 结果左移12位／补零接Add64 |
| `sfd070255ebd51076` | Mul14×18→32 | 结果左移8位／补零接Add64 |
| `sa3fb07b49b32ae35` | Add(24,40)→41，rhs低8位为零 | 补零接Add64 |
| `s6792d9de71d0dbde` | Add(40,56)→57 | 补零接Add64 |

这些查询均处于原冻结函数支持域。候选身份只用于数据职责，不进入函数预测特征。四源各128周期独立算术／银行观察通过；源码与admission已实际归档恢复。准确预算上限16 synth／16 grt／384 support，单物理任务、每工具4线程，原300秒综合／1200秒grt，无自动重试；单源失败停止该源并保留费用，其他源可继续。每次运行前核对冻结身份与实时预算，仍保留后续688／688调用、86400秒墙钟／172800秒CPU／30GiB职责，不提高总额度。

后继控制器已经排队，等待原v2完成独立评价，才测量新源。只测量并评价原冻结函数，不拟合、改域、改reserve或擦除旧结论。新源按完整源等权、median≤15%／P95≤35%检查延迟和面积，全部源／T必须覆盖，采集失败门槛为0，精确1000ps单列。小规模新职责本身不授予任意完整域、S／G联合或正式D资格。

新包位于`/home/zyrv/vulsim-artifacts/operator-ownership-fresh-independent-20261111-v1`，控制器日志为`build/step7-ownership-recovery-20261111/fresh-independent-controller.log`。当前状态以该目录`progress.json`、`followthrough.json`和最终`independent-result.json`为准。原v2独立及其证据控制器仍独立运行，不热改旧协议。

## 证据与资源

本包的三个gzpart包含107个冻结源码／模型成员及16份真实packet、证书、端点和标签。经共享Ledger执行`python3 -I -B replay.py --evidence .`，实际恢复后仅从恢复源码导入读取器，重算16阶段通过，不调用EDA或拟合。浮点面积求和因JSON键排序可有约1e-14差异，后继回放明确使用绝对1e-8／相对1e-12比较；结构、集合、证书及角色仍严格核对。首包精确浮点比较失败保留在`step7_operator_ownership_recovery_v1`，没有覆盖。

[完整恢复归档](restore-proof.json)已实际恢复1392成员、约30.6MB原始字节，逐文件大小和SHA核对通过。完整原始产物留在`/home/zyrv/vulsim-artifacts/operator-ownership-recovery-20261111-v1`及`-v2`，保留至用户清理；同盘持久目录不是异机备份。

[本轮资源](resources.json)为0 synth／0 grt／0 detailed、51 support，叶墙钟153.172895秒／CPU170.31秒，pending=0，包含开发验证／封包回放失败；不含后台原独立采集和未来16项新物理请求，所有费用共用原Ledger。模型、S参数和原测量依赖不变，`full_D_ready=false`。

后续执行检查点：原v2已完成692点、独立评价及证据回放，数值误差与1000ps检查通过，但Add原采集失败和Mul3389ps超出339–3362ps支持范围的拒绝仍使整包failed_independent。后继新源首个500ps点已完成synth／grt、新归属读取及CEC并归档，控制器继续其余请求；不把一次链路成功当作新独立整包通过，实时状态见新持久根。
