"""Versioned fitting-only S control-boundary collection; frozen area prices retained."""
import argparse
import inspect
from pathlib import Path
import shutil
import types

from . import model_general_state_collection as parent
from . import model_general_control_samples as samples
from . import sdc_storage_v3
from .model_collection import sha, write

CONFIG = Path(__file__).with_name('configs') / 'model_asap7_general_control_v1.json'
VERSION = 'asap7-general-state-control-boundary-successor-v1'


def function(original, **overrides):
    namespace = dict(original.__globals__); namespace.update(overrides)
    result = types.FunctionType(original.__code__, namespace, original.__name__, original.__defaults__, original.__closure__)
    result.__kwdefaults__ = original.__kwdefaults__
    return result


def dependencies():
    cfg = parent.read(CONFIG)
    for key in ('parent_general_candidate', 'parent_general_selection', 'parent_fitting_dataset',
                'parent_independent_verdict', 'parent_test_consumed'):
        if sha(parent.ROOT / cfg[key]) != cfg[key + '_sha256']:
            raise ValueError('control-boundary frozen predecessor changed: ' + key)
    candidate = parent.read(parent.ROOT / cfg['parent_general_candidate'])
    result = parent.read(parent.ROOT / cfg['parent_independent_verdict'])
    if (result['status'] != 'failed' or not result['test_labels_permanently_excluded_from_future_fitting']
            or not all(q['status'] == 'passed' for stage in result['stages'].values() for q in stage['owner_area_quality'].values())
            or candidate['full_D_ready']):
        raise ValueError('retain original S failure and passing unchanged area evidence')
    return cfg


def prepare(folder, proof):
    cfg = dependencies()
    function(parent.prepare, CONFIG=CONFIG, specifications=samples.specifications,
        source=samples.source, features=samples.features, VERSION=samples.VERSION)(folder, proof)
    admission = parent.read(folder / 'admission.json')
    extra = [Path(__file__), Path(samples.__file__), Path(sdc_storage_v3.__file__),
        parent.ROOT / 'regression/arithmetic_general_control.py',
        parent.ROOT / 'experiments/arithmetic_dse/model_general_state_samples_v2.py',
        parent.ROOT / 'experiments/arithmetic_dse/model_general_state_fit.py',
        parent.ROOT / 'experiments/arithmetic_dse/model_m2_state_fit.py',
        parent.ROOT / 'experiments/arithmetic_dse/model_training.py']
    for path in extra:
        name = str(path.relative_to(parent.ROOT)); dest = folder / 'source' / name
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dest); admission['sources'][name] = sha(path)
    for key in ('parent_general_candidate', 'parent_general_selection', 'parent_fitting_dataset',
                'parent_independent_verdict', 'parent_test_consumed'):
        path = parent.ROOT / cfg[key]; dest = folder / 'baseline' / (key + '.json')
        dest.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(path, dest)
    admission.update(control_boundary_successor=VERSION, mutable_paths=cfg['boundary_mutable_paths'],
        area_candidate_sha256=cfg['parent_general_candidate_sha256'], area_refit_permitted=False,
        consumed_predecessor_test_labels_forbidden=True, full_D_ready=False)
    write(folder / 'admission.json', admission); verify(folder)
    print('control-boundary fitting admitted; area parameters fixed; new54 independent tests locked', flush=True)


def verify(folder):
    cfg = dependencies()
    a = function(parent.verify, CONFIG=CONFIG, specifications=samples.specifications, features=samples.features)(folder)
    if (a.get('control_boundary_successor') != VERSION or a['area_refit_permitted']
            or a['area_candidate_sha256'] != cfg['parent_general_candidate_sha256']
            or a['mutable_paths'] != ['native_enable', 'native_valid']):
        raise ValueError('control-boundary area/role policy changed')
    for key in ('parent_general_candidate', 'parent_general_selection', 'parent_fitting_dataset',
                'parent_independent_verdict', 'parent_test_consumed'):
        if sha(folder / 'baseline' / (key + '.json')) != cfg[key + '_sha256']:
            raise ValueError('archived control-boundary baseline changed')
    return a


class GeneralLedger(parent.GeneralLedger):
    pass


_reserve = function(parent.GeneralLedger.reserve, verify=verify)
_old = 'asap7-general-state-successor-v1'
if _reserve.__code__.co_consts.count(_old) != 1:
    raise ValueError('unsupported control-boundary ledger identity')
_reserve.__code__ = _reserve.__code__.replace(co_consts=tuple(VERSION if c == _old else c for c in _reserve.__code__.co_consts))
GeneralLedger.reserve = _reserve


def run_task(folder, task):
    text = inspect.getsource(parent.run_task)
    marker = 'from .sdc import verify_sdc,rtl_ports'
    if text.count(marker) != 1:
        raise ValueError('unsupported control-boundary SDC adapter')
    text = text.replace(marker, 'from .sdc_storage_v3 import verify_sdc\n    from .sdc import rtl_ports')
    namespace = dict(parent.run_task.__globals__)
    namespace.update(CONFIG=CONFIG, verify=verify, GeneralLedger=GeneralLedger)
    exec(compile(text, str(Path(__file__).resolve()) + '::control_worker', 'exec'), namespace)
    return namespace['run_task'](folder, task)


def run(folder):
    from . import backend
    verify(folder); backend.verify_sdc = sdc_storage_v3.verify_sdc; backend.SDC_CONTRACT_VERSION = sdc_storage_v3.VERSION
    function(parent.run, verify=verify, run_task=run_task)(folder)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('prepare', 'verify', 'run', 'status'))
    parser.add_argument('--folder', type=Path, required=True); parser.add_argument('--proof', type=Path)
    args = parser.parse_args(); folder = args.folder.resolve()
    if args.action == 'prepare': prepare(folder, args.proof.resolve())
    elif args.action == 'verify': verify(folder); print('frozen control-boundary fitting admission verified')
    elif args.action == 'run': run(folder)
    else: parent.status(folder)
