"""Create only the new delta freeze; all parent bytes stay immutable."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import gzip,hashlib,json,shutil,sys
R=Path.cwd();sys.path.insert(0,str(R))
from experiments.arithmetic_dse.budget import usage,cpu_seconds
B=R/'build/step4-review-20261031';P=R/'experiments/arithmetic/arithmetic_interfaces_freeze_v1.json';F=R/'experiments/arithmetic/arithmetic_interfaces_freeze_v2.json';E=R/'experiments/arithmetic/evidence/step4_interfaces_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def compress(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
prior=json.loads(P.read_text());baseline=json.loads((B/'before_sha256.json').read_text());assert sha(P)==hashlib.sha256((B/'freeze-before.json').read_bytes()).hexdigest()
for path,h in baseline.items():
 if path.startswith('experiments/arithmetic/evidence/') or (path.startswith('experiments/arithmetic/') and 'freeze' in Path(path).name):assert sha(R/path)==h,path
checks=json.loads((B/'checks.json').read_text());reports=[];failures=[]
for i,item in enumerate(checks['reports']):
 source=R/item['generated_report'];label=source.stem if source.parent!=B/'generated' else source.stem
 if item.get('embedded_wrapper'):label='vul-kernel'
 target=E/'reports'/(label+'.json.gz');compress(source,target)
 report={k:v for k,v in item.items() if k not in ('generated_report','register_bits','register_count','graph_sha256','schedule_sha256','rtl_sha256')};report['report']=rel(target)
 if item.get('embedded_wrapper'):
  copy(R/item['rtl'],E/'vul-kernel.sv');copy(R/item['embedded_wrapper'],E/'vul-top.sv');report['rtl']=rel(E/'vul-kernel.sv');report['embedded_wrapper']=rel(E/'vul-top.sv')
 reports.append(report)
for item in checks['failure_reports']:
 source=R/item['generated_report'];target=E/'failures'/source.name;copy(source,target);failures.append({'report':rel(target),'failure_code':item['failure_code']})
write(E/'report_index.json',reports);write(E/'failure_index.json',failures);copy(B/'checks.json',E/'checks.json');compress(B/'type-tests.log',E/'type-tests.log.gz')
before=json.loads((B/'usage-before.json').read_text());parent_usage=R/prior['evidence_directory']/'usage_after.json';assert before['entries']==json.loads(parent_usage.read_text())['entries']
after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());assert after['entries'][:len(before['entries'])]==before['entries'];extra=after['entries'][len(before['entries']):];assert not usage(after['entries'])['pending'] and all(e['stage'] is None for e in extra)
write(E/'usage_delta.json',{'prefix':rel(parent_usage),'prefix_sha256':sha(parent_usage),'prefix_entries':len(before['entries']),'entries':extra})
receipts=[]
for entry in extra:
 p=Path(entry['command_record']);record=json.loads(p.read_text());target=E/'commands'/entry['id'];copy(p,target/'command.json');copy(Path(record['gnu_time']),target/'GNU-time.txt');compress(Path(record['log']),target/'log.gz')
 manifest=p.with_name(p.name.removesuffix('.command.json')+'.sources.json');h=sha(manifest);snapshot=E/'execution_source_identities'/h
 if not snapshot.exists():copy(manifest,snapshot)
 receipts.append({'id':entry['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt'),'log':rel(target/'log.gz'),'execution_source_identity':rel(snapshot)})
 assert abs(cpu_seconds(target/'GNU-time.txt')-entry['CPU_time_s'])<1e-9
write(E/'command_index.json',receipts);write(E/'resources.json',{'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'new_physical_calls':0,'global_caps_changed':False,'failed_support_leaves':sum(e['exit_code']!=0 for e in extra),'expected_failing_CLI_subcommands':len(checks['failure_reports']),'max_sampled_RSS_KiB':max(json.loads((R/x['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for x in receipts)})
parts=defaultdict(lambda:{'files':0,'content_bytes':0,'allocated_file_bytes':0})
for path in baseline:
 if path.startswith('experiments/arithmetic/evidence/'):
  p=R/path;key=Path(path).parts[3];parts[key]['files']+=1;parts[key]['content_bytes']+=p.stat().st_size;parts[key]['allocated_file_bytes']+=p.stat().st_blocks*512
write(E/'storage_inventory.json',{'scope':'pre-review protected evidence files, pyc excluded; no Git pack claim','directory_metadata_excluded':True,'parent_v1_index_members':len(json.loads((R/prior['evidence_index']).read_text())['files_sha256']),'parent_v1_files_including_index':parts['step4_interfaces_v1']['files'],'by_directory':dict(sorted(parts.items())),'total':{k:sum(row[k] for row in parts.values()) for k in ('files','content_bytes','allocated_file_bytes')},'future_300_500_MB':'unmeasured projection; freeze per-batch inventory before bulk work'})
paths=set(prior['files_sha256'])|{'.gitignore','experiments/arithmetic_dse/report_types.py','experiments/arithmetic_dse/configs/evidence_storage_v1.json','experiments/arithmetic_dse/evidence_storage.md','regression/arithmetic_report_types.py','experiments/arithmetic/evidence/README.md','experiments/arithmetic/evidence/step4/README.md','experiments/arithmetic/evidence/step4_review/README.md'}
snapshots={}
for path in sorted(paths):
 if prior['files_sha256'].get(path)==sha(R/path):snapshots[path]=prior['validated_source_snapshot']+'/'+path
 else:
  target=E/'source_delta'/path;copy(R/path,target);snapshots[path]=rel(target)
copy(Path(__file__),E/'archive_receipt.py');copy(B/'check_reports.py',E/'check_reports.py')
for name in ('portable_checks.py','portable_checks.json','preservation_checks.py','preservation_checks.json'):
 if (B/name).exists():copy(B/name,E/name)
index=E/'index.json';write(index,{'version':'arithmetic-interfaces-evidence-index-v2','files_sha256':{rel(p):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}})
write(F,{'version':'arithmetic-interfaces-freeze-v2','frozen_at':datetime.now(timezone.utc).isoformat(),'supersedes':{'path':rel(P),'sha256':sha(P),'reason':'report integer type and key-field schemas; historical navigation; prospective evidence retention'},'files_sha256':{path:sha(R/path) for path in sorted(paths)},'source_snapshots':snapshots,'historical_freezes':{**prior['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'source_delta'),prior['validated_source_snapshot'],*prior['historical_source_roots']],'retired_active_paths':prior['retired_active_paths'],'evidence_directory':rel(E),'evidence_index':rel(index),'evidence_index_sha256':sha(index),'no_new_functional_or_physical_measurements':True,'previous_freezes_modified':False,'scope':'step4 nonblocking report types/navigation/storage; inherited v1 computation/trace and step3 P1/P2 preserved'})
print(json.dumps({'source_files':len(paths),'new_source_snapshots':sum(v.startswith(rel(E)) for v in snapshots.values()),'new_evidence_files':len(json.loads(index.read_text())['files_sha256']),'package_bytes':sum(p.stat().st_size for p in E.rglob('*') if p.is_file() and '__pycache__' not in p.parts)+F.stat().st_size,'reports':len(reports),'new_usage':usage(extra)},indent=2))
