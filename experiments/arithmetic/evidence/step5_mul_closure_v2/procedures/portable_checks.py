"""Isolated successor audit: no build, EDA, network or complete artifact store."""
from pathlib import Path
from copy import deepcopy
import gzip,hashlib,json,shutil,subprocess,sys,tempfile
R=Path.cwd();B=R/'build/step5-closure-20261031';F='experiments/arithmetic/mul_templates_freeze_v2.json';results=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='step5-closure-portable-') as tmp:
 root=Path(tmp);f=json.loads((R/F).read_text());ev=root/f['evidence_directory'];cap=root/f['capacity_evidence']['directory']
 shutil.copytree(R/'experiments/arithmetic',root/'experiments/arithmetic',ignore=shutil.ignore_patterns('__pycache__','*.pyc','artifact_store','backend_usage.json.lock'))
 def copy(relative):
  p=R/relative;q=root/relative
  if p.is_file() and relative not in f['retired_active_paths']:q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 for freeze in (R/'experiments/arithmetic').glob('*freeze*.json'):
  for path in json.loads(freeze.read_text()).get('files_sha256',{}):copy(path)
 assert not (root/'build').exists() and not (root/'experiments/arithmetic/artifact_store').exists()
 def entries(path):
  d=json.loads(path.read_text())
  return (entries(root/d['prefix']) if 'prefix' in d else [])+d['entries']
 state=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());state['entries']=entries(ev/'usage_delta.json');(root/'experiments/arithmetic/backend_usage.json').write_text(json.dumps(state))
 env={'PATH':'','PYTHONPATH':'','PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'}
 def run(label,reasons=None,external=False,parents=False):
  command=[sys.executable,'-m','experiments.arithmetic_dse.closure_evidence']
  if external:command+=['--verify-external']
  if not parents:command+=['--no-parents']
  p=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True,timeout=120)
  if reasons:
   assert p.returncode and any(v in p.stderr for v in reasons),(label,p.stderr[-3000:]);results.append({'name':label,'status':'rejected','reason':p.stderr.strip().splitlines()[-1]})
  else:
   assert p.returncode==0,(label,p.stderr[-3000:]);r=json.loads(p.stdout);results.append({'name':label,'status':'passed','parent_status':r['parent_status'],'artifact_verification':r['artifact_verification']})
 run('isolated_successor_and_v1_parent',parents=True)
 run('missing_complete_artifacts_explicitly_rejected',['artifact_unavailable'],external=True)
 def negative(label,path,edit,reasons,capacity=False):
  index=root/(f['capacity_evidence']['path'] if capacity else f['evidence_index']);raw=path.read_bytes();original_index=index.read_bytes();original_freeze=(root/F).read_bytes()
  try:
   edit(path);i=json.loads(original_index);i['files_sha256'][str(path.relative_to(root))]=sha(path);index.write_text(json.dumps(i,indent=2)+'\n');current=json.loads(original_freeze)
   if capacity:current['capacity_evidence']['sha256']=sha(index)
   else:current['evidence_index_sha256']=sha(index)
   (root/F).write_text(json.dumps(current,indent=2)+'\n');run(label,reasons)
  finally:path.write_bytes(raw);index.write_bytes(original_index);(root/F).write_bytes(original_freeze)
 def change(edit):
  def apply(p):d=json.loads(p.read_text());edit(d);p.write_text(json.dumps(d,indent=2)+'\n')
  return apply
 def fake_feasible(d):
  d['placements']=d['placements'][:2]
  for row in d['placements']:row['within_production_cap']=True
  d['feasible_count']=2
 negative('over_budget_positions_forged_feasible',ev/'positions_v2.json',change(fake_feasible),['feasibility disagrees'])
 negative('wrong_production_cap',ev/'positions_v2.json',change(lambda d:d.__setitem__('cap',{'numerator':100,'denominator':1})),['cap mismatch'])
 negative('false_production_minimum_claim',ev/'positions_v2.json',change(lambda d:d['production'].__setitem__('minimum_bits_at_equal_delay_and_comb',129)),['summary mismatch'])
 negative('rational_zero_denominator',ev/'sensitivity_v2.json',change(lambda d:d['rows'][0]['structures'][0]['linear_comb'].__setitem__('denominator',0)),['positive denominator'])
 negative('boolean_count_token',ev/'positions_v2.json',change(lambda d:d['production'].__setitem__('register_bits',True)),['JSON integer'])
 def wrong_sdc(p):p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b'set_clock_transition 10.0000',b'set_clock_transition 0.0000'),mtime=0))
 negative('actual_grt_SDC_wrong_transition',cap/'5_1_grt.sdc.gz',wrong_sdc,['transition'],True)
 def checkpoint(p):d=json.loads(gzip.decompress(p.read_bytes()));d['checkpoint_reuse']['checkpoint_sha256']['1_synth.odb']='0'*64;p.write_bytes(gzip.compress((json.dumps(d)+'\n').encode(),mtime=0))
 negative('checkpoint_reuse_identity_changed',cap/'manifest.json.gz',checkpoint,['bound synthesis checkpoint'],True)
 run('isolated_restored')
summary={'version':'step5-closure-portable-checks-v2','status':'passed','PATH':'','build_EDA_or_artifact_store_present':False,'checks':results,'negative_checks_rejected':sum(r['status']=='rejected' for r in results),'semantic_negative_hashes_rebound':True,'native_CXX_execution_scope':'archived receipt; portable independent graph certificate reruns; no native executable in isolated copy'}
(B/'portable_checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
