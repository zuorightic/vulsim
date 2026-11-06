# ASAP7一般状态S模型：限定组件发布与生产绑定交接

2026-11-06，当前结果见[fix第四章§7.48](lxy-plan-fix.md#step7-general-state-qualified-publication)：新54独立原始核验／冻结参数一次性评价通过，ASAP7 grt有界S组件已发布；便携数值／完整原始／external／隔离／篡改、冻结训练精确复现和本组件Git视图均通过。§7.45旧失败、§7.46–§7.47采集／验证冻结、全部已消费测试与§7.42九目标保持。S的生产查询／所有权绑定、G／I及完整D仍待，正式36条未放行。

## 当前结果与复现入口

新54项独立已经全部完成、错误0，原始核验及冻结参数一次性评价通过；synth／grt八类非birth边界均72／72，三个面积分项均过原中位20%／P95 50%。当前没有本实验的后台EDA队列；原status只显示采集进度，资格／发布以本节及新publication／independent-verdict为准。

| grt功能状态／控制面积所有者 | 新独立中位误差 | 新独立P95误差 |
| --- | ---: | ---: |
| input_service | 0.33944% | 1.09599% |
| native_state | 0.48657% | 0.90230% |
| external_state | 0.04684% | 0.17216% |

grt全部状态路径的最小上界覆盖余量37.372788ps，见4162ps的external_data保留边界；两类后继控制路径最小余量68.873866ps。synth全部路径最小余量44.471734ps。这些是模型上界覆盖余量，不是正式目标的setup slack；面积误差不包含shared clock／physical／root repair，也不是整阶段PPA。原三面积系数、六类边界、九个目标及50ps reserve均保持，新54项test已写test-consumed.json并永久排除后继拟合／验证／算法／裕量／域选择。首轮旧54项失败保持。

[发布包及详细说明](../experiments/arithmetic/evidence/step7_general_state_v1/README.md)包含`asap7-general-state.json`、`publication.json`、`capabilities.json`和冻结源／数据／收据。模型SHA256为`1b61a68d80b704532ff38483a034ec2c03de921448095deb6acdcbbb00be383d`，发布manifest为`a05f864ed99407fbb30747043e1dc8e153284bedae27ca103e84a48e043571f4`。只发布ASAP7 grt合成原生银行的三所有者功能状态／控制面积及八类状态边界；任意算术来源相关性、联合G、shared面积、真实I区间和生产D价格绑定均未由本包授予资格。

```bash
cd /home/zyrv/vulsim
python3 -B -m experiments.arithmetic_dse.model_general_control_evidence_v2 verify \
  --folder experiments/arithmetic/evidence/step7_general_state_v1
```

增加`--external`执行完整原始／实际Liberty／工具／已存完整CTS CEC回放；将`verify`改为`retrain`重算冻结train／validation的全部候选参数／校正／选择并精确比较，改为`isolated`执行隔离数值／训练与篡改负控。全部已实测通过，没有重采物理数据或重新消费测试。数值运行库安装于用户Python包目录，v2显式允许其安装目录及冻结版本元数据，仍禁原项目／build／账本及其他原home读取、PATH为空且禁回放子进程；该后继适配不改原始归档／生产者或模型数值。

完整原始归档为`build/step7-general-control-20261106/release-raw-archive-v1`，378银行／756阶段／6804路径、2268测量付费叶，37个内容池分块、144400007字节。Git侧小包2594036字节（约2.47MiB）、13文件，最大单文件1493018字节；实际Git可纳入文件副本与manifest一致，大归档被忽略，未git add／commit／push。收尾检查及费用记录见`publication-closure-v1.json`和`publication-git-view-proof.json`。

本轮收尾全局结清前缀：2042 synth／2016 grt／16 final／8047 support、12121 entries，叶墙钟232268.820083s／CPU509320.29s，pending／active／unsettled均0。本轮独立核验／发布／训练复现／Git视图只新增12个support，不新增synth／grt／final，旧失败费用不退款。

下一步使用该冻结组件完善实际C++ service／native／external状态查询、所有权和条件边界价格绑定，并逐候选／位置核对；G受限整阶段／联合边界、I真实half／quarter区间、完整初始／试移／最终预算、D选择／RTL及正式36条／步骤九仍待。production_price_binding_qualified=false、full_D_ready=false，不能用新S组件替换旧包字段后直接放行D，也不将其合成来源域转授任意算术图。

## 本轮完整回放、验证与冻结（§7.47历史检查点）

新162项与原162项有效train／validation合并回放，覆盖36个语义源／324份测量／648阶段／5832路径，1944收费叶和69199文件hash核验通过。实际Liberty面积／FF／pin／函数、全部单元唯一归属／状态几何、SDC存储v3／RC、原生面积JSON、完整已存CTS CEC及收费祖先一致，未重跑旧综合／OpenROAD，PPA0。拟合只用train，原54已消费及新54锁定独立标签不进入拟合／选择。

三个面积模型完整参数、六类保留边界的九周期完整参数逐项保持。面积在原／新／合并验证分别通过原20%／50%，六类保留边界全部覆盖、最小余量50ps。下表仅为新增54项validation的grt功能状态／控制面积误差，排除shared clock／physical／root repair，不是整阶段PPA：

| 面积所有者 | 新验证中位误差 | 新验证P95误差 |
| --- | ---: | ---: |
| input_service | 0.20269% | 2.96235% |
| native_state | 0.56409% | 1.71520% |
| external_state | 0.04634% | 0.24574% |

仅native_enable／native_valid比较原登记三候选，系数及最大正残差校正均只用train，原50ps工程reserve不变。synth选择不带周期指示的静态控制负载NNLS，最小控制验证余量40.969143ps；grt选择带九精确周期指示的NNLS，最小余量97.135391ps。grt平均预测控制上界641.948721ps，登记的跨周期最大值基线为718.770218ps。该选择量属于验证侧，不等于独立泛化或整图收益；不插值或转授任意算术相关性／G联合边界。

`fit-v1`／`fit-v2`的candidate、validation、selection-freeze三文件逐字节一致（`fit-byte-proof.json`）。冻结独立查询在1728次实际验证行查询上与验证判定一致；错误周期／负值／非有限特征、validation／test校正均拒绝。条件上界反例通过：需要检查每个样本自己的上界，即使其所需时延不是该类最大值也可能超界，不能只取最大所需时延样本。

关键SHA256：

- 合并拟合数据：`cda58a769d49dd1ea61a957cedadcf9a79d776ebfb64bcfa572712c08a243500`。
- candidate：`ed506072834b9744ff8a817b1e071a92d71e3ee080db6edc48781e2723696a17`。
- selection-freeze：`b27fced59c3a61b2fbcebd37cc52346c4fa2f523305b56acaaa9680e059852e3`。
- 新独立准入：`f7dbf878b7041a17f04dc9a08850b783ab303a930657ef54e00e397007c25265`。

原candidate保持当时awaiting_independent_test字节；§7.48由独立verdict及新发布承接实际资格，不覆写原候选，生产绑定及full_D仍为false。新准入绑定53份生产／拟合／评价／回归源，错角色／错周期／错线程数／改candidate拒绝，逐收费叶绑定selection-freeze，守卫无新增物理预约。独立任务54个新synth／54个新grt及support的包络36000s墙钟／144000sCPU／13.5GiB，并保留后续86400s墙钟／172800sCPU／688 synth／688 grt／30GiB；启动时可用内存约45GiB、磁盘164GiB。

新独立服务启动前结清前缀为1988 synth／1962 grt／16 final／7819 support、11785 entries，叶墙钟227555.105971s／CPU501500.95s、pending／active／unsettled均0；此后费用实时累加，不宣称运行中全局结清。采完后先完整回放54任务／108阶段／972路径及收费祖先，再按冻结上界函数一次性评价，逐样本／精确周期／八类非birth路径全覆盖，三面积分项仍过原20%／50%。评价写test-consumed.json，新独立标签永久排除后继拟合／验证／算法／裕量／域选择；全部grt门槛通过才发布有据S范围并另做生产绑定与发布核验。

## 首轮一次性独立结论与封存

54任务／108阶段／972路径、324收费叶及11658文件hash原始核验通过。冻结参数一次性评价：synth全部通过，grt三个功能状态／控制面积分项全部通过，边界69／72，故拒绝发布，发布清单为空；原参数、域、九目标和50ps reserve未改。

| grt面积所有者 | 独立中位误差 | 独立P95误差 |
| --- | ---: | ---: |
| input_service | 0.32954% | 1.21461% |
| native_state | 0.28542% | 1.71838% |
| external_state | 0.02239% | 0.16256% |

| 失败控制边界 | 冻结上界ps | 独立所需ps | 超界ps |
| --- | ---: | ---: | ---: |
| 1431ps native_enable | 793.935883 | 808.473206 | 14.537323 |
| 4528ps native_valid | 498.802216 | 559.385254 | 60.583038 |
| 11913ps native_valid | 486.033676 | 488.299805 | 2.266129 |

三个超界见证都来自test-04的valid控制网；4528ps主要是Q-D控制路径增长，H仅比同周期冻结H最大值多约0.259ps。原报告见不同buffer分支；相近的大银行也已存在于validation，因此不能只按总位数或简单增加reserve认定问题已解决。首轮54项test已写test-consumed.json，永久排除后继拟合／验证／算法／裕量／域选择。

完整216银行／432阶段／3888路径、1308收费收据（含四份旧失败综合）的便携原始回放、完整external／隔离／篡改核验通过。约106MiB完整原始归档按存储分层移到`build/step7-general-state-20261106/failure-raw-archive-v1`，原manifest和全部内容字节保持，迁移收据为同父目录`raw-archive-relocation.json`。Git使用另立的[小型数值封存v2](../experiments/arithmetic/evidence/step7_general_state_failure_v2/README.md)：便携模式重算固定特征／验证／边界／独立结论，完整原始报告回放由external读取上述归档，不混称小包包含全部物理原始文本。

## 控制边界后继范围与准入

新协议`model_asap7_general_control_v1.json`的SHA256为`51cbbfc436de2c689907374f7b02d2ce588bf76e4ad3d4ed99490b5f38bd7193`；新准入SHA256为`14cc02d03991d5d8d83f080c865c7a51b350d34e373be03fba50976c3e36be00`。只允许native_enable／native_valid两类控制边界另行拟合；原三所有者面积系数、其余六类非birth边界及其精确周期值保持。最终仍逐所有者检验原面积20%／50%门槛，并要求全部八类非birth边界覆盖。面积独立合格证据可继承，但首轮S整体失败保持，未发布任何新S价格。

新24源×九目标预登记216任务，split为108 train／54 validation／54 locked test；整个源及全部周期／阶段同split。使用新的盐值重建reset、两输入相关来源及每级寿命／使能负载分布，与此前全部源语义签名分离；30种声明宽度至66位、18通道、一般复位／不完整链和三种service协议保持。独立性是已见宽度上的新控制负载／复位／来源／寿命上下文，不是新位宽或任意算术相关性。

软件前检为`build/step7-general-control-20261106/preflight-v1/software/proof.json`：24×128周期、86784项完整状态检查、544个service-valid保持区分周期、15867次invalid下external无条件捕获检查；实际错误external门控RTL拒绝，通用FF几何与各split完整30宽度通过。新训练侧最大使能位负载552、最大原生data位779；validation／test为新上下文，完整物理资格仍待。仅看这些上限不能授予任意真实银行或G联合域。

拟合侧已复用原162 train／validation并加入新增162任务，旧54 consumed test绝不进入后继。两个控制路径的候选在新采集前登记：跨九个已登记周期的train最大值基线、静态控制负载NNLS、带九个精确周期指示的NNLS。特征为使能位负载、sqrt／log负载、词分支数、valid目标数、原生状态／复位one位、输入和external位数等；不使用映射单元或后端标签作查询特征。NNLS上界校正只取train最大正残差，工程reserve仍50ps；每阶段整组选两个路径模型，先要求所有旧／新validation行覆盖，再比较平均预测上界、序列化大小及预登记顺序。原三个面积模型不重拟合，六类保留边界不暗改；它们也必须通过后继验证和新独立测试。

全216任务预留新216 synth／216 grt、136800s墙钟／547200sCPU／54GiB（含support7200s），另保留后续86400s墙钟／172800sCPU／688 synth／688 grt／30GiB；原162测量复用不会伪造新物理费用。验证／冻结／字节复现由§7.47完成，§7.48已完成新54独立评价及有据S发布；生产绑定与联合资格仍待。G／I、生产统一所有权／查询、D选择／RTL及正式36条仍待，full_D_ready=false。

新服务启动前结清前缀为1826 synth／1800 grt／16 final／7163 support、10805 entries，叶墙钟215597.671158s／CPU479271.80s、pending／active／unsettled均0；此后新增费用按原Ledger累加，运行中不宣称全局结清。首轮支持入口失败和两次预约前计费上下文拒绝保留，不退款或重写收据。小型封存v2的便携／完整external／隔离／篡改核验亦已通过，大小1612045字节。

## 首轮原始回放、验证与冻结（历史检查点）

`fitting-check-v1/fitting-dataset.json`完整回放18个拟合侧源／162任务／324阶段／2916路径，核验972个收费叶及34772个文件hash。RTL／特征重生成、真实Liberty单元面积／FF／pin／函数、互斥所有权／实际FF、SDC v3、RC、原生面积JSON、完整CTS CEC及全部命令收费祖先一致。原四个失败综合探针另保留且不继承数值标签；提取时原54项test运行目录不存在。

`model_asap7_general_state_fit_v1.json`和执行源在提取前复制登记。比较三种train-only NNLS：bits／signals、typed state、按九个精确SDC分别拟合typed state；无截距、不加后验面积裕量。每个物理阶段整组选一个三所有者模型，先要求三个所有者均通过原面积中位20%／P95 50%，再比较归一化总绝对误差、序列化大小和稳定名称。synth和grt均选择`per_owner_NNLS_typed_state`，特征为data_bits、data_signals、valid_bits、enable_domains、reset_one_bits。

| 阶段 | 功能状态／控制面积所有者 | 验证中位误差 | 验证P95误差 |
| --- | --- | ---: | ---: |
| synth | input_service | 0.08164% | 0.20230% |
| synth | native_state | 0.22637% | 1.62826% |
| synth | external_state | 0.02105% | 0.03978% |
| grt | input_service | 0.23707% | 0.56572% |
| grt | native_state | 0.17054% | 1.75095% |
| grt | external_state | 0.04248% | 0.16485% |

这些数值只对应各自拥有的功能状态／控制面积，共享clock／physical／root repair另存；不是整阶段面积或时延误差。原native总面积系数保持不变，仅在独立诊断文件中对新源报告，不参与模型选择或联合分项叠加。逐周期面积明细只报告，不在测试后新增门槛。

边界按每阶段／每精确周期／八个非birth路径类冻结为`max(0,max训练／验证H) + max训练／验证路径延迟 + 50ps`，保留两个最大值各自的见证，输入IO只扣一次。birth适配器路径只诊断；任意算术输入相关性和G联合边界仍未取得资格。独立测试要求每个对应上下文的最大H＋delay不超过已冻结值，不根据测试加reserve。

`fit-v1`与`fit-v2`重复拟合的candidate、validation、immutable-baseline-diagnostic、selection-freeze四文件逐字节一致，proof为`fit-byte-proof.json`。关键SHA256：

- 拟合数据：`d9be0843352f110aa6e37e013423051fc49e21c7e42f850ecfcf5bacd05cb4c5`。
- candidate：`5300b9a7076a9bc583ba5f1bc651cd65904bfaf1dbcb71042576774a85fb89da`。
- selection-freeze：`16dba85ab9237c6be1a7d8416f00d2571e03d4de32808fb37158fd297696a834`。
- 独立准入：`16f9d0cfe72f5e09c984ddfe6fce019b83c495139f4d37887d9ab488fd92b745`。

独立准入绑定全部50份生产／拟合／评价源、原拟合准入、数据、candidate和selection-freeze，并逐付费叶在共享Ledger中绑定冻结身份。错误split、错周期任务及改candidate均拒绝，准入负控没有新增物理预约（`independent-lock-guards.json`）。此处候选的awaiting_independent_test为§7.44历史停点；§7.45的一次性评价已失败，原candidate字节不改，结论由独立verdict／空发布清单另行承接。

## 合成源与范围

首轮协议为[model_asap7_general_state_v2.json](../experiments/arithmetic_dse/configs/model_asap7_general_state_v2.json)，SHA256 `9aaa9c8503ee8e84b34ab41ff08f52e817e4f6fcf43bb868b9b12e96b79895b6`；首轮拟合准入SHA256为`55a4b0a565c255bd22e1e0af64a35c3b57c75af4bd048df81161185d500946bc`。原v1协议／准入及四份诊断保留。

目标来自不变`model_asap7_m2_targets_v1.json`：精确SDC为1119／1253／1431／3141／3385／4162／4528／11913／14897ps，ABC固定1500ps、I/O0.2T。同源全部目标／阶段只属于一个split，24个规范化语义签名不同；独立性是已暴露宽度上的新复位／掩码／来源／生存期上下文，不宣称未见位宽。

源包含30种预登记声明字宽，最大66位、每字最多64个变量位、最多18通道、130个service输入数据位；包含一般哈希复位、已知零孔洞／高低补零、非完整生存期和相关来源。相关源为共享注册根上的不同两输入XOR／排列／反相，适配器组合面积单独归属；不能由本批S独立推断任意算术相关性，后者仍需G联合资格。

三种协议分别实现并检查：service数据按独立或共享写使能捕获，输入valid也可随写使能保持；native valid逐拍推进，native数据按前级valid使能；external数据／valid无条件捕获。九个实际公共VUL外壳的service使能见证已核对。每个service／native／external状态位恰好被观察一次，明确保留所有待测状态；observer面积排除，不将被优化掉的导出别名当作寄存器端点。

面积按input_service、native_state、external_state、source_adapter、observer、shared_clock、shared_physical、root_boundary_repair互斥归属，实际FF数量必须与静态保留几何一致。三个state所有者分别拟合；原native总价仅作不可改诊断基线，不作为可叠加的联合分项。共享clock／physical／repair另保留，未来不能与G重复收费。九类路径保留native data／enable／valid、external data／valid、input data／enable／valid及birth data；birth适配器路径只作诊断，不冒充state纯控制边界或D_ref。

## 已完成前检、精度修订与失败保留

最终软件proof为`build/step7-general-state-20261106/preflight-v6/software/proof.json`：24源×128周期、93696个完整状态检查，544个区分service valid保持的周期、18573个在valid为0时检查external更新的词次；错误valid门控external的实际RTL变体被拒绝。24源通用未映射几何成立，train／validation／test各自覆盖全部30种声明宽度并含18通道／无完整链样本。软件前检只读独立源结构，不读独立物理标签。

首轮collection-v1有四个综合工具命令成功、grt0，随后停止：14897ps的两份SDC中0.2T写成2979.4001ps，比名义值多约0.0001ps；另外两份快照缺native_valid路径。继续核验发现部分未使用的导出状态口被裁剪／置常量、相关位还可共享，原“按名字找到全部保留FF”的假设不成立。四份诊断与费用保留，**不进入拟合、不冒充当前新源检查点**。新源显式观察并保留全部状态，采用不同的两输入相关位，故当前v2需要新的综合；没有重测原已发布模型或参考。

新`sdc_storage_v3.py`沿用原严格SDC语法，只为IO延迟接受“名义值或其IEEE binary32秒存储值，再按write_sdc十进制位数舍入”的准确结果，不增加相对容差、不改时钟／I/O政策。四份实际SDC重放与14项负控通过：更大IO偏差、正延迟归零、非有限值、改时钟、改uncertainty、时序例外及命令注入均拒绝。proof为`storage-check-v1/software/proof.json`。原`sdc.py`、旧契约和旧证据不改；新验证器只由本后继显式绑定。

早期三个软件前检停止分别为容量上限检查、外部协议区分用例不足及公共RTL历史目录路径；均在正式采集准入前保留收据。后继准入负控最初省略显式context产生参数错误，随后按真实叶命令签名重验，锁定test／外来任务拒绝、pilot的Ledger父类路由和后继hash身份均通过，未分配额外物理预约。当前所有真实叶调用都显式提供context。

## 首轮预算与后继依赖（历史额度保留）

216项全部新综合／新grt，单任务完整叶包络600s＝environment60＋synth120＋初始快照120＋专用synth快照60＋grt180＋专用grt快照60。全cohort加support7200s为136800s墙钟／547200sCPU、54GiB存储；另保留后续86400s墙钟／172800sCPU／688 synth／688 grt／30GiB。均使用原共享Ledger，旧失败不退款；运行中不宣称全局结清。容量准入只覆盖明确24源及九周期，不转授G／I／任意实际银行或正式36条。

首轮独立准入包含54个新synth／54个新grt及support，墙钟包络36000s、CPU144000s、存储13.5GiB；另保留后续86400s墙钟／172800sCPU／688 synth／688 grt／30GiB。启动时可用内存约46GiB、磁盘约163GiB，4×4线程及每任务8GiB符合容量；额度是上限，不是预计耗时或实时已用量。继续共用原Ledger，不退款或清零，运行中不宣称全局结清。

首轮已完整回放54任务／108阶段／972路径及收费祖先，并用冻结参数一次性评价；面积通过、控制边界失败，发布为空。原规则保留：面积仍逐所有者／阶段要求原中位20%／P95 50%；逐精确周期／非birth路径类要求最大H＋delay不超过冻结边界。一次性评价写入`test-consumed.json`；测试此后永久排除拟合／验证／算法／裕量／域选择，无论通过与否都保留原结论。只有全部grt门槛通过才可发布有据范围，之后另做生产所有权／实际查询绑定及便携／external／隔离／篡改核验，不用训练／验证替代独立资格。

原R目标工作已完成；G／I仍需合成源前检、完整分组及容量／预算，C++完整阶段所有权／预算／部分阶段界和D选择／RTL继续待完成。full_D_ready=false、formal_36_complete=false，完整步骤七与688条未关闭；Git由用户操作。
