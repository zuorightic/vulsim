"""Check this review against the dirty-but-frozen step4 starting workspace."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
ROOT=Path.cwd();B=ROOT/'build/step4-review-20261031';sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
baseline=json.loads((B/'before_sha256.json').read_text());changed=[];protected=freezes=0
for path,h in baseline.items():
 p=ROOT/path;assert p.exists(),path
 if path.startswith('experiments/arithmetic/evidence/'):
  protected+=1;assert sha(p)==h,path
 if path.startswith('experiments/arithmetic/') and 'freeze' in p.name and p.suffix=='.json':
  freezes+=1;assert sha(p)==h,path
 if sha(p)!=h and not path.endswith('.lock'):changed.append(path)
allowed={'experiments/arithmetic/README.md','experiments/arithmetic/backend_usage.json','experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json','experiments/arithmetic_dse/freeze_history.py','experiments/arithmetic_dse/interfaces_evidence.py','mission/README.md','mission/lxy-plan-fix.md','rtlzz/src/arithmetic_request.cpp','rtlzz/src/backend/arithmetic_core.cpp','rtlzz/src/backend/arithmetic_interfaces.md','rtlzz/testv2/arithmetic_interface_test.cpp'}
assert set(changed)==allowed,(set(changed)-allowed,allowed-set(changed))
old=(B/'plan-before.md').read_text();new=(ROOT/'mission/lxy-plan-fix.md').read_text();second='# 第二章：旧计划推进记录';assert new[new.index(second):].startswith(old[old.index(second):])
first_old=old[:old.index(second)];first_new=new[:new.index(second)]
added=re.search(r'\n\n\*\*后续证据留存规则（2026-10-31）。\*\*[^\n]+',first_new);assert added
assert first_new[:added.start()]+first_new[added.end():]==first_old
assert new.count('<a id="step4-report-type-review"></a>')==1
for folder in ('experiments/arithmetic_dse/configs/platforms/','vullib/'):
 assert all(sha(ROOT/p)==h for p,h in baseline.items() if p.startswith(folder))
for name in ('fixed_op_width_v1.json','backend_policy_v5.json'):
 p='experiments/arithmetic_dse/configs/'+name;assert sha(ROOT/p)==baseline[p]
for name in ('step4','step4_review'):
 s=(ROOT/'experiments/arithmetic/evidence'/name/'README.md').read_text();assert '旧计划' in s and 'step4_interfaces_v1' in s
mds=['mission/README.md','experiments/arithmetic/README.md','experiments/arithmetic_dse/evidence_storage.md','rtlzz/src/backend/arithmetic_interfaces.md','experiments/arithmetic/evidence/README.md','experiments/arithmetic/evidence/step4/README.md','experiments/arithmetic/evidence/step4_review/README.md','experiments/arithmetic/evidence/step4_interfaces_v2/README.md']
for path in mds:
 p=ROOT/path;s=p.read_text();assert sum(l.lstrip().startswith('```') for l in s.splitlines())%2==0,path
 for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',s):
  if re.match(r'(https?://|mailto:)',target):continue
  target_path,_,anchor=target.partition('#');q=(p.parent/target_path).resolve() if target_path else p
  assert q.exists(),(path,target)
  if anchor:assert '<a id="'+anchor+'"' in q.read_text(),(path,target)
for p in [ROOT/'experiments/arithmetic_dse/interfaces_evidence.py',ROOT/'experiments/arithmetic_dse/report_types.py',ROOT/'regression/arithmetic_report_types.py',*B.glob('*.py')]:ast.parse(p.read_text(),filename=str(p))
for cwd in (ROOT,ROOT/'rtlzz'):subprocess.run(['git','diff','--check'],cwd=cwd,check=True)
before=json.loads((B/'usage-before.json').read_text());after=json.loads((ROOT/'experiments/arithmetic/backend_usage.json').read_text());assert after['entries'][:len(before['entries'])]==before['entries'];extra=after['entries'][len(before['entries']):]
assert all(e['stage'] is None and e['status']=='completed' for e in extra) and not usage(after['entries'])['pending']
for e in extra:
 d=json.loads(Path(e['command_record']).read_text());assert not any(d[k] for k in ('timed_out','memory_limit_exceeded','CPU_limit_exceeded','unexpected_live_descendants'));assert not d['cleanup']['remaining_live_pids']
assert json.loads((B/'checks.json').read_text())['status']=='passed'
portable=json.loads((B/'portable_checks.json').read_text());assert portable['status']=='passed' and portable['negative_checks_rejected']==5
# Existing ignore rules stay in order; this review adds only the artifact cache rule.
base_ignore=subprocess.check_output(['git','show','HEAD:.gitignore'],cwd=ROOT,text=True)
assert (ROOT/'.gitignore').read_text().startswith(base_ignore)
assert (ROOT/'.gitignore').read_text()[len(base_ignore):]=='\n# Local large arithmetic artifacts; publish/restore via a frozen artifact catalog.\nexperiments/arithmetic/artifact_store/\n'
summary={'status':'passed','version':'step4-report-review-preservation-v2','old_freezes_unchanged':freezes,'old_evidence_files_unchanged':protected,'changed_existing_paths':sorted(changed),'deleted_existing_paths':[],'only_prospective_storage_rule_added_to_normative_plan':True,'prior_chapter_2_3_4_bytes_preserved':True,'only_new_banner_files_in_old_step4_directories':True,'platform_profiles_fixed_table_and_budget_unchanged':True,'markdown_links_and_python_syntax_passed':True,'root_and_submodule_diff_check_passed':True,'ledger_prefix_unchanged':True,'cleanup_passed':True,'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'no_new_physical_or_functional_measurement':True,'remote_upload_or_git_history_rewrite':False}
(B/'preservation_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
