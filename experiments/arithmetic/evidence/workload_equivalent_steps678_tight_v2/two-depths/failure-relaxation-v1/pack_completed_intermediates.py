"""Reversibly gzip superseded ODBs of terminal, released current runs.

Keep final grt DBs, the latest failed-stage DB, reports, netlists and explicit
inputs directly readable. Never touch active or aborted runs. Earlier ODB bytes
remain recoverable; check each gzip against the original SHA before unlink.
"""
import argparse
import fcntl
import datetime
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

ROOT = Path('/home/zyrv/vulsim')
LIVE = ROOT.parent / 'vulsim-artifacts/workload-equivalent-two-depths-v1'
HERE = Path(__file__).resolve().parent
DEST = LIVE / 'storage-successors/completed-intermediates-v1'
NAMES = {'1_synth.odb','2_floorplan.odb','2_1_floorplan.odb','2_2_floorplan_macro.odb',
    '2_3_floorplan_tapcell.odb','2_4_floorplan_pdn.odb','3_place.odb','3_1_place_gp_skip_io.odb',
    '3_2_place_iop.odb','3_3_place_gp.odb','3_4_place_resized.odb','3_5_place_dp.odb',
    '4_cts.odb','4_1_cts.odb','4_1_post_repair_pre_lec.odb'}


def read(p): return json.loads(p.read_text())


def stamp(s): return s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_mode


def digest(p, compressed=False):
    h = hashlib.sha256()
    with (gzip.open(p,'rb') if compressed else p.open('rb')) as stream:
        for block in iter(lambda:stream.read(2**20),b''): h.update(block)
    return h.hexdigest()


def settled(run):
    outcome=run/'measurement-outcome.json'
    if not outcome.exists() or read(outcome).get('status') not in ('completed','failed'): return False
    state=read(ROOT/'experiments/arithmetic/backend_usage.json')
    jobs=[j for j in state.get('jobs',[]) if j['admission_id']==run.parents[1].name and j['task_id']==run.name]
    return len(jobs)==1 and jobs[0]['status']=='released'


def main(target):
    DEST.mkdir(parents=True,exist_ok=True)
    receipt=DEST/'receipt.json'
    doc=read(receipt) if receipt.exists() else dict(version='completed-intermediate-gzip-v1',files=[],
        authorization='Prior user request to remove unused backend results; reversible compression retains original bytes.',
        final_databases_preserved=True)
    doc.pop('failed_and_active_runs_preserved',None)
    doc.update(active_and_aborted_runs_untouched=True,
        latest_failed_stage_DB_preserved=True,all_original_ODB_bytes_recoverable=True)
    protected=set()
    for parent in ('backend','failure-successors','reference-successors'):
        for p in (LIVE/parent).glob('*/freeze.json'):
            protected.update(read(p).get('files',{}))
    candidates=[]
    runs=[*(LIVE/'backend').glob('*/runs/*'),*(LIVE/'failure-successors').glob('*/runs/*')]
    for run in runs:
        if not run.is_dir() or not settled(run): continue
        final=run/'results/asap7/arithmetic_probe/base/5_1_grt.odb'
        if not final.exists():
            databases=[p for p in final.parent.glob('*.odb') if p.is_file() and not p.is_symlink()]
            if not databases:continue
            # Failed, released runs are cold-retested in another directory.
            # Preserve their latest stage directly and every earlier byte in
            # the verified recovery index; retain all failure reports/logs.
            final=max(databases,key=lambda p:(int(p.name[0]) if p.name[0].isdigit() else -1,p.stat().st_mtime_ns))
        for p in final.parent.glob('*.odb'):
            if p!=final and p.name in NAMES and str(p) not in protected and not p.is_symlink() and p.stat().st_nlink==1:
                candidates.append((p.stat().st_size,p,run,final))
    for _,p,run,final in sorted(candidates,key=lambda r:r[0],reverse=True):
        if shutil.disk_usage(ROOT).free >= target*1024**3: break
        if not settled(run): raise ValueError('run no longer settled')
        st=p.stat(); fs=final.stat(); identity=digest(p); out=p.with_suffix('.odb.gz'); temp=p.with_suffix('.odb.gz.tmp')
        if out.exists() or temp.exists(): raise ValueError('unindexed gzip exists: '+str(p))
        with p.open('rb') as source,temp.open('xb') as destination:
            with gzip.GzipFile(filename='',mode='wb',fileobj=destination,compresslevel=1,mtime=0) as stream:
                shutil.copyfileobj(source,stream,2**20)
            destination.flush();os.fsync(destination.fileno())
        if digest(temp,True)!=identity or digest(p)!=identity or stamp(p.stat())!=stamp(st) or stamp(final.stat())!=stamp(fs) or not settled(run):
            raise ValueError('gzip roundtrip or immutable-run check failed')
        os.replace(temp,out)
        row=dict(path=str(p),gzip_path=str(out),original_sha256=identity,gzip_sha256=digest(out),
            original_bytes=st.st_size,gzip_bytes=out.stat().st_size,original_mtime_ns=st.st_mtime_ns,
            original_mode=st.st_mode & 0o777,final_DB=str(final),roundtrip_verified=True)
        doc['files'].append(row)
        # Publish the recovery index before removing a redundant original.
        tempindex=receipt.with_suffix('.tmp');tempindex.write_text(json.dumps(doc,indent=2)+'\n');os.replace(tempindex,receipt)
        p.unlink()
        print('PACKED',p.name,run.name,round((st.st_size-out.stat().st_size)/1024**2,1),'MiB',flush=True)
    doc.update(at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        saved_bytes=sum(r['original_bytes']-r['gzip_bytes'] for r in doc['files']),
        free_bytes_after=shutil.disk_usage(ROOT).free,
        failed_run_policy='Latest failed stage DB and all reports stay direct; superseded failed-stage bytes are recoverable in this index.',
        restore='gunzip -k the indexed gzip, then verify original_sha256; original modes/mtime are recorded.')
    receipt.write_text(json.dumps(doc,indent=2)+'\n');shutil.copyfile(receipt,HERE/'storage-receipt.json')
    print(json.dumps({k:doc[k] for k in ('saved_bytes','free_bytes_after')},indent=2),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--target-free-gib',type=float,default=40)
    p.add_argument('--watch-seconds',type=int,default=0)
    p.add_argument('--wait-lock',action='store_true',help='Wait for the current one-shot packer before maintaining space.')
    args=p.parse_args()
    DEST.mkdir(parents=True,exist_ok=True)
    with (DEST/'keeper.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX if args.wait_lock else fcntl.LOCK_EX|fcntl.LOCK_NB)
        deadline=time.monotonic()+args.watch_seconds
        while True:
            main(args.target_free_gib)
            if not args.watch_seconds or time.monotonic()>=deadline:break
            state=read(ROOT/'experiments/arithmetic/backend_usage.json')
            status=LIVE/'failure-successors/matrix-failure-relaxation-v2/controller-progress.json'
            if status.exists() and read(status).get('status')=='settled' and not any(j['status'] in ('active','unsettled') for j in state.get('jobs',[])):break
            time.sleep(30)
