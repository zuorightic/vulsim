# 第6—7步扩展组合验证首批

对应[规划§7.73](../../../../mission/lxy-plan-fix.md#step67-combination-validation-batch1)。parallel、bypass各两种原有放置，T=1500ps，共4个有效物理实现／8个synth及grt阶段。测量前冻结节点函数、S绑定、计费候选、支持域和50ps整级预留；没有拟合新参数或从本批校准reserve。

**本批整级数值门槛通过，联合资格仍失败。** 8阶段点误差median／P95为10.9599%／19.6552%，4项总面积误差9.5567%／11.2255%。全部setup满足，仍缺实测违约样本，不能据此证明违约域没有错误可行预测。4项hold均非负，其中3项低于5ps复核带。

| 结构／放置 | s0预测／实测ps | s1预测／实测ps | 面积误差 | setup slack ps | hold slack ps |
| --- | ---: | ---: | ---: | ---: | ---: |
| parallel／p0 | 803.759／763.812 | 1323.486／1201.302 | 11.2255% | +298.698181 | +3.475255 |
| parallel／p1 | 1010.696／1006.410 | 531.413／475.542 | 10.7220% | +493.590271 | +7.131226 |
| bypass／p0 | 822.506／756.449 | 629.644／526.216 | 8.3915% | +743.550720 | +0.138549 |
| bypass／p1 | 1295.131／1084.092 | 155.317／133.933 | 3.1018% | +415.908417 | +2.228794 |

预测为不含预留的点值；决策值在完整路径只加一次50ps。实测为同SDC下T−slack等效预算，不是重新优化的最小时钟。parallel两位置实测面积差0.60%、bypass差0.46%，均处预登记5%并列带；bypass的预测／实测面积顺序相反仍完整报告，不能称排序全部一致。

联合失败明确保留：

- S-only input_service→native共5个银行误差median／P95为56.6494%／59.8657%，超过50%分类门槛；整级max通过没有覆盖这个失败。S-only native→external为16.8315%／20.7677%。
- root_repair独占面积诊断误差median／P95为211.5511%／328.6957%；shared_clock为32.9726%／60.8841%；shared_physical为47.4684%／56.4659%。小总面积误差中存在所有者误差抵消。
- 正式S/G联合、新联合独立测试和正式D未授予，`zero_G_joint_qualified=false`、`full_D_ready=false`。本轮没有增加G或放宽节点支持规则。

需求审计复算最低MAC32的44个放置、四档T共2752项节点查询，全部覆盖。原shared／wide_reduction／cross_stage_saved_value六项1500ps拒绝保持原样，分别涉及capture／联合负载、已知零位和rhs位宽。这是需求回归，不能作为形状白名单；更大复用范围仍需自己的证据。

执行中保留了两项工具链后继。第一项parallel已通过完整CEC及普通负控，但旧脚本错误地按端口名查找向量常量`y[33]`，grt记失败。v4按完整AIG实际索引选择常量top／FF D输出，保存pair重验后仅继续原post-repair ODB／SDC尾段，不重做综合／CTS／repair。bypass／p0的16组逻辑状态共享物理FF由实际映射发现；同owner／stage／enable／reset／极性核对及每个逻辑引用布尔证明通过，330个唯一FF计一次，346个逻辑位引用全部保留。不同控制／生命周期仍拒绝，冻结S价格没有按实测FF回改。

读取器新增完整动态／常量top-port分区：mapped常量位、完整物理端口census及STA常量值一致才排除动态查询。累计8阶段5624动态端点、124常量输出检查，940逻辑状态引用／924唯一物理FF；33项真实负控拒绝，14份实际CEC负控日志保留。首次缺CTS gold的布尔检查、一次提前启动状态汇总缺最后映射、常量输出旧适配器拒绝、初次封包超大小及过早回放失败都在原收据中，未删除或退款。

便携回放从封存源码恢复，不调用实时源码、EDA或拟合：

```bash
python3 -I -B experiments/arithmetic/evidence/step67_combination_batch1_v2/replay.py replay \
  --evidence experiments/arithmetic/evidence/step67_combination_batch1_v2
```

已得到`passed_isolated_batch1_replay`。回放重算实际状态／别名census、布尔状态、严格Liberty／net路径、常量端点、冻结函数组合和完整分析／排序／四项联合失败；只对诊断路径`raw_reports_prefix`允许恢复位置变化。物理浮点比较绝对1e-8／相对1e-12，结构与角色严格一致。CEC实际执行已在收费叶中验证；回放核对保存前后网表SHA及主／负结论日志，不重新调用工具或把日志当作新一次CEC。

[manifest.json](manifest.json)及[file-index.json.gz](file-index.json.gz)记录6818成员和每个文件SHA，分块均≤512KiB。v2将首包超过1MiB的文件索引压缩，语义、价格和物理标签不变；首包的超限失败及完整字节保留在显式大产物目录，见[v1说明](../step67_combination_batch1_v1/README.md)。本包约4.96MB（最终README／费用结算另计，仍≤5MiB）。

完整物理产物依次保留在`/home/zyrv/vulsim-artifacts/stage67-batch1-20261111-v1`、`...-v2`、`...-v3`；最终有效分析为v3的`analysis-v2/validation.json`，原失败和早期分析都保留。完整原始归档约57.7MB，9322成员已实际恢复并逐文件核对，见[restore-proof.json](restore-proof.json)；同盘保留不是异机备份。封包后补入的说明、完整性、费用与超限首包搬移记录另存，不冒充已进入较早归档。

最终完整性与费用见[integrity.json](integrity.json)和[resource-closure.json](resource-closure.json)：4 synth／5 grt／0 detailed、54 support、356.963593秒叶墙钟／543.64秒CPU，pending=0。4 synth／5 grt包含首项失败及从保存CTS检查点的唯一后继；所有support和失败按共享Ledger结算，不与原serial pilot或计费推导重复收费。25项原冻结推理、241项封存后继源、四项预测／RTL／端点及继承设计文件SHA核对通过。联合独立源及1000ps保持锁定，后续688／688调用、86400秒墙钟／172800秒CPU／30GiB保留额度核对通过。本包含收尾文件约5.08MB，最大单文件512KiB，满足5MiB／1MiB限制。未git add／commit／push。
