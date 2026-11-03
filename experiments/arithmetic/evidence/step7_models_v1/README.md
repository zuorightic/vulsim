# 步骤七：局部 grt 模型检查点 v1

本包是四平台离线训练的阶段检查点，**步骤七未完成**。`models/` 中四份 JSON 是可用于已声明局部域的真实拟合模型。不得将本包当作完整 original/half/quarter 联合选择、五档整数、商余、binary32 或 688 条主矩阵的验收。

模型包括动态等宽 Mul（完整／低位）、Add、动态 AddCarry 的局部操作模型、单算子阶段／有限 Mul-Add 树修正及状态／边界模型。ABC 固定为 ASAP7 1500 ps、Nangate45 3000 ps、Sky130HD／GF180 30000 ps；SDC 的已验证目标域为各自 R..1.5R。具体宽度／结果形状／扇出／图约束以模型中的联合域及原生 provider 为准，不能由数值最小最大值推导额外支持域。异宽乘加、已知位模式、常量／相关操作数、多个数据输出、任意接线或 DAG 均不能自动继承覆盖。

孤立操作 v2 的 24 个独立测试 scope 通过。v6 阶段模型四平台 grt 通过原门槛；Sky130HD synth 独立 delay P95 失败，完整 v6 包保持 failed，此处只发布已通过的 grt。12 个单银行／目标上下文使用冻结系数测试，不回填训练；原失败模型及费用继续保留。`model_state_bits` 表示尚未被证明为常量的保存位，不保证综合不会继续裁剪或合并。

原生验证使用实际模型，包含 C++／Python 推理、公开 source→调度→RTL、独立成本／排序重算及周期 scoreboard。AddCarry8 的正式 D 路径只有一个结构；Mul8 的原始实现可用，但 half／quarter 尚未覆盖，因此仍是诊断性子集选择，`formal_D_selection=false`。完整 VUL MulProbe 暴露 AND 尚未覆盖，失败如实保留，不回退 C。

`text-*.json.gz` 为按 SHA256 去重的原始 UTF-8 字节池。索引保留完整模型、关键数据集、质量报告、原生报告／RTL，以及与训练收据一致的 8 份 v6 训练源码／配置。默认便携核验重算这些数据集上的质量指标及原生成本，**不声称读取全部阶段原始文件**。完整 manifest／SDC／路径点／实例列表和报告位于本机 ignored 全文归档，`--verify-external` 才逐成员重算；ODB 等大产物另有本机目录清单。远端持久留存尚未确认。

模板区间追加证据包含38份实际typed图、402个区间、3216项逐项RTL观测、6432项裁剪前后整数对照，以及四平台TEST_ONLY三候选报告／价格。默认核验重算位映射、静态特征、观测值和原生成本／排序；external另回读新增区间原始测量的SDC、路径点、唯一core面积和实际DFF数量。最初5个v1探针继续排除拟合；当前仅有2个v2训练bundle、24行阶段标签，无独立测试数据。

当前仍是未发布候选，核验命令为：

```sh
python3 -m experiments.arithmetic_dse.model_evidence --freeze build/step7-models-20261102/candidate-offline-model-freeze-v1.json
```

本机完整核验追加`--verify-external`。候选缺失时必须先完成明确的打包／结算／seal，不能把裸命令失败解释成已通过。将来的正式入口使用`experiments/arithmetic/offline_model_freeze_v1.json`，当前尚未发布；候选保持`full_step7_complete=false`。历史冻结和测量原始文件均不覆写。
