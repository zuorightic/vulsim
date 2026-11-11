# 共享通用函数：兼容服务结构拟合与新validation

对应[规划§7.75](../../../../mission/lxy-plan-fix.md#step67-shared-function-fitting)。本包拟合shared clock、shared physical、root repair的独占面积；复用已发布小算子函数和S三所有者功能面积，G保持0，原S边界与50ps整级预留不变。

24个train点来自8个参数源×500／1500／3000ps；9个validation点来自三个全新源（20位三乘并行、28位归约、24位串联）×同三档。参数与实现身份先冻结，再进行新validation物理采集。原6项闲置输入FF失败、300秒Boolean读取超时、首次浮点支持边界不一致、资格脚本见证路径错误及归档／恢复包装器失败均保留收费。旧成功点不重测，修复源使用新内容／身份，角色不重分配。

| validation项目 | median误差 | P95误差 | 门槛 |
| --- | ---: | ---: | --- |
| shared clock | 4.6509% | 18.8526% | 15%／35% |
| shared physical | 2.3492% | 7.8236% | 15%／35% |
| root repair | 7.0377% | 19.7289% | 15%／35% |
| 完整总面积 | 2.4336% | 4.6306% | 15%／35% |

全部9项覆盖，结果为`passed_shared_validation_not_joint`。train physical P95为35.1683%，略超35%仍保留。33个合格快照共有10263个逻辑FF引用／唯一FF，CEC、逐位Boolean状态及实际grt库存／全单元面积守恒通过；其中12项负setup、3项负hold不被面积通过覆盖。此包没有验证完整阶段的错误可行／候选排序，不授予完整S/G或正式D，`full_D_ready=false`。

令F为语义FF位数，A为冻结节点＋S状态的预测功能面积，I为输入数据位数，R为变量reset-one位数，p=1500/T。非零参数为：

```text
clock    = 0.018401064302 F + 0.006594856265 A + 0.245141680317 p
physical = 4.444542029756 + 0.009375960385 A
repair   = 0.126442131732 I + 0.039797792032 F
         + 0.106223786960 R + 0.875323393779 p
total    = A + clock + physical + repair
```

T以ps计，面积以µm²计。登记的sqrt(F)、常数及input-port等其他基函数在相应拟合中可有0系数，冻结输入域仍保留。源ID仅用于角色和源等权训练，模型不存在每源／shape／候选／placement截距或精确T价格。数值支持由train产生，FF99–643位、预测功能面积173.342539–2365.125131µm²，T500–3000ps；其余输入域见封存candidate。统一`1e-10×max(1,|low|,|high|)`容差只处理浮点舍入，不进行经验外推。

MAC32的44候选×7数值T共308项完整调用全部覆盖，包括1000ps。11源×7T跨语言检查为76覆盖／1真实拒绝：16位最小结构在2200ps预测面积173.284346µm²低于支持下限，保留拒绝。462项域外／特征负控、241项函数／归属负控、source改名／行序不变、独立SciPy与标准库NNLS预测核对通过；1051条连接、591个capture的零G数值复算一致。44候选是需求与搜索回归集，没有逐候选后端采价。

便携回放无需EDA或用户目录数值库：

```bash
python3 -I -B experiments/arithmetic/evidence/step67_shared_function_v1/replay.py replay \
  --evidence experiments/arithmetic/evidence/step67_shared_function_v1
```

回放实际解包400成员并逐文件验SHA，独立重拟合train标量、复算新validation门槛、重证真实完整归属见证和MAC32通用共享价格；完整CEC／状态／原始ODB资格由收费测量及下述实际恢复归档承担。小包未重新打开全部33个ODB。

完整产物保留于`/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1`。候选SHA为`460222628523b1c8e78b23f85f1e4d5778fdf3c86253da5e4528c2dd09975ce3`，参数与实现冻结见`fit-v1/freeze-v2.json`。`archives/shared-function-raw-v2.tar.gz`包含11555成员、928236054字节，已实际恢复逐文件验SHA；首个超时的部分归档保留，后补失败收据及最终费用另存，不冒充进入较早归档。同盘存储不能防同盘故障，原始目录未删除。1000ps与locked源的物理联合test均未解锁。

最终费用以[resource-closure.json](resource-closure.json)的精确reservation ID去重结算为准；后续688 synth／688 grt、86400秒墙钟／172800秒CPU／30GiB保留。未执行git add／commit／push。

最终39 synth／33 grt／0 detailed、311 support，5390.481854秒叶墙钟／12081.42秒CPU，pending=0；连收据小包约4.42MB、单文件≤512KiB。冻结模型及实际测量依赖的收尾见[final-integrity.json](final-integrity.json)。宽泛源快照中一项证据发布脚本在测量后补了后继路径，原快照保持原字节，实际物理／状态／CEC依赖闭包不导入它；首次过宽检查失败及后继核验分别保留，不将此发布变更说成冻结推理或物理产生器漂移。
