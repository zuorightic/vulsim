# 已撤回的固定RTL改时钟方案

本文件保存修订前字节，只供追溯。用户已指出其不能用于新目标下的D对比，执行记录及费用保留。

## 1.12 用户授权的失败实验宽松后继（2026-11-16）

用户明确要求“请记录要修复的问题，补进第一章的内容。失败的实验请放宽条件重跑”。本节授权范围覆盖本次冻结时已失败的19条BCD及6条同池归因，共25条旧方法记录；不续测已废弃的逐目标A，Montgomery27000ps新A继续独立运行。旧矩阵、原失败／费用及现有在运任务保持；新批次另登记，不覆盖原目标的失败，也不把变更时钟后的成功计为原目标达标。

### 1.12.1 条件、比较与执行步骤

1. 从已释放账本租约的失败run中读取既有synth／全局布局／resizer／详细布局／CTS的core-clock周期。按案例和L分组，以**主BCD失败**的最大中间周期与旧请求的最大值为基数，首档乘1.10、次档乘1.20，向上取整至50ps；同池静态归因随同评价，不决定BCD的新时钟。中间值只选择新请求，不冒充完整grt Tmin。
2. 新时钟下固定原相应档的RTL、拆分及寄存器位置，不用PPA重选D，也不把原T下的预测改写成新T预测；这是固定实现的失败恢复／容量评价，不是新目标下的D算法优化实验。每组补齐同请求的B／C／D及同池归因，A继续引用原请求和原实测参考。不同请求分表比较。
3. 每任务最多一次冷启动synth和一次完整grt：综合上限3600秒，grt由7200增至14400秒，support最多4×300秒；每工具2线程、共享原累计账本和9个槽位。Dot16的C／D／归因因已触及或接近8GiB峰值而使用16GiB，其他8GiB。无自动retry，不跳过合法化、CTS验证、时序覆盖或setup阈值夹逼。
4. 独立调度器在空槽及内存／存储足够时发射；领槽时仅短暂停旧父调度器以核对尚未领租约的子任务，立即恢复，EDA子进程不中止。原主队列继续运行。仅完成grt、setup±0.1ps固定DB夹逼、必要实际CTS证明及账本释放后发布有效读数，hold另外保留。
5. NTT L8的软件−11另作一次有限恢复：原失败日志和47/48候选缓存保留，改用64MiB栈（原8MiB）、16GiB地址空间、CPU4小时／墙钟6小时及faulthandler；不修改模型或选择算法。完成全部候选、回放、功能及ready收据后才由原控制器登记原1550／1850ps目标的BCD；若原控制器已自然退出，只恢复同一控制器及其原尝试账本，不重复已尝试任务。再失败则保留崩溃栈和退出状态，不循环重启。

| 案例 | L | 原请求 ps | 后继统一请求 ps | 方法 |
| --- | ---: | --- | --- | --- |
| Dot16 | 4 | 850／1050 | 2250／2450 | 各档B／C／D／同池归因 |
| Dot16 | 5 | 700／850 | 1950／2150 | 各档B／C／D／同池归因 |
| Barrett64 | 4 | 2150 | 2800 | B／C／D／同池归因 |
| Karatsuba256 | 4 | 2300／2750 | 4350／4750 | 各档B／C／D／同池归因 |
| Karatsuba256 | 8 | 1150／1400 | 2150／2300 | 各档B／C／D／同池归因 |

以上9组共27条BCD、9条同池归因，按RTL／T去重为34个物理任务；叶墙钟最坏包络654840秒、CPU包络1309680秒，已按原累计额度核对，历史费用不重置。A不增加后端调用。较宽时钟仅为恢复可完成的公平后端比较，原紧目标对拆分收益的测量及失败解释保留，不能用后继宽松目标宣称原目标已完成。

### 1.12.2 已启动身份与存储

代码入口为[workload_failure_relaxation.py](../experiments/arithmetic_dse/workload_failure_relaxation.py)，准入身份`workload-explicit-failure-relaxation-v2`，实际目录`/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/failure-successors/matrix-failure-relaxation-v2`。2026-11-16 23:00:26 +08:00已启动调度器及NTT软件恢复；首次ready核验时原9槽仍占满，34个新物理任务排队，不能把排队写成已经完成。19项针对时钟依据、冻结身份、进程内绑定、失败保留及控制器复用的相关回归通过。最新状态和完整时序依据见[后继结果表／机器状态](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/failure-relaxation-v1/README.md)。

为避免存储耗尽，按用户此前清理无用results的授权，只对已终结且租约已释放的run作可逆gzip。完成run的最终grt数据库、失败run的最近阶段数据库、全部报告／日志、网表／SDC及显式冻结输入保持直接可读；更早的中间ODB逐文件验证解压SHA后才移除原副本，其原字节仍可恢复。运行中与中止现场不动。恢复索引记录原路径／SHA／模式／mtime；截至23:12:40累计归档596个库、释放约44.38GiB、当时可用约48.31GiB，第二轮仍在继续，快照见[存储进度](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/failure-relaxation-v1/storage-progress.json)。

另已启动低CPU／I/O优先级、最多48小时的单实例存储维护，等待当前压缩锁释放后接续，仅处理上述已终结现场，不发射或重试EDA。65GiB是尽力维护的可用空间目标；新任务的发射检查门槛为14GiB，12GiB是保留目标，并非对在运任务后续增长的绝对保证。完整索引、恢复办法及维护启动收据见[运行与存储说明](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/failure-relaxation-v1/operational-notes.md)；项目内[索引副本](../experiments/arithmetic/evidence/workload_equivalent_steps678_tight_v2/two-depths/failure-relaxation-v1/storage-receipt.json)在每轮压缩完成时更新，实时逐文件索引以说明中的产物根路径为准。

本次启动只处理R6的实验失败恢复；R1a、R2～R5的模型特征和位置算法仍是待实施修复，不能因重跑启动就标为已经解决。

