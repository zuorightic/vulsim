"""Compact retest evidence plus an explicit local complete-artifact catalog."""
from pathlib import Path
import gzip,hashlib,io,json,shutil,tarfile
R=Path.cwd();B=R/'build/step5-closure-20261031';run=B/'capacity-retest'
E=R/'experiments/arithmetic/evidence/step5_mul_capacity_v2';STORE=R/'experiments/arithmetic/artifact_store/step5_mul_capacity_v2'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,d):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def copy(p,q):q.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,q)
def compress(p,q):q.parent.mkdir(parents=True,exist_ok=True);q.write_bytes(gzip.compress(p.read_bytes(),mtime=0))
m=json.loads((run/'manifest.json').read_text());assert m['status'] in ('completed','failed')
E.mkdir(parents=True,exist_ok=True);STORE.mkdir(parents=True,exist_ok=True)
copy(B/'capacity-retest-admission.json',E/'admission.json');copy(B/'timing.json',E/'timing.json');compress(run/'manifest.json',E/'manifest.json.gz')
for name in ('input.sv','effective-environment.txt','config.mk'):copy(run/name,E/name)
compress(run/'liberty_cells.json',E/'liberty_cells.json.gz')
for p in (run/'reports').rglob('*'):
 if p.is_file() and p.suffix!='.v' and not p.name.endswith('_instances.tsv'):compress(p,E/'reports'/(str(p.relative_to(run/'reports'))+'.gz'))
for name in ('1_synth.sdc','5_1_grt.sdc'):
 p=run/'results/asap7/arithmetic_probe/base'/name
 if p.exists():compress(p,E/(name+'.gz'))
for p in (run/'logs/asap7/arithmetic_probe/base').glob('*.log'):compress(p,E/'stage_logs'/(p.name+'.gz'))
sources=[]
for relative,h in m['source_sha256'].items():
 p=run/'source'/relative;assert sha(p)==h;target=E/'execution_sources'/(h+'.gz')
 if not target.exists():compress(p,target)
 sources.append({'path':relative,'sha256':h,'snapshot':str(target.relative_to(R))})
write(E/'execution_sources.json',sources)
archive=STORE/'ASAP7-W128-postsynth-grt-complete.tar.gz';members=[]
# The full directory includes actual checkpoint/result bytes, tool logs, rendered
# flow scripts and launch-source snapshots. No whole PDK is copied.
with archive.open('wb') as output:
 with gzip.GzipFile(filename='',mode='wb',fileobj=output,mtime=0) as gz:
  with tarfile.open(mode='w',fileobj=gz) as tar:
   for p in sorted(run.rglob('*')):
    if not p.is_file() or '__pycache__' in p.parts:continue
    raw=p.read_bytes();name=str(p.relative_to(run));entry=tarfile.TarInfo(name);entry.size=len(raw);entry.mtime=0;entry.mode=0o644;tar.addfile(entry,io.BytesIO(raw));members.append({'relative_member_path':name,'sha256':hashlib.sha256(raw).hexdigest(),'content_size_bytes':len(raw)})
catalog=[{'artifact_id':'step5-ASAP7-W128-retest-complete','location':str(archive.relative_to(R)),'encoding':'tar+gzip','stored_sha256':sha(archive),'stored_size_bytes':archive.stat().st_size,'availability_status':'available_locally; durable_remote_retention_not_confirmed','license_or_source_constraints':'generated run products and launch scripts under local tool/platform licenses; no whole PDK copied','members':members}]
write(E/'artifact_catalog.json',catalog)
write(E/'summary.json',{'version':'step5-capacity-retest-v1','task_id':m['task_id'],'source_task_id':'asap7-mul128-C-capacity-v1','status':m['status'],'failure_code':m.get('failure_code'),'metrics':m['metrics'],'full_chain_timing':'timing.json','new_calls':{'synth':0,'grt':1,'final':0},'scope':'exact admitted C implementation only; full new post-synthesis chain; no original paired run, no scale/split attribution, no blanket batch release','source_manifest_sha256':m['checkpoint_reuse']['source_manifest_sha256']})
index=E/'index.json';write(index,{'version':'step5-capacity-evidence-index-v2','files_sha256':{str(p.relative_to(R)):sha(p) for p in sorted(E.rglob('*')) if p.is_file() and p!=index}})
print({'package':str(E.relative_to(R)),'files':len(json.loads(index.read_text())['files_sha256']),'bytes':sum(p.stat().st_size for p in E.rglob('*') if p.is_file()),'local_complete_artifact_bytes':archive.stat().st_size})
