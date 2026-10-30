"""One-shot step-three evidence assembly; raw inputs never overwritten."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess,sys
sys.path.insert(0,str(Path.cwd()))
from experiments.arithmetic_dse.budget import usage,usage_by,cpu_seconds,POLICY

ROOT=Path.cwd()
BUILD=ROOT/'build/step3-platforms-20261030'
PROBES=BUILD/'probes'
EVIDENCE=ROOT/'experiments/arithmetic/evidence/step3_platforms_v1'
FREEZE=ROOT/'experiments/arithmetic/backend_freeze_v5.json'

def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def write(path,data):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
def copy(source,target):
    if source.is_file():
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
def compressed(source,target):
    if source.is_file():
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(gzip.compress(source.read_bytes(),mtime=0))
def rel(path):return str(path.relative_to(ROOT))

before=json.loads((BUILD/'usage-before.json').read_text())
after=json.loads((ROOT/'experiments/arithmetic/backend_usage.json').read_text())
if usage(after['entries'])['pending']:raise ValueError('cannot seal evidence with a pending leaf')
if after['entries'][:len(before['entries'])]!=before['entries']:raise ValueError('historical ledger changed')
copy(BUILD/'usage-before.json',EVIDENCE/'usage_before.json')
copy(ROOT/'experiments/arithmetic/backend_usage.json',EVIDENCE/'usage_after.json')
copy(PROBES/'preparation.json',EVIDENCE/'preparation.json')
for source in PROBES.glob('admission*.json'):copy(source,EVIDENCE/'admissions'/source.name)
for kind in ('add','mul'):
    for source in (PROBES/kind).iterdir():copy(source,EVIDENCE/'generated'/kind/source.name)
    for mode in ('software','native'):
        generated=PROBES/(kind+'-'+mode)
        for path in generated.rglob('*'):
            relative=path.relative_to(generated)
            if (path.is_file() and path.suffix in ('.cpp','.hpp','.h','.sv','.sh')
                    and not any(part.startswith(('obj_','obj_dir','build')) for part in relative.parts)):
                copy(path,EVIDENCE/'generated'/(kind+'-'+mode)/relative)

runs=[]
external={}
for directory in sorted((PROBES/'runs').iterdir()):
    if not (directory/'manifest.json').exists():continue
    manifest=json.loads((directory/'manifest.json').read_text())
    if manifest['status']=='running':raise ValueError('run still active')
    target=EVIDENCE/'runs'/directory.name
    for name in ('manifest.json','metrics.json','liberty_cells.json','effective-environment.txt','config.mk','input.sv'):
        copy(directory/name,target/name)
    if (directory/'source').exists():shutil.copytree(directory/'source',target/'source',dirs_exist_ok=True)
    copy(directory/'flow-scripts/abc_speed.script',target/'abc_speed.script')
    platform=manifest['target_platform']
    suffix=Path(platform)/'arithmetic_probe/base'
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
    item={'task_id':manifest['task_id'],'platform':platform,
          'kernel':'add_u32' if '-add' in manifest['task_id'] else 'mul_u32',
          'status':manifest['status'],'failure_stage':manifest.get('failure_stage'),
          'failure_reason':manifest.get('failure_reason'),'metrics':manifest['metrics'],
          'source_snapshot_at_execution':bool(manifest.get('source_sha256'))}
    if (results/'6_final.spef').exists():item['extracted_spef_sha256']=digest(results/'6_final.spef')
    runs.append(item)
    external.update({path:sha for path,sha in manifest.get('files_sha256',{}).items()
                     if Path(path).is_relative_to('/home/zyrv/OpenROAD-flow-scripts')})
    for library in manifest.get('libraries',[]):external[library['path']]=library['sha256']
    for tool in manifest.get('tools',{}).values():external[tool['path']]=tool['sha256']

extra=after['entries'][len(before['entries']):]
receipts=[]
for entry in extra:
    source=Path(entry['command_record'])
    record=json.loads(source.read_text())
    target=EVIDENCE/'commands'/entry['id']
    copy(source,target/'command.json')
    copy(Path(record['gnu_time']),target/'GNU-time.txt')
    compressed(Path(record['log']),target/'log.gz')
    same_cpu=cpu_seconds(target/'GNU-time.txt')
    if abs(same_cpu-entry['CPU_time_s'])>1e-8:raise ValueError('CPU charge mismatch')
    receipts.append({'id':entry['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt'),
                     'log':rel(target/'log.gz'),'original_log':record['log']})
write(EVIDENCE/'command_index.json',receipts)
write(EVIDENCE/'resources.json',{'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),
    'new_by_platform':usage_by(extra,'target_platform'),'new_by_admission':usage_by(extra,'admission_id'),
    'all_by_platform':usage_by(after['entries'],'target_platform'),
    'policy':rel(POLICY),'policy_sha256':digest(POLICY),'global_caps_changed':False,
    'max_leaf_sampled_RSS_KiB':max(json.loads((ROOT/r['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for r in receipts)})
write(EVIDENCE/'summary.json',{'version':'platform-connection-summary-v1','runs':runs,
    'training_or_main_records':0,'scope':'32-bit add/register and common original unsigned32x32->64 multiplier; L3 II1',
    'source_snapshot_note':'Early ASAP7 trials predate full per-run Python source copying; their exact RTL/SDC/ABC/ORFS/tool hashes and reports remain. Later runs copy executable source before launch. Final acceptance uses a fully captured ASAP7 multiplier rerun when present.',
    'automatic_retries':0,'multi_corner_signoff':False})
copy(Path(__file__),EVIDENCE/'archive_receipt.py')

orfs=Path('/home/zyrv/OpenROAD-flow-scripts')
unit_sources={'abc_liberty_units.c':orfs/'tools/yosys/abc/src/map/scl/sclLiberty.c',
              'abc_normalization.c':orfs/'tools/yosys/abc/src/map/scl/sclLibUtil.c',
              'openroad_metric_precision.h':orfs/'tools/OpenROAD/src/utl/include/utl/Logger.h',
              'load.tcl':orfs/'flow/scripts/load.tcl','floorplan.tcl':orfs/'flow/scripts/floorplan.tcl',
              'gf180_technology.lef':orfs/'flow/platforms/gf180/lef/gf180mcu_5LM_1TM_9K_9t_tech.lef',
              'gf180_native_setRC.tcl':orfs/'flow/platforms/gf180/setRC.tcl',
              'gf180_pdn.tcl':orfs/'flow/platforms/gf180/openROAD/pdn/pdn_grid_strategy_9t_6M.cfg',
              'OpenROAD_estimated_RC.tcl':orfs/'tools/OpenROAD/src/est/src/EstimateParasitics.tcl'}
for name,path in unit_sources.items():copy(path,EVIDENCE/'unit_basis'/name);external[str(path)]=digest(path)
write(EVIDENCE/'unit_basis/index.json',{name:{'path':str(path),'sha256':digest(path)} for name,path in unit_sources.items()})

files=[ROOT/'experiments/arithmetic_dse'/name for name in ('backend.py','platforms.py','platform_probe.py',
    'platform_evidence.py','run.py','budget.py','evidence.py','freeze_history.py','characterization.py','physical_control.py',
    'processes.py','timing_evidence.py','mul_split_evidence.py')]
files.extend(p for p in (ROOT/'experiments/arithmetic_dse/backend').iterdir() if p.is_file())
files.extend((ROOT/'experiments/arithmetic_dse/configs/platforms').glob('*.json'))
files.extend([POLICY,ROOT/'experiments/arithmetic_dse/configs/implementation_migration_v1.json',
              ROOT/'regression/arithmetic_backend.py'])
files.extend(p for p in (ROOT/'experiments/arithmetic/backend_probe').iterdir() if p.is_file())
for path in files:copy(path,EVIDENCE/'source_v5'/path.relative_to(ROOT))
source_hashes={rel(path):digest(path) for path in sorted(files)}
step2=json.loads((ROOT/'experiments/arithmetic/step2_freeze_v4.json').read_text())
parents={**step2['historical_freezes'],'experiments/arithmetic/step2_freeze_v4.json':digest(ROOT/'experiments/arithmetic/step2_freeze_v4.json')}
source_roots=[rel(EVIDENCE/'previous_source'),*step2['historical_source_roots']]
index=EVIDENCE/'index.json'
write(index,{'version':'platform-evidence-index-v1','files_sha256':{
    rel(path):digest(path) for path in sorted(EVIDENCE.rglob('*'))
    if path.is_file() and path!=index and path.suffix!='.pyc' and '__pycache__' not in path.parts}})
write(FREEZE,{'version':'arithmetic-backend-freeze-v5','frozen_at':datetime.now(timezone.utc).isoformat(),
    'files_sha256':source_hashes,'validated_source_snapshot':rel(EVIDENCE/'source_v5'),
    'historical_freezes':parents,'historical_source_roots':source_roots,
    'retired_active_paths':['experiments/arithmetic_dse/backend/asap7.mk'],
    'evidence_directory':rel(EVIDENCE),'evidence_index':rel(index),'evidence_index_sha256':digest(index),
    'external_files_sha256':external,'source_base':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),
    'rtlzz_base':subprocess.check_output(['git','-C','rtlzz','rev-parse','HEAD'],text=True).strip(),
    'planning_reference':'mission/lxy-plan-fix.md 第一章§3、§10.3，第四章步骤三',
    'scope':'four-platform physical backend connection; no trained D model or main matrix',
    'supersedes':{'path':'experiments/arithmetic/backend_freeze_v4.json','sha256':parents['experiments/arithmetic/backend_freeze_v4.json']}})
print(json.dumps({'freeze':rel(FREEZE),'runs':len(runs),'source_files':len(files),'usage':usage(extra)},indent=2))
