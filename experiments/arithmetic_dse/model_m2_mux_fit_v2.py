"""Operation-level validation selection over the registered Mux candidate pool."""
import argparse
import copy
import json
from pathlib import Path
import shutil

from . import model_m2_mux_fit as base
from .model_collection import sha,write
from .model_features import infer
from .model_m2_fit_v4 import predict,quality,target_key
from .model_training import algorithms

CONFIG=Path(__file__).with_name('configs')/'model_asap7_m2_mux_fit_selection_v2.json'


def read(path):return json.loads(Path(path).read_text())


def candidate_pool(rows):
    import numpy as np
    if any(r['split'] not in ('train','validation') for r in rows):raise ValueError('Mux candidate pool rejects independent rows')
    train=[r for r in rows if r['split']=='train'];val=[r for r in rows if r['split']=='validation']
    raw=dict(algorithms(train,'delay_ps',1.5));folds={}
    for held in sorted({r['source_sha256'] for r in train}):folds[held]=dict(algorithms([r for r in train if r['source_sha256']!=held],'delay_ps',1.5))
    pool={}
    for name,predictor in raw.items():
        margin=float(np.quantile([max(0,r['delay_ps']-infer(predictor,r['features'])) for r in val],.95))+1.5
        vr=max([1.]+[r['delay_ps']/max(1.5,infer(predictor,r['features'])) for r in val])
        cr=max([1.]+[r['delay_ps']/max(1.5,infer(folds[r['source_sha256']][name],r['features'])) for r in train])
        for reserve,scale,offset in (('validation_positive_p95',1.,margin),('complete_source_ratio',max(vr,cr)*1.05,1.5)):
            pool[name+'/'+reserve]={'kind':'pooled','predictor':predictor,'delay_scale':scale,'delay_margin_ps':offset,'algorithm':name,'calibration':reserve}
    return pool


def score(q):
    g=read(base.CONFIG)['quality_gates']
    violation=max(q['median_relative_error']/g['delay_median_relative_error_max'],q['p95_relative_error']/g['delay_p95_relative_error_max'],
        q['false_feasible']/q['denominator']/g['false_feasible_fraction_max'],q['actual_target_false_feasible']/q['actual_target_denominator']/g['false_feasible_fraction_max'])
    return (q['status']!='passed',violation if q['status']!='passed' else 0.,q['MAE'],q['p95_relative_error'])


def select(rows,start,pools):
    if any(r['split'] not in ('train','validation') for r in rows):raise ValueError('global selector rejects independent rows')
    val=[r for r in rows if r['split']=='validation'];model=copy.deepcopy(start)
    if model['kind']!='exact_width_target_slices':raise ValueError('registered starting model must enumerate width/target')
    q=quality(val,model,'delay');trace=[]
    for iteration in range(read(CONFIG)['max_replacements']):
        incumbent=score(q);best=None
        for component in sorted(pools):
            for name,entry in sorted(pools[component].items()):
                proposal=copy.deepcopy(model);proposal['slices'][component]=entry;observed=quality(val,proposal,'delay')
                ranking=score(observed)
                if ranking<incumbent and (best is None or (ranking,component,name)<(best[0],best[1],best[2])):
                    best=(ranking,component,name,proposal,observed)
        if best is None:break
        _,component,name,model,q=best
        trace.append({'iteration':iteration,'component':component,'candidate':name,'operation_quality':q})
    return model,q,trace


def fit(data_path,parent,out):
    f=base.verify_fit(parent/'fit-freeze.json');data,a=base.validate_data(data_path)
    if sha(data_path)!=f['dataset_sha256']:raise ValueError('Mux global selector changed fitting data')
    out.mkdir(parents=True,exist_ok=False);candidate=read(parent/'candidate.json');report=read(parent/'fit-report.json')
    rows=[r for r in data['rows'] if r['stage']=='grt'];pools={}
    for component in sorted({target_key(r) for r in rows}):pools[component]=candidate_pool([r for r in rows if target_key(r)==component])
    start=candidate['stages']['grt']['operations']['mux']['delay'];model,q,trace=select(rows,start,pools)
    candidate['version']='asap7-m2-mux-composite-candidate-v2';candidate['stages']['grt']['operations']['mux']['delay']=model
    ready=q['status']==report['stages']['grt']['mux']['area']['quality']['status']=='passed'
    candidate['stages']['grt']['operations']['mux'].update(validation_ready=ready,quality_status='awaiting_independent_test' if ready else 'failed_validation')
    candidate['stages']['grt']['validation_ready']=ready;report['version']='asap7-m2-mux-fit-report-v2'
    old_report=copy.deepcopy(report['stages']['grt']['mux']['delay'])
    report['stages']['grt']['mux']['delay']={'selected':'registered_candidates_global_operation_selection','quality':q,'parent_local_selection':old_report,
        'replacements':trace,'candidate_counts':{c:len(p) for c,p in pools.items()}}
    report['stages']['grt']['mux_validation_ready']=ready
    write(out/'candidate.json',candidate);write(out/'fit-report.json',report)
    sources={**f['sources'],str(Path(__file__).relative_to(base.ROOT)):sha(__file__),str(CONFIG.relative_to(base.ROOT)):sha(CONFIG)}
    for name in sources:
        dst=out/'source'/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(base.ROOT/name,dst)
    frozen={**f,'version':'asap7-m2-mux-fit-freeze-v2','parent_mux_fit_path':str((parent/'fit-freeze.json').resolve()),'parent_mux_fit_sha256':sha(parent/'fit-freeze.json'),
        'candidate_sha256':sha(out/'candidate.json'),'fit_report_sha256':sha(out/'fit-report.json'),'selector_protocol_sha256':sha(CONFIG),'sources':sources,'grt_validation_ready':ready}
    write(out/'fit-freeze.json',frozen)
    if ready:write(out/'selection-freeze.json',{**frozen,'version':'asap7-m2-mux-selection-v2'})
    print(json.dumps({'grt_mux_validation_ready':ready,'delay':q,'replacements':len(trace),'unchanged_qualified_operations':11,'independent_labels_read':False}),flush=True)


def verify_fit(path):
    f=read(path);folder=Path(path).parent
    if f['version'] not in ('asap7-m2-mux-fit-freeze-v2','asap7-m2-mux-selection-v2') or f['test_consumed'] is not False:raise ValueError('wrong global Mux selection')
    base.verify_fit(Path(f['parent_mux_fit_path']))
    if sha(f['dataset_path'])!=f['dataset_sha256'] or sha(CONFIG)!=f['selector_protocol_sha256'] or sha(f['parent_mux_fit_path'])!=f['parent_mux_fit_sha256']:
        raise ValueError('changed global Mux selector inputs')
    for name,h in f['sources'].items():
        if sha(base.ROOT/name)!=h or sha(folder/'source'/name)!=h:raise ValueError('changed global selector source')
    for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
        if sha(folder/name)!=f[key]:raise ValueError('changed global selector model/report')
    data,a=base.validate_data(Path(f['dataset_path']));c=read(folder/'candidate.json');r=read(folder/'fit-report.json');parent=read(Path(f['parent_mux_fit_path']).parent/'candidate.json')
    if c['stages']['synth']!=parent['stages']['synth']:raise ValueError('global selector modified synth')
    for op,m in c['stages']['grt']['operations'].items():
        if op!='mux' and m!=parent['stages']['grt']['operations'][op]:raise ValueError('global selector changed inherited operation')
    if any(c['stages']['grt']['operations']['mux'][key]!=parent['stages']['grt']['operations']['mux'][key] for key in ('area','joint_domain')):raise ValueError('global selector changed area/domain')
    val=[v for v in data['rows'] if v['stage']=='grt' and v['split']=='validation']
    q=quality(val,c['stages']['grt']['operations']['mux']['delay'],'delay')
    if q!=r['stages']['grt']['mux']['delay']['quality'] or f['grt_validation_ready']!=(q['status']=='passed'):
        raise ValueError('global Mux quality does not recompute')
    if Path(path).name=='selection-freeze.json' and not f['grt_validation_ready']:raise ValueError('unready global Mux choice')
    return f


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('action',choices=['fit','reproduce','verify'])
    for name in ('data','parent','out','selection'):ap.add_argument('--'+name,type=Path)
    a=ap.parse_args()
    if a.action=='fit':fit(a.data.resolve(),a.parent.resolve(),a.out.resolve())
    elif a.action=='verify':print(json.dumps({'status':'verified','ready':verify_fit(a.selection)['grt_validation_ready']}))
    else:
        f=verify_fit(a.selection);fit(Path(f['dataset_path']),Path(f['parent_mux_fit_path']).parent,a.out.resolve())
        for name,key in (('candidate.json','candidate_sha256'),('fit-report.json','fit_report_sha256')):
            if sha(a.out/name)!=f[key]:raise ValueError('global selector refit differs')
        write(a.out/'reproduction.json',{'status':'passed','parent_fit_sha256':sha(a.selection),'independent_labels_read':False})


if __name__=='__main__':main()
