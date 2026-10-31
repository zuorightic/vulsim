"""New delta freeze must replay without build/EDA or coercing report counters."""
from pathlib import Path
import gzip,hashlib,json,shutil,subprocess,sys,tempfile
ROOT=Path.cwd();OUT=ROOT/'build/step4-review-20261031';FREEZE='experiments/arithmetic/arithmetic_interfaces_freeze_v2.json';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
results=[]
with tempfile.TemporaryDirectory(prefix='vulsim-step4-types-') as temp:
 r=Path(temp)
 def copy(relative):
  p=ROOT/relative;q=r/relative
  if p.is_file():q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 shutil.copytree(ROOT/'experiments/arithmetic',r/'experiments/arithmetic',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for p in (ROOT/'experiments/arithmetic').glob('*freeze*.json'):
  for relative in json.loads(p.read_text()).get('files_sha256',{}):copy(relative)
 for relative in ('experiments/__init__.py','experiments/arithmetic_dse/__init__.py'):copy(relative)
 f=json.loads((r/FREEZE).read_text());directory=r/f['evidence_directory'];delta=json.loads((directory/'usage_delta.json').read_text());ledger=json.loads((r/delta['prefix']).read_text());ledger['entries']+=delta['entries'];(r/'experiments/arithmetic/backend_usage.json').write_text(json.dumps(ledger))
 assert not (r/'build').exists();env={'PATH':'','PYTHONPATH':'','PYTHONDONTWRITEBYTECODE':'1','LC_ALL':'C.UTF-8'}
 def check(label,reason=None):
  p=subprocess.run([sys.executable,'-m','experiments.arithmetic_dse.interfaces_evidence'],cwd=r,env=env,text=True,capture_output=True,timeout=90)
  if reason:
   assert p.returncode!=0 and reason in p.stderr,(label,p.stderr[-3000:]);results.append({'name':label,'status':'rejected','hashes_rebound':True,'reason':p.stderr.strip().splitlines()[-1]})
  else:
   assert p.returncode==0,p.stderr[-3000:];d=json.loads(p.stdout);assert d['status']=='passed';results.append({'name':label,'status':'passed','parent_status':d['parent_status'],'package_bytes':d['new_evidence_bytes']})
 check('isolated_baseline')
 p=directory/'reports/asap7.json.gz';index=r/f['evidence_index'];initial=p.read_bytes();initial_index=index.read_bytes();initial_freeze=(r/FREEZE).read_bytes()
 for label,value,reason in [('counter_string','128','register_bits requires integer'),('counter_float',128.0,'register_bits requires integer'),('counter_boolean',True,'register_bits requires integer'),('counter_negative',-1,'register_bits minimum'),('counter_overflow',2**64,'register_bits maximum')]:
  try:
   report=json.loads(gzip.decompress(initial));report['pipeline']['register_bits']=value;p.write_bytes(gzip.compress((json.dumps(report)+'\n').encode(),mtime=0))
   i=json.loads(initial_index);i['files_sha256'][str(p.relative_to(r))]=sha(p);index.write_text(json.dumps(i,indent=2)+'\n');current=json.loads(initial_freeze);current['evidence_index_sha256']=sha(index);(r/FREEZE).write_text(json.dumps(current,indent=2)+'\n')
   check(label,reason)
  finally:p.write_bytes(initial);index.write_bytes(initial_index);(r/FREEZE).write_bytes(initial_freeze)
 check('isolated_restored')
summary={'status':'passed','version':'step4-report-type-portable-checks-v2','frozen_index_sha256':f['evidence_index_sha256'],'PATH':'','build_compiler_EDA_absent':True,'checks':results,'negative_checks_rejected':5,'parent_evidence_files_copied_only_to_temporary_validation_root':True,'new_archive_uses_references_not_parent_copies':True}
(OUT/'portable_checks.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False,indent=2))
