"""Append-only successor: source deltas, audit results and settled ledger delta."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil
import sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import usage,cpu_seconds
B=R/'build/step5-closure-20261031';E=R/'experiments/arithmetic/evidence/step5_mul_closure_v2';C=R/'experiments/arithmetic/evidence/step5_mul_capacity_v2';F=R/'experiments/arithmetic/mul_templates_freeze_v2.json';P=R/'experiments/arithmetic/mul_templates_freeze_v1.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def compress(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
parent=json.loads(P.read_text());baseline=json.loads((B/'before_sha256.json').read_text());before=json.loads((B/'backend_usage.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text())
assert after['entries'][:len(before['entries'])]==before['entries'];assert not usage(after['entries'])['pending'];extra=after['entries'][len(before['entries']):]
old_plan=(B/'lxy-plan-fix.md').read_text();new_plan=(R/'mission/lxy-plan-fix.md').read_text()
assert old_plan.split('# 第二章：',1)[1].split('# 第四章：',1)[0]==new_plan.split('# 第二章：',1)[1].split('# 第四章：',1)[0]
assert old_plan.split('# 第四章：',1)[1].rstrip()==new_plan.split('# 第四章：',1)[1].split('<a id="step5-closure-review">',1)[0].rstrip()
E.mkdir(parents=True,exist_ok=True)
preserved=[]
for path,h in baseline.items():
 if (path.startswith('experiments/arithmetic/evidence/') and path!='experiments/arithmetic/evidence/README.md') or (path.startswith('experiments/arithmetic/') and 'freeze' in Path(path).name):
  assert sha(R/path)==h,path;preserved.append(path)
preservation={'status':'passed','protected_files':len(preserved),'protected_freezes':sum(Path(x).parent==Path('experiments/arithmetic') and 'freeze' in Path(x).name for x in preserved),'protected_evidence_files':sum('/evidence/' in x for x in preserved),'plan_chapters_2_3_and_existing_chapter_4_preserved':True,'original_sha256':{p:baseline[p] for p in preserved},'new_navigation_files_not_old_frozen_members':['experiments/arithmetic/evidence/step5/README.md','experiments/arithmetic/evidence/step5_placement/README.md']}
(E/'preservation.json.gz').write_bytes(gzip.compress((json.dumps(preservation,indent=2)+'\n').encode(),mtime=0))
for source,name in [('positions_v2.json','positions_v2.json'),('sensitivity_v2.json','sensitivity_v2.json'),('historical_replay_inputs.json','historical_replay_inputs.json'),('historical_replay_final.json','historical_replay.json'),('software_checks.json','software_checks.json'),('software_validation.json','software_validation.json')]:copy(B/source,E/name)
for name in ('portable_checks.json','retest_validation.json','final_audit.json'):
 if (B/name).exists():copy(B/name,E/name)
for name in ('support.py','check_analysis.py','software_validation.py','timing_report.py','archive_capacity.py','archive_closure.py','portable_checks.py','retest_validation.py','final_software.py','final_audit.py'):
 if (B/name).exists():copy(B/name,E/'procedures'/name)
prefix=R/parent['evidence_directory']/'usage_delta.json'
write(E/'usage_delta.json',{'prefix':rel(prefix),'prefix_sha256':sha(prefix),'prefix_format':'chained_delta','entries':extra})
receipts=[];nonzero=[]
for entry in extra:
 path=Path(entry['command_record']);record=json.loads(path.read_text());target=E/'commands'/entry['id'];copy(path,target/'command.json');copy(Path(record['gnu_time']),target/'GNU-time.txt')
 raw=Path(record['log']).read_bytes()
 if entry['stage']=='grt':
  lines=raw.splitlines(keepends=True);(target/'log.gz').write_bytes(gzip.compress(b''.join(lines[:30])+b'\n[complete log in retest artifact catalog]\n'+b''.join(lines[-80:]),mtime=0));write(target/'log-scope.json',{'scope':'first30_last80 lines only','full_log_sha256':hashlib.sha256(raw).hexdigest(),'full_log_bytes':len(raw),'artifact_id':'step5-ASAP7-W128-retest-complete','member':Path(record['log']).name})
 else:compress(Path(record['log']),target/'log.gz')
 sources=Path(record['log']).with_suffix('.sources.json')
 if sources.exists():compress(sources,target/'sources.json.gz')
 receipts.append({'id':entry['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt'),'log':rel(target/'log.gz')})
 if record['exit_code']!=0:nonzero.append({'id':entry['id'],'stage':entry['stage'],'task_id':entry.get('task_id'),'exit_code':record['exit_code'],'timed_out':record['timed_out'],'scope':'retained actual development or physical failure; not omitted/refunded'})
write(E/'command_index.json',receipts);write(E/'nonzero_commands.json',nonzero)
launch=json.loads((B/'capacity-retest-admission.json').read_text())['starting_usage_live']
# Classify support by ledger position relative to the exact prelaunch prefix,
# including the separate backend environment/snapshot/report leaves.
launch_count=next(i for i in range(len(before['entries']),len(after['entries'])+1) if usage(after['entries'][:i])==launch)
post_entries=after['entries'][launch_count:];post_support=[e for e in post_entries if e['stage'] is None]
envelope=json.loads((B/'capacity-retest-admission.json').read_text())['support_envelope'];support=usage(post_support)
assert support['walltime_s']<=envelope['walltime_s'] and support['CPU_time_s']<=envelope['CPU_time_s']
write(E/'resources.json',{'baseline_usage':usage(before['entries']),'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'new_physical_calls':{s:sum(e['stage']==s for e in extra) for s in ('synth','grt','final')},'failed_leaves':len(nonzero),'post_admission_support_usage':support,'post_admission_support_envelope':envelope,'post_admission_support_envelope_met':True,'prelaunch_software_support_usage':usage(after['entries'][len(before['entries']):launch_count]),'global_caps_changed':False,'max_sampled_RSS_KiB':max(json.loads((R/x['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for x in receipts),'CPU_note':'GNU time actual where present; timeout with missing GNU time charged full CPU reservation, sampled tree CPU kept separate'})
paths={p for p in parent['files_sha256'] if (R/p).is_file()}
paths|={'rtlzz/src/backend/mul_contract.cpp','rtlzz/src/backend/mul_contract.hpp','rtlzz/testv2/arithmetic_report_reader.hpp','rtlzz/testv2/mul_replay_test.cpp','experiments/arithmetic_dse/capacity_retest.py','experiments/arithmetic_dse/closure_evidence.py','experiments/arithmetic_dse/block_tree_evidence.py','experiments/arithmetic_dse/exact_analysis.py','experiments/arithmetic_dse/configs/exact_analysis_v2.json','experiments/arithmetic_dse/analysis_protocol.md','regression/arithmetic_analysis.py','regression/arithmetic_block_evidence.py','regression/arithmetic_capacity_retest.py','experiments/arithmetic/evidence/step5/README.md','experiments/arithmetic/evidence/step5_placement/README.md'}
prior_identity={**parent['files_sha256'],**baseline}
write(E/'file_changes.json',{'scope':'active source/document changes in this closure relative to before_sha256 or exact v1 parent identity; generated evidence separately indexed; prior dirty step5 implementation preserved','files':[{'path':p,'kind':'new' if p not in prior_identity else 'modified','before_sha256':prior_identity.get(p),'after_sha256':sha(R/p)} for p in sorted(paths) if prior_identity.get(p)!=sha(R/p)],'generated_evidence_packages':[rel(E),rel(C)],'ledger':{'path':'experiments/arithmetic/backend_usage.json','mode':'append only; preserved prefix plus usage_delta'}})
snapshots={}
for path in sorted(paths):
 if parent['files_sha256'].get(path)==sha(R/path):snapshots[path]=parent['source_snapshots'][path]
 else:target=E/'source_delta'/path;copy(R/path,target);snapshots[path]=rel(target)
index=E/'index.json';write(index,{'version':'step5-closure-evidence-index-v2','files_sha256':{rel(p):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}})
ci=C/'index.json';write(ci,{'version':'step5-capacity-evidence-index-v2','files_sha256':{rel(p):sha(p) for p in sorted(C.rglob('*')) if p.is_file() and p!=ci}})
write(F,{'version':'mul-templates-freeze-v2','frozen_at':datetime.now(timezone.utc).isoformat(),'source_base':parent['source_base'],'rtlzz_base':parent['rtlzz_base'],'files_sha256':{p:sha(R/p) for p in sorted(paths)},'source_snapshots':snapshots,'historical_freezes':{**parent['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'source_delta'),*parent['historical_source_roots']],'retired_active_paths':parent['retired_active_paths'],'evidence_directory':rel(E),'evidence_index':rel(index),'evidence_index_sha256':sha(index),'capacity_evidence':{'path':rel(ci),'sha256':sha(ci),'directory':rel(C)},'scope':'strengthened certificates and exact analysis only; circuit/schedule unchanged; one same-circuit 3600s post-synth->grt retest; no new synthesis/final/original/main matrix','old_freezes_modified':False,'physical_results_inherited':'all v1 accepted data/RTL and old timeout retained; new task is separate successor evidence','remote_artifact_retention_confirmed':False})
print(json.dumps({'software_package_bytes':sum(p.stat().st_size for p in E.rglob('*') if p.is_file())+F.stat().st_size,'capacity_package_bytes':sum(p.stat().st_size for p in C.rglob('*') if p.is_file()),'files':len(json.loads(index.read_text())['files_sha256']),'new_usage':usage(extra)},indent=2))
