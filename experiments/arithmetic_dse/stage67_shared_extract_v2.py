"""Successor shared labels: actual grt FF inventory and immutable input audit.

Report-only successor; physical producers and previously collected snapshots
are unchanged. Does not measure or fit node delays or full stage paths.
"""
import argparse
import inspect
from pathlib import Path

from . import stage67_shared_collect_v1 as base
from .model_fast_preflight import read,write,sha


def extract(root,out,completed_subset=False):
    a=read(root/'admission.json')
    for n,h in a['sources'].items():
        if sha(base.ROOT/n)!=h or sha(root/'source'/n)!=h:raise ValueError('frozen metrology implementation drift '+n)
    if sha(a['protocol_path'])!=a['protocol_sha256']:raise ValueError('registered fitting protocol drift')
    for task in a['tasks']:
        if sha(task['rtl'])!=task['rtl_sha256'] or sha(task['endpoint_contract'])!=task['endpoint_sha256']:raise ValueError('actual registered physical input drift')
    text=inspect.getsource(base.extract)
    if completed_subset:
        text=text.replace("if p['phase']!='physical_batch_complete':raise ValueError('all admitted physical tasks must settle successfully before dataset')", "if p['active']:raise ValueError('wait for finite batch settlement')\n    a['tasks']=[t for t in a['tasks'] if t['id'] in p['completed']]")
    old="owners=readout.certificate(directory,directory,'grt',contract)"
    new=old+"\n        actual_FFs={n for n,m in owners['instances'].items() if owners['liberty'][m]['sequential']}\n        mapped_FFs={r['cell'] for w in state['words'] for r in w['rows'] if 'cell' in r}\n        if actual_FFs!=mapped_FFs:raise ValueError('physical grt storage differs from mapped semantic state')"
    if text.count(old)!=1:raise ValueError('frozen shared label callsite drift')
    text=text.replace(old,new).replace("setup_slack_ps=metrics.get('setup_worst_slack_ps'),","setup_slack_ps=metrics.get('setup_worst_slack_ps'),hold_slack_ps=metrics.get('hold_worst_slack_ps'),")
    namespace=dict(base.extract.__globals__);exec(compile(text,__file__,'exec'),namespace);namespace['extract'](root,out)
    d=read(out/'dataset.json');d.update(version='shared-compatible-dataset-v2',extractor_sha256=sha(Path(__file__)),actual_grt_storage_equal_mapped_proof=True)
    if completed_subset:d.update(excluded_failed_requests=read(root/'progress.json')['errors'],subset_has_no_claim_of_complete_training=True)
    write(out/'dataset.json',d)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--completed-subset',action='store_true');a=p.parse_args();extract(a.root.resolve(),a.out.resolve(),a.completed_subset)
