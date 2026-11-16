# 2026-11-16 旧后端中间文件清理

执行完成：2026-11-16T06:21:27.512806+00:00。删除 18,919 个旧中间文件，释放文件系统块 54.649 GiB；核查时可用空间约 126.67 GiB。

仅处理旧批次 results 中的指定综合／floorplan／place／CTS等中间ODB和 .guide，且同目录必须已有5_1_grt.odb或6_final.odb。保留全部报告、日志、标签、JSON、模型、RTL／Verilog／RTLIL、SDC／SPEF／DEF和最终数据库；缺少最终DB的失败现场及显式冻结文件也保留。当前two-depths、tight-v2、dot16-L45和steps45完整目录排除。

删除前后核对 835,384 个保留文件的路径与元数据，一致；当前 12 份准入清单的源码／输入哈希通过，57 条含归因的已完成读数通过面积、完整setup WNS、hold、覆盖、目标、阈值夹逼和实际线程控制核对。清理未调用EDA、未读独立标签、未改模型或冻结后端源码。

删除的中间文件没有额外归档，无法从本轮清理收据恢复；对应旧阶段的直接回放应标明该文件已按用户授权删除。最终DB、网表、约束和报告仍在，不声称仅凭hash能恢复中间文件。

| 旧批次 | 释放 GiB |
| --- | ---: |
| `/home/zyrv/vulsim-artifacts/common-family-continuation-20261113-v1` | 10.830 |
| `/home/zyrv/vulsim-artifacts/common-functions-20261112-v4` | 5.866 |
| `/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-v1` | 5.740 |
| `/home/zyrv/vulsim-artifacts/common-model-repair-20261113-v1` | 4.323 |
| `/home/zyrv/vulsim/build/step7-target-load-20261103` | 4.066 |
| `/home/zyrv/vulsim-artifacts/common-functions-repair-20261112-v2` | 3.258 |
| `/home/zyrv/vulsim/build/step7-MAC-first-20261107` | 3.125 |
| `/home/zyrv/vulsim-artifacts/common-functions-20261112-v1` | 1.417 |
| `/home/zyrv/vulsim-artifacts/common-family-extension-20261113-v1` | 1.383 |
| `/home/zyrv/vulsim-artifacts/W345-rebuffer-context-20261114-v6` | 1.184 |
| `/home/zyrv/vulsim/build/step7-models-20261102` | 1.163 |
| `/home/zyrv/vulsim-artifacts/common-functions-20261112-v2` | 0.982 |

完整路径清单和删除收据：[清理目录](/home/zyrv/vulsim-artifacts/storage-cleanup-20261116-v1/README.md)；简要机器收据：[storage-cleanup-20261116-v1.json](storage-cleanup-20261116-v1.json)。

同期进度：ABCD实测 45/148、目标登记 27/37、活动后端 9；软件ready 13/18。进度快照：[storage-and-progress-20261116-v1.json](storage-and-progress-20261116-v1.json)，持续更新见[latest.md](latest.md)。

Montgomery256的9×2／16GiB参考A仍以grt 7200秒超时失败，实际保守CTS证明已完成，后续停在引脚访问／全局布线阶段。L16/L32仍等待合法完整参考，不采用综合或未完成路由结果设目标；未自动重试。Barrett64 A的900ps超时和1100ps工具分配器崩溃均保留。九个Dot16物理任务仍在正常计算，当前没有新崩溃事件。
