# Nangate45 N3＋N4：小批配对采样与共享函数

本轮只处理 MAC32、Add512、Mul128 所需的小算术与少量归约源。N3 的有限采样、N4 的函数拟合／验证选择／参数冻结／封存测试均已执行；完整 D 包仍待 N5／N6 的 S、shared、G 嵌入、H_char 与采样合同。正式配置继续保持 pending。

20 个逻辑源包括 Mul 6 个、Add／ADC 10 个、G 4 个，每源 SDC＝ABC＝500／1500／3000ps，共 60 个 Nangate45 grt 点，与 60 个已有 ASAP7 点逐一配对。原始 RTL 在三时钟及两平台间逐字节相同；没有新增 ASAP7 后端调用。全部源均来自历史 ASAP7 train，迁移批次按完整local-context源ID将两平台副本共同分为 11 train／4 validation／5 test，同一源ID的时钟不跨职责。新后端 test 只证明留出标签上的迁移表现，不能称为 ASAP7 模型未见结构的独立泛化，原锁定独立源未读。

**2026-11-17分组勘误：** 此前“负载变体不跨职责”的表述不准确。validation的`wide-f826704868db02bf`与test的`wide-d842786f167bb36d`使用相同ADC128／carry=one producer，分别是单bank、双bank负载；实际跨了职责。原始数据、参数和下表数值保留，相应独立性降低。三档补采后继按producer语义归并负载／时钟变体；本批test只作已消费开发回归，不进入后继训练或选择。后继记录见[现行规划§1.6.3](../../../../mission/lxy-plan-fix.md#nangate45-pressure-refit)。

测量标签是独占 producer 的内部最大延迟与组合面积。完整引脚／输出／所有权、CTS 全状态边界等价与 D／clock／top 负控、1000 倍 ns→ps 换算、同路径数据读数和完整面积守恒均有收据。虚拟采样 FF、控制、clock、tap、observer 面积不混入算术组合面积。

Nangate45 的小 shell 不满足默认电源条带最小宽度，因此本批统一采用 `core_side=max(60,ceil(sqrt(synth_area/0.4)))` µm 的正方形 core 和原 5µm margin。除最小 core 外保持 40% 规则，实际 DIE／CORE 及清空自动 CORE_UTILIZATION 的命令保留。S／shared、边界及应用嵌入仍需 N5／N6 验证这一采样差异。接通阶段的 PDN、floorplan 设置、CLK／CK 负控及 tap 分类失败原样保留；沿用已付费综合、post-repair 或 grt checkpoint，未清零／退款费用，也未将失败点当训练标签。

模型依次比较全局比例、类型比例、类型仿射和共享 log 特征 ridge。时延与面积分别选择；请求轴比例仅从预登记的 0.5／1／2 选择，ridge 只取 0.1／1／10。训练源发现宽加法的面积请求响应后，在任何新后端验证／测试标签采集前封存统一的 `log(1+width)*log(T/1500)` 特征；没有精确形状／时钟／案例价格。参数只拟合 train，形式只根据 validation 选择；随后锁定参数再采集／打开 test，测试未回流。时间轴比例只是数值校准参数；本批只有三档同数值 T 的配对测量，不能据此宣称后端固有速度比例或采样边界相同。

统计先取每源各时钟 APE 的 median，再继承原合同的最近秩 source-macro median 与 P95；门槛为 15%／35%，同时保留最大逐源 median≤35% 的保护项。原提案中的插值分位数在验证／测试前通过独立合同修正；没有放宽门槛。

| 共享类型 | 指标 | 冻结形式／时间轴比例 | 验证 median／P95 | 测试 median／P95 | 验证／测试门槛 |
| --- | --- | --- | --- | --- | --- |
| Mul | delay_ps | global_scale / 2 | 2.21% / 2.21% | 4.99% / 7.42% | 通过／通过 |
| Mul | area_um2 | global_scale / 1 | 1.05% / 1.05% | 3.56% / 7.62% | 通过／通过 |
| Add | delay_ps | family_affine / 2 | 9.20% / 16.02% | 15.15% / 16.71% | 通过／未通过 |
| Add | area_um2 | shared_log_feature_ridge / 2 | 7.97% / 9.40% | 9.35% / 17.63% | 通过／通过 |
| G | delay_ps | global_scale / 0.5 | 16.60% / 16.60% | 8.69% / 8.69% | 未通过／通过 |
| G | area_um2 | global_scale / 2 | 3.48% / 3.48% | 4.12% / 4.12% | 通过／通过 |

测试样本数量较少，所有误差以这里的有限源为界；未覆盖的截断、mask、负载组合和大型 G 继续视为外推，G 成员仍只能由整个归约所有者计价一次。实测对实测缩放与旧函数预测迁移分别列在 [summary.json](summary.json)，不能把旧函数自身误差算作后端比例误差。

仓库只保存小型参数、摘要和代码。[model.json](model.json) 引用已有 ASAP7 响应的 SHA256；加载时校验平台、profile、stage 与引用哈希，数值推理阶段不读取文件、不启动子进程。宽度 12×20、未采样的 1700ps、未知 source／case／instance 元数据及全 120 个冻结预测均有软件复核；平台、profile、阶段、ABC 请求等错配拒绝。插值软件测试不授予该宽度实测资格。

完整 RTL、映射、ODB、报告、Liberty 引脚、路径、训练／验证选择／封存测试和累计账本收据均位于仓库外，路径和哈希见摘要。ASAP7 的现行控制器、已冻结模型、输入和安装均未修改；N1 的 770 个基线文件与 1056 个需求文件再次核对一致。未执行 R1～R5，也未启动三例应用 A／BCD 主表。

实测对实测的 train 全局倍率为时延 **1.299043**、面积 **13.973255**，各类型 validation／test 的源聚合门槛均通过，支持本批范围内的近似比例复用。[linearity.json](linearity.json)用报告已有系数补齐各职责统计，没有新增拟合或改变函数。训练 G 面积的 P95 为 40.94%，Add 面积测试单点最大 37.35%，因此不能将该结果推广为全域／逐时钟严格线性，也不能把基于 ASAP7 实测值的倍率直接当作编译器价格。编译器仍需要上述离线函数，不能用配对实测价格表替代。

按函数实际预测，Add 时延的测试 median **15.15%** 超过 15% 门槛，G 时延的验证 median **16.60%** 也未通过；测试通过不覆盖旧验证失败。Add 面积虽按源聚合通过，Add512／500ps 单点预测 21513.272µm²、实测 13854.876µm²，误差 **+55.28%**，继续作为异常保留。[qualification.json](qualification.json)明确区分验证、测试及完整 D 资格；所有数值查询保持 `qualified=False`、`full_D_ready=False`。测试没有回流调参。

最终软件验证通过：120 条冻结预测与便携函数一致，加上未采样请求／形状和零价语义，共 124 次禁用文件 I/O 及子进程的数值检查；六类身份／请求负控通过。[provenance.json](provenance.json)补充选模规则、特征／统计封存、实现快照及接通失败历史的审计索引。参数冻结早于首次 test 工具预约，所有修订早于首次 validation 工具预约。`finish-status.json`中的 guard 停止是事先安排的规则交接；本批有效状态是外部 `completion-status.json` 的 `completed`。

本轮使用单个串行 worker、每工具 2 线程／4GiB、启动需至少 12GiB 可用内存，并共享原累计账本与九槽内核锁。含接通失败，共 60 次综合、64 次 grt（60 次成功、4 次失败）及 436 次 support；叶墙钟 7065.715 秒、CPU 9941.20 秒。费用全部结清，自有槽位全部释放，没有重置／退款历史费用。60 个有效点中，23 点 setup 目标未满足、2 点 hold 负值、50 点处于 hold 复核带；这些测量状态与算术标签资格分别保存，不授予完整时序签核。

只读核验冻结输入，不启动 EDA 或改写结果：

```bash
python3 -B -m experiments.arithmetic_dse.nangate45_samples verify \
  --root /home/zyrv/vulsim-artifacts/nangate45-n34-20261117-v9
```

后续仍限定 MAC32 L2／L3、Add512 与 Mul128 L2／L4。N5／N6需验证 S／shared、G 嵌入、H_char、逻辑单元面积及完整 D 请求合同；本批未通过项继续保留，必要的模型后继须另冻数据职责，不能把本次 test 重新用作训练或选模。
