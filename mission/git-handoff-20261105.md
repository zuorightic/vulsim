# 2026-11-05 ASAP7组件模型Git交接

本轮按原门槛发布12类grt组件，原F5失败保留。发布模型及可复核证据为`experiments/arithmetic/evidence/step7_m2_mux_static_v1/`，原始ODB／AIG／物理运行目录继续保存在ignored build，未把它们纳入Git。模型身份、支持域及下一轮接口工作见[lxy-plan-fix.md第四章§7.30](lxy-plan-fix.md#step7-m2-mux-static-independent-verdict)和[ASAP7 D端接口清单](asap7-d-interface.md)。

本轮由代理做工作树及证据核验，用户执行暂存、提交和推送；没有执行git add／commit／push。检查以cached或可见untracked的实际工作文件为准，尚未暂存的文件需要用户纳入本次提交。该局部交接不代替九例36条后的完整步骤九审计。

提交需处理两个仓库。`rtlzz`是子模块，其未提交C++源不会被主仓库直接收入：先在rtlzz仓库提交并保留可访问的提交，再在主仓库提交更新后的gitlink及Python／协议／计划／证据／账本。当前rtlzz修改包括`src/backend/arithmetic_model.cpp`及新增`src/backend/arithmetic_mux_context.hpp`、`testv2/arithmetic_m2_atom_export.cpp`、`testv2/arithmetic_mux_static_context.cpp`、`testv2/arithmetic_mux_static_predict.cpp`、`testv2/arithmetic_target_interval_test.cpp`。

主仓库本阶段的大文件主要是共享资源账本和带来源的压缩文本证据。这些用于保留历史失败、付费、原始报告及可复算结论，应随相应源代码／配置保留；本次不删减其字节或改写旧索引以减小提交。原F5、原基础／区间失败及Mux验证失败包均是当前父链，不能只提交最终passed模型而遗漏来源。

暂存前后可检查：

```bash
git -C rtlzz status --short
git -C rtlzz diff --stat
git status --short
git diff --stat
git diff --cached --stat
```

工作树大于5MiB的文本／压缩证据不等于误提交产物；重点排除build、ODB、AIG、目标文件、可执行文件、波形、缓存和运行lock。本轮审计收据保存于发布目录的`verification.json`，Git体积快照为`build/step7-m2-models-20261105/git-delivery-audit-v1.json`；Git对象体积与可提交工作文件体积分开统计，不能据工作树字节数推定push增量或最终pack大小。

便携回放入口：

```bash
python3 -m experiments.arithmetic_dse.model_m2_mux_static_evidence verify --folder experiments/arithmetic/evidence/step7_m2_mux_static_v1
```

本机完整原始回放在上述命令末尾增加`--external`；两个模式均不启动EDA、SAT或重新拟合。独立P4已消费，永久排除后续拟合、验证和参数／裕量／域选择。当前后台全部退出，无新实验自动启动；下一轮先做生产接口，再按真实九例缺口补资格。

本轮已完成Git可见工作文件副本核验：禁止读取原build、工具目录和活账本，PATH为空，便携回放仍通过；压缩池字节篡改被拒绝。主仓库与rtlzz的diff --check通过。审计时主仓库.git磁盘占用约61MiB，其中主仓库已有pack为45.58MiB、松散对象9.51MiB；可见主工作文件约255.83MiB，本阶段已改／未跟踪文件约119.87MiB；新Mux证据约41.51MiB，rtlzz可见源文件约3.00MiB。这些是工作文件快照，不是已生成的Git包或push增量；最终sidecar／交接文本会有小幅追加。未发现Git可见的build／ODB／AIG／对象文件／波形／缓存／lock。最大单文件为共享账本，约15.44MiB；新Mux索引约9.91MiB、原F5索引约8.42MiB，均为有用途的文本来源与结算证据，保留。
