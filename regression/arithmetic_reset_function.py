"""Real reset candidate: numerical Python/C++ parity and domain rejection.

Physical exact1000 remains locked; these are function calls without labels.
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.stage67_reset_model_v2 import predict


def run(freeze,binary,data,out):
    if out.exists():raise ValueError('preserve actual reset inference parity')
    f=read(freeze)
    for n,h in f['files'].items():
        if sha(n)!=h:raise ValueError('reset inference freeze drift '+n)
    model=read(freeze.parent/'candidate.json');rows=read(data)['rows'];queries=[]
    for ff,ones in sorted({(r['features']['total_FF_bits'],r['features']['reset_one_bits']) for r in rows}):
        for t in (500.,750.,1000.,1250.,1500.,2200.,3000.):queries.append(dict(total_FF_bits=ff,reset_one_bits=ones,target_ps=t,native_depth=1))
    lo,hi=model['numeric_support']['total_FF_bits'];rlo,rhi=model['numeric_support']['reset_one_bits'];ff=(lo+hi)//2;ones=min(ff,rhi)
    base=dict(total_FF_bits=ff,reset_one_bits=ones,target_ps=1500.,native_depth=1);negative=[]
    for key,val in [('target_ps',499.),('target_ps',3001.),('target_ps',0.),('total_FF_bits',lo-1),('total_FF_bits',hi+1),('total_FF_bits',ff+.5),('reset_one_bits',rhi+1),('reset_one_bits',-1),('native_depth',0),('native_depth',2)]:
        q=dict(base);q[key]=val;negative.append(q)
    queries+=negative;out.mkdir(parents=True);write(out/'queries.json',queries)
    result=subprocess.run([str(binary),str(freeze.parent/'candidate.json'),str(out/'queries.json')],capture_output=True,text=True,timeout=60)
    (out/'native-stdout.json').write_text(result.stdout);(out/'native-stderr.log').write_text(result.stderr)
    if result.returncode:raise ValueError('native reset inference failed')
    native=json.loads(result.stdout);compared=[]
    if len(native)!=len(queries):raise ValueError('native query count differs')
    for i,(q,a) in enumerate(zip(queries,native)):
        try:p=predict(model,q['total_FF_bits'],q['reset_one_bits'],q['target_ps'],q['native_depth'])
        except ValueError as e:
            if a['covered']:raise ValueError('native accepted rejected domain')
            compared.append(dict(index=i,status='rejected',reason=str(e)));continue
        if not a['covered']:raise ValueError('native rejected covered domain')
        for key in ('point_intrinsic_ps','guard_intrinsic_ps','required_period_ps'):
            if not math.isclose(a[key],p[key],rel_tol=1e-12,abs_tol=1e-9):raise ValueError('native/Python reset differs '+key)
        if a['violates']!=p['violates']:raise ValueError('native/Python feasibility differs')
        compared.append(dict(index=i,status='covered',prediction=p))
    if any(r['status']!='rejected' for r in compared[-len(negative):]):raise ValueError('expected negative accepted')
    # A requested exact T has no label or discrete index and changes response.
    q=base;a=predict(model,q['total_FF_bits'],q['reset_one_bits'],1000.);b=predict(model,q['total_FF_bits'],q['reset_one_bits'],1500.)
    if math.isclose(a['point_intrinsic_ps'],b['point_intrinsic_ps']):raise ValueError('numerical T ignored')
    for n,h in f['files'].items():
        if sha(n)!=h:raise ValueError('frozen function changed during replay')
    write(out/'parity.json',dict(status='passed_real_reset_python_cpp_parity',rows=compared,covered=sum(r['status']=='covered' for r in compared),rejected=sum(r['status']=='rejected' for r in compared),
        candidate_sha256=sha(freeze.parent/'candidate.json'),native_sha256=sha(binary),physical_exact1000_unlocked=False,model_identity_features=False,full_D_ready=False))
    print('RESET_PARITY_PASS queries='+str(len(queries))+' expected_refusals='+str(len(negative)),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('freeze','binary','data','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();run(a.freeze.resolve(),a.binary.resolve(),a.data.resolve(),a.out.resolve())
