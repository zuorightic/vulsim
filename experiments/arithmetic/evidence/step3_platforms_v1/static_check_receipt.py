from pathlib import Path
import hashlib,json,re,subprocess
ROOT=Path.cwd();build=ROOT/'build/step3-platforms-20261030'
before=json.loads((build/'before_sha256.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
changed=[]
for rel,expected in before.items():
    p=ROOT/rel
    if not p.is_file() or sha(p)!=expected:changed.append(rel)
allowed={'experiments/arithmetic/README.md','experiments/arithmetic/backend_usage.json',
'experiments/arithmetic_dse/backend.py','experiments/arithmetic_dse/backend/README.md',
'experiments/arithmetic_dse/backend/asap7.mk','experiments/arithmetic_dse/backend/constraints.sdc',
'experiments/arithmetic_dse/backend/environment.mk','experiments/arithmetic_dse/budget.py',
'experiments/arithmetic_dse/configs/implementation_migration_v1.json','experiments/arithmetic_dse/evidence.py',
'experiments/arithmetic_dse/freeze_history.py','experiments/arithmetic_dse/mul_split_evidence.py',
'experiments/arithmetic_dse/physical_control.py','experiments/arithmetic_dse/run.py',
'mission/README.md','mission/lxy-plan-fix.md','regression/arithmetic_backend.py'}
assert set(changed)==allowed,(set(changed)-allowed,allowed-set(changed))
old=(build/'plan-before.md').read_text();new=(ROOT/'mission/lxy-plan-fix.md').read_text()
def part(text,start,end):return text[text.index(start):text.index(end,text.index(start))]
checks={}
checks['chapters_2_and_3_byte_preserved']=(part(old,'# 第二章：','# 第四章：')==part(new,'# 第二章：','# 第四章：'))
checks['prior_chapter_4_steps_byte_preserved']=new[new.index('# 第四章：'):].startswith(old[old.index('# 第四章：'):])
for start,end in [('## 7. 代价、训练、位置选择与资源','## 8. 案例矩阵'),('## 8. 案例矩阵','## 9. 正确性'),('## 9. 正确性','## 10. 按依赖'),('### 10.10 阶段里程碑','### 10.11 接口预留')]:
    checks['unchanged_'+start]=part(old,start,end)==part(new,start,end)
checks['all_old_freezes_and_evidence_unchanged']=not any((('freeze' in rel or '/evidence/' in rel) and rel!='experiments/arithmetic_dse/freeze_history.py') for rel in changed)
checks['rtlzz_unchanged']=not any(rel.startswith('rtlzz/') for rel in changed)
checks['submodule_worktree_clean']=not subprocess.check_output(['git','-C','rtlzz','status','--short'],text=True)
checks['retired_active_asap7_make_absent']=not (ROOT/'experiments/arithmetic_dse/backend/asap7.mk').exists()
budget=(ROOT/'experiments/arithmetic_dse/budget.py').read_text()
checks['old_budget_functions_retired']=all('def '+name+'(' not in budget for name in ['plan_cost','planning_status','required_data_plan'])
checks['policy_caps_unchanged']=sha(ROOT/'experiments/arithmetic_dse/configs/backend_policy_v5.json')==before['experiments/arithmetic_dse/configs/backend_policy_v5.json']
freeze=json.loads((ROOT/'experiments/arithmetic/backend_freeze_v5.json').read_text())
for rel in freeze['files_sha256']:
    if rel.endswith('.py'):compile((ROOT/rel).read_text(),rel,'exec')
checks['current_python_syntax']=True
for rel in ['mission/README.md','experiments/arithmetic/README.md','experiments/arithmetic_dse/backend/README.md','mission/lxy-plan-fix.md']:
    s=(ROOT/rel).read_text();fence=False;columns=None
    for line in s.splitlines():
        if line.startswith('```'):fence=not fence;columns=None;continue
        if fence:continue
        if line.startswith('|') and line.endswith('|'):
            count=len(re.findall(r'(?<!\\)\|',line))
            if columns is None:columns=count
            assert count==columns,(rel,line)
        else:columns=None
    assert not fence,rel
checks['markdown_fences_and_table_columns']=True
link_inputs={ROOT/'mission/README.md':(ROOT/'mission/README.md').read_text(),
 ROOT/'experiments/arithmetic/README.md':(ROOT/'experiments/arithmetic/README.md').read_text(),
 ROOT/'mission/lxy-plan-fix.md':new[new.index('<a id="step3-platform-acceptance"'):],
 ROOT/'experiments/arithmetic/evidence/step3_platforms_v1/README.md':(ROOT/'experiments/arithmetic/evidence/step3_platforms_v1/README.md').read_text()}
for doc,text in link_inputs.items():
    for target in re.findall(r'\]\(([^)]+)\)',text):
        if target.startswith(('http:','https:','app:')):continue
        name,_,anchor=target.partition('#');path=(doc.parent/name).resolve() if name else doc
        assert path.exists(),(doc,target)
        if anchor:assert f'id="{anchor}"' in path.read_text(),(doc,target)
checks['new_and_navigation_links_and_stable_anchors']=True
checks['diff_whitespace_clean']=subprocess.run(['git','diff','--check'],capture_output=True).returncode==0
assert all(checks.values()),{k:v for k,v in checks.items() if not v}
report={'status':'passed','checks':checks,'tracked_file_hashes_compared':len(before),'changed_tracked_paths':changed,
        'static_checks_only':True,'new_EDA_invocations':0}
(build/'static_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
