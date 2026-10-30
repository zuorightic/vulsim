from pathlib import Path
import hashlib,json,re,subprocess
R=Path.cwd();B=R/'build/step3-sdc-parser-20261030';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prior=json.loads((B/'before_sha256.json').read_text())
changed=[p for p,h in prior.items() if not (R/p).is_file() or sha(R/p)!=h]
allowed={'mission/README.md','mission/lxy-plan-fix.md','experiments/arithmetic/README.md','experiments/arithmetic/backend_usage.json','experiments/arithmetic_dse/backend.py','experiments/arithmetic_dse/backend/README.md','experiments/arithmetic_dse/platform_evidence.py','experiments/arithmetic_dse/platforms.py','experiments/arithmetic_dse/sdc.py','experiments/arithmetic_dse/freeze_history.py','regression/arithmetic_sdc.py','regression/arithmetic_backend.py'}
assert not set(changed)-allowed,set(changed)-allowed
assert not any('/evidence/' in p or ('freeze' in p and p.endswith('.json')) for p in changed)
old=(B/'plan-before.md').read_text();new=(R/'mission/lxy-plan-fix.md').read_text()
def section(text,start,end):return text[text.index(start):text.index(end,text.index(start))]
checks={}
checks['chapters_2_3_unchanged']=section(old,'# 第二章：','# 第四章：')==section(new,'# 第二章：','# 第四章：')
checks['fourth_chapter_steps_1_2_unchanged']=section(old,'# 第四章：','<a id="step3-platform-acceptance"')==section(new,'# 第四章：','<a id="step3-platform-acceptance"')
start='<a id="step3-sdc-correction">';checks['P1_record_3_9_unchanged']=old[old.index(start):].rstrip()==new[new.index(start):new.index('<a id="step3-validator-closure">')].rstrip()
for a,b in [('## 7. 代价、训练、位置选择与资源','## 8. 案例矩阵'),('## 8. 案例矩阵','## 9. 正确性'),('## 9. 正确性','## 10. 按依赖'),('### 10.10 阶段里程碑','### 10.11 接口预留')]:checks['unchanged_'+a]=section(old,a,b)==section(new,a,b)
checks['all_old_freezes_and_evidence_immutable']=True
checks['policy_unchanged']=sha(R/'experiments/arithmetic_dse/configs/backend_policy_v5.json')==prior['experiments/arithmetic_dse/configs/backend_policy_v5.json']
checks['four_effective_profiles_unchanged']=all(sha(R/p)==prior[p] for p in prior if '/configs/platforms/' in p)
checks['rtlzz_unchanged']=not subprocess.check_output(['git','-C','rtlzz','status','--short'],text=True) and subprocess.check_output(['git','-C','rtlzz','rev-parse','HEAD'],text=True).strip()=='2d2ae4083655d5322c28ccd90fd897b291cb51b4'
checks['no_compiler_or_vullib_edits']=not any(p.startswith(('src/','rtlzz/','vullib/')) for p in subprocess.check_output(['git','diff','--name-only'],text=True).splitlines())
f=json.loads((R/'experiments/arithmetic/backend_freeze_v7.json').read_text())
for p,h in f['files_sha256'].items():
 assert sha(R/p)==h,p
 if p.endswith('.py'):compile((R/p).read_text(),p,'exec')
checks['source_hashes_and_python_syntax']=True
for relative in ('mission/README.md','mission/lxy-plan-fix.md','experiments/arithmetic/README.md','experiments/arithmetic_dse/backend/README.md','experiments/arithmetic_dse/backend/handoff_checks.md','experiments/arithmetic/evidence/step3_platforms_v3/README.md'):
 path=R/relative;text=path.read_text();fence=False;columns=None
 for line in text.splitlines():
  if line.startswith('```'):fence=not fence;columns=None;continue
  if fence:continue
  if line.startswith('|') and line.endswith('|'):
   count=len(re.findall(r'(?<!\\)\|',line));columns=count if columns is None else columns;assert count==columns,(relative,line)
  else:columns=None
 assert not fence,relative
 for target in re.findall(r'\]\(([^)]+)\)',text):
  if target.startswith(('http:','https:','app:')):continue
  name,_,anchor=target.partition('#');dest=(path.parent/name).resolve() if name else path;assert dest.exists(),(relative,target)
  if anchor:assert 'id="'+anchor+'"' in dest.read_text(),(relative,target)
checks['markdown_tables_fences_links_anchors']=True
checks['diff_check_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
before=json.loads((B/'usage-before.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text())
checks['ledger_prefix_immutable']=after['entries'][:len(before['entries'])]==before['entries']
extra=after['entries'][len(before['entries']):];checks['no_physical_calls_added']=all(e['stage'] is None for e in extra)
checks['no_pending_reservations']=all(e['status']!='reserved' for e in after['entries'])
assert all(checks.values()),checks
report={'status':'passed','before_hashes_checked':len(prior),'changed_existing_paths':changed,'checks':checks,'new_EDA_calls':0}
(B/'static_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
