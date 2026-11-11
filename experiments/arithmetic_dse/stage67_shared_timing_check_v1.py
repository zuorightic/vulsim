"""Independent zero-G recurrence on the new graph/cut inventory.

No physical label or coefficient choice here. The former verified Python bit
oracle is reused with the new version tag and a separate shared-area parity
record; timing does not read those areas or prices.
"""
import argparse
import inspect
import math
from pathlib import Path

from . import stage67_factored_timing_v1 as parent
from .model_fast_preflight import read,write,sha
from .stage67_shared_fit_v1 import NODE,BINDING


def compare(native,policy_path,out):
    if out.exists():raise ValueError('preserve timing parity')
    n=read(native);policy=read(policy_path);m=read(NODE);s=read(BINDING.parent/'reused-S.json')
    if n['policy_sha256']!=sha(policy_path) or n['model_sha256']!=sha(NODE):raise ValueError('actual inference identity differs')
    text=inspect.getsource(parent.estimate).replace("policy['version']!='factored-state-shared-v1'","policy['version']!='factored-state-shared-v2'")
    namespace=dict(parent.estimate.__globals__);namespace['area']=lambda *args:{}
    exec(compile(text,__file__,'exec'),namespace);checked=0;captures=0;arcs=0;refused=0
    for source in n['sources']:
        for variant in source['variants']:
            for target in variant['targets']:
                actual=target['owned_timing']
                if actual['status']!='candidate_covered':refused+=1;continue
                p=namespace['estimate'](variant['graph'],variant,target,policy,m,s)
                if p['status']!='candidate_covered':raise ValueError('zero-G recurrence refused covered source')
                for left,right in zip(p['stages'],actual['stages'],strict=True):
                    a=[e|dict(wire_point_ps=policy['inter_arithmetic_wire_point_ps'] if e['owner']=='inter_arithmetic' else 0.) for e in left['connections']]
                    if a!=right['connections']:raise ValueError('native/Python exact connected bit arcs differ')
                    arcs+=len(a)
                    for x,y in zip(left['captures'],right['captures'],strict=True):
                        if x.keys()!=y.keys() or any(not math.isclose(x[k],y[k],abs_tol=1e-8,rel_tol=1e-10) for k in x):raise ValueError('native/Python point/guard/reserve timing differs')
                        captures+=1
                if not math.isclose(p['point_violation_ps'],actual['point_violation_ps'],abs_tol=1e-8):raise ValueError('native/Python worst point violation differs')
                checked+=1
    out.mkdir(parents=True);write(out/'timing-parity.json',dict(status='passed_new_graph_zero_G_language_parity',requests=checked,refused=refused,arcs=arcs,captures=captures,
        timing_parameters_changed=False,reserve_ps=50,physical_timing_quality_granted=False,full_D_ready=False))
    print(read(out/'timing-parity.json'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','policy','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();compare(a.native.resolve(),a.policy.resolve(),a.out.resolve())
