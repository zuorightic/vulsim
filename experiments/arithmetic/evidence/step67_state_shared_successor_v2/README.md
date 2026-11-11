# 第6—7步：纯转发S与共享面积后继（第二次封包）

本包补齐源码依赖后，隔离数值重算因用户目录numpy不可见而失败。现行[后继v3](../step67_state_shared_successor_v3/README.md)用标准库独立NNLS完成回放，原模型、标签和联合失败不变。下文保留此封包的内容与范围。

对应[规划§7.74](../../../../mission/lxy-plan-fix.md#step67-state-shared-train-audit)。本轮不运行新synth／grt，不读取联合独立测试。先用原train审计／拟合并冻结候选，再用已消费的combination_validation复验；结果为`failed_joint_validation`，不得绑定正式D。

冻结候选SHA256：`8f9d79b80d0c8f12c60a0d55fef499b3a1fef1c05e230b74a299099c21ba00db`。节点发布、原S三所有者状态面积系数、50ps整级reserve不变。原旧失败／价格保留，新消费实现为`FactoredTimingCostProvider`，Python独立核对；原`OwnedTimingCostProvider`保持原身份。

train审计得到三项具体修正：

- 原S分区沿FF反向追踪clock树，漏计输入接clock、输出悬空的CTS负载缓冲器；后继按实际clock net连接转归clock，旧标签不覆盖。216个S train快照累计6829个此类引用，面积按快照累计1070.18658µm²，不是唯一单元数。
- birth_data含人工adapter／observer的负载；剔除串联逻辑不能还原launch slew，所以纯寄存器转发改用原native_data的同类FF-Q／capture边界147.7647705ps。算术birth诊断另列231.422455ps，native→external为155.316833ps。实际S-only保存银行全部进入计时，不只看算术cut captures。
- repair只剔除完整实际负载最终均属于adapter／observer的根部支路；触及状态或混合责任仍保留。共享面积用语义位数／FF数／reset-one及冻结预测功能面积的简单train-only NNLS，禁止使用实测节点面积作为D特征。

训练包括S的216行／24源组和原节点352行／38源组，共568行／62源组；需要完整功能预测面积的clock／physical用462行／61源组，其余106行因某consumer函数缺覆盖只用于repair。648条S路径在原提取叶逐弧／net验证。每个源等权，不用validation选择系数；初次无布局范围特征的train草稿保留为诊断。候选、5项实现源及二进制先冻结，后读取后继validation结果。

| 六位置／1500ps validation项目 | median／P95误差 | 结论 |
| --- | ---: | --- |
| 12个完整阶段点值 | 12.7537%／19.6552% | 通过15%／35% |
| 6项总面积 | 5.8306%／7.7231% | 通过15%／35% |
| 8个S-only输入转发银行 | 3.0147%／6.0190% | 通过50%分类门槛 |
| 5个S-only外部转发银行 | 16.8315%／20.7677% | 通过50%分类门槛 |
| shared physical面积 | 3.1213%／17.8894% | 通过15%／35% |
| root repair面积 | 26.1543%／29.0350% | median失败 |
| shared clock面积 | 10.8506%／42.5219% | P95失败 |

这里的实测时序是同SDC下T−slack预算，不是重新优化得到的最小时钟。6项setup均满足，仍缺实测违约样本；hold沿用原快照，serial／placement-1仍为负。两项失败后没有调整参数、reserve或门槛。

真实6组合×2位置×3T共36请求的C++／Python连接、全状态captures、价格、共享特征及独占面积一致，18覆盖／18保留原节点拒绝。12项原生拒绝检查及4类错误共享参数各36请求全部拒绝；原先未计入的两个bypass纯转发银行已实际进入C++结果。真实train根部图见证含528根部单元、23个clock负载重归属，改名不改变责任；触及真实状态的支路保留，断开输入和多驱动负控拒绝。

**完整D需求覆盖也未通过。** 真实MAC32编译得到44合法放置，500／1500／3000ps每档均27覆盖／17拒绝，共81覆盖／51拒绝，均为新shared语义特征超冻结训练支持域。原节点函数的2752项覆盖结论不变；没有以旧常数或外推填价。44仅用于需求回归，不是形状白名单。`zero_G_joint_qualified=false`、`full_D_ready=false`。

便携回放入口如下，无EDA或实时源码：

```bash
python3 -I -B experiments/arithmetic/evidence/step67_state_shared_successor_v2/replay.py replay \
  --evidence experiments/arithmetic/evidence/step67_state_shared_successor_v2
```

小包封存266成员，约2.61MB、单块≤512KiB；逐文件索引在[file-index.json.gz](file-index.json.gz)，身份见[manifest.json](manifest.json)。回放从568份认证train标量／特征重新做固定NNLS，从648条路径分解复算源等权边界，并重算一个完整真实根部连接见证、36项Python／C++结果、六位置validation及失败、MAC32覆盖记录。数值容差绝对1e-8／相对1e-10，结构／角色严格相同。它不重开全部原训练ODB；原始完整图提取与全量Liberty／net资格由收费提取叶和完整保留产物承担，不能把小包标量重放称为全量物理重读。

原v1缺传递导入的回放失败保留，v2只补依赖。完整本轮根为`/home/zyrv/vulsim-artifacts/stage67-state-shared-20261111-v1`，含早期失败、train草稿、冻结、原生结果及复验；原始归档约11.2MB、22成员实际恢复逐文件验SHA，见[restore-proof.json](restore-proof.json)。同盘留存不是异机备份，原目录保留直到用户清理。封包后增补的README、费用及完整性另存，不冒充已进入较早归档。

本轮最终完整性与费用见[integrity.json](integrity.json)、[resource-closure.json](resource-closure.json)。禁止使用本六位置继续调到通过；下一包应先登记共享需求域、角色、有限采样及新validation职责，针对小FF／布局范围和repair服务／reset负载补证。1000ps及原联合独立源继续锁定，未git add／commit／push。
