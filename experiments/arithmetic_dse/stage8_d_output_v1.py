"""Finite software D delivery; reset timing deferred by explicit user scope."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage

ROOT=Path(__file__).resolve().parents[2]
SHARED=Path('/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1')
NODE=ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'
BINDING=Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/binding-candidate.json')
SOURCE=ROOT/'build/step7-operator-query-20261110/query-hierarchy-20261110-v4/input/request.json'


def prepare(out):
    if out.exists():raise ValueError('preserve D output package')
    freeze=read(SHARED/'fit-v1/freeze-v2.json')
    for n,h in freeze['files'].items():
        if sha(n)!=h:raise ValueError('frozen node/S/composition dependency drift '+n)
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3)
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources'];wall=24*600
    if used['synth']+688>limits['max_synthesis_calls'] or used['grt']+688>limits['max_global_route_calls'] or used['walltime_s']+wall+86400>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+4*wall+172800>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(out.parent).free<later['storage_bytes']+2*1024**3:raise ValueError('finite D software batch and later reserve unfunded')
    source=deepcopy(read(SOURCE)['source']);source_path=Path(source['source'])
    if sha(source_path)!=source['generated_source_sha256']:raise ValueError('public source drift')
    out.mkdir(parents=True);shutil.copy2(source_path,out/'source.cpp');source['source']=str(out/'source.cpp')
    write(out/'source-request.json',dict(version='D-source-metadata-v1',source=source))
    deps={name:dict(path=str(p),sha256=sha(p)) for name,p in [('node',NODE),('S_binding',BINDING),('composition',SHARED/'fit-v1/candidate.json'),('freeze',SHARED/'fit-v1/freeze-v2.json')]}
    write(out/'admission.json',dict(version='function-D-software-output-v1',user_scope='先不管reset的问题，先往后推进，让D端产出',output_scope='prototype-no-reset-timing-v1',
        targets_ps=[500,1000,1250,1500,3000],latency=2,II=1,dependencies=deps,source_request_sha256=sha(out/'source-request.json'),source_sha256=sha(out/'source.cpp'),
        source_role='public MAC32 output demonstration; no model fit or physical test labels',selection='all covered candidates priced from numerical functions, feasible area or closest timing fallback',
        budget=dict(synth=0,grt=0,final=0,support=24,per_leaf_timeout_s=600,threads=4,memory_MiB=8192,parallel_jobs=4),later_work_reserved=later,
        reset_functional_preserved=True,reset_timing_checked=False,locked_physical_tests_unlocked=False,full_D_ready=False))
    print('D_OUTPUT_ADMITTED five_numerical_targets L=2 II=1 EDA=0',flush=True)


def verify(out):
    a=read(out/'admission.json')
    for d in a['dependencies'].values():
        if sha(d['path'])!=d['sha256']:raise ValueError('D frozen dependency drift')
    for n,h in read(a['dependencies']['freeze']['path'])['files'].items():
        if sha(n)!=h:raise ValueError('D published inference drift '+n)
    if sha(out/'source-request.json')!=a['source_request_sha256'] or sha(out/'source.cpp')!=a['source_sha256']:raise ValueError('D source changed')
    return a


def command(out,binary,target,destination,limit=None,request=None):
    a=verify(out);d=a['dependencies']
    cmd=[str(binary),'--root',str(ROOT),'--source-request',str(request or out/'source-request.json'),'--node-model',d['node']['path'],
        '--state-binding',d['S_binding']['path'],'--composition-policy',d['composition']['path'],'--period-ps',str(target),'--latency',str(a['latency']),
        '--output-scope',a['output_scope'],'--out',str(destination)]
    if limit is not None:cmd+=['--assignment-limit',str(limit)]
    return cmd


def run(out,binary):
    from regression.arithmetic_steps123 import execute
    a=verify(out)
    for t in a['targets_ps']:
        execute(out/'receipts'/('d8-run-T'+str(t)),'D-function-select',command(out,binary,t,out/'outputs'/('T'+str(t))),600)
    write(out/'run-status.json',dict(status='D_RTL_outputs_emitted',targets=a['targets_ps'],backend_calls=0,full_D_ready=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','run'));p.add_argument('--out',type=Path,required=True);p.add_argument('--binary',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve())
    else:run(a.out.resolve(),a.binary.resolve())
