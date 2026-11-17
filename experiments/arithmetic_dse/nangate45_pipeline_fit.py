"""Train-only shared S/area/boundary fitting and separately frozen evaluation."""
from collections import defaultdict,Counter
from copy import deepcopy
import math
from pathlib import Path
from statistics import median

from .nangate45_samples import ROOT,read,write,sha
from . import nangate45_pipeline_samples as samples
from . import nangate45_pipeline as pipeline
from . import nangate45_artifacts as arithmetic
from . import workload_diagnostic as diagnostic
from . import centered_response as response
from .workload_demand import Graph
from .workload_abcd import static_node

AREA_FEATURES=['data_bits','data_signals','valid_bits','enable_domains','reset_one_bits']
SHARED_FEATURES={
    'shared_clock':['one','total_FF_bits','sqrt_FF_bits','predicted_functional_area_um2','clock_pressure'],
    'shared_physical':['one','predicted_functional_area_um2'],
    'root_repair':['one','input_data_bits','total_FF_bits','clock_pressure']}


def nnls(rows,names,label):
    import numpy as np
    from scipy.optimize import nnls as fit
    groups=Counter(r['source'] for r in rows)
    w=np.array([1/math.sqrt(groups[r['source']]) for r in rows])
    x=np.array([[r['f'][n] for n in names] for r in rows]);y=np.array([r['y'][label] for r in rows])
    c,_=fit(x*w[:,None],y*w)
    return dict(kind='nonnegative_linear',features=names,coefficients=c.tolist(),training_sources=len(groups),training_rows=len(rows))


def apply(model,f):return sum(c*f[n] for n,c in zip(model['features'],model['coefficients'],strict=True))


def metadata(source,target):
    folder=Path(source['folder']);g=Graph(read(folder/'graph.json'));v=read(folder/'view.json');s=read(folder/'state.json')
    o=pipeline.rebind(read(folder/'owners.json'));o['target_ps']=target;s['features']['sdc_period_ps']=target
    for r in o['operators']:r['query']['flow_context'].update(target_period_ps=target,abc_target_ps=target)
    for r in o['G_regions']:r['query']['target_ps']=target
    return g,v,s,o


def source_median(rows,key):
    groups=defaultdict(list)
    for r in rows:groups[r['source']].append(r[key])
    if not groups:raise ValueError('missing training evidence: '+key)
    return median(median(v) for v in groups.values())


def characterize():
    roots=[ROOT.parent/'vulsim-artifacts/nangate45-n34-20261117-v9',ROOT.parent/'vulsim-artifacts/nangate45-refit-20261117-v4']
    groups=defaultdict(list);audit=[]
    for root in roots:
        a=read(root/'admission.json')
        for t in a['tasks']:
            if t['role']!='train':continue
            label=root/'runs'/t['id']/'grt-labels.json'
            if not label.exists():continue
            d=read(label);paths=d['path_decompositions']
            if len(paths)!=1:
                audit.append(dict(path=str(label),sha256=sha(label),status='excluded_multiple_paths_with_aggregate_slack'));continue
            p=paths[0]
            if not p['increments_owned_exactly_once'] or d['source_role']!='train' or d['stage']!='grt' or d['target_platform']!='nangate45':raise ValueError('N56 characterization ownership/role')
            m=read(label.parent/'manifest.json');synth=read(label.parent/'synth.command.json')
            abc=[float(v.split('=',1)[1]) for v in synth['command'] if v.startswith('ABC_CLOCK_PERIOD_IN_PS=')]
            check=d['stored_SDC_check'];actual=check['actual_clock_periods_native']['core_clk']*check['time_to_ps']
            if abc!=[float(t['period_ps'])] or abs(actual-t['period_ps'])>.001 or m['abc_target_ps']!=t['period_ps']:raise ValueError('N56 actual characterization ABC/SDC')
            body=sum(p['node_delay_ps'].values());h=t['period_ps']-d['data_setup_slack_ps']-body
            if not math.isfinite(h) or h<0:raise ValueError('invalid same-path H_char')
            row=dict(source=t['source'],family=t['family'],target_ps=t['period_ps'],H_char_ps=h,path_body_ps=body,
                other_owners=[x for x in p['node_order'] if x!='producer'],path=str(label),sha256=sha(label),status='eligible',same_path=True)
            audit.append(row);groups[t['family']].append(row)
    families={k:dict(alpha=1.,H_char_ps=source_median(v,'H_char_ps'),sources=len({r['source'] for r in v}),rows=len(v),
        row_range_ps=[min(r['H_char_ps'] for r in v),max(r['H_char_ps'] for r in v)]) for k,v in groups.items()}
    if set(families)!={'Mul','Add','G'}:raise ValueError('missing needed characterization family')
    return dict(version='characterization-body-window-diagnostic-v1',profile_sha256=samples.read(samples.MODEL)['profile_sha256'],
        families=families,formula='min_p(alpha_p*T-H_char,p-D_other,char,p)',
        derivation='Nangate45 T minus same-path slack minus sum of all same-path arithmetic owners; train only',
        summary_rule='median per complete source, then median across sources; one shared H per family',
        audit=audit,operator_response_refitted=False,application_PPA_used=False,validation_labels_read=False,independent_labels_read=False,
        whole_design_boundary_separate=True,virtual_register_area_added=False,qualified=False,
        consumers='all actual immediate consumer endpoints retained; subtract each response at numerical tau, take minimum',
        limitations='family-fixed H approximation; multiple aggregate-slack paths excluded from fitting; no source lookup')


def legal_cover(pins,profile_sha):
    mapping=dict(and2='AND2_X1',and3='AND3_X1',and4='AND4_X1',or2='OR2_X1',or3='OR3_X1',or4='OR4_X1',
        nand2='NAND2_X1',nand3='NAND3_X1',nor2='NOR2_X1',nor3='NOR3_X1',xor2='XOR2_X1',not_='INV_X1',
        ao21='AOI21_X1',oa21='OAI21_X1',aoi21='AOI21_X1',oai21='OAI21_X1')
    area={};evidence={}
    for n,m in mapping.items():
        name='not' if n=='not_' else n
        if m not in pins:raise ValueError('missing legal Nangate45 primitive '+m)
        area[name]=pins[m]['area_um2'];evidence[name]=[m]
    # Nangate45 has no AND5/OR5 or positive AO21/OA21: explicit legal covers.
    for k,masters in [('and5',['AND4_X1','AND2_X1']),('or5',['OR4_X1','OR2_X1']),
        ('ao21',['AOI21_X1','INV_X1']),('oa21',['OAI21_X1','INV_X1'])]:
        area[k]=sum(pins[n]['area_um2'] for n in masters);evidence[k]=masters
    return dict(profile_sha256=profile_sha,area_um2=area,legal_masters=evidence,source='actual Nangate45 Liberty; composed covers explicit')


def freeze(root):
    root=Path(root);a=samples.verify(root);out=root/'package'
    if out.exists():raise ValueError('preserve frozen N56 model')
    completed=read(root/'progress.json')['completed']
    if any(t['id'] not in completed for t in a['tasks'] if t['role']=='train'):raise ValueError('all train points required')
    if any((root/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train'):raise ValueError('freeze before validation/test physical labels')
    train=[];state_rows=defaultdict(list);controls=[];boundaries=[];wires=[];bridge=[]
    functions=arithmetic.load(samples.MODEL)
    for t in a['tasks']:
        if t['role']!='train':continue
        source=next(s for s in a['sources'] if s['id']==t['source']);d=read(root/'runs'/t['id']/'pipeline-labels.json')
        g,v,s,o=metadata(source,t['period_ps']);p=diagnostic.state_projection(g,s,source['L'],t['period_ps']);nodeprices={}
        for r in o['operators']:nodeprices['node_'+str(r['node'])]=functions.operator_price(r['query'])
        for r in o['G_regions']:nodeprices['node_'+str(r['root'])]=functions.reduction_price(r['query'])
        for owner,f in p['owners'].items():state_rows[owner].append(dict(source=source['source_group'],f=f,y=dict(area=d['owner_area_um2'].get(owner,0))))
        train.append(dict(task=t,source=source,labels=d,projection=p,nodeprices=nodeprices))
        for path in d['functional_paths']:
            kind=path['path_class'];stage=path['stage'];body=sum(path['node_delay_ps'].values())
            if kind in ('native_enable','native_valid','input_valid','external_valid'):
                f=diagnostic.control_query(p,kind,stage)
                actual=(.8 if kind=='input_valid' else 1.)*t['period_ps']-path['slack_ps']
                controls.append(dict(source=source['source_group'],fold=source['source_group'],role='train',path_class=kind,f=f,actual=actual))
            if kind in ('native_data','external_data'):
                role='native_state->external_state' if kind=='external_data' else 'input_service->native_state' if stage==0 else 'native_state->native_state'
                iw=[x['delay_ps'] for x in path['segments'] if x['kind']=='inter_owner_wire' and set(x['owner'].split('->'))<=set(d['nodes'])]
                h=t['period_ps']-path['slack_ps']-body-sum(iw)
                boundaries.append(dict(source=source['source_group'],role=role,value=h))
                wires.extend(dict(source=source['source_group'],value=x) for x in iw)
        for n,label in d['nodes'].items():
            node=int(n.split('_')[1]);region=next((r for r in o['G_regions'] if r['root']==node),None)
            members=region['members'] if region else [node]
            w=sum(static_node(g,g.nodes[i]) for i in members)
            if w>0:bridge.append(dict(source=source['source_group'],weight=w,delay=label['operator_delay_ps'],area=label['comb_area_um2']))
        Graph.origins.cache_clear();Graph.roots.cache_clear()
    areas={k:nnls(v,AREA_FEATURES,'area') for k,v in state_rows.items()}
    sf=[]
    for r in train:
        p=r['projection'];base=sum(apply(areas[k],f) for k,f in p['owners'].items())+sum(v['area_um2'] for v in r['nodeprices'].values())
        f=dict(one=1.,total_FF_bits=p['total_FF_bits'],sqrt_FF_bits=math.sqrt(p['total_FF_bits']),predicted_functional_area_um2=base,
            input_data_bits=p['owners']['input_service']['data_bits'],clock_pressure=1500/p['target_ps'])
        sf.append(dict(source=r['source']['source_group'],f=f,y={k:r['labels']['owner_area_um2'].get(k,0) for k in SHARED_FEATURES}))
    shared={k:nnls(sf,n,k) for k,n in SHARED_FEATURES.items()}
    ctrl,audit=diagnostic.fit_state(controls)
    b={k:source_median([r for r in boundaries if r['role']==k],'value') for k in
       ('input_service->native_state','native_state->native_state','native_state->external_state')}
    if any(x<=0 or not math.isfinite(x) for x in b.values()):raise ValueError('nonpositive measured data boundary')
    inter=source_median(wires,'value') if wires else 0.
    # Reserve is the train-only boundary underprediction residual, separate
    # from arithmetic residuals and not a knob selected on validation labels.
    reserve=max(0.,max(r['value']-b[r['role']] for r in boundaries))
    alpha={metric:source_median([dict(source=r['source'],value=r[metric]/r['weight']) for r in bridge],'value') for metric in ('delay','area')}
    first=root/'runs'/next(t['id'] for t in a['tasks'] if t['role']=='train')
    pins=read(first/'liberty-pins.json');cover=legal_cover(pins,a['profile_sha256'])
    state=dict(schema='nangate45-N56-state-shared-functions-v1',profile_sha256=a['profile_sha256'],
        S=dict(area_models=areas,valid_bit_area_um2=pins['DFF_X1']['area_um2'],functions=ctrl,features=diagnostic.S_FEATURES,
            data_boundary_ps=b,joint_reserve_ps=reserve,control_training_audit=audit),
        shared=shared,inter_owner_wire_ps=inter,
        static_bridge=dict(alpha=dict(operator_delay_ps=alpha['delay'],comb_area_um2=alpha['area']),train_only=True,source_equal=True),
        numerical_floors=dict(gate_delay_ps=min(x['operator_delay_ps'] for r in train for x in r['labels']['nodes'].values()),gate_area_um2=min(cover['area_um2'].values())),
        derivation='exclusive measured state/shared owners and same-path boundaries; arithmetic parameters unchanged',application_PPA_used=False,
        support=dict(total_FF_bits=[min(r['projection']['total_FF_bits'] for r in train),max(r['projection']['total_FF_bits'] for r in train)],
            L=[2,3,4],target_ps=list(samples.CLOCKS),reset_one_bits=[0,0]),
        precision_qualified=False,extrapolation_requires_explicit_reporting=True)
    out.mkdir();write(out/'state-shared.json',state);write(out/'cell-cover.json',cover);write(out/'characterization.json',characterize())
    import shutil
    shutil.copy2(samples.MODEL,out/'arithmetic.json')
    package=dict(schema=pipeline.SCHEMA,platform='nangate45',profile_sha256=a['profile_sha256'],evaluation_stage='grt',
        status='ready_for_finite_three_case_experiments',pricing='offline_shared_functions',exact_lookup=False,online_backend_feedback=False,application_PPA_used=False,
        scope=dict(mac32=[2,3],add512=[2,4],mul128=[2,4]),G_acceptance=a['G_acceptance'],
        selection_algorithm='frozen old D; no R1-R5 repairs',implementation_ABC='global requested T; local tau prediction only',
        precision_qualified=False,validation_pending=True,state_support=state['support'])
    for key,name in [('arithmetic','arithmetic.json'),('state_shared','state-shared.json'),('characterization','characterization.json'),('cell_cover','cell-cover.json')]:
        package[key]=dict(path=name,sha256=sha(out/name))
    write(out/'package.json',package)
    write(root/'fit-audit.json',dict(train_tasks=[r['task']['id'] for r in train],boundaries=boundaries,wires=wires,controls=controls,
        state_areas=state_rows,shared_rows=sf,reserve_derivation='max train boundary residual only',arithmetic_refitted=False,validation_labels_read=False,test_labels_read=False))
    write(root/'model-freeze.json',dict(package_sha256=sha(out/'package.json'),files={str(p):sha(p) for p in out.iterdir()},
        implementation={str(p):sha(p) for p in Path(__file__).parent.glob('nangate45_pipeline*.py')},admission_sha256=sha(root/'admission.json')))
    pipeline.load_package(out/'package.json')
    return dict(status='frozen_before_validation',boundaries_ps=b,reserve_ps=reserve,wire_ps=inter)


def stats(rows):
    groups=defaultdict(list)
    for r in rows:groups[r['source']].append(r['APE'])
    values=sorted(median(v) for v in groups.values())
    if not values:return dict(sources=0,median=None,P95=None,passed=False)
    m=values[math.ceil(.5*len(values))-1];p=values[math.ceil(.95*len(values))-1]
    return dict(sources=len(values),median=m,P95=p,maximum=max(values),passed=m<=.15 and p<=.35,
        source_APE={k:median(v) for k,v in groups.items()})


def evaluate(root):
    root=Path(root);a=samples.verify(root);seal=read(root/'model-freeze.json')
    for p,h in seal['files'].items():
        if sha(p)!=h:raise ValueError('N56 frozen model drift')
    rt=pipeline.load_package(root/'package/package.json');rows=[];panels=defaultdict(list)
    for t in a['tasks']:
        source=next(s for s in a['sources'] if s['id']==t['source']);d=read(root/'runs'/t['id']/'pipeline-labels.json')
        g,v,s,o=metadata(source,t['period_ps']);prediction=rt.evaluate(g,v,s,o)
        # Compare entire frozen implementation including independently constrained
        # inputs/outputs; .8T-slack at IR/RO, T-slack at register paths.
        actual=max((t['period_ps']-p['slack_ps'])/(.8 if p['path_class'] in ('input_data','input_enable','input_valid','reset','output_data','output_valid') else 1.)
            if p['path_class'] not in ('input_data','input_enable','input_valid','reset','output_data','output_valid') else
            (.8*t['period_ps']-p['slack_ps'])/.8 for p in d['functional_paths'])
        # Reset is an input path even when the capture bank is native.
        area=d['total_area_um2'];ape=abs(prediction['critical_required_ps']/actual-1);ae=abs(prediction['total_area_um2']/area-1)
        row=dict(task=t['id'],source=source['source_group'],role=t['role'],target_ps=t['period_ps'],
            predicted_required_ps=prediction['critical_required_ps'],actual_required_ps=actual,timing_APE=ape,
            predicted_area_um2=prediction['total_area_um2'],actual_area_um2=area,area_APE=ae,
            hold_slack_ps=d['whole_shell_metrics']['hold_worst_slack_ps'],owner_area={},node_errors={},
            point_prediction=prediction,candidate_PPA_calls=0)
        for owner,value in prediction['S']['area_owners_um2'].items():
            actual_owner=d['owner_area_um2'].get(owner,0);error=abs(value-actual_owner)/max(.01,actual_owner)
            row['owner_area'][owner]=dict(predicted=value,actual=actual_owner,APE=error)
            panels[(t['role'],'owner_area/'+owner)].append(dict(source=source['source_group'],APE=error))
        for p in prediction['owners']:
            actual_node=d['nodes']['node_'+str(p['node'])]
            row['node_errors'][str(p['node'])]=dict(delay_APE=abs(p['delay_ps']/actual_node['operator_delay_ps']-1),area_APE=abs(p['area_um2']/actual_node['comb_area_um2']-1))
        panels[(t['role'],'complete_timing')].append(dict(source=source['source_group'],APE=ape))
        panels[(t['role'],'total_area')].append(dict(source=source['source_group'],APE=ae))
        rows.append(row);Graph.origins.cache_clear();Graph.roots.cache_clear()
    result=dict(version='nangate45-N56-frozen-composition-evaluation-v1',rows=rows,
        metrics={role:{key:stats(value) for (r,key),value in panels.items() if r==role} for role in ('train','validation','test')},
        model_freeze_sha256=sha(root/'model-freeze.json'),parameters_changed_after_validation=False,application_PPA_used=False,
        G_acceptance=a['G_acceptance'],arithmetic_refitted=False)
    write(root/'evaluation.json',result)
    return result['metrics']
