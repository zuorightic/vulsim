# ASAP7 G归约区域函数 v1

本包是G组合模型中的归约融合函数。小算子函数继续预测独立Mul／Add，S继续预测实际状态与边界；G发现并整体预测同级归约区域。区域时延和面积替换内部Add加总，区域之间按DAG传播，并重新计算依赖功能面积的shared项。

该函数使用位列几何和数值T计算价格。模型没有源、MAC、候选、placement、精确shape或精确T编号的系数／白名单；训练与验证数据也不作为在线价格表加载。

令C为进位跨度，H为最大活跃列高度，L为将H反复变换为`2*floor(H/3)+H%3`直到不超过2的层数，N为逐列压缩工作量。冻结函数为：

```
d_ps = 52.24865081504073 * log2(C+1)
     + 0.6799196156994592 * C
     + 80.92325616653225 * L
     + 32.12540022886656 * log2(T/500)

A_um2 = 0.2756333371018192 * N
      + 0.8170832778498687 * C
      + 0.018066565227793718 * (N+C) * 1500/T
```

两个截距均为0。N是D根据位分布计算的结构量，不能输入实测映射单元数；逐列扫描轮数单列诊断，不当作平衡压缩层数。完整精度系数和每个支持区间见`reduction.json`。

首版适用范围为无符号、同级、寄存器／服务输入发起、输入变量位无重复纯别名、单个实际capture银行的加法归约。移位／补零按真实位连接表示。内部截断后扩展必须证明不丢失会重新参与结果的进位，中间结果被其他消费者观察、同级Mul→Add耦合、非零常量和其他未覆盖语义保持原边界；已经判定融合而区域函数缺覆盖时，D明确报告`cost_uncovered`。

目标数值区间为500–3000ps，输出需求16–96位、3–17个live加数；最终支持是所有数值和语义条件的交集。宽度／加数范围不是逐宽度价格表，也不保证区间内任意位分布都自动被接收。区域内部使用规范化固定宽度求和RTL，允许联合综合，外部保留层次。Mul与未融合Add仍按原策略保层次。

Python调用示例：

```python
import json
from pathlib import Path
from experiments.arithmetic_dse.reduction_function_v2 import predict

model = json.loads(Path("experiments/arithmetic/models/asap7_G_reduction_v1/reduction.json").read_text())
# 每个三元组为[来源身份, 来源位, 输出列]；来源身份只作连接／重复检测。
geometry = [(24, 0), (21, 7), (16, 16), (12, 28), (48, 0)]
terms = [[[i, b, shift+b] for b in range(width)]
         for i, (width, shift) in enumerate(geometry)]
price = predict(model, 48, terms, 1000.0)
print(price["delay_ps"], price["area_um2"])
```

返回的是组合区域点预测，不包含FF、状态门、clock、setup、不确定度、外部连线或整级50ps预留。D通过真实S与区域DAG组合这些责任项；区域内部的节点价格／连线／逐节点reserve不再叠加。区域外额外G残差为0，经验reserve不声称严格上界。

训练、validation和独立评价均在对应标签读取前登记角色。36个训练请求来自12个结构源，12个validation请求来自另外4源，8个独立请求来自另4源，后者使用未用于拟合／选择的1000和1250ps。2个not_training探针只验证读取器；旧手写split16和ABCD最终PPA排除训练及独立职责。采集的RTL、FF银行、端口、Liberty实际弧、独占面积、SDC及CEC均留证，融合内部不强造独立Add标签。

训练误差median／P95：延迟2.8861%／9.8640%，面积7.9064%／21.3669%。最终validation／独立数值及冻结身份由发布收据和证据README给出。区域独立质量只授予本函数；整设计S／G联合、reset预测及完整签核不因此自动通过。

最终验收已通过：validation延迟median／P95=2.9514%／7.7886%、面积11.3145%／14.7280%；独立延迟4.1913%／11.2578%、面积8.4554%／15.6727%，全部请求均覆盖，参数／域未调。发布与候选唯一数值差异为资格状态及绑定验收收据。

新D公共入口见[后继依赖包](../asap7_fused_D_prototype_v1/README.md)，可搬移证据见[回放包](../../evidence/G_reduction_D_v1/README.md)。原始产物位于`/home/zyrv/vulsim-artifacts/G-reduction-20261112-v1`。
