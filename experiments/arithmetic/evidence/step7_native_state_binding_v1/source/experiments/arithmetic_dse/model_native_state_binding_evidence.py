"""Portable successor evidence for C++ component/state binding, without new model fitting."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
VERSION='asap7-native-state-production-binding-evidence-v1'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n')


def replay(folder):
    script=folder/'source/regression/arithmetic_composite_state.py'
    spec=importlib.util.spec_from_file_location('frozen_native_state_binding',script)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.verify(folder,folder/'source/experiments/arithmetic_dse/configs/model_asap7_d_components_v1.json')


def seal(checks,baseline,folder):
    folder.mkdir(parents=True,exist_ok=False)
    originals={}
    def copy(src,dest):
        dest=folder/dest;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest)
        originals[str(src.resolve())]={'copy':str(dest.relative_to(folder)),'sha256':sha(src)}
    # Complete active C++ source snapshot, including transitive project headers;
    # the replay checks receipts/numerics, and rebuilding uses the real toolchain.
    sources=[p for p in (ROOT/'rtlzz/src').rglob('*') if p.is_file()]
    sources += [ROOT/'rtlzz/testv2/arithmetic_composite_state_test.cpp',ROOT/'rtlzz/CMakeLists.txt',
        ROOT/'regression/arithmetic_composite_state.py',Path(__file__).resolve(),
        ROOT/'experiments/arithmetic_dse/configs/model_asap7_d_components_v1.json',
        ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json',
        ROOT/'experiments/arithmetic/evidence/step7_m2_mux_static_v1/asap7-primitives.json',
        ROOT/'experiments/arithmetic/evidence/step7_native_state_v1/asap7-native-state.json']
    for src in sources:copy(src,Path('source')/src.relative_to(ROOT))
    for name in ('queries.json','D-diagnostic.json','public-bank-coverage.json'):copy(checks/'native'/name,Path('native')/name)
    for name in ('parity.json','commands.json','resource-summary.json'):copy(checks/name,name)
    for tag,origin in (('latest',checks),('baseline',baseline)):
        for src in origin.glob('*'):
            if src.is_file() and (src.name.endswith(('.log','.json')) or 'resource' in src.name):
                copy(src,Path('receipts')/tag/src.name)
    for src in (baseline/'primitives').rglob('*'):
        if src.is_file() and src.suffix=='.json':copy(src,Path('baseline-primitives')/src.relative_to(baseline/'primitives'))
    write(folder/'capabilities.json',dict(version=VERSION,state_component_binding_qualified=True,
        qualified_scope='independent native-protocol scalar banks with checked masks/lifetimes and registered reset-pattern subset; core plus explicit external capture',
        reset_subset='zero, one, alternating or one-in-three on packed variable bits; arbitrary semantic resets remain refused',
        public_original_banks_covered=0,all_candidates_and_moves_checked=False,
        initial_move_final_full_pipeline_qualified=False,joint_arithmetic_boundary_qualified=False,
        wrapper_state_included=False,whole_stage_model_qualified=False,real_interval_model_qualified=False,
        full_D_ready=False,formal_36_complete=False,PPA_calls=0,
        limitations=['state-bank budgets are conditional residuals, not formal arithmetic boundary qualification',
            'whole-D scheduling still refuses absent joint/service boundary and whole-stage/interval qualification',
            'nine public original cores plus three diagnostic layouts checked; all currently refuse state bank price',
            'published component bytes/coefficients/domains/test verdicts unchanged; consumer conservatively narrows reset support']))
    binary=ROOT/'build/step4-rtlzz/testv2/arithmetic-composite-state-test'
    write(folder/'provenance.json',dict(version=VERSION,checks=str(checks),baseline=str(baseline),
        binary_path=str(binary),binary_sha256=sha(binary),originals=originals,
        no_new_fitting=True,no_independent_test_selection=True,model_bytes_changed=False))
    hashes={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*') if p.is_file()}
    write(folder/'manifest.json',dict(version=VERSION,files=hashes))
    print(json.dumps(dict(status='sealed',files=len(hashes),bytes=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file()))),flush=True)


def verify(folder,external=False):
    manifest=read(folder/'manifest.json')
    if manifest['version']!=VERSION:raise ValueError('binding evidence schema mismatch')
    for name,h in manifest['files'].items():
        p=folder/name
        if not p.is_file() or sha(p)!=h:raise ValueError('binding evidence content identity mismatch: '+name)
    capability=read(folder/'capabilities.json')
    if (not capability['state_component_binding_qualified'] or capability['full_D_ready']
        or capability['joint_arithmetic_boundary_qualified'] or capability['formal_36_complete'] or capability['PPA_calls']):
        raise ValueError('binding evidence scope changed')
    parity=replay(folder)
    if parity!=read(folder/'receipts/latest/parity.json'):
        raise ValueError('portable binding replay differs from paid receipt')
    baseline=read(folder/'baseline-primitives/parity.json')
    if baseline['status']!='passed' or baseline['native_queries']!=436 or baseline['maximum_native_Python_delta']!=0:
        raise ValueError('primitive regression receipt missing')
    for name,token in [('ordinary','Arithmetic model native checks: 250'),('pipeline-test','pipeline tests passed'),
                       ('pipeline-reset-test','pipeline reset API tests passed'),('pipeline-valid-test','pipeline valid API and IR tests passed')]:
        if token not in (folder/f'receipts/baseline/{name}.log').read_text():raise ValueError('baseline regression failed: '+name)
    provenance=read(folder/'provenance.json')
    if external:
        for name,item in provenance['originals'].items():
            if not Path(name).is_file() or sha(name)!=item['sha256']:raise ValueError('external original differs: '+name)
        if sha(provenance['binary_path'])!=provenance['binary_sha256']:raise ValueError('external compiler binary differs')
    result=dict(status='passed',external=external,files=len(manifest['files']),replay=parity,
        coefficients_or_domains_changed=False,full_D_ready=False,PPA_calls=0)
    print(json.dumps(result),flush=True)
    return result


def isolated_check(folder):
    # Copy only Git-eligible small evidence, then run the frozen stdlib replay
    # with no original tree/tools and PATH empty. No new C++/EDA is launched.
    with tempfile.TemporaryDirectory(prefix='native-state-binding-replay-') as tmp:
        local=Path(tmp)/'evidence';shutil.copytree(folder,local)
        script=local/'source/experiments/arithmetic_dse/model_native_state_binding_evidence.py'
        code="""import builtins,runpy,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve();script=sys.argv[2]
original_open=builtins.open;original_io=__import__('io').open
def guard(original):
 def checked(file,*args,**kwargs):
  if isinstance(file,(str,bytes,__import__('os').PathLike)):
   p=Path(file).resolve()
   if str(p).startswith('/home/zyrv/vulsim'):
    raise RuntimeError('original tree read forbidden: '+str(p))
  return original(file,*args,**kwargs)
 return checked
builtins.open=guard(original_open);__import__('io').open=guard(original_io)
def forbidden(*args,**kwargs):raise RuntimeError('subprocess forbidden during portable replay')
__import__('subprocess').Popen=forbidden
sys.argv=[script,'verify','--folder',str(root)];runpy.run_path(script,run_name='__main__')
"""
        import os
        env=os.environ.copy();env.update(PATH='',PYTHONDONTWRITEBYTECODE='1');env.pop('PYTHONPATH',None)
        result=subprocess.run([sys.executable,'-B','-c',code,str(local),str(script)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode:raise ValueError('isolated portable replay failed: '+result.stderr[-2000:])
        # Tampering must fail before numerical replay.
        changed=local/'native/queries.json';changed.write_bytes(changed.read_bytes()+b' ')
        result=subprocess.run([sys.executable,'-B',str(script),'verify','--folder',str(local)],cwd=tmp,env=env,capture_output=True,text=True)
        if result.returncode==0 or 'content identity mismatch' not in result.stderr:raise ValueError('binding evidence tampering accepted')
    print(json.dumps(dict(status='passed',isolated_original_tree_denied=True,PATH_empty=True,
        replay_subprocess_forbidden=True,tampering_rejected=True,PPA_calls=0)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('seal','verify','isolated'))
    p.add_argument('--folder',type=Path,required=True);p.add_argument('--checks',type=Path);p.add_argument('--baseline',type=Path);p.add_argument('--external',action='store_true')
    a=p.parse_args()
    if a.action=='seal':seal(a.checks.resolve(),a.baseline.resolve(),a.folder.resolve())
    elif a.action=='isolated':isolated_check(a.folder.resolve())
    else:verify(a.folder.resolve(),a.external)
