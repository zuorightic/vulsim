from pathlib import Path
from copy import deepcopy
import hashlib,json,subprocess,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step5-metric-scope-20261031';E=R/'experiments/arithmetic/evidence/step5_metric_scope_v1';F=R/'experiments/arithmetic/mul_templates_freeze_v3.json'
from experiments.arithmetic_dse.metric_scope_evidence import verify,analyze
base=verify(R);data=analyze(R);checks=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name,edit in [('confuse_internal_and_overall_slack',lambda d:d['rows'][2].__setitem__('setup_worst_slack_ps',235.70)),('mix_W64_synth_and_grt_period',lambda d:d['rows'][1].__setitem__('core_same_clock_min_period_ps',871.71)),('deduct_both_IO_delays_on_input_path',lambda d:d['rows'][2]['worst_path'].__setitem__('output_external_delay_ps',300))]:
 p=E/'analysis.json';index=E/'index.json';original=p.read_bytes();oldindex=index.read_bytes();oldfreeze=F.read_bytes()
 try:
  bad=deepcopy(data);edit(bad);p.write_text(json.dumps(bad,indent=2)+'\n');i=json.loads(oldindex);i['files_sha256'][str(p.relative_to(R))]=sha(p);index.write_text(json.dumps(i,indent=2)+'\n');f=json.loads(oldfreeze);f['evidence_index_sha256']=sha(index);F.write_text(json.dumps(f,indent=2)+'\n')
  try:verify(R,parents=False)
  except ValueError as error:
   assert str(error)=='STA scope interpretation mismatch',str(error);checks.append({'name':name,'status':'rejected','reason':str(error)})
  else:raise AssertionError('false scope accepted: '+name)
 finally:p.write_bytes(original);index.write_bytes(oldindex);F.write_bytes(oldfreeze)
for folder in (R,R/'rtlzz'):subprocess.run(['git','diff','--check'],cwd=folder,check=True)
result={'status':'passed','baseline':base,'negative_checks':checks,'original_reports_read_only':True,'new_EDA_or_STA_calls':0};(B/'audit.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
