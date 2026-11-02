# 步骤六Git交付集合复核

本包补齐技术验收后的Git交付检查。根目录`build`忽略规则曾使17份父冻结链必需manifest不在Git文件集合中；原工作区整目录复制的隔离测试带入了这些文件，未检验忽略规则。修补在`step3_budget/historical_manifests/.gitignore`增加局部白名单，只纳入历史`manifest.json`和`probe-manifest.json`。根.gitignore、whole_graph_freeze_v2及其父链、17份原manifest字节均不改变。

修补前按Git集合复制的副本确因缺失manifest而失败；修补后，按主仓库和子模块的“已跟踪＋未忽略待提交”文件构造副本，根build和大产物均不复制，PATH为空，正式默认入口及完整父链通过。移除这17份文件的负例拒绝；ODB、SPEF、运行日志仍被忽略。17份manifest及局部规则已定向暂存，最终提交还须包含本包和步骤六其他待提交内容，子模块按既有顺序提交。

`before-fix.json`保留实际修补前结果，`verification.json`是暂存后复验。文件数和Git内容清单哈希是各自命令的执行时点，包含当时账本内容；本包后加的报告、索引及规划追加不冒充已被原命令复制。最终本包保护集合以`index.json`为准，它同时绑定原v2冻结、根忽略规则、局部忽略规则和17份历史文件。`resources.json`、`usage_delta.json`及命令回执保留本轮support增量；原v2冻结的856 support统计保持其原时点。

从仓库根目录重新执行交付检查，可使用包内脚本；它会实际调用Git列出工作区文件，故需保留主仓库和子模块的Git元数据：

```bash
python3 experiments/arithmetic/evidence/step6_git_delivery_v1/procedures/support.py git-delivery-check 180 python3 experiments/arithmetic/evidence/step6_git_delivery_v1/procedures/verify_git_delivery.py
```

输出写入ignored的`build/step6-git-delivery-20261102/`，命令名称需未使用。该检查不编译、不执行RTL或EDA，也不取用完整本机大产物；不重新解释UDR/F2指标、85项回归或原生收据。完整产物仍按旧catalog的本机可获得边界处理。
