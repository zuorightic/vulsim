"""Archive portable metric evidence, plus separately catalogued large artifacts."""
from pathlib import Path
import gzip,hashlib,io,json,shutil,tarfile
R=Path.cwd();B=R/'build/step5-parameterized-20261031';E=R/'experiments/arithmetic/evidence/step5_mul_capacity_v1';STORE=R/'experiments/arithmetic/artifact_store/step5_mul_capacity_v1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
E.mkdir(parents=True,exist_ok=True);STORE.mkdir(parents=True,exist_ok=True)
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def compress(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
copy(B/'capacity-admission.json',E/'admission.json');summary=[];catalog=[]
for w in (64,128):
 run=B/f'capacity{w}';m=json.loads((run/'manifest.json').read_text());assert m['status'] in ('completed','failed')
 target=E/f'W{w}';compress(run/'manifest.json',target/'manifest.json.gz')
 task=next(t for t in json.loads((B/'capacity-admission.json').read_text())['tasks'] if t['id']==m['task_id'])
 assert sha(Path(task['compiler_report']))==task['compiler_report_sha256'];compress(Path(task['compiler_report']),target/'compiler-report-at-admission.json.gz')
 for name in ('input.sv','abc_speed.script','liberty_cells.json','effective-environment.txt','config.mk'):
  if (run/name).exists():
   if name.endswith('.json'):compress(run/name,target/(name+'.gz'))
   else:copy(run/name,target/name)
 # Small table/paths, coverage, units and SDC are genuinely present in Git.
 for p in (run/'reports').rglob('*'):
  if p.is_file() and p.suffix not in ('.v',) and not p.name.endswith('_instances.tsv'):
   compress(p,target/'reports'/(str(p.relative_to(run/'reports'))+'.gz'))
 for stage,name in [('synth','1_synth.sdc'),('grt','5_1_grt.sdc')]:
  p=run/'results/asap7/arithmetic_probe/base'/name
  if p.exists():compress(p,target/(name+'.gz'))
 # Source files at actual physical launch: retain references when the same bytes
 # already exist in the compiler package's parent/current snapshots.
 sources=[]
 for relative,h in m['source_sha256'].items():
  p=run/'source'/relative
  if not p.exists():
   candidates=list(run.rglob(Path(relative).name));p=next(x for x in candidates if x.is_file() and sha(x)==h)
  destination=E/'execution_sources'/h
  if not destination.exists():compress(p,destination.with_suffix('.gz'))
  sources.append({'path':relative,'sha256':h,'snapshot':str(destination.with_suffix('.gz').relative_to(R))})
 write(target/'execution_sources.json',sources)
 archive=STORE/(f'W{w}-complete-artifacts.tar.gz');members=[]
 files=[p for folder in ('reports','logs') for p in (run/folder).rglob('*') if p.is_file()]+[p for p in run.glob('*') if p.is_file() and (p.suffix=='.log' or p.name.endswith('.command.json') or p.name.endswith('.resources.txt'))]
 with archive.open('wb') as output:
  with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
   with tarfile.open(mode='w',fileobj=gz) as tar:
    for p in sorted(files):
     raw=p.read_bytes();name=str(p.relative_to(run));entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mtime=0;entry.mode=0o644;tar.addfile(entry,io.BytesIO(raw));members.append({'relative_member_path':name,'sha256':hashlib.sha256(raw).hexdigest(),'content_size_bytes':len(raw)})
 catalog.append({'artifact_id':f'step5-ASAP7-W{w}-complete','location':str(archive.relative_to(R)),'encoding':'tar+gzip','stored_sha256':sha(archive),'stored_size_bytes':archive.stat().st_size,'availability_status':'available_locally; durable_remote_retention_not_confirmed','license_or_source_constraints':'generated netlists/logs under local tool and platform licenses; no complete PDK copied','members':members})
 summary.append({'W':w,'status':m['status'],'task_id':m['task_id'],'metrics':m['metrics'],'failure_stage':m.get('failure_stage'),'failure_code':m.get('failure_code'),'failure_reason':m.get('failure_reason'),'directory':str(target.relative_to(R))})
write(E/'artifact_catalog.json',catalog);write(E/'summary.json',{'version':'step5-capacity-v1','runs':summary,'scope':'ASAP7 selected C double Mul; no original/split PPA comparison; no final/SPEF/DRC claim','portable_metric_recompute':True,'full_artifact_status':'local store catalogued and checked; remote retention unresolved; default portable verification does not claim full artifact replay'})
index=E/'index.json';write(index,{'version':'step5-capacity-evidence-index-v1','files_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index}})
print(json.dumps({'package':str(E.relative_to(R)),'bytes':sum(p.stat().st_size for p in E.rglob('*') if p.is_file()),'files':len(json.loads(index.read_text())['files_sha256']),'external_artifact_bytes':sum(x['stored_size_bytes'] for x in catalog)},indent=2))
