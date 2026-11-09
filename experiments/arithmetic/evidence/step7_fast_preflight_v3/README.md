# 近速度极限模型原型：P0静态需求与复用审计

真实公共源码经当前RTLzz生产候选／调度组重新导出，穷举有界的可动组级分配并由生产evaluateSchedule检查。当前先导为MAC32，导出器及审计按源码清单和图特征工作，不以案例名查价格。

复核：`python3 -B -m experiments.arithmetic_dse.model_fast_preflight verify --out experiments/arithmetic/evidence/step7_fast_preflight_v3`

便携核验重算冻结图上的形状、负载、组合及状态需求和旧模型形状／精确周期交集；不重新编译C++、不运行EDA、不拟合、不读取独立物理标签。四份改变的生产／检查源在source-pool中，其余RTLzz生产源身份及原模型由source-freeze追溯；全部源码仍由项目仓库提供。

requirements保留旧拟合侧几何特征匹配数量，不将匹配数量当成近极限或级内负载资格。S的native／external投影计数与公开外部无条件捕获策略明确分开；输入service仍需从外壳绑定。G的聚合静态描述不是完整拓扑资格或阶段模型。PPA0，full_D_ready=false。

源角色及旧测试隔离保持；独立测试、参考和not_training诊断未进入新拟合。实际命令、日志、资源及旧九例兼容复核在build/step7-fast-prototype-20261109的对应P0后继目录；publication-closure.json另绑定全部本轮support收据和结清资源，不将封包之后的核验费用回填到此前前缀。
