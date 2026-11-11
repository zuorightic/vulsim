# 第6—7步真实pilot后继证据 v2

这是[step67_joint_pilot_v1](../step67_joint_pilot_v1/README.md)的证据封包后继。v1的逻辑归属依赖缺失导致隔离回放导入失败，原失败和收据保留；v2只补齐完整冻结DSE Python依赖和归档命名，模型、物理packet、标签、零G失败及选择规则没有改变。

隔离回放已通过：

```text
passed_isolated_stage67_pilot_replay
physical_stages=4
endpoint_checks=3394
Boolean_FF_checks=567
software_queries=96
covered=78
zero_G_failure_preserved=true
new_EDA_calls=0
full_D_ready=false
```

发布节点模型SHA256为`513f2f7693c702c492fec380ed81b385f4691f18bd05aaac6596d27f0340f0d2`，S binding SHA256为`76dd37094be027dd5e4c6565d63ae037be1b541a88e63e0dfe233fe571ef3542`。隔离回放从封存内容重算四个物理阶段的端点、真实Liberty弧、所有权、面积和567个FF的状态语义，并复算96次函数查询，保留零G失败。28项负控在实际packet资格叶中执行通过，其报告另行封存；隔离入口不重复运行该负控叶，也没有调用EDA或重新拟合。

原始pilot产物及后继归档保留在`/home/zyrv/vulsim-artifacts/stage67-joint-20261111-v2`，同盘目录不是异机备份。本轮及封包／回放／源码语法核对结算2 synth、2 grt、36 support，叶墙钟191.731497秒、CPU286.93秒，pending=0；失败收据均保留。当前仍是“状态／端点pilot通过，零G联合失败，G未发布，`full_D_ready=false`”。
