from pathlib import Path
import gzip,hashlib,json,os,shutil,subprocess,sys,tempfile
R=Path.cwd();B=R/'build/step6-review-20261102';F='experiments/arithmetic/whole_graph_freeze_v2.json';E='experiments/arithmetic/evidence/step6_review_v2';C='experiments/arithmetic/evidence/step6_capacity_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):raw=p.read_bytes();return json.loads(gzip.decompress(raw) if p.suffix=='.gz' else raw)
def write(p,d):p.write_text(json.dumps(d,indent=2)+'\n')
with tempfile.TemporaryDirectory(prefix='step6-review-isolated-') as tmp:
 root=Path(tmp)
 shutil.copytree(R/'experiments/arithmetic/evidence',root/'experiments/arithmetic/evidence',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 shutil.copytree(R/'experiments/arithmetic_dse',root/'experiments/arithmetic_dse',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 for p in (R/'experiments/arithmetic').glob('*.json'):
  q=root/p.relative_to(R);q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
 for prior in (R/'experiments/arithmetic').glob('*freeze*.json'):
  for path in load(prior).get('files_sha256',{}):
   source=R/path
   if source.is_file() and source.is_relative_to(R):q=root/path;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,q)
 for name in ('__init__.py','arithmetic_whole_graph.py','arithmetic_vul_suite.py','arithmetic_divisor.py'):
  source=R/'regression'/name
  if source.exists():q=root/'regression'/name;q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,q)
 env=os.environ.copy();env.update(PATH='',PYTHONPATH=str(root),PYTHONDONTWRITEBYTECODE='1',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
 def run(external=False):return subprocess.run([sys.executable,'-m','experiments.arithmetic_dse.whole_graph_evidence',*(['--verify-external'] if external else [])],cwd=root,env=env,text=True,capture_output=True)
 result=run();assert result.returncode==0,result.stderr;positive=json.loads(result.stdout);checks=[];print('PASS isolated latest/parent chain with empty PATH and no build/artifacts',flush=True)
 # The precise user heading change and subsequent prose changes do not alter
 # frozen source snapshots or relax source/configuration identity enforcement.
 doc=root/'mission/lxy-plan-fix.md';raw=doc.read_bytes();doc.write_bytes(raw+b'\n<!-- independently edited navigation prose -->\n');changed=run();assert changed.returncode==0,changed.stderr;assert 'mission/lxy-plan-fix.md' in json.loads(changed.stdout)['documentation_drift'];doc.write_bytes(raw);print('PASS current narrative drift reported; all numerical evidence remains verifiable',flush=True)
 freeze=load(root/F)
 def mutation(label,path,edit,rebind=True,reason=None):
  target=root/path;raw=target.read_bytes();fraw=(root/F).read_bytes();indexes={x['index']:(root/x['index']).read_bytes() for x in freeze['packages']}
  try:
   edit(target)
   if rebind:
    f=load(root/F)
    for package in f['packages']:
     index=root/package['index'];d=load(index)
     if path in d['files_sha256']:d['files_sha256'][path]=sha(target);write(index,d);package['sha256']=sha(index)
    write(root/F,f)
   bad=run();assert bad.returncode!=0,(label,'accepted')
   if reason:assert reason in bad.stderr,(label,bad.stderr[-1500:])
   checks.append({'case':label,'status':'rejected','diagnostic':bad.stderr.splitlines()[-1][:250]});print('PASS rejection',label,flush=True)
  finally:
   target.write_bytes(raw);(root/F).write_bytes(fraw)
   for p,old in indexes.items():(root/p).write_bytes(old)
 def native(p):d=load(p);d['observed_wrong_acceptances']=1;write(p,d)
 mutation('fake_native_proof_success',E+'/new_cpp.json',native,reason='corrected real C++ entry')
 def fake_role(p):d=load(p);next(x for x in d['cases_detail'] if x['case_id']=='UDR_128')['role']='mul_internal_structure_choice';write(p,d)
 mutation('atomic_UDR_claims_internal_structure_choice',E+'/case-role-audit.json',fake_role,reason='actual structure capability role')
 mutation('changed_active_compiler','rtlzz/src/backend/arithmetic_core.cpp',lambda p:p.write_bytes(p.read_bytes()+b'\n// unbound source edit\n'),False)
 mutation('changed_fixed_cost_table','experiments/arithmetic_dse/configs/fixed_op_width_v1.json',lambda p:p.write_bytes(p.read_bytes()+b'\n'),False)
 def sdc(p):p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b'set_clock_transition 10.0000',b'set_clock_transition 0.0000'),mtime=0))
 mutation('actual_FP_grt_SDC',C+'/runs/asap7-step6-fp32_serial-capacity-recheck-v2/5_1_grt.sdc.gz',sdc,reason='SDC transition mismatch')
 clock=C+'/clock_relaxation/runs/asap7-step6-udr_unsigned_128-sdc100ns-v5'
 def clock_period(p):p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b'-period 100000.0000',b'-period 200000.0000'),mtime=0))
 mutation('actual_UDR_grt_clock',clock+'/5_1_grt.sdc.gz',clock_period,reason='SDC period mismatch')
 def clock_IO(p):p.write_bytes(gzip.compress(gzip.decompress(p.read_bytes()).replace(b'300.0000 -clock',b'20000.0000 -clock'),mtime=0))
 mutation('actual_UDR_absolute_IO',clock+'/5_1_grt.sdc.gz',clock_IO,reason='SDC IO')
 def copied_checkpoint(p):d=load(p);d['checkpoint_reuse']['old_ODB_or_old_SDC_copied']=True;p.write_bytes(gzip.compress((json.dumps(d,indent=2)+'\n').encode(),mtime=0))
 mutation('old_physical_checkpoint_falsely_reused',clock+'/manifest.json.gz',copied_checkpoint,reason='fresh SDC and complete physical chain')
 snapshot=freeze['source_snapshots']['mission/lxy-plan-fix.md']
 mutation('changed_protected_plan_snapshot',snapshot,lambda p:p.write_bytes(p.read_bytes()+b'\n<!-- changed frozen bytes -->\n'),False)
 def metric(p):d=load(p);next(x for x in d['runs'] if 'fp32_serial-capacity' in x['task_id'])['status']='failed';write(p,d)
 mutation('faked_capacity_status',C+'/outcome.json',metric,reason='outcome and raw manifest')
 missing=run(True);assert missing.returncode and 'artifact_unavailable' in missing.stderr;checks.append({'case':'missing_complete_artifacts','status':'rejected'});print('PASS unavailable complete artifacts rejected',flush=True)
 report={'status':'passed','isolated_no_build_EDA_or_artifact_store':True,'PATH':'empty','parent_status':positive['parent_status'],'editable_documentation_drift_accepted_and_reported':True,'strict_source_and_cost_config_rejections_retained':True,'negative_checks':checks,'semantic_mutations_rebound_index_hashes':True,'positive_summary':positive}
 (B/'portable_checks.json').write_text(json.dumps(report,indent=2)+'\n')
