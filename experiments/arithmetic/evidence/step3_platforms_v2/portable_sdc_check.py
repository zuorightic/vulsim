from pathlib import Path
import hashlib,json,os,shutil,subprocess,tempfile
ROOT=Path.cwd();frel=Path('experiments/arithmetic/backend_freeze_v6.json')
freeze=json.loads((ROOT/frel).read_text());prior=json.loads((ROOT/freeze['supersedes']['path']).read_text())
results={}
with tempfile.TemporaryDirectory(prefix='vulsim-sdc-portable-') as temporary:
 root=Path(temporary)
 for rel in [str(frel),*freeze['files_sha256'],*freeze['historical_freezes']]:
  target=root/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/rel,target)
 for relative in (freeze['evidence_directory'],prior['evidence_directory']):
  shutil.copytree(ROOT/relative,root/relative,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 env=os.environ.copy();env.update(PATH='',PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1')
 command=['/usr/bin/python3','-m','experiments.arithmetic_dse.platform_evidence']
 def check(label,expected,needle=None):
  r=subprocess.run(command,cwd=root,env=env,text=True,capture_output=True)
  if (r.returncode==0)!=expected or (needle and needle not in r.stderr):raise AssertionError(label+': '+r.stdout+r.stderr)
  results[label]={'exit_code':r.returncode,'expected_rejection':not expected,
                  'diagnostic':r.stderr.splitlines()[-1] if r.stderr else json.loads(r.stdout)['status']}
 check('isolated_without_build_EDA_Tcl_or_PATH',True)
 index=root/freeze['evidence_index'];original_index=index.read_bytes();original_freeze=(root/frel).read_bytes()
 def rebind(relative):
  data=json.loads(original_index);data['files_sha256'][str(relative)]=hashlib.sha256((root/relative).read_bytes()).hexdigest()
  index.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
  f=json.loads(original_freeze);f['evidence_index_sha256']=hashlib.sha256(index.read_bytes()).hexdigest()
  (root/frel).write_text(json.dumps(f,ensure_ascii=False,indent=2)+'\n')
 import gzip
 ev=Path(freeze['evidence_directory'])
 for label,task,old,new,needle in [
  ('zero_setup_uncertainty','nangate45-mul-sdcfix','-setup 0.0200','-setup 0.0000','SDC setup uncertainty mismatch'),
  ('zero_hold_uncertainty','gf180-mul-sdcfix','-hold 0.0250','-hold 0.0000','SDC hold uncertainty mismatch'),
  ('zero_clock_transition','sky130hd-mul-sdcfix','set_clock_transition 0.1000','set_clock_transition 0.0000','SDC transition mismatch'),
  ('zero_output_load','gf180-mul-sdcfix','-pin_load 0.0134','-pin_load 0.0000','SDC output load mismatch'),
  ('wrong_period','nangate45-mul-sdcfix','-period 3.0000','-period 3000.0000','SDC period mismatch'),
  ('zero_reset_max_IO_delay','nangate45-mul-sdcfix','set_input_delay 0.6000 -clock [get_clocks {io_clk}] -max -add_delay [get_ports {rstn}]','set_input_delay 0.0000 -clock [get_clocks {io_clk}] -max -add_delay [get_ports {rstn}]','SDC IO max mismatch')]:
  relative=ev/'runs'/task/'6_final.sdc.gz';original=(root/relative).read_bytes()
  text=gzip.decompress(original).decode()
  if old not in text:raise AssertionError('negative check pattern missing: '+label)
  (root/relative).write_bytes(gzip.compress(text.replace(old,new).encode(),mtime=0));rebind(relative)
  check(label+'_after_hash_rebinding',False,needle)
  (root/relative).write_bytes(original);index.write_bytes(original_index);(root/frel).write_bytes(original_freeze)
 # Original bad NS SDC cannot be substituted into an otherwise valid current run.
 relative=ev/'runs/nangate45-mul-sdcfix/1_synth.sdc.gz';original=(root/relative).read_bytes()
 bad=root/prior['evidence_directory']/'runs/nangate45-mul/1_synth.sdc.gz'
 (root/relative).write_bytes(bad.read_bytes());rebind(relative)
 check('old_invalid_SDC_cannot_be_accepted_after_hash_rebinding',False,'SDC transition mismatch')
 (root/relative).write_bytes(original);index.write_bytes(original_index);(root/frel).write_bytes(original_freeze)
report={'status':'passed','checks':results,'mutations_confined_to_temporary_copy':True,'EDA_invocations':0}
(ROOT/'build/step3-sdcfix-20261030/portable_sdc_check.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False,indent=2))
