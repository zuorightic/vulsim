"""Isolate all repository evidence; semantic mutations rebind archive hashes."""
from pathlib import Path
import copy,gzip,hashlib,json,os,shutil,subprocess,sys,tempfile
R=Path.cwd();B=R/'build/step6-integration-20261031';F='experiments/arithmetic/whole_graph_freeze_v1.json';E='experiments/arithmetic/evidence/step6_whole_graph_v1';G='experiments/arithmetic/evidence/step6_graphs_v1';C='experiments/arithmetic/evidence/step6_capacity_v1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
def load(p):raw=p.read_bytes();return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
def save(p,d):raw=(json.dumps(d,indent=2)+'\n').encode();p.write_bytes(gzip.compress(raw,mtime=0) if p.suffix=='.gz' else raw)
with tempfile.TemporaryDirectory(prefix='step6-no-build-') as tmp:
 root=Path(tmp)
 # Actual bytes are copied. No build, PDK, executables or ignored artifact store.
 shutil.copytree(R/'experiments/arithmetic/evidence',root/'experiments/arithmetic/evidence',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copytree(R/'experiments/arithmetic_dse',root/'experiments/arithmetic_dse',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for p in (R/'experiments/arithmetic').glob('*.json'):
  q=root/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 f=load(root/F)
 for path in f['files_sha256']:
  q=root/path;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/path,q)
 # Historical verifiers also inspect active dependencies outside the latest
 # freeze's direct file set (e.g. backend handoff documentation).
 for prior in (R/'experiments/arithmetic').glob('*freeze*.json'):
  for path in json.loads(prior.read_text()).get('files_sha256',{}):
   source=R/path
   if source.is_file() and source.is_relative_to(R):
    q=root/source.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,q)
 for name in ('__init__.py','arithmetic_whole_graph.py','arithmetic_vul_suite.py'):
  p=R/'regression'/name
  if p.exists():q=root/'regression'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 env=os.environ.copy();env.update(PATH='',PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
 def run(external=False):
  return subprocess.run([sys.executable,'-m','experiments.arithmetic_dse.whole_graph_evidence',*(['--verify-external'] if external else [])],cwd=root,env=env,text=True,capture_output=True)
 positive=run();assert positive.returncode==0,positive.stderr;print('PASS isolated no-build no-EDA empty-PATH parent chain',flush=True)
 checks=[]
 def mutate(label,path,change,reason,external=False,rebind=True):
  target=root/path;old=target.read_bytes();aux=root/E/'public_bindings.json';auxraw=aux.read_bytes();freeze=(root/F).read_bytes();indexes={p['index']:(root/p['index']).read_bytes() for p in f['packages']}
  try:
   change(target)
   if rebind:
    data=load(root/F)
    for package in data['packages']:
     index=root/package['index'];d=load(index)
     if path in d['files_sha256']:d['files_sha256'][path]=sha(target)
     if str(aux.relative_to(root)) in d['files_sha256']:d['files_sha256'][str(aux.relative_to(root))]=sha(aux)
     write(index,d);package['sha256']=sha(index)
    write(root/F,data)
   result=run(external)
   assert result.returncode!=0,(label,'was accepted')
   assert reason in result.stderr,(label,result.stderr[-2000:]);checks.append({'name':label,'status':'rejected','diagnostic_excerpt':result.stderr.splitlines()[-1][:250]});print('PASS rejection',label,flush=True)
  finally:
   target.write_bytes(old);aux.write_bytes(auxraw);(root/F).write_bytes(freeze)
   for path,raw in indexes.items():(root/path).write_bytes(raw)
 def graph_change(path,kind):
  r=load(path)
  if kind=='cost':
   n=next(n for n in r['graph']['nodes'] if n['delay']>0);n['delay']+=1
   r['graph_identity_text']=json.dumps(r['graph'],sort_keys=True,separators=(',',':'));r['graph_sha256']=hashlib.sha256(r['graph_identity_text'].encode()).hexdigest();r['schedule_sha256']=hashlib.sha256((r['graph_sha256']+r['schedule_identity_text']).encode()).hexdigest()
  elif kind=='D':r['D_inference_implemented']=True
  elif kind=='L':r['request']['L']+=1
  save(path,r)
 mutate('independently_recomputed_node_cost',G+'/reports/UDR_128_C.json.gz',lambda p:graph_change(p,'cost'),'node delay')
 mutate('fake_D_success',G+'/reports/F2_C.json.gz',lambda p:graph_change(p,'D'),'inference scope')
 mutate('changed_latency',G+'/reports/UDR_128_C.json.gz',lambda p:graph_change(p,'L'),'L/N protocol')
 def trace(p):
  lines=gzip.decompress(p.read_bytes()).decode().splitlines();words=lines[2].split();words[1]=hex(int(words[1],16)^(1<<255))[2:];lines[2]=' '.join(words);p.write_bytes(gzip.compress(('\n'.join(lines)+'\n').encode(),mtime=0))
 mutate('actual_wide_RTL_trace_data',E+'/replays/native/rtl-run.log.gz',trace,'AssertionError')
 def sdc(p):p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b'set_clock_transition 10.0000',b'set_clock_transition 0.0000'),mtime=0))
 mutate('actual_F2_stage_SDC',C+'/runs/asap7-step6-fp32_serial-capacity-v1/1_synth.sdc.gz',sdc,'SDC transition mismatch')
 def outcome(p):d=load(p);next(x for x in d['runs'] if 'fp32_serial-capacity' in x['task_id'])['status']='completed';write(p,d)
 mutate('fake_capacity_completion',C+'/outcome.json',outcome,'outcome agrees with original manifest')
 def public(p):
  d=load(p);d['pipeline']['register_bits']+=1;save(p,d)
  aux=root/E/'public_bindings.json';rows=load(aux);next(x for x in rows if x['case']=='UDR_128')['report_sha256']=hashlib.sha256(gzip.decompress(p.read_bytes())).hexdigest();write(aux,rows)
 mutate('public_VUL_shared_register_count',G+'/public/UDR_128.json.gz',public,'shared register bits')
 # Source integrity is intentionally not rebound: a successor must not silently
 # accept unrelated active compiler bytes while continuing to cite this freeze.
 mutate('changed_active_compiler', 'rtlzz/src/backend/arithmetic_core.cpp',lambda p:p.write_text(p.read_text()+'\n// unbound change\n'),'ValueError',rebind=False)
 missing=run(True);assert missing.returncode and 'artifact_unavailable' in missing.stderr;checks.append({'name':'missing_complete_artifacts','status':'rejected','diagnostic_excerpt':'artifact_unavailable'});print('PASS missing complete artifacts rejected',flush=True)
 # The semantic helper is also exercised directly against the saved graph:
 # force a valid-width zero denominator and require the declared reason code.
 code='''import gzip,json;from pathlib import Path;from experiments.arithmetic_dse.whole_graph_checks import verify_safe_divisors
r=json.loads(gzip.decompress(Path("'''+G+'''/reports/UDR_128_C.json.gz").read_bytes()));n=next(n for n in r['graph']['nodes'] if n['kind']==4 and n['opcode']==4);v=n['operands'][1];v.update(kind=1,node='literal',constant_width=v['width'],limbs=['0']);verify_safe_divisors(r)
'''
 unsafe=subprocess.run([sys.executable,'-c',code],cwd=root,env=env,text=True,capture_output=True);assert unsafe.returncode and 'unsafe_divisor' in unsafe.stderr;checks.append({'name':'saved_graph_zero_divisor','status':'rejected','diagnostic_excerpt':'unsafe_divisor in saved graph'})
 report={'status':'passed','isolated_root_has_build':(root/'build').exists(),'isolated_has_EDA_or_artifact_store':False,'PATH':'empty','parent_chain_status':json.loads(positive.stdout)['parent_status'],'positive':json.loads(positive.stdout),'semantic_and_identity_negative_checks':checks,'rebound_archive_hashes_for_semantic_mutations':True,'physical_calls':0}
 (B/'portable_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='positive'},indent=2))
