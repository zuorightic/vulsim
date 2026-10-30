# 修订计划步骤三：四平台接通证据

本目录仅验收 `mission/lxy-plan-fix.md` 第一章§3、§10.3 的后端接通：新增三平台的小加法/寄存器探针、四平台共同原始32×32→64乘法核的synth/grt/final、单位/PVT/资产/面积检查、失败和资源。当前实现以 `backend_freeze_v5.json` 绑定。所有物理结果为所声明TT/typical配置，`multi_corner_signoff=false`；没有训练D、制定正式案例ps目标或运行688条主矩阵。

`summary.json`保留所有尝试和已有阶段；`runs/`保存原始manifest、每次执行源码、ABC脚本、网表、时序/单元/覆盖报告、DRC指标和提取SPEF的压缩原件。`generated/`及`preparation.json`保存两个探针的VUL输入、生成结果和软件/原生10000周期验证。早期ASAP7尝试保留原哈希和证据，完整源码快照采用后续同配置ASAP7复核，避免把运行后的源码补写成运行时原件。

`admissions/`保留初始有限清单及全部显式修订。修订针对实际发现的解析/平台配置/源码追溯问题，使用新ID、父清单哈希、原因和继承的调用上限；自动重试为0，未改变任何探针周期。全局策略v5额度未增加，物理阶段均沿用共享账本、单任务、2线程、8GiB上限和原超时限制。`usage_before.json`和`usage_after.json`保留完整历史，`command_index.json`、`commands/`及`resources.json`逐条核对GNU time、状态、清理、平台与准入分账。旧记录没有被补写平台身份。

`unit_basis/`保存ABC单位归一化、OpenROAD面积汇总精度、ORFS默认RC/track解析、GF180技术LEF/原RC/PDN等依据。GF180本地适配从实际LEF的4.5Ω默认单孔补齐TC Via1–Via4的RC映射，并核对Liberty和STA均为1Ω单位；保留电源网格分析。Sky130HD共享的互连RCX文件按指定符号链接的目标和内容哈希单列。

`source_v5/`是本轮冻结的活动实现；`previous_source/`和`execution_source_pre_rcfix/`仅用于历史/执行过程审计。历史freeze及旧证据未覆写。旧九案例预算公式和ASAP7专用Make设置只在这些明确快照中保留，活动预算/后端使用修订实现。

从仓库根目录运行，无需build目录、EDA工具或网络：

```bash
python3 -m experiments.arithmetic_dse.platform_evidence
python3 -m experiments.arithmetic_dse.step2_evidence
python3 -m experiments.arithmetic_dse.placement_evidence
```

第一条重算本轮原始时序/单位、逐单元面积、网表/SPEF/DRC身份、准入谱系及累计资源；后两条核对原步骤二和历史区域/拆分/位置证据，旧结论仍只属于旧冻结。`--verify-external`额外核对本机原工具、库和流程文件哈希，默认离线验收不要求这些绝对路径存在。大型ODB和完整开发目录保留在build；便携核验不依赖它们。
