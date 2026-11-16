# ABCD比较：A复用原未拆分参考，BCD按流水目标测试

2026-11-16T13:40:17.911183+00:00

A参考已实测8/9；BCD已实测50/111。37组展示重复引用每案例同一份A，不再产生37次A测量要求。
A_request是当时实际SDC/ABC请求，A_Tmin是该固定实现的完整RR/IR/RO实测最小周期；BCD_T是B/C/D的流水目标。A不按BCD_T判断setup，也不将A_Tmin改写成BCD_T。
面积单位µm²，周期单位ps；✓仅表示BCD setup达标，hold与频率单列。工艺／外壳／I/O规则保持；A与BCD映射请求有意不同，比较为原始基线与目标流水实现。

| 案例 | A实际请求 ps | A实测Tmin ps | A面积µm² | A hold ps | 状态 |
| --- | ---: | ---: | ---: | ---: | --- |
| mac32 | 1000 | 1444.706055 | 758.743200 | 0.195746 | measured_grt |
| add512 | 1100 | 1059.684803 | 2133.389340 | 0.271880 | measured_grt |
| mul128 | 2000 | 1884.844337 | 7225.600140 | 0.192943 | measured_grt |
| dot16 | 2700 | 2705.125456 | 33186.748140 | 1.879941 | measured_grt |
| horner64 | 7600 | 5981.928589 | 4147.266420 | 1.690620 | measured_grt |
| barrett64 | 6000 | 5603.325317 | 7497.327600 | -4.240358 | measured_grt |
| karatsuba256 | 9700 | 7201.306396 | 21206.916180 | 11.165096 | measured_grt |
| montgomery256 | 36000 | — | — | — | failed |
| ntt8x64 | 9700 | 9734.198421 | 11182.524660 | 13.047647 | measured_grt |

| 案例 | 比较L | BCD目标 ps | A请求 ps | A实测Tmin/面积 | B实测Tmin/面积 | C实测Tmin/面积 | D实测Tmin/面积 |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| mac32 | 2 | 950 | 1000 | 1444.706 / 758.743 | running | running | running |
| mac32 | 2 | 1100 | 1000 | 1444.706 / 758.743 | not_started | not_started | not_started |
| mac32 | 3 | 500 | 1000 | 1444.706 / 758.743 | 1167.750 / 868.851 | 1143.552 / 2619.035 | 679.986 / 1556.444 |
| mac32 | 3 | 750 | 1000 | 1444.706 / 758.743 | 1175.982 / 858.077 | 1127.928 / 2453.187 | 752.738 / 1394.606 |
| mac32 | 3 | 1000 | 1000 | 1444.706 / 758.743 | 1175.412 / 850.568 | 1147.771 / 2384.690 | 1000.594 / 1002.608 |
| add512 | 2 | 700 | 1100 | 1059.685 / 2133.389 | 876.179 / 2707.389 | 876.179 / 2707.389 | 876.179 / 2707.389 |
| add512 | 2 | 800 | 1100 | 1059.685 / 2133.389 | 887.153 / 2602.122 | 887.153 / 2602.122 | 887.153 / 2602.122 |
| add512 | 4 | 350 | 1100 | 1059.685 / 2133.389 | 893.142 / 3440.574 | 893.142 / 3440.574 | 660.684 / 3703.233 |
| add512 | 4 | 400 | 1100 | 1059.685 / 2133.389 | 907.544 / 3425.411 | 907.544 / 3425.411 | 658.909 / 3667.191 |
| mul128 | 2 | 1200 | 2000 | 1884.844 / 7225.600 | not_started | not_started | not_started |
| mul128 | 2 | 1450 | 2000 | 1884.844 / 7225.600 | not_started | not_started | not_started |
| mul128 | 4 | 600 | 2000 | 1884.844 / 7225.600 | 1772.376 / 8157.875 | not_started | not_started |
| mul128 | 4 | 750 | 2000 | 1884.844 / 7225.600 | 1798.567 / 8162.001 | not_started | not_started |
| dot16 | 4 | 850 | 2700 | 2705.125 / 33186.748 | failed | failed | failed |
| dot16 | 4 | 1050 | 2700 | 2705.125 / 33186.748 | failed | failed | failed |
| dot16 | 5 | 700 | 2700 | 2705.125 / 33186.748 | failed | failed | failed |
| dot16 | 5 | 850 | 2700 | 2705.125 / 33186.748 | failed | failed | failed |
| horner64 | 4 | 1900 | 7600 | 5981.929 / 4147.266 | 1889.954 / 4643.861 ✓ | 1754.577 / 5696.187 ✓ | 1897.885 / 4941.031 ✓ |
| horner64 | 4 | 2250 | 7600 | 5981.929 / 4147.266 | 1910.728 / 4631.002 ✓ | 1777.791 / 5682.613 ✓ | 1910.728 / 4631.002 ✓ |
| horner64 | 8 | 950 | 7600 | 5981.929 / 4147.266 | 1319.629 / 5733.672 | 1228.655 / 8963.245 | 993.287 / 6670.160 |
| horner64 | 8 | 1150 | 7600 | 5981.929 / 4147.266 | 1318.734 / 5745.788 | 1219.562 / 8681.632 | 1108.999 / 6477.005 ✓ |
| barrett64 | 4 | 1800 | 6000 | 5603.325 / 7497.328 | 1719.659 / 8055.202 ✓ | 2475.952 / 15646.717 | 1719.659 / 8055.202 ✓ |
| barrett64 | 4 | 2150 | 6000 | 5603.325 / 7497.328 | 1795.253 / 8039.616 ✓ | failed | 1795.253 / 8039.616 ✓ |
| barrett64 | 8 | 900 | 6000 | 5603.325 / 7497.328 | 1566.563 / 8719.861 | 1748.352 / 26877.880 | 1487.043 / 10915.827 |
| barrett64 | 8 | 1100 | 6000 | 5603.325 / 7497.328 | 1543.046 / 8696.678 | 1740.600 / 26019.118 | 1488.661 / 10779.548 |
| karatsuba256 | 4 | 2300 | 9700 | 7201.306 / 21206.916 | 3845.544 / 25748.688 | failed | 2304.854 / 25497.883 |
| karatsuba256 | 4 | 2750 | 9700 | 7201.306 / 21206.916 | failed | failed | 2552.382 / 25476.611 ✓ |
| karatsuba256 | 8 | 1150 | 9700 | 7201.306 / 21206.916 | 3820.217 / 28307.697 | running | running |
| karatsuba256 | 8 | 1400 | 9700 | 7201.306 / 21206.916 | running | running | not_started |
| montgomery256 | 16 | 待A/档1 | 36000 | failed | awaiting_A_reference | awaiting_A_reference | awaiting_A_reference |
| montgomery256 | 16 | 待A/档2 | 36000 | failed | awaiting_A_reference | awaiting_A_reference | awaiting_A_reference |
| montgomery256 | 32 | 待A/档1 | 36000 | failed | awaiting_A_reference | awaiting_A_reference | awaiting_A_reference |
| montgomery256 | 32 | 待A/档2 | 36000 | failed | awaiting_A_reference | awaiting_A_reference | awaiting_A_reference |
| ntt8x64 | 8 | 1550 | 9700 | 9734.198 / 11182.525 | software_pending | software_pending | software_pending |
| ntt8x64 | 8 | 1850 | 9700 | 9734.198 / 11182.525 | software_pending | software_pending | software_pending |
| ntt8x64 | 16 | 800 | 9700 | 9734.198 / 11182.525 | not_started | not_started | not_started |
| ntt8x64 | 16 | 950 | 9700 | 9734.198 / 11182.525 | not_started | not_started | not_started |

已测BCD逐项（A单独见上表及JSON，未测值不填预测）：

| 案例 | L/T | 方法 | Tmin ps | 面积µm² | MHz | setup | hold ps | 实际线程 | 原始读数 |
| --- | --- | --- | ---: | ---: | ---: | --- | ---: | ---: | --- |
| add512 | 2/700 | B | 876.179123 | 2707.389360 | 1141.319 | False | 0.002096 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5/clock-readout/result.json) |
| add512 | 2/700 | C | 876.179123 | 2707.389360 | 1141.319 | False | 0.002096 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5/clock-readout/result.json) |
| add512 | 2/700 | D | 876.179123 | 2707.389360 | 1141.319 | False | 0.002096 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5/clock-readout/result.json) |
| add512 | 2/800 | B | 887.152786 | 2602.121760 | 1127.202 | False | 0.198758 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5/clock-readout/result.json) |
| add512 | 2/800 | C | 887.152786 | 2602.121760 | 1127.202 | False | 0.198758 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5/clock-readout/result.json) |
| add512 | 2/800 | D | 887.152786 | 2602.121760 | 1127.202 | False | 0.198758 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5/clock-readout/result.json) |
| add512 | 4/350 | B | 893.141663 | 3440.573820 | 1119.643 | False | 0.200867 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-27125920dc8d/clock-readout/result.json) |
| add512 | 4/350 | C | 893.141663 | 3440.573820 | 1119.643 | False | 0.200867 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-27125920dc8d/clock-readout/result.json) |
| add512 | 4/350 | D | 660.684143 | 3703.232520 | 1513.583 | False | 0.631495 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-7c2184192453/clock-readout/result.json) |
| add512 | 4/400 | B | 907.544464 | 3425.410620 | 1101.874 | False | 0.336134 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-27125920dc8d/clock-readout/result.json) |
| add512 | 4/400 | C | 907.544464 | 3425.410620 | 1101.874 | False | 0.336134 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-27125920dc8d/clock-readout/result.json) |
| add512 | 4/400 | D | 658.909332 | 3667.190760 | 1517.659 | False | -0.140096 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-7c2184192453/clock-readout/result.json) |
| barrett64 | 4/1800 | B | 1719.659157 | 8055.202140 | 581.511 | True | 7.352091 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-876198aa88c9/clock-readout/result.json) |
| barrett64 | 4/1800 | C | 2475.951538 | 15646.716540 | 403.885 | False | 13.210655 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-83a434da7745/clock-readout/result.json) |
| barrett64 | 4/1800 | D | 1719.659157 | 8055.202140 | 581.511 | True | 7.352091 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-876198aa88c9/clock-readout/result.json) |
| barrett64 | 4/2150 | B | 1795.253326 | 8039.616120 | 557.024 | True | 10.181106 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-876198aa88c9/clock-readout/result.json) |
| barrett64 | 4/2150 | D | 1795.253326 | 8039.616120 | 557.024 | True | 10.181106 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-876198aa88c9/clock-readout/result.json) |
| barrett64 | 8/900 | B | 1566.563232 | 8719.860600 | 638.340 | False | 5.451792 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-1c5b5d444d6f/clock-readout/result.json) |
| barrett64 | 8/900 | C | 1748.351501 | 26877.880080 | 571.967 | False | -0.715650 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-4f5c9617af40/clock-readout/result.json) |
| barrett64 | 8/900 | D | 1487.043335 | 10915.827300 | 672.475 | False | 9.772696 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-18a834929666/clock-readout/result.json) |
| barrett64 | 8/1100 | B | 1543.046478 | 8696.678400 | 648.069 | False | 10.007356 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-1c5b5d444d6f/clock-readout/result.json) |
| barrett64 | 8/1100 | C | 1740.600220 | 26019.118080 | 574.514 | False | 8.648915 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-4f5c9617af40/clock-readout/result.json) |
| barrett64 | 8/1100 | D | 1488.660980 | 10779.548040 | 671.745 | False | 14.151013 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-18a834929666/clock-readout/result.json) |
| horner64 | 4/1900 | B | 1889.953814 | 4643.861220 | 529.113 | True | 4.826098 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-7dfa023a85cd/clock-readout/result.json) |
| horner64 | 4/1900 | C | 1754.576996 | 5696.187300 | 569.938 | True | 1.592129 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-c4d9a155e3c4/clock-readout/result.json) |
| horner64 | 4/1900 | D | 1897.885025 | 4941.030780 | 526.902 | True | 5.314041 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-6ed012ed51db/clock-readout/result.json) |
| horner64 | 4/2250 | B | 1910.727844 | 4631.001660 | 523.361 | True | 4.615502 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-7dfa023a85cd/clock-readout/result.json) |
| horner64 | 4/2250 | C | 1777.790619 | 5682.613320 | 562.496 | True | 5.686729 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-c4d9a155e3c4/clock-readout/result.json) |
| horner64 | 4/2250 | D | 1910.727844 | 4631.001660 | 523.361 | True | 4.615502 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-7dfa023a85cd/clock-readout/result.json) |
| horner64 | 8/950 | B | 1319.628540 | 5733.672480 | 757.789 | False | 9.863305 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-428e4557d83e/clock-readout/result.json) |
| horner64 | 8/950 | C | 1228.654755 | 8963.244540 | 813.898 | False | 6.086923 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-cd5be660311a/clock-readout/result.json) |
| horner64 | 8/950 | D | 993.286819 | 6670.160460 | 1006.759 | False | 9.078571 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T950-4f83e78449a4/clock-readout/result.json) |
| horner64 | 8/1150 | B | 1318.734360 | 5745.788460 | 758.303 | False | 2.804895 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-428e4557d83e/clock-readout/result.json) |
| horner64 | 8/1150 | C | 1219.562248 | 8681.631840 | 819.966 | False | 2.150960 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-cd5be660311a/clock-readout/result.json) |
| horner64 | 8/1150 | D | 1108.999352 | 6477.004620 | 901.714 | True | 4.519954 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-4f83e78449a4/clock-readout/result.json) |
| karatsuba256 | 4/2300 | B | 3845.543701 | 25748.688240 | 260.041 | False | 12.941010 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-karatsuba256-L4/runs/karatsuba256-L4-T2300-afb74d898573/clock-readout/result.json) |
| karatsuba256 | 4/2300 | D | 2304.853673 | 25497.883080 | 433.867 | False | 21.220192 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-karatsuba256-L4/runs/karatsuba256-L4-T2300-8f7d78972cbb/clock-readout/result.json) |
| karatsuba256 | 4/2750 | D | 2552.381638 | 25476.610860 | 391.791 | True | 21.418478 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-karatsuba256-L4/runs/karatsuba256-L4-T2750-8f7d78972cbb/clock-readout/result.json) |
| karatsuba256 | 8/1150 | B | 3820.217285 | 28307.696940 | 261.765 | False | 22.247232 | 2 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-karatsuba256-L8/runs/karatsuba256-L8-T1150-d82729a2bd2b/clock-readout/result.json) |
| mac32 | 3/500 | B | 1167.750366 | 868.851360 | 856.347 | False | 0.111591 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-63bbc97d17bb/clock-readout/result.json) |
| mac32 | 3/500 | C | 1143.552002 | 2619.034560 | 874.468 | False | -0.158318 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-b469e122a49c/clock-readout/result.json) |
| mac32 | 3/500 | D | 679.986298 | 1556.444160 | 1470.618 | False | 0.430267 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-a603cc65f248/clock-readout/result.json) |
| mac32 | 3/750 | B | 1175.982422 | 858.076740 | 850.353 | False | 0.071457 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-63bbc97d17bb/clock-readout/result.json) |
| mac32 | 3/750 | C | 1127.928070 | 2453.187060 | 886.581 | False | 0.261596 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-b469e122a49c/clock-readout/result.json) |
| mac32 | 3/750 | D | 752.738254 | 1394.606160 | 1328.483 | False | 0.525649 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-a603cc65f248/clock-readout/result.json) |
| mac32 | 3/1000 | B | 1175.411911 | 850.568040 | 850.766 | False | 0.007785 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-63bbc97d17bb/clock-readout/result.json) |
| mac32 | 3/1000 | C | 1147.770569 | 2384.690220 | 871.254 | False | 0.476091 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-b469e122a49c/clock-readout/result.json) |
| mac32 | 3/1000 | D | 1000.593858 | 1002.608280 | 999.406 | False | -0.254512 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-9b41cfd87866/clock-readout/result.json) |
| mul128 | 4/600 | B | 1772.376343 | 8157.874500 | 564.214 | False | 13.125223 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T600-e18af3cbdef4/clock-readout/result.json) |
| mul128 | 4/750 | B | 1798.567383 | 8162.000640 | 555.998 | False | 9.701101 | 4 | [readout](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T750-e18af3cbdef4/clock-readout/result.json) |

MAC32复用已预登记的1000ps原A；其余复用初次A-reference。Montgomery保持原36000ps及已有失败，没有用综合值或紧目标A代替。
原紧目标A的已有实测、失败、中止及费用保存在旧快照和JSON的legacy_per_target_A_records中，不删除、不冒充新口径A。
A参考请求不改变此前已冻结的BCD目标、模型、候选选择和RTL；应用PPA没有回流D。当前共享模型仍为诊断身份。
独立原始A表：[A-references.json](A-references.json)；全部当前记录：[comparison.json](comparison.json)；调度：[controller-progress.json](controller-progress.json)。
