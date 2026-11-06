# ASAP7一般状态S：grt有界组件发布

原162拟合测量复用，新增108 train／54 validation／54新独立test完成。冻结参数一次性评价synth／grt均通过，grt八类非birth边界72／72，最小覆盖余量37.372788ps。
grt功能状态／控制面积独立中位／P95：input_service 0.339440%／1.095993%、native_state 0.486566%／0.902302%、external_state 0.046844%／0.172164%。原中位20%／P95 50%门槛、九目标和50ps工程reserve不变。

asap7-general-state.json仅发布ASAP7 grt：三个互斥所有者的功能状态／控制面积，六类原精确周期边界，以及native_enable／native_valid的冻结语义控制负载上界函数。
ABC1500ps、精确SDC1119／1253／1431／3141／3385／4162／4528／11913／14897ps、IO0.2T。一般复位／已知零位／部分寿命／service使能及无条件external捕获只在登记合成原生银行范围内取得资格；来源相关性仅两输入XOR／排列／反相，不授予任意算术来源相关性。
面积排除shared clock／physical／root repair、adapter和observer；联合阶段未来须明确一次计费。三个面积系数和六类原边界完整保持，控制模型只由train拟合、validation选择并在新独立测试前冻结。

便携数值核验：`python3 -B -m experiments.arithmetic_dse.model_general_control_evidence_v2 verify --folder experiments/arithmetic/evidence/step7_general_state_v1`
不依赖原build、活账本或EDA；重生成语义特征、重算固定验证／模型选择及独立结论，不再次消费测试。原始报告位于build中的分块压缩大归档，见raw-archive.json。
完整本机核验：上述命令增加`--external`，回放378银行／756阶段／6804路径、2268收费测量叶、实际Liberty／工具和完整已存CTS CEC，不执行新EDA／SAT。
训练复现：上述模块使用`retrain --folder ...`；使用冻结train／validation重算全部候选参数／校正／选择，检查系数精确一致，不读取任何独立标签来拟合。Python／NumPy／SciPy版本见selection-freeze归档。
隔离／篡改核验：上述模块使用`isolated --folder ...`，禁原树／build／账本读取、PATH为空、禁回放子进程，检查原始文档／发布参数／能力清单篡改拒绝。

旧首轮S失败、旧原生银行和12类primitive发布保留原字节；所有已消费独立标签永久排除后继拟合／验证／算法／裕量／域选择。
production_price_binding_qualified=false、full_D_ready=false。下一步仍需实际C++所有权／查询绑定、G联合边界／受限整阶段、I真实half／quarter区间和完整D选择／RTL／正式36条，不将本组件发布改写成步骤七或九例完成。Git由用户提交。

隔离运行库说明：NumPy／SciPy安装在用户Python包目录；v2显式允许该运行库目录及元数据，并核对冻结版本，仍禁止原项目／build／账本及其他原home读取、PATH为空且禁回放子进程。该适配不改数值生产者、模型、范围或原始归档。
