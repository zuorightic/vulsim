"""Prepare new step6 evidence; never modify any inherited freeze or payload."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,sys,re
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-integration-20261031'
E=R/'experiments/arithmetic/evidence/step6_whole_graph_v1';G=R/'experiments/arithmetic/evidence/step6_graphs_v1';C=R/'experiments/arithmetic/evidence/step6_capacity_v1';F=R/'experiments/arithmetic/whole_graph_freeze_v1.json';P=R/'experiments/arithmetic/mul_templates_freeze_v3.json'
from experiments.arithmetic_dse.budget import usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def gz(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
def gzdoc(q,d):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress((json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode(),mtime=0))
for directory in (E,G,C):directory.mkdir(parents=True,exist_ok=True)
parent=json.loads(P.read_text());protected=json.loads((B/'protected.json').read_text());before=json.loads((B/'usage-before.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text())
assert after['entries'][:len(before['entries'])]==before['entries'];after['entries']=[e for e in after['entries'] if e['status']!='reserved']
# Prior frozen evidence, including every old failure and resource receipt, remains immutable.
for p,h in protected.items():assert sha(R/p)==h,p
gzdoc(E/'preservation.json.gz',protected)
items=json.loads((B/'fixtures-v3/items.json').read_text());gzdoc(E/'implementations.json.gz',items);bindings={}
for item in items:
 name=item['name'];report=json.loads((B/'release'/(name+'.json')).read_text());old=json.loads((B/'generated-v2'/(name+'.json')).read_text());oldrtl=B/'generated-v2'/(name+'.sv');current=B/'release'/(name+'.sv')
 for k in ('graph','stages','protocol','graph_sha256','schedule_sha256'):assert report[k]==old[k],(name,k)
 changed=oldrtl.read_bytes()!=current.read_bytes();assert not changed or item['case'].get('diagnostic')=='shared_divrem'
 bindings[name]={'graph_sha256':old['graph_sha256'],'schedule_sha256':old['schedule_sha256'],'executed_rtl_sha256':sha(oldrtl),'comments_changed':changed,'execution_source':'generated-v2 plus simulation-v2 actual build; final release has same graph/schedule/RTL logic'}
 if changed:gz(oldrtl,G/'execution_RTL'/(name+'.sv.gz'))
 gz(B/'release'/(name+'.json'),G/'reports'/(name+'.json.gz'));gz(current,G/'reports'/(name+'.sv.gz'))
gzdoc(E/'trace_bindings.json.gz',bindings)
for name,source in [('native','simulation-v2'),('exhaustive8','exhaustive8'),('circt','circt-simulation')]:
 directory=E/'replays'/name
 for fn in ('items.json','vectors.txt','rtl-run.log','mode.json'):
  if (B/source/fn).exists():gz(B/source/fn,directory/(fn+'.gz'))
 copy(B/source/'functional.json',directory/'functional.json')
source=B/'public-combined';target=E/'replays/public';gz(source/'items.json',target/'items.json.gz');copy(source/'functional.json',target/'functional.json');gz(source/'execution_bindings.json',target/'execution_bindings.json.gz')
for item in json.loads((source/'items.json').read_text()):
 name=item['case']['id'];fixture=Path(item['directory']);gz(fixture/'vectors.json',target/(name+'.vectors.json.gz'));gz(source/(name+'.log'),target/(name+'.log.gz'))
for name in ('software_audit.json','followups.json','contracts.json'):copy(B/name,E/name)
for name in ('portable_checks.json','final_audit.json'):
 if (B/name).exists():copy(B/name,E/name)
# Native/CIRCT/profile compilation receipts do not claim four-platform physical measurement.
for variant,directory in [('circt',B/'circt-generated')]+[(p,B/'platform-generated'/p) for p in ('nangate45','sky130hd','gf180')]:
 for report in directory.glob('*.json'):gz(report,G/'representatives'/variant/(report.name+'.gz'));gz(report.with_suffix('.sv'),G/'representatives'/variant/(report.stem+'.sv.gz'))
public=[]
for item in json.loads((B/'public-combined/items.json').read_text()):
 name=item['case']['id'];run=B/('public-final' if (B/'public-final'/name).exists() else 'public-remaining')/name;report=next(run.rglob('*.arithmetic.json'));r=json.loads(report.read_text());raw=(run/'sim/top.sv').read_bytes();start=raw.index(b'if (1) begin : __vul_pipeline_');start=raw.index(b'\n',start)+1;found=None
 for match in re.finditer(rb'(?m)^end\s*\n',raw[start:]):
  end=start+match.start()
  if hashlib.sha256(raw[start:end]).hexdigest()==r['rtl_sha256']:found=end;break
 assert found is not None,(name,'missing actual embedded kernel')
 gz(report,G/'public'/(name+'.json.gz'));gz(run/'sim/top.sv',G/'public'/(name+'.sv.gz'));public.append({'case':name,'actual_run':str(run),'byte_range':[start,found],'wrapper_sha256':sha(run/'sim/top.sv'),'report_sha256':sha(report),'L':item['L']})
write(E/'public_bindings.json',public)
copy(B/'capacity-admission.json',C/'admission.json');copy(B/'physical-outcome.json',C/'outcome.json');copy(B/'physical-postmortem.json',C/'postmortem.json')
for task in json.loads((C/'admission.json').read_text())['tasks']:
 run=B/'physical'/task['id'];target=C/'runs'/task['id']
 if not run.exists():continue
 gz(run/'manifest.json',target/'manifest.json.gz');gz(run/'input.sv',target/'input.sv.gz');copy(run/'synth.command.json',target/'synth.command.json');copy(run/'synth.resources.txt',target/'synth.GNU-time.txt');gz(run/'synth.log',target/'synth.log.gz')
 if (run/'results/asap7/arithmetic_probe/base/1_synth.sdc').exists():gz(run/'results/asap7/arithmetic_probe/base/1_synth.sdc',target/'1_synth.sdc.gz')
if (B/'artifact_catalog.json').exists():gz(B/'artifact_catalog.json',C/'artifact_catalog.json.gz')
extra=after['entries'][len(before['entries']):];prefix=R/'experiments/arithmetic/evidence/step5_metric_scope_v1/usage_delta.json';write(E/'usage_delta.json',{'prefix':rel(prefix),'prefix_sha256':sha(prefix),'entries':extra})
receipts=[]
for entry in extra:
 path=Path(entry['command_record']);record=json.loads(path.read_text());r={'id':entry['id'],'record':record,'GNU_time':Path(record['gnu_time']).read_text(),'actual_command_record_sha256':sha(path),'actual_log_sha256':sha(Path(record['log'])),'actual_log_content_bytes':Path(record['log']).stat().st_size}
 sources=path.with_name(path.name.replace('.command.json','.sources.json'))
 if sources.exists():r['actual_source_sha256']=json.loads(sources.read_text())
 receipts.append(r)
 # Complete support logs are compressed in the small package. Physical logs
 # remain in the separately indexed capacity package and external archive.
 if entry['stage'] is None:gz(Path(record['log']),E/'logs'/(entry['id']+'.log.gz'))
gzdoc(E/'receipts.json.gz',receipts)
nonzero=[{'id':x['id'],'stage':x['stage'],'task_id':x.get('task_id'),'status':x['status'],'exit_code':x.get('exit_code')} for x in extra if x.get('exit_code')]
write(E/'failures.json',nonzero)
launch=json.loads((C/'admission.json').read_text())['starting_usage_live'];launch_count=next(i for i in range(len(before['entries']),len(after['entries'])+1) if usage(after['entries'][:i])==launch);post=usage([x for x in after['entries'][launch_count:] if x['stage'] is None]);assert post['walltime_s']<=1800 and post['CPU_time_s']<=3600
write(E/'resources.json',{'baseline_usage':usage(before['entries']),'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'new_physical_calls':{s:sum(e['stage']==s for e in extra) for s in ('synth','grt','final')},'failed_leaves':len(nonzero),'post_admission_support_usage':post,'post_admission_support_envelope':{'walltime_s':1800,'CPU_time_s':3600},'post_admission_support_envelope_met':True,'global_caps_changed':False,'CPU_note':'GNU time actual when available; UDR memory kill lacks complete GNU time, full 600 CPU seconds reservation charged; samples do not refund charge','max_sampled_process_tree_RSS_KiB':max(r['record']['sampled_process_tree_peak_rss_KiB'] for r in receipts)})
# Reuse protected source bytes; new or changed paths get one incremental snapshot.
plan=R/'mission/lxy-plan-fix.md';text=plan.read_text();base=usage(before['entries']);inc=usage(extra);total=usage(after['entries'])
rows=['| 资源 | 本步开始前 | 本步新增 | 累计 |','| --- | ---: | ---: | ---: |',f"| synth / grt / final | {base['synth']} / {base['grt']} / {base['final']} | {inc['synth']} / {inc['grt']} / {inc['final']} | {total['synth']} / {total['grt']} / {total['final']} |",f"| support叶命令 | {base['support_calls']} | {inc['support_calls']} | {total['support_calls']} |",f"| 叶命令墙钟秒 | {base['walltime_s']:.6f} | {inc['walltime_s']:.6f} | {total['walltime_s']:.6f} |",f"| CPU计费秒 | {base['CPU_time_s']:.6f} | {inc['CPU_time_s']:.6f} | {total['CPU_time_s']:.6f} |",'| pending | 0 | 0 | 0 |']
start='<!-- step6-resources:start -->';end='<!-- step6-resources:end -->';left,tail=text.split(start,1);_,right=tail.split(end,1);plan.write_text(left+start+'\n\n'+'\n'.join(rows)+'\n\n'+end+right)
paths={p for p in parent['files_sha256'] if (R/p).is_file()}
new={'experiments/arithmetic_dse/whole_graph.py','experiments/arithmetic_dse/whole_graph_checks.py','experiments/arithmetic_dse/whole_graph_validation.py','experiments/arithmetic_dse/whole_graph_evidence.py','experiments/arithmetic_dse/whole_graph.md','rtlzz/testv2/arithmetic_suite_test.cpp','regression/arithmetic_whole_graph.py','regression/arithmetic_vul_suite.py','vullib/unsigned_divrem.hpp','experiments/arithmetic_dse/sdc.py','regression/arithmetic_sdc.py','mission/README.md','mission/lxy-plan-fix.md'}
paths|=new
# Capture all tracked changed implementation sources, including RTLzz submodule.
import subprocess
for base,cmd in [('', ['git','diff','--name-only']),('rtlzz/', ['git','-C','rtlzz','diff','--name-only'])]:
 for path in subprocess.check_output(cmd,text=True).splitlines():
  p=base+path
  if p.startswith(('rtlzz/src/','rtlzz/testv2/','experiments/arithmetic_dse/','regression/','vullib/')) and (R/p).is_file():paths.add(p)
snapshots={}
for path in sorted(paths):
 if parent['files_sha256'].get(path)==sha(R/path):snapshots[path]=parent['source_snapshots'][path]
 else:q=E/'source_delta'/path;copy(R/path,q);snapshots[path]=rel(q)
write(E/'file_changes.json',{'files':[{'path':p,'before_sha256':parent['files_sha256'].get(p),'after_sha256':sha(R/p),'kind':'modified' if p in parent['files_sha256'] else 'new_or_newly_bound'} for p in sorted(paths) if parent['files_sha256'].get(p)!=sha(R/p)],'historical_payload_files_preserved':len(protected),'ledger':'append only; use chained usage_delta','new_packages':[rel(E),rel(G),rel(C)]})
for name in ('archive_step6.py','postmortem.py','audit_software.py','check_public.py','prepare_capacity.py','run_capacity.py','support.py','software_followups.py','release_generation.py','package_artifacts.py','portable_checks.py','final_check.py'):
 if (B/name).exists():copy(B/name,E/'procedures'/name)
packages=[]
for directory,role in [(E,'software'),(G,'graphs'),(C,'capacity')]:
 index=directory/'index.json';write(index,{'version':'step6-'+role+'-index-v1','files_sha256':{rel(p):sha(p) for p in sorted(directory.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}});packages.append({'role':role,'index':rel(index),'sha256':sha(index)})
write(F,{'version':'whole-graph-freeze-v1','frozen_at':datetime.now(timezone.utc).isoformat(),'scope':'step6 software fixed-L whole graphs and two failed finite capacity attempts; no D model, grt success, main matrix or training labels','files_sha256':{p:sha(R/p) for p in sorted(paths)},'source_snapshots':snapshots,'historical_freezes':{**parent['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'source_delta'),*parent['historical_source_roots']],'retired_active_paths':parent['retired_active_paths'],'evidence_directory':rel(E),'graph_directory':rel(G),'capacity_directory':rel(C),'preservation':rel(E/'preservation.json.gz'),'packages':packages,'physical_measurement_results_inherited':rel(P),'remote_artifact_retention_confirmed':False,'full_step6_acceptance':False,'software_stage_accepted':True,'remaining':['UDR128 specific implementation exceeds 8GiB synth envelope','F2 grt and four sensitivity controls unmeasured after failure gate','other platform/scale capacity not established','D model inference is step7']})
print(json.dumps({'packages':{rel(d):sum(p.stat().st_size for p in d.rglob('*') if p.is_file())+(F.stat().st_size if d==E else 0) for d in (E,G,C)},'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'preserved':len(protected)},indent=2))
