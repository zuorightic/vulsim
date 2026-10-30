"""Test strict SDC semantics in a disposable copy, with no Tcl or EDA."""
from pathlib import Path
import gzip,hashlib,json,os,shutil,subprocess,tempfile
R=Path.cwd();F=Path('experiments/arithmetic/backend_freeze_v7.json');freeze=json.loads((R/F).read_text());V6=Path(freeze['measurement_freeze']['path']);v6=json.loads((R/V6).read_text());v5=json.loads((R/v6['supersedes']['path']).read_text());results={};sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
with tempfile.TemporaryDirectory(prefix='vulsim-sdc-review-') as temporary:
 root=Path(temporary)
 for path in [str(F),*freeze['files_sha256'],*freeze['historical_freezes']]:
  target=root/path;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/path,target)
 for relative in (freeze['evidence_directory'],v6['evidence_directory'],v5['evidence_directory']):
  shutil.copytree(R/relative,root/relative,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
 provenance=json.loads((R/'experiments/arithmetic_dse/configs/platform_parameter_sources_v1.json').read_text())
 for profile in provenance['profiles'].values():
  for row in profile['parameters'].values():
   for basis in row['basis']:
    relative=Path(basis['path'])
    if not relative.is_absolute() and not (root/relative).exists():
     (root/relative).parent.mkdir(parents=True,exist_ok=True);shutil.copy2(R/relative,root/relative)
 env=os.environ.copy();env.update(PATH='',PYTHONPATH='',PYTHONDONTWRITEBYTECODE='1');cmd=['/usr/bin/python3','-m','experiments.arithmetic_dse.platform_evidence']
 def check(label,expected,needle=None):
  result=subprocess.run(cmd,cwd=root,env=env,text=True,capture_output=True)
  if (result.returncode==0)!=expected or (needle and needle not in result.stderr):raise AssertionError(label+': '+result.stdout+result.stderr)
  results[label]={'exit_code':result.returncode,'expected_rejection':not expected,'diagnostic':result.stderr.splitlines()[-1] if result.stderr else json.loads(result.stdout)['status']}
 check('isolated_no_build_no_EDA_no_Tcl_empty_PATH',True)
 original={}
 def write(path,data):
  original.setdefault(path,path.read_bytes());path.write_bytes(data)
 def json_write(path,data):write(path,(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode())
 def rebind(relative):
  index=root/v6['evidence_index'];data=json.loads(index.read_text());data['files_sha256'][str(relative)]=sha(root/relative);json_write(index,data)
  old=json.loads((root/V6).read_text());old['evidence_index_sha256']=sha(index);json_write(root/V6,old)
  metadata=Path('experiments/arithmetic_dse/configs/platform_parameter_sources_v1.json');source=json.loads((root/metadata).read_text());source['measurement_freeze']['sha256']=sha(root/V6);json_write(root/metadata,source)
  snapshot=root/freeze['validated_source_snapshot']/metadata;write(snapshot,(root/metadata).read_bytes())
  latest_index=root/freeze['evidence_index'];idx=json.loads(latest_index.read_text());idx['files_sha256'][str(snapshot.relative_to(root))]=sha(snapshot);json_write(latest_index,idx)
  f=json.loads((root/F).read_text());f['files_sha256'][str(metadata)]=sha(root/metadata);f['historical_freezes'][str(V6)]=sha(root/V6);f['measurement_freeze']['sha256']=sha(root/V6);f['supersedes']['sha256']=sha(root/V6);f['evidence_index_sha256']=sha(latest_index);json_write(root/F,f)
 def restore():
  for path,data in original.items():path.write_bytes(data)
  original.clear()
 relative=Path(v6['evidence_directory'])/'runs/nangate45-mul-sdcfix/1_synth.sdc.gz'
 text=gzip.decompress((root/relative).read_bytes()).decode();normal='current_design MulProbe_sim_top'
 cases=[
  ('P2_minimal_semicolon_bypass',text+'\ncurrent_design MulProbe_sim_top; set_false_path -from [get_ports {rstn}]\n','unsupported SDC command boundary'),
  ('P2_existing_declaration_semicolon',text.replace(normal,normal+'; set_false_path -from [get_ports {rstn}]'),'unsupported SDC command boundary'),
  ('invalid_current_design_arity',text.replace(normal,normal+' extra'),'unsupported SDC current_design'),
  ('wrong_current_design',text.replace(normal,'current_design WrongTop'),'SDC current_design identity mismatch'),
  ('quoted_dynamic_current_design',text.replace(normal,'current_design "[set top MulProbe_sim_top]"'),'unsupported SDC literal nesting or substitution'),
  ('comment_continuation_hides_constraint',text.replace('set_clock_transition','# hidden\\\nset_clock_transition'),'unsupported SDC continuation'),
  ('adjacent_collection_substitution',text.replace('[get_clocks {core_clk}]','[get_clocks {core_clk}][get_clocks {core_clk}]',1),'unsupported SDC word concatenation'),
  ('standalone_false_path',text+'\nset_false_path -from [get_ports {rstn}]\n','unsupported SDC constraint command'),
  ('zero_setup',text.replace('-setup 0.0200','-setup 0.0000'),'SDC setup uncertainty mismatch'),
  ('zero_hold',text.replace('-hold 0.0050','-hold 0.0000'),'SDC hold uncertainty mismatch'),
  ('zero_transition',text.replace('set_clock_transition 0.0100','set_clock_transition 0.0000'),'SDC transition mismatch'),
  ('zero_load',text.replace('-pin_load 3.8980','-pin_load 0.0000'),'SDC output load mismatch'),
  ('wrong_period',text.replace('-period 3.0000','-period 3000.0000'),'SDC period mismatch'),
  ('zero_IO_max',text.replace('set_input_delay 0.6000','set_input_delay 0.0000'),'SDC IO max mismatch'),
  ('missing_reset', '\n'.join(line for line in text.splitlines() if not (line.startswith('set_input_delay') and '{rstn}' in line)),'SDC IO coverage mismatch'),
 ]
 for label,corrupted,needle in cases:
  assert corrupted!=text,label
  write(root/relative,gzip.compress(corrupted.encode(),mtime=0));rebind(relative);check(label+'_after_identity_rebinding',False,needle);restore()
 old=root/v5['evidence_directory']/'runs/nangate45-mul/1_synth.sdc.gz';write(root/relative,old.read_bytes());rebind(relative)
 check('old_invalid_ns_SDC_after_identity_rebinding',False,'SDC transition mismatch');restore()
 check('restored_copy_still_passes',True)
 # --root must use the audited copy's metadata, not the running module's repo.
 rooted=cmd+['--root',str(root)]
 r=subprocess.run(rooted,cwd=R,env=env,text=True,capture_output=True)
 if r.returncode:raise AssertionError(r.stderr)
 results['explicit_root_uses_copied_bundle']={'exit_code':r.returncode,'expected_rejection':False,'diagnostic':'passed'}
 metadata=Path('experiments/arithmetic_dse/configs/platform_parameter_sources_v1.json')
 data=json.loads((root/metadata).read_text());data['profiles']['nangate45']['parameters']['setup_uncertainty_ps']['value']=0;json_write(root/metadata,data)
 snapshot=root/freeze['validated_source_snapshot']/metadata;write(snapshot,(root/metadata).read_bytes())
 idxpath=root/freeze['evidence_index'];idx=json.loads(idxpath.read_text());idx['files_sha256'][str(snapshot.relative_to(root))]=sha(snapshot);json_write(idxpath,idx)
 f=json.loads((root/F).read_text());f['files_sha256'][str(metadata)]=sha(root/metadata);f['evidence_index_sha256']=sha(idxpath);json_write(root/F,f)
 r=subprocess.run(rooted,cwd=R,env=env,text=True,capture_output=True)
 if r.returncode==0 or 'parameter provenance value/unit/basis mismatch' not in r.stderr:raise AssertionError(r.stdout+r.stderr)
 results['explicit_root_provenance_tamper_after_rebinding']={'exit_code':r.returncode,'expected_rejection':True,'diagnostic':r.stderr.splitlines()[-1]}
 restore()
report={'status':'passed','checks':results,'mutations_confined_to_temporary_copy':True,'EDA_invocations':0,'archived_Tcl_executions':0,'hash_rebinding':'modified SDC, measurement index/freeze, successor inherited hashes and source metadata identities all rebound before semantic checks'}
(R/'build/step3-sdc-parser-20261030/portable_review.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report,ensure_ascii=False,indent=2))
