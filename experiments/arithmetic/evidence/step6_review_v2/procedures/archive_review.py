"""Append-only step6 correction evidence; old v1 remains immutable."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-review-20261102';E=R/'experiments/arithmetic/evidence/step6_review_v2';C=R/'experiments/arithmetic/evidence/step6_capacity_v2';F=R/'experiments/arithmetic/whole_graph_freeze_v2.json';P=R/'experiments/arithmetic/whole_graph_freeze_v1.json'
from experiments.arithmetic_dse.budget import usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def gz(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
def gzdoc(q,d):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode(),mtime=0))
for d in (E,C):d.mkdir(parents=True,exist_ok=True)
parent=json.loads(P.read_text());protected=json.loads((B/'protected.json').read_text());before=json.loads((B/'backend_usage.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());after['entries']=[e for e in after['entries'] if e['status']!='reserved'];assert after['entries'][:len(before['entries'])]==before['entries']
for p,h in protected.items():assert sha(R/p)==h,p
gzdoc(E/'preservation.json.gz',protected)
for name in ('old_cpp.json','new_cpp.json','old_native_test_source.cpp','yosys_threading_note.json','yosys_threading_excerpt.cc.txt','user_heading.diff','portable_checks.json','final_audit.json'):
 if (B/name).exists():copy(B/name,E/name)
identities=[]
for p in sorted((B/'generated').glob('*.json')):
 old=R/'build/step6-integration-20261031/release'/p.name;assert p.read_bytes()==old.read_bytes();assert p.with_suffix('.sv').read_bytes()==old.with_suffix('.sv').read_bytes()
 identities.append({'name':p.stem,'report_sha256':sha(p),'rtl_sha256':sha(p.with_suffix('.sv'))})
write(E/'regenerated_identity.json',identities)
copy(B/'capacity-admission-v2.json',C/'admission.json');copy(B/'physical-outcome-v2.json',C/'outcome.json')
copy(B/'thread-admission-v3.json',C/'thread_correction/admission.json');copy(B/'physical-outcome-v3.json',C/'thread_correction/outcome.json')
copy(B/'completion-admission-v4.json',C/'completion/admission.json');copy(B/'physical-outcome-v4.json',C/'completion/outcome.json')
clock=R/'build/step6-relaxed-clock-20261102';clock_admission=json.loads((clock/'admission-v5.json').read_text());clock_raw=json.loads((clock/'outcome.json').read_text());clock_id=clock_admission['tasks'][0]['id']
copy(clock/'admission-v5.json',C/'clock_relaxation/admission.json');copy(clock/'outcome.json',C/'clock_relaxation/raw-outcome.json')
write(C/'clock_relaxation/outcome.json',{'version':'step6-clock-relaxation-outcome-v1','runs':[{'task_id':clock_id,**clock_raw}]})
for name in ('completion-verification.json','case-role-audit.json','diagnosis.json','previous-logs-index.json'):
 copy(clock/name,E/name)
runsets=[(B/'physical',C),(B/'physical-threads',C/'thread_correction'),(B/'physical-complete',C/'completion')]
for base,target in runsets:
 for manifest in sorted(base.glob('*/manifest.json')):
  run=manifest.parent;dest=target/'runs'/run.name;m=json.loads(manifest.read_text());gz(manifest,dest/'manifest.json.gz');gz(run/'input.sv',dest/'input.sv.gz');gz(run/'liberty_cells.json',dest/'liberty_cells.json.gz');gz(run/'effective-environment.txt',dest/'effective-environment.txt.gz')
  if m.get('observational_checkpoint'):
   gz(run/'flow-scripts/synth.tcl',dest/'executed_synth.tcl.gz');gz(R.parent/'OpenROAD-flow-scripts/flow/scripts/synth.tcl',dest/'base_synth.tcl.gz')
  for metric in m['metrics']:
   stage=metric['stage'];prefix={'synth':'1_synth','grt':'5_1_grt'}[stage];gz(run/'results/asap7/arithmetic_probe/base'/(prefix+'.sdc'),dest/(prefix+'.sdc.gz'))
   for p in (run/'reports/asap7/arithmetic_probe/base').glob('vulsim_'+stage+'*'):
    if p.suffix in ('.rpt','.tsv') and not p.name.endswith('_instances.tsv'):gz(p,dest/'reports'/(p.name+'.gz'))
  for command in m['commands']:
   stem=Path(command['log']).stem;copy(run/(stem+'.command.json'),dest/'commands'/(stem+'.json'));copy(run/(stem+'.resources.txt'),dest/'commands'/(stem+'.GNU-time.txt'));gz(run/(stem+'.log'),dest/'commands'/(stem+'.log.gz'))
run=clock/'run';dest=C/'clock_relaxation/runs'/clock_id;m=json.loads((run/'manifest.json').read_text())
for name in ('manifest.json','input.sv','liberty_cells.json','effective-environment.txt'):gz(run/name,dest/(name+'.gz'))
for metric in m['metrics']:
 stage=metric['stage'];prefix={'synth':'1_synth','grt':'5_1_grt'}[stage];gz(run/'results/asap7/arithmetic_probe/base'/(prefix+'.sdc'),dest/(prefix+'.sdc.gz'))
 for p in (run/'reports/asap7/arithmetic_probe/base').glob('vulsim_'+stage+'*'):
  if p.suffix in ('.rpt','.tsv') and not p.name.endswith('_instances.tsv'):gz(p,dest/'reports'/(p.name+'.gz'))
for command in m['commands']:
 stem=Path(command['log']).stem;copy(run/(stem+'.command.json'),dest/'commands'/(stem+'.json'));copy(run/(stem+'.resources.txt'),dest/'commands'/(stem+'.GNU-time.txt'));gz(run/(stem+'.log'),dest/'commands'/(stem+'.log.gz'))
if (B/'artifact_catalog.json').exists():gz(B/'artifact_catalog.json',C/'artifact_catalog.json.gz')
extra=after['entries'][len(before['entries']):];prefix=R/'experiments/arithmetic/evidence/step6_whole_graph_v1/usage_delta.json';write(E/'usage_delta.json',{'prefix':rel(prefix),'prefix_sha256':sha(prefix),'entries':extra})
receipts=[]
for entry in extra:
 path=Path(entry['command_record']);r=json.loads(path.read_text());receipt={'id':entry['id'],'record':r,'GNU_time':Path(r['gnu_time']).read_text(),'actual_command_record_sha256':sha(path),'actual_log_sha256':sha(Path(r['log']))}
 sources=path.with_name(path.name.replace('.command.json','.sources.json'))
 if sources.exists():receipt['actual_source_sha256']=json.loads(sources.read_text())
 receipts.append(receipt)
 if entry['stage'] is None:gz(Path(r['log']),E/'logs'/(entry['id']+'.log.gz'))
gzdoc(E/'receipts.json.gz',receipts)
write(E/'resources.json',{'baseline_usage':usage(before['entries']),'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'global_caps_changed':False,'failed_leaves':sum(e.get('exit_code',0)!=0 for e in extra),'new_physical_calls':{s:sum(e['stage']==s for e in extra) for s in ('synth','grt','final')},'CPU_note':'actual GNU time when available; terminated commands with missing GNU time retain full CPU reservations; Yosys unbounded-pool v2 attempt preserved separately from worker-capped v3','pending':0})
# Only the appended review subsection has a live resource table. Original step6
# table, all old freezes, raw manifests and every previous charge are untouched.
p=R/'mission/lxy-plan-fix.md';text=p.read_text();start='<!-- step6-review-resources:start -->';end='<!-- step6-review-resources:end -->'
if start in text:
 a=usage(before['entries']);n=usage(extra);u=usage(after['entries']);table=['| 资源 | 本轮开始前 | 本轮新增 | 累计 |','| --- | ---: | ---: | ---: |',f"| synth / grt / final | {a['synth']} / {a['grt']} / {a['final']} | {n['synth']} / {n['grt']} / {n['final']} | {u['synth']} / {u['grt']} / {u['final']} |",f"| support叶命令 | {a['support_calls']} | {n['support_calls']} | {u['support_calls']} |",f"| 墙钟秒 | {a['walltime_s']:.6f} | {n['walltime_s']:.6f} | {u['walltime_s']:.6f} |",f"| CPU计费秒 | {a['CPU_time_s']:.6f} | {n['CPU_time_s']:.6f} | {u['CPU_time_s']:.6f} |",'| pending | 0 | 0 | 0 |'];left,tail=text.split(start,1);_,right=tail.split(end,1);p.write_text(left+start+'\n\n'+'\n'.join(table)+'\n\n'+end+right)
paths=set(parent['files_sha256']);new={'rtlzz/testv2/divisor_contract_test.cpp','regression/arithmetic_divisor.py','regression/arithmetic_bounded_recheck.py','regression/arithmetic_documentation_snapshot.py','regression/arithmetic_clock_relaxation.py','experiments/arithmetic_dse/bounded_recheck.py','experiments/arithmetic_dse/clock_relaxation.py','experiments/arithmetic_dse/whole_graph_review_evidence.py'};paths|=new
for base,cmd in [('', ['git','diff','--name-only']),('rtlzz/', ['git','-C','rtlzz','diff','--name-only'])]:
 for path in subprocess.check_output(cmd,text=True).splitlines():
  name=base+path
  if name.startswith(('rtlzz/src/','experiments/arithmetic_dse/','regression/','mission/','experiments/arithmetic/README','experiments/arithmetic/evidence/README')) and (R/name).is_file():paths.add(name)
snapshots={}
for path in sorted(paths):
 if parent['files_sha256'].get(path)==sha(R/path):snapshots[path]=parent['source_snapshots'][path]
 else:q=E/'source_delta'/path;copy(R/path,q);snapshots[path]=rel(q)
write(E/'file_changes.json',[{'path':p,'before_sha256':parent['files_sha256'].get(p),'after_sha256':sha(R/p)} for p in sorted(paths) if parent['files_sha256'].get(p)!=sha(R/p)])
for name in ('support.py','software_validation.py','prepare_recheck.py','run_recheck.py','prepare_thread_correction.py','run_thread_correction.py','prepare_completion.py','run_completion.py','thread_source_note.py','archive_review.py','package_artifacts.py','portable_checks.py','final_check.py','final_software.py'):
 if (B/name).exists():copy(B/name,E/'procedures'/name)
for name in ('support.py','launch.py','archive_logs.py','verify_completion.py'):
 copy(clock/name,E/'procedures/clock_relaxation'/name)
packages=[]
for directory,role in [(E,'software'),(C,'capacity')]:
 index=directory/'index.json';write(index,{'version':'step6-review-'+role+'-index-v2','files_sha256':{rel(p):sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts}});packages.append({'role':role,'index':rel(index),'sha256':sha(index)})
write(F,{'version':'whole-graph-freeze-v2','frozen_at':datetime.now(timezone.utc).isoformat(),'scope':'P1 actual-width divisor certificates and real native historical replay; user heading retained, editable narrative snapshots; bounded 32GiB rechecks and explicit Yosys worker limit correction, original failures/costs retained; no D/training/main matrix','files_sha256':{p:sha(R/p) for p in sorted(paths)},'source_snapshots':snapshots,'historical_freezes':{**parent['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'source_delta'),*parent['historical_source_roots']],'retired_active_paths':parent.get('retired_active_paths',[]),'evidence_directory':rel(E),'capacity_directory':rel(C),'packages':packages,'preservation':rel(E/'preservation.json.gz'),'remote_artifact_retention_confirmed':False,'P1_corrected':True,'new_RTL_circuit_change':False,'mutable_documentation_policy':'explicit narrative paths use protected original snapshots; current drift reported; source and cost configs remain strict'})
print(json.dumps({'packages':{rel(d):sum(p.stat().st_size for p in d.rglob('*') if p.is_file())+(F.stat().st_size if d==E else 0) for d in (E,C)},'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'old_files_preserved':len(protected)},indent=2))
