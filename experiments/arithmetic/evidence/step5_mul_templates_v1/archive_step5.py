"""Freeze step5 source/compact software evidence with no historical overwrite."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import usage,cpu_seconds
B=R/'build/step5-parameterized-20261031';G=B/'release';E=R/'experiments/arithmetic/evidence/step5_mul_templates_v1';P=R/'experiments/arithmetic/arithmetic_interfaces_freeze_v2.json';F=R/'experiments/arithmetic/mul_templates_freeze_v1.json';C=R/'experiments/arithmetic/evidence/step5_mul_capacity_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def compress(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
prior=json.loads(P.read_text());baseline=json.loads((B/'before_sha256.json').read_text());E.mkdir(parents=True,exist_ok=True)
for path,h in baseline.items():
 if (path.startswith('experiments/arithmetic/evidence/') and path!='experiments/arithmetic/evidence/README.md') or (path.startswith('experiments/arithmetic/') and 'freeze' in Path(path).name):assert sha(R/path)==h,path
reports=[]
for source in sorted(G.glob('*.json')):
 if source.name in ('summary.json','positions.json'):continue
 name=source.stem;compress(source,E/'reports'/(name+'.json.gz'));compress(source.with_suffix('.sv'),E/'rtl'/(name+'.sv.gz'));reports.append({'name':name,'report':rel(E/'reports'/(name+'.json.gz')),'rtl':rel(E/'rtl'/(name+'.sv.gz'))})
write(E/'report_index.json',reports)
for label,folder in [('mul',B/'rtl-validation'),('mac',B/'mac-validation')]:
 for name in ('items.json','vectors.txt','rtl-run.log','wrapper.sv','driver.cpp'):compress(folder/name,E/label/(name+'.gz'))
 copy(folder/'functional.json',E/label/'functional.json')
for name in ('analysis.json','sensitivity.json','positions.json','integration.json','integration-final.json','regressions.json'):
 if (B/name).exists():
  if name=='portable_checks.json':
   report=json.loads((B/name).read_text());report['original_summary_sha256']=sha(B/name)
   for row in report['checks']:
    if len(row.get('reason',''))>240:row['reason']=row['reason'][:240]+'...';row['reason_excerpt_only']=True
   write(E/name,report)
  else:copy(B/name,E/name)
circt=[]
for p in (B/'circt-final').glob('*.json'):
 if p.name in ('summary.json','positions.json'):continue
 r=json.loads(p.read_text());native=json.loads((G/p.name).read_text())
 for key in ('graph','stages','protocol','schedule_sha256','graph_sha256'):assert r[key]==native[key]
 rtl=p.with_suffix('.sv');assert sha(rtl)==r['rtl_sha256'];compress(rtl,E/'circt'/(rtl.name+'.gz'))
 circt.append({'name':p.stem,'native_report':rel(E/'reports'/(p.stem+'.json.gz')),'graph_sha256':r['graph_sha256'],'schedule_sha256':r['schedule_sha256'],'rtl':rel(E/'circt'/(rtl.name+'.gz')),'rtl_sha256':sha(rtl),'actual_full_report_sha256':sha(p),'full_report_scope':'graph/schedule equal to referenced native; report not duplicated'})
 old=E/'circt'/(p.name+'.gz')
 if old.exists():old.unlink()
write(E/'circt/index.json',circt)
for p in B.glob('*.failure.json'):compress(p,E/'request_failures'/(p.name+'.gz'))
for name in ('python-regressions.log','integration.log','integration-final.log'):
 if (B/name).exists():compress(B/name,E/(name+'.gz'))
# Preserve all actual charges, including development fixtures and timeout.
before=json.loads((B/'usage-before.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());assert after['entries'][:len(before['entries'])]==before['entries'];extra=after['entries'][len(before['entries']):];assert not usage(after['entries'])['pending']
prefix=R/prior['evidence_directory']/'usage_delta.json';original=R/'experiments/arithmetic/evidence/step4_interfaces_v1/usage_after.json'
# v2's prefix+delta is already protected, so do not copy the accumulated ledger.
write(E/'usage_delta.json',{'prefix':rel(prefix),'prefix_sha256':sha(prefix),'prefix_format':'chained_delta','entries':extra})
receipts=[];nonzero=[]
for entry in extra:
 path=Path(entry['command_record']);record=json.loads(path.read_text());physical=entry.get('admission_id')=='step5-bounded-wide-capacity-v1';target=(C if physical else E)/'commands'/entry['id'];copy(path,target/'command.json');copy(Path(record['gnu_time']),target/'GNU-time.txt')
 if physical:
  raw=Path(record['log']).read_bytes();lines=raw.splitlines(keepends=True);excerpt=b''.join(lines[:30])+b'\n[full log catalogued separately]\n'+b''.join(lines[-80:]);(target/'log.gz').write_bytes(gzip.compress(excerpt,mtime=0))
  write(target/'log-scope.json',{'scope':'first30_last80_lines; full file in capacity artifact catalog','full_log_sha256':hashlib.sha256(raw).hexdigest(),'full_log_bytes':len(raw),'member':Path(record['log']).name,'artifact_id':'step5-ASAP7-W'+('128' if '128' in entry['task_id'] else '64')+'-complete'})
  old=E/'commands'/entry['id']
  if old.exists():shutil.rmtree(old)
 else:compress(Path(record['log']),target/'log.gz')
 receipts.append({'id':entry['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt'),'log':rel(target/'log.gz')})
 if record['exit_code']!=0:nonzero.append({'id':entry['id'],'stage':entry['stage'],'purpose':entry['purpose'],'command':entry['command'],'exit_code':entry['exit_code'],'timed_out':record['timed_out']})
 if entry.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':
  assert record['timed_out'] and entry['CPU_time_s']==record['CPU_limit_s'] and not (target/'GNU-time.txt').read_text().strip()
 else:assert abs(cpu_seconds(target/'GNU-time.txt')-entry['CPU_time_s'])<1e-8
write(E/'command_index.json',receipts);write(E/'nonzero_commands.json',nonzero)
write(E/'resources.json',{'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'new_physical_calls':{s:sum(e['stage']==s for e in extra) for s in ('synth','grt','final')},'failed_leaves':len(nonzero),'timeout_leaves':sum(x['timed_out'] for x in nonzero),'global_caps_changed':False,'CPU_accounting_note':'GNU time actual leaves plus 2400s full reservation for timed-out grt with empty GNU time; sampled process CPU 2060.98s is separate evidence, not an exact refund','max_sampled_RSS_KiB':max(json.loads((R/x['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for x in receipts)})
# Source deltas; all unchanged source paths refer to exact parent snapshots.
paths={p for p in prior['files_sha256'] if (R/p).is_file()}
paths|={'rtlzz/src/backend/arithmetic_selection.cpp','rtlzz/src/backend/arithmetic_selection.hpp','rtlzz/src/backend/mul_templates.md','rtlzz/testv2/mul_template_test.cpp','experiments/arithmetic_dse/step5_analysis.py','experiments/arithmetic_dse/step5_evidence.py','regression/arithmetic_mul_templates.py','regression/arithmetic_mul_mac.py','experiments/arithmetic/evidence/README.md'}
snapshots={}
for path in sorted(paths):
 if prior['files_sha256'].get(path)==sha(R/path):snapshots[path]=prior['source_snapshots'][path]
 else:
  target=E/'source_delta'/path;copy(R/path,target);snapshots[path]=rel(target)
retired=set(prior['retired_active_paths'])|{p for p in baseline if not (R/p).exists()}
for path in sorted(retired):
 if path not in baseline:continue
 candidates=[B/'retired_source'/path,B/'previous_source'/path]
 source=next((p for p in candidates if p.exists() and sha(p)==baseline[path]),None)
 if source is not None:copy(source,E/'retired_source'/path)
# Exact final compiler source manifest from execution; earlier development IDs
# remain receipts, without claiming unavailable source variants can be replayed.
for name in ('release-generation.sources.json','release-native-build.sources.json','delivery-generation.sources.json'):
 if (B/name).exists():compress(B/name,E/(name+'.gz'))
for name in ('archive_step5.py','archive_capacity.py','analyze.py','final_checks.py','portable_checks.py','portable_checks.json','preservation_checks.py','preservation_checks.json'):
 if (B/name).exists():
  if name=='portable_checks.json':
   report=json.loads((B/name).read_text());report['original_summary_sha256']=sha(B/name)
   for row in report['checks']:
    if len(row.get('reason',''))>240:row['reason']=row['reason'][:240]+'...';row['reason_excerpt_only']=True
   write(E/name,report)
  else:copy(B/name,E/name)
capacity_index=C/'index.json';write(capacity_index,{'version':'step5-capacity-evidence-index-v1','files_sha256':{rel(p):sha(p) for p in sorted(C.rglob('*')) if p.is_file() and p!=capacity_index}})
index=E/'index.json';write(index,{'version':'step5-mul-evidence-index-v1','files_sha256':{rel(p):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}})
write(F,{'version':'mul-templates-freeze-v1','frozen_at':datetime.now(timezone.utc).isoformat(),'source_base':'49814a34d769b5d6cf28584a6103de1064a5d20f','rtlzz_base':'ed2919aa2d4db35bcbfa80b7c6159382995265ad','files_sha256':{p:sha(R/p) for p in sorted(paths)},'source_snapshots':snapshots,'historical_freezes':{**prior['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'source_delta'),rel(E/'retired_source'),*prior['historical_source_roots']],'retired_active_paths':sorted(retired),'evidence_directory':rel(E),'evidence_index':rel(index),'evidence_index_sha256':sha(index),'capacity_evidence':{'path':rel(C/'index.json'),'sha256':sha(C/'index.json'),'directory':rel(C)},'scope':'parameterized unsigned Mul/low product/MAC and C scheduling; ASAP7 wide capacity; 128grt timeout retained; no D inference/main matrix','old_freezes_modified':False})
print(json.dumps({'sources':len(paths),'new_source_snapshots':sum(p.startswith(rel(E)) for p in snapshots.values()),'software_evidence_files':len(json.loads(index.read_text())['files_sha256']),'software_package_bytes':sum(p.stat().st_size for p in E.rglob('*') if p.is_file())+F.stat().st_size,'new_usage':usage(extra)},indent=2))
