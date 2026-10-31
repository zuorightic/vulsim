"""Portable parameterized Mul/C evidence and explicit optional artifact audit."""
import argparse,contextlib,gzip,hashlib,io,json,math,tarfile,tempfile
from pathlib import Path
from .budget import usage,cpu_seconds
from .interfaces_evidence import verify_report,same
from .backend import stage_metrics
from .sdc import verify_sdc,rtl_ports
ROOT=Path(__file__).resolve().parents[2]
FREEZE='experiments/arithmetic/mul_templates_freeze_v1.json'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):
 p=Path(p);return gzip.decompress(p.read_bytes()).decode() if p.suffix=='.gz' else p.read_text()
def verify(root=ROOT,external=False,parents=True):
 root=Path(root);freeze=json.loads((root/FREEZE).read_text());ev=root/freeze['evidence_directory']
 from .freeze_history import historical_step5_analysis
 original_analysis=historical_step5_analysis(root);validate_selection=original_analysis.validate_selection;position_analysis=original_analysis.position_analysis;sensitivity=original_analysis.sensitivity
 for path,h in freeze['files_sha256'].items():
  from .freeze_history import source_location
  same(digest(source_location(root,FREEZE,path,h)),h,'source or explicit successor '+path);same(digest(root/freeze['source_snapshots'][path]),h,'snapshot '+path)
 for path,h in freeze['historical_freezes'].items():same(digest(root/path),h,'historical freeze '+path)
 for path in freeze['retired_active_paths']:
  if (root/path).exists():raise ValueError('retired implementation remains '+path)
 for item in [dict(path=freeze['evidence_index'],sha256=freeze['evidence_index_sha256']),freeze['capacity_evidence']]:
  same(digest(root/item['path']),item['sha256'],'index')
  for path,h in json.loads((root/item['path']).read_text())['files_sha256'].items():same(digest(root/path),h,'evidence '+path)
 types=json.loads((root/'experiments/arithmetic_dse/configs/arithmetic_compiler_interfaces_v1.json').read_text())['report_schemas'];features=json.loads((root/'experiments/arithmetic_dse/configs/beir_cost_features_v1.json').read_text())
 index=json.loads((ev/'report_index.json').read_text());data={};queries=nodes=regions=0
 for item in index:
  r=json.loads(read(root/item['report']));rtl=read(root/item['rtl']);stats=verify_report(r,rtl,features,report_schemas=types);data[item['name']]=r;nodes+=stats['nodes'];regions+=stats['regions'];queries+=validate_selection(r)
  for row in r['selection']['candidates']:
   if row['status']=='scheduled':verify_report(row['computation'],None,features,report_schemas=types)
 same(len(data),129,'accepted structural reports')
 for item in json.loads((ev/'circt/index.json').read_text()):
  r=data[item['name']];same(r['graph_sha256'],item['graph_sha256'],'CIRCT graph identity');same(r['schedule_sha256'],item['schedule_sha256'],'CIRCT schedule identity');same(hashlib.sha256(read(root/item['rtl']).encode()).hexdigest(),item['rtl_sha256'],'actual CIRCT RTL identity')

 same(sensitivity(data),json.loads((ev/'sensitivity.json').read_text()),'exact sensitivity')
 pos=json.loads((ev/'positions.json').read_text());same(position_analysis(data['w8_full_1'],pos['placements']),pos,'position analysis')
 # Replay the actual traces with the checked-in independent integer scoreboards.
 from regression.arithmetic_mul_templates import verify as mul_trace
 from regression.arithmetic_mul_mac import verify as mac_trace
 functional={}
 for name,check in [('mul',mul_trace),('mac',mac_trace)]:
  directory=ev/name
  with tempfile.TemporaryDirectory(prefix='vulsim-step5-trace-') as tmp:
   dest=Path(tmp)
   for file in ('items.json','vectors.txt','rtl-run.log'):(dest/file).write_text(read(directory/(file+'.gz')))
   with contextlib.redirect_stdout(io.StringIO()):check(dest)
   actual=json.loads((dest/'functional.json').read_text());same(actual,json.loads((directory/'functional.json').read_text()),name+' numerical trace');functional[name]=actual
 capacity_dir=root/freeze['capacity_evidence']['directory'];summary=json.loads((capacity_dir/'summary.json').read_text());capacity=[]
 for item in summary['runs']:
  directory=root/item['directory'];m=json.loads(read(directory/'manifest.json.gz'))
  same(m['status'],item['status'],'physical outcome');same(digest(directory/'input.sv'),next(t['rtl_sha256'] for t in json.loads((capacity_dir/'admission.json').read_text())['tasks'] if t['id']==m['task_id']),'admitted RTL')
  selected=data[f'w{item["W"]}_full_3'];same(digest(directory/'input.sv'),selected['rtl_sha256'],'current selected RTL = actual physical input')
  admitted=next(t for t in json.loads((capacity_dir/'admission.json').read_text())['tasks'] if t['id']==m['task_id']);same(hashlib.sha256(read(directory/'compiler-report-at-admission.json.gz').encode()).hexdigest(),admitted['compiler_report_sha256'],'compiler report at admission')
  same(m['target_platform'],'asap7','capacity platform');same(m['platform_profile']['profile_sha256'],selected['request']['platform_profile_sha256'],'capacity profile')
  same(m['period_ps'],1500.0,'fixed trial SDC period');same(m['abc_target_ps'],1500.0,'fixed trial ABC target')
  same(hashlib.sha256(json.dumps(m['mapping_context'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),m['mapping_context_sha256'],'mapping context identity')
  if any(lib['voltage_V']!=0.7 or lib['temperature_C']!=25 or lib['time_to_ps']!=1 for lib in m['libraries']):raise ValueError('capacity selected PVT/unit mismatch')

  cells=json.loads(read(directory/'liberty_cells.json.gz'))['cells'];p=m['platform_profile']
  for metric in m['metrics']:
   stage=metric['stage'];tag=directory/'reports/asap7/arithmetic_probe/base'
   with tempfile.TemporaryDirectory(prefix='vulsim-step5-STA-') as tmp:
    reports=Path(tmp)
    for file in tag.glob('vulsim_'+stage+'*'):(reports/file.name.removesuffix('.gz')).write_text(read(file))
    recalculated=stage_metrics(reports,stage,cells,m['period_ps'],selected=p)
    for key,value in recalculated.items():
     if key=='raw_reports_prefix':continue
     if type(value) in (int,float) and type(metric.get(key)) in (int,float):
      if not math.isclose(value,metric[key],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('STA metric '+key)
     elif value!=metric.get(key):raise ValueError('STA metric '+key)
   sdc=directory/('1_synth.sdc.gz' if stage=='synth' else '5_1_grt.sdc.gz')
   verify_sdc(read(sdc),p,m['period_ps'],rtl_ports((directory/'input.sv').read_text()))
  capacity.append({'W':item['W'],'status':m['status'],'stages':[x['stage'] for x in m['metrics']]})
 artifacts=json.loads((capacity_dir/'artifact_catalog.json').read_text());artifact_status='not_requested; portable reports/SDC/costs/trace only'
 if external:
  for artifact in artifacts:
   path=root/artifact['location']
   if not path.is_file():raise ValueError('artifact_unavailable: '+artifact['location'])
   same(digest(path),artifact['stored_sha256'],'actual external archive')
   with tarfile.open(path,'r:gz') as tar:
    same(set(tar.getnames()),{x['relative_member_path'] for x in artifact['members']},'archive member list')
    for member in artifact['members']:
     raw=tar.extractfile(member['relative_member_path']).read();same(len(raw),member['content_size_bytes'],'member bytes');same(hashlib.sha256(raw).hexdigest(),member['sha256'],'member hash')
  artifact_status='all local complete artifact bytes checked; persistent remote retention unconfirmed'
 delta=json.loads((ev/'usage_delta.json').read_text());parent_delta=json.loads((root/delta['prefix']).read_text());before=json.loads((root/parent_delta['prefix']).read_text());same(digest(root/delta['prefix']),delta['prefix_sha256'],'budget prefix identity');same(digest(root/parent_delta['prefix']),parent_delta['prefix_sha256'],'parent budget prefix identity');entries=before['entries']+parent_delta['entries']+delta['entries'];resources=json.loads((ev/'resources.json').read_text());same(usage(delta['entries']),resources['new_usage'],'new resources');same(usage(entries),resources['cumulative_usage'],'total resources')
 if usage(entries)['pending']:raise ValueError('unsettled ledger')
 live=root/'experiments/arithmetic/backend_usage.json'
 if live.exists():same(json.loads(live.read_text())['entries'][:len(entries)],entries,'live prefix')
 receipts=json.loads((ev/'command_index.json').read_text());same({r['id'] for r in receipts},{e['id'] for e in delta['entries']},'all charged leaves archived')
 for r in receipts:
  entry=next(e for e in delta['entries'] if e['id']==r['id']);record=json.loads((root/r['record']).read_text());same(record['exit_code'],entry['exit_code'],'leaf outcome');same(record['walltime_s'],entry['walltime_s'],'leaf wall')
  if entry.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':
   if not record['timed_out'] or (root/r['CPU_report']).read_text().strip() or entry['CPU_time_s']!=record['CPU_limit_s']:raise ValueError('invalid conservative timeout CPU settlement')
  else:same(cpu_seconds(root/r['CPU_report']),entry['CPU_time_s'],'actual CPU')
  if record['unexpected_live_descendants'] or record['cleanup']['remaining_live_pids']:raise ValueError('unclean leaf')
  if any(record[k] for k in ('timed_out','memory_limit_exceeded','CPU_limit_exceeded')):
   matched=next((x for x in summary['runs'] if x['task_id']==entry.get('task_id')),None)
   if not matched or matched['status']!='failed' or entry['stage']!=matched['failure_stage']:raise ValueError('resource failure missing explicit physical failure scope')
   if record['timed_out'] and matched['failure_code']!='timeout':raise ValueError('timeout failure code mismatch')
 policy=json.loads((root/'experiments/arithmetic_dse/configs/evidence_storage_v1.json').read_text())
 for item in [dict(path=freeze['evidence_index']),freeze['capacity_evidence']]:
  members=json.loads((root/item['path']).read_text())['files_sha256'];sizes=[(root/path).stat().st_size for path in members]+[(root/item['path']).stat().st_size]
  if item['path']==freeze['evidence_index']:sizes.append((root/FREEZE).stat().st_size)
  if sum(sizes)>policy['new_git_package_target_bytes'] or max(sizes)>policy['new_git_single_file_max_bytes']:raise ValueError('new package exceeds evidence storage target')
 parent_status={}
 if parents:
  from .interfaces_evidence import verify as interface_parent
  parent_status['step4_interfaces_v2']=interface_parent(root)['status']
 return {'status':'passed','freeze':freeze['version'],'structural_reports':len(data),'nodes':nodes,'regions':regions,'candidates_recomputed':queries,'functional':functional,'sensitivity_structures':30,'sensitivity_selected_changes':json.loads((ev/'sensitivity.json').read_text())['selected_changes'],'capacity':capacity,'artifact_verification':artifact_status,'new_usage':resources['new_usage'],'cumulative_usage':resources['cumulative_usage'],'parent_status':parent_status,'requires_build_or_EDA':False,'D_inference_or_main_matrix':False}
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--verify-external',action='store_true');p.add_argument('--no-parents',action='store_true');a=p.parse_args();print(json.dumps(verify(a.root,a.verify_external,not a.no_parents),indent=2))
if __name__=='__main__':main()
