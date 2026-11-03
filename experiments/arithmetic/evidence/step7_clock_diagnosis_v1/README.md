# ASAP7 区间时钟压力诊断

本包记录已完成的24个预登记实现点：四个独立单核参考、12个固定映射的SDC变体、八个固定SDC的ABC变体，共48份synth／grt标签。它是离线采样设计的诊断证据，所有点均为not_training；不证明拟合模型通过，也不证明第一轮独立测试失败的因果来源。

实验保持ASAP7库／物理profile、两线程、边界壳和单捕获银行一致，I/O最大延迟固定300ps。四个参考在ABC=SDC=1500ps下测得并一次冻结；SDC点由`ceil(H_ref+k*D_ref)`生成，k为0.8／1／1.5；ABC点由`ceil(a*D_ref)`生成，a为0.8／1.5，SDC固定`ceil(H_ref+D_ref)`。SDC变体复用原始映射网表的精确字节，重新生成SDC／ODB并运行floorplan到grt；未复用旧物理结果。数值比率是探测点，不是通用“饱和／修复／极端”分界。

| 结构区间 | 参考Q→D（ps） | 偏紧SDC（ps） | 偏紧Q→D（ps） | 时延变化 | 组合面积变化 |
| --- | ---: | ---: | ---: | ---: | ---: |
| W16 half/full/0/0 | 647.677 | 611 | 552.949 | −14.63% | +15.65% |
| W16 quarter/full/1/3 | 531.395 | 513 | 422.011 | −20.58% | +6.39% |
| W32 quarter/full/0/0 | 759.168 | 700 | 611.663 | −19.43% | +4.32% |
| W32 quarter/low/1/4 | 619.455 | 588 | 552.322 | −10.84% | +6.87% |

四个结构的ABC变体均与同一SDC下ABC=1500ps对照保持相同的规范化映射网表和结果。实际日志记录了目标传递及部分映射片段未触发upsizing；例如W16 half的核心ABC片段约195ps，低于519ps目标。因此不能把完整STA的Q→D当作ABC片段自身的临界目标，也不能据本轮未见响应删除ABC身份轴。

24个实现点中有四点局部区间setup满足而整图setup违约，均出现在W16 quarter/full/1/3的固定300ps I/O条件下。619ps例的区间裕量+17.268ps，输出到io_clk路径−78.631ps。固定300ps诊断不能自动成为正式`I/O=0.2*T`条件的资格验证。偏紧目标下工具成功、时序违约的结果全部保留。

一次实际尝试在synth之后因SDC序列化校验失败而停止：名义1021ps被OpenSTA写成1020.9999ps。源码核查和单精度重算得到其内部秒值`1.0209999512511558e-9`，输出换算值`1020.9999389648438`。后继准入显式使用与名义周期对应同一内部秒值的请求表示，不修改SDC校验器、不放宽误差或质量门槛。原失败目录、manifest和费用保留；此前21个完成点继承，后继仅运行三个剩余点。因此共有25次synth阶段调用（其中12次SDC扫描仅重建综合ODB／SDC、复用映射，另有一次同类失败尝试）和24次grt调用；不能把所有synth调用写成25次重新ABC映射。

文件包括：

- `response.json`／`response.csv`：完整48行实测值和逐轴比较。
- `response.png`／`response.svg`：参考归一化后的实测响应，连线仅连接实测点。
- `raw-text.json.gz`／`index.json`：782项去重原始文本、源快照及身份，压缩池4,239,505字节；完整日志／ODB等大产物保留在本机build的索引路径。

核验命令：

```sh
python3 -B -m experiments.arithmetic_dse.model_clock_evidence verify --out experiments/arithmetic/evidence/step7_clock_diagnosis_v1
```

实际Git可纳入文件的副本在无根build、PATH为空时通过24个run／48份实际SDC／48份Q→D及面积回放；重新计算归档哈希后的伪造Q→D也被原始报告重算拒绝。收据：`build/step7-clock-20261103/delivery-check-v1.json`。相关准入／数值表示／原后端回归59项通过。统计收据见`build/step7-clock-20261103/observations-v1.json`；其结算前缀为本诊断25 synth／24 grt／83 support、墙钟1240.670s、CPU1705.08s，后续归档核验继续计入共享实时账本。

下一轮设计见`experiments/arithmetic_dse/configs/model_mul_interval_target_load_draft_v2.json`：固定ABC=1500ps，按正式I/O策略采集SDC与真实负载上下文；比较简单基线和目标条件模型，以验证表现决定复杂度。具体目标表、分组和容量准入尚未形成，不启动旧固定R负载批量或688条主矩阵。
