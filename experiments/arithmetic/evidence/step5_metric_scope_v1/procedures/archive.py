from pathlib import Path
from datetime import datetime,timezone
import gzip,hashlib,json,shutil,subprocess,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step5-metric-scope-20261031';E=R/'experiments/arithmetic/evidence/step5_metric_scope_v1';P=R/'experiments/arithmetic/mul_templates_freeze_v2.json';F=R/'experiments/arithmetic/mul_templates_freeze_v3.json'
from experiments.arithmetic_dse.metric_scope_evidence import analyze
from experiments.arithmetic_dse.budget import usage
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:str(p.relative_to(R))
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
parent=json.loads(P.read_text());protected=json.loads((B/'protected.json').read_text())
for path,h in protected.items():assert sha(R/path)==h,path
E.mkdir(parents=True,exist_ok=True);write(E/'analysis.json',analyze(R));(E/'preservation.json.gz').write_bytes(gzip.compress((json.dumps(protected,indent=2)+'\n').encode(),mtime=0))
sta=Path('/home/zyrv/OpenROAD-flow-scripts/tools/OpenROAD/src/sta');source=sta/'search/Sta.cc';raw=source.read_text();start=raw.index('void\nMinPeriodEndVisitor::visit(');end=raw.index('\nbool\nMinPeriodEndVisitor::pathIsFromInputPort',start);excerpt=raw[start:end];(E/'MinPeriodEndVisitor.cc.txt').write_text(excerpt)
manifest=json.loads(gzip.decompress((R/'experiments/arithmetic/evidence/step5_mul_capacity_v2/manifest.json.gz').read_bytes()))
write(E/'tool_source.json',{'source_path':str(source),'full_source_sha256':sha(source),'excerpt_sha256':hashlib.sha256(excerpt.encode()).hexdigest(),'openroad_source_commit':subprocess.check_output(['git','-C',str(sta.parent.parent),'rev-parse','HEAD'],text=True).strip(),'OpenSTA_source_commit':subprocess.check_output(['git','-C',str(sta),'rev-parse','HEAD'],text=True).strip(),'OpenSTA_worktree_clean':not subprocess.check_output(['git','-C',str(sta),'status','--short'],text=True).strip(),'actual_tool':manifest['tools']['openroad'],'scope':'source tree commit matches runtime reported OpenROAD commit; installed binary identity remains the original manifest identity; no recompilation or new STA run'})
before=json.loads((B/'backend_usage.json').read_text());after=json.loads((R/'experiments/arithmetic/backend_usage.json').read_text());assert after['entries'][:len(before['entries'])]==before['entries'];assert not usage(after['entries'])['pending'];delta=after['entries'][len(before['entries']):];assert all(x['stage'] is None for x in delta)
prefix=R/parent['evidence_directory']/'usage_delta.json';write(E/'usage_delta.json',{'prefix':rel(prefix),'prefix_sha256':sha(prefix),'entries':delta});write(E/'resources.json',{'new_usage':usage(delta),'cumulative_usage':usage(after['entries']),'physical_calls':0,'global_budget_changed':False})
receipts=[]
for item in delta:
 record=Path(item['command_record']);d=json.loads(record.read_text());target=E/'commands'/item['id'];copy(record,target/'command.json');copy(Path(d['gnu_time']),target/'GNU-time.txt');copy(Path(d['log']),target/'log.txt');receipts.append({'id':item['id'],'record':rel(target/'command.json'),'CPU_report':rel(target/'GNU-time.txt')})
write(E/'command_index.json',receipts)
for name in ('archive.py','support.py','audit.py'):
 if (B/name).exists():copy(B/name,E/'procedures'/name)
if (B/'audit.json').exists():copy(B/'audit.json',E/'audit.json')
paths=set(parent['files_sha256'])|{'experiments/arithmetic_dse/timing_metric_scopes.md','experiments/arithmetic_dse/metric_scope_evidence.py'};snapshots={}
for path in sorted(paths):
 if parent['files_sha256'].get(path)==sha(R/path):snapshots[path]=parent['source_snapshots'][path]
 else:target=E/'source_delta'/path;copy(R/path,target);snapshots[path]=rel(target)
index=E/'index.json';write(index,{'version':'STA-scope-evidence-v1','files_sha256':{rel(p):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index and '__pycache__' not in p.parts}})
write(F,{'version':'mul-templates-freeze-v3','scope':'saved STA report interpretation and admission documentation only; no change to RTL, SDC, backend metrics or physical results','files_sha256':{p:sha(R/p) for p in sorted(paths)},'source_snapshots':snapshots,'historical_freezes':{**parent['historical_freezes'],rel(P):sha(P)},'historical_source_roots':[rel(E/'source_delta'),*parent['historical_source_roots']],'retired_active_paths':parent['retired_active_paths'],'evidence_index':rel(index),'evidence_index_sha256':sha(index),'evidence_directory':rel(E),'physical_evidence_inherited_from':rel(P),'frozen_at':datetime.now(timezone.utc).isoformat()})
print(json.dumps({'new_usage':usage(delta),'package_bytes':sum(p.stat().st_size for p in E.rglob('*') if p.is_file())+F.stat().st_size,'old_frozen_payloads_preserved':len(protected)},indent=2))
