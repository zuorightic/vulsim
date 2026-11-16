# 当前两档流水级数：全部ABCD比较

快照：2026-11-16 18:07:23 +08:00。

主方法实测55/148，独立实测物理目录46个；setup通过9条，对应6个独立物理任务。状态：`{'not_started': 45, 'measured_grt': 55, 'failed': 17, 'running': 7, 'awaiting_A_reference': 16, 'not_registered': 8}`。

收尾2026-11-16 18:18:39新增Horner L4/T1900的A，完整Tmin=5140.954834ps、面积4409.823060µm²，当前实测56/148。详见[增量读数](final-readout-update.md)；下表保持18:07快照，不将后来的读数冒充当时状态。
单元格为“完整setup Tmin ps / 总面积µm²”；✓只表示setup通过，hold另看逐行表。A实际L=1，其他方法的L为比较L；II=1，额外输入服务偏移1周期。
所有读数为grt阶段固定实现的RR/IR/RO完整setup最小周期，经±0.1ps阈值复核。未测与失败不填写预测值。相同RTL/T/流程可能共享一次物理测量；4线程继承结果与2线程新结果在CSV分别标识。

| 案例 | 比较L | 目标T ps | A | B | C | D |
| --- | ---: | ---: | --- | --- | --- | --- |
| mac32 | 2 | 950 | 排队 | 排队 | 排队 | 排队 |
| mac32 | 2 | 1100 | 排队 | 排队 | 排队 | 排队 |
| mac32 | 3 | 500 | 1440.4 / 764.6 | 1167.8 / 868.9 | 1143.6 / 2619.0 | 680.0 / 1556.4 |
| mac32 | 3 | 750 | 1425.9 / 756.0 | 1176.0 / 858.1 | 1127.9 / 2453.2 | 752.7 / 1394.6 |
| mac32 | 3 | 1000 | 1444.7 / 758.7 | 1175.4 / 850.6 | 1147.8 / 2384.7 | 1000.6 / 1002.6 |
| add512 | 2 | 700 | 839.3 / 2360.8 | 876.2 / 2707.4 | 876.2 / 2707.4 | 876.2 / 2707.4 |
| add512 | 2 | 800 | 849.0 / 2221.5 | 887.2 / 2602.1 | 887.2 / 2602.1 | 887.2 / 2602.1 |
| add512 | 4 | 350 | 841.8 / 2481.6 | 893.1 / 3440.6 | 893.1 / 3440.6 | 660.7 / 3703.2 |
| add512 | 4 | 400 | 841.4 / 2467.7 | 907.5 / 3425.4 | 907.5 / 3425.4 | 658.9 / 3667.2 |
| mul128 | 2 | 1200 | 排队 | 排队 | 排队 | 排队 |
| mul128 | 2 | 1450 | 排队 | 排队 | 排队 | 排队 |
| mul128 | 4 | 600 | 1662.9 / 7702.8 | 1772.4 / 8157.9 | 排队 | 排队 |
| mul128 | 4 | 750 | 1699.6 / 7666.7 | 1798.6 / 8162.0 | 排队 | 排队 |
| dot16 | 4 | 850 | 失败 | 失败 | 失败 | 失败 |
| dot16 | 4 | 1050 | 失败 | 失败 | 失败 | 失败 |
| dot16 | 5 | 700 | 失败 | 失败 | 失败 | 失败 |
| dot16 | 5 | 850 | 失败 | 失败 | 运行中 | 运行中 |
| horner64 | 4 | 1900 | 运行中 | 1890.0 / 4643.9 ✓ | 1754.6 / 5696.2 ✓ | 1897.9 / 4941.0 ✓ |
| horner64 | 4 | 2250 | 运行中 | 1910.7 / 4631.0 ✓ | 运行中 | 1910.7 / 4631.0 ✓ |
| horner64 | 8 | 950 | 5118.3 / 4419.6 | 1319.6 / 5733.7 | 1228.7 / 8963.2 | 993.3 / 6670.2 |
| horner64 | 8 | 1150 | 5137.5 / 4442.2 | 1318.7 / 5745.8 | 1219.6 / 8681.6 | 排队 |
| barrett64 | 4 | 1800 | 失败 | 1719.7 / 8055.2 ✓ | 2476.0 / 15646.7 | 1719.7 / 8055.2 ✓ |
| barrett64 | 4 | 2150 | 运行中 | 1795.3 / 8039.6 ✓ | 运行中 | 1795.3 / 8039.6 ✓ |
| barrett64 | 8 | 900 | 失败 | 1566.6 / 8719.9 | 1748.4 / 26877.9 | 1487.0 / 10915.8 |
| barrett64 | 8 | 1100 | 失败 | 1543.0 / 8696.7 | 1740.6 / 26019.1 | 1488.7 / 10779.5 |
| karatsuba256 | 4 | 2300 | 排队 | 排队 | 排队 | 排队 |
| karatsuba256 | 4 | 2750 | 排队 | 排队 | 排队 | 排队 |
| karatsuba256 | 8 | 1150 | 排队 | 排队 | 排队 | 排队 |
| karatsuba256 | 8 | 1400 | 排队 | 排队 | 排队 | 排队 |
| montgomery256 | 16 | 待A参考/档1 | 待A参考 | 待A参考 | 待A参考 | 待A参考 |
| montgomery256 | 16 | 待A参考/档2 | 待A参考 | 待A参考 | 待A参考 | 待A参考 |
| montgomery256 | 32 | 待A参考/档1 | 待A参考 | 待A参考 | 待A参考 | 待A参考 |
| montgomery256 | 32 | 待A参考/档2 | 待A参考 | 待A参考 | 待A参考 | 待A参考 |
| ntt8x64 | 8 | 1550 | 软件待就绪 | 软件待就绪 | 软件待就绪 | 软件待就绪 |
| ntt8x64 | 8 | 1850 | 软件待就绪 | 软件待就绪 | 软件待就绪 | 软件待就绪 |
| ntt8x64 | 16 | 800 | 排队 | 排队 | 排队 | 排队 |
| ntt8x64 | 16 | 950 | 排队 | 排队 | 排队 | 排队 |

## 已测逐项：完整数值、hold及来源

| 案例 | 比较L/T | 方法 | 实际L | 块/limb | Tmin ps | MHz | 面积µm² | setup | hold WNS ps | 线程 | 原始测量 |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| mac32 | 3/500 | A | 1 | 0/0 | 1440.360901 | 694.270 | 764.560620 | False | -4.178602 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-073243214bc6/clock-readout/result.json) |
| mac32 | 3/500 | B | 3 | 0/0 | 1167.750366 | 856.347 | 868.851360 | False | 0.111591 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-63bbc97d17bb/clock-readout/result.json) |
| mac32 | 3/500 | C | 3 | 4/0 | 1143.552002 | 874.468 | 2619.034560 | False | -0.158318 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-b469e122a49c/clock-readout/result.json) |
| mac32 | 3/500 | D | 3 | 4/0 | 679.986298 | 1470.618 | 1556.444160 | False | 0.430267 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-a603cc65f248/clock-readout/result.json) |
| mac32 | 3/750 | A | 1 | 0/0 | 1425.865906 | 701.328 | 755.958420 | False | 0.112611 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-073243214bc6/clock-readout/result.json) |
| mac32 | 3/750 | B | 3 | 0/0 | 1175.982422 | 850.353 | 858.076740 | False | 0.071457 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-63bbc97d17bb/clock-readout/result.json) |
| mac32 | 3/750 | C | 3 | 4/0 | 1127.928070 | 886.581 | 2453.187060 | False | 0.261596 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-b469e122a49c/clock-readout/result.json) |
| mac32 | 3/750 | D | 3 | 4/0 | 752.738254 | 1328.483 | 1394.606160 | False | 0.525649 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-a603cc65f248/clock-readout/result.json) |
| mac32 | 3/1000 | A | 1 | 0/0 | 1444.706055 | 692.182 | 758.743200 | False | 0.195746 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-073243214bc6/clock-readout/result.json) |
| mac32 | 3/1000 | B | 3 | 0/0 | 1175.411911 | 850.766 | 850.568040 | False | 0.007785 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-63bbc97d17bb/clock-readout/result.json) |
| mac32 | 3/1000 | C | 3 | 4/0 | 1147.770569 | 871.254 | 2384.690220 | False | 0.476091 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-b469e122a49c/clock-readout/result.json) |
| mac32 | 3/1000 | D | 3 | 12/0 | 1000.593858 | 999.406 | 1002.608280 | False | -0.254512 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-9b41cfd87866/clock-readout/result.json) |
| add512 | 2/700 | A | 1 | 0/0 | 839.263275 | 1191.521 | 2360.779020 | False | -3.619882 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-41f1f36cf2c3/clock-readout/result.json) |
| add512 | 2/700 | B | 2 | 0/0 | 876.179123 | 1141.319 | 2707.389360 | False | 0.002096 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5/clock-readout/result.json) |
| add512 | 2/700 | C | 2 | 0/0 | 876.179123 | 1141.319 | 2707.389360 | False | 0.002096 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5/clock-readout/result.json) |
| add512 | 2/700 | D | 2 | 0/0 | 876.179123 | 1141.319 | 2707.389360 | False | 0.002096 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5/clock-readout/result.json) |
| add512 | 2/800 | A | 1 | 0/0 | 848.971714 | 1177.896 | 2221.496280 | False | -0.558012 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-41f1f36cf2c3/clock-readout/result.json) |
| add512 | 2/800 | B | 2 | 0/0 | 887.152786 | 1127.202 | 2602.121760 | False | 0.198758 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5/clock-readout/result.json) |
| add512 | 2/800 | C | 2 | 0/0 | 887.152786 | 1127.202 | 2602.121760 | False | 0.198758 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5/clock-readout/result.json) |
| add512 | 2/800 | D | 2 | 0/0 | 887.152786 | 1127.202 | 2602.121760 | False | 0.198758 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5/clock-readout/result.json) |
| add512 | 4/350 | A | 1 | 0/0 | 841.821472 | 1187.900 | 2481.559740 | False | 0.086001 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-41f1f36cf2c3/clock-readout/result.json) |
| add512 | 4/350 | B | 4 | 0/0 | 893.141663 | 1119.643 | 3440.573820 | False | 0.200867 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-27125920dc8d/clock-readout/result.json) |
| add512 | 4/350 | C | 4 | 0/0 | 893.141663 | 1119.643 | 3440.573820 | False | 0.200867 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-27125920dc8d/clock-readout/result.json) |
| add512 | 4/350 | D | 4 | 0/128 | 660.684143 | 1513.583 | 3703.232520 | False | 0.631495 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-7c2184192453/clock-readout/result.json) |
| add512 | 4/400 | A | 1 | 0/0 | 841.418732 | 1188.469 | 2467.708740 | False | -0.049821 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-41f1f36cf2c3/clock-readout/result.json) |
| add512 | 4/400 | B | 4 | 0/0 | 907.544464 | 1101.874 | 3425.410620 | False | 0.336134 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-27125920dc8d/clock-readout/result.json) |
| add512 | 4/400 | C | 4 | 0/0 | 907.544464 | 1101.874 | 3425.410620 | False | 0.336134 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-27125920dc8d/clock-readout/result.json) |
| add512 | 4/400 | D | 4 | 0/128 | 658.909332 | 1517.659 | 3667.190760 | False | -0.140096 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-7c2184192453/clock-readout/result.json) |
| mul128 | 4/600 | A | 1 | 0/0 | 1662.859985 | 601.374 | 7702.803540 | False | 0.890676 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T600-6d72e638cd85/clock-readout/result.json) |
| mul128 | 4/600 | B | 4 | 0/0 | 1772.376343 | 564.214 | 8157.874500 | False | 13.125223 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T600-e18af3cbdef4/clock-readout/result.json) |
| mul128 | 4/750 | A | 1 | 0/0 | 1699.602966 | 588.373 | 7666.732620 | False | 0.886485 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T750-6d72e638cd85/clock-readout/result.json) |
| mul128 | 4/750 | B | 4 | 0/0 | 1798.567383 | 555.998 | 8162.000640 | False | 9.701101 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T750-e18af3cbdef4/clock-readout/result.json) |
| horner64 | 4/1900 | B | 4 | 0/0 | 1889.953814 | 529.113 | 4643.861220 | True | 4.826098 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-7dfa023a85cd/clock-readout/result.json) |
| horner64 | 4/1900 | C | 4 | 8/0 | 1754.576996 | 569.938 | 5696.187300 | True | 1.592129 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-c4d9a155e3c4/clock-readout/result.json) |
| horner64 | 4/1900 | D | 4 | 32/0 | 1897.885025 | 526.902 | 4941.030780 | True | 5.314041 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-6ed012ed51db/clock-readout/result.json) |
| horner64 | 4/2250 | B | 4 | 0/0 | 1910.727844 | 523.361 | 4631.001660 | True | 4.615502 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-7dfa023a85cd/clock-readout/result.json) |
| horner64 | 4/2250 | D | 4 | 0/0 | 1910.727844 | 523.361 | 4631.001660 | True | 4.615502 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-7dfa023a85cd/clock-readout/result.json) |
| horner64 | 8/950 | A | 1 | 0/0 | 5118.309570 | 195.377 | 4419.606240 | False | 3.032768 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-6c415b9cf3b2/clock-readout/result.json) |
| horner64 | 8/950 | B | 8 | 0/0 | 1319.628540 | 757.789 | 5733.672480 | False | 9.863305 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-428e4557d83e/clock-readout/result.json) |
| horner64 | 8/950 | C | 8 | 8/0 | 1228.654755 | 813.898 | 8963.244540 | False | 6.086923 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-cd5be660311a/clock-readout/result.json) |
| horner64 | 8/950 | D | 8 | 16/0 | 993.286819 | 1006.759 | 6670.160460 | False | 9.078571 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T950-4f83e78449a4/clock-readout/result.json) |
| horner64 | 8/1150 | A | 1 | 0/0 | 5137.531250 | 194.646 | 4442.234400 | False | 2.397235 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-6c415b9cf3b2/clock-readout/result.json) |
| horner64 | 8/1150 | B | 8 | 0/0 | 1318.734360 | 758.303 | 5745.788460 | False | 2.804895 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-428e4557d83e/clock-readout/result.json) |
| horner64 | 8/1150 | C | 8 | 8/0 | 1219.562248 | 819.966 | 8681.631840 | False | 2.150960 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-cd5be660311a/clock-readout/result.json) |
| barrett64 | 4/1800 | B | 4 | 0/0 | 1719.659157 | 581.511 | 8055.202140 | True | 7.352091 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-876198aa88c9/clock-readout/result.json) |
| barrett64 | 4/1800 | C | 4 | 8/0 | 2475.951538 | 403.885 | 15646.716540 | False | 13.210655 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-83a434da7745/clock-readout/result.json) |
| barrett64 | 4/1800 | D | 4 | 0/0 | 1719.659157 | 581.511 | 8055.202140 | True | 7.352091 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-876198aa88c9/clock-readout/result.json) |
| barrett64 | 4/2150 | B | 4 | 0/0 | 1795.253326 | 557.024 | 8039.616120 | True | 10.181106 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-876198aa88c9/clock-readout/result.json) |
| barrett64 | 4/2150 | D | 4 | 0/0 | 1795.253326 | 557.024 | 8039.616120 | True | 10.181106 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-876198aa88c9/clock-readout/result.json) |
| barrett64 | 8/900 | B | 8 | 0/0 | 1566.563232 | 638.340 | 8719.860600 | False | 5.451792 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-1c5b5d444d6f/clock-readout/result.json) |
| barrett64 | 8/900 | C | 8 | 8/0 | 1748.351501 | 571.967 | 26877.880080 | False | -0.715650 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-4f5c9617af40/clock-readout/result.json) |
| barrett64 | 8/900 | D | 8 | 32/0 | 1487.043335 | 672.475 | 10915.827300 | False | 9.772696 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-18a834929666/clock-readout/result.json) |
| barrett64 | 8/1100 | B | 8 | 0/0 | 1543.046478 | 648.069 | 8696.678400 | False | 10.007356 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-1c5b5d444d6f/clock-readout/result.json) |
| barrett64 | 8/1100 | C | 8 | 8/0 | 1740.600220 | 574.514 | 26019.118080 | False | 8.648915 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-4f5c9617af40/clock-readout/result.json) |
| barrett64 | 8/1100 | D | 8 | 32/0 | 1488.660980 | 671.745 | 10779.548040 | False | 14.151013 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-18a834929666/clock-readout/result.json) |

[全部148条CSV](all-main-records.csv)；[全部已测CSV](measured-main-records.csv)；[带来源的快照JSON](snapshot.json)。
同池静态归因是第五种对照，不混入ABCD主表，原始rows保存在快照JSON。

历史版本保持独立：[v10停止队列完整比较](/home/zyrv/vulsim/experiments/arithmetic/evidence/workload_diagnostic_stopped_v1/comparison.md)；[原紧目标矩阵](/home/zyrv/vulsim/experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/README.md)；[Dot16 L4/L5版本](/home/zyrv/vulsim/experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/dot16-L45/README.md)。未混用旧周期、旧模型。
