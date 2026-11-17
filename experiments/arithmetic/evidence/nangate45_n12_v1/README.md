# Nangate45：冻结D迁移的N1＋N2

2026-11-17完成。范围是MAC32 L2／L3、Add512 L2／L4、Mul128 L2／L4；N3～N8尚未执行。本目录只保存本说明及[小型JSON摘要](summary.json)，完整产物在`/home/zyrv/vulsim-artifacts/nangate45-n12-20261117-v1/`。未将数据库、日志、二进制、需求全集或模型测试夹具加入Git。

实际D编译器SHA256为`a44b9b6d8f664894bac1c6c5ad9d872d9cdb3be865bf922d0641e64a74bd12c1`，完整诊断模型SHA256为`de067c6983fe92eb7b5771b014f7881483bc2be06a5f70eddd3bc521208bc575`，组件模型仍为`a1466f0272b55bd20358ea9e3beb84844db8fe8fefe4152e0478224d8f13243d`。先核对在运父合同496份文件，再冻结实际编译器、源、配置与迁移入口等770份文件，快照83,715,502字节；需求输入1056份另行绑定。原选择器、预算／反解、候选语法、位置策略、排序及全局ABC策略保持，R1～R5继续暂缓。

需求来自原生静态候选、已有模型压力位置及MAC32第4～5步有限池，去重以RTL和位置为准。这里记录三例实际需要的共享模型和边界，需求描述本身没有实测价格。

| 案例 | L | 前瞻实现 | 原状态位范围 | 观察到的最多活跃算术／G级 |
| --- | ---: | ---: | ---: | ---: |
| MAC32 | 2 | 14 | 130～834 | 2 |
| MAC32 | 3 | 76 | 195～2147 | 3 |
| Add512 | 2 | 24 | 1028～1532 | 2 |
| Add512 | 4 | 44 | 2056～3589 | 4 |
| Mul128 | 2 | 20 | 514～69378 | 2 |
| Mul128 | 4 | 51 | 1028～113412 | 4 |

完整需求保留操作数／结果位、已知位、carry、capture、消费者、G项列与相关性、状态、首／中／末边界及每候选的算术空级。跨L合并为Mul385、Add325、ADC201、G645种描述，只用于选择少量代表采样源，不能逐描述建立价格表。Mul包括4／8／12／16／32／64／128位及不等宽尾块；G存在高达1024项的候选。保留这些语法，不为容易拟合而暗中删除候选或修复算法。后续共享函数只覆盖通过验证的需求；未知仍报缺价。新模型可能产生新压力位置，N5～N7必须重提实际查询，当前候选并集不宣称覆盖全部未来位置。

后端依赖审计见摘要的`dependency_audit`，外部完整文件是`migration-audit.json`：

| 部分 | 本轮处理及后续责任 |
| --- | --- |
| 图／位语义、G所有权、静态表、有限搜索、预算／反解／排序 | 复用冻结实现；不修改在运文件 |
| 原生工作负载导出器及C++ provider写死的ASAP7身份 | 用原二进制和空价格模型导出，在独立产物中显式重绑前瞻查询；原导出身份、graph／state／RTL哈希另存；空价报告明确缺价 |
| 完整Python模型、采样合同、逻辑单元面积 | 新平台包分别绑定文件哈希、profile及grt；旧入口保留 |
| Mul、Add／ADC、G的响应系数与负载／消费者效应 | N3配对采样，N4按证据缩放、校准或重拟合共享函数 |
| S／shared、H_char、wire／boundary／reserve、静态归因桥 | N5～N6按本后端及首中末级合同检查；不照搬ASAP7数值 |
| 10ps／0.04374µm²数值下限与ASAP7逻辑单元面积表 | 明确列为平台参数；新包须提供完整面积绑定。当前六类需求中功能逻辑所有者为0，但Add特征仍消费逻辑cover |
| 历史Nangate45局部模型 | 仅作历史诊断资产，不能视为本次完整D模型 |

新增入口位于[workload_platform_entry.py](../../../arithmetic_dse/workload_platform_entry.py)，只加载离线冻结函数及合同，不拟合模型或执行后端。正式[Nangate45配置](../../../arithmetic_dse/configs/nangate45_frozen_d_v1.json)保持`pending_N3_N6_offline_calibration`，消费时明确拒绝。测试中临时使用“ASAP7原数值＋Nangate45身份”的夹具，只验证平台传递、完整预算与身份拒绝；它没有获得本后端价格、模型精度或应用发射资格。

软件检查已通过：

- 六种案例／L各取一份真实所选D，旧入口与新入口的完整评分逐项相等；重算其完整预算、等效T、S／G及完整路径，与原冻结所选预测一致。
- 旧矩阵13组、327个候选的冻结完整预测重新排序，赢家相同。这里的13组是ASAP7旧回归数据，Nangate45仍计划12组；没有重新数值评分全部327个候选。
- 模型消费期间禁用`subprocess.Popen`及文件I/O仍通过；查询只用内存模型和图／状态。错误平台包、owner profile、采样合同profile、查询平台、响应hash及未就绪模型均拒绝。
- 新入口实际导出六种案例／L，各以一个拆分结构验证平台绑定；每份192周期RTL整数结果、周期、reset和停顿协议仿真通过。这些是入口测试，非N7正式D。

有限物理接通先导使用Nangate45 TC、1.1V、25°C，SDC与ABC均为3000ps，2线程／2GiB，串行到post-CTS global route。三个源均为寄存器launch／capture，数学分别是33位全精度加法、64位全精度乘法和16位回绕乘加。

| 探针 | grt面积 µm² | setup最坏松弛 ps | hold最坏松弛 ps | 覆盖 |
| --- | ---: | ---: | ---: | --- |
| Add32 | 1131.032 | 2106.162 | 0.091 | 完整 |
| Mul32 | 7327.236 | 1149.277 | 0.662 | 完整 |
| MAC8 | 844.816 | 1987.165 | 11.173 | 完整 |

实际Liberty及报告单位是ns／fF，转换为ps的因子1000；序列化SDC中的周期3ns、不确定度0.02／0.005ns、跃迁0.01ns、BUF_X1/Z和3.898fF负载均核验通过。库、工具、LEF、setRC及RCX规则哈希存于实际manifest和摘要。Add32、Mul32的hold低于5ps复核带，保留`recheck_required`，没有宣称最终布线或多角签核。各探针另通过256组整数／溢出／reset向量仿真。

这些读数证明后端接通，不能推导完整RR／IR／RO最小时钟，也不能证明后端影响线性、共享模型精度或D优于C。三个探针不算N7的A／BCD，不进入本轮训练标签。

物理叶及功能验证支持叶共用原累计账本，新增3次综合、3次grt、10次支持调用，叶墙钟122.376814秒、实际CPU148.45秒，全部结清，四个任务槽租约均已释放。未迁移／清零账本，未改策略，未停止或修改ASAP7任务。启动探针时至少留出2GiB任务额度及额外8GiB可用内存；全局仍为9槽。物理manifest保留工具线程、RSS、超时、GNU time与清理收据；费用快照另记录当时三个仍活跃的ASAP7任务，后续状态由其原控制器管理。

外部主要文件如下，SHA256均在`summary.json.external_evidence`中：

| 文件 | 内容 |
| --- | --- |
| `baseline.json`、`snapshot/` | 实际源码／二进制／模型依赖冻结及副本 |
| `demand.json.gz`、`demand-summary.json` | 全部前瞻查询、状态／逐级边界、1056份源哈希及摘要 |
| `migration-audit.json` | 可复用算法、平台绑定及需采样／校准项 |
| `software-check/software-check.json` | 六份完整回放、13组排序、六种拒绝及原生导出收据 |
| `connection/admission.json`、`connection/runs/*/manifest.json` | 三个具名一次性先导及完整工具／库／RC／SDC证据 |
| `functional/receipt.json`、`functional-accounting/` | 九份RTL仿真及支持叶结清 |
| `accounting-receipt.json` | 本轮费用、共享账本身份、释放租约及ASAP7活跃任务观测 |

本机只读核验：

```bash
python3 -B -m experiments.arithmetic_dse.nangate45_migration \
  --out /home/zyrv/vulsim-artifacts/nangate45-n12-20261117-v1 verify
```

它核对770份冻结文件和副本、需求包与1056份需求输入，不启动EDA或写账本。软件检查可在新的外部目录运行`python3 -B -m experiments.arithmetic_dse.nangate45_entry_check --out NEW_EXTERNAL_DIRECTORY`；会重新数值回放并做纯软件原生导出。连接探针是具名一次性任务，**不要重新发射已完成任务**；有新实验需求时另冻结批次并共享原账本。本轮准备阶段曾发现待迁移的v12 checkpoint尚未生成，在任何EDA叶发射前修正为实际在运桥接身份；初次不完整候选清单也保留在外部`initial-incomplete-*`，交付使用补齐原始池后的版本。
