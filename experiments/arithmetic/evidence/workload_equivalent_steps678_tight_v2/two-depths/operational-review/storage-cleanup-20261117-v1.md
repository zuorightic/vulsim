# 2026-11-17 旧CEC展开缓存清理

执行完成：2026-11-17 00:04:12 +08:00。删除9,090个指定旧缓存，释放文件系统块72.925 GiB；当时可用137.42 GiB。

范围限定为5个旧build实验；其中4个目录存在可删缓存。只删除structural_cec目录中的gate/gold-flat、cut、hier六种展开网表JSON；它们由保留的Verilog生成，证明收据和原日志保留。最终ODB、映射Verilog、原RTL、模型、训练／评价标签和时序报告均未删除。当前two-depths及后继、原A参考、Dot16和预算／模型文件均不在删除根目录内。

删除前后逐项核对其余452,806个文件的路径与元数据，全部一致；清理后再次核验14份原后端准入，以及撤回批次、资源后继和Montgomery参考准入，全部冻结输入与源码hash匹配。未调用EDA或改变模型。

| 旧目录 | 释放 GiB |
| --- | ---: |
| `step7-MAC-first-20261107` | 46.021 |
| `step7-I-exact-20261106` | 9.892 |
| `step7-general-state-20261106` | 8.697 |
| `step7-general-control-20261106` | 8.315 |

[机器收据](storage-cleanup-20261117-v1/receipt.json)；[删除清单](storage-cleanup-20261117-v1/deleted-files.jsonl.gz)；[清理代码](storage-cleanup-20261117-v1/prune_cec_scratch.py)。

完整保留元数据索引及原始清理目录：`/home/zyrv/vulsim-artifacts/storage-cleanup-20261117-v1`。本次对这些生成缓存直接删除，没有另存字节归档；不能仅凭清理清单恢复它们。原网表与证明／运行日志仍在，旧CEC原样回放需要重新生成相应展开缓存。

当前有效重测为[原时钟不变的资源后继](../failure-resource-only-v1/README.md)。已撤回的固定RTL改后端T批次不计ABCD主对比。
