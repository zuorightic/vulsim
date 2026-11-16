"""Reversible storage of settled physical ODBs; no EDA or price changes.

The original logical path, bytes, digest and metadata are kept in a per-batch
index. A verified gzip is published before removing an original ODB. Running
batches are refused. Report/readout/RTL/netlist files stay directly readable.
"""
import argparse
import fcntl
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil


def digest(path, compressed=False):
    h=hashlib.sha256()
    with (gzip.open(path,'rb') if compressed else Path(path).open('rb')) as stream:
        for block in iter(lambda:stream.read(2**20),b''):h.update(block)
    return h.hexdigest()


def write_index(path,doc):
    temp=path.with_suffix('.tmp');temp.write_text(json.dumps(doc,indent=2)+'\n')
    os.replace(temp,path)


def settled(batch):
    if json.loads((batch/'progress.json').read_text())['status']!='batch_settled':
        raise ValueError('only a settled physical batch may be packed or restored')
    # An additional worker may still own a transferred task after the old
    # dispatcher has rejected its later duplicate claim. Never archive live DBs.
    from .budget import LEDGER
    if LEDGER.exists():
        admission=batch/'admission.json'
        if admission.exists():
            identity=json.loads(admission.read_text())['id']
            state=json.loads(LEDGER.read_text())
            if any(j['admission_id']==identity and j['status'] in ('active','unsettled') for j in state['jobs']):
                raise ValueError('batch still has an active or unsettled whole-job lease')


def pack(batch):
    batch=Path(batch).resolve();settled(batch);index=batch/'storage-index.json'
    with (batch/'storage-index.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        doc=json.loads(index.read_text()) if index.exists() else dict(
            version='settled-physical-ODB-gzip-v1',algorithm='gzip',
            original_bytes_retained=True,EDA_calls=0,files={})
        for p in sorted((batch/'runs').glob('*/results/**/*.odb')):
            settled(batch);name=str(p.relative_to(batch));target=p.with_suffix(p.suffix+'.gz')
            if name in doc['files']:
                row=doc['files'][name]
                if digest(p)!=row['original_sha256'] or digest(target)!=row['gzip_sha256']:
                    raise ValueError('previous archive or restored ODB changed')
                p.unlink();continue
            if target.exists():raise ValueError('unindexed archive exists: '+str(target))
            temp=target.with_suffix(target.suffix+'.tmp');stat=p.stat();identity=digest(p)
            with p.open('rb') as source,temp.open('xb') as destination:
                with gzip.GzipFile(filename='',mode='wb',fileobj=destination,compresslevel=3,mtime=0) as stream:
                    shutil.copyfileobj(source,stream,2**20)
                destination.flush();os.fsync(destination.fileno())
            if digest(temp,True)!=identity or digest(p)!=identity:
                raise ValueError('compressed-byte roundtrip failed')
            os.replace(temp,target)
            doc['files'][name]=dict(original_sha256=identity,original_size=stat.st_size,
                original_mode=stat.st_mode & 0o777,original_mtime_ns=stat.st_mtime_ns,
                gzip_path=str(target.relative_to(batch)),gzip_sha256=digest(target),gzip_size=target.stat().st_size)
            write_index(index,doc);p.unlink()
        return dict(batch=str(batch),files=len(doc['files']),
            original_bytes=sum(r['original_size'] for r in doc['files'].values()),
            stored_bytes=sum(r['gzip_size'] for r in doc['files'].values()),
            index_sha256=digest(index) if index.exists() else None)


def restore(batch):
    batch=Path(batch).resolve();settled(batch);index=batch/'storage-index.json'
    with (batch/'storage-index.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);doc=json.loads(index.read_text())
        for name,row in doc['files'].items():
            p=batch/name;compressed=batch/row['gzip_path']
            if digest(compressed)!=row['gzip_sha256'] or digest(compressed,True)!=row['original_sha256']:
                raise ValueError('archive byte identity failed')
            if p.exists():
                if digest(p)!=row['original_sha256']:raise ValueError('original ODB path occupied by different bytes')
                continue
            temp=p.with_suffix(p.suffix+'.restore.tmp')
            with gzip.open(compressed,'rb') as source,temp.open('xb') as destination:
                shutil.copyfileobj(source,destination,2**20)
                destination.flush();os.fsync(destination.fileno())
            if digest(temp)!=row['original_sha256']:raise ValueError('restored-byte identity failed')
            os.chmod(temp,row['original_mode']);os.utime(temp,ns=(row['original_mtime_ns'],row['original_mtime_ns']))
            os.replace(temp,p)
        return dict(batch=str(batch),restored=len(doc['files']),archive_retained=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['pack','restore']);p.add_argument('--batch',type=Path,required=True)
    a=p.parse_args();print((pack if a.action=='pack' else restore)(a.batch))
