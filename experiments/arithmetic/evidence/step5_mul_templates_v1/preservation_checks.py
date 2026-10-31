"""Scope, immutable payload and final software/capacity evidence preservation."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
R=Path.cwd();B=R/'build/step5-parameterized-20261031';sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();baseline=json.loads((B/'before_sha256.json').read_text());changed=[];retired=[];oldpayload=oldfreezes=0
for path,h in baseline.items():
 p=R/path
 if path.startswith('experiments/arithmetic/evidence/') and path!='experiments/arithmetic/evidence/README.md':oldpayload+=1;assert p.exists() and sha(p)==h,path
 if path.startswith('experiments/arithmetic/') and 'freeze' in p.name and p.suffix=='.json':oldfreezes+=1;assert p.exists() and sha(p)==h,path
 if not p.exists():retired.append(path)
 elif sha(p)!=h:changed.append(path)
old=(B/'plan-before.md').read_text();new=(R/'mission/lxy-plan-fix.md').read_text();marker='# 第二章：旧计划推进记录';assert new[new.index(marker):].startswith(old[old.index(marker):]);assert new.count('<a id="step5-mul-template-acceptance"></a>')==1
old_first=old[:old.index(marker)].splitlines();new_first=new[:new.index(marker)].splitlines();assert len(old_first)==len(new_first)
changes=[(a,b) for a,b in zip(old_first,new_first) if a!=b];assert len(changes)==2
assert changes[0][0].startswith('保留九步骤编号') and changes[1][0]=='**历史状态：32×32 split16及旧位置补验完成；参数化和新C需重新验收。**'
for path,h in baseline.items():
 if path.startswith('experiments/arithmetic_dse/configs/platforms/') or path in ['experiments/arithmetic_dse/configs/fixed_op_width_v1.json','experiments/arithmetic_dse/configs/backend_policy_v5.json','experiments/arithmetic_dse/configs/selection_protocol_v2.json','experiments/arithmetic_dse/configs/cost_sensitivity_v1.json','experiments/arithmetic/cases_v2.json']:
  assert sha(R/path)==h,path
for folder in ('rtlzz/src','rtlzz/main','rtlzz/testv2'):
 for p in (R/folder).rglob('*'):
  if p.is_file() and p.suffix in ('.cpp','.hpp','.h'):
   assert not re.search(r'\b(use_simple_cost|arithmetic_candidate|expand32|mul32_split16)\b',p.read_text()),p
for p in (R/'experiments/arithmetic_dse').glob('*.py'):
 if p.name=='freeze_history.py':continue
 assert not re.search(r'from \.simple_cost|from \.placement_analysis',p.read_text()),p
for cwd in (R,R/'rtlzz'):subprocess.run(['git','diff','--check'],cwd=cwd,check=True)
for p in [*B.glob('*.py'),R/'experiments/arithmetic_dse/step5_evidence.py',R/'experiments/arithmetic_dse/step5_analysis.py',R/'regression/arithmetic_mul_mac.py',R/'regression/arithmetic_mul_templates.py']:ast.parse(p.read_text(),filename=str(p))
for path in ['mission/README.md','experiments/arithmetic/README.md','experiments/arithmetic/evidence/README.md','rtlzz/src/backend/mul_templates.md','rtlzz/src/backend/arithmetic_interfaces.md','experiments/arithmetic/evidence/step5_mul_templates_v1/README.md','experiments/arithmetic/evidence/step5_mul_capacity_v1/README.md']:
 p=R/path;s=p.read_text();assert sum(l.lstrip().startswith('```') for l in s.splitlines())%2==0,path
 for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',s):
  if re.match(r'(https?://|mailto:)',target):continue
  name,_,anchor=target.partition('#');q=(p.parent/name).resolve() if name else p;assert q.exists(),(path,target)
  if anchor:assert '<a id="'+anchor+'"' in q.read_text(),(path,target)
ledger=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());before=json.loads((B/'usage-before.json').read_text());assert ledger['entries'][:len(before['entries'])]==before['entries'];extra=ledger['entries'][len(before['entries']):];assert not usage(ledger['entries'])['pending']
assert {s:sum(e['stage']==s for e in extra) for s in ('synth','grt','final')}=={'synth':2,'grt':2,'final':0}
for e in extra:
 d=json.loads(Path(e['command_record']).read_text());assert not d['cleanup']['remaining_live_pids'] and not d['unexpected_live_descendants']
 if d['timed_out']:assert e['task_id']=='asap7-mul128-C-capacity-v1' and e['stage']=='grt' and e['CPU_accounting']=='full_reservation_missing_CPU_evidence'
 else:assert not d['memory_limit_exceeded'] and not d['CPU_limit_exceeded']
for name,expected in [('portable_checks.json','passed'),('analysis.json','passed'),('integration-final.json','passed'),('regressions.json','passed')]:assert json.loads((B/name).read_text())['status']==expected
for source,h in json.loads((B/'release-generation.sources.json').read_text()).items():assert sha(R/source)==h,source
# Numerical execution predates report/invariant refinements, with all actual
# executable SV bytes unchanged; verify this directly rather than infer it.
for p in (B/'generated-3').glob('*.sv'):assert p.read_bytes()==(B/'release'/p.name).read_bytes()
summary={'status':'passed','version':'step5-preservation-v1','old_frozen_payload_files_unchanged':oldpayload,'old_freezes_unchanged':oldfreezes,'active_navigation_source_updated_with_parent_snapshot':'experiments/arithmetic/evidence/README.md','changed_existing_paths':changed,'retired_paths':retired,'prior_chapter_2_3_4_bytes_preserved':True,'normative_plan_only_two_status_paragraphs_changed':True,'profiles_weights_budget_selection_and_sensitivity_unchanged':True,'legacy_public_implementation_scan_passed':True,'Python_syntax_links_fences_and_both_diff_checks_passed':True,'executed_compiler_sources_match_current':True,'88_numerically_executed_SV_files_match_current':True,'no_pending_or_live_descendants':True,'timeout_CPU_conservatively_settled':True,'new_usage':usage(extra),'cumulative_usage':usage(ledger['entries'])}
(B/'preservation_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
