# 真实 ConditionalBoundaryProvider 与 S 有限复用

本包对应 `mission/lxy-plan-fix.md` 第四章 §7.63。RTLzz 新增 `ReusedStateBoundaryProvider`，以真实 BEIR、placement、状态寿命／掩码／reset／enable和公共服务协议构造非算术价格。原S面积系数、边界回归器和reserve不变；共享项从原train取得，未用原test或新验证数据调参。

真实S提供者已接入44视图选择接口；本轮节点价格仍为明确的软件夹具，不能作为正式D或PPA结论。默认qualified模式拒绝缺联合资格的价格，显式candidate模式也保持 `joint_qualified=false`、`full_D_ready=false`。

## 结果

- 两新银行×500／1500／3000ps，ABC=T，共6点／12 synth/grt阶段，状态FF分别491／812；6项真实CTS CEC通过，8类边界48/48覆盖，shared clock／physical／root repair／wire各6/6。
- 每源3目标的状态面积中位误差最高1.595%、P95最高8.139%，通过预先冻结的20%／50%门限。详细逐项数据见 [validation.json](validation.json)。
- 44视图×3T共132次实际S价格／控制／DAG／排序的Python独立重算通过，18项错误输入拒绝通过，见 [software-proof.json](software-proof.json)。
- 三份入选RTL各160周期算术／valid／复位检查通过，见 [cycle-proof.json](cycle-proof.json)。新银行另有各128周期、共5248项软件状态检查，准入绑定原proof哈希。
- 两个500ps点setup违约，银行0在500／1500ps的hold分别−0.153197／−0.224723ps；其余hold也均不足5ps review band。标签有效／S复用门限通过与物理可行分别报告。

旧S覆盖至64变量位；真实MAC32存在65／66／67位，故原拒绝后建立明确候选后继并纳入新银行验证，旧文件未改。250–3000ps为候选查询区间，本轮只验证其中3个T。实际算术相关状态保留、最终服务／输出边界、G的共享／wire情境及完整stage联合资格仍待。经验上界可较保守，不保证任意域覆盖，也不证明排序最优。

## 复核

`manifest.json` 绑定chunk、每个恢复成员和当前源码。压缩pool包含69文件：原S、binding／服务／proposal／admission／推导身份、新点观测、原生报告、独立proof、RTL／向量／仿真日志、完整物理归档恢复索引及当前实现快照。所有chunk不超过512KiB；单文件小于1MiB，小包总量小于5MiB。历史§7.62和旧S证据保持原字节。

在任意目录复制本包后，可用标准Python执行，不启动EDA／SAT或拟合：

```bash
python3 -B replay.py replay --evidence .
```

回放在临时目录实际恢复并逐hash核对69文件，执行包内冻结的纯Python验收器，重算六点结论及132视图状态／S／shared／控制／DAG／选择，检查仿真RTL／向量身份。它复核保存结果，不在回放中重新做物理测量或重新运行仿真。实际原始路径／归属的重提取收据保存在本轮support及完整产物中。

完整原始目录为 `/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3`，明确保留至用户清理；归档 `archives/S6-full-products-v1.tar.gz` 的1867成员已实际恢复、逐hash通过，逻辑592014657字节、压缩60716664字节，SHA256为 `484edae45c90cc0731f63a0903463e8f9edb18861409a61e7129d054403832ff`，原始产物未删除。这是保留的本地存储，同盘故障不在保证内。

原始测量身份绑定6点准入和冻结Python测量源；增强后的C++拒绝检查另经最终build／native／parity绑定源码，不重写初始proposal。确切费用见本目录后继 `resource-closure.json` 及其外层关闭叶命令；仅按本任务support准确reservation ID和物理admission `conditional-boundary-20261110-v3-S6`核对，后台算子采集继续运行，不能宣称全局账本结清。

含外层关闭叶的最终本任务费用为63项：6 synth、6 grt、51 support、0 final，叶墙钟619.152540s、CPU1125.12s，pending为0，3项失败保留。关闭叶reservation为 `aa14848d586945f18fc71a4bbe761781`，其最终收据在叶结束后作为记账元数据附入resource closure；压缩pool的科学内容和先前回放字节保持不变。最终源码／原S／后台93冻结文件及123本地链接核对通过，后台快照为397有效点、batch-034、locked_test未启动。
