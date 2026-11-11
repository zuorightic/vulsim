"""Shared-load measurability probes; no invented prices or node fitting.

The same real source retains validation role. Its two placements are measured
only to check real FF aliases/loading before choosing a successor model domain.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import inspect
from pathlib import Path
import re
import shutil
from types import SimpleNamespace

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import stage7_physical_prepare as prep
from . import stage67_shared_collect_v1 as shared
from . import stage67_physical_probe_v1 as physical

ROOT=Path(__file__).resolve().parents[2]
PRIOR=Path('/home/zyrv/vulsim-artifacts/stage67-multiclock-20261111-v1/remaining-software')
NODE=ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'
BINDING=Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/binding-candidate.json')


def prepare(root):
    if root.exists():raise ValueError('preserve shared probe preparation')
    d=root/'sources/stage_shared_16';d.mkdir(parents=True)
    source=read(PRIOR/'sources/stage_shared_16/request.json');shutil.copytree(PRIOR/'sources/stage_shared_16/structural-native',d/'native')
    write(d/'request.json',source);write(root/'sources.json',dict(sources=[source]))
    deps=dict(model=dict(path=str(NODE),sha256=sha(NODE)),S_binding=dict(path=str(BINDING),sha256=sha(BINDING)),preparation_sources={})
    write(root/'dependencies.json',deps);prep.prepare_products(root)
    write(root/'probe-contract.json',dict(version='shared-alias-measurability-probe-v1',source_role='validation',kind='not_training',
        exact_requests=[dict(source='stage_shared_16',placement='placement-'+str(i),target_ps=1500) for i in range(2)],
        existing_model_prices='uncovered; intentionally never supplied to physical collection',readout='actual unique FF, alias Boolean proof, direct gate loads and full ownership',
        model_support_relaxation=False,parameters_fitted=False,full_D_ready=False))
    print('SHARED_ALIAS_PROBE_PREPARED placements=2 model_prices=uncovered',flush=True)


def admit(root,prepared):
    if root.exists():raise ValueError('preserve probe physical attempt')
    if read(prepared/'simulation.json')['status']!='passed':raise ValueError('actual cycle verification missing')
    tasks=[]
    for row in read(prepared/'structures.json')['rows']:
        if row['source']!='stage_shared_16' or row['role']!='validation':raise ValueError('only existing validation source allowed')
        ident='shared-alias-'+row['placement']+'-T1500';d=root/'inputs'/ident;d.mkdir(parents=True)
        rtl_text=(prepared/row['rtl']).read_text();tops=re.findall(r'\bmodule\s+(Stage7_\w+)\s*\(',rtl_text)
        if len(tops)!=1 or sha(prepared/row['rtl'])!=row['rtl_sha256']:raise ValueError('physical RTL identity drift')
        rtl=d/'input.sv';rtl.write_text(rtl_text.replace('module '+tops[0]+'(','module ModelBundle('))
        shutil.copy2(prepared/row['endpoint_contract'],d/'endpoints.json');shutil.copy2(prepared/'sources/stage_shared_16/request.json',d/'source.json')
        shutil.copy2(prepared/'sources/stage_shared_16/native/export.json',d/'export.json')
        tasks.append(dict(id=ident,source='stage_shared_16',source_role='validation',purpose='not_training_measurability',placement=row['placement'],period_ps=1500,
            rtl=str(rtl),rtl_sha256=sha(rtl),endpoint_contract=str(d/'endpoints.json'),endpoint_sha256=sha(d/'endpoints.json'),input_directory=str(d)))
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3);wall=2*1500+32*120
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources']
    if used['synth']+2+688>limits['max_synthesis_calls'] or used['grt']+2+688>limits['max_global_route_calls'] or used['walltime_s']+wall+86400>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+4*wall+172800>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(root).free<later['storage_bytes']+2*1024**3:raise ValueError('finite probe and future work not funded')
    from .operator_collection import measurement_sources
    names=set(measurement_sources())|{str(Path(__file__).relative_to(ROOT)),str(Path(shared.__file__).relative_to(ROOT)),str(Path(physical.__file__).relative_to(ROOT)),str(Path(prep.__file__).relative_to(ROOT)),
        'experiments/arithmetic_dse/stage67_mapped_state_v1.py','experiments/arithmetic_dse/stage67_mapped_state_v2.py','experiments/arithmetic_dse/stage67_mapped_state_v3.py','experiments/arithmetic_dse/model_m2_live_cec_v4.py'}
    hashes={}
    for n in sorted(names):
        d=root/'source'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,d);hashes[n]=sha(d)
    write(root/'admission.json',dict(version='shared-alias-two-placement-probe-v1',id=root.name,tasks=tasks,sources=hashes,
        model=dict(path=str(NODE),sha256=sha(NODE)),S_binding=dict(path=str(BINDING),sha256=sha(BINDING)),
        synth_max=2,grt_max=2,support_max=32,synth_timeout_s=300,grt_timeout_s=1200,threads=4,memory_limit_MiB=8192,parallel_jobs=2,automatic_retries=0,
        later_work_reserved=later,probe_role='not_training physical qualification; original source stays validation',uncovered_model_allowed_for_measurement_only=True,full_D_ready=False))
    write(root/'progress.json',dict(phase='admitted',completed=[],errors=[],active=[]));print('SHARED_ALIAS_PROBE_ADMITTED synth=2 grt=2',flush=True)


def point(root,task):
    text=inspect.getsource(physical.point)
    def verify(d,p,c,s):return shared.verify_state(d,p,c,s,Path(task['rtl']).read_text())
    ns=dict(physical.point.__globals__);ns['mapped']=SimpleNamespace(verify=verify)
    exec(compile(text.replace('model_m2_live_cec_v3','model_m2_live_cec_v4'),__file__,'exec'),ns);ns['point'](root,task)


def run(root):
    a=read(root/'admission.json');p=read(root/'progress.json')
    if p['completed'] or p['errors'] or p['active']:raise ValueError('no automatic probe retry')
    p.update(phase='running',active=[t['id'] for t in a['tasks']]);write(root/'progress.json',p)
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures={pool.submit(point,root,t):t for t in a['tasks']}
        for future in as_completed(futures):
            t=futures[future]
            try:future.result();p['completed'].append(t['id'])
            except Exception as e:p['errors'].append(dict(task=t['id'],reason=str(e)))
            p['active'].remove(t['id']);write(root/'progress.json',p)
    p['phase']='physical_batch_complete' if not p['errors'] else 'stopped_on_errors';write(root/'progress.json',p)
    print('SHARED_ALIAS_PROBE_SETTLED complete='+str(len(p['completed']))+' errors='+str(len(p['errors'])),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','admit','run'));p.add_argument('--root',type=Path,required=True);p.add_argument('--prepared',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.root.resolve())
    elif a.action=='admit':admit(a.root.resolve(),a.prepared.resolve())
    else:run(a.root.resolve())
