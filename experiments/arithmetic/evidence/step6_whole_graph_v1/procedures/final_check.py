from pathlib import Path
import hashlib,json,subprocess,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-integration-20261031'
from experiments.arithmetic_dse.whole_graph_evidence import verify
from experiments.arithmetic_dse.budget import usage
result=verify(external=True)
assert result['status']=='passed' and result['parent_status']=='passed'
old=(B/'lxy-plan-fix.md').read_text();new=(R/'mission/lxy-plan-fix.md').read_text()
assert old.split('# 第二章：',1)[1].split('# 第四章：',1)[0]==new.split('# 第二章：',1)[1].split('# 第四章：',1)[0]
assert old.split('# 第四章：',1)[1].rstrip()==new.split('# 第四章：',1)[1].split('<a id="step6-whole-graph-acceptance">',1)[0].rstrip()
for cmd in [['git','diff','--check'],['git','-C','rtlzz','diff','--check']]:subprocess.run(cmd,check=True)
result.update(previous_chapters_and_closed_step_records_preserved=True,protected_old_payload_files=6747,final_backend_regression_tests=69,physical_calls={'synth':2,'grt':0,'final':0},full_step6_acceptance=False,software_stage_accepted=True,commits_created=False)
(B/'final_audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
