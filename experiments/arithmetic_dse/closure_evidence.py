"""Step5 closure: exact positions, saved block graphs and one bounded retest.

Default verification needs repository evidence only. Native C++ execution is
retained as a receipt; the static saved-graph certificate is rerun independently.
--verify-external also reads every actual byte of the local artifact archives.
"""
import argparse,gzip,hashlib,json,math,re,tarfile,tempfile
from pathlib import Path
from .step5_evidence import read,digest
from .interfaces_evidence import same
from .block_tree_evidence import verify_block_trees
from .step5_analysis import validate_selection,verify_position_analysis,sensitivity
from .exact_analysis import check_sensitivity
from .backend import stage_metrics
from .budget import usage,cpu_seconds
from .sdc import verify_sdc,rtl_ports

ROOT=Path(__file__).resolve().parents[2]
FREEZE='experiments/arithmetic/mul_templates_freeze_v2.json'

def document(path):return json.loads(read(path))

def software(root,evidence,parent):
 index=document(root/parent['evidence_directory']/'report_index.json')
 replay_inputs={x['name']:x for x in document(evidence/'historical_replay_inputs.json')}
 native=document(evidence/'historical_replay.json');data={};blocked=regions=queries=0
 for item in index:
  path=root/item['report'];r=document(path);data[item['name']]=r;binding=replay_inputs[item['name']]
  same(binding['archived_path'],item['report'],'replayed actual archive path')
  same(binding['archived_sha256'],digest(path),'replayed archive bytes')
  same(binding['input_sha256'],hashlib.sha256(read(path).encode()).hexdigest(),'native actual graph input')
  blocked+=verify_block_trees(r);regions+=len(r['graph']['regions']);queries+=validate_selection(r)
 same(len(index),129,'saved graph reports');same(regions,219,'saved regions');same(queries,340,'outer candidate choices')
 same(native['reports'],129,'native historical reports');same(native['regions'],219,'native historical regions')
 same(native['rejected_reports'],0,'native rejected reports');same(native['unreconstructable_reports'],0,'native unreconstructable reports');same(native['status'],'passed','native status')
 same({x['name'] for x in native['results']},set(data),'native report list')
 for row in native['results']:
  same(row['status'],'passed','native saved graph');same(row['regions'],len(data[row['name']]['graph']['regions']),'native region count')
 expected={'duplicate_low_block','omitted_reduction_high_term','wrong_original_source','wrong_partial_shift','nonuniform_tail_coordinate'}
 same({x['name'] for x in native['mutations']},expected,'native mutation cases')
 for row in native['mutations']:
  same(row['status'],'rejected','native negative');same(row['failure_code'],'invalid_expansion_graph','native diagnostic protocol')
  if not row['reason'].startswith('invalid_expansion_graph: ') or '\0' in row['reason']:raise ValueError('unreadable native diagnostic')
 positions=verify_position_analysis(data['w8_full_1'],document(evidence/'positions_v2.json'))
 diagnostic=document(evidence/'sensitivity_v2.json');check_sensitivity(diagnostic);same(diagnostic,sensitivity(data),'exact sensitivity and numeric ranking')
 same(diagnostic['selected_changes'],0,'unchanged diagnostic selections')
 return data,{'reports':129,'regions':regions,'blocked_regions':blocked,'native_rejected':0,'native_unreconstructable':0,'native_mutations_rejected':5,'C_candidates_recomputed':queries,'feasible_positions':positions['feasible_count'],'production_register_bits':positions['production']['register_bits'],'sensitivity_structures':30,'sensitivity_contexts':10,'sensitivity_selected_changes':0}

def capacity(root,evidence,data):
 m=document(evidence/'manifest.json.gz');a=document(evidence/'admission.json');t=a['tasks'][0];reuse=m['checkpoint_reuse']
 old=document(root/'experiments/arithmetic/evidence/step5_mul_capacity_v1/W128/manifest.json.gz')
 old_hash=hashlib.sha256(read(root/'experiments/arithmetic/evidence/step5_mul_capacity_v1/W128/manifest.json.gz').encode()).hexdigest()
 same(a['purpose'],'mul_capacity_retest_only','bounded capacity purpose');same(len(a['tasks']),1,'one retest')
 same(a['call_caps'],{'synth':0,'grt':1,'final':0},'retest call caps')
 same(m['task_id'],'asap7-mul128-C-postsynth-grt-3600-v1','one named retest');same(m['task_id'],t['id'],'admitted task')
 same(m['admission_id'],a['id'],'retest admission ID');same(t['source_manifest_sha256'],old_hash,'source original manifest')
 same(digest(root/'experiments/arithmetic_dse/configs/backend_policy_v5.json'),a['policy_sha256'],'unchanged global policy')
 same(m['target_platform'],'asap7','retest platform');same(m['period_ps'],1500.0,'period');same(m['abc_target_ps'],1500.0,'ABC target')
 same(m['threads_per_tool'],2,'threads');same(m['memory_limit_MiB'],8192,'memory cap');same(m['stages_requested'],'grt','no final')
 same(m['platform_profile']['profile_sha256'],old['platform_profile']['profile_sha256'],'same profile')
 same(m['mapping_context'],old['mapping_context'],'same mapping conditions')
 same(hashlib.sha256(json.dumps(m['mapping_context'],sort_keys=True,separators=(',',':')).encode()).hexdigest(),m['mapping_context_sha256'],'mapping context hash')
 for key in ('graph_sha256','schedule_sha256','rtl_sha256'):same(t[key],data['w128_full_3'][key],'retest compiler '+key)
 same(t['selected_candidate'],data['w128_full_3']['selection']['selected_candidate'],'selected retest structure')
 same((t['L'],t['II']),(3,1),'fixed L/II');same(digest(evidence/'input.sv'),t['rtl_sha256'],'same actual input RTL')
 same(t['checkpoint_sha256'],reuse['checkpoint_sha256'],'only bound synthesis checkpoint')
 same(reuse['source_manifest_sha256'],old_hash,'reused original source manifest')
 same(reuse['reused_stages'],['synth'],'only synth reused');same(reuse['executed_stages'],['floorplan','placement','CTS','global_route'],'complete post synthesis chain')
 same(reuse['later_stage_products_copied'],0,'fresh later stages')
 same(set(t['checkpoint_sha256']),{'1_synth.odb','1_synth.sdc','1_2_yosys.v','1_2_yosys.sdc'},'checkpoint set')
 for name,h in t['checkpoint_sha256'].items():
  key='results/asap7/arithmetic_probe/base/'+name
  same(old['evidence_sha256'][key],h,'original actual checkpoint');same(m['evidence_sha256'][key],h,'new actual checkpoint')
 for tool,identity in m['tools'].items():same(identity,old['tools'][tool],'tool identity '+tool)
 for key in ('LIB_FILES','TECH_LEF','SC_LEF','RCX_RULES','ABC_DRIVER_CELL','ABC_LOAD_IN_FF','CORNER','ASAP7_USE_VT','LIB_MODEL','TC_TEMPERATURE','NUM_CORES'):
  same(m['effective_environment'][key],old['effective_environment'][key],'effective physical condition '+key)
 for path,h in old['files_sha256'].items():
  if '/OpenROAD-flow-scripts/' in path or '/arithmetic_dse/backend/' in path:same(m['files_sha256'][path],h,'unchanged physical script/asset '+path)
 for row in document(evidence/'execution_sources.json'):
  same(hashlib.sha256(read(root/row['snapshot']).encode()).hexdigest(),row['sha256'],'execution source bytes')
  same(m['source_sha256'][row['path']],row['sha256'],'execution source binding')
 for lib in m['libraries']:
  if lib['voltage_V']!=0.7 or lib['temperature_C']!=25 or lib['time_to_ps']!=1:raise ValueError('retest PVT/unit mismatch')
 chain=[c for c in m['commands'] if c['log'].endswith('/grt.log')]
 same(len(chain),1,'one physical leaf');chain=chain[0]
 same(chain['CPU_limit_s'],7200,'full CPU envelope')
 if chain['walltime_s']>3602 or chain['memory_limit_MiB']!=8192:raise ValueError('retest resource envelope exceeded')
 if any(c['log'].endswith(('/synth.log','/final.log')) for c in m['commands']):raise ValueError('unadmitted physical stage')
 same({x.removeprefix('--assume-old=') for x in chain['command'] if x.startswith('--assume-old=')},set(reuse['make_assume_old_targets']),'Make only assumes synthesis products')
 timings=document(evidence/'timing.json');new=timings['retest'];full=new['full_post_synthesis_to_grt']
 same(full['walltime_s'],chain['walltime_s'],'complete chain walltime');same(full['cleanup'],chain['cleanup'],'complete chain cleanup')
 if full['cleanup']['remaining_live_pids'] or chain['unexpected_live_descendants']:raise ValueError('unclean retest')
 same(timings['stitched_historical_time_used'],False,'no stitched time');same(timings['original_comparison_or_split_attribution'],False,'no unsupported attribution')
 footers={r['stage'] for r in new['substage_footers']}
 for phase in ('2_1_floorplan','3_3_place_gp','4_1_cts'):
  if phase not in footers:raise ValueError('complete new chain lacks '+phase+' execution footer')
 for row in new['substage_footers']:
  name=Path(row['source']).name;raw=read(evidence/'stage_logs'/(name+'.gz'))
  match=list(re.finditer(r'Elapsed time:\s*(\d+):(\d+)(?:\.(\d+))?\[h:\]min:sec\. CPU time: user ([\d.]+) sys ([\d.]+)',raw))
  if not match:raise ValueError('missing actual stage timing footer')
  x=match[-1];elapsed=int(x[1])*60+int(x[2])+(float('0.'+x[3]) if x[3] else 0)
  same(row['walltime_s'],elapsed,'stage walltime');same(row['CPU_time_s'],float(x[4])+float(x[5]),'stage CPU')
 p=m['platform_profile'];cells=document(evidence/'liberty_cells.json.gz')['cells'];metric_results=[]
 verify_sdc(read(evidence/'1_synth.sdc.gz'),p,1500,rtl_ports((evidence/'input.sv').read_text()))
 for metric in m['metrics']:
  same(metric['stage'],'grt','only new grt metrics; synth remains inherited')
  with tempfile.TemporaryDirectory(prefix='closure-STA-') as tmp:
   reports=Path(tmp)
   for file in (evidence/'reports').rglob('vulsim_grt*'):(reports/file.name.removesuffix('.gz')).write_text(read(file))
   recalculated=stage_metrics(reports,'grt',cells,1500,selected=p)
  for key,value in recalculated.items():
   if key=='raw_reports_prefix':continue
   if type(value) in (int,float) and type(metric.get(key)) in (int,float):
    if not math.isclose(value,metric[key],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('retest STA metric '+key)
   else:same(value,metric[key],'retest STA '+key)
  verify_sdc(read(evidence/'5_1_grt.sdc.gz'),p,1500,rtl_ports((evidence/'input.sv').read_text()));metric_results.append(metric)
 if m['status']=='completed':
  same(len(metric_results),1,'completed grt metric');same(chain['exit_code'],0,'complete flow exit');same(chain['timed_out'],False,'completed within bound')
  if '5_1_grt' not in footers:raise ValueError('completed grt lacks own timing')
 elif m['status']=='failed':
  same(len(metric_results),0,'failed run has no accepted grt metric');same(m['failure_stage'],'grt','explicit failure stage')
 else:raise ValueError('unsettled physical result')
 return {'task_id':m['task_id'],'status':m['status'],'failure_code':m.get('failure_code'),'complete_chain':full,'separate_5_1_grt':new['separate_5_1_grt'],'process_completed':m['status']=='completed','target_setup_met':metric_results[0]['measured_feasibility'] if metric_results else None,'hold_feasible_at_TT':metric_results[0]['hold_feasible_at_TT'] if metric_results else None,'scale_vs_split_attribution':'not established; no original paired run','batch_release':'separate domain admission required; no blanket release'}

def resources(root,evidence):
 delta=document(evidence/'usage_delta.json');parent_delta=document(root/delta['prefix']);parent_parent=document(root/parent_delta['prefix']);before=document(root/parent_parent['prefix'])
 same(digest(root/delta['prefix']),delta['prefix_sha256'],'usage prefix');same(digest(root/parent_delta['prefix']),parent_delta['prefix_sha256'],'parent usage prefix')
 entries=before['entries']+parent_parent['entries']+parent_delta['entries']+delta['entries']
 table=document(evidence/'resources.json');same(usage(entries),table['cumulative_usage'],'cumulative resources');same(usage(delta['entries']),table['new_usage'],'new resources')
 if usage(entries)['pending']:raise ValueError('unsettled frozen charges')
 live=root/'experiments/arithmetic/backend_usage.json'
 if live.exists():same(document(live)['entries'][:len(entries)],entries,'live preserved prefix')
 receipts=document(evidence/'command_index.json');same({r['id'] for r in receipts},{e['id'] for e in delta['entries']},'all charged leaves present')
 physical=[e for e in delta['entries'] if e['stage'] in ('synth','grt','final')]
 same([e['stage'] for e in physical],['grt'],'only one new physical call')
 for r in receipts:
  entry=next(e for e in delta['entries'] if e['id']==r['id']);record=document(root/r['record'])
  same(record['exit_code'],entry['exit_code'],'charged outcome');same(record['walltime_s'],entry['walltime_s'],'charged walltime')
  if entry.get('CPU_accounting')=='full_reservation_missing_CPU_evidence':
   if not record['timed_out'] or (root/r['CPU_report']).read_text().strip():raise ValueError('invalid conservative CPU settlement')
   same(entry['CPU_time_s'],record['CPU_limit_s'],'conservative CPU reservation')
  else:same(cpu_seconds(root/r['CPU_report']),entry['CPU_time_s'],'actual GNU CPU')
  if record['unexpected_live_descendants'] or record['cleanup']['remaining_live_pids']:raise ValueError('unclean charged leaf')
 return table

def verify(root=ROOT,external=False,parents=True):
 root=Path(root);f=document(root/FREEZE);e=root/f['evidence_directory'];c=root/f['capacity_evidence']['directory']
 from .freeze_history import source_location
 for path,h in f['files_sha256'].items():
  same(digest(source_location(root,FREEZE,path,h)),h,'source or explicit successor '+path);same(digest(root/f['source_snapshots'][path]),h,'frozen source '+path)
 for path,h in f['historical_freezes'].items():same(digest(root/path),h,'unchanged historical freeze '+path)
 for binding in ({'path':f['evidence_index'],'sha256':f['evidence_index_sha256']},f['capacity_evidence']):
  same(digest(root/binding['path']),binding['sha256'],'new evidence index')
  for path,h in document(root/binding['path'])['files_sha256'].items():same(digest(root/path),h,'new evidence '+path)
 for path,h in document(e/'preservation.json.gz')['original_sha256'].items():same(digest(root/path),h,'immutable historical payload '+path)
 parent=document(root/'experiments/arithmetic/mul_templates_freeze_v1.json');data,s=software(root,e,parent);physical=capacity(root,c,data);r=resources(root,e)
 physical_charge=next(x for x in document(e/'usage_delta.json')['entries'] if x['stage']=='grt')
 same(physical['complete_chain']['walltime_s'],physical_charge['walltime_s'],'physical measured/charged walltime')
 same(physical['complete_chain']['CPU_time_s'],physical_charge['CPU_time_s'],'physical measured/charged CPU')
 artifact_status='not requested; compact evidence only; native C++ execution is an archived receipt, static graph checks rerun'
 if external:
  for a in document(c/'artifact_catalog.json'):
   path=root/a['location']
   if not path.is_file():raise ValueError('artifact_unavailable: '+a['location'])
   same(digest(path),a['stored_sha256'],'actual artifact bytes');same(path.stat().st_size,a['stored_size_bytes'],'artifact size')
   with tarfile.open(path,'r:gz') as tar:
    same(set(tar.getnames()),{x['relative_member_path'] for x in a['members']},'artifact member set')
    for item in a['members']:
     stream=tar.extractfile(item['relative_member_path']);h=hashlib.sha256();size=0
     while chunk:=stream.read(1024*1024):h.update(chunk);size+=len(chunk)
     same(h.hexdigest(),item['sha256'],'artifact member identity');same(size,item['content_size_bytes'],'artifact member size')
  artifact_status='all locally available archive bytes verified; remote durable retention unconfirmed'
 policy=document(root/'experiments/arithmetic_dse/configs/evidence_storage_v1.json')
 for binding in ({'path':f['evidence_index']},f['capacity_evidence']):
  paths=[root/p for p in document(root/binding['path'])['files_sha256']]+[root/binding['path']]
  if binding['path']==f['evidence_index']:paths.append(root/FREEZE)
  if sum(p.stat().st_size for p in paths)>policy['new_git_package_target_bytes'] or max(p.stat().st_size for p in paths)>policy['new_git_single_file_max_bytes']:raise ValueError('new evidence storage target exceeded')
 parent_status={}
 if parents:
  from .step5_evidence import verify as previous
  parent_status=previous(root,external,True)
 return {'status':'passed','freeze':f['version'],'software':s,'capacity':physical,'new_usage':r['new_usage'],'cumulative_usage':r['cumulative_usage'],'artifact_verification':artifact_status,'parent_status':parent_status.get('status'),'requires_build_or_EDA':False,'new_original_synth_final_or_main_matrix_calls':False}

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,default=ROOT);p.add_argument('--verify-external',action='store_true');p.add_argument('--no-parents',action='store_true');a=p.parse_args();print(json.dumps(verify(a.root,a.verify_external,not a.no_parents),indent=2))
if __name__=='__main__':main()
