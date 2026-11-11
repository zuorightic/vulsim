"""Small common shared-area functions, portable stdlib fitting and inference.

Identifiers are absent from predict(). Source ID only balances train rows.
Validation is read only after candidate and implementation identities freeze.
"""
import argparse
from collections import Counter
from copy import deepcopy
import math
from pathlib import Path

from .model_fast_preflight import read,write,sha
from .stage67_shared_fit_v1 import FEATURES,ROOT,NODE,BINDING,PARENT,features
from .stage67_factored_timing_v1 import linear,complete_variant,estimate as old_estimate
from .operator_condition_model import query
from .stage67_batch1_analyze_v1 import stats


def solve(matrix,rhs):
    a=[list(row)+[b] for row,b in zip(matrix,rhs)];n=len(rhs)
    for c in range(n):
        pivot=max(range(c,n),key=lambda i:abs(a[i][c]))
        if abs(a[pivot][c])<1e-13:return None
        a[c],a[pivot]=a[pivot],a[c];scale=a[c][c];a[c]=[v/scale for v in a[c]]
        for i in range(n):
            if i==c:continue
            value=a[i][c];a[i]=[x-value*y for x,y in zip(a[i],a[c])]
    return [row[-1] for row in a]


def fit_models(rows,definitions):
    if not rows or any(r['role']!='train' for r in rows):raise ValueError('nontrain row prohibited')
    result={};counts=Counter(r['source'] for r in rows)
    for owner,names in definitions.items():
        scales=[max(1.,max(abs(r['features'][n]) for r in rows)) for n in names]
        x=[[r['features'][n]/s for n,s in zip(names,scales)] for r in rows];y=[r['labels'][owner] for r in rows];w=[1/counts[r['source']] for r in rows]
        g=[[math.fsum(weight*v[i]*v[j] for weight,v in zip(w,x)) for j in range(len(names))] for i in range(len(names))]
        h=[math.fsum(weight*v[i]*z for weight,v,z in zip(w,x,y)) for i in range(len(names))];best=None
        for mask in range(1<<len(names)):
            active=[i for i in range(len(names)) if mask>>i&1];solution=solve([[g[i][j] for j in active] for i in active],[h[i] for i in active]) if active else []
            if solution is None or any(v< -1e-9 for v in solution):continue
            c=[0.]*len(names)
            for i,v in zip(active,solution):c[i]=max(0.,v)
            loss=math.fsum(weight*(math.fsum(a*b for a,b in zip(v,c))-z)**2 for weight,v,z in zip(w,x,y))
            if best is None or loss<best[0]:best=(loss,c)
        coefficients=[v/s for v,s in zip(best[1],scales)]
        result[owner]=dict(kind='nonnegative_linear',features=names,coefficients=coefficients,
            numeric_support={n:[min(r['features'][n] for r in rows),max(r['features'][n] for r in rows)] for n in names},
            training_rows=len(rows),training_sources=len(counts),objective='source-balanced train-only squared error; fixed features, no validation selection')
    return result


def predict(policy,f,t):
    if not math.isfinite(t) or not policy['target_interval_ps'][0]<=t<=policy['target_interval_ps'][1]:raise ValueError('outside numerical T support')
    if any(not math.isfinite(v) or v<0 for v in f.values()):raise ValueError('invalid numerical feature')
    if not math.isclose(f['clock_pressure'],1500/t,rel_tol=1e-12) or not math.isclose(f['sqrt_FF_bits']**2,f['total_FF_bits'],rel_tol=1e-12):raise ValueError('inconsistent derived features')
    return {owner:linear(m,f) for owner,m in policy['shared_area_models'].items()}


def fit(data,protocol,out):
    if out.exists():raise ValueError('preserve candidate fit')
    out.mkdir(parents=True);d=read(data);p=read(protocol)
    if p['features']!=FEATURES or d['protocol_sha256']!=sha(protocol):raise ValueError('prospective feature/protocol drift')
    expected={(v['source'],v['target_ps']) for v in p['train_requests']};actual={(r['source'],r['target_ps']) for r in d['rows']}
    if actual!=expected or len(d['rows'])!=len(expected):raise ValueError('all registered training requests required')
    policy=read(PARENT);policy.update(version='factored-state-shared-v2',shared_area_models=fit_models(d['rows'],p['features']),
        parent_policy_sha256=sha(PARENT),quality_status='candidate_accounting',fit_protocol_sha256=sha(protocol),training_dataset_sha256=sha(data),
        training_context='actual compatible independent service writes, held-valid, native state, unconditional reset-bearing output capture',
        area_features='prediction-time semantic numerical features; no source/shape/placement/exact-T indicators',validation_labels_read=False,
        joint_quality='not yet validated',full_D_ready=False)
    write(out/'candidate.json',policy);diagnostics=[]
    for r in d['rows']:
        a=predict(policy,r['features'],r['target_ps']);diagnostics.append(dict(source=r['source'],target_ps=r['target_ps'],owners={n:dict(predicted=a[n],actual=y,relative_error=abs(a[n]-y)/max(.01,y)) for n,y in r['labels'].items()}))
    write(out/'training-diagnostic.json',dict(rows=diagnostics,errors={n:stats([r['owners'][n]['relative_error'] for r in diagnostics]) for n in FEATURES},validation_labels_read=False))
    files=[out/'candidate.json',Path(__file__),ROOT/'experiments/arithmetic_dse/stage67_shared_fit_v1.py',
        ROOT/'experiments/arithmetic_dse/stage67_factored_timing_v1.py',ROOT/'experiments/arithmetic_dse/operator_condition_model.py',
        ROOT/'experiments/arithmetic_dse/stage67_shared_extract_v2.py',
        ROOT/'rtlzz/src/backend/arithmetic_shared_function.cpp',ROOT/'rtlzz/src/backend/arithmetic_shared_function.hpp',
        ROOT/'rtlzz/testv2/arithmetic_shared_function_consumer.cpp',ROOT/'rtlzz/testv2/arithmetic_shared_function_mac32.cpp',
        ROOT/'build/step4-rtlzz/testv2/arithmetic-shared-function-consumer',ROOT/'build/step4-rtlzz/testv2/arithmetic-shared-function-mac32',
        NODE,BINDING,protocol,data]
    write(out/'freeze.json',dict(version='shared-function-freeze-v1',files={str(n):sha(n) for n in files},
        parameters_support_features_reserve_implementation_frozen=True,validation_labels_read=False,independent_tests_unlocked=False,full_D_ready=False))
    print(dict(status='candidate_frozen',candidate_sha256=sha(out/'candidate.json'),training=read(out/'training-diagnostic.json')['errors'],full_D_ready=False),flush=True)


def validate(data,freeze,out):
    if out.exists():raise ValueError('preserve one-time validation')
    f=read(freeze)
    for n,h in f['files'].items():
        if sha(n)!=h:raise ValueError('frozen implementation/model drift '+n)
    policy_path=freeze.parent/'candidate.json';policy=read(policy_path);d=read(data);rows=[];failures=[];refused=[]
    if any(r['role']!='validation' for r in d['rows']):raise ValueError('fresh validation role required')
    train=read(next(n for n in f['files'] if n.endswith('dataset.json')))
    if {r['source'] for r in train['rows']}&{r['source'] for r in d['rows']}:raise ValueError('train/validation source overlap')
    for r in d['rows']:
        try:a=predict(policy,r['features'],r['target_ps'])
        except ValueError as e:refused.append(dict(source=r['source'],target_ps=r['target_ps'],reason=str(e)));continue
        total=r['features']['predicted_functional_area_um2']+sum(a.values());actual=r['total_area_um2']
        rows.append(dict(source=r['source'],target_ps=r['target_ps'],features=r['features'],owners={n:dict(predicted=a[n],actual=y,relative_error=abs(a[n]-y)/max(.01,y)) for n,y in r['labels'].items()},
            total_area=dict(predicted=total,actual=actual,relative_error=abs(total-actual)/max(.01,actual))))
    errors={n:stats([r['owners'][n]['relative_error'] for r in rows]) for n in FEATURES};total=stats([r['total_area']['relative_error'] for r in rows])
    for n,v in errors.items():
        if v['median']>.15 or v['P95']>.35:failures.append(n+'/owner_error')
    if total['median']>.15 or total['P95']>.35:failures.append('total_area_error')
    if refused:failures.append('validation_support_refusals')
    out.mkdir(parents=True);write(out/'validation.json',dict(status='failed_fresh_validation' if failures else 'passed_shared_validation_not_joint',rows=rows,refused=refused,owner_errors=errors,total_error=total,failures=failures,
        candidate_sha256=sha(policy_path),validation_dataset_sha256=sha(data),parameters_changed_after_validation=False,
        stage_timing_evaluated=False,zero_G_joint_qualified=False,independent_tests_unlocked=False,full_D_ready=False))
    print(dict(status=read(out/'validation.json')['status'],owner_errors=errors,total_error=total,failures=failures,refused=len(refused)),flush=True)


def parity(native,policy_path,out):
    if out.exists():raise ValueError('preserve cross-language comparison')
    policy=read(policy_path);m=read(NODE);s=read(Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/reused-S.json'));n=read(native);rows=[]
    for source in n['sources']:
        for v in source['variants']:
            for target in v['targets']:
                # Independent semantic projection including numeric input reset.
                owners={k:dict(data_bits=0,data_signals=0,enable_domains=0,valid_bits=0,reset_one_bits=0) for k in ('input_service','native_state','external_state')}
                inputs={x['name']:x for x in source['input_ports']};controls=set(v['cuts'][0]['controls'])
                for x in v['graph']['nodes']:
                    if x['kind']!='input' or x['id'] in controls:continue
                    active=x['width']-len(set(x['known_zero'])|set(x['known_one']))
                    if active:
                        o=owners['input_service'];o['data_bits']+=active;o['data_signals']+=1
                owners['input_service'].update(valid_bits=1,enable_domains=len(inputs)+1,reset_one_bits=sum(int(x['reset_hex'],16).bit_count() for x in inputs.values()))
                enables=set()
                for slot in v['state']['slots']:
                    o=owners['external_state' if slot['external_capture'] else 'native_state']
                    if slot['valid']:o['valid_bits']+=1;continue
                    if slot['variable_bits']:
                        o['data_bits']+=slot['variable_bits'];o['data_signals']+=1
                        reset=sum(int(x,16)<<(64*i) for i,x in enumerate(slot['reset_hex']));mask=sum(int(x,16)<<(64*i) for i,x in enumerate(slot['variable_mask_hex']));o['reset_one_bits']+=(reset&mask).bit_count()
                        if not slot['external_capture']:enables.add(slot['enable_stage'])
                owners['native_state']['enable_domains']=len(enables)
                areas={k:linear(s['stages']['grt']['area_models'][k],o) for k,o in owners.items()};prices=[query(m,q['descriptor']) for q in target['queries']]
                if any(p['status']!='covered' for p in prices):raise ValueError('fresh node query refused')
                areas['operators']=sum(p['comb_area_um2'] for p in prices)
                f=features(dict(owner_features=owners,total_FF_bits=sum(o['data_bits']+o['valid_bits'] for o in owners.values())),sum(areas.values()),target['target_ps'])
                try:areas.update(predict(policy,f,target['target_ps']));status='candidate_covered'
                except ValueError:status='cost_uncovered'
                a=target['owned_timing']
                if a['status']!=status:raise ValueError('native/Python support differs')
                if status=='candidate_covered':
                    for name,val in areas.items():
                        if not math.isclose(a['owner_area_um2'][name],val,abs_tol=1e-8,rel_tol=1e-10):raise ValueError('native/Python exclusive area differs '+name)
                    if set(f)!=set(a['shared_features']) or any(not math.isclose(val,a['shared_features'][name],abs_tol=1e-8,rel_tol=1e-10) for name,val in f.items()):raise ValueError('native/Python actual semantic feature differs')
                    if not math.isclose(a['total_area_um2'],sum(areas.values()),abs_tol=1e-8,rel_tol=1e-10):raise ValueError('native/Python area sum differs')
                rows.append(dict(source=source['source'],target_ps=target['target_ps'],status=status,features=f))
    # Function invariance: identity fields do not exist at this interface.
    negatives=0
    for r in rows:
        for name in ('total_FF_bits','predicted_functional_area_um2','input_data_bits','reset_one_bits','input_ports','clock_pressure'):
            modified=dict(r['features']);models=[x for x in policy['shared_area_models'].values() if name in x['numeric_support']]
            modified[name]=max(x['numeric_support'][name][1] for x in models)*10+100
            try:predict(policy,modified,r['target_ps'])
            except ValueError:negatives+=1
            else:raise ValueError('outside-domain feature accepted '+name)
    out.mkdir(parents=True);write(out/'parity.json',dict(status='passed_general_shared_native_parity',rows=rows,counts=dict(Counter(r['status'] for r in rows)),negative_checks=negatives,
        numerical_targets=sorted({r['target_ps'] for r in rows}),physical_1000ps_unlocked=False,parameters_selected_using_unseen_T=False,full_D_ready=False))
    print(dict(status='passed_general_shared_native_parity',counts=dict(Counter(r['status'] for r in rows)),negative_checks=negatives),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('fit','validate','parity'))
    for k in ('data','protocol','out','freeze','native','policy'):p.add_argument('--'+k,type=Path)
    a=p.parse_args()
    if a.action=='fit':fit(a.data.resolve(),a.protocol.resolve(),a.out.resolve())
    elif a.action=='validate':validate(a.data.resolve(),a.freeze.resolve(),a.out.resolve())
    else:parity(a.native.resolve(),a.policy.resolve(),a.out.resolve())


if __name__=='__main__':main()
