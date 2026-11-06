# ASAP7原生状态价格绑定与实际银行缺口交接

更新：2026-11-06。当前一般状态S发布见[§7.48交接](asap7-general-state-handoff.md)，参考／目标见[§7.42交接](asap7-reference-handoff.md)，全部候选静态需求见[§7.39交接](asap7-d-requirements-handoff.md)；本文保留[lxy-plan-fix.md第四章§7.38](lxy-plan-fix.md#step7-native-state-production-binding)的受限消费结果；原生协议组件独立发布保持[§7.37](lxy-plan-fix.md#step7-native-state-independent-publication)，旧状态银行及全部测试／失败追溯保持§7.34–§7.36。

**生产组合清单及有界状态价格消费已接通，完整D尚未放行；17项参考及目标冻结完成，首轮S的162拟合任务原始回放／分项验证／冻结及字节复现通过，首轮54独立完成但控制边界69／72拒绝发布，原测试永久封存；§7.46保留面积原参数，只补控制边界后继；§7.47完成原／新324测量回放／验证冻结，§7.48新54独立通过并发布ASAP7 grt有界S组件，面积与六类边界不变，当前无本实验后台EDA。** 新入口为 `experiments/arithmetic_dse/configs/model_asap7_d_components_v1.json`，显式绑定原12类primitive和原生state两份不可变发布。schema／hash／ASAP7 profile／grt／ABC1500／IO0.2T、primitive父链及共同measurement身份逐项核对。S有据组件发布已完成，实际生产特征／所有权／价格绑定仍待，旧清单／系数未替换，未授予整阶段／真实区间／联合边界资格。

§7.40核对真实公共VUL后明确：内核原生数据按前级valid使能，公共外部输出捕获无条件更新，input／service另有独立使能。本文及旧消费证据中的external capture是显式请求的受限上下文，不能转授公共外壳协议；后继S／联合标签须分别建模和计费，旧发布／测试结论不改。

原生StateCostQuery保存投影输入；消费者从真实图／协议／完整placement重构，检查每槽mask／reset／enable、独立来源、连续寿命、完整链、容量及external输出capture所有权，再计算冻结NNLS面积和状态银行残余预算。输入／service外壳仍排除，旧scalar stateArea拒绝绕过检查。数据复位消费范围保守限制为采样中的零、全一、交替、每三位一位模式（按变量位打包），没有用两个数量特征取代结构／上下文资格。

175次价格查询（168次真实原生寄存器物化）与独立Python数值最大差0，35项身份／过期／越域／实际错误使能拒绝通过，实际placement改变后价格刷新。零孔洞／高零填充及非零注册复位已覆盖。375ps有56个负input预算查询，保持负值；状态银行独立质量通过不表示该目标时序可行。原436次组件查询／14拒绝、250旧模型检查与pipeline／reset／valid回归通过。生产D小图保留original／half／quarter有序拒绝，首缺已更新为联合算术／service边界资格。

**九例仍有实际银行资格缺口。** 本轮重新编译九个公共VUL原始核及3诊断并核对真实物化状态，它们均被当前保守数据复位域拒绝，例如0x80000035。原始九例状态覆盖0／9；这不是新的独立误差失败，也不据此推断复位之外的共享／相关状态、外围／联合边界已合格。全21候选和每个移动位置尚未完整审计。完整pipeline的typed计价／最终核对钩子已加入，但当前预检拒绝联合边界，尚无合格完整D调度／选择／RTL证据。

后继证据为[step7_native_state_binding_v1](../experiments/arithmetic/evidence/step7_native_state_binding_v1/README.md)，约3.79MiB；212份源／组件／查询／收据快照的便携／external核验通过，隔离副本禁读原树、PATH为空、禁止回放子进程时数值复现通过，查询篡改拒绝。入口：

```bash
python3 -B -m experiments.arithmetic_dse.model_native_state_binding_evidence verify \
  --folder experiments/arithmetic/evidence/step7_native_state_binding_v1
```

增加 `--external`只核对本机原始依赖与测试二进制，无编译／拟合／EDA。完整C++回归见证据README。verification.json绑定实际检查及结清前缀。

原[原生状态独立发布](../experiments/arithmetic/evidence/step7_native_state_v1/asap7-native-state.json)SHA256仍为 `ce280fb25047038d0a9ff80084d744191419546d72072864f316ec7c4a8d9bff`，144任务全部完成。独立grt状态面积中位6.034688%／P95 18.922855%，边界最小余量183.134460ps；系数／域／803.206085ps边界／50ps reserve与原20%／50%门槛保持。其production_price_binding_qualified=false是当时发布检查点，原字节未改；本轮受限消费资格由后继capabilities单独声明，full_D_ready=false。所有已消费测试永久排除后继拟合／验证／算法／裕量／域选择。

§7.39已登记全部21候选／108视图需求与计费责任；当前应先实现17类参考与联合标签归属的软件前检和采集准入，取得数值目标，再登记实际语义复位、共享／相关状态及外围／联合算术边界的合成后继资格，并与用户已确认的[受限整阶段独立模型](asap7-stage-topologies-draft.md)统一计费／边界所有权。随后补真实half／quarter后继、正式目标交集、全候选／位置、完整预算／初始放置／移动／选择与RTL，最后冻结正式九例36条。不得用正式／保留整图PPA回填训练或改已消费测试结论；已合格且域匹配的11类不重训。

本轮新增support24，无物理调用。全历史1589 synth／1567 grt／16 final／6126 support，叶墙钟197923.066499s／CPU447036.48s，9298条entry，pending／active／unsettled均0。无需用户监看后台。未git add／commit／push，完整步骤七和688条未关闭。
