# 进度、ABCD、后端耗时与未测RTL审计

快照：2026-11-16 18:07:23 +08:00。

[全部ABCD比较与已测逐项](abcd-comparison.md)；[后端命令／子阶段耗时](backend-timing.md)；[瓶颈归因与LEC内部耗时](backend-bottleneck-analysis.md)；[未测RTL的拆分和寄存器](unmeasured-rtl.md)。
当前队列只读，报告不改模型、选择、周期、RTL、准入或后端配置；未发射EDA或拟合。
[快照JSON](snapshot.json)、[验证收据](verification.json)、[生成脚本](generate-audit.py)。

收尾2026-11-16 18:18:39新增Horner L4/T1900的A实测，主记录达到56/148；[增量读数与原始来源](final-readout-update.md)单独保存，不覆盖18:07的耗时／RTL审计快照。
脚本可从仓库根用python3执行；再次执行会以新的时间点覆盖本目录报告，须另存旧目录才能比较快照。
