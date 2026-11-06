"""Retained general-state successor with explicit binary32-IO SDC validation."""
import argparse
import inspect
from pathlib import Path
import shutil
import types

from . import model_general_state_collection as parent
from . import model_general_state_samples_v2 as samples
from . import sdc_storage_v3
from .model_collection import sha,write

CONFIG=Path(__file__).with_name('configs')/'model_asap7_general_state_v2.json'
VERSION='general-state-retained-source-and-IO-storage-execution-v2'


def function(original,**overrides):
    namespace=dict(original.__globals__);namespace.update(overrides)
    return types.FunctionType(original.__code__,namespace,closure=original.__closure__)


def prepare(folder,proof,parent_folder,storage_proof):
    old=parent.verify(parent_folder);p=parent.read(parent_folder/'progress.json');q=parent.read(proof)
    if p['phase']!='stopped_on_error' or p['active'] or len(p['errors'])!=4:
        raise ValueError('settled four-source diagnostic predecessor required')
    for row in p['errors']:
        m=parent.read(parent_folder/'runs'/row['task_id']/'manifest.json')
        if not any(c['log'].endswith('/synth.log') and c['exit_code']==0 for c in m['commands']):
            raise ValueError('predecessor synth diagnostic missing')
        if any(c['log'].endswith('/grt.log') for c in m['commands']):raise ValueError('unexpected predecessor grt')
    if not q.get('all_semantic_state_outputs_explicitly_observed'):raise ValueError('retained-source preflight missing')
    storage=parent.read(storage_proof)
    if storage['status']!='passed' or storage['producer_sha256']!=sha(Path(sdc_storage_v3.__file__)):
        raise ValueError('explicit IO storage validation proof missing')
    function(parent.prepare,CONFIG=CONFIG,specifications=samples.specifications,source=samples.source,
        features=samples.features,VERSION=samples.VERSION)(folder,proof)
    a=parent.read(folder/'admission.json')
    for name in ('model_general_state_collection_v2.py','model_general_state_samples_v2.py','sdc_storage_v3.py'):
        path=Path(__file__).with_name(name);label=str(path.relative_to(parent.ROOT));dest=folder/'source'/label
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dest);a['sources'][label]=sha(path)
    for name in ('regression/arithmetic_general_state_v2.py','regression/arithmetic_sdc_storage.py'):
        dest=folder/'source'/name;dest.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(parent.ROOT/name,dest);a['sources'][name]=sha(parent.ROOT/name)
    a.update(execution_successor=VERSION,predecessor_admission=str(parent_folder/'admission.json'),
        predecessor_admission_sha256=sha(parent_folder/'admission.json'),
        predecessor_progress_sha256=sha(parent_folder/'progress.json'),
        predecessor_runs={row['task_id']:sha(parent_folder/'runs'/row['task_id']/'manifest.json') for row in p['errors']},
        storage_proof=str(storage_proof),storage_proof_sha256=sha(storage_proof),
        predecessor_numeric_labels_inherited=False,predecessor_failed_probes_retained=True,
        SDC_runtime_validator=sdc_storage_v3.VERSION)
    write(folder/'admission.json',a);verify(folder)
    print('retained general-state v2 admitted; old four synth diagnostics retained, independent test locked',flush=True)


def verify(folder):
    a=function(parent.verify,CONFIG=CONFIG,specifications=samples.specifications,features=samples.features)(folder)
    if (a.get('execution_successor')!=VERSION
        or sha(a['predecessor_admission'])!=a['predecessor_admission_sha256']
        or sha(Path(a['predecessor_admission']).parent/'progress.json')!=a['predecessor_progress_sha256']
        or sha(a['storage_proof'])!=a['storage_proof_sha256']):
        raise ValueError('retained general-state execution predecessor changed')
    for key,h in a['predecessor_runs'].items():
        if sha(Path(a['predecessor_admission']).parent/'runs'/key/'manifest.json')!=h:
            raise ValueError('retained general-state failed probe changed')
    return a


class GeneralLedger(parent.GeneralLedger):
    pass
_reserve=function(parent.GeneralLedger.reserve,verify=verify)
_old_model='asap7-general-state-successor-v1'
if _reserve.__code__.co_consts.count(_old_model)!=1:raise ValueError('unsupported general-state ledger identity point')
_reserve.__code__=_reserve.__code__.replace(co_consts=tuple(
    'asap7-general-state-successor-v2-retained' if value==_old_model else value for value in _reserve.__code__.co_consts))
GeneralLedger.reserve=_reserve


def run_task(folder,t):
    source=inspect.getsource(parent.run_task)
    marker='from .sdc import verify_sdc,rtl_ports'
    if source.count(marker)!=1:raise ValueError('unsupported general-state SDC consumption point')
    source=source.replace(marker,'from .sdc_storage_v3 import verify_sdc\n    from .sdc import rtl_ports')
    namespace=dict(parent.run_task.__globals__);namespace.update(CONFIG=CONFIG,verify=verify,GeneralLedger=GeneralLedger)
    exec(compile(source,str(Path(__file__).resolve())+'::retained_worker','exec'),namespace)
    return namespace['run_task'](folder,t)


def run(folder):
    from . import backend
    verify(folder);backend.verify_sdc=sdc_storage_v3.verify_sdc;backend.SDC_CONTRACT_VERSION=sdc_storage_v3.VERSION
    function(parent.run,verify=verify,run_task=run_task)(folder)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('prepare','verify','run','status'))
    parser.add_argument('--folder',type=Path,required=True);parser.add_argument('--proof',type=Path)
    parser.add_argument('--parent',type=Path);parser.add_argument('--storage-proof',type=Path);args=parser.parse_args();folder=args.folder.resolve()
    if args.action=='prepare':prepare(folder,args.proof.resolve(),args.parent.resolve(),args.storage_proof.resolve())
    elif args.action=='verify':verify(folder);print('retained general-state admission verified')
    elif args.action=='run':run(folder)
    else:parent.status(folder)
