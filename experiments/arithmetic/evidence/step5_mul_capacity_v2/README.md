# ASAP7指定双128位C实现：单次3600秒容量复测

本包是原`asap7-mul128-C-capacity-v1`1200秒超时的后继证据。新任务`asap7-mul128-C-postsynth-grt-3600-v1`只复用已核验的4份综合产物，完整新执行floorplan→place→CTS→grt；未执行synth或final，也未增加original对照。准入、任务、费用独立，旧失败保持不变。

RTL为相同双128×128→256、quarter/quarter（32位块）、L=3、II=1、valid/reset；平台ASAP7 RVT/TT、0.7V/25°C，SDC与ABC目标1500ps，2线程、8192MiB。工具、物理脚本、库及约束身份与原运行一致。资源上限3600墙钟秒／7200 CPU秒，support另外预留。

新完整链路墙钟1450.193215秒、GNU time实际CPU2489.33秒，采样进程树峰值2931364KiB，无超时／内存越限及遗留后代。`5_1_grt`本身按工具footer为1021.23墙钟秒／1948.68 CPU秒；完整链路包含新floorplan、布局、CTS及Make开销，不是将旧前置阶段时间拼接而成。各子阶段见`timing.json`及实际`stage_logs/`，footer为工具的舍入值，不代替收费叶命令。

grt面积17679.31434µm²、setup+0.278111ps、hold+7.473827ps、时序覆盖完整，TT setup和hold在本次配置下均满足。setup裕量很窄；未做重复、final、SPEF或多角签核，不声称稳定裕量或原始／拆分PPA收益。

**容量完成、当前目标时序和批次准入分开判定。** 本次关闭这个具体实现“3600秒内是否能完成”的未知项；批次仍须按平台／算子模板／实际结构或已论证容量域／规模／阶段复审并预留资源，不自动授权任何采样或主矩阵。单探针不代表ASAP7的32条128位规划记录，也不代表全平台128条。规模与拆分耗时的归因尚未完成，必要的同条件配对诊断另行准入。

`manifest.json.gz`、实际SDC、单元／单位／路径／覆盖报告、时序／面积和日志均可在仓库小证据中重算。完整生成运行目录（含ODB、网表、完整工具日志、渲染脚本与运行源码快照）存放在本机ignored artifact_store，`artifact_catalog.json`逐成员列实际大小/hash和取得位置，不复制整套PDK。默认便携核验不承诺取得大产物；完整核验必须实际读取其字节，远程持久保留未确认。

后继冻结见[mul_templates_freeze_v2.json](../../mul_templates_freeze_v2.json)，软件／资源增量见[收尾v2](../step5_mul_closure_v2/README.md)，实际记录见[规划第四章§5.8](../../../../mission/lxy-plan-fix.md#step5-closure-review)。原[容量v1](../step5_mul_capacity_v1/README.md)与所有费用保持原字节。
