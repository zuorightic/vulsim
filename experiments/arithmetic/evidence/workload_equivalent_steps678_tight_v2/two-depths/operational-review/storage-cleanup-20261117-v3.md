# 旧 ASAP7 中间 ODB 清理：2026-11-17 v3

按用户授权，于 2026-11-17 19:58（Asia/Shanghai）删除 182 个旧 ASAP7 中间 ODB，实际释放 **13.278698 GiB**。随后磁盘可用约 **81 GiB**、使用率 **91%**；后台任务持续写盘，可用量随时间变化。

仅处理仓库外 `workload-equivalent-two-depths-v1` 中 13 个已完整完成的旧任务，删除早期综合、floorplan、布局和 CTS 的 ODB，保留最终 grt/final ODB。涉及 Mul128 L2、NTT L16 和两个旧失败后继批次中已成功完成的任务；未清空 results。

**Nangate45 相关路径完整排除，删除数为 0。** 当前在跑／排队任务、模型、冻结 RTL、网表、日志、报告、最终数据库和账本保留。未改变调度或终止进程。执行前后 2,724 个保留文件元数据一致，最终 ODB SHA256、manifest 和 outcome SHA256 核验通过。

完整范围与核验方式见[清理说明](/home/zyrv/vulsim-artifacts/storage-cleanup-20261117-v3/README.md)，实际数量见[执行收据](/home/zyrv/vulsim-artifacts/storage-cleanup-20261117-v3/receipt.json)，逐文件凭据见[删除清单](/home/zyrv/vulsim-artifacts/storage-cleanup-20261117-v3/deleted.jsonl.gz)。大产物保持仓库外。

已删除的早期阶段 ODB 无副本，若需从这些阶段恢复须重新运行相应阶段。历史 manifest、冻结合同及哈希未改写；旧结果和报告仍可引用。
