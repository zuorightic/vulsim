"""Read-only step4 scope and preservation audit; writes only its new result."""
from pathlib import Path
import ast,hashlib,json,re,subprocess,sys
ROOT=Path.cwd();B=ROOT/'build/step4-interfaces-20261030';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.budget import usage
before=json.loads((B/'before_sha256.json').read_text())
changed=[];deleted=[];old_evidence=old_freezes=0
allowed={
 'experiments/arithmetic/README.md','experiments/arithmetic/backend_usage.json',
 'experiments/arithmetic_dse/configs/implementation_migration_v1.json',
 'experiments/arithmetic_dse/freeze_history.py','experiments/arithmetic_dse/platform_evidence.py',
 'mission/README.md','mission/lxy-plan-fix.md',
 'src/rtlgen.h','src/rtlgen_rtlzz.cpp','src/rtlzz_bridge.cpp','src/rtlzz_bridge.hpp','tools/vulrtlgen.cpp',
 'rtlzz/README.md','rtlzz/main/main.cpp','rtlzz/src/backend/beir.hpp','rtlzz/src/backend/pipeline.cpp','rtlzz/src/backend/pipeline.hpp',
 'rtlzz/src/pipelinev2/PipelineV2.cpp','rtlzz/src/pipelinev2/PipelineV2.h','rtlzz/src/rtlzz.cpp','rtlzz/src/rtlzz.hpp'}
for relative,expected in before.items():
    p=ROOT/relative
    if not p.exists():deleted.append(relative)
    elif sha(p)!=expected:changed.append(relative)
    if relative.startswith('experiments/arithmetic/evidence/'):
        old_evidence+=1;assert p.is_file() and sha(p)==expected,relative
    if relative.startswith('experiments/arithmetic/') and 'freeze' in p.name and p.suffix=='.json':
        old_freezes+=1;assert p.is_file() and sha(p)==expected,relative
assert not deleted and set(changed)==allowed,(deleted,set(changed)-allowed,allowed-set(changed))
old=(B/'plan-before.md').read_text();new=(ROOT/'mission/lxy-plan-fix.md').read_text();marker='# 第二章：旧计划推进记录'
assert new[new.index(marker):].startswith(old[old.index(marker):])
first_old=old[:old.index(marker)];first_new=new[:new.index(marker)]
# Only two status paragraphs may change in the normative first chapter.
a=first_old.splitlines();b=first_new.splitlines();assert len(a)==len(b)
line_changes=[(i+1,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
assert len(line_changes)==2
assert line_changes[0][1].startswith('保留九步骤编号以追溯实施记录。')
assert line_changes[1][1]=='**历史状态：完成；受影响接口需回归。**'
assert 'step4-interface-acceptance' not in old
assert len(re.findall(r'<a id="step4-interface-acceptance"></a>',new))==1
for folder in ('experiments/arithmetic_dse/configs/platforms','vullib'):
    assert all(sha(ROOT/k)==v for k,v in before.items() if k.startswith(folder+'/'))
for relative in ('experiments/arithmetic_dse/configs/fixed_op_width_v1.json','experiments/arithmetic_dse/configs/backend_policy_v5.json','experiments/arithmetic/cases_v2.json'):
    assert sha(ROOT/relative)==before[relative]
for cwd in (ROOT,ROOT/'rtlzz'):subprocess.run(['git','diff','--check'],cwd=cwd,check=True)
# Current feature enum identities come from the actual compiler header.
text=re.sub(r'//[^\n]*','',(ROOT/'rtlzz/src/backend/beir.hpp').read_text());schema=json.loads((ROOT/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text())
for name,key in [('OperationKind','operation_kinds'),('OpCode','opcodes'),('OperandKind','operand_kinds'),('PortDirection','port_directions')]:
    body=re.search(r'enum class '+name+r'\s*\{([^}]+)\}',text).group(1);values=[v.strip() for v in body.split(',') if v.strip()]
    assert {v:i for i,v in enumerate(values)}==schema[key],name
pyfiles=list((ROOT/'experiments/arithmetic_dse').glob('*.py'))+[ROOT/'regression/arithmetic_interfaces.py',B/'portable_checks.py',Path(__file__),B/'archive_interfaces.py']
for p in pyfiles:ast.parse(p.read_text(),filename=str(p))
for p in (ROOT/'experiments/arithmetic_dse/configs').rglob('*.json'):json.loads(p.read_text())
# New/edited document targets; old frozen prose is not reauthored for lint.
docs=[ROOT/'mission/README.md',ROOT/'experiments/arithmetic/README.md',ROOT/'rtlzz/src/backend/arithmetic_interfaces.md',ROOT/'experiments/arithmetic/evidence/step4_interfaces_v1/README.md']
for p in docs:
    s=p.read_text();assert sum(line.lstrip().startswith('```') for line in s.splitlines())%2==0,p
    for target in re.findall(r'\[[^\]\n]*\]\(([^)\n]+)\)',s):
        if re.match(r'(https?://|mailto:)',target):continue
        path,_,anchor=target.partition('#');q=(p.parent/path).resolve() if path else p
        assert q.exists(),(p,target)
        if anchor and '<a id="'+anchor+'"' not in q.read_text():
            raise AssertionError('new document link lacks explicit stable anchor: '+str((p,target)))
block=new[len(old):] if new.startswith(old) else new[new.index('<a id="step4-interface-acceptance"></a>'):]
assert not any(phrase in block for phrase in ('待收尾','由本节收尾表','数量以随仓库'))
assert sum(line.lstrip().startswith('```') for line in block.splitlines())%2==0
for line in block.splitlines():
    if line.startswith('|'):assert line.count('|') in (3,5),line
baseline=json.loads((B/'usage-before.json').read_text());ledger=json.loads((ROOT/'experiments/arithmetic/backend_usage.json').read_text());assert ledger['entries'][:len(baseline['entries'])]==baseline['entries']
extra=ledger['entries'][len(baseline['entries']):];assert all(e['stage'] is None and e['status'] in ('completed','failed') for e in extra)
assert not usage(ledger['entries'])['pending']
for entry in extra:
    record=json.loads(Path(entry['command_record']).read_text())
    assert not any(record[k] for k in ('timed_out','memory_limit_exceeded','CPU_limit_exceeded','unexpected_live_descendants'))
    assert not record['cleanup']['remaining_live_pids']
portable=json.loads((B/'portable_checks.json').read_text());assert portable['status']=='passed' and portable['negative_checks_rejected']==9
accept=json.loads((B/'acceptance/regression.json').read_text());assert accept['status']=='passed' and accept['native_cpp_checks']=='PASS arithmetic interfaces checks=3729'
disabled=json.loads((B/'validation-no-circt/regression.json').read_text());assert disabled['status']=='passed' and disabled['circt']['status']=='skipped' and disabled['circt']['reason']=='VUL_REGRESSION_CIRCT=0'
assert disabled['functional']==accept['functional'] and len(disabled['negative_requests'])==8
assert accept['circt']['status']=='passed'
# Successful report-generating compiler bytes match the final implementation.
for relative,expected in json.loads((B/'acceptance/execution_source_sha256.json').read_text()).items():assert sha(ROOT/relative)==expected,relative
summary={'status':'passed','version':'arithmetic-interfaces-static-checks-v1','baseline_tracked_files':len(before),'old_frozen_evidence_unchanged':old_evidence,'old_freezes_unchanged':old_freezes,'modified_tracked_files':sorted(changed),'deleted_tracked_files':deleted,'plan_chapters_2_3_and_previous_chapter4_bytes_unchanged':True,'first_chapter_only_two_status_paragraphs_changed':True,'platform_profiles_fixed_table_budget_cases_vullib_unchanged':True,'feature_enums_match_actual_BEIR':True,'python_syntax_files':len(pyfiles),'markdown_links_and_fences_passed':True,'both_git_diff_checks_passed':True,'accepted_compiler_execution_source_matches_current':True,'ledger_prefix_preserved':True,'new_usage':usage(extra),'cumulative_usage':usage(ledger['entries']),'cleanup_and_resource_limits_passed':True,'no_new_physical_calls':True,'no_CIRCT_disable_bypass':True,'old_simple_cost_split16_temporarily_required_by_step5':True}
(B/'static_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
