"""Explicit continuation of successful synthesis after alias proof repair.

Exactly one not-yet-run global route, no synthesis retry. The failed admission
and commands are immutable; continuation writes its own receipt and admission.
"""
import argparse
from copy import deepcopy
import inspect
from pathlib import Path
import shutil
from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import stage67_physical_probe_v1 as physical
from .stage67_pure_alias_v2 import semantics

ROOT=physical.ROOT


def admit(root,parent,qualification):
    if root.exists():raise ValueError('preserve physical continuation admission')
    q=read(qualification/'qualification.json')
    if q['status']!='passed_exact_alias_state_qualification_not_joint':raise ValueError('exact alias proof required before continuation')
    for n,h in q['inputs'].items():
        if sha(n)!=h:raise ValueError('alias proof input drift')
    a=read(parent/'admission.json');p=read(parent/'progress.json');task=deepcopy(next(t for t in a['tasks'] if t['placement']=='placement-0'));d=parent/'runs'/task['id']
    if any(e.get('task')==task['id'] and e.get('reason','').startswith('variable state bit was optimized away') for e in p['errors']) is False:raise ValueError('unexpected original stop')
    if (d/'results'/physical.SUFFIX/'5_1_grt.odb').exists():raise ValueError('route already attempted')
    if not (d/'results'/physical.SUFFIX/'1_synth.odb').exists():raise ValueError('successful synth required')
    task.update(physical_directory=str(d),qualified_state=str(qualification/'mapped-state.json'))
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];wall=1200+16*120
    if used['grt']+1+688>limits['max_global_route_calls'] or used['walltime_s']+wall+86400>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+4*wall+172800>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(parent).free<32*1024**3:raise ValueError('continuation and later work unfunded')
    root.mkdir(parents=True);names=set(a['sources'])|{str(Path(__file__).relative_to(ROOT))}
    names.update(str(f.relative_to(ROOT)) for pattern in ('stage67_pure_alias_v*.py','stage67_alias_qualify_v*.py','stage67_state_semantics_v*.py') for f in (ROOT/'experiments/arithmetic_dse').glob(pattern))
    hashes={}
    for n in sorted(names):
        dst=root/'source'/n;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dst);hashes[n]=sha(dst)
    inputs={str(f):sha(f) for f in (qualification/'qualification.json',qualification/'mapped-state.json',qualification/'state-semantics.json',d/'manifest.json',d/'mapped.json',d/'liberty-pins.json')}
    inputs.update({str(f):sha(f) for f in (d/'results').rglob('*') if f.is_file()})
    write(root/'admission.json',dict(version='pure-alias-synth-continuation-v1',id=root.name,tasks=[task],sources=hashes,model=a['model'],S_binding=a['S_binding'],
        parent_admission_sha256=sha(parent/'admission.json'),parent_progress_sha256=sha(parent/'progress.json'),qualification_inputs=inputs,
        synth_max=0,grt_max=1,support_max=16,synth_timeout_s=300,grt_timeout_s=1200,threads=4,memory_limit_MiB=8192,parallel_jobs=1,automatic_retries=0,
        continuation='inherit successful synthesis, repair semantic reader only, run first grt; original error remains',later_work_reserved=a['later_work_reserved'],full_D_ready=False))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=None))
    print('ALIAS_CONTINUATION_ADMITTED new_synth=0 first_grt=1',flush=True)


def run(root):
    a=read(root/'admission.json');task=a['tasks'][0];p=read(root/'progress.json')
    if p['phase']!='admitted':raise ValueError('no automatic continuation retry')
    for n,h in a['qualification_inputs'].items():
        if sha(n)!=h:raise ValueError('inherited successful synth/proof drift '+n)
    text=inspect.getsource(physical.point)
    start=text.index('        args=SimpleNamespace(');end=text.index("        manifest=read(out/'manifest.json')",start)
    text=text[:start]+text[end:]
    start=text.index("        cells=read(out/'liberty_cells.json')");end=text.index("        wrapper=out/'live-cec.py'",start)
    text=text[:start]+"        cells=read(out/'liberty_cells.json')['cells']\n        contract=read(task['qualified_state']);write(out/'mapped-state.json',contract)\n"+text[end:]
    text=text.replace("out=root/'runs'/task['id']","out=Path(task['physical_directory'])").replace("out/'pilot-commands.json'","out/'continuation-commands.json'").replace('model_m2_live_cec_v3','model_m2_live_cec_v4')
    ns=dict(physical.point.__globals__);exec(compile(text,__file__,'exec'),ns)
    p.update(phase='running',active=task['id']);write(root/'progress.json',p)
    try:
        ns['point'](root,task)
        d=Path(task['physical_directory']);proof=semantics(d,read(d/'mapped-state.json'),Path(task['rtl']).read_text(),read(task['endpoint_contract']))
        write(root/'state-semantics-after-CEC.json',proof)
        p.update(phase='physical_continuation_complete',active=None,completed=[task['id']])
    except Exception as e:
        p.update(phase='stopped_on_error',active=None,errors=[dict(task=task['id'],reason=str(e))]);write(root/'progress.json',p);raise
    write(root/'progress.json',p);print('ALIAS_CONTINUATION_COMPLETE inherited_synth=1 new_grt=1 exact_Boolean_and_CEC=passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--parent',type=Path);p.add_argument('--qualification',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve(),a.parent.resolve(),a.qualification.resolve())
    else:run(a.root.resolve())
