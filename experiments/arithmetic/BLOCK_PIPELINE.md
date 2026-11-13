# 通用分块乘法与多级归约先导

本后继增加可配置块宽及按依赖枚举合法放置的接口，先以MAC32三级需求验收，再用矩形乘法、截断结果、不同位宽、改名和多乘法图检查复用。尚未发布新的算子／S／shared／G价格，原公共D的覆盖规则保持。

结构策略见[block_pipeline_policy_v1.json](../arithmetic_dse/configs/block_pipeline_policy_v1.json)，模型后继约束见[block_pipeline_extension_v1.json](../arithmetic_dse/configs/block_pipeline_extension_v1.json)。RTLzz接口为`enumerateBlockPipelineViews`：0块宽保留原始算子，正块宽使用原有保进位schoolbook模板；默认0／4／8／16／32，适用性由输入位宽和语义决定。按真实不可拆调度组的依赖顺序枚举，每个结果仍通过原合法性和寄存器／valid／reset物化检查。

策略显式限制结构数、合法放置数和完整分配数，触限报告不完整；缺固定前置价格或物化失败不能当作结构不合法而静默删除。它不按T或预测价格裁剪，不强制每级有算术或选择最小块宽，也不能通过旧三结构注册器悄悄执行成original／half／quarter。

## 构建和结构导出

在包含本后继的主仓库及RTLzz子模块源码中执行：

```bash
cmake -S rtlzz -B build/block-pipeline-check -DCMAKE_BUILD_TYPE=Release
cmake --build build/block-pipeline-check \
    --target arithmetic-block-pipeline-export-test arithmetic-reduction-merge-test -j4

build/block-pipeline-check/testv2/arithmetic-block-pipeline-export-test \
    "$PWD" experiments/arithmetic/examples/fused_d/mac32/request.json 3 \
    experiments/arithmetic_dse/configs/block_pipeline_policy_v1.json \
    build/block-pipeline-inventory
```

输出目录须尚不存在。这是通用接口的测试／需求导出器，输入为独立源码请求、L和结构策略；发射RTL供功能验收，不代表D已按合格价格选中它。`inventory.json`记录完整性、预算及视图索引；`graphs/`、`descriptors.json`、`views/`分别存图、去重Query和实际状态／placement。描述哈希只做存储去重，不作为在线价格索引或支持白名单。

其他软件入口：

```bash
python3 -B -m regression.arithmetic_block_pipeline prepare --out build/block-reuse-fixtures
python3 -B -m regression.arithmetic_block_state --out build/block-state-check
```

前者生成可搬移的独立源码请求，可逐一传给同一导出器；其`verify`动作读取实际导出清单、检查整数参考与RTL周期。后者检查参数化状态银行的非零／在途reset、独立写使能、held-valid及寄存器值。均不启动物理后端或授予价格资格。

## 已取得的证据

MAC32三级生成4结构／505合法放置。旧324项逐一保留，新增181个4位放置；33个具有三个非空算术阶段，进一步有8个首级仅部分积、后两级仅Add，其中5个将乘法内部归约实际分到后两级。已发射并周期检查这5份RTL，例如可表达`64个4×4 → 32个Add节点 → 32个Add节点`。这是BEIR节点计数，实际仍按相容G区域联合综合，不能直接当作映射单元数或价格。

真实需求包括65并行字、最高69位变量字、2624位native数据／2820总FF，以及最多65个加数和零压缩工作量的G区域。后继范围按共同数值和位几何规划，不按某个视图刚好需要的数值放宽门禁。

8个全新`not_training`物理先导覆盖窄算子／负载、稀疏G、大银行及含补零／直通输出的归约，见[验收证据](evidence/block_pipeline_common_v1/README.md)。它们永久不进入拟合或独立测试。旧公式外推到4位Mul时延迟高估约32–34%，两个稀疏G区域面积高估约82%／155%；S的native／external面积接近两个大银行实测，input service面积则低估约18–21%。应优先复用合适项，按真实负载和独占计费修正失败项。

`reduction_merge_features`增加压缩后的半加法／全加法／单比特递增／直通列和数值T，103项Python／C++核对通过。`reduction_sampling_v2`证明常量／直通位，只为动态输出放捕获FF，再核对实际映射；一个64位代表核对43零位／4直通位／17算术位。两者尚无新价格系数或支持资格。

下一步先冻结新增train／validation／locked_test准确源、T、拟合规则和有限批次，再补采／拟合。复用旧train保留原职责和标签，旧已消费test、最终PPA及本轮资格探针不得转train。新独立与实际算术状态／完整S/G联合验收通过后，再用同一函数和原规则重新得到D RTL。现有正式函数、50ps经验整级预留及`full_D_ready=false`保持。
