# 有界近极限扫描与时延口径前检 v3

2026-11-09。当前计划见[第四章§7.52](../../../../mission/lxy-plan-fix.md#step7-fast-prototype-characterization-protocol)。本包交付有界扫描的软件证明、已有32条物理数据路径的独占分段回放和四项独立节点计时机制探针，不发布新训练模型。

用户确认ABC=SDC、每源最多10点；两个更紧点必须让数据路径受压，时延改善不超过2%才标为有限扫描包络内稳定。软件同时拒绝仅服务壳／边界H违约、内部节点未受压的情况。建库成对取点5%与D等速带5%分别保持。固定策略在源快照`model_fast_scan_v2.json`中；正式源／分组／质量／容量／预算仍待准入。

- 扫描：9项性质，463个状态／232条终止轨迹，最长10点；无重复目标和自动重试。
- 路径：32条已有synth／grt数据路径，节点cell／内部wire、跨所有者wire和边界逻辑逐段计费，全部守恒。含真实pin方向、网连接和原始到达值。
- 负控：18项错误拒绝，涵盖ABC与SDC不一致、跨源／跨角色混用、错误覆盖、非有限数、错误连线和未知pin等。
- 节点机制：四个已付费grt数据库的独立输入→输出最大时延查询；查询前后原Q→D路径表和全部边界slew相同。节点端点／真实多节点消费者的完整资格仍为false。
- 所有物理数字均为原`not_training`诊断；没有拟合、独立模型测试或新增综合／物理优化。

节点独立最大值与Q→D见证中的节点段不同。例如mul32一银行1500ps分别为1131.529175ps和1124.508651ps。不能用整路径上的一个节点段代替节点最大值，也不能把整个外壳延迟按节点重复相加。

`replay.json.gz`包含小型源池、软件结果、原始路径／Liberty pin／连接回放输入和四项节点探针原始表／报告；`manifest.json`绑定内容。便携回放重算扫描和路径守恒，隔离回放禁原home／项目／build／工具／账本、空PATH并禁子进程，另做两项内容篡改拒绝。

```bash
python3 -B regression/arithmetic_fast_characterization_evidence.py portable \
  --evidence experiments/arithmetic/evidence/step7_fast_characterization_v3
python3 -B regression/arithmetic_fast_characterization_evidence.py isolated \
  --evidence experiments/arithmetic/evidence/step7_fast_characterization_v3
```

`publication-closure.json`记录最终封包／便携／隔离三项付费support结算；其他软件／只读探针及失败保留在共享Ledger和`build/step7-fast-characterization-20261109/`。初步包v1／v2按原字节迁至该build下`provisional-evidence/`并登记迁移hash。大型ODB／完整CEC仍依赖原build或将来落实的外部存储，不声称由本包小报告重建。

`physical_admission_allowed=false`，`fitting_allowed=false`，`full_D_ready=false`。
