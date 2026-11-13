# 通用宽算子与Add／S／G后继检查点

日期：2026-11-13。完整产物根为`/home/zyrv/vulsim-artifacts/common-family-extension-20261113-v1`，配置见[common_family_extension_v1.json](../../../arithmetic_dse/configs/common_family_extension_v1.json)。本包完成宽语义／接口及7个物理资格点，推进固定S／G候选诊断，并启动有限54点train／validation采集。**没有发布新价格，没有切换D，没有解锁独立测试。** 进度以产物根的`wide-guard-pilot-progress.json`及各批`progress.json`为准；本目录summary为检查点快照，包含尚未结算的后台费用。

## 宽语义、接口与物理资格

新增后继Query，明确输入mask、运算内部精度、输出位段、carry／borrow输入与输出、消费者及capture。每个标量字段的软件上限为4096位，512位回绕与513位完整结果均能表达；这不扩展旧生产Query／图提取／选择器的257位资格。Add／ADC采用确定的内部输入顺序，外部位连接随合同保留；Sub／SBB保持方向。高位乘法从完整所需低位依赖形成进位，不以“结果只需64位”裁掉64×64高半乘的输入。比较与数据Mux属于功能算子，不算S的valid控制。0／1／移位等按数值语义消简，纯位连接不强造物理算子标签。

软件后继v4通过180项Python／C++ Query、特征和RTL核对、2880次native算术核对、1920次RTL算术比较、9项非法Query拒绝，以及50个完整采样壳各32周期的完整capture／独立observer／valid／reset核对。小位宽carry／borrow穷举、高位乘法、已知位证明和Add交换／Sub方向回归通过。见[软件收据](wide-software-proof.json)。

7个永久not_training代表均在1500ps完成synth／grt：512位完整Add、动态ADC、Sub借位、动态SBB、64×64取高64位、无符号比较、193位Mux。实际FF银行、常量／别名、节点最大值、功能路径、独占面积、Liberty、RC／SDC、CEC检查通过；同14阶段标签回放不变。删除每阶段实际使用的一条Liberty弧时，重新生成只随元数据变化的所有权证书，再检查实际弧，14项均在弧检查拒绝，避免只因旧证书摘要过期而误报负控成功。见[物理资格](wide-qualification-proof.json)。资格点永久不转训练或独立测试。

## 样本因素及有限采集

源由共享因素选取，ID只表示数据职责。v1为30 train／12 validation／10 locked_test；采训练标签前的需求审计发现train没有非零`result_lo`，因此追加96×96取高96位的train代表，形成v3协议的31／12／10。原角色、全部旧测试和7资格点不变；新增宽域10个独立源不能替代旧14源的职责，也没有任何一个解锁。

本次准确放行的先导为12个train、6个validation代表，各1500／500／3000ps，共54点，六个批次分别12／12／12／6／6／6项。范围包含窄有效位／移位宽消费者、512位Add、非零carry／borrow、64位完整与96位高位Mul、比较及Mux。见[准确请求清单](wide-guard-pilot-schedule.json)。运行后停止，不自动拟合、解锁或发布；不是无条件执行所有43源的129个guard请求，更不是全部13点容量。完整原子队列、4个全局job、每工具4线程／8192MiB、未来688 synth／688 grt储备继续执行。

这三档是初始时钟取点，不等于三区已覆盖，也不限制将来T只能取这三个数。后继函数仍以T及log₂(T)、1/T等数值变换为输入。物理750／1000／1125／1250ps留出保持；软件使用1000／1373ps不算解锁物理标签。先检查算子响应、消费者、截断／位需求及负载覆盖，再决定有据的自适应补点。

`requirements-and-factor-audit.json.gz`还保存132／256／512／513位G和更深S／shared的逻辑需求设计；没有启动这些组合／银行的物理采集。Horner精度、点积反馈、模数／常量及算法图尚待冻结，不能因节点准备完成就称八例D已覆盖。

## G面积候选

新增可计算的压缩后Brent–Kung前缀DAG，消简常量、裁掉无输出用途的节点，统计存活XOR／AND／OR、深度、逻辑扇出、数值T工作量交互。它是逻辑工作量代理，不使用实际buffer数，也不宣称与ABC映射逐门相同。宽度是数值参数，源码不含候选／形状／精确T价格键。

固定一次源等权相对NNLS，以69个train点／23源拟合7个面积系数；归一化矩阵rank=7。102个既有train／validation点加24项宽域／未见数值T软件Query，共126项Python／C++特征核对通过。G时延保留父函数，不因面积后继无故重拟合。

| validation职责 | 源median相对误差 | 源P95相对误差 |
| --- | ---: | ---: |
| 全部 | 10.51% | 22.13% |
| 原域 | 12.22% | 16.74% |
| 前轮新增域 | 8.12% | 24.45% |
| 本轮repair域 | 3.69% | 3.84% |

500／1500／3000ps各档median为12.39%／9.12%／10.51%，本批33个validation请求结构误拒绝为0。这些是已消费validation的后继回归证据，**不能当独立验收**；实际算术状态、完整阶段误差与排序仍待。参数、数据、秩及逐点误差保存在`SG-fit-*.json.gz`；原发布G与D的49项冻结文件复核通过。

## S逐源候选仍失败

27个train银行保存数据库只读STA重放完成；原9类路径与旧标签的最大差异为0ps。新增逐源路径后共351条，实际检查2050条组合Liberty弧，351项真实删弧负控通过，无新增synth／grt／物理优化。最初pilot在STA成功后因旧银行没有本地Liberty元数据而停止，后继复用原报告、从实际manifest绑定的Liberty提取，没有重跑工具。

首个固定逐源拟合的native_valid仍失败，train归因显示最大四个低估均来自native-valid向下一valid传播。其价格基函数漏用了Query中已有的控制源类型。因此先登记后继，加入“native来源”及其与负载／数值T的交互，只做一次固定Ridge alpha=1和留train源保护。没有按源或级号存系数，也没有在validation扫描模型。

| 控制路径 | validation源median／P95 | train留源保护量 | validation保护漏覆盖 |
| --- | ---: | ---: | ---: |
| native_valid | 20.74%／27.88% | 332.77ps | 0 |
| native_enable | 7.91%／12.31% | 187.46ps | 1 |
| input_valid | 12.84%／23.35% | 15.18ps | 1 |
| external_valid | 3.55%／11.75% | 22.48ps | 0 |

native_valid仍超过15% median门限，保护量也过大；另外两类各有漏覆盖，**S未通过发布**。这四类控制路径的计数不能替代全S／整设计错误可行计数。数据边界、S面积、shared保留既有参数与资格，不从此表授予实际算术或深流水资格。原最大异常仍有cell／wire／H守恒归因，例如702.19ps=435.38+88.58+178.23ps；下一后继应据train检查控制映射、实现保持／使能、银行空间分布及边界，不能继续抬reserve掩盖。

## 复核与保留记录

可在仓库根运行：

```bash
python3 -m regression.arithmetic_wide_family
python3 -m regression.arithmetic_prefix_control
cmake -S rtlzz -B build/block-pipeline-20261112
cmake --build build/block-pipeline-20261112 --target arithmetic-wide-query-test arithmetic-prefix-feature-test -j4
```

实验执行仍须通过共享Ledger和准确请求准入，不因以上编译命令自动获准物理采集。`source-and-tools.json.gz`保存新通用源码及仓库外临时驱动的文本／摘要，其他压缩JSON保存候选及逐点诊断。大型物理产物留在完整产物根，临时Python未放入活动代码目录；无git add／commit／push。

首次宽资格控制器在工具预约前因重复`model_version`元数据停止，7项均未执行EDA；旧协议、失败manifest和进度保留，v2修正后首次实际执行7点，没有付费物理重试。编译入口、测试驱动与报告负控的失败和修正收据也保留，不删除失败费用。后台54点尚未结算；不能把本包summary快照当成最终资源结算或模型验收报告。
