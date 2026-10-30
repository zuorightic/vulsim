"""Assemble the software-only v7 successor; never write v5/v6 evidence."""
from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,sys
sys.path.insert(0,str(Path.cwd()))
from experiments.arithmetic_dse.budget import usage,cpu_seconds
R=Path.cwd();B=R/'build/step3-sdc-parser-20261030';E=R/'experiments/arithmetic/evidence/step3_platforms_v3';F=R/'experiments/arithmetic/backend_freeze_v7.json';P=R/'experiments/arithmetic/backend_freeze_v6.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
prior=json.loads(P.read_text());before=json.loads((B/'usage-before.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text())
assert before['entries']==after['entries'][:len(before['entries'])]
assert usage(after['entries'])['pending']==0
extra=after['entries'][len(before['entries']):];assert all(x['stage'] is None for x in extra)
copy(B/'usage-before.json',E/'usage_before.json');copy(R/'experiments/arithmetic/backend_usage.json',E/'usage_after.json')
receipts=[]
for entry in extra:
 source=Path(entry['command_record']);record=json.loads(source.read_text());d=E/'commands'/entry['id']
 copy(source,d/'command.json');copy(Path(record['gnu_time']),d/'GNU-time.txt');(d/'log.gz').write_bytes(gzip.compress(Path(record['log']).read_bytes(),mtime=0))
 assert abs(cpu_seconds(d/'GNU-time.txt')-entry['CPU_time_s'])<1e-8
 receipts.append({'id':entry['id'],'record':rel(d/'command.json'),'CPU_report':rel(d/'GNU-time.txt'),'log':rel(d/'log.gz')})
write(E/'command_index.json',receipts)
write(E/'resources.json',{'new_usage':usage(extra),'cumulative_usage':usage(after['entries']),'physical_runs_added':0,'global_caps_changed':False,'max_leaf_sampled_RSS_KiB':max(json.loads((R/x['record']).read_text())['sampled_process_tree_peak_rss_KiB'] for x in receipts)})
paths=set(prior['files_sha256'])|{'experiments/arithmetic_dse/configs/platform_parameter_sources_v1.json','experiments/arithmetic_dse/configs/platform_parameter_decisions_v1.md','experiments/arithmetic_dse/backend/handoff_checks.md','mission/README.md','mission/lxy-plan-fix.md','experiments/arithmetic/README.md'}
for path in paths:copy(R/path,E/'source_v7'/path)
copy(Path(__file__),E/'archive_receipt.py');copy(B/'collect_provenance.py',E/'collect_provenance.py')
index=E/'index.json';write(index,{'version':'platform-evidence-index-v3','scope':'software-only validator/provenance closure; v6 physical artifacts inherited','files_sha256':{rel(p):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts and p.suffix!='.pyc'}})
external=dict(prior['external_files_sha256'])
for v in json.loads((E/'parameter_source_excerpts.json').read_text())['sources'].values():
 if Path(v['path']).is_absolute() and Path(v['path']).is_relative_to('/home/zyrv/OpenROAD-flow-scripts'):external[v['path']]=v['sha256']
write(F,{'version':'arithmetic-backend-freeze-v7','frozen_at':datetime.now(timezone.utc).isoformat(),'files_sha256':{p:sha(R/p) for p in sorted(paths)},'validated_source_snapshot':rel(E/'source_v7'),'historical_freezes':{**prior['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'previous_source'),prior['validated_source_snapshot'],*prior['historical_source_roots']],'retired_active_paths':prior['retired_active_paths'],'evidence_directory':rel(E),'evidence_index':rel(index),'evidence_index_sha256':sha(index),'external_files_sha256':external,'source_base':prior['source_base'],'rtlzz_base':prior['rtlzz_base'],'measurement_freeze':{'path':rel(P),'sha256':sha(P)},'supersedes':{'path':rel(P),'sha256':sha(P),'previous_physical_acceptance_valid':True,'reason':'P2 strict static Tcl command boundaries; provenance and handoff closure; no physical parameter changes'},'sdc_contract_version':'serialized-sdc-contract-v2','effective_profiles_changed':False,'new_physical_runs':0,'scope':'four-platform connection revalidation only; GF180 wire RC calibration open; no model/main matrix','planning_reference':'mission/lxy-plan-fix.md 第一章§3.4，第四章步骤三§3.10'})
print(json.dumps({'source_files':len(paths),'new_evidence_files':len(json.loads(index.read_text())['files_sha256']),'new_usage':usage(extra)},indent=2))
