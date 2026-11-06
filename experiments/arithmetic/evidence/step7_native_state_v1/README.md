# ASAP7原生协议状态／边界组件

72 train／36 validation／36新独立状态测试全部完成。冻结参数一次性评价通过：grt状态总面积误差中位6.034688%、P95 18.922855%；synth诊断3.755745%／17.635903%，原中位20%／P95 50%门槛保持。
输入与注册控制边界在三个精确目标全通过，grt最小余量183.134460ps；冻结input／register均803.206085ps，原50ps reserve未改。

发布asap7-native-state.json仅ASAP7 grt原生协议合成银行，ABC1500ps／精确SDC40500、1500、375ps／IO0.2T。
stage1由内核输入valid使能，其后由前级valid使能，同cut共享；包含非均匀寿命、已知零孔洞／高零填充和预登记复位上下文。
面积包含状态／控制、时钟／tap和未归属repair，排除observer；输入service外壳与联合算术／正式边界尚未覆盖。375ps可能没有正的数据预算。

便携核验：`python3 -B -m experiments.arithmetic_dse.model_native_state_evidence verify --folder experiments/arithmetic/evidence/step7_native_state_v1`

加`--external`核对本机原始大产物、Liberty重建、完整已存CTS状态图／CEC及收费祖先。144银行／288阶段／1152路径及12个真实原生结构的便携数值回放不依赖原build或EDA，不重新训练、SAT或消费测试；external也不启动EDA。

旧12类和旧受限状态银行发布均保持原字节。新独立标签已消费，永久排除后继拟合、验证和算法／裕量／域选择。
新原生查询已做投影／物化／RTL核对，生产价格绑定、全候选／位置、整阶段／真实区间与完整D仍待资格；本包不声称九例36条或步骤七完成。Git由用户提交。
