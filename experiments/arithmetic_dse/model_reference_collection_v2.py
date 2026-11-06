"""Reference reader successor; reuse exact paid synthesis ODBs without resynthesis."""
import argparse
import copy
import inspect
import json
from pathlib import Path
import shutil
import sys
import types

from . import model_reference_collection as base
from . import model_reference_labels as old_labels
from . import model_reference_labels_v2 as new_labels
from .budget import Ledger
from .model_collection import sha,write

VERSION='reference-execution-reader-and-synth-continuation-v2'
ROOT=base.ROOT


def paid_checkpoint(directory):
    m=base.read(directory/'manifest.json');entries={e['id']:e for e in base.read(Ledger().path)['entries']};owner=sha(directory.parent.parent/'admission.json')
    if m['status']!='failed' or m['failure_reason'] not in ('reference unknown path cell','unattributed functional cell: _1_'):
        raise ValueError('not the registered support-only reference failure')
    if not any(c['log'].endswith('/synth.log') and c['exit_code']==0 for c in m['commands']):raise ValueError('reference synthesis checkpoint missing')
    if any(c['log'].endswith('/grt.log') for c in m['commands']):raise ValueError('unexpected already-routed reference source')
    for c in m['commands']:
        e=entries[c['budget_reservation_id']]
        if e['status']!='completed' or e['command']!=c['command'] or e.get('admission_sha256')!=owner or c['exit_code'] or c['cleanup']['remaining_live_pids']:
            raise ValueError('reference source leaf not paid/complete')
    for name,h in m['evidence_sha256'].items():
        if sha(directory/name)!=h:raise ValueError('reference raw synthesis evidence changed')
    return m


def preflight(parent,out):
    from .model_reference_samples import spec
    from .platforms import profile
    a=base.verify(parent);progress=base.read(parent/'progress.json')
    if progress['phase']!='stopped_on_error' or progress['active'] or {x['task_id'] for x in progress['errors']}!=set(a['capacity_pilots']):raise ValueError('settled three-pilot reader stop required')
    out.mkdir(parents=True,exist_ok=False);cells=base.read(a['Liberty_pin_table']);rows=[]
    for key in a['capacity_pilots']:
        directory=parent/'runs'/key;paid_checkpoint(directory);prefix=directory/'reports'/base.SUFFIX/'vulsim_synth';s=spec(key)
        ownership,instances,_=new_labels.partition(prefix,cells,profile('asap7'),expected={n:s[n+'_bits'] for n in ('input_service','native_state','external_state')})
        paths=new_labels.labels(prefix,s,40500,1,cells,instances)
        write(out/(key+'.json'),{'ownership':ownership,'paths':paths,'source_manifest_sha256':sha(directory/'manifest.json')})
        rows.append({'id':key,'paths':len(paths),'root_constants':ownership['explicit_root_constant_drivers'],'owner_FF_bits':ownership['owner_FF_bits']})
    try:new_labels.canonical_instances({'data\\[0\\]':'cell','data[0]':'cell'})
    except ValueError:pass
    else:raise ValueError('escaped name collision accepted')
    proof={'status':'passed','version':VERSION,'parent_admission':str(parent/'admission.json'),'parent_admission_sha256':sha(parent/'admission.json'),
        'pilots':rows,'escaped_collision_rejected':True,'unknown_root_logic_still_rejected':True,
        'sampling_parameters_or_RTL_changed':False,'synth_or_grt_reexecuted':False,'PPA_calls':0,
        'sources':{str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),Path(new_labels.__file__)]}}
    write(out/'proof.json',proof);print(json.dumps(proof),flush=True)


def prepare(folder,parent,proof):
    a=base.verify(parent);p=base.read(proof)
    if p['status']!='passed' or p['parent_admission_sha256']!=sha(parent/'admission.json') or p['sampling_parameters_or_RTL_changed']:
        raise ValueError('reference reader successor proof required')
    for name,h in p['sources'].items():
        if sha(ROOT/name)!=h:raise ValueError('reference successor producer changed')
    base.prepare(folder,Path(a['software_proof_path']),Path(a['reader_proof_path']))
    current=base.read(folder/'admission.json');resume={}
    for key in a['capacity_pilots']:
        directory=parent/'runs'/key;paid_checkpoint(directory);resume[key]={'directory':str(directory),'manifest_sha256':sha(directory/'manifest.json')}
    for name,h in p['sources'].items():
        dst=folder/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dst);current['sources'][name]=h
    current.update(execution_successor=VERSION,parent_admission=str(parent/'admission.json'),parent_admission_sha256=sha(parent/'admission.json'),
        reader_successor_proof=str(proof),reader_successor_proof_sha256=sha(proof),synth_resume=resume,
        source_RTL_ABC_SDC_or_sample_roles_changed=False,planned_new_synth_calls=14,planned_new_grt_calls=17)
    write(folder/'admission.json',current);verify(folder)
    print(json.dumps({'status':'reference_execution_successor_admitted','exact_synth_checkpoints':list(resume),'new_synth_calls':14,'new_grt_calls':17}),flush=True)


def verify(folder):
    a=base.verify(folder)
    if a.get('execution_successor')!=VERSION or a['source_RTL_ABC_SDC_or_sample_roles_changed'] or sha(a['parent_admission'])!=a['parent_admission_sha256'] or sha(a['reader_successor_proof'])!=a['reader_successor_proof_sha256']:
        raise ValueError('reference execution successor changed')
    for ref in a['synth_resume'].values():
        if sha(Path(ref['directory'])/'manifest.json')!=ref['manifest_sha256']:raise ValueError('reference synthesis ancestor changed')
    return a


class ReferenceLedger(base.ReferenceLedger):
    def reserve(self,*args,**kwargs):verify(self.folder);return super().reserve(*args,**kwargs)


def install():
    from . import backend
    original_evaluate=backend._evaluate
    def evaluate(args,ledger):
        a=verify(ledger.folder)
        if args.task_id not in a['synth_resume']:return original_evaluate(args,ledger)
        ref=a['synth_resume'][args.task_id];old_dir=Path(ref['directory']);old=paid_checkpoint(old_dir);out=args.out
        out.mkdir(parents=True,exist_ok=False)
        for path in old_dir.iterdir():
            if path.is_file() and path.name!='manifest.json' and not path.name.endswith(('.log','.command.json','.gnu-time.txt')):
                shutil.copy2(path,out/path.name)
        for name in ('source','flow-scripts'):shutil.copytree(old_dir/name,out/name,symlinks=True)
        results=out/'results'/base.SUFFIX;results.mkdir(parents=True)
        for path in (old_dir/'results'/base.SUFFIX).glob('1*'):
            if path.is_file():shutil.copy2(path,results/path.name)
        config=out/'config.mk';config.write_text(config.read_text().replace(str(old_dir),str(out)))
        m=copy.deepcopy(old);m.update(status='completed',commands=[],metrics=[],admission_id=a['id'],task_id=args.task_id,
            budget_job_id=ledger.job_id,execution_successor=VERSION)
        for name in ('failure_stage','failure_reason','failure_code','finished_at','evidence_sha256'):m.pop(name,None)
        m['checkpoint_reuse']={'mode':'exact_paid_synth_ODB_netlist_and_SDC','source_run':str(old_dir),'source_manifest_sha256':ref['manifest_sha256'],
            'old_ODB_or_SDC_copied':True,'Yosys_ABC_reexecuted':False,
            'files_sha256':{name:sha(results/name) for name in ('1_synth.odb','1_synth.sdc','1_2_yosys.v')}}
        from .model_m2_mux_collection import physical_base
        command=[x.replace(str(old_dir),str(out)) for x in physical_base(old) if not x.startswith('--assume-old=')]
        for path in [config,out/'input.sv',*results.glob('1*')]:command.append('--assume-old='+str(path))
        # This is a planned continuation command, not an executed leaf. The
        # adapter below reads it explicitly; commands contains only real leaves
        # executed in this successor. Ancestor commands remain byte-identical.
        m['continuation_base_command']=command
        m['files_sha256'].update({str(config):sha(config),str(out/'input.sv'):sha(out/'input.sv')})
        write(out/'manifest.json',m);return 0
    backend._evaluate=evaluate
    old_labels.partition=new_labels.partition;old_labels.labels=new_labels.labels


def run_task(folder,t):
    namespace=dict(base.run_task.__globals__);namespace.update(verify=verify,ReferenceLedger=ReferenceLedger)
    source=inspect.getsource(base.run_task)
    marker="base=next(c['command'][:-1] for c in m['commands'] if c['log'].endswith('/synth.log'))"
    if source.count(marker)!=1:raise ValueError('unsupported frozen reference worker continuation point')
    source=source.replace(marker,"base=m['continuation_base_command'] if 'continuation_base_command' in m else "+marker[5:])
    exec(compile(source,str(Path(__file__).resolve())+'::reference_worker','exec'),namespace)
    return namespace['run_task'](folder,t)


def run(folder):
    verify(folder);install();namespace=dict(base.run.__globals__);namespace.update(verify=verify,run_task=run_task)
    types.FunctionType(base.run.__code__,namespace)(folder)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('preflight','prepare','verify','run','status'));p.add_argument('--folder',type=Path,required=True)
    p.add_argument('--parent',type=Path);p.add_argument('--proof',type=Path);a=p.parse_args();folder=a.folder.resolve()
    if a.action=='preflight':preflight(a.parent.resolve(),folder)
    elif a.action=='prepare':prepare(folder,a.parent.resolve(),a.proof.resolve())
    elif a.action=='verify':verify(folder);print('reference execution successor verified')
    elif a.action=='run':run(folder)
    else:base.status(folder)
