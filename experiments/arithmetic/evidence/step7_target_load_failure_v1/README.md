# ASAP7目标／负载区间模型的失败检查点

本包保留2026-11-04的实际一次性独立评价：grt41／42、synth38／42类通过，发布为空。唯一grt失败为`quarter/low/1/1`，20个标签均时延高估，中位误差34.2549%超过原30%门槛。面积和该类错误可行比例通过；没有放宽门槛或回调参数。

`quality-labels.json.gz`保存压缩后的训练／验证／测试数值标签、候选、冻结、验证报告、独立结果和空发布；`verify_quality.py`只用Python标准库，核验冻结文件的数值序列化哈希并独立重算每类指标、状态和发布决定。运行：

```bash
python3 experiments/arithmetic/evidence/step7_target_load_failure_v1/verify_quality.py
```

此小包的核验范围是标签与数值质量决定。完整原始SDC、Q→D、捕获银行、源快照和外部产物回放另存本机`build/step7-target-load-20261103/parallel-evidence-v1`，当前约134MB，未声明异机持久副本。完整便携回放覆盖603个run、1206份阶段／SDC和15708份Q→D／银行路径；external以归档代码及空PATH核验89547项完整原始产物。小包不能替代完整原始归档或从工具重新测量。

`checkpoint.json`记录原选择／结果哈希、失败类和大包身份；`m2-model-inventory.json`是九例的静态需求审计，不是合格模型或最终D选择。资源完整结算见同一工作目录中的后继封账，后续support审计继续记入共享账本。

现行优先交付为ASAP7 M2九例×A/B/C/D＝36条及其复现审计，见`mission/asap7-m2-closure.md`。本轮独立测试已消费并封存，不进入后续拟合、验证、算法或裕量选择；没有正式D模型发布，也没有据此开始36条物理评价。
