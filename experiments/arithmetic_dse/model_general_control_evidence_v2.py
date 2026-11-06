"""Allow installed numerical Python runtime during otherwise isolated S replay.

The executed numerical producer and raw archive stay immutable. This successor
only declares the runtime directory required by the already recorded NumPy and
SciPy versions; original project/build/ledger reads remain forbidden.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from . import model_general_control_evidence as base
from .model_d_requirements_evidence import pack, unpack, sha, read, write

ADAPTER = 'qualified-S-installed-numerical-runtime-isolation-v2'


def runtime_contract():
    return {'version': ADAPTER, 'immutable_executed_numerical_producers': True,
        'numerical_runtime': 'installed NumPy/SciPy Python package directory and metadata; exact versions from archived selection-freeze',
        'original_source_build_and_ledger_reads': 'forbidden', 'other_original_home_reads': 'forbidden',
        'PATH': 'empty', 'replay_subprocesses': 'forbidden', 'parameters_domain_reserve_changed': False}


def publish(archive, root, folder):
    draft = root / 'publication-small-draft-v1'
    base.publish(archive, root, draft)
    folder.mkdir(parents=True, exist_ok=False)
    for p in draft.iterdir():
        if p.name not in ('manifest.json', 'source-pool.json.gz', 'README.md'):
            shutil.copy2(p, folder / p.name)
    with tempfile.TemporaryDirectory() as td:
        source = Path(td); unpack(draft / 'source-pool.json.gz', source)
        own = source / 'experiments/arithmetic_dse/model_general_control_evidence_v2.py'
        own.write_bytes(Path(__file__).read_bytes())
        pack(folder / 'source-pool.json.gz', {str(p.relative_to(source)): p for p in source.rglob('*') if p.is_file()})
    text = (draft / 'README.md').read_text().replace('experiments.arithmetic_dse.model_general_control_evidence',
        'experiments.arithmetic_dse.model_general_control_evidence_v2')
    text += '\n隔离运行库说明：NumPy／SciPy安装在用户Python包目录；v2显式允许该运行库目录及元数据，并核对冻结版本，仍禁止原项目／build／账本及其他原home读取、PATH为空且禁回放子进程。该适配不改数值生产者、模型、范围或原始归档。\n'
    (folder / 'README.md').write_text(text)
    write(folder / 'runtime-contract.json', runtime_contract())
    write(folder / 'manifest.json', {'version': base.VERSION, 'verification_adapter': ADAPTER,
        'parent_draft_manifest_sha256': sha(draft / 'manifest.json'),
        'files': {p.name: sha(p) for p in folder.iterdir() if p.is_file()}})
    print(json.dumps({'status': 'published', 'verification_adapter': ADAPTER,
        'model_sha256': sha(folder / 'asap7-general-state.json'),
        'bytes': sum(p.stat().st_size for p in folder.iterdir() if p.is_file()),
        'production_price_binding_qualified': False, 'full_D_ready': False}), flush=True)


def verify(folder, external=False, retrain=False):
    if read(folder / 'runtime-contract.json') != runtime_contract():
        raise ValueError('qualified S runtime declaration differs')
    base.verify(folder, external=external, retrain=retrain)


def isolated(folder):
    with tempfile.TemporaryDirectory(prefix='qualified-S-runtime-isolated-') as td:
        temp = Path(td); local = temp / 'evidence'; shutil.copytree(folder, local); source = temp / 'source'
        unpack(local / 'source-pool.json.gz', source)
        code = '''import builtins,io,os,runpy,subprocess,sys,importlib.util
from pathlib import Path
source,folder,action=sys.argv[1:]
runtime=[]
for name in ('numpy','scipy'):
 spec=importlib.util.find_spec(name)
 if spec is None or spec.origin is None:raise RuntimeError('declared numerical runtime missing')
 runtime.append(Path(spec.origin).resolve().parent.parent)
def guard(original):
 def checked(path,*a,**kw):
  if isinstance(path,(str,bytes,os.PathLike)):
   p=Path(path).resolve()
   if str(p).startswith('/home/zyrv/') and not any(p.is_relative_to(root) for root in runtime):
    raise RuntimeError('original tree read forbidden')
  return original(path,*a,**kw)
 return checked
builtins.open=guard(builtins.open);io.open=guard(io.open)
def forbidden(*a,**kw):raise RuntimeError('S replay subprocess forbidden')
subprocess.Popen=forbidden
sys.path.insert(0,source);sys.argv=['sealed',action,'--folder',folder]
runpy.run_module('experiments.arithmetic_dse.model_general_control_evidence_v2',run_name='__main__')
'''
        env = os.environ.copy(); env.update(PATH='', PYTHONDONTWRITEBYTECODE='1'); env.pop('PYTHONPATH', None)
        command = [sys.executable, '-B', '-c', code, str(source), str(local)]
        for action in ('verify', 'retrain'):
            p = subprocess.run(command + [action], cwd=temp, env=env, capture_output=True, text=True)
            if p.returncode: raise ValueError('qualified S runtime-isolated ' + action + ' failed: ' + p.stderr[-2500:])
        for name in ('documents-pool.json.gz', 'asap7-general-state.json', 'capabilities.json'):
            path = local / name; original = path.read_bytes(); changed = bytearray(original); changed[len(changed) // 2] ^= 1; path.write_bytes(changed)
            p = subprocess.run(command + ['verify'], cwd=temp, env=env, capture_output=True, text=True)
            path.write_bytes(original)
            if p.returncode == 0 or 'qualified S evidence identity mismatch' not in p.stderr:
                raise ValueError('qualified S runtime-isolated tamper accepted: ' + name)
    print(json.dumps({'status': 'passed', 'verification_adapter': ADAPTER,
        'original_source_build_ledger_denied': True, 'installed_numerical_runtime_allowed': True,
        'PATH_empty': True, 'replay_subprocess_denied': True, 'isolated_train_only_reproduction': True,
        'document_model_capability_tamper_rejected': True, 'PPA_calls': 0}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('action', choices=('publish', 'verify', 'retrain', 'isolated'))
    parser.add_argument('--folder', type=Path, required=True); parser.add_argument('--archive', type=Path)
    parser.add_argument('--root', type=Path); parser.add_argument('--external', action='store_true')
    args = parser.parse_args(); folder = args.folder.resolve()
    if args.action == 'publish': publish(args.archive.resolve(), args.root.resolve(), folder)
    elif args.action == 'isolated': isolated(folder)
    else: verify(folder, external=args.external, retrain=args.action == 'retrain')
