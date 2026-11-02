from pathlib import Path
import hashlib,json,tarfile,sys
R=Path.cwd();sys.path.insert(0,str(R));B=R/'build/step6-integration-20261031';store=R/'experiments/arithmetic/artifact_store/step6';store.mkdir(parents=True,exist_ok=True)
files=[]
for p in sorted(B.rglob('*')):
 if not p.is_file() or p.is_symlink() or any(x in p.parts for x in ('obj','obj_dir','__pycache__')) or p.name in ('artifact_catalog.json',):continue
 # The archive contains actual generated RTL/graphs, raw traces, all command
 # logs, source variants available on disk and complete failed physical runs.
 # Executable/compiler caches are rebuildable and not preservation claims.
 files.append(p)
tmp=store/'step6-run-content.tar.gz';members=[]
with tarfile.open(tmp,'w:gz') as tar:
 for p in files:
  name=str(p.relative_to(B));raw=p.read_bytes();tar.add(p,arcname=name,recursive=False);members.append({'relative_member_path':name,'sha256':hashlib.sha256(raw).hexdigest(),'content_size_bytes':len(raw)})
h=hashlib.sha256(tmp.read_bytes()).hexdigest();dest=store/(h+'.tar.gz');tmp.rename(dest)
item={'artifact_id':'step6-actual-generated-traces-and-failed-capacity','sha256':hashlib.sha256(json.dumps(members,sort_keys=True,separators=(',',':')).encode()).hexdigest(),'content_size_bytes':sum(x['content_size_bytes'] for x in members),'encoding':'tar+gzip','stored_sha256':h,'stored_size_bytes':dest.stat().st_size,'relative_member_path':'see members','location':str(dest.relative_to(R)),'availability_status':'local_ignored_store_available; remote durable retention unconfirmed','license_or_source_constraints':'project sources and runtime reports/checkpoints; external PDK installation not copied; no rebuilt binaries or obj caches; early development source hashes do not promise recoverability of every transient edit','members':members}
(B/'artifact_catalog.json').write_text(json.dumps([item],indent=2)+'\n');print(json.dumps({'members':len(members),'bytes':item['content_size_bytes'],'stored_bytes':dest.stat().st_size,'location':item['location']},indent=2))
