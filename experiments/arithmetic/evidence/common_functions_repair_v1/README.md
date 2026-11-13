# 通用函数三线修复后继

**采集和完成审查已结束，发布验收未通过。** 100个有效点、2084项同候选数值核对、6个Add源三区完成；14个独立源保持锁定。最新结果见[completed-review/RESULTS.md](completed-review/RESULTS.md)，其中区分部署T与全部采样T、顺序敏感性及真实结构缺覆盖。下方描述保留启动及恢复阶段的检查点；当前不再有活动采集任务。

本包承接[204点首轮失败审查](../common_functions_v1/completed-review/RESULTS.md)。后继配置见[common_function_repair_v1.json](../../../arithmetic_dse/configs/common_function_repair_v1.json)，现行实施见[规划§7.89](../../../../mission/lxy-plan-fix.md#common-functions-repair-successor)。当前为有限采集和固定后继拟合准备，未发布新参数或D价格。

完整产物根为`/home/zyrv/vulsim-artifacts/common-functions-repair-20261112-v2`。`protocol.json`固定26源／职责、采样与拟合规则，`fitting-rules.json`和`fitting-freeze.json`固定数值特征、共享函数、支持／拒绝算法及实现身份；这些是诊断实现冻结，不能称为已通过独立测试的模型发布冻结。旧8源和新增6源均保持locked_test。

首版`common-functions-repair-20261112-v1`的槽冲突使一个S请求在任何付费叶启动前停止，Ledger该任务记录为0。5个有效点／原标签全部继承，原错误、费用和未启动清单保留。v2只将全任务槽准入改为排队，沿用每批最多12请求、4任务×4线程及0自动物理重试；已完成点不会再次测量。120是train／validation容量，不是一次放行量。

软件准备已完成615项Python／C++特征核对（最大差0）、505个真实placement控制负载投影、连续T的结构支持检查及域外／validation反用负控。三个准备脚本停点（G公共接口要求至少3项、保留旧失败目录及physical-only单元扫描）及调度恢复均保留原日志和费用；软件修复不改物理标签。原始`control_audit_v2`适配未实际应用替换的问题也保留；后继使用显式v3脚本。

实际连通验证复用15个旧train银行物理点，沿真实网络及合法Liberty弧到FF-D，45条valid控制锥的跨级负载与服务自身保持反馈全部匹配，0不匹配，详见`actual-control-connectivity.json`。这证明该银行结构的逻辑计数与实际保留状态相容，尚不等于实际算术S或映射电容模型合格。

`progress.json`、`collection.log`记录当前有限采集；`work-status.json`、`finish-v2.log`记录自动收尾。采完只执行一次固定train拟合、同一候选跨语言核对和诊断报告；出现物理／软件错误停止，不自动重试、解锁test或发布。自动收尾入口的导入错误在`finish.log`保留，后继driver不修改冻结拟合实现。

详细有效位／进位和消费者特征、真实银行扇出、shared独占归属及失败结论见本包紧凑快照。原始ODB／报告在完整根中，尚未清理。
