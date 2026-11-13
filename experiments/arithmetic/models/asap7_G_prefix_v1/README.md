# ASAP7融合归约G：前缀面积后继v1

此包以通用位列／压缩／前缀几何和数值T计算融合归约区域的节点最大时延与独占组合面积。它替换区域内的Add价格；区域外S、连线与shared另计。DAG的串联／并行传播仍不增加额外G残差。

参数在独立测量前冻结，面积采用7项共享NNLS系数，时延复用此前固定函数。4个未参与拟合的源在1000／1250ps完成8次独立测量：时延源median／P95相对误差为4.13%／4.76%，面积为11.22%／19.62%，结构误拒绝0。16项Python／C++特征及同参数价格检查通过，模型没有根据独立结果改参或改支持规则。原冻结参数的字节保存在[parameters.json](parameters.json)，完整一次性结果见[independent.json](independent.json)。

边界要求是独立无符号位项、寄存器发起、一个直接capture银行，无额外消费者。T在连续500–3000ps内，并须同时满足数值结构支持；不能只看输出位宽。源码没有源、候选、精确形状或精确T价格索引。纯位连接应先按语义消简；宽归约、更多capture或其他发起边界尚不能自动继承本包资格。

```python
from experiments.arithmetic_dse import reduction_prefix_model as G

model = G.load("experiments/arithmetic/models/asap7_G_prefix_v1")
terms = [[(source, bit, bit) for bit in range(64)] for source in range(3)]
price = G.predict(model, 64, terms, 1373)
print(price)
```

加载器核对本地相对路径的参数、验收收据及特征源码摘要。预测不读取仓库外物理目录；JSON中的绝对历史路径仅作溯源。返回`covered`时，`operator_delay_ps`及`comb_area_um2`为该区域价格；不合格边界／数值域返回`cost_uncovered`。

这是G组件的限定发布。S控制、实际算术状态、完整阶段及候选排序仍需联合验收，`full_D_ready=false`；公共D和旧G包保持原绑定。新的4个G独立源已消费，不得重新分配为训练源。
