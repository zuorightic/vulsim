"""Portable replay of restored physical packets, no physical tools or fitting."""
import argparse
import gzip
import hashlib
import importlib
import json
import math
from pathlib import Path
import sys
import tempfile


def digest(b):return hashlib.sha256(b).hexdigest()


def equal(a,b):
    if isinstance(a,float) or isinstance(b,float):return isinstance(a,(int,float)) and isinstance(b,(int,float)) and math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-8)
    if isinstance(a,dict):return isinstance(b,dict) and a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if isinstance(a,(list,tuple)):return isinstance(b,(list,tuple)) and len(a)==len(b) and all(equal(x,y) for x,y in zip(a,b))
    return a==b


def replay(evidence):
    manifest=json.loads((evidence/'manifest.json').read_text());raw=b''
    for n,h in manifest['parts'].items():
        if Path(n).name!=n:raise ValueError('unsafe part')
        part=(evidence/n).read_bytes()
        if digest(part)!=h:raise ValueError('changed evidence part')
        raw+=part
    raw=gzip.decompress(raw)
    if digest(raw)!=manifest['payload_sha256']:raise ValueError('changed payload')
    payload=json.loads(raw)
    with tempfile.TemporaryDirectory(prefix='ownership-restored-') as tmp:
        tree=Path(tmp)
        for n,text in payload['files'].items():
            if Path(n).is_absolute() or '..' in Path(n).parts:raise ValueError('unsafe source member')
            p=tree/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
            if p.read_text()!=text:raise ValueError('restore changed member')
        sys.path.insert(0,str(tree/'source'))
        for n in list(sys.modules):
            if n=='experiments' or n.startswith('experiments.'):del sys.modules[n]
        reader=importlib.import_module('experiments.arithmetic_dse.model_logical_ownership_v2')
        if not Path(reader.__file__).is_relative_to(tree):raise ValueError('live reader used')
        stages=0
        for task in payload['tasks']:
            result=reader.extract(task['packet'],task['nodes'],task['banks'],task['ports'],task['certificate'])
            for k in ('nodes','operator_delay_ps','comb_area_um2','data_setup_slack_ps','owner_area_um2','total_cell_area_um2','path_decompositions'):
                if not equal(result[k],task['label'][k]):raise ValueError('restored strict label differs '+task['id']+'/'+k)
            stages+=1
    print(dict(status='passed_portable_ownership_replay',stages=stages,restored_source_files=len(payload['files']),floating_sum_tolerance=dict(abs=1e-8,rel=1e-12),new_synth=0,new_grt=0,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True);a=p.parse_args();replay(a.evidence.resolve())
