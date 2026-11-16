# 已撤回：固定RTL改变后端时钟的诊断批次

**本批次不能用于新目标下的D比较，已停止，结果和费用仅作诊断留存。当前重测保持原T，只放宽资源，见[有效资源后继](../failure-resource-only-v1/README.md)。** [撤回收据](withdrawal.json)；[原规划归档](withdrawn-plan-section.md)。

# 失败实验宽松条件后继

2026-11-16T15:51:19.839690+00:00

用户授权的单次重测；原主矩阵、失败和费用保留。固定原RTL及寄存器位置，在新统一请求下测B/C/D及同池归因；原模型预测仍属原T，未重新优化D。A继续引用原参考，不按流水T重测。

综合上限3600秒、完整grt上限14400秒、每工具2线程；共享原9槽及累计账本。Dot16的C/D/归因使用16GiB，其他8GiB；保留至少12GiB存储，发射阈值14GiB。每任务一次，后继失败不自动重试。

| 案例 | L | 原T ps | 新请求 ps | B Tmin/面积 | C Tmin/面积 | D Tmin/面积 | 同池归因 |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| barrett64 | 4 | 2150 | 2800 | 1874.826 / 8045.915 ✓ | failed | 1874.826 / 8045.915 ✓ | queued |
| dot16 | 4 | 850 | 2250 | queued | queued | queued | queued |
| dot16 | 4 | 1050 | 2450 | queued | queued | queued | queued |
| dot16 | 5 | 700 | 1950 | queued | queued | queued | queued |
| dot16 | 5 | 850 | 2150 | queued | queued | queued | queued |
| karatsuba256 | 4 | 2300 | 4350 | queued | queued | queued | queued |
| karatsuba256 | 4 | 2750 | 4750 | queued | queued | queued | queued |
| karatsuba256 | 8 | 1150 | 2150 | queued | queued | queued | queued |
| karatsuba256 | 8 | 1400 | 2300 | queued | queued | queued | queued |

新时钟依据为主BCD失败现场已有synth/place/CTS的最大core-clock周期与原请求的最大值，首档乘1.10、次档乘1.20，向上取整到50ps；同池静态归因不决定主方法的时钟。中间周期仅决定新请求，不是完整实测Tmin。
NTT L8另作一次软件恢复：栈增至64MiB、地址空间16GiB、CPU4小时／墙钟6小时、faulthandler；保留原−11日志及既有候选。成功仍需完整回放及ready收据，之后由原控制器登记原目标BCD，不强行写入本宽松时钟表。

[准入](admission.json)；[时钟依据](clock-basis.json)；[机器状态](results.json)。
