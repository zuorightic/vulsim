# Montgomery参考A超时与目标周期复核

2026-11-16T06:48:59.864312+00:00

Montgomery参考A的36000ps请求没有形成setup修复压力。综合setup WNS为+15503.520508ps，CTS后为+12203.6ps、TNS=0；CTS日志明确写No setup violations found，setup buffer为0。

CTS插入21313个hold buffer，hold修复约59.8秒，完整repair_timing约99秒；增大setup周期不能直接解决hold短路径。CTS后751317单元、898734条net。grt限时7200秒，已完成floorplan至CTS阶段合计3420.71秒，余下约3779秒耗在未完成的global-route子阶段；最后记录为pin_access完成300000 groups。未发生内存或CPU限额失败。较长的有限参考时限和pin_access性能分析比继续放宽36000ps更符合现有证据；没有启动新后继。

45条主记录中A/B/C/D分别为11/13/11/10条，D仅覆盖4个案例。A保留未拆分逻辑，B保留原子算术，二者未达流水目标不能单独证明目标设错。

| 案例 | L | 目标ps | D实测Tmin ps | 超出目标 | 块宽/limb |
| --- | ---: | ---: | ---: | ---: | --- |
| add512 | 2 | 700 | 876.179 | 25.17% | [0, 0] |
| add512 | 2 | 800 | 887.153 | 10.89% | [0, 0] |
| add512 | 4 | 350 | 660.684 | 88.77% | [0, 128] |
| add512 | 4 | 400 | 658.909 | 64.73% | [0, 128] |
| barrett64 | 8 | 900 | 1487.043 | 65.23% | [32, 0] |
| barrett64 | 8 | 1100 | 1488.661 | 35.33% | [32, 0] |
| horner64 | 8 | 950 | 993.287 | 4.56% | [16, 0] |
| mac32 | 3 | 500 | 679.986 | 36.00% | [4, 0] |
| mac32 | 3 | 750 | 752.738 | 0.37% | [4, 0] |
| mac32 | 3 | 1000 | 1000.594 | 0.06% | [12, 0] |

Add512 L4与Barrett64 L8目前的目标明显紧于已取得的D实现；MAC750/1000仅差2.738/0.594ps，Horner950差43.287ps。Add512 L2的D选择原始未拆算术，不能将它的失败全归因于固定边界。不能据这10条D记录宣布其余五例全部不可实现。

建议保留原周期作为压力组，后继实际比较使用统一考虑边界、切分不均衡和原子限制的规则。参考形式：ceil50(max(gamma*(T_A-H_A)/L+H_stage+M_split, T_atomic, T_control, T_IO))；建议先比较gamma=1.5/2.0，固定边界与分割裕量另列。边界、原子与控制项先按现有采样／库／软件DAG定义冻结，诊断模型不能作为已证明物理下界；新周期应保持比A参考紧凑。此处是建议，没有冻结新周期、替换队列或根据D实测重新拟合。

扩大T后D会重新优化面积，可能再次靠近新边界。近阈值失败还须检查来自既有训练／验证的预测裕量；不能通过将原D实测Tmin向上取整或更换达标阈值宣称新目标下实现已完成。

原始证据：

- [Montgomery manifest](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/montgomery-A-reference-9x2/runs/montgomery256-A-reference-9x2-capacity/manifest.json)
- [CTS日志](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/montgomery-A-reference-9x2/runs/montgomery256-A-reference-9x2-capacity/logs/asap7/arithmetic_probe/base/4_1_cts.log)
- [CTS指标](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/montgomery-A-reference-9x2/runs/montgomery256-A-reference-9x2-capacity/logs/asap7/arithmetic_probe/base/4_1_cts.json)
- [引脚访问日志](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/montgomery-A-reference-9x2/runs/montgomery256-A-reference-9x2-capacity/logs/asap7/arithmetic_probe/base/5_1_grt.log)
- [耗时与资源收据](/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/backend/montgomery-A-reference-9x2/runs/montgomery256-A-reference-9x2-capacity/grt.command.json)
