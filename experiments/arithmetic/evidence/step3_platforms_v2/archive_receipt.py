"""Assemble successor SDC-correction evidence; never modify backend-v5 files."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess,sys
sys.path.insert(0,str(Path.cwd()))
from experiments.arithmetic_dse.budget import usage,usage_by,cpu_seconds,POLICY

ROOT=Path.cwd();BUILD=ROOT/'build/step3-sdcfix-20261030';PROBES=BUILD/'probes'
EVIDENCE=ROOT/'experiments/arithmetic/evidence/step3_platforms_v2'
FREEZE=ROOT/'experiments/arithmetic/backend_freeze_v6.json'
PRIOR=ROOT/'experiments/arithmetic/backend_freeze_v5.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rel(path):return str(path.relative_to(ROOT))
def write(path,data):
 path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def copy(source,target):
 if source.is_file():target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
def compressed(source,target):
 if source.is_file():target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(gzip.compress(source.read_bytes(),mtime=0))

before=json.loads((BUILD/'usage-before.json').read_text());after=json.loads((ROOT/'experiments/arithmetic/backend_usage.json').read_text())
if usage(after['entries'])['pending']:raise ValueError('pending leaf')
if after['entries'][:len(before['entries'])]!=before['entries']:raise ValueError('historical ledger changed')
copy(BUILD/'usage-before.json',EVIDENCE/'usage_before.json');copy(ROOT/'experiments/arithmetic/backend_usage.json',EVIDENCE/'usage_after.json')
copy(PROBES/'admission.json',EVIDENCE/'admissions/admission.json')
runs=[];external={}
previous=json.loads(PRIOR.read_text())
# Carry forward only the ASAP7 run proven unaffected by actual-SDC checks.
old_run=Path(previous['evidence_directory'])/'runs/asap7-mul-finalinterface'
m=json.loads((ROOT/old_run/'manifest.json').read_text())
runs.append({'task_id':m['task_id'],'platform':'asap7','kernel':'mul_u32','status':m['status'],
             'metrics':m['metrics'],'artifact_directory':str(old_run),'carried_forward_unaffected':True,
             'extracted_spef_sha256':next(r['extracted_spef_sha256'] for r in json.loads((ROOT/previous['evidence_directory']/'summary.json').read_text())['runs'] if r['task_id']==m['task_id'])})
for directory in sorted((PROBES/'runs').iterdir()):
 if not (directory/'manifest.json').exists():continue
 manifest=json.loads((directory/'manifest.json').read_text())
 if manifest['status']=='running':raise ValueError('run still active')
 target=EVIDENCE/'runs'/directory.name
 for name in ('manifest.json','metrics.json','liberty_cells.json','effective-environment.txt','config.mk','input.sv'):
  copy(directory/name,target/name)
 if (directory/'source').exists():shutil.copytree(directory/'source',target/'source',dirs_exist_ok=True)
 copy(directory/'flow-scripts/abc_speed.script',target/'abc_speed.script')
 platform=manifest['target_platform'];suffix=Path(platform)/'arithmetic_probe/base'
 for source in (directory/'reports'/suffix).glob('vulsim_*'):
  if source.suffix=='.v':compressed(source,target/'reports'/(source.name+'.gz'))
  else:copy(source,target/'reports'/source.name)
 for source in (directory/'logs'/suffix).glob('*'):
  if source.is_file() and source.suffix in ('.json','.log','.rpt','.txt'):
   if source.stat().st_size>2_000_000:compressed(source,target/'logs'/(source.name+'.gz'))
   else:copy(source,target/'logs'/source.name)
 results=directory/'results'/suffix
 for name in ('1_2_yosys.v','1_synth.sdc','5_1_grt.sdc','6_final.sdc','6_final.spef','6_final.v'):
  compressed(results/name,target/(name+'.gz'))
 item={'task_id':manifest['task_id'],'platform':platform,'kernel':'add_u32' if '-add' in manifest['task_id'] else 'mul_u32',
       'status':manifest['status'],'metrics':manifest['metrics'],'failure_stage':manifest.get('failure_stage'),
       'failure_reason':manifest.get('failure_reason'),'carried_forward_unaffected':False}
 if (results/'6_final.spef').exists():item['extracted_spef_sha256']=digest(results/'6_final.spef')
 runs.append(item)
 external.update({path:sha for path,sha in manifest.get('files_sha256',{}).items() if Path(path).is_relative_to('/home/zyrv/OpenROAD-flow-scripts')})
 for lib in manifest.get('libraries',[]):external[lib['path']]=lib['sha256']
 for tool in manifest.get('tools',{}).values():external[tool['path']]=tool['sha256']
external.update(previous['external_files_sha256'])
write(EVIDENCE/'summary.json',{'version':'platform-connection-summary-v2','runs':runs,'training_or_main_records':0,
 'scope':'SDC integer-division correction: three ns platforms, small add grt + common unsigned32x32->64 mul synth/grt/final; ASAP7 checked and carried forward',
 'automatic_retries':0,'multi_corner_signoff':False,'previous_four_platform_acceptance':'revoked; ns results invalid, retain original files and charges'})
extra=after['entries'][len(before['entries']):];receipts=[]
for entry in extra:
 source=Path(entry['command_record']);record=json.loads(source.read_text());target=EVIDENCE/'commands'/entry['id']
 copy(source,target/'command.json');copy(Path(record['gnu_time']),target/'GNU-time.txt');compressed(Path(record['log']),target/'log.gz')
 if abs(cpu_seconds(target/'GNU-time.txt')-entry['CPU_time_s'])>1e-8:raise ValueError('CPU charge mismatch')
 receipts.append({'id':entry['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt'),'log':rel(target/'log.gz')})
write(EVIDENCE/'command_index.json',receipts)
write(EVIDENCE/'resources.json',{'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),
 'new_by_platform':usage_by(extra,'target_platform'),'new_by_admission':usage_by(extra,'admission_id'),
 'policy':rel(POLICY),'policy_sha256':digest(POLICY),'global_caps_changed':False,
 'max_leaf_sampled_RSS_KiB':max(json.loads((ROOT/r['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for r in receipts)})
files=[ROOT/path for path in previous['files_sha256']]
files.extend([ROOT/'experiments/arithmetic_dse/sdc.py',ROOT/'regression/arithmetic_sdc.py'])
for path in files:copy(path,EVIDENCE/'source_v6'/path.relative_to(ROOT))
copy(Path(__file__),EVIDENCE/'archive_receipt.py')
index=EVIDENCE/'index.json'
write(index,{'version':'platform-evidence-index-v2','files_sha256':{rel(p):digest(p) for p in sorted(EVIDENCE.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}})
write(FREEZE,{'version':'arithmetic-backend-freeze-v6','frozen_at':datetime.now(timezone.utc).isoformat(),
 'files_sha256':{rel(path):digest(path) for path in sorted(files)},'validated_source_snapshot':rel(EVIDENCE/'source_v6'),
 'historical_freezes':{**previous['historical_freezes'],rel(PRIOR):digest(PRIOR)},
 'historical_source_roots':[rel(EVIDENCE/'previous_source'),previous['validated_source_snapshot'],*previous['historical_source_roots']],
 'retired_active_paths':previous['retired_active_paths'],'evidence_directory':rel(EVIDENCE),
 'evidence_index':rel(index),'evidence_index_sha256':digest(index),'external_files_sha256':external,
 'source_base':previous['source_base'],'rtlzz_base':previous['rtlzz_base'],
 'planning_reference':'mission/lxy-plan-fix.md 第一章§3、§10.3，第四章步骤三§3.9',
 'scope':'corrected four-platform connection only; no trained D model or main matrix',
 'supersedes':{'path':rel(PRIOR),'sha256':digest(PRIOR),'previous_acceptance_valid':False,
               'reason':'P1 Tcl integer division zeroed ns platform clock uncertainty/transition'},
 'sdc_contract_version':'serialized-sdc-contract-v1','carried_forward_platforms':['asap7'],
 'rerun_platforms':['nangate45','sky130hd','gf180']})
print(json.dumps({'freeze':rel(FREEZE),'runs':len(runs),'source_files':len(files),'new_usage':usage(extra)},indent=2))
