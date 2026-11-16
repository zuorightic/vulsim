# A复用原始参考：实验与调度修订

用户最新要求：A表只列初版实际请求和实测周期，不再以流水目标重测未拆分A。

当前状态：`applied`。2026-11-16 19:49:49 +08:00交接，19:49:52确认后继ready。3个在运Karatsuba A专属重复任务已正常清理、账本全部释放；已登记22个A专属重复任务排除后续发射，其中7个未启动。BCD及归因继续9并行／2线程，接管后补入3个非A任务。当前快照A参考8/9、BCD实测46/111；实时数见[机器进度](controller-progress.json)和主表。

[37组ABCD主表](comparison.md)、[全部显示绑定CSV](comparison.csv)、[A独立参考CSV](A-references.csv)、[A原始身份与失败](A-references.json)。每组ABCD的A引用同一案例的原参考，A请求、A实测Tmin和BCD目标分别列出。主验收是9份A参考＋111条BCD；148仅是含重复A引用的显示绑定，另列37条同池归因。当前A参考8/9；Montgomery原36000ps参考失败，Tmin留空、BCD目标仍待参考。

原A的映射请求与BCD流水目标有意不同；setup各按自身请求判断，hold单列。旧紧目标A的实测、失败、中止和费用保留历史。MAC32使用此前已登记的原1000ps那次A，其余使用初次A-reference，不按实际快慢重新挑A。

独立控制器：`experiments/arithmetic_dse/workload_reference_A.py`。原runtime／controller／selector／backend及所有旧admission／freeze均保留原hash。只排除A专属重复任务；共用B／C／D或归因的物理任务保留。在运BCD子任务保留，NTT既有软件失败另列；9并行／每工具2线程、同一账本、自动retry=0。后续就绪NTT L8只准入BCD及静态归因。新控制器保留原崩溃诊断处理，不自动重试失败任务。

```bash
cd /home/zyrv/vulsim
python3 -m experiments.arithmetic_dse.workload_reference_A report --root /home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1
cat /home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/original-A-reference-v1/controller-progress.json
```

实际后台目录：`/home/zyrv/vulsim-artifacts/workload-equivalent-two-depths-v1/original-A-reference-v1`。原控制器末次表、进度及观察器快照在其`predecessor-snapshot`保存；preapply草稿不涉及EDA，另存`preapply-drafts`。旧快照[上轮完整审计](../operational-review/progress-ppa-rtl-20261116-v1/README.md)的55/148与56/148保留为原时点记录。

验证：7项A复用／调度回归与原两档L／崩溃监控回归合计21项通过，覆盖A原请求保留、失败无Tmin、A/BCD共享任务不取消、未来登记不含A、C/D去重、148展示绑定复用原A、完成竞争及交接前失败恢复旧父调度器。未运行额外EDA或拟合来验证此政策修订。

接管及核验收据：[handoff.json](handoff.json)、[postapply-verification.json](postapply-verification.json)。旧父调度器及旧观察器保持暂停，防止再次发射A；现行控制器独立运行，沿用原崩溃监控逻辑。原冻结源与准入hash全部核对相同。

已确认的既有阻塞：接管前NTT L8软件worker已以−11退出，日志停在第一档47/48；未生成软件就绪收据。保留失败和日志，不自动重跑，其6条BCD仍未登记。Montgomery两档的12条BCD继续等待有效A参考。其余BCD及归因继续调度。

用户随后要求Montgomery256重测A，现另行准入[27ns参考后继](../montgomery-A-retest-v1/README.md)，时钟取旧物理中间数据留余量。该新参考单独发布状态，原36000ps失败和本表的历史读数保留。
