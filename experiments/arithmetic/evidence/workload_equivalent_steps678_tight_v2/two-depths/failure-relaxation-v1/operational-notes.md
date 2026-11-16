> 2026-11-17纠正：本变时钟批次已撤回并停止。当前有效入口为[原时钟资源后继](../failure-resource-only-v1/README.md)。NTT恢复于23:40再次−11，未ready；下文首次启动快照仅供追溯。存储维护与恢复索引继续有效。

# 失败重测的运行与存储说明

宽松后继已于2026-11-16 23:00:26 +08:00启动，身份为`workload-explicit-failure-relaxation-v2`。每任务只允许一次；自动重试为0。[结果表](README.md)与[机器结果](results.json)由控制器刷新。原主矩阵、原失败、原请求下的预测及费用独立保留。本批固定原RTL／寄存器位置，没有修复或重选D。

首次运行核验时原9个物理槽仍占满，34个新任务排队。NTT L8的软件恢复已实际运行，原47份候选缓存保留。日志中的`Timeout (0:10:00)!`是faulthandler每600秒打印的诊断栈，并非六小时墙钟限额已到或进程已经失败；成功仍须全部评分、回放、功能及ready收据。实际退出或超限由控制器记录，不凭日志尾部判断完成。

产物根为`/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1`。后继动态状态分别在：

- `failure-successors/matrix-failure-relaxation-v2/controller-progress.json`
- `failure-successors/matrix-failure-relaxation-v2/ntt-software-result.json`
- `failure-successors/matrix-failure-relaxation-v2/ntt-software.log`

磁盘维护沿用用户此前清理无用后端results的授权，采用可逆压缩，保留原ODB字节。只处理`measurement-outcome.status`为`completed`或`failed`且账本租约已`released`的run；运行中与中止run不处理。完成run保留最终`5_1_grt.odb`直接可读；失败run保留最先进／最近阶段DB直接可读。所有报告、失败日志、网表、SDC与显式冻结输入保持直接可读。

较早、已被后续阶段取代的中间ODB压缩为相邻`.odb.gz`。每个文件均完成原SHA、gzip解压SHA、源文件未变与run仍已释放核验，并先发布恢复索引，再移除冗余原副本。索引记录原路径、原SHA、gzip SHA、原字节数、模式与mtime；不能将归档数量当作删除失败证据的数量。回放早期阶段时，先用`gunzip -k`恢复相应索引项，再核验其`original_sha256`；需恢复原模式和mtime时按索引记录设置。普通最终读数核验仍可直接使用最终DB。

实时恢复索引为产物根下`storage-successors/completed-intermediates-v1/receipt.json`，逐文件原子更新；[项目内索引副本](storage-receipt.json)在每轮完成时同步。[存储快照](storage-progress.json)记录2026-11-16 23:12:40的596个库、累计释放44.38GiB及可用48.31GiB，第二轮当时仍在执行，后续空间随实验运行变化。

[存储维护启动收据](storage-keeper-launch.json)记录低CPU／I/O优先级的单实例维护进程：等待当前一次压缩的锁，接续维护最多172800秒（48小时），每30秒检查；当新后继已结清且全局无活动任务时可提前退出。尽力将可用空间维护至65GiB，候选不足时不处理在运现场，也不扩大归档范围。该进程不发射／重试EDA。14GiB是新后继的发射检查门槛，12GiB是保留目标，不能保证在运任务继续增长时空间始终高于此值。

维护代码为[pack_completed_intermediates.py](pack_completed_intermediates.py)，启动后SHA固定在上述收据。任务调度器、原runtime、模型、选择与准入均未因磁盘维护修改。
