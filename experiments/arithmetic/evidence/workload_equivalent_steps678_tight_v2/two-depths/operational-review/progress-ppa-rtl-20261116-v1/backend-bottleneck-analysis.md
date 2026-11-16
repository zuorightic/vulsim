# 后端最长耗时的实际位置与原因

样本来自2026-11-16 18:07:23 +08:00的唯一物理目录清单；以下只细分当时已结算的日志，包含超时失败。

**主要瓶颈是OpenROAD物理阶段中的时序修复、CTS内的等价性证明／合法化，以及5_1_grt的引脚访问准备；Yosys综合不是主要累计耗时。**
已返回grt命令累计56.06任务小时，综合3.32任务小时。grt占所有已返回命令累计耗时约93%；并行有重叠，不能将任务小时相加当机器墙钟时间。

| 具体任务 | 已测耗时／日志证据 | 判断 |
| --- | --- | --- |
| Barrett64 L4，A，1800ps | synth 66.11秒；grt 7200.16秒超时；CTS内setup repair 6390.74秒、hold repair 9.59秒 | 该任务主要卡setup优化，约占grt预算89%；不是hold修复或纯路由 |
| Dot16 L4，A，850ps | CTS 4624.77秒（77.08分）；其中setup 1397.22秒、hold 192.14秒、LEC日志区间1743.081秒（SAT求解1682.238秒）、后续详细合法化1035秒 | CTS不是仅造时钟树：证明和合法化也占大量时间；插入44255个hold buffers后网表／布局负担增大 |
| 同一Dot16任务的下一阶段 | 5_1_grt没有结束；日志停在pin_access、70000 groups；grt余时约1520.61秒 | 这约25.34分钟包括该子阶段读库、pin_access及make开销，无法精确全归pin_access；真正全局布线尚未开始 |
| Montgomery256当前A参考，36000ps，9×2／16GiB | synth 836.58秒；floorplan到CTS约3420.71秒；CTS 821.01秒、repair约99秒；5_1_grt余时约3779.35秒，pin_access到300000 groups后超时 | 当前setup WNS +12203.6ps，setup buffers=0；该参考超时主要是大网表和引脚访问容量，不能用“时钟过紧”解释 |

Barrett原始证据：[setup与hold修复](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-barrett64-L4/runs/barrett64-L4-T1800-fe0456a5a32c/logs/asap7/arithmetic_probe/base/4_1_cts.log:371)。
Dot16原始证据：[LEC时间戳](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-2776e286ec00/logs/asap7/arithmetic_probe/base/4_rsz_lec_check.log)；[CTS修复及详细合法化](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-2776e286ec00/logs/asap7/arithmetic_probe/base/4_1_cts.log:1130)；[pin_access](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/matrix-dot16-L4/runs/dot16-L4-T850-2776e286ec00/logs/asap7/arithmetic_probe/base/5_1_grt.log)。

Montgomery的CTS为751317个标准单元，hold buffers=21313；保守CTS等价性证明已经成功。早期版本在Kepler检查处超时、后继8GiB内存不足和当前16GiB的pin_access超时是三个不同失败身份，应分别保留。

| CTS等内部类别（嵌套，不能再加到外层总时长） | 计时条目数 | 累计任务小时 | 最大秒 |
| --- | ---: | ---: | ---: |
| setup_repair_internal | 186 | 11.08 | 6390.740 |
| hold_repair_internal | 130 | 1.33 | 1546.510 |
| detailed_placement | 83 | 2.80 | 1385.000 |
| LEC_completed_logged_span | 71 | 4.46 | 2152.967 |

LEC统计是首条到末条日志时间差，包含构图／求解但不含进程启动；未完成的LEC不进入累计完成分母。各类别并不覆盖CTS所有开销，也不应相互或与外层时长重复相加。内存／分配器崩溃后的包装器等待亦不等于有效计算时间。

本机仍使用用户要求的9并行、每工具2线程。Dot16上述CTS日志CPU利用率约124%，相当于该阶段平均约1.24个CPU核；一些证明、合法化及pin_access步骤不能稳定吃满线程。没有并发对照实测，不能据此断言改成更高线程或更少并发就一定更快。

后续处理按原因推进：

1. 先修复位置提案与G路径，报告状态峰值，避免在目标不可达时生成大量部分积／保存寄存器，给CTS、hold缓冲和pin_access增加负担。
2. 对setup修复很长的未拆分A，保留其压力目标结果／失败；若追加容量或较宽松参考，应另登记版本，不能把宽松映射结果冒充当前紧目标的A。
3. 对LEC，后继可核验哪些变换满足已有的保守结构充分条件证明；只在满足前提并有真实消费收据时使用，其他变换回退完整证明，不跳过等价性。
4. 对pin_access，先核查单元／net／buffer规模及实际组进度，再为固定RTL、固定T登记有限容量／时限／工具版本后继；单纯放宽周期不能保证缩短。
5. 当前冻结队列继续运行，失败不自动重试；本次没有更改NUM_CORES、限时、时钟、修复策略或工具。

[完整命令与子阶段表](backend-timing.md)；[内部计时／LEC时间戳JSON](backend-hotspots.json)；[只读分析脚本](analyze-hotspots.py)。
