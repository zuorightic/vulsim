"""Reference continuation with the original paid synthesis metric JSON retained."""
import argparse
from pathlib import Path
import shutil
import sys
import types
from . import model_reference_collection as base
from . import model_reference_collection_v2 as v2
from .model_collection import sha,write

VERSION='reference-synthesis-metadata-continuation-v3'


def prepare(folder,parent,metadata_parent,reader_proof):
    stopped=v2.verify(metadata_parent);progress=base.read(metadata_parent/'progress.json')
    if progress['phase']!='stopped_on_error' or progress['active'] or {r['task_id'] for r in progress['errors']}!=set(stopped['capacity_pilots']):raise ValueError('settled synthesis-metadata stop required')
    for row in progress['errors']:
        if '1_synth.json' not in row['reason']:raise ValueError('unexpected reference continuation failure')
    v2.prepare(folder,parent,reader_proof);a=base.read(folder/'admission.json')
    source=Path(__file__).resolve();name=str(source.relative_to(base.ROOT));dest=folder/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,dest)
    a['sources'][name]=sha(source);a.update(execution_metadata_successor=VERSION,
        support_predecessor_admission=str(metadata_parent/'admission.json'),support_predecessor_sha256=sha(metadata_parent/'admission.json'),
        retained_synth_native_metrics={key:sha(Path(ref['directory'])/'logs'/base.SUFFIX/'1_synth.json') for key,ref in a['synth_resume'].items()})
    write(folder/'admission.json',a);verify(folder)
    print('reference metadata continuation v3 admitted; exact three synth checkpoints, no resynthesis',flush=True)


def verify(folder):
    a=v2.verify(folder)
    if a.get('execution_metadata_successor')!=VERSION or sha(a['support_predecessor_admission'])!=a['support_predecessor_sha256']:raise ValueError('reference metadata predecessor changed')
    for key,h in a['retained_synth_native_metrics'].items():
        if sha(Path(a['synth_resume'][key]['directory'])/'logs'/base.SUFFIX/'1_synth.json')!=h:raise ValueError('original synthesis metric JSON changed')
    return a


def install():
    from . import backend
    v2.install();evaluate=v2_evaluate=backend._evaluate
    def with_native_metric(args,ledger):
        a=verify(ledger.folder);result=evaluate(args,ledger)
        if args.task_id in a['synth_resume']:
            original=Path(a['synth_resume'][args.task_id]['directory'])/'logs'/base.SUFFIX/'1_synth.json'
            target=args.out/'logs'/base.SUFFIX/'1_synth.json';target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(original,target)
            m=base.read(args.out/'manifest.json');m['checkpoint_reuse']['native_synth_metric_sha256']=sha(target);m['checkpoint_reuse']['native_synth_metric_source']=str(original);write(args.out/'manifest.json',m)
        return result
    backend._evaluate=with_native_metric


def bootstrap_check(folder,out):
    from . import backend
    from .backend import stage_metrics,verify_orfs_area
    from .platforms import profile
    from .model_reference_labels_v2 import partition,labels
    from .model_reference_samples import spec
    from types import SimpleNamespace
    a=verify(folder);out.mkdir(parents=True,exist_ok=False);install();rows=[]
    for key,ref in a['synth_resume'].items():
        d=out/key;ledger=v2.ReferenceLedger(folder,next(t for t in a['tasks'] if t['id']==key));backend._evaluate(SimpleNamespace(out=d,task_id=key),ledger)
        # Reuse the already paid v2 read-only snapshot solely for this staging
        # check; actual resumed runs produce fresh snapshot leaves.
        previous=Path(a['support_predecessor_admission']).parent/'runs'/key
        shutil.copytree(previous/'reports',d/'reports')
        cells=base.read(d/'liberty_cells.json')['cells'];pins=base.read(a['Liberty_pin_table']);s=spec(key);p=profile('asap7')
        g=stage_metrics(d/'reports'/base.SUFFIX,'synth',cells,40500,selected=p);prefix=d/'reports'/base.SUFFIX/'vulsim_synth'
        ownership,instances,_=partition(prefix,pins,p,expected={n:s[n+'_bits'] for n in ('input_service','native_state','external_state')})
        paths=labels(prefix,s,40500,1,pins,instances)
        native=base.read(d/'logs'/base.SUFFIX/'1_synth.json')['synth__design__instance__area__stdcell'];verify_orfs_area(g['cell_area_um2'],native)
        if base.read(d/'manifest.json')['commands']:raise ValueError('inherited commands falsely represented as new leaves')
        rows.append({'id':key,'paths':len(paths),'native_synth_area_checked':True,'no_new_command_records':True})
    write(out/'proof.json',{'status':'passed','rows':rows,'synth_reexecuted':False,'grt_executed':False,'PPA_calls':0})
    print('reference exact-checkpoint staging and complete raw synthesis reparse passed',flush=True)


def run_task(folder,t):verify(folder);return v2.run_task(folder,t)
def run(folder):
    verify(folder);install();namespace=dict(base.run.__globals__);namespace.update(verify=verify,run_task=run_task)
    types.FunctionType(base.run.__code__,namespace)(folder)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','verify','bootstrap','run','status'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--parent',type=Path);p.add_argument('--metadata-parent',type=Path);p.add_argument('--proof',type=Path);p.add_argument('--out',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='prepare':prepare(folder,a.parent.resolve(),a.metadata_parent.resolve(),a.proof.resolve())
    elif a.action=='verify':verify(folder);print('reference metadata successor verified')
    elif a.action=='bootstrap':bootstrap_check(folder,a.out.resolve())
    elif a.action=='run':run(folder)
    else:base.status(folder)
