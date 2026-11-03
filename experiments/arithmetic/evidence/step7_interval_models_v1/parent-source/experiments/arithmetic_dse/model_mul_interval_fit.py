"""Fit per native legal-group interval; independent test stays sealed."""
import argparse,json,math
from pathlib import Path
from .model_mul_intervals import CONFIG,key,features
from .model_collection import sha,write,verify_test_release
from .model_features import infer
from .model_training import metric


LABEL_AUDIT=Path(__file__).with_name('configs')/'model_mul_interval_labels_v1.json'

def extract(folder,splits,selection_freeze=None):
    a=json.loads((folder/'admission.json').read_text())
    if a['supplemental_protocol']['sha256']!=sha(CONFIG):raise ValueError('changed interval sampling protocol')
    if 'test' in splits:verify_test_release(folder/'admission.json',selection_freeze,{t['platform'] for t in a['tasks'] if t['split']=='test'})
    rows=[];failures=[]
    for t in a['tasks']:
        if t['split'] not in splits:continue
        d=folder/'runs'/t['id'];path=d/'manifest.json'
        if not path.is_file():failures.append({'task':t['id'],'status':'not_run'});continue
        m=json.loads(path.read_text())
        if m['status']!='completed':failures.append({'task':t['id'],'status':m['status'],'reason':m.get('failure_reason')});continue
        if sha(d/'input.sv')!=t['rtl_sha256'] or sha(d/'sample-contract.json')!=t['sample_contract_sha256']:raise ValueError('changed interval sample')
        contract=json.loads((d/'sample-contract.json').read_text());specs={s['id']:s for s in contract['labels']};cells=json.loads((d/'liberty_cells.json').read_text())['cells']
        for stage in m['metrics']:
            instances=d/f'reports/{t["platform"]}/arithmetic_probe/base/vulsim_{stage["stage"]}_instances.tsv'
            if sha(instances)!=m['evidence_sha256'][str(instances.relative_to(d))]:raise ValueError('changed interval instance labels')
            actual=[line.split('\t')[:2] for line in instances.read_text().splitlines()]
            for label in stage['model_labels']:
                s=specs[label['id']];comb=0.;capture=0;launch=0
                for name,master in actual:
                    if not name.startswith(s['instance_scope']) or master not in cells:continue
                    cell=cells[master]
                    if cell['sequential']:
                        capture+=int(name.startswith(s['instance_scope']+'dst') or name.startswith(s['instance_scope']+'y'))
                        launch+=int(name.startswith(s['instance_scope']+'src'))
                    elif name.startswith(s['arithmetic_scope']):comb+=cell['area_um2']
                if not 0<capture<=s['capture_width'] or not 0<launch<=sum(s['input_widths']):raise ValueError(f'actual packed boundary mismatch {t["id"]}/{s["id"]}: capture {capture}/{s["capture_width"]}, launch {launch}/{sum(s["input_widths"])}')
                if comb<=0:raise ValueError('interval has no positive mapped core area')
                rows.append({'id':t['id']+'/'+s['id']+'/'+stage['stage'],'platform':t['platform'],'stage':stage['stage'],'split':t['split'],'interval_key':s['interval_key'],
                    'features':s['features'],'spec':s,'delay_ps':label['data_delay_ps'],'comb_area_um2':comb,'capture_DFFs':capture,'launch_DFFs':launch,'elided_or_merged_capture_bits':s['capture_width']-capture,'elided_or_merged_launch_bits':sum(s['input_widths'])-launch,
                    'source_sha256':t['rtl_sha256'],'contract_sha256':t['sample_contract_sha256'],'manifest_sha256':sha(path),'instances_sha256':sha(instances),
                    'points_sha256':label['points_sha256'],'profile_sha256':t['profile_sha256'],'period_ps':t['period_ps'],'abc_target_ps':t['abc_target_ps']})
    return {'version':'arithmetic-mul-interval-dataset-v1','protocol_sha256':sha(CONFIG),'admission_sha256':sha(folder/'admission.json'),'rows':rows,'failures':failures,
            'no_formal_or_holdout_data':True,'label_audit_sha256':sha(LABEL_AUDIT),'label_limitation':'static unknown-bit capacities are pre-mapping features; actual mapped boundary counts recorded separately; no mapped LEC claim'}


def predictors(train,label,floor):
    import numpy as np
    from sklearn.linear_model import LinearRegression,Ridge
    from sklearn.tree import DecisionTreeRegressor
    y=np.array([r[label] for r in train]);weights=1/np.maximum(np.abs(y),floor)**2;result=[]
    result.append(('constant',{'kind':'linear','features':[],'intercept':float(y.mean()),'coefficients':[]}))
    for name,names in [('linear-width',['width']),('quadratic-width',['width','width_squared'])]:
        x=np.array([[r['features'][k] for k in names] for r in train]);fit=LinearRegression().fit(x,y,sample_weight=weights)
        result.append((name,{'kind':'linear','features':names,'intercept':float(fit.intercept_),'coefficients':list(map(float,fit.coef_))}))
    names=['width','width_squared','log_width','capture_bits','input_bits'];x=np.array([[r['features'][k] for k in names] for r in train]);mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale==0]=1
    for alpha in (1e-6,1e-4,1e-2):
        fit=Ridge(alpha=alpha).fit((x-mean)/scale,y,sample_weight=weights*len(y)/sum(weights));coef=fit.coef_/scale
        result.append((f'ridge-relative-{alpha}',{'kind':'linear','features':names,'intercept':float(fit.intercept_-np.dot(coef,mean)),'coefficients':list(map(float,coef))}))
    fit=DecisionTreeRegressor(max_depth=2,min_samples_leaf=1,random_state=20261103).fit(x,y);tree=fit.tree_;nodes=[]
    for i in range(tree.node_count):nodes.append({'value':float(tree.value[i][0][0])} if tree.children_left[i]<0 else {'feature':int(tree.feature[i]),'threshold':float(tree.threshold[i]),'left':int(tree.children_left[i]),'right':int(tree.children_right[i])})
    result.append(('tree-depth-2',{'kind':'tree','features':names,'nodes':nodes}));return result


def quality(model,rows,ref):
    cfg=json.loads(CONFIG.read_text());g=cfg['quality_gates'];pred=[(infer(model['delay'],r['features'])*model['validation_delay_scale'],infer(model['area'],r['features'])) for r in rows]
    delay=metric([r['delay_ps'] for r in rows],[p[0] for p in pred],max(1,ref*.001));area=metric([r['comb_area_um2'] for r in rows],[p[1] for p in pred],1e-4)
    false=sum(p[0]<=r['delay_ps']*ratio<r['delay_ps'] for r,p in zip(rows,pred) for ratio in cfg['feasibility_ratios']);den=len(rows)*len(cfg['feasibility_ratios'])
    passed=all(m[k+'_relative_error']<=g[label+'_'+k+'_relative_error_max'] for m,label in [(delay,'delay'),(area,'area')] for k in ('median','p95')) and false/den<=g['false_feasible_fraction_max']
    return {'status':'passed' if passed else 'failed','delay':delay,'area':area,'false_feasible':false,'denominator':den}


def fit(data,base,out):
    d=json.loads(data.read_text());rows=d['rows'];out.mkdir(parents=True,exist_ok=False);cfg=json.loads(CONFIG.read_text());index=[]
    if d['failures'] or any(r['split']=='test' for r in rows):raise ValueError('complete fitting partitions only, no test labels')
    for platform in sorted({r['platform'] for r in rows}):
        source=base/(platform+'.json');bundle=json.loads(source.read_text());ref=bundle['mapping_abc_target_ps'];reports={}
        for stage in ('synth','grt'):
            entries={};detail={}
            for group in sorted({r['interval_key'] for r in rows if r['platform']==platform and r['stage']==stage}):
                subset=[r for r in rows if r['platform']==platform and r['stage']==stage and r['interval_key']==group];train=[r for r in subset if r['split']=='train'];val=[r for r in subset if r['split']=='validation']
                if {r['features']['width'] for r in train}!=set(cfg['splits']['train']) or {r['features']['width'] for r in val}!=set(cfg['splits']['validation']):raise ValueError('incomplete declared widths per interval')
                entry={};choices={}
                for field,name,floor in [('delay_ps','delay',max(1,ref*.001)),('comb_area_um2','area',1e-4)]:
                    candidates=[]
                    for algorithm,predictor in predictors(train,field,floor):
                        metrics=metric([r[field] for r in val],[infer(predictor,r['features']) for r in val],floor)
                        violation=max(metrics['median_relative_error']/cfg['quality_gates'][name+'_median_relative_error_max'],metrics['p95_relative_error']/cfg['quality_gates'][name+'_p95_relative_error_max'])
                        score=(violation>1,violation if violation>1 else 0,metrics['MAE']/max(floor,sum(r[field] for r in val)/len(val)),len(json.dumps(predictor)))
                        candidates.append((score,algorithm,predictor,metrics))
                    chosen=min(candidates,key=lambda c:c[0]);entry[name]=chosen[2];choices[name]={'algorithm':chosen[1],'validation_before_margin':chosen[3],'candidates':[{'algorithm':c[1],'metrics':c[3]} for c in candidates]}
                entry['validation_delay_scale']=max([1.]+[r['delay_ps']/max(1e-9,infer(entry['delay'],r['features'])) for r in val])*1.05
                entry['quality_status']='awaiting_independent_test';q=quality(entry,val,ref);entry['validation_ready']=q['status']=='passed';entries[group]=entry;detail[group]={'selection':choices,'quality_after_margin':q}
            model={'version':cfg['model_schema'],'quality_status':'awaiting_independent_test','min_width':8,'max_width':32,'abc_target_ps':ref,'sdc_period_ps':ref,'max_operations':64,'max_result_bits':4096,'intervals':entries,'domain':'exact registered full/low half/quarter contiguous reduction groups; equal inputs divisible by four; no extra paid stage operation'}
            # The released base contains grt only. Synth interval quality is
            # evaluated separately and never authorizes a missing base model.
            reports[stage]={'intervals':detail,'model':model,'base_stage_available':stage in bundle['stages']}
            if stage in bundle['stages']:bundle['stages'][stage]['mul_interval_model']=model
        bundle['quality_status']='awaiting_independent_test';bundle['id']=platform+'-native-mul-interval-v1';bundle['interval_fit_dataset_sha256']=sha(data);bundle['interval_fit_protocol_sha256']=sha(CONFIG)
        write(out/(platform+'.candidate.json'),bundle);write(out/(platform+'.fit.json'),reports);index.append({'platform':platform,'candidate_sha256':sha(out/(platform+'.candidate.json'))})
    write(out/'selection-freeze.json',{'version':'arithmetic-mul-interval-selection-freeze-v1','dataset_sha256':sha(data),'fitting_dataset_path':str(data.resolve()),'protocol_sha256':sha(CONFIG),'admission_sha256':d['admission_sha256'],'models':index,'test_consumed':False})


def main():
    p=argparse.ArgumentParser();p.add_argument('action',choices=['extract','fit']);p.add_argument('--data',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--base',type=Path);p.add_argument('--splits',nargs='+',default=['train','validation']);p.add_argument('--selection-freeze',type=Path);a=p.parse_args()
    if a.action=='extract':write(a.out,extract(a.data,a.splits,a.selection_freeze))
    else:fit(a.data,a.base,a.out)
if __name__=='__main__':main()
