"""Read-only collection coverage/resource snapshot, no locked-test label reads."""
import argparse
from collections import Counter
from pathlib import Path
import shutil
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write
from experiments.arithmetic_dse.budget import usage
from experiments.arithmetic_dse.model_three_region_scan import decide


def status(root,out):
    progress=read(root/'progress.json');counts=Counter();regions=Counter();stops=Counter();source_counts=Counter();completed_sources=Counter();failures=[]
    for row in read(root/'corpus/manifest.json')['sources']:
        if row['role']=='locked_test':continue
        path=root/'raw'/row['id']/'history.json';history=read(path) if path.exists() else []
        source_counts[row['role']]+=bool(history);d=decide(history,row['id'],row['role']);completed_sources[row['role']]+=d['next_request'] is None
        for point in history:
            counts[row['role']+'/'+point['status']]+=1
            if point['status']=='failed':failures.append(dict(source=row['id'],reason=point['failure_reason']))
        for bucket in d['regions']:regions[bucket['region']]+=bucket['effective_points']
        if d['next_request'] is None:stops[d['stop_reason']]+=1
    ledger=read(ROOT/'experiments/arithmetic/backend_usage.json');cfg=read(root/'collection.json');increment=usage(ledger['entries'][cfg['baseline_entries']:])
    result=dict(phase=progress['phase'],completed_points=progress['completed_points'],points=dict(counts),sources_started=dict(source_counts),sources_scan_finished=dict(completed_sources),
        regions=dict(regions),stop_reasons=dict(stops),active_source_failures=failures,resource_increment=increment,
        free_disk_bytes=shutil.disk_usage(root).free,locked_test_labels_read=False)
    write(out,result);print(result,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();status(a.root,a.out)
