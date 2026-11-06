# ASAP7生产组件清单与原生状态价格绑定

承接 `step7_native_state_v1` 的独立状态资格及 `step7_m2_native_integration_v1` 的基础组件接口。2026-11-05，实施记录见 `mission/lxy-plan-fix.md` 第四章§7.38。本包验收生产C++组件读取／真实银行价格绑定，不新增拟合、物理测量或独立测试选模，不宣称完整D可用。

生产入口为 `experiments/arithmetic_dse/configs/model_asap7_d_components_v1.json`，SHA256 `54ff7b6e706bdfc465b425e6d51ef288f23d43c17d57fd2029fce212819b4a18`。清单分别引用不变的12类primitive与原生state组件，核对schema、hash、ASAP7 profile、grt、ABC1500／IO0.2T、父模型及共同measurement身份。各查询仍须匹配其所属组件的精确域；没有把两包的目标或支持范围取并集。

`NativeStateModel` 从冻结JSON消费位数／信号数NNLS和803.206085ps边界。消费者重新构造StateCostQuery，检查真实placement、逐位mask／reset、前级valid使能、独立通道、连续寿命、完整链、宽度／容量及external capture所有权。数据复位消费范围保守限制为采样中的零、全一、交替、每三位一位模式（按变量位打包）；任意语义复位值没有据此放行。输入／service外壳及联合算术／正式边界不在此价格内。旧数量接口仍拒绝，状态模型不自动授予完整流水线资格。

验证结果：175次价格查询、其中168次实际原生物化寄存器核对，独立Python重构特征与价格最大数值差0；35项身份／越域／过期查询／实际使能拒绝检查通过，两个真实放置的状态价格刷新成立。含5位4变量零孔洞、65位64变量高零填充、非零注册复位，以及56个负输入预算查询。375ps的负预算保留，未钳为0或判为可行。

原436次12类primitive数值查询、14项拒绝及实际双Mux绑定保持；250项旧模型检查与pipeline／reset／valid回归通过。真实D请求经新清单保留original／half／quarter三次有序拒绝，当前共同首缺为联合算术／service边界资格。完整阶段计价、初始／试移／最终整流水线及有效D选择未因此验收。

`native/public-bank-coverage.json`另保存九个公共VUL原始核及3个诊断的实际银行查询。12个均被当前保守复位域拒绝；原始九例覆盖为0／9，尚未审计所有21候选／每个移动位置。该覆盖审计使用静态图／语义复位，没有读取正式整图PPA或独立测试标签。复位条件之外的共享／相关状态及联合阶段／边界仍须后继核验。

复现数值／证据：

```bash
python3 -B -m experiments.arithmetic_dse.model_native_state_binding_evidence verify \
  --folder experiments/arithmetic/evidence/step7_native_state_binding_v1
```

`--external`额外核对本机原始源／构建与测试收据及实际测试二进制；无新编译、拟合或EDA。完整C++回归需本机LLVM18等工具，另运行：

```bash
python3 -B regression/arithmetic_composite_state.py run \
  --out build/native-state-binding-new-check
```

后者使用共享账本收费；已有目录不可覆盖。若要复现12个原始银行审计，可在完整本机依赖保留时增加 `--public-manifest build/step7-native-state-20261105/checks-v5/cases.json`；其声明是原始核及诊断，不是完整D候选覆盖。

`manifest.json`保护212份源快照／组件／查询／收据，`verification.json`另绑定实际便携、external及隔离／篡改核验。隔离副本禁读原仓库，PATH为空并禁止回放子进程，数值回放通过；查询字节篡改拒绝。此项不等于在无工具环境重新编译C++。原模型的 `production_price_binding_qualified=false` 是当时发布检查点，原字节保持；本轮受限消费资格写在后继 `capabilities.json`，`full_D_ready=false`。

本轮新增24个support，无synth／grt／final；全历史结清1589 synth／1567 grt／16 final／6126 support、叶墙钟197923.066499s／CPU447036.48s，9298条entry，pending／active／unsettled均0。无后台EDA，九例正式36条未开始，Git由用户提交。
