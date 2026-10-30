from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path.cwd();BUILD=ROOT/'build/step3-sdcfix-20261030'
before=json.loads((BUILD/'before_sha256.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=[r for r,h in before.items() if not (ROOT/r).is_file() or sha(ROOT/r)!=h]
allowed={'mission/README.md','mission/lxy-plan-fix.md','experiments/arithmetic/README.md',
 'experiments/arithmetic/backend_usage.json','experiments/arithmetic_dse/backend.py',
 'experiments/arithmetic_dse/backend/README.md','experiments/arithmetic_dse/backend/constraints.sdc',
 'experiments/arithmetic_dse/platform_evidence.py','experiments/arithmetic_dse/platform_probe.py',
 'experiments/arithmetic_dse/freeze_history.py','regression/arithmetic_backend.py'}
assert not set(changed)-allowed,set(changed)-allowed
old=(BUILD/'plan-before.md').read_text();new=(ROOT/'mission/lxy-plan-fix.md').read_text()
def part(text,start,end):return text[text.index(start):text.index(end,text.index(start))]
checks={}
checks['previous_chapters_2_3_unchanged']=part(old,'# 第二章：','# 第四章：')==part(new,'# 第二章：','# 第四章：')
checks['prior_steps_1_2_unchanged']=part(old,'# 第四章：','<a id="step3-platform-acceptance"')==part(new,'# 第四章：','<a id="step3-platform-acceptance"')
for a,b in [('## 7. 代价、训练、位置选择与资源','## 8. 案例矩阵'),('## 8. 案例矩阵','## 9. 正确性'),('## 9. 正确性','## 10. 按依赖'),('### 10.10 阶段里程碑','### 10.11 接口预留')]:checks['unchanged_'+a]=part(old,a,b)==part(new,a,b)
checks['all_prior_freezes_and_evidence_preserved']=not any('/evidence/' in r or r.endswith('freeze_v5.json') for r in changed)
checks['vullib_and_rtlzz_unchanged']=not any(r.startswith(('vullib/','rtlzz/')) for r in changed)
checks['submodule_clean']=not subprocess.check_output(['git','-C','rtlzz','status','--short'],text=True)
checks['budget_caps_unchanged']=sha(ROOT/'experiments/arithmetic_dse/configs/backend_policy_v5.json')==before['experiments/arithmetic_dse/configs/backend_policy_v5.json']
f=json.loads((ROOT/'experiments/arithmetic/backend_freeze_v6.json').read_text())
for rel,h in f['files_sha256'].items():
 assert sha(ROOT/rel)==h,rel
 if rel.endswith('.py'):compile((ROOT/rel).read_text(),rel,'exec')
checks['current_frozen_source_hashes_and_python_syntax']=True
checks['prior_backend_v5_acceptance_explicitly_revoked']=f['supersedes']['previous_acceptance_valid'] is False
checks['six_new_tasks_and_ASAP7_carry_forward']=f['rerun_platforms']==['nangate45','sky130hd','gf180'] and f['carried_forward_platforms']==['asap7']
for rel in ('mission/README.md','mission/lxy-plan-fix.md','experiments/arithmetic/README.md','experiments/arithmetic_dse/backend/README.md'):
 s=(ROOT/rel).read_text();fence=False;cols=None
 for line in s.splitlines():
  if line.startswith('```'):fence=not fence;cols=None;continue
  if fence:continue
  if line.startswith('|') and line.endswith('|'):
   count=len(re.findall(r'(?<!\\)\|',line))
   if cols is None:cols=count
   assert count==cols,(rel,line)
  else:cols=None
 assert not fence,rel
checks['markdown_tables_and_fences']=True
for rel in ('mission/README.md','experiments/arithmetic/README.md'):
 path=ROOT/rel
 for target in re.findall(r'\]\(([^)]+)\)',path.read_text()):
  if target.startswith(('http:','https:','app:')):continue
  name,_,anchor=target.partition('#');dest=(path.parent/name).resolve() if name else path
  assert dest.exists(),(rel,target)
  if anchor:assert f'id="{anchor}"' in dest.read_text(),(rel,target)
checks['navigation_links_and_stable_anchors']=True
checks['diff_check_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
assert all(checks.values()),checks
report={'status':'passed','checks':checks,'prior_file_hashes_compared':len(before),'changed_existing_paths':changed,
        'new_experimental_leaf_commands':0,'new_EDA_invocations':0}
(BUILD/'static_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
