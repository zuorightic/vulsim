# W3／W4／W5：合法门工作量与控制分支后继 v5

本包完成 `W345-branch-load-functions-v5` 的训练内有限选择、冻结、Python／C++实际消费和已消费数据回归。它是诊断候选；W3—W5尚未整体关闭，公共D没有切换，`full_D_ready=false`。20个其余算子独立源保持锁定。本轮没有新增物理调用，也没有把旧验证重新赋予fresh或独立职责。

当前计划见[§7.104](../../../../mission/lxy-plan-fix.md#W345-legal-cover-branch-successor)。前驱[结构v4](../common_flow_structure_v2/README.md)、[稳定响应v1](../common_centered_v1/README.md)保持原身份与原结论。完整本机产物根为 `/home/zyrv/vulsim-artifacts/W345-branch-load-20261114-v5`；这里的压缩JSON与源码快照可独立阅读和回放，无需该绝对目录。

## 机制与输入

实际ASAP7流程的 `DONT_USE_CELLS` 排除 `*x1p*_ASAP7*`、`*xp*_ASAP7*`、`SDF*`、`ICG*`。保留train日志确认ABC使用了这些限制，因此旧参考中 `HAxp5` 的面积不能被解释为该流程的合法实际映射；旧cut仍可作为经验结构代理。`FAx1` 没有被这组规则禁用，本包不声称ABC采用了它的多输出映射。

新[门覆盖实现](../../../arithmetic_dse/prospective_cell_cover.py)从prospective Boolean DAG计算AND／OR2—5、AO／OA、AOI／OAI、INV、XOR、NAND／NOR2的单输出cut。只有完全被当前cut拥有且无外部观察／共享用户的内部信号才能吸收。确定性的贪心覆盖计算面积工作量、cut数量及深度；它不是ABC精确重建，也不模拟电气尺寸选择。`legal-provenance.json.gz`保存18项常数对应的合法Liberty单元、train综合日志、流程配置与匹配techmap／maccmap／Kogge–Stone源码及SHA。

Add／Mux增加合法工作量和数值T的连续交互；同算子的不同宽度共用参数。G保留fused／serial两种图并比较合法工作量、按项重叠与原有KS几何。S按服务valid与native valid分支、reset是否含1、负载及数值T拟合同路径 `R=d+H`，随后取银行最大值。新增 `input_valid` 的service capture上下文字段，原字段保留；本次其余三类S参数未变，不能把该审计字段称为它们已获得新拟合。端口标签保持已经扣除0.2T的H定义。

所有在线特征只来自Query／状态与冻结常数。模型消费不启动Yosys／ABC／OpenROAD／OpenSTA，不读取候选实测价格，不按案例、源、精确形状或精确T查价；拒绝与支持由完整内嵌的冻结v4包继承，公共请求继续拒绝。

## 有限训练与冻结

`protocol.json.gz`在数值拟合前登记。Add面积、Mux时延、G面积、G时延各3种形式×3个alpha；S native_valid为3种形式×2种link×2种目标×3个alpha，共36项。选择分别采用完整语义源／银行LOSO、源等权损失和预登记minimax规则。S逐源路径与银行max一起验证，其他三类S函数和保护原样继承v4；native_valid保护按原非负数值T LP方法从LOSO残差推导。

训练为Add53点／18源、Mux15点／5源、G81点／27源及S13银行／45实现／270路径，其中native_valid90路径。`train-report.json.gz`保存所有72项有限候选，`train-predictions.json.gz`保存入选项完整LOSO与train预测；LOSO是选模诊断，不是独立测试。

| 项目 | train源聚合LOSO median／P95 | 尚存边界 |
| --- | --- | --- |
| Add面积 | 8.41%／13.96% | 小工作量子域9.87%／14.28%；一个源15.61% |
| Mux时延 | 14.62%／19.33% | 两个源19.45%／18.84%，未由汇总豁免 |
| G面积 | 3.76%／13.98% | 零压缩12.96%／18.02%；64位源19.33% |
| G时延 | 4.80%／14.59% | 零压缩4.75%／7.30%；全部域另有逐源失败 |
| S native_valid银行max | 18.93%／27.18% | 失败 |
| S native_valid逐路径，先按源聚合 | 13.36%／20.85% | native分支16.68%／26.06%，失败 |

G的合法工作量候选没有胜出，入选的面积／时延函数及参数与v4相同。S服务分支7.10%／26.39%，全零reset银行26.74%／28.35%，混合reset银行17.29%／26.09%；全零只有2个train银行，不能据此宣布充分辨识。直接按90条路径计的误差median／P95为10.62%／39.35%，与先按13个源聚合的13.36%／20.85%不同，两种口径均保留。LOSO残差校准保护的训练漏点为0，这不构成独立保护资格；各T保护与保守量在 `train-post-selection-audit.json.gz` 中另列。

候选及runtime均为SHA256 `b9546e8f622b6758fe81d224140e74fd3519470fea6919fc96426c0e40582b0b`。`freeze.json.gz`冻结模型、训练数据、协议、特征和拟合实现；`execution-freeze.json.gz`进一步冻结消费实现、二进制及依赖。`source-and-tools.json.gz`保存源码与外置临时工具文本。

## 冻结后的已消费回归

回归读取旧Add、补充Mux、旧G、稳定响应包、v4已消费18点及旧S银行。所有数据都仅作回归；`evaluation--data.json.gz`保存来源SHA和去重，`source-duty-audit.json.gz`按Add交换等价和G有序word列集合核对职责。35个Add点中有3点／1源与train交换等价，不能当作新泛化；下表Add已经排除该源。

| 已消费回归 | v5 median／P95 | 同一批v4 | 结论 |
| --- | --- | --- | --- |
| Add面积，32点／12个非train等价源 | 9.11%／19.40% | 10.36%／19.74% | 总体通过，逐源失败保留 |
| Mux时延，12点／4源 | 11.44%／25.25% | 8.48%／29.02% | 汇总median退化，仍通过；旧子域失败 |
| G面积，48点／16源 | 2.79%／16.87% | 相同 | 参数相同，旧失败保留 |
| G时延，48点／16源 | 4.89%／13.94% | 相同 | 参数相同，旧失败保留 |
| native_valid，已消费因素银行 | 21.89%／27.16% | 30.10%／30.55% | 改善，仍失败 |
| native_valid，旧聚合银行覆盖部分 | 17.86%／23.12% | 16.10%／26.57% | median退化，仍失败；覆盖12/15 |

Add17+9面积22.45%、11+7面积15.59%、旧47+63带消费者源面积16.90%仍失败；12+5从15.48%降至10.56%，不抵消其他源。旧Mux两源6点仍17.49%／26.56%，其中96位源27.56%；v4两个源的已消费6点为11.44%／12.05%，相对v4的8.48%／9.46%退化。G97短重叠时延17.48%和G56面积32.93%仍失败。

S已消费因素银行native_valid／native_enable／input_valid／external_valid逐路径保护漏点为0／0／0／1，external_valid银行最大值也有1个漏点。旧聚合银行覆盖12/15，拒绝与reset支持边界沿用v4；聚合标签没有逐路径见证，逐路径误差及保护漏点保持null，不把空集合记作0。银行保护过量、分支、单源及子域见 `evaluation--post-regression-audit.json.gz`。回归结果没有反馈重拟合、重选参数或提高reserve。

流程边界单独保存：准备回归时，在原生二进制冻结前阅读过v4的已消费归因报告；当时v5数值拟合与特征已经冻结。`regression-boundary-note.json.gz`如实记录此访问。本包没有fresh验证声明，也没有把该访问描述为新的盲测。

## 实现、失败与回放

Python接口为[branch_load_model_v5.py](../../../arithmetic_dse/branch_load_model_v5.py)，C++接口为[arithmetic_branch_load.hpp](../../../../rtlzz/src/backend/arithmetic_branch_load.hpp)。新C++隔离保存v4私有Boolean建图辅助的源码快照，加入显式顺序建图与合法覆盖；冻结v4文件没有就地修改。

初次跨语言核对发现C++嵌套函数参数求值顺序会改变Mux建图ID，使贪心cut深度为3级而Python为2级。改为与Python相同的显式建图顺序后通过；原源码与日志保留。另保留train审计首次join失败、测试Query漏T，以及评价脚本只裁剪Python状态字段而未裁剪native元数据的失败；后者仅修正比较字段，不改变模型／特征／支持。没有物理重跑。

初次343条特征／343条实际参数价格一致；回归另116条特征／116条价格一致，合计各459条。15项跨语言拒绝与5项新回归测试、6项前驱回归测试通过。前驱稳定响应包和v4证据回放均通过。默认回放在推理期间同时阻止文件读取和子进程启动；native选项只显式运行指定的软件测试程序，并再次核对全部特征、价格与拒绝。

在仓库根执行：

```bash
python3 -B -m unittest discover -s regression -p test_branch_load_v5.py -v
python3 -B -m experiments.arithmetic_dse.branch_load_replay_v5
cmake -S regression/branch_load_build -B build/branch-load-v5 -DCMAKE_BUILD_TYPE=Release
cmake --build build/branch-load-v5 --target arithmetic-branch-load-test -j 4
python3 -B -m experiments.arithmetic_dse.branch_load_replay_v5 \
  --native build/branch-load-v5/arithmetic-branch-load-test
```

`identity.json`核对证据摘要和668个源码身份，`source-and-tools.json.gz`核对原文。证据约9.9MiB，单文件最大约2.8MiB；全部文件≤10MiB。新EDA与support叶调用均为0，Ledger累计synth3520／grt3489／final16／support22414、wall362165.52s／CPU738523.70s、pending=0，policy v11／budget v5不变。没有Git提交／推送。

W4还需要解释全零／混合reset及服务／native分支差异，取得宽／深实际算术S和shared资格；W3继续处理窄Add／Mux工作量与真实消费者；W5仍缺组合发起、相关根、多消费者、区域间连线和完整阶段资格。正式W6独立／联合、W7 MAC32新D及W8九案例ABCD保持依赖，不能由本包回放通过自动转授。
