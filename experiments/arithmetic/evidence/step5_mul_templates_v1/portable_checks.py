"""Static isolation and semantic counterexamples; no EDA or remote artifacts."""
from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,sys,tempfile
R=Path.cwd();B=R/'build/step5-parameterized-20261031';F='experiments/arithmetic/mul_templates_freeze_v1.json';results=[];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='step5-portable-') as tmp:
 root=Path(tmp);f=json.loads((R/F).read_text());ev=root/f['evidence_directory']
 shutil.copytree(R/'experiments/arithmetic',root/'experiments/arithmetic',ignore=shutil.ignore_patterns('__pycache__','*.pyc','artifact_store','backend_usage.json.lock'))
 def copy(relative):
  p=R/relative;q=root/relative
  if p.is_file() and relative not in f['retired_active_paths']:q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 for p in (R/'experiments/arithmetic').glob('*freeze*.json'):
  for path in json.loads(p.read_text()).get('files_sha256',{}):copy(path)
 for path in f['files_sha256']:copy(path)
 assert not (root/'build').exists() and not (root/'experiments/arithmetic/artifact_store').exists()
 # Exclude the pending outer verification leaf, use the settled archive prefix.
 d=json.loads((ev/'usage_delta.json').read_text());p=json.loads((root/d['prefix']).read_text());old=json.loads((root/p['prefix']).read_text());old['entries']+=p['entries']+d['entries'];(root/'experiments/arithmetic/backend_usage.json').write_text(json.dumps(old))
 env={'PATH':'','PYTHONPATH':'','PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'}
 def run(label,reasons=None,external=False):
  cmd=[sys.executable,'-m','experiments.arithmetic_dse.step5_evidence']
  if external:cmd+=['--verify-external']
  p=subprocess.run(cmd,cwd=root,env=env,text=True,capture_output=True,timeout=90)
  if reasons:
   assert p.returncode!=0 and any(x in p.stderr for x in reasons),(label,p.stderr[-3000:]);results.append({'name':label,'status':'rejected','reason':p.stderr.strip().splitlines()[-1]})
  else:
   assert p.returncode==0,p.stderr[-3000:];d=json.loads(p.stdout);assert d['status']=='passed';results.append({'name':label,'status':'passed','parent_status':d['parent_status'],'artifact_verification':d['artifact_verification']})
 run('isolated_baseline');run('missing_complete_artifacts_fail_full_verification',['artifact_unavailable'],True)
 index=root/f['evidence_index'];original_index=index.read_bytes();original_freeze=(root/F).read_bytes()
 def negative(label,relative,edit,reasons):
  p=root/relative;original=p.read_bytes()
  try:
   edit(p);i=json.loads(original_index);i['files_sha256'][str(p.relative_to(root))]=sha(p);index.write_text(json.dumps(i,indent=2)+'\n');current=json.loads(original_freeze);current['evidence_index_sha256']=sha(index);(root/F).write_text(json.dumps(current,indent=2)+'\n');run(label,reasons)
  finally:p.write_bytes(original);index.write_bytes(original_index);(root/F).write_bytes(original_freeze)
 def report_negative(label,name,edit,reasons):
  def change(p):
   r=json.loads(gzip.decompress(p.read_bytes()));edit(r);r['graph_identity_text']=json.dumps(r['graph'],separators=(',',':'),sort_keys=True);r['graph_sha256']=hashlib.sha256(r['graph_identity_text'].encode()).hexdigest();r['schedule_identity_text']=json.dumps({'stages':r['stages'],'protocol':r['protocol']},separators=(',',':'),sort_keys=True);r['schedule_sha256']=hashlib.sha256((r['graph_sha256']+r['schedule_identity_text']).encode()).hexdigest();p.write_bytes(gzip.compress((json.dumps(r)+'\n').encode(),mtime=0))
  negative(label,f['evidence_directory']+'/reports/'+name+'.json.gz',change,reasons)
 def wrong_cost(r):next(n for n in r['graph']['nodes'] if n['opcode']==3)['delay']=0
 report_negative('wrong_partial_cost','w128_full_2',wrong_cost,['node delay'])
 def cut(r):g=r['graph']['regions'][0]['legal_groups'][0];r['stages'][int(g[0])]=(r['stages'][int(g[0])]+1)%3
 report_negative('cut_legal_group','w32_full_1',cut,['indivisible group cut','backwards schedule'])
 report_negative('wrong_block_parameter','w32_full_1',lambda r:r['graph']['regions'][0]['parameters'].__setitem__('block_width',1),['blocked Mul parameter range'])
 report_negative('wrong_C_selected_candidate','w32_full_3',lambda r:r['selection'].__setitem__('selected_candidate','candidate/original/original'),['C did not choose'])
 def traceflip(p):
  rows=gzip.decompress(p.read_bytes()).decode().splitlines()
  for i,line in enumerate(rows):
   vals=[int(v,16) for v in line.split()]
   if vals[0]:vals[97]^=1<<255;rows[i]=' '.join(format(v,'x') for v in vals);break
  p.write_bytes(gzip.compress(('\n'.join(rows)+'\n').encode(),mtime=0))
 negative('flip_256_product_bit',f['evidence_directory']+'/mul/rtl-run.log.gz',traceflip,['AssertionError'])
 def square(p):d=json.loads(p.read_text());d['rows'][0]['structures'][0]['square_comb']='999';p.write_text(json.dumps(d))
 negative('wrong_square_diagnostic',f['evidence_directory']+'/sensitivity.json',square,['exact sensitivity'])
 run('isolated_restored')
summary={'version':'step5-portable-checks-v1','status':'passed','PATH':'','build_or_EDA_or_external_artifacts_present':False,'tested_index_sha256':f['evidence_index_sha256'],'checks':results,'negative_checks_rejected':sum(x['status']=='rejected' for x in results),'semantic_negative_hashes_rebound':True,'same_archived_1129_and_1011_cycle_vectors_replayed_not_new_RTL_simulation':True}
(B/'portable_checks.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
