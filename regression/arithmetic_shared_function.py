"""Qualify common shared functions without adding model parameters."""
import argparse
from copy import deepcopy
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha
from experiments.arithmetic_dse.stage67_shared_model_v1 import fit_models
from experiments.arithmetic_dse.stage67_shared_model_v2 import predict
from experiments.arithmetic_dse.stage67_analyze_v1 import verify_ownership_packet


def qualify(root,out):
    if out.exists():raise ValueError('preserve qualification')
    policy=read(root/'fit-v1/candidate.json');rows=read(root/'train-labels-v1/dataset.json')['rows'];protocol=read(root/'preparation-v2/protocol.json')
    from collections import Counter
    import numpy as np
    from scipy.optimize import nnls
    counts=Counter(r['source'] for r in rows);comparisons=[]
    for owner,model in policy['shared_area_models'].items():
        names=model['features'];x=np.asarray([[r['features'][n] for n in names] for r in rows]);y=np.asarray([r['labels'][owner] for r in rows]);weights=np.asarray([1/math.sqrt(counts[r['source']]) for r in rows]);c,_=nnls(x*weights[:,None],y*weights)
        expected=x@np.asarray(model['coefficients']);independent=x@c
        if not np.allclose(expected,independent,rtol=1e-8,atol=1e-7):raise ValueError('stdlib/scipy NNLS predictions differ')
        comparisons.append(dict(owner=owner,max_prediction_difference_um2=float(np.max(np.abs(expected-independent)))))
    renamed=deepcopy(rows);groups={n:'arbitrary-renamed-'+str(i) for i,n in enumerate(sorted(counts))}
    for r in renamed:r['source']=groups[r['source']]
    a=fit_models(renamed,protocol['features']);b=fit_models(list(reversed(rows)),protocol['features'])
    for name,m in policy['shared_area_models'].items():
        for other in (a[name],b[name]):
            if not all(math.isclose(x,y,rel_tol=1e-9,abs_tol=1e-8) for x,y in zip(m['coefficients'],other['coefficients'])):raise ValueError('source spelling or row order changes function')
    negatives=[]
    for r in rows:
        f=r['features'];t=r['target_ps'];predict(policy,f,t)
        for name in ('total_FF_bits','input_data_bits','input_ports','reset_one_bits','predicted_functional_area_um2','clock_pressure'):
            bad=dict(f);bad[name]=float('nan')
            try:predict(policy,bad,t)
            except ValueError:negatives.append('nonfinite_'+name)
            else:raise ValueError('nonfinite feature accepted')
        for t_bad in (499,3001,0,float('nan')):
            try:predict(policy,f,t_bad)
            except ValueError:negatives.append('outside_T')
            else:raise ValueError('outside T accepted')
    witness=read(next((root/'train-inherited-labels-v2').glob('*-ownership.json')));verify_ownership_packet(witness)
    bad=deepcopy(witness);n=next(iter(bad['owners']));bad['owners'][n]='invented_owner'
    try:verify_ownership_packet(bad)
    except ValueError:negatives.append('forged_actual_owner')
    else:raise ValueError('forged ownership accepted')
    demand=read(root/'mac32-v1/proof.json');refusals=[v for t in demand['targets'] for v in t['views'] if v['estimate']['status']!='candidate_covered']
    if refusals:raise ValueError('minimum actual demand remains uncovered')
    # Shape/placement IDs only name regression rows; predictors get the same
    # numerical fields for all cases, including unsampled exact clock values.
    out.mkdir(parents=True);write(out/'proof.json',dict(status='passed_general_shared_function_checks',scipy_independent_fit=comparisons,
        row_order_and_source_spelling_invariant=True,negative_checks=len(negatives),MAC32_requests=sum(len(t['views']) for t in demand['targets']),MAC32_refusals=0,
        exact_T_inference=[t['target_ps'] for t in demand['targets']],locked_joint_measurements=0,full_D_ready=False))
    print(read(out/'proof.json'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();qualify(a.root.resolve(),a.out.resolve())
