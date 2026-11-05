"""Train/validation-only context crossfit for conservative primitive delays."""
import argparse
import copy
import json
from pathlib import Path
import shutil

from . import model_m2_fit as base
from . import model_m2_fit_v2 as parent
from .model_collection import sha,write
from .model_features import infer
from .model_training import algorithms

CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_fit_v3.json'


def read(path):return json.loads(Path(path).read_text())


def predict(model,row,quantity):
    entry=model['slices'][parent.key(row)] if model['kind']=='exact_width_slices' else model
    raw=infer(entry['predictor'],row['features'])
    return raw*entry.get('delay_scale',1.)+entry.get('delay_margin_ps',0.) if quantity=='delay' else raw


def quality(rows,model,quantity):
    adjusted=[{**r,'features':{**r['features'],'lhs_width':predict(model,r,quantity)}} for r in rows]
    identity={'kind':'linear','features':['lhs_width'],'coefficients':[1.],'intercept':0.}
    return base.quality(adjusted,identity,'delay_ps' if quantity=='delay' else 'comb_area_um2')


def calibrate(rows):
    train=[r for r in rows if r['split']=='train'];validation=[r for r in rows if r['split']=='validation']
    if not train or not validation or any(r['split'] not in ('train','validation') for r in rows):raise ValueError('calibration accepts train/validation only')
    groups=sorted({r['spec']['fanout'] for r in train})
    if groups!=[1,3] or {r['spec']['fanout'] for r in validation}!={2}:raise ValueError('unregistered crossfit contexts')
    fitted=dict(algorithms(train,'delay_ps',1.5));folds={}
    for held in groups:
        fitting=[r for r in train if r['spec']['fanout']!=held]
        folds[held]=dict(algorithms(fitting,'delay_ps',1.5))
    reports=[];models={}
    for name,predictor in fitted.items():
        vr=max([1.]+[r['delay_ps']/max(1.5,infer(predictor,r['features'])) for r in validation])
        cr=max([1.]+[r['delay_ps']/max(1.5,infer(folds[r['spec']['fanout']][name],r['features'])) for r in train])
        model={'kind':'pooled','predictor':predictor,'delay_scale':max(vr,cr)*1.05,'delay_margin_ps':1.5,'algorithm':name}
        q=quality(validation,model,'delay');models[name]=model
        reports.append({'algorithm':name,'quality':q,'validation_ratio':vr,'training_context_crossfit_ratio':cr,
            'delay_scale':model['delay_scale'],'delay_margin_ps':1.5,'crossfit_rows':len(train),'validation_rows':len(validation)})
    chosen=min(reports,key=lambda r:(r['quality']['status']!='passed',r['quality']['MAE'],r['quality']['p95_relative_error'],len(json.dumps(models[r['algorithm']])),r['algorithm']))
    return models[chosen['algorithm']],{'selected':chosen['algorithm'],'quality':chosen['quality'],'candidates':reports}


def choose(rows):
    pooled,pooled_report=calibrate(rows);sliced={'kind':'exact_width_slices','slices':{}};details={}
    for key in sorted({parent.key(r) for r in rows}):
        group=[r for r in rows if parent.key(r)==key];model,detail=calibrate(group)
        sliced['slices'][key]={k:v for k,v in model.items() if k!='kind'};details[key]=detail
    val=[r for r in rows if r['split']=='validation']
    candidates=[('pooled',pooled,quality(val,pooled,'delay')),('exact_width_slices',sliced,quality(val,sliced,'delay'))]
    chosen=min(candidates,key=lambda c:(c[2]['status']!='passed',c[2]['MAE'],c[2]['p95_relative_error'],len(json.dumps(c[1])),c[0]))
    return chosen[1],{'selected':chosen[0],'quality':chosen[2],'partitions':{name:q for name,_,q in candidates},'pooled':pooled_report,'slices':details}


def fit(data_path,prior,out):
    frozen=parent.verify_fit(prior/'selection-freeze.json')
    if sha(data_path)!=frozen['dataset_sha256']:raise ValueError('calibration successor changed fitting data')
    data,plan=base.validate_data(data_path)
    out.mkdir(parents=True,exist_ok=False);candidate=read(prior/'candidate.json');old=read(prior/'fit-report.json')
    candidate.update(version='asap7-m2-primitives-candidate-v3',quality_status='awaiting_independent_test',parent_candidate_sha256=sha(prior/'candidate.json'))
    report={'version':'asap7-m2-primitives-fit-report-v3','environment':old['environment'],'stages':{},'old_test_labels_read':False}
    for stage,stage_model in candidate['stages'].items():
        details={}
        for op,model in stage_model['operations'].items():
            rows=[r for r in data['rows'] if r['stage']==stage and r['operation']==op]
            delay,detail=choose(rows);area=copy.deepcopy(model['area']);val=[r for r in rows if r['split']=='validation']
            aq=quality(val,area,'area');ready=detail['quality']['status']==aq['status']=='passed'
            model.update(delay=delay,area=area,validation_ready=ready,quality_status='awaiting_independent_test' if ready else 'failed_validation')
            details[op]={'delay':detail,'area':{'quality':aq,'inherited_pretest_area_sha256':sha(prior/'candidate.json')},'validation_ready':ready}
        ready=all(m['validation_ready'] for m in stage_model['operations'].values());stage_model['validation_ready']=ready
        report['stages'][stage]={'operations':details,'validation_ready':ready,'passing_operations':sum(m['validation_ready'] for m in stage_model['operations'].values()),'operation_count':len(details)}
    write(out/'candidate.json',candidate);write(out/'fit-report.json',report)
    sources={**frozen['sources'],str(Path(__file__).relative_to(base.ROOT)):sha(__file__),str(CONFIG.relative_to(base.ROOT)):sha(CONFIG)}
    for name in sources:
        dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base.ROOT/name,dst)
    f={'version':'asap7-m2-primitives-fit-freeze-v3','dataset_path':str(data_path.resolve()),'dataset_sha256':sha(data_path),
       'parent_fit_path':str((prior/'selection-freeze.json').resolve()),'parent_fit_sha256':sha(prior/'selection-freeze.json'),
       'plan_path':frozen['plan_path'],'plan_sha256':frozen['plan_sha256'],'sources':sources,'protocol_sha256':sha(CONFIG),
       'candidate_sha256':sha(out/'candidate.json'),'fit_report_sha256':sha(out/'fit-report.json'),'test_consumed':False,
       'excluded_test_source_sha256':sorted({t['rtl_sha256'] for t in plan['tasks'] if t['split']=='test'}),
       'grt_validation_ready':candidate['stages']['grt']['validation_ready']}
    write(out/'fit-freeze.json',f)
    if f['grt_validation_ready']:write(out/'selection-freeze.json',{**f,'version':'asap7-m2-primitives-selection-v3'})
    print(json.dumps({'stages':{s:{k:v for k,v in r.items() if k!='operations'} for s,r in report['stages'].items()},'independent_test_eligible':f['grt_validation_ready']}),flush=True)


def verify_fit(path):
    f=read(path);folder=Path(path).parent
    if f['version'] not in ('asap7-m2-primitives-fit-freeze-v3','asap7-m2-primitives-selection-v3') or f['test_consumed'] is not False:
        raise ValueError('wrong context calibration freeze')
    parent.verify_fit(Path(f['parent_fit_path']))
    if sha(CONFIG)!=f['protocol_sha256'] or sha(f['dataset_path'])!=f['dataset_sha256'] or sha(f['parent_fit_path'])!=f['parent_fit_sha256']:
        raise ValueError('changed context calibration inputs')
    for name,h in f['sources'].items():
        if sha(base.ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed calibration source')
    for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
        if sha(folder/name)!=f[key]:raise ValueError('changed calibrated model/report')
    data,_=base.validate_data(Path(f['dataset_path']));candidate=read(folder/'candidate.json');r=read(folder/'fit-report.json')
    for stage,value in candidate['stages'].items():
        for op,model in value['operations'].items():
            rows=[v for v in data['rows'] if v['stage']==stage and v['operation']==op and v['split']=='validation']
            for q in ('delay','area'):
                if quality(rows,model[q],q)!=r['stages'][stage]['operations'][op][q]['quality']:raise ValueError('calibrated validation does not recompute')
    ready=all(m['validation_ready'] for m in candidate['stages']['grt']['operations'].values())
    if ready!=f['grt_validation_ready'] or Path(path).name=='selection-freeze.json' and not ready:raise ValueError('wrong calibration release decision')
    return f


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['fit','reproduce','verify'])
    for name in ('data','prior','out','selection'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='fit':fit(a.data.resolve(),a.prior.resolve(),a.out.resolve())
    elif a.action=='verify':print(json.dumps({'status':'verified','ready':verify_fit(a.selection)['grt_validation_ready']}))
    else:
        f=verify_fit(a.selection);fit(Path(f['dataset_path']),Path(f['parent_fit_path']).parent,a.out.resolve())
        for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
            if sha(a.out/name)!=f[key]:raise ValueError('calibrated refit differs')
        write(a.out/'reproduction.json',{'status':'passed','parent_fit_sha256':sha(a.selection),'test_labels_read':False})


if __name__=='__main__':main()
