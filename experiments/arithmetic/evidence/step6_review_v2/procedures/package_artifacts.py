from pathlib import Path
import hashlib,json,tarfile
R=Path.cwd();B=R/'build/step6-review-20261102';store=R/'experiments/arithmetic/artifact_store/step6-review';store.mkdir(parents=True,exist_ok=True);tmp=store/'new-content.tar.gz';members=[]
files=[]
for base in ('physical','physical-threads','physical-complete'):
 for p in sorted((B/base).rglob('*')):
  preserved_log_link=(p.is_symlink() and p.suffix=='.log' and p.resolve().is_relative_to(B/'archived_udr_logs'))
  if p.is_file() and (not p.is_symlink() or preserved_log_link) and '__pycache__' not in p.parts:files.append((p,str(p.relative_to(B))))
clock=R/'build/step6-relaxed-clock-20261102';task=json.loads((clock/'admission-v5.json').read_text())['tasks'][0]['id']
for p in sorted((clock/'run').rglob('*')):
 if p.is_file() and not p.is_symlink() and '__pycache__' not in p.parts:files.append((p,str(Path('clock_relaxation')/task/p.relative_to(clock/'run'))))
with tarfile.open(tmp,'w:gz',dereference=True) as tar:
 for p,name in files:
  raw=p.read_bytes();tar.add(p,arcname=name,recursive=False);members.append({'relative_member_path':name,'sha256':hashlib.sha256(raw).hexdigest(),'content_size_bytes':len(raw)})
h=hashlib.sha256(tmp.read_bytes()).hexdigest();dest=store/(h+'.tar.gz');tmp.rename(dest)
row={'artifact_id':'step6-reviewed-capacity-complete-runs','sha256':hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'content_size_bytes':sum(x['content_size_bytes'] for x in members),'encoding':'tar+gzip','stored_sha256':h,'stored_size_bytes':dest.stat().st_size,'relative_member_path':'see members','location':str(dest.relative_to(R)),'availability_status':'local ignored store available; remote durable retention unconfirmed','license_or_source_constraints':'project runtime reports/checkpoints and actual run source snapshots; PDK/tool installations referenced by hash, not copied','members':members};(B/'artifact_catalog.json').write_text(json.dumps([row],indent=2)+'\n');print(json.dumps({k:v for k,v in row.items() if k!='members'},indent=2))
