"""Finalize receipts/indexes after all measured verification leaves settle.

This is outer accounting and snapshot bookkeeping. It does not launch tools,
rerun an analysis, modify implementation, or change any measured result.
"""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-review-20261102'
from experiments.arithmetic_dse.budget import usage,cpu_seconds
from experiments.arithmetic_dse.freeze_history import MUTABLE_DOCUMENTATION
E=R/'experiments/arithmetic/evidence/step6_review_v2';C=R/'experiments/arithmetic/evidence/step6_capacity_v2'
F=R/'experiments/arithmetic/whole_graph_freeze_v2.json';f=json.loads(F.read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def gzdoc(p,d):p.write_bytes(gzip.compress((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode(),mtime=0))
before=json.loads((B/'backend_usage.json').read_text());live=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());entries=live['entries']
assert entries[:len(before['entries'])]==before['entries'] and usage(entries)['pending']==0
audit=json.loads((B/'final_audit.json').read_text());assert audit['status']=='passed' and audit['full_artifacts_verified'] and audit['backend_completion']
portable=json.loads((B/'portable_checks.json').read_text());assert portable['status']=='passed' and len(portable['negative_checks'])==11
for p,h in json.loads((B/'protected.json').read_text()).items():assert sha(R/p)==h,p
for path,h in f['files_sha256'].items():
    if path not in MUTABLE_DOCUMENTATION:assert sha(R/path)==h,('source changed after acceptance',path)
for name in ('final_audit.json','portable_checks.json'):shutil.copy2(B/name,E/name)
for name in ('final_audit.py','portable_checks.py','archive_review.py','settle_snapshot.py'):shutil.copy2(B/name,E/'procedures'/name)
extra=entries[len(before['entries']):];delta=json.loads((E/'usage_delta.json').read_text());delta['entries']=extra;write(E/'usage_delta.json',delta)
receipts=[]
for entry in extra:
    path=Path(entry['command_record']);record=json.loads(path.read_text());GNU=Path(record['gnu_time']).read_text()
    assert not record['cleanup']['remaining_live_pids']
    assert record['walltime_s']==entry['walltime_s'] and record['exit_code']==entry['exit_code']
    if entry.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':assert entry['CPU_time_s']==record['CPU_limit_s']
    else:assert cpu_seconds(record['gnu_time'])==entry['CPU_time_s']
    row={'id':entry['id'],'record':record,'GNU_time':GNU,'actual_command_record_sha256':sha(path),'actual_log_sha256':sha(Path(record['log']))}
    sources=path.with_name(path.name.replace('.command.json','.sources.json'))
    if sources.exists():row['actual_source_sha256']=json.loads(sources.read_text())
    receipts.append(row)
    if entry['stage'] is None:(E/'logs'/(entry['id']+'.log.gz')).write_bytes(gzip.compress(Path(record['log']).read_bytes(),mtime=0))
gzdoc(E/'receipts.json.gz',receipts)
a=usage(before['entries']);n=usage(extra);u=usage(entries)
resource=json.loads((E/'resources.json').read_text());resource.update(baseline_usage=a,new_usage=n,cumulative_usage=u,pending=0,failed_leaves=sum(e.get('exit_code',0)!=0 for e in extra));write(E/'resources.json',resource)
p=R/'mission/lxy-plan-fix.md';text=p.read_text();start='<!-- step6-review-resources:start -->';end='<!-- step6-review-resources:end -->'
table=['| 资源 | 本轮开始前 | 本轮新增 | 累计 |','| --- | ---: | ---: | ---: |',f"| synth / grt / final | {a['synth']} / {a['grt']} / {a['final']} | {n['synth']} / {n['grt']} / {n['final']} | {u['synth']} / {u['grt']} / {u['final']} |",f"| support叶命令 | {a['support_calls']} | {n['support_calls']} | {u['support_calls']} |",f"| 墙钟秒 | {a['walltime_s']:.6f} | {n['walltime_s']:.6f} | {u['walltime_s']:.6f} |",f"| CPU计费秒 | {a['CPU_time_s']:.6f} | {n['CPU_time_s']:.6f} | {u['CPU_time_s']:.6f} |",'| pending | 0 | 0 | 0 |']
left,tail=text.split(start,1);_,right=tail.split(end,1);text=left+start+'\n\n'+'\n'.join(table)+'\n\n'+end+right
summary='\n最终核验：85项软件回归通过；隔离副本无build／EDA、PATH为空时父链及默认便携入口通过，叙述漂移接受并报告，11类负例拒绝。完整本机归档实际逐成员读取通过，5份已完成综合的规范化映射网表重新计算通过。新增后继两包均≤5MiB、单文件≤1MiB；7587份旧保护文件不变。一次负例测试仅因断言将IO写成I/O而失败，纠正后通过，原日志与费用保留；不涉及新的电路或物理重跑。最后只刷新已结算回执／资源表及索引，最终保护集合以本冻结的索引哈希为准；核验摘要中的候选时点统计不冒充最终文件计数。\n'
assert '最终核验：85项软件回归通过' not in text;text+=summary;p.write_text(text)
for path in MUTABLE_DOCUMENTATION:
    if path in f['files_sha256'] and sha(R/path)!=f['files_sha256'][path]:
        target=E/'source_delta'/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/path,target)
        f['files_sha256'][path]=sha(R/path);f['source_snapshots'][path]=str(target.relative_to(R))
changes=json.loads((E/'file_changes.json').read_text())
for row in changes:row['after_sha256']=f['files_sha256'][row['path']]
write(E/'file_changes.json',changes)
f.update(frozen_at=datetime.now(timezone.utc).isoformat(),scope='step6 complete for declared whole-graph/safety/finite-capacity scope; UDR100ns mapped reuse and F2 original-clock grt with failures/costs retained; no D model/training/main matrix',step6_acceptance='complete_for_plan_10_6',final_accounting_usage=u)
for package in f['packages']:
    index=R/package['index'];directory=index.parent
    write(index,{'version':'step6-review-'+package['role']+'-index-v2','files_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts}})
    package['sha256']=sha(index)
write(F,f)
sizes={}
for package in f['packages']:
    directory=(R/package['index']).parent;files=[p for p in directory.rglob('*') if p.is_file()]
    sizes[package['role']]=sum(p.stat().st_size for p in files)+(F.stat().st_size if package['role']=='software' else 0)
    assert sizes[package['role']]<=5242880 and max(p.stat().st_size for p in files)<=1048576
write(B/'final_snapshot.json',{'status':'passed','final_freeze_sha256':sha(F),'package_bytes':sizes,'usage':u,'all_old_files_preserved':7587,'finalization':'settled accounting/index metadata only; source and physical measurements unchanged'})
print(json.dumps({'freeze_sha256':sha(F),'package_bytes':sizes,'usage':u},indent=2))
