# 两档流水矩阵运行审查

2026-11-16T11:49:15.966727+00:00

主方法实测 59/148；已登记 31/37 组；活动后端 9 个。

| 案例 | L | 阶段 | 已实测主方法 |
| --- | ---: | --- | ---: |
| mac32 | 2 | backend_registered | 0 |
| mac32 | 3 | backend_registered | 12 |
| add512 | 2 | backend_registered | 8 |
| add512 | 4 | backend_registered | 8 |
| mul128 | 2 | backend_registered | 0 |
| mul128 | 4 | backend_registered | 4 |
| dot16 | 4 | backend_registered | 0 |
| dot16 | 5 | backend_registered | 0 |
| horner64 | 4 | backend_registered | 8 |
| horner64 | 8 | backend_registered | 8 |
| barrett64 | 4 | backend_registered | 5 |
| barrett64 | 8 | backend_registered | 6 |
| karatsuba256 | 4 | backend_registered | 0 |
| karatsuba256 | 8 | backend_registered | 0 |
| montgomery256 | 16 | awaiting_A_reference | 0 |
| montgomery256 | 32 | awaiting_A_reference | 0 |
| ntt8x64 | 8 | software_waiting | 0 |
| ntt8x64 | 16 | backend_registered | 0 |

当前主方法失败 22 条；历史软件错误已恢复 3/4 条。
可用内存 26298 MiB；磁盘可用 52.6 GiB。
确认工具崩溃且日志停止至少120秒时，仅通知其任务包装器正常清理和结算；不自动重试。
