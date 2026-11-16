# 后端耗时：命令与ORFS子阶段

快照：2026-11-16 18:07:23 +08:00。

按当前矩阵引用的唯一物理目录去重，另列Montgomery当前A参考；不将共享ABCD记录重复计时。
表中累计时长是各任务耗时之和，包含并发重叠，不能当作机器经过的墙钟时间。命令统计使用已返回的命令（含超时）；运行命令只在逐任务表列下界。
`grt`命令包含floorplan、placement、CTS和global-route整个流程；下表ORFS子阶段用于继续定位。未结束的长阶段没有Elapsed，不进入“已结束子阶段”分位数，所以该表存在幸存偏差。

| 命令 | 已返回次数 | 累计任务小时 | 中位秒 | P90秒 | 最大秒 |
| --- | ---: | ---: | ---: | ---: | ---: |
| grt | 76 | 56.06 | 1234.9 | 7200.1 | 7200.5 |
| synth | 83 | 3.32 | 48.9 | 416.0 | 836.6 |
| clock-readout | 56 | 0.32 | 14.6 | 38.7 | 111.6 |
| synth-snapshot | 83 | 0.20 | 5.1 | 21.6 | 36.3 |
| grt-snapshot | 56 | 0.15 | 8.3 | 17.0 | 46.1 |
| environment | 85 | 0.02 | 0.2 | 1.5 | 9.6 |

| 已结束ORFS子阶段 | 次数 | 累计任务小时 | 中位秒 | P90秒 | 最大秒 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 4_1_cts | 73 | 15.71 | 213.7 | 2447.5 | 5531.7 |
| 5_1_grt | 56 | 11.06 | 435.9 | 1718.4 | 4213.1 |
| 3_3_place_gp | 82 | 5.14 | 82.2 | 677.8 | 1407.9 |
| 2_1_floorplan | 83 | 3.07 | 63.9 | 396.4 | 700.3 |
| 3_5_place_dp | 81 | 2.09 | 32.2 | 299.0 | 522.3 |
| 3_1_place_gp_skip_io | 83 | 1.35 | 19.1 | 165.7 | 364.0 |
| 3_4_place_resized | 82 | 1.34 | 23.5 | 181.8 | 294.7 |
| 2_4_floorplan_pdn | 83 | 0.08 | 2.5 | 8.0 | 13.5 |
| 3_2_place_iop | 83 | 0.05 | 1.7 | 3.6 | 5.2 |
| 2_2_floorplan_macro | 83 | 0.05 | 1.8 | 3.5 | 4.7 |
| 2_3_floorplan_tapcell | 83 | 0.04 | 1.5 | 2.9 | 4.1 |

| 任务（去重） | 线程 | 状态 | synth秒 | grt秒 | 当前／终止阶段 | 未完成阶段余时估计秒 |
| --- | ---: | --- | ---: | ---: | --- | ---: |
| [add512-T350-27125920dc8d](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-27125920dc8d) | 4 | completed | 25.5 | 325.1 | 5_1_grt | — |
| [add512-T350-41f1f36cf2c3](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-41f1f36cf2c3) | 4 | completed | 24.6 | 264.4 | 5_1_grt | — |
| [add512-T350-7c2184192453](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T350-7c2184192453) | 4 | completed | 14.9 | 325.2 | 5_1_grt | — |
| [add512-T400-27125920dc8d](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-27125920dc8d) | 4 | completed | 26.0 | 296.2 | 5_1_grt | — |
| [add512-T400-41f1f36cf2c3](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-41f1f36cf2c3) | 4 | completed | 24.3 | 245.3 | 5_1_grt | — |
| [add512-T400-7c2184192453](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-add512/runs/add512-T400-7c2184192453) | 4 | completed | 15.3 | 348.1 | 5_1_grt | — |
| [horner64-T950-428e4557d83e](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-428e4557d83e) | 4 | completed | 26.0 | 741.9 | 5_1_grt | — |
| [horner64-T950-6c415b9cf3b2](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-6c415b9cf3b2) | 4 | completed | 26.7 | 1676.9 | 5_1_grt | — |
| [horner64-T950-cd5be660311a](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-horner64/runs/horner64-T950-cd5be660311a) | 4 | completed | 48.1 | 793.6 | 5_1_grt | — |
| [mac32-T1000-073243214bc6](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-073243214bc6) | 4 | completed | 10.2 | 106.7 | 5_1_grt | — |
| [mac32-T1000-63bbc97d17bb](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-63bbc97d17bb) | 4 | completed | 7.2 | 124.6 | 5_1_grt | — |
| [mac32-T1000-9b41cfd87866](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-9b41cfd87866) | 4 | completed | 8.4 | 69.1 | 5_1_grt | — |
| [mac32-T1000-b469e122a49c](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-b469e122a49c) | 4 | completed | 16.4 | 155.1 | 5_1_grt | — |
| [mac32-T1000-f6095f4a151a](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T1000-f6095f4a151a) | 4 | completed | 8.6 | 94.7 | 5_1_grt | — |
| [mac32-T500-073243214bc6](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-073243214bc6) | 4 | completed | 7.4 | 120.7 | 5_1_grt | — |
| [mac32-T500-63bbc97d17bb](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-63bbc97d17bb) | 4 | completed | 6.8 | 146.5 | 5_1_grt | — |
| [mac32-T500-83903048b70d](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-83903048b70d) | 4 | completed | 13.0 | 172.3 | 5_1_grt | — |
| [mac32-T500-a603cc65f248](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-a603cc65f248) | 4 | completed | 20.3 | 135.0 | 5_1_grt | — |
| [mac32-T500-b469e122a49c](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T500-b469e122a49c) | 4 | completed | 23.1 | 251.5 | 5_1_grt | — |
| [mac32-T750-073243214bc6](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-073243214bc6) | 4 | completed | 16.4 | 157.2 | 5_1_grt | — |
| [mac32-T750-63bbc97d17bb](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-63bbc97d17bb) | 4 | completed | 6.9 | 203.7 | 5_1_grt | — |
| [mac32-T750-a4315f7c75b2](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-a4315f7c75b2) | 4 | completed | 11.1 | 143.2 | 5_1_grt | — |
| [mac32-T750-a603cc65f248](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-a603cc65f248) | 4 | completed | 12.0 | 84.9 | 5_1_grt | — |
| [mac32-T750-b469e122a49c](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mac32/runs/mac32-T750-b469e122a49c) | 4 | completed | 18.6 | 210.7 | 5_1_grt | — |
| [mul128-T600-334ab0c95758](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T600-334ab0c95758) | 4 | completed | 91.6 | 1293.5 | 5_1_grt | — |
| [mul128-T600-6d72e638cd85](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T600-6d72e638cd85) | 4 | completed | 46.2 | 1010.7 | 5_1_grt | — |
| [mul128-T600-e18af3cbdef4](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T600-e18af3cbdef4) | 4 | completed | 44.9 | 1121.5 | 5_1_grt | — |
| [mul128-T750-334ab0c95758](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T750-334ab0c95758) | 4 | completed | 94.7 | 1486.9 | 5_1_grt | — |
| [mul128-T750-6d72e638cd85](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T750-6d72e638cd85) | 4 | completed | 48.9 | 1098.0 | 5_1_grt | — |
| [mul128-T750-e18af3cbdef4](/home/zyrv/vulsim-artifacts/workload-equivalent-steps678-tight-v2-scaled-A/final-mul128/runs/mul128-T750-e18af3cbdef4) | 4 | completed | 47.4 | 1010.9 | 5_1_grt | — |
| [add512-L2-T700-41f1f36cf2c3](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-41f1f36cf2c3) | 2 | completed | 27.9 | 436.1 | 5_1_grt | — |
| [add512-L2-T700-be37505847a5](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T700-be37505847a5) | 2 | completed | 27.1 | 529.7 | 5_1_grt | — |
| [add512-L2-T800-41f1f36cf2c3](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-41f1f36cf2c3) | 2 | completed | 28.2 | 375.9 | 5_1_grt | — |
| [add512-L2-T800-be37505847a5](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-add512-L2/runs/add512-L2-T800-be37505847a5) | 2 | completed | 33.8 | 461.0 | 5_1_grt | — |
| [barrett64-L4-T1800-83a434da7745](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-83a434da7745) | 2 | completed | 131.6 | 5593.1 | 5_1_grt | — |
| [barrett64-L4-T1800-876198aa88c9](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-876198aa88c9) | 2 | completed | 76.9 | 1070.7 | 5_1_grt | — |
| [barrett64-L4-T1800-c3eba59eb78f](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-c3eba59eb78f) | 2 | completed | 82.1 | 3582.5 | 5_1_grt | — |
| [barrett64-L4-T1800-fe0456a5a32c](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-fe0456a5a32c) | 2 | failed | 66.1 | 7200.2 | 4_1_cts | 6425.8 |
| [barrett64-L4-T2150-83a434da7745](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-83a434da7745) | 2 | running | 149.5 | 3074.8（运行下界） | 4_1_cts | 2494.0 |
| [barrett64-L4-T2150-876198aa88c9](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-876198aa88c9) | 2 | completed | 74.1 | 1176.3 | 5_1_grt | — |
| [barrett64-L4-T2150-c3eba59eb78f](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-c3eba59eb78f) | 2 | completed | 81.3 | 2458.2 | 5_1_grt | — |
| [barrett64-L4-T2150-fe0456a5a32c](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T2150-fe0456a5a32c) | 2 | running | 69.8 | 5703.3（运行下界） | 4_1_cts | 4727.7 |
| [barrett64-L8-T1100-18a834929666](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-18a834929666) | 2 | completed | 74.0 | 2268.7 | 5_1_grt | — |
| [barrett64-L8-T1100-1c5b5d444d6f](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-1c5b5d444d6f) | 2 | completed | 68.9 | 2511.4 | 5_1_grt | — |
| [barrett64-L8-T1100-4f5c9617af40](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-4f5c9617af40) | 2 | completed | 218.6 | 4311.5 | 5_1_grt | — |
| [barrett64-L8-T1100-f0fe43c6f58a](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-f0fe43c6f58a) | 2 | completed | 99.4 | 3161.5 | 5_1_grt | — |
| [barrett64-L8-T1100-fe0456a5a32c](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T1100-fe0456a5a32c) | 2 | failed | 66.6 | 6211.7 | 3_5_place_dp | 5445.6 |
| [barrett64-L8-T900-18a834929666](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-18a834929666) | 2 | completed | 87.0 | 2816.4 | 5_1_grt | — |
| [barrett64-L8-T900-1c5b5d444d6f](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-1c5b5d444d6f) | 2 | completed | 66.4 | 2268.7 | 5_1_grt | — |
| [barrett64-L8-T900-4f5c9617af40](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-4f5c9617af40) | 2 | completed | 215.9 | 5866.8 | 5_1_grt | — |
| [barrett64-L8-T900-df305882385e](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-df305882385e) | 2 | completed | 90.9 | 2604.5 | 5_1_grt | — |
| [barrett64-L8-T900-fe0456a5a32c](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L8/runs/barrett64-L8-T900-fe0456a5a32c) | 2 | failed | 61.0 | 7200.1 | 4_1_cts | 6367.3 |
| [dot16-L4-T1050-13041929dd25](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T1050-13041929dd25) | 2 | failed | 433.1 | 7200.0 | 5_1_grt | 4923.9 |
| [dot16-L4-T1050-2776e286ec00](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T1050-2776e286ec00) | 2 | failed | 248.2 | 7200.1 | 5_1_grt | 528.4 |
| [dot16-L4-T1050-5d322a4d43a9](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T1050-5d322a4d43a9) | 2 | failed | 300.1 | 7200.1 | 5_1_grt | 3255.7 |
| [dot16-L4-T1050-8327002228a5](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T1050-8327002228a5) | 2 | failed | 599.6 | 7200.1 | 5_1_grt | 3535.4 |
| [dot16-L4-T1050-fc4843e24724](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T1050-fc4843e24724) | 2 | failed | 428.4 | 7200.1 | 5_1_grt | 1986.4 |
| [dot16-L4-T850-13041929dd25](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-13041929dd25) | 2 | failed | 417.1 | 7200.1 | 5_1_grt | 4252.0 |
| [dot16-L4-T850-2776e286ec00](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-2776e286ec00) | 2 | failed | 283.4 | 7200.1 | 5_1_grt | 1520.6 |
| [dot16-L4-T850-5d322a4d43a9](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-5d322a4d43a9) | 2 | failed | 291.4 | 7200.1 | 5_1_grt | 2753.0 |
| [dot16-L4-T850-75964220595d](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-75964220595d) | 2 | failed | 396.0 | 7200.1 | 5_1_grt | 3247.5 |
| [dot16-L4-T850-8327002228a5](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-8327002228a5) | 2 | failed | 550.7 | 7200.1 | 5_1_grt | 3924.4 |
| [dot16-L5-T700-2776e286ec00](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T700-2776e286ec00) | 2 | failed | 287.1 | 7200.1 | 5_1_grt | 1172.5 |
| [dot16-L5-T700-4c2ee7748c79](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T700-4c2ee7748c79) | 2 | failed | 405.5 | 7200.5 | 5_1_grt | 4776.0 |
| [dot16-L5-T700-5d8ecc4f2639](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T700-5d8ecc4f2639) | 2 | failed | 411.4 | 7200.0 | 5_1_grt | 2864.7 |
| [dot16-L5-T700-8bbe5fa52f58](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T700-8bbe5fa52f58) | 2 | failed | 336.9 | 3754.4 | 4_1_cts | — |
| [dot16-L5-T700-b6a28e166624](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T700-b6a28e166624) | 2 | failed | 751.7 | 3828.9 | 4_1_cts | 960.1 |
| [dot16-L5-T850-4c2ee7748c79](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T850-4c2ee7748c79) | 2 | running | 392.3 | 2144.7（运行下界） | 4_1_cts | 401.6 |
| [dot16-L5-T850-5d8ecc4f2639](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T850-5d8ecc4f2639) | 2 | running | 423.1 | 2114.6（运行下界） | 4_1_cts | 205.0 |
| [dot16-L5-T850-8bbe5fa52f58](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T850-8bbe5fa52f58) | 2 | failed | 309.3 | 7200.4 | 5_1_grt | 3627.3 |
| [dot16-L5-T850-b6a28e166624](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L5/runs/dot16-L5-T850-b6a28e166624) | 2 | running | 733.2 | 1823.6（运行下界） | 3_3_place_gp | 1133.4 |
| [horner64-L4-T1900-6c415b9cf3b2](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-6c415b9cf3b2) | 2 | running | 30.7 | 2291.9（运行下界） | 5_1_grt | 626.9 |
| [horner64-L4-T1900-6ed012ed51db](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-6ed012ed51db) | 2 | completed | 40.0 | 619.8 | 5_1_grt | — |
| [horner64-L4-T1900-7dfa023a85cd](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-7dfa023a85cd) | 2 | completed | 35.0 | 617.8 | 5_1_grt | — |
| [horner64-L4-T1900-c4d9a155e3c4](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T1900-c4d9a155e3c4) | 2 | completed | 46.8 | 651.2 | 5_1_grt | — |
| [horner64-L4-T2250-6c415b9cf3b2](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-6c415b9cf3b2) | 2 | running | 37.3 | 877.6（运行下界） | 4_1_cts | 581.6 |
| [horner64-L4-T2250-6ed012ed51db](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-6ed012ed51db) | 2 | running | — | — | 尚未进入物理阶段 | — |
| [horner64-L4-T2250-7dfa023a85cd](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-7dfa023a85cd) | 2 | completed | 32.0 | 567.1 | 5_1_grt | — |
| [horner64-L4-T2250-c4d9a155e3c4](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L4/runs/horner64-L4-T2250-c4d9a155e3c4) | 2 | running | — | — | 尚未进入物理阶段 | — |
| [horner64-L8-T1150-428e4557d83e](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-428e4557d83e) | 2 | completed | 34.2 | 1326.4 | 5_1_grt | — |
| [horner64-L8-T1150-6c415b9cf3b2](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-6c415b9cf3b2) | 2 | completed | 32.7 | 2254.2 | 5_1_grt | — |
| [horner64-L8-T1150-cd5be660311a](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T1150-cd5be660311a) | 2 | completed | 56.4 | 1392.0 | 5_1_grt | — |
| [horner64-L8-T950-4f83e78449a4](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T950-4f83e78449a4) | 2 | completed | 40.4 | 1095.9 | 5_1_grt | — |
| [horner64-L8-T950-c4bab4fd0309](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-horner64-L8/runs/horner64-L8-T950-c4bab4fd0309) | 2 | completed | 39.5 | 1372.2 | 5_1_grt | — |
| [montgomery256-A-reference-9x2-capacity](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/montgomery-A-reference-9x2/runs/montgomery256-A-reference-9x2-capacity) | 2 | failed | 836.6 | 7200.1 | 5_1_grt | 3779.3 |

逐任务原始日志、命令与修复内部计时见[JSON](backend-timing.json)。`repair_timing`外层包含setup/hold内部修复，不能将三者再次相加。
约束过紧可触发漫长setup repair；hold repair受短路径、使能／保持逻辑和状态规模影响，放宽setup周期不能保证消除。引脚访问检查发生在5_1_grt真正路由之前，大网表规模会独立拖慢。
运行配置为每任务NUM_CORES=2；进程树线程数包含辅助线程、多个进程或工具内部线程，不能仅凭瞬时线程数把任务称为全部2核已吃满。实际CPU/墙钟及分线程汇总见JSON。
诊断不修改当前队列。后继可先检查setup修复、hold缓冲、LEC和pin_access分别占比；优化拆分／寄存器状态规模，再独立登记容量／时限／工具后继。改变修复策略或跳过检查会改变评价口径，不能悄悄应用到本轮。
