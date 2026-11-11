# v2独立采集停点审计与冻结续采

2026-11-11检查后端停止：train／validation已完成524个有效点并冻结候选；独立测试新增47个有效点后，batch-017在11成功／1拒绝处结算，累计571有效点。拒绝点为locked_test源`s32e03528a3472a5c`、ABC=SDC=500ps。本包不是独立质量通过报告。

[实际拒绝审计](audit.json)重放了同一保存快照的mapped FF／银行、算子端口证书和整网CEC。物理优化在root产生`clone283`（`AO21x2_ASAP7_75t_R`），与`consumer0/_243_`有相同输入，位于全部声明算子scope之外。原读取器继续拒绝`unowned physical cell`，未生成grt节点标签；没有把该单元分配给某节点、S或G。该源此前1481ps／1000ps两个有效点保留，失败500ps保留且整个源停止，不补跑1500／3000ps或换源。

[续采合同](resumption-contract.json)核对原候选、selection、角色、原20个独立批次的上限及batch-018的准确12源／T请求。已使用4个独立批次，剩余最多16批；每批仍按实际pending请求和实时预算准入，不意味着放行全部18×13网格。97项测量依赖和25项冻结拟合／推理文件保持原SHA。其余17源继续原采样器，旧测试源和本次已采测试源均不改作拟合／validation。

控制器实现为`experiments/arithmetic_dse/operator_condition_v2_continue.py`，故障审计为`regression/arithmetic_operator_test_stop.py`；没有修改冻结的采集、拟合或评价实现。原停止状态、账目及源码复制到持久根`controller-attempts/attempt-002`，实际归档恢复通过，见[收据](checkpoint-restore.json)。本机同盘目录不称异机备份。

[六类控制状态检查](transition-proof.json)在隔离临时目录中通过：正常结束、经审计后继续、未知失败停止、原批次上限耗尽、冻结身份错误、有限批次仍未完成。检查确认没有重走拟合／冻结、没有重置额度、没有把有限进度提升为合格，最终提取／评价只执行一次，失败结论保持；不启动EDA或读取真实独立标签。恢复后的真实batch-018也已有多个有效点完成，实际链路继续推进。

续采控制器只执行独立采集→完整标签重放提取→一次性独立评价→真实恢复回放及费用结算。它不会重走拟合／选模型／改域。若再次遇到相同类型的采集拒绝，必须先核对真实映射、FF／端口、CEC及首败停源规则并保存新的审计／检查点，才继续其余源；其他错误停止。每次继续都递减原总批次数，失败点始终不重试。源码／scope／ownership规则、参数和reserve不为测试结果改变。

既定`operator_condition_fit_v2.test`将`acquisition_failed`计入独立失败门槛。因此已发现的Add源采集失败不能被剩余点成功或数值误差良好抵消；必须保留该版本失败结论。完整采集用于区分其余独立数值质量、覆盖／拒绝和未见1000ps响应，不在本集合内调参挽救。正式发布需最终独立结论；`full_D_ready=false`，S／G联合资格仍待。

最新运行状态位于：

- `/home/zyrv/vulsim-artifacts/operator-conditional-wide-20261110-v1/progress.json`
- 同目录`v2-work-status.json`、`v2-evidence-status.json`
- `/home/zyrv/vulsim/build/step7-operator-v2-20261110/independent-continuation-20261111.log`

OpenROAD空闲也可能处于归档／提取／评价，最终是否结算以状态文件和账目为准。本文571点只解释原停点，不冒充后续实时总数。
