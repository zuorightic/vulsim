"""Mux-only static-context fitting; all prices of other operators stay frozen."""
import argparse
from collections import Counter
import copy
import hashlib
from importlib.metadata import version
import json
import os
from pathlib import Path
import shutil
import sys

from . import model_m2_mux_fit as base
from .model_collection import sha,write
from .model_m2_mux_fit_v2 import verify_fit as verify_parent
from .model_m2_mux_static_features import VERSION,FEATURES,descriptor,features,predict
from .model_m2_mux_static_algorithms import algorithms
from .model_features import infer
from .model_m2_fit import quality as scalar_quality
from .model_m2_fit_v4 import width_key,target_key

ROOT=Path(__file__).resolve().parents[2]
CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_mux_static_v1.json'


def read(path):return json.loads(Path(path).read_text())


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def quality(rows,model,quantity):
    values=[predict(model,r,quantity) for r in rows]
    adjusted=[{**r,'features':{'lhs_width':v}} for r,v in zip(rows,values)]
    identity={'kind':'linear','features':['lhs_width'],'coefficients':[1.],'intercept':0.}
    return scalar_quality(adjusted,identity,'delay_ps' if quantity=='delay' else 'comb_area_um2')


def extract(data_path,out,native=None):
    import subprocess
    data,a=base.validate_data(data_path);legacy=read(a['parent_plan']);tasks={t['id']:t for t in legacy['tasks']};tasks.update({t['id']:t for t in a['tasks']})
    result=copy.deepcopy(data);contexts={};parity={}
    for row in result['rows']:
        t=tasks[row['task_id']];contract=read(t['sample_contract']);cut=descriptor(contract['labels']);h=digest(cut)
        contexts[h]=cut;row['static_context_sha256']=h;row['static_features']=features(row['features'],cut,row['spec']['id'])
        if native and row['source_sha256'] not in parity:
            shape='mixed' if row['source_context']=='legacy_mixed_control' else str(t['replicas'])
            actual=json.loads(subprocess.run([str(native),str(row['spec']['lhs_width']),str(row['spec']['fanout']),shape],check=True,capture_output=True,text=True).stdout)
            expected={k:row['static_features'][k] for k in row['static_features'] if k.startswith('context_') or k=='selector_fanout_bits'}
            if not actual['covered'] or actual['features']!=expected:raise ValueError('actual BEIR static features differ from contract reconstruction')
            parity[row['source_sha256']]=actual['features']
    result.update(version='asap7-m2-mux-static-fitting-data-v1',feature_schema=VERSION,static_contexts=contexts,
        parent_dataset_path=str(data_path.resolve()),parent_dataset_sha256=sha(data_path),static_protocol_sha256=sha(CONFIG),
        native_feature_parity={'executable_sha256':sha(native),'source_groups':parity} if native else None)
    if out.exists():raise ValueError('preserve existing static-context data')
    write(out,result);print(json.dumps({'status':'extracted','rows':len(result['rows']),'source_groups':len(parity),'features':len(FEATURES),'backend_reexecuted':False}),flush=True)


def validate(path):
    d=read(path)
    if (d.get('version')!='asap7-m2-mux-static-fitting-data-v1' or d.get('feature_schema')!=VERSION
        or sha(CONFIG)!=d['static_protocol_sha256'] or sha(d['parent_dataset_path'])!=d['parent_dataset_sha256']):raise ValueError('changed Mux static-context fitting identity')
    original,a=base.validate_data(Path(d['parent_dataset_path']))
    if len(d['rows'])!=len(original['rows']) or len(d['rows'])!=768:raise ValueError('incomplete Mux static rows')
    old={r['id']:r for r in original['rows']}
    for r in d['rows']:
        parent=old[r['id']];cut=d['static_contexts'][r['static_context_sha256']]
        if digest(cut)!=r['static_context_sha256'] or r['static_features']!=features(parent['features'],cut,parent['spec']['id']):raise ValueError('static context/feature changed')
        if {k:v for k,v in r.items() if k not in ('static_context_sha256','static_features')}!=parent:raise ValueError('static successor changed original numeric label')
    if not d.get('native_feature_parity') or len(d['native_feature_parity']['source_groups'])!=48:raise ValueError('all48 fitted source contexts require native feature parity')
    return d,a


def raw_predict(p,row):return infer(p,row['static_features'],feature_names=FEATURES)


def component(rows):
    import numpy as np
    if any(r['split'] not in ('train','validation') for r in rows):raise ValueError('static Mux fit rejects independent rows')
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
    def fit_rows(items):return [{**r,'features':r['static_features']} for r in items]
    raw=dict(algorithms(fit_rows(train),'delay_ps',1.5));folds={}
    for source in sorted({r['source_sha256'] for r in train}):folds[source]=dict(algorithms(fit_rows([r for r in train if r['source_sha256']!=source]),'delay_ps',1.5))
    candidates=[];models={}
    for name,p in raw.items():
        margin=float(np.quantile([max(0,r['delay_ps']-raw_predict(p,r)) for r in val],.95))+1.5
        vr=max([1.]+[r['delay_ps']/max(1.5,raw_predict(p,r)) for r in val])
        cr=max([1.]+[r['delay_ps']/max(1.5,raw_predict(folds[r['source_sha256']][name],r)) for r in train])
        for reserve,scale,offset in (('validation_positive_p95',1.,margin),('complete_source_ratio',max(vr,cr)*1.05,1.5)):
            key=name+'/'+reserve;model={'kind':'pooled','predictor':p,'delay_scale':scale,'delay_margin_ps':offset,'algorithm':name,'calibration':reserve}
            q=quality(val,model,'delay');models[key]=model;candidates.append({'key':key,'quality':q,'delay_scale':scale,'delay_margin_ps':offset})
    chosen=min(candidates,key=lambda c:(c['quality']['status']!='passed',c['quality']['MAE'],c['quality']['p95_relative_error'],len(json.dumps(models[c['key']])),c['key']))
    return models[chosen['key']],{'selected':chosen['key'],'quality':chosen['quality'],'candidates':candidates,
        'training_sources':len(folds),'validation_sources':len({r['source_sha256'] for r in val})}


def choose(rows,baseline):
    pooled,pr=component(rows);widths={'kind':'exact_width_slices','slices':{}};wr={};targets={'kind':'exact_width_target_slices','slices':{}};tr={}
    for key in sorted({width_key(r) for r in rows}):
        m,r=component([x for x in rows if width_key(x)==key]);widths['slices'][key]=m;wr[key]=r
    for key in sorted({target_key(r) for r in rows}):
        m,r=component([x for x in rows if target_key(x)==key]);targets['slices'][key]=m;tr[key]=r
    val=[r for r in rows if r['split']=='validation']
    candidates=[(name,m,quality(val,m,'delay')) for name,m in [('legacy12',{'kind':'legacy12','model':baseline}),('pooled',pooled),('exact_width',widths),('exact_width_target',targets)]]
    chosen=min(candidates,key=lambda c:(c[2]['status']!='passed',c[2]['MAE'],c[2]['p95_relative_error'],len(json.dumps(c[1])),c[0]))
    return chosen[1],{'selected':chosen[0],'quality':chosen[2],'partitions':{name:q for name,_,q in candidates},'pooled':pr,'widths':wr,'width_targets':tr}


def fit(data_path,parent,out):
    parent_freeze=verify_parent(parent/'fit-freeze.json');d,a=validate(data_path)
    if parent_freeze['dataset_sha256']!=d['parent_dataset_sha256']:raise ValueError('static model not bound to eligible parent')
    out.mkdir(parents=True,exist_ok=False);c=read(parent/'candidate.json');old_report=read(parent/'fit-report.json')
    c.update(version='asap7-m2-mux-static-composite-candidate-v1',mux_feature_schema=VERSION,quality_status='awaiting_independent_test')
    report={'version':'asap7-m2-mux-static-fit-report-v1','stages':{},'independent_labels_read':False,
        'environment':{'python':sys.version,'numpy':version('numpy'),'scikit-learn':version('scikit-learn'),'seed':20261102,
            'threads':{k:os.environ.get(k) for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS')}}}
    for stage,value in c['stages'].items():
        rows=[r for r in d['rows'] if r['stage']==stage];m=value['operations']['mux'];delay,detail=choose(rows,m['delay'])
        aq=quality([r for r in rows if r['split']=='validation'],m['area'],'area');ready=detail['quality']['status']==aq['status']=='passed'
        m.update(delay=delay,static_feature_schema=VERSION,validation_ready=ready,quality_status='awaiting_independent_test' if ready else 'failed_validation')
        m['context_domain']={'version':'independent-control-forest-v1','pure_dynamic_mux_counts':[2,3,4],
            'mixed_control_operations':['mux','mux_zero','mux_one','mux_ones','eq_zero','or'],'equal_data_widths':True,
            'disjoint_inputs':True,'production_capture_banks':1,'max_semantic_launch_bits':640,'max_declared_capture_bits':2048,
            'limitation':'registered local characterization contexts only; no arbitrary pipeline-stage composition'}
        value['validation_ready']=ready
        report['stages'][stage]={'mux':{'delay':detail,'area':{'quality':aq,'unchanged_parent_model':True}},'mux_validation_ready':ready,
            'unchanged_qualified_operations':11 if stage=='grt' else 0,'counts':dict(Counter(r['split'] for r in rows))}
    write(out/'candidate.json',c);write(out/'fit-report.json',report)
    source_paths=[Path(__file__),CONFIG,Path(__file__).with_name('model_m2_mux_static_features.py'),Path(__file__).with_name('model_m2_mux_static_algorithms.py'),
        ROOT/'rtlzz/src/backend/arithmetic_mux_context.hpp',ROOT/'rtlzz/testv2/arithmetic_mux_static_context.cpp']+[ROOT/name for name in parent_freeze['sources']]
    sources={}
    for path in source_paths:
        name=str(path.relative_to(ROOT));dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(path,dst);sources[name]=sha(path)
    f={'version':'asap7-m2-mux-static-fit-freeze-v1','dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),
        'parent_fit_path':str((parent/'fit-freeze.json').resolve()),'parent_fit_sha256':sha(parent/'fit-freeze.json'),'protocol_sha256':sha(CONFIG),
        'collection_admission_path':d['admission_path'],'collection_admission_sha256':d['admission_sha256'],
        'inherited11_path':d['inherited11_path'],'inherited11_sha256':d['inherited11_sha256'],'sources':sources,
        'candidate_sha256':sha(out/'candidate.json'),'fit_report_sha256':sha(out/'fit-report.json'),'grt_validation_ready':c['stages']['grt']['validation_ready'],'test_consumed':False}
    write(out/'fit-freeze.json',f)
    if f['grt_validation_ready']:write(out/'selection-freeze.json',{**f,'version':'asap7-m2-mux-static-selection-v1'})
    print(json.dumps({'stages':{s:{'mux_validation_ready':v['mux_validation_ready'],'delay':v['mux']['delay']['quality'],'area':v['mux']['area']['quality']} for s,v in report['stages'].items()},
        'independent_test_eligible':f['grt_validation_ready'],'unchanged_qualified_operations':11}),flush=True)


def verify_fit(path):
    f=read(path);folder=Path(path).parent
    if f['version'] not in ('asap7-m2-mux-static-fit-freeze-v1','asap7-m2-mux-static-selection-v1') or f['test_consumed'] is not False:raise ValueError('wrong Mux static fit freeze')
    verify_parent(Path(f['parent_fit_path']))
    if sha(CONFIG)!=f['protocol_sha256'] or sha(f['dataset_path'])!=f['dataset_sha256'] or sha(f['parent_fit_path'])!=f['parent_fit_sha256']:
        raise ValueError('changed static fitting inputs')
    for name,h in f['sources'].items():
        if sha(ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed static fitter/ABI source')
    for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
        if sha(folder/name)!=f[key]:raise ValueError('changed static predictor/report')
    d,a=validate(Path(f['dataset_path']));c=read(folder/'candidate.json');r=read(folder/'fit-report.json');parent=read(Path(f['parent_fit_path']).parent/'candidate.json')
    for op,value in parent['stages']['grt']['operations'].items():
        if op!='mux' and c['stages']['grt']['operations'][op]!=value:raise ValueError('static successor changed inherited11')
    for stage,value in c['stages'].items():
        model=value['operations']['mux'];val=[v for v in d['rows'] if v['stage']==stage and v['split']=='validation']
        if model['area']!=parent['stages'][stage]['operations']['mux']['area'] or model['joint_domain']!=parent['stages'][stage]['operations']['mux']['joint_domain']:
            raise ValueError('static successor changed Mux area or width/target domain')
        for q in ('delay','area'):
            if quality(val,model[q],q)!=r['stages'][stage]['mux'][q]['quality']:raise ValueError('static validation does not recompute')
        ready=all(r['stages'][stage]['mux'][q]['quality']['status']=='passed' for q in ('delay','area'))
        if ready!=model['validation_ready'] or ready!=value['validation_ready']:raise ValueError('wrong static validation status')
    if f['grt_validation_ready']!=c['stages']['grt']['validation_ready'] or Path(path).name=='selection-freeze.json' and not f['grt_validation_ready']:raise ValueError('unready static choice')
    return f


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['extract','fit','reproduce','verify'])
    for name in ('data','out','parent','selection','native'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='extract':extract(a.data.resolve(),a.out.resolve(),a.native.resolve() if a.native else None)
    elif a.action=='fit':fit(a.data.resolve(),a.parent.resolve(),a.out.resolve())
    elif a.action=='verify':print(json.dumps({'status':'verified','ready':verify_fit(a.selection)['grt_validation_ready']}))
    else:
        f=verify_fit(a.selection);fit(Path(f['dataset_path']),Path(f['parent_fit_path']).parent,a.out.resolve())
        for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
            if sha(a.out/name)!=f[key]:raise ValueError('static-context refit differs')
        write(a.out/'reproduction.json',{'status':'passed','parent_fit_sha256':sha(a.selection),'independent_labels_read':False})


if __name__=='__main__':main()
