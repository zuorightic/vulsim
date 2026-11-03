"""State/stage residual calibration with a separately frozen test command."""
import argparse
import json
import math
import re
from pathlib import Path
from .model_collection import sha,write
from .model_calibration import CALIBRATION
from .model_features import features,infer
from .model_training import metric
from .model_training import fit as fit_predictor

FIT_PROTOCOL=Path(__file__).with_name('configs')/'model_calibration_fit_v6.json'


def extract(out,splits=None):
    a=json.loads((out/'admission.json').read_text());rows=[]
    if a.get('not_training'):
        from .model_qualification import QUALIFICATION
        if a['supplemental_protocol']['sha256']!=sha(QUALIFICATION):raise ValueError('changed context qualification protocol')
    elif a['supplemental_protocol']['sha256']!=sha(CALIBRATION):raise ValueError('changed calibration protocol')
    for t in a['tasks']:
        if splits is not None and t['split'] not in splits:continue
        directory=out/'runs'/t['id'];m=json.loads((directory/'manifest.json').read_text())
        if m['status']!='completed':raise ValueError('calibration implementation incomplete: '+t['id'])
        contract=directory/'sample-contract.json'
        if sha(contract)!=t['sample_contract_sha256']:raise ValueError('changed calibration graph')
        if a.get('not_training') and json.loads(contract.read_text()).get('base_calibration_protocol_sha256')!=sha(CALIBRATION):raise ValueError('changed qualification source family')
        specs={r['id']:r for r in json.loads(contract.read_text())['labels']};cells=json.loads((directory/'liberty_cells.json').read_text())['cells']
        for metrics in m['metrics']:
            path=directory/f'reports/{t["platform"]}/arithmetic_probe/base/vulsim_{metrics["stage"]}_instances.tsv'
            if sha(path)!=m['evidence_sha256'][str(path.relative_to(directory))]:raise ValueError('changed calibration instances')
            instances=[line.split('\t')[:2] for line in path.read_text().splitlines()];scoped=0.;local=[]
            for label in metrics['model_labels']:
                spec=specs[label['id']];scope=spec['instance_scope'];comb=0.;state=0.;functional=0.;capture=0;launch=0;launch_banks=set()
                for name,master in instances:
                    if not name.startswith(scope) or master not in cells:continue
                    c=cells[master];functional+=c['area_um2']
                    if name.startswith(spec['arithmetic_scope']) and not c['sequential']:comb+=c['area_um2']
                    if c['sequential']:
                        state+=c['area_um2'];capture+=int(name.startswith(scope+'y') or name.startswith(scope+'dst'));launch+=int(name.startswith(scope+'src'))
                        if name.startswith(scope+'src'):
                            bank=re.match(r'src\d+',name[len(scope):])
                            if not bank:raise ValueError('unrecognized launch register bank')
                            launch_banks.add(bank[0])
                if capture!=spec['result_width']*spec['fanout']:raise ValueError('calibration capture fanout mismatch')
                if spec['role']=='state' and launch!=spec['lhs_width']:raise ValueError('state launch width mismatch')
                scoped+=functional
                if any(k not in label for k in ('slack_ps','setup_margin_ps','clock_skew_ps')):raise ValueError('missing actual boundary timing evidence')
                local.append({'id':t['id']+'/'+label['id']+'/'+metrics['stage'],'platform':t['platform'],'stage':metrics['stage'],
                    'split':t['split'],'source_group':t['source_group'],'spec':spec,'delay_ps':label['data_delay_ps'],'comb_area_um2':comb,
                    'scoped_functional_area_um2':functional,'scoped_sequential_area_um2':state,'state_bits':capture+launch,'state_signals':spec['fanout']+len(launch_banks),
                    'boundary_overhead_ps':t['period_ps']-label['data_delay_ps']-label['slack_ps'],
                    'setup_margin_ps':label['setup_margin_ps'],'clock_skew_ps':label['clock_skew_ps'],'period_ps':t['period_ps'],'abc_target_ps':t['abc_target_ps'],
                    'manifest_sha256':sha(directory/'manifest.json'),'source_sha256':t['rtl_sha256'],'profile_sha256':t['profile_sha256'],
                    'points_sha256':label['points_sha256'],'expanded_path_report_sha256':label['expanded_path_report_sha256'],'instances_sha256':sha(path)})
            # Preserve global unassigned physical/clock/port-repair overhead;
            # use one explicitly declared per-state-bit allocation, not an
            # unsupported claim that each of these cells belongs to an op.
            unassigned=max(0,metrics['cell_area_um2']-scoped)
            for row in local:row['allocated_unassigned_area_per_bit_um2']=unassigned/metrics['sequential_cells']
            rows.extend(local)
    groups={}
    for row in rows:
        key=(row['platform'],row['source_sha256'])
        if key in groups and groups[key]!=row['split']:raise ValueError('calibration source crosses splits')
        groups[key]=row['split']
    return {'version':'state-stage-calibration-dataset-v1','admission_sha256':sha(out/'admission.json'),'protocol_sha256':sha(CALIBRATION),
            'included_splits':sorted({r['split'] for r in rows}),'not_training':a.get('not_training',False),'rows':rows,
            'unassigned_area_rule':'(whole cell area minus all scoped functional area) / whole sequential cell count; includes clock/physical/boundary repair; approximate allocation'}


def base_prediction(bundle,row):
    nodes=row['spec']['graph_nodes'];arrivals=[];area=0.;stage=bundle['stages'][row['stage']]
    for i,n in enumerate(nodes):
        model=stage['operations'].get(n['operation'])
        if not model or model['quality_status']!='passed':raise ValueError('isolated operation model not ready: '+n['operation'])
        # Logical result-consumer banks are visible before mapping. All
        # interior chain/tree edges have one user in these registered graphs;
        # the last result has the declared capture bank count.
        fan=row['spec']['fanout'] if i==len(nodes)-1 else 1
        f=features(n['lhs_width'],n['rhs_width'],n['result_width'],fan,row['abc_target_ps'],row['period_ps'])
        before=max((arrivals[k] for k in n['inputs']),default=0)
        arrivals.append(before+infer(model['delay'],f)+model['delay_margin_ps']);area+=infer(model['area'],f)
    return max(arrivals,default=0),area,len(nodes),sum(n['result_width'] for n in nodes)


def calibrated_prediction(bundle,row):
    base,area,n,bits=base_prediction(bundle,row);c=bundle['stages'][row['stage']]['stage_correction']
    if n==1 and 'single_operation_models' in bundle['stages'][row['stage']]:
        node=row['spec']['graph_nodes'][0];model=bundle['stages'][row['stage']]['single_operation_models'][node['operation']]
        f=features(node['lhs_width'],node['rhs_width'],node['result_width'],row['spec']['fanout'],row['abc_target_ps'],row['period_ps'])
        return (infer(model['delay'],f)+model['delay_margin_ps'])*model['validation_delay_scale'],infer(model['area'],f)
    return (c['delay_base_scale']*base+c['intercept_ps']+c['per_operation_ps']*n+c['per_result_bit_ps']*bits,
            c['area_base_scale']*area+c['intercept_um2']+c['per_operation_um2']*n+c['per_result_bit_um2']*bits)


def quality(bundle,stage,group):
    cfg=json.loads(CALIBRATION.read_text());gates=cfg['quality_gates_before_test'];model=bundle['stages'][stage]
    contexts=[r for r in group if r['spec']['role']=='synthetic_context'];states=[r for r in group if r['spec']['role']=='state']
    if not contexts or not states:raise ValueError('separate graph and state labels required')
    predictions=[calibrated_prediction(bundle,r) for r in contexts]
    delay=metric([r['delay_ps'] for r in contexts],[p[0] for p in predictions],max(1,bundle['mapping_abc_target_ps']*.001))
    area=metric([r['comb_area_um2'] for r in contexts],[p[1] for p in predictions],1e-4)
    state=model['state_model'];actual_state=[r['scoped_functional_area_um2']+r['state_bits']*r['allocated_unassigned_area_per_bit_um2'] for r in states]
    predicted_state=[r['state_bits']*(state['bit_area_um2']+state['clock_area_per_bit_um2'])+r['state_signals']*state['signal_area_um2'] for r in states]
    state_metric=metric(actual_state,predicted_state,1e-4);false_feasible=0;decisions=0
    for r,p in zip(contexts,predictions):
        for ratio in cfg['feasibility_budgets']:
            budget=r['delay_ps']*ratio;decisions+=1;false_feasible+=int(p[0]<=budget<r['delay_ps'])
    passed=(delay['median_relative_error']<=gates['stage_delay_median_relative_error_max'] and delay['p95_relative_error']<=gates['stage_delay_p95_relative_error_max']
        and area['median_relative_error']<=gates['stage_area_median_relative_error_max'] and area['p95_relative_error']<=gates['stage_area_p95_relative_error_max']
        and state_metric['median_relative_error']<=gates['state_area_median_relative_error_max'] and state_metric['p95_relative_error']<=gates['state_area_p95_relative_error_max']
        and false_feasible/decisions<=gates['false_feasible_fraction_max'])
    return {'status':'passed' if passed else 'failed','stage_delay':delay,'stage_area':area,'state_area':state_metric,'false_feasible':false_feasible,'classification_denominator':decisions}


def fit(data,isolated,out):
    import numpy as np
    from scipy.optimize import nnls
    cfg=json.loads(CALIBRATION.read_text());dataset=json.loads(data.read_text());rows=dataset['rows'];out.mkdir(parents=True,exist_ok=False);models=[]
    if dataset.get('not_training'):raise ValueError('context qualification data cannot be used for fitting')
    if json.loads(data.read_text())['protocol_sha256']!=sha(CALIBRATION):raise ValueError('changed calibration gates')
    if cfg.get('independent_test_read_after_selection_freeze_only') and any(r['split']=='test' for r in rows):raise ValueError('deferred test labels must not appear in fitting dataset')
    for platform in sorted({r['platform'] for r in rows}):
        source=isolated/(platform+'.tested.json');bundle=json.loads(source.read_text());reports={};ready=True
        for stage,stage_model in bundle['stages'].items():
            group=[r for r in rows if r['platform']==platform and r['stage']==stage]
            if any(r['profile_sha256']!=bundle['platform_profile_sha256'] for r in group):raise ValueError('calibration/platform identity mismatch')
            train=[r for r in group if r['split']=='train'];validation=[r for r in group if r['split']=='validation'];states=[r for r in train if r['spec']['role']=='state']
            x=np.asarray([[r['state_bits'],r['state_signals']] for r in states],dtype=float);y=np.asarray([r['scoped_functional_area_um2'] for r in states]);coeff,_=nnls(x,y)
            eta=float(np.median([r['allocated_unassigned_area_per_bit_um2'] for r in train]))
            stage_model['state_model']={'bit_area_um2':float(coeff[0]),'signal_area_um2':float(coeff[1]),'clock_area_per_bit_um2':eta,
                'overhead_scope':'clock and unassigned physical/port repair allocation, not exclusively clock cells',
                'protocol_id':'sync_zero_reset_valid_enable_v1',
                'domain':{'max_bits':sum(r['state_bits'] for r in states),'max_signals':sum(r['state_signals'] for r in states),
                          'max_data_word_width':max(r['spec']['result_width'] for r in states),'min_variable_data_word_bits':min(r['spec']['result_width'] for r in states)},
                'protocol':'synchronous_zero_reset_enabled_data; nonenabled valid uses same conservative local surrogate'}
            contexts=[r for r in train if r['spec']['role']=='synthetic_context' and len(r['spec']['graph_nodes'])>1];values=[]
            try:
                single_reports={};single_models={}
                singles=[r for r in train+validation if r['spec']['role']=='synthetic_context' and len(r['spec']['graph_nodes'])==1]
                for operation in sorted({r['spec']['graph_nodes'][0]['operation'] for r in singles}):
                    group=[]
                    for r in singles:
                        node=r['spec']['graph_nodes'][0]
                        if node['operation']!=operation:continue
                        group.append({**r,'features':features(node['lhs_width'],node['rhs_width'],node['result_width'],r['spec']['fanout'],r['abc_target_ps'],r['period_ps'])})
                    floor=max(1,bundle['mapping_abc_target_ps']*.001)
                    delay,margin,dreport=fit_predictor(group,'delay_ps',floor);area,_,areport=fit_predictor(group,'comb_area_um2',1e-4)
                    if not dreport['validation_ready'] or not areport['validation_ready']:raise ValueError('single-stage validation algorithm not ready: '+operation)
                    scale=max([1.]+[r['delay_ps']/max(1e-9,infer(delay,r['features'])+margin) for r in group if r['split']=='validation'])*cfg['delay_validation_ratio_reserve']
                    single_models[operation]={'delay':delay,'delay_margin_ps':margin,'validation_delay_scale':scale,'area':area}
                    single_reports[operation]={'delay':dreport,'area':areport,'delay_validation_scale':scale}
                stage_model['single_operation_models']=single_models
                predicted=[base_prediction(bundle,r) for r in contexts]
                dmatrix=np.asarray([[delay,1,n,bits] for delay,_,n,bits in predicted],dtype=float)
                amatrix=np.asarray([[area,1,n,bits] for _,area,n,bits in predicted],dtype=float)
                dcoef,_=nnls(dmatrix,np.asarray([r['delay_ps'] for r in contexts]));acoef,_=nnls(amatrix,np.asarray([r['comb_area_um2'] for r in contexts]))
                correction={'delay_base_scale':float(dcoef[0]),'area_base_scale':float(acoef[0]),
                            'intercept_ps':float(dcoef[1]),'per_operation_ps':float(dcoef[2]),'per_result_bit_ps':float(dcoef[3]),
                            'intercept_um2':float(acoef[1]),'per_operation_um2':float(acoef[2]),'per_result_bit_um2':float(acoef[3]),
                            'max_operations':cfg.get('max_operations',7),'max_live_result_bits':cfg.get('max_live_result_bits',112),
                            'monotone_group_lower_bound':False,'composition_schema':'cardinality-specific-stage-v1',
                            'method':'nonnegative base scale/interactions; independent stage validation/test required'}
                stage_model['stage_correction']=correction
                if cfg.get('observer'):
                    correction['graph_domain']={'version':'independent-single-output-arithmetic-tree-v1',
                        'max_multiplications':4,'max_output_roots':1,
                        'multi_node_operations':['mul','add'],'single_node_operations':['mul','add','addcarry'],
                        'primary_input_policy':'independent operands; no shared arithmetic intermediate fanout',
                        'source':'registered v5 mixed contexts; numeric size bounds alone never imply arbitrary-DAG coverage'}
                v=[r for r in validation if r['spec']['role']=='synthetic_context' and len(r['spec']['graph_nodes'])>1]
                if 'delay_validation_ratio_reserve' in cfg:
                    ratio=max([1.]+[r['delay_ps']/max(1e-9,calibrated_prediction(bundle,r)[0]) for r in v])*cfg['delay_validation_ratio_reserve']
                    for key in ('delay_base_scale','intercept_ps','per_operation_ps','per_result_bit_ps'):correction[key]*=ratio
                    correction['validation_ratio_margin']=ratio
                    correction['margin_rule']='max validation actual/predicted ratio (floor1) times predeclared 1.05; no test use'
                else:
                    under=[max(0,r['delay_ps']-calibrated_prediction(bundle,r)[0]) for r in v]
                    correction['intercept_ps']+=float(np.quantile(under,.95))+max(1,bundle['mapping_abc_target_ps']*.001)
            except ValueError as error:
                ready=False;reports[stage]={'status':'isolated_model_not_ready','reason':str(error)};continue
            # This aggregate is derived from real boundary paths. uncertainty
            # already occurs inside H = T-D-slack and is never charged twice.
            observed=train+validation;h=max(0,max(r['boundary_overhead_ps'] for r in observed))
            mux=max(r['delay_ps'] for r in observed if r['spec']['role']=='state')
            reserve=cfg['clock_reserve_ps'][platform]
            stage_model['boundary_model']={'io_delay_fraction':.2,'input_overhead_ps':h+mux+reserve,'register_overhead_ps':h+mux+reserve,
                'actual_boundary_H_max_ps':h,'capture_control_path_max_ps':mux,'engineering_clock_reserve_ps':reserve,
                'definition':'H=T-QD-slack includes clkQ/setup/skew/uncertainty once; reset/enable capture path and declared reserve separate; input conservatively retains clkQ'}
            validation_report=quality(bundle,stage,validation);validation_ready=validation_report['status']=='passed';ready &= validation_ready
            stage_model['calibration_validation_ready']=validation_ready
            reports[stage]={'status':'fitted_before_test' if validation_ready else 'failed_validation','state_training_rows':len(states),'stage_training_rows':len(contexts),'stage_validation_rows':len(v),'single_operation_fitting':single_reports,'validation':validation_report}
        bundle['base_node_model_id']=bundle['id'];bundle['id']=platform+'-local-ops-state-stage-fit-v6'
        bundle['quality_status']='awaiting_calibration_test' if ready else 'failed_calibration_validation';bundle['isolated_tested_model_sha256']=sha(source);bundle['calibration_dataset_sha256']=sha(data);bundle['calibration_protocol_sha256']=sha(CALIBRATION);bundle['calibration_fit_protocol_sha256']=sha(FIT_PROTOCOL)
        bundle['support_status']='local stage/state calibration pending independent test; no full five-width/Div/FP readiness';write(out/(platform+'.candidate.json'),bundle);write(out/(platform+'.calibration-fit.json'),reports)
        models.append({'platform':platform,'candidate_sha256':sha(out/(platform+'.candidate.json'))})
    write(out/'calibration-selection-freeze.json',{'version':'state-stage-selection-freeze-v1','models':models,'dataset_sha256':sha(data),
        'admission_sha256':dataset['admission_sha256'],'fitting_source_sha256':sorted({r['source_sha256'] for r in rows}),
        'protocol_sha256':sha(CALIBRATION),'fit_protocol_sha256':sha(FIT_PROTOCOL),'test_observed':False})


def test(data,out):
    result=out/'calibration-independent-test.json'
    if result.exists():raise ValueError('independent calibration test already evaluated')
    cfg=json.loads(CALIBRATION.read_text());gates=cfg['quality_gates_before_test'];frozen=json.loads((out/'calibration-selection-freeze.json').read_text());dataset=json.loads(data.read_text());rows=dataset['rows'];reports=[]
    if frozen['protocol_sha256']!=sha(CALIBRATION) or dataset['protocol_sha256']!=sha(CALIBRATION):raise ValueError('changed calibration gates after fit')
    if frozen.get('fit_protocol_sha256')!=sha(FIT_PROTOCOL):raise ValueError('changed numerical calibration protocol after fit')
    if cfg.get('independent_test_read_after_selection_freeze_only'):
        if (dataset.get('fitting_dataset_sha256')!=frozen['dataset_sha256'] or dataset['admission_sha256']!=frozen['admission_sha256']
                or any(r['split']!='test' for r in rows) or set(frozen['fitting_source_sha256']) & {r['source_sha256'] for r in rows}):
            raise ValueError('deferred calibration test identity/split mismatch')
    elif frozen['dataset_sha256']!=sha(data):raise ValueError('changed calibration data after fit')
    for item in frozen['models']:
        path=out/(item['platform']+'.candidate.json')
        if sha(path)!=item['candidate_sha256']:raise ValueError('changed model after validation freeze')
        bundle=json.loads(path.read_text());passed=True;stage_reports={}
        for stage,model in bundle['stages'].items():
            if not model.get('calibration_validation_ready',False):
                stage_reports[stage]={'status':'not_evaluated','reason':'validation not ready; test labels not consumed'};passed=False;continue
            group=[r for r in rows if r['platform']==item['platform'] and r['stage']==stage and r['split']=='test'];stage_reports[stage]=quality(bundle,stage,group);passed &= stage_reports[stage]['status']=='passed'
        bundle['quality_status']='passed' if passed else 'failed';bundle['support_status']='local isolated operations and bounded stage/state surrogate; width/shape/target conditions and per-operation quality still apply; Div/FP/wide/full matrix not ready'
        write(out/(item['platform']+'.json'),bundle);reports.append({'platform':item['platform'],'status':bundle['quality_status'],'stages':stage_reports})
    write(result,{'version':'state-stage-independent-test-v1','selection_freeze_sha256':sha(out/'calibration-selection-freeze.json'),
        'test_dataset_sha256':sha(data),'reports':reports,'no_test_tuning':True})


def main():
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['extract','fit','test']);ap.add_argument('--data',type=Path,required=True);ap.add_argument('--isolated',type=Path);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--splits',nargs='+',choices=['train','validation','test']);ap.add_argument('--fitting-data',type=Path);args=ap.parse_args()
    if args.action=='extract':
        dataset=extract(args.data,args.splits)
        if args.fitting_data:dataset['fitting_dataset_sha256']=sha(args.fitting_data)
        write(args.out,dataset)
    elif args.action=='fit':fit(args.data,args.isolated,args.out)
    else:test(args.data,args.out)


if __name__=='__main__':main()
