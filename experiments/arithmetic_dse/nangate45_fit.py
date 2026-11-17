"""Pre-registered source-balanced N4 calibration and sealed-test evaluation."""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import itertools
import math
from pathlib import Path

import numpy as np
from .nangate45_samples import ROOT,read,write,sha,verify
from . import nangate45_model as model
from . import centered_response as response
from . import workload_diagnostic as old

OLD=ROOT/'experiments/arithmetic/evidence/workload_equivalent_mac32_v1/diagnostic-model.json'


def dataset(root,roles):
    a=verify(root);rows=[]
    for t in a['tasks']:
        if t['role'] not in roles:continue
        s=next(s for s in a['sources'] if s['id']==t['source'])
        path=root/'runs'/t['id']/'grt-labels.json';label=read(path)
        if label['profile_sha256']!=a['profile_sha256'] or label['source_role']!=t['role'] or not label['physical_training_label_eligible']:
            raise ValueError('label identity/role invalid')
        node=label['nodes']['producer']
        pair=next(r for r in s['paired_ASAP7'] if r['target_ps']==t['period_ps'])
        if sha(pair['label'])!=pair['label_sha256']:raise ValueError('paired ASAP7 label changed')
        prior=read(pair['label']);pnode=prior['nodes']['producer']
        row=dict(source=t['source'],family=t['family'],role=t['role'],target_ps=t['period_ps'],query=s['query'],
                 label_path=str(path),label_sha256=sha(path),ASAP7_label_path=pair['label'],ASAP7_label_sha256=pair['label_sha256'],
                 delay_ps=node['operator_delay_ps'],area_um2=node['comb_area_um2'],
                 ASAP7_delay_ps=pnode['operator_delay_ps'],ASAP7_area_um2=pnode['comb_area_um2'])
        rows.append(row)
    return rows


def metrics(rows,predicted,key):
    groups=defaultdict(list)
    for r,p in zip(rows,predicted,strict=True):groups[r['source']].append(abs(p/r[key]-1.))
    by={s:float(np.median(v)) for s,v in groups.items()};v=list(by.values())
    return dict(rows=len(rows),sources=len(v),median_APE=float(np.median(v)),P95_APE=float(np.quantile(v,.95)),
                per_source_median_APE=by,passed=bool(np.median(v)<=.15 and np.quantile(v,.95)<=.35 and max(v)<=.35))


def weights(rows):
    c=Counter(r['source'] for r in rows);w=np.array([1/c[r['source']] for r in rows]);return w/w.sum()


def fit_function(rows,family,metric,form,time_scale,prices,alpha=None):
    values=[model.basis(r['family'],r['query'],r['target_ps'],metric,prices,time_scale) for r in rows]
    ref=np.array([v[0] for v in values]);y=np.array([r[metric] for r in rows]);w=weights(rows)
    fn=dict(form=form,time_scale=time_scale)
    if form in ('global_scale','family_scale'):
        fn['scale']=float(np.exp(w@np.log(y/ref)))
    elif form=='family_affine':
        x=np.array([ref/y,1/y]).T;z=np.ones(len(y))
        c=np.linalg.lstsq(x*np.sqrt(w)[:,None],z*np.sqrt(w),rcond=None)[0]
        fn.update(scale=float(max(0,c[0])),intercept=float(c[1]))
    else:
        names=model.FEATURES[family];x=np.array([[v[1][n] for n in names] for v in values]);latent=np.log(y/ref)
        mean=w@x;scale=np.sqrt(w@((x-mean)**2));active=scale>1e-10;scale[~active]=1.;z=(x-mean)/scale;z[:,~active]=0
        intercept=float(w@latent);coef=np.linalg.solve((z.T*w)@z+alpha*np.eye(len(names)),(z.T*w)@(latent-intercept))
        fn.update(alpha=alpha,response=dict(version=response.VERSION,features=names,centers=mean.tolist(),scales=scale.tolist(),
            coefficients=coef.tolist(),intercept=intercept,link='positive_log_linear'))
    return fn


def predict(fn,rows,family,metric,prices):
    result=[]
    for r in rows:
        ref,f=model.basis(family,r['query'],r['target_ps'],metric,prices,fn['time_scale'])
        if fn['form'] in ('global_scale','family_scale'):v=ref*fn['scale']
        elif fn['form']=='family_affine':v=max(1e-9,ref*fn['scale']+fn['intercept'])
        else:v=ref*response.predict(fn['response'],f)
        result.append(v)
    return result


def freeze(root):
    if (root/'frozen-model.json').exists():raise ValueError('selected model already frozen')
    if any((root/'runs'/t['id']).exists() for t in verify(root)['tasks'] if t['role']=='test'):
        raise ValueError('test collection started before model freeze')
    a=verify(root);rows=dataset(root,('train','validation'));bundle=read(OLD);prices=old.DiagnosticPrices(bundle)
    functions={};audits={}
    for family in model.FEATURES:
        train=[r for r in rows if r['family']==family and r['role']=='train'];val=[r for r in rows if r['family']==family and r['role']=='validation']
        functions[family]={};audits[family]={}
        for metric in ('delay_ps','area_um2'):
            candidates=[]
            for form in a['model_candidates']:
                for ts in a['request_time_scale_candidates']:
                    for alpha in (a['ridge_alpha'] if form=='shared_log_feature_ridge' else [None]):
                        fit_rows=[r for r in rows if r['role']=='train'] if form=='global_scale' else train
                        fn=fit_function(fit_rows,family,metric,form,ts,prices,alpha)
                        stats=metrics(val,predict(fn,val,family,metric,prices),metric)
                        candidates.append(dict(function=fn,validation=stats))
            ranks={n:i for i,n in enumerate(a['model_candidates'])}
            chosen=min(range(len(candidates)),key=lambda i:(candidates[i]['validation']['median_APE'],candidates[i]['validation']['P95_APE'],ranks[candidates[i]['function']['form']],i))
            functions[family][metric]=candidates[chosen]['function']
            audits[family][metric]=dict(chosen=chosen,candidates=candidates,
                train=metrics(train,predict(functions[family][metric],train,family,metric,prices),metric))
    doc=dict(version=model.VERSION,target_platform='nangate45',profile_sha256=a['profile_sha256'],functions=functions,
             ASAP7_response=bundle,ASAP7_response_sha256=sha(OLD),admission_sha256=sha(root/'admission.json'),
             clock_support_ps=[min(a['clocks_ps']),max(a['clocks_ps'])],full_D_ready=False,qualification='pending sealed new-backend tests; arithmetic only',
             source_keys_used_in_inference=False,exact_clock_tables=False,backend_called_at_inference=False,
             application_PPA_used=False,characterization_H_pending_N6=True,S_shared_pending_N5=True,
             support='limited paired unsigned Mul/Add/ADC/G shells; unmeasured shapes/widths/loads/large G remain extrapolations')
    write(root/'selection.json',audits);write(root/'calibration-data.json',rows);write(root/'frozen-model.json',doc)
    write(root/'model-freeze.json',dict(model_sha256=sha(root/'frozen-model.json'),selection_sha256=sha(root/'selection.json'),
                                      calibration_data_sha256=sha(root/'calibration-data.json'),test_labels_read=False,fit_parameters_final=True))
    return {f:{m:functions[f][m]['form'] for m in functions[f]} for f in functions}


def evaluate(root):
    a=verify(root);seal=read(root/'model-freeze.json')
    if sha(root/'frozen-model.json')!=seal['model_sha256']:raise ValueError('frozen parameters changed')
    if (root/'evaluation.json').exists():raise ValueError('sealed evaluation already consumed; use saved evidence')
    rows=dataset(root,('train','validation','test'));payload=read(root/'frozen-model.json');prices=old.DiagnosticPrices(payload['ASAP7_response'])
    stats={};paired={};predictions=[]
    for f in model.FEATURES:
        stats[f]={};paired[f]={}
        for metric in ('delay_ps','area_um2'):
            stats[f][metric]={}
            for role in ('train','validation','test'):
                rr=[r for r in rows if r['family']==f and r['role']==role]
                pp=predict(payload['functions'][f][metric],rr,f,metric,prices)
                stats[f][metric][role]=metrics(rr,pp,metric)
                predictions.extend(dict(source=r['source'],family=f,role=role,target_ps=r['target_ps'],metric=metric,actual=r[metric],prediction=p,error_fraction=abs(p/r[metric]-1)) for r,p in zip(rr,pp))
            # Actual-to-actual scaling is evaluated separately from reuse of
            # an imperfect ASAP7 fitted function. Never conflate the two.
            tr=[r for r in rows if r['family']==f and r['role']=='train'];w=weights(tr)
            ratio=float(np.exp(w@np.log([r[metric]/r['ASAP7_'+metric] for r in tr])))
            paired[f][metric]=dict(scale=ratio,roles={role:metrics(
                [r for r in rows if r['family']==f and r['role']==role],
                [ratio*r['ASAP7_'+metric] for r in rows if r['family']==f and r['role']==role],metric) for role in ('train','validation','test')})
    all_pass=all(stats[f][m]['test']['passed'] for f in stats for m in stats[f])
    report=dict(version='nangate45-N34-evaluation-v1',model_sha256=seal['model_sha256'],stats=stats,paired_actual_scaling=paired,
                arithmetic_test_gates_passed=all_pass,full_D_ready=False,test_labels_returned_to_fit=False,
                test_sources_are_new_backend_holdouts_only=True,unseen_ASAP7_structures=False,
                training_rows=sum(r['role']=='train' for r in rows),validation_rows=sum(r['role']=='validation' for r in rows),test_rows=sum(r['role']=='test' for r in rows),
                finite_campaign_complete=True,remaining=['N5 S/shared/composition and G embedding','N6 characterization H and full D package qualification'])
    write(root/'evaluation-data.json',rows);write(root/'predictions.json',predictions);write(root/'evaluation.json',report)
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('freeze','evaluate'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    import json
    print(json.dumps(freeze(a.root) if a.action=='freeze' else evaluate(a.root),indent=2))
