"""Frozen-function whole-stage validation on nine existing physical snapshots.

The source roles stay validation. No fitted parameters or support rules change;
all new EDA report leaves are charged, synth/grt snapshots are never rerun.
"""
import argparse
from copy import deepcopy
import math
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha
from .budget import Ledger,POLICY,usage
from . import backend,model_fast_sdc_v3 as sdc
from .platforms import profile,verify_wire_readback
from .stage67_physical_probe_v1 import SUFFIX
from .stage67_parse_v2 import parse_stage
from .stage67_batch1_analyze_v1 import stats,banks as old_banks
from .stage67_factored_timing_v1 import complete_variant
from .operator_condition_model import query

ROOT=Path(__file__).resolve().parents[2]
PARENT=Path('/home/zyrv/vulsim-artifacts/stage67-shared-fit-20261111-v1')
NODE=ROOT/'experiments/arithmetic/models/asap7_conditional_operators_v1/operators.json'
BINDING=Path('/home/zyrv/vulsim-artifacts/conditional-boundary-20261110-v3/binding-candidate.json')
POLICY_PATH=PARENT/'fit-v1/candidate.json'
FREEZE=PARENT/'fit-v1/freeze-v2.json'


def dependencies():
    # Conservative implementation snapshot for this report/analysis package.
    files=[p for p in (ROOT/'experiments/arithmetic_dse').glob('*.py')]
    files += [ROOT/'regression/arithmetic_steps123.py']
    files += [ROOT/'experiments/arithmetic_dse/reference_assets'/n for n in ('stage67_context_v1.tcl','stage7_readout_v1.tcl')]
    files += list((ROOT/'experiments/arithmetic_dse/backend').glob('*'))
    return {str(p.relative_to(ROOT)):sha(p) for p in files if p.is_file()}


def admit(root):
    if root.exists():raise ValueError('preserve whole-stage admission')
    f=read(FREEZE)
    for n,h in f['files'].items():
        if sha(n)!=h:raise ValueError('frozen model or inference drift '+n)
    physical=PARENT/'validation-batch-v1';a=read(physical/'admission.json');p=read(physical/'progress.json')
    if p['phase']!='physical_batch_complete' or p['errors'] or len(p['completed'])!=9:raise ValueError('complete prior validation snapshots required')
    native=read(PARENT/'native-v2/native.json');tasks=[]
    for task in a['tasks']:
        if task['source_role']!='validation' or task['period_ps'] not in (500,1500,3000):raise ValueError('unregistered role/target')
        t=deepcopy(task);directory=physical/'runs'/t['id'];source=next(s for s in native['sources'] if s['source']==t['source'])
        variant=next(v for v in source['variants'] if v['id']==t['placement']);target=next(v for v in variant['targets'] if v['target_ps']==t['period_ps'])
        if target['owned_timing']['status']!='candidate_covered':raise ValueError('uncovered frozen candidate')
        t['physical_directory']=str(directory)
        t['snapshot_files']={str(x):sha(x) for x in directory.rglob('*') if x.is_file() and (x.is_relative_to(directory/'results') or x.name in ('mapped.json','mapped-state.json','liberty-pins.json','input.sv','manifest.json','pilot-metrics.json') or x.name.startswith('census-'))}
        v=complete_variant(variant['graph'],variant);prices=[dict(node=q['trace']['node'],**query(read(NODE),q['descriptor'])) for q in target['queries']]
        prediction=dict(source=t['source'],role='validation',placement=t['placement'],target_ps=t['period_ps'],graph=v['graph'],cuts=v['cuts'],state=v['state'],
            queries=target['queries'],prices=prices,owned_timing=target['owned_timing'],model_sha256=sha(NODE),policy_sha256=sha(POLICY_PATH),
            S_binding_sha256=sha(BINDING),basis='already frozen before shared validation measurements; complete-stage paths not consumed for fitting',full_D_ready=False)
        out=root/'predictions'/(t['id']+'.json');write(out,prediction);t.update(prediction=str(out),prediction_sha256=sha(out));tasks.append(t)
    later=dict(synth=688,grt=688,walltime_s=86400,CPU_time_s=172800,storage_bytes=30*1024**3)
    budget=dict(synth=0,grt=0,support=64,walltime_s=18*120+12*300,CPU_time_s=4*(18*120+12*300),storage_bytes=2*1024**3)
    used=usage(read(Ledger().path)['entries']);limits=read(POLICY)['resources']
    if used['synth']+688>limits['max_synthesis_calls'] or used['grt']+688>limits['max_global_route_calls'] or used['walltime_s']+budget['walltime_s']+86400>limits['max_global_walltime_h']*3600 or used['CPU_time_s']+budget['CPU_time_s']+172800>limits['max_tool_CPU_time_h']*3600 or shutil.disk_usage(root).free<later['storage_bytes']+budget['storage_bytes']:raise ValueError('report batch and later work not funded')
    names=dependencies()
    for n in names:
        dest=root/'source'/n;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/n,dest)
    write(root/'admission.json',dict(version='frozen-multiclock-whole-stage-v1',id=root.name,tasks=tasks,sources=names,
        freeze_path=str(FREEZE),freeze_sha256=sha(FREEZE),policy_path=str(POLICY_PATH),policy_sha256=sha(POLICY_PATH),
        parent_admission=str(physical/'admission.json'),parent_admission_sha256=sha(physical/'admission.json'),
        numerical_targets=[500,1500,3000],synth_max=0,grt_max=0,support_max=64,batch_budget=budget,later_work_reserved=later,
        gates=dict(point_median=.15,point_P95=.35,class_P95=.50,total_area_median=.15,total_area_P95=.35,owner_area_median=.15,owner_area_P95=.35,false_feasible_max=0),
        second_placement_measurement_gate='only after this full-stage/false-feasible validation passes; exact structural placement and budget separately admitted',
        parameters_changed=False,independent_tests_unlocked=False,full_D_ready=False))
    write(root/'progress.json',dict(phase='physical_batch_complete',inherited_snapshots=9,new_physical_calls=0))
    print('MULTICLOCK_STAGE_READOUT_ADMITTED inherited=9 synth=0 grt=0 locked_test=0',flush=True)


def verify_admission(root):
    a=read(root/'admission.json')
    if sha(a['freeze_path'])!=a['freeze_sha256'] or sha(a['policy_path'])!=a['policy_sha256']:raise ValueError('frozen target policy changed')
    for n,h in read(a['freeze_path'])['files'].items():
        if sha(n)!=h:raise ValueError('frozen inference drift '+n)
    for n,h in a['sources'].items():
        if sha(ROOT/n)!=h or sha(root/'source'/n)!=h:raise ValueError('report producer drift '+n)
    for t in a['tasks']:
        if sha(t['prediction'])!=t['prediction_sha256'] or sha(t['endpoint_contract'])!=t['endpoint_sha256'] or sha(t['rtl'])!=t['rtl_sha256']:raise ValueError('prediction/RTL/endpoint identity changed')
        for n,h in t['snapshot_files'].items():
            if sha(n)!=h:raise ValueError('saved physical snapshot modified '+n)


def banks(prediction,actual,policy,t):
    # Same checked bank-to-bit-signature matching; only numerical T changes.
    import inspect
    text=inspect.getsource(old_banks)
    if text.count('1500')!=2:raise ValueError('frozen bank period callsite changed')
    namespace=dict(old_banks.__globals__);namespace['target_ps']=t
    exec(compile(text.replace('1500','target_ps'),__file__,'exec'),namespace)
    typed=deepcopy(policy);typed['boundary_point_ps']=typed['forward_boundary_point_ps']
    return namespace['banks'](prediction,actual,typed)


def analyze(root,out):
    if out.exists():raise ValueError('preserve complete-stage analysis')
    verify_admission(root);out.mkdir(parents=True);a=read(root/'admission.json');policy=read(POLICY_PATH);points=[];all_stages=[];witnesses=[]
    for task in a['tasks']:
        t=task['period_ps'];directory=Path(task['physical_directory']);prediction=read(task['prediction']);labels={}
        for stage in ('synth','grt'):
            folder=root/'readout-v1'/task['id']/stage;owners=read(folder/'ownership.json')
            if owners['target_period_ps']!=t:raise ValueError('stale physical target packet')
            label=parse_stage(folder);g=backend.stage_metrics(directory/'reports'/SUFFIX,stage,read(directory/'liberty_cells.json')['cells'],t,selected=profile('asap7'))
            verify_wire_readback(directory/'reports'/SUFFIX/('vulsim_'+stage+'_layer_rc.tsv'),profile('asap7'))
            stem='1_synth' if stage=='synth' else '5_1_grt'
            sdc.verify_sdc((directory/'results'/SUFFIX/(stem+'.sdc')).read_text(),profile('asap7'),t,sdc.rtl_ports(Path(task['rtl']).read_text(),'ModelBundle'),serialization_stage=stage)
            if not math.isclose(label['total_area_um2'],g['cell_area_um2'],abs_tol=1e-5):raise ValueError('unique ownership/OpenDB area differs')
            label.update(target_ps=t,whole_shell_metrics=g);write(out/(task['id']+'-'+stage+'-labels.json'),label);labels[stage]=label
        actual=labels['grt'];score=prediction['owned_timing'];b=banks(prediction,actual,policy,t);stages=[]
        prices={'node_'+str(p['node']):p for p in prediction['prices']}
        node_errors={n:dict(predicted_delay_ps=prices[n]['operator_delay_ps'],observed_delay_ps=v['operator_delay_ps'],
            delay_relative_error=(prices[n]['operator_delay_ps']-v['operator_delay_ps'])/max(10,v['operator_delay_ps']),predicted_area_um2=prices[n]['comb_area_um2'],observed_area_um2=v['comb_area_um2'],
            area_relative_error=(prices[n]['comb_area_um2']-v['comb_area_um2'])/max(.01,v['comb_area_um2'])) for n,v in actual['nodes'].items()}
        for s in score['stages']:
            physical_banks=[r for r in b if r['stage']==s['stage']]
            if not physical_banks:raise ValueError('complete stage has no dynamic data bank')
            point=max([c['point_required_period_ps'] for c in s['captures']]+[r['point_required_ps'] for r in physical_banks]);needed=max(r['observed_required_ps'] for r in physical_banks);decision=point+policy['reserve']['joint_reserve_ps']
            row=dict(task=task['id'],source=task['source'],target_ps=t,stage=s['stage'],point_required_ps=point,observed_required_ps=needed,decision_required_ps=decision,
                relative_error=abs(point-needed)/max(10,needed),signed_error_ps=point-needed,false_feasible=decision<=t<needed,conservative_rejection=needed<=t<decision)
            stages.append(row);all_stages.append(row)
        nonarithmetic=[]
        for path in actual['functional_paths']:
            if path['path_class'] in ('native_data','external_data'):continue
            nonarithmetic.append(dict(path_class=path['path_class'],stage=path['stage'],word=path['word'],endpoint=path['end'],slack_ps=path['slack_ps']))
        for path in actual['functional_paths']:
            if not path['node_order']:continue
            independent=sum(actual['nodes'][n]['operator_delay_ps'] for n in path['node_order']);onpath=sum(path['node_delay_ps'].values());pred=sum(prices[n]['operator_delay_ps'] for n in path['node_order'])
            inter=sum(s['delay_ps'] for s in path['segments'] if s['kind']=='inter_owner_wire' and set(s['owner'].split('->'))<=set(actual['nodes']))
            witnesses.append(dict(task=task['id'],target_ps=t,path_class=path['path_class'],stage=path['stage'],endpoint=path['end'],node_order=path['node_order'],
                observed_required_ps=t-path['slack_ps'],predicted_node_sum_ps=pred,observed_independent_max_sum_ps=independent,observed_onpath_node_sum_ps=onpath,
                base_function_error_ps=pred-independent,independent_max_conservatism_ps=independent-onpath,observed_inter_arithmetic_wire_ps=inter,
                observed_S_clock_adjacent_wire_ps=t-path['slack_ps']-onpath-inter))
        owner_errors={}
        for n,val in score['owner_area_um2'].items():
            measured=sum(v['comb_area_um2'] for v in actual['nodes'].values()) if n=='operators' else actual['owner_area_um2'].get(n,0)
            owner_errors[n]=dict(predicted=val,observed=measured,relative_error=abs(val-measured)/max(.01,measured))
        whole=actual['whole_shell_metrics'];predicted_feasible=score['decision_violation_ps']<=0;observed_feasible=whole['setup_worst_slack_ps']>=0
        points.append(dict(task=task['id'],source=task['source'],target_ps=t,placement=task['placement'],stages=stages,banks=b,node_errors=node_errors,owner_errors=owner_errors,
            total_area=dict(predicted=score['total_area_um2'],observed=actual['total_area_um2'],relative_error=abs(score['total_area_um2']-actual['total_area_um2'])/max(.01,actual['total_area_um2'])),
            predicted_setup_feasible=predicted_feasible,observed_setup_feasible=observed_feasible,whole_shell_false_feasible=predicted_feasible and not observed_feasible,
            conservative_rejection=not predicted_feasible and observed_feasible,predicted_violation_ps=score['decision_violation_ps'],observed_violation_ps=max(0,-whole['setup_worst_slack_ps']),
            whole_shell=whole,nonarithmetic_paths=nonarithmetic,endpoint_checks=actual['endpoint_checks'],constant_outputs=actual['proven_constant_output_bits']))
    timing=stats([x['relative_error'] for x in all_stages]);area=stats([x['total_area']['relative_error'] for x in points]);classes={n:stats([s['relative_error'] for s in all_stages if s['source']==n]) for n in sorted({s['source'] for s in all_stages})}
    owners={n:stats([p['owner_errors'][n]['relative_error'] for p in points]) for n in points[0]['owner_errors']};bank_classes={}
    for name in ('S_only_input_service_to_native','S_only_native_to_external'):
        values=[b['relative_error'] for p in points for b in p['banks'] if not b['arithmetic_path'] and (b['stage']==0)==(name=='S_only_input_service_to_native')]
        if values:bank_classes[name]=stats(values)
    failures=[]
    if timing['median']>.15 or timing['P95']>.35:failures.append('complete_stage_error')
    if area['median']>.15 or area['P95']>.35:failures.append('total_area_error')
    failures.extend(n+'/class_error' for n,v in classes.items() if v['P95']>.50)
    failures.extend(n+'/bank_error' for n,v in bank_classes.items() if v['P95']>.50)
    failures.extend(n+'/owner_error' for n,v in owners.items() if n in ('shared_clock','shared_physical','root_repair') and (v['median']>.15 or v['P95']>.35))
    failures.extend(s['task']+'/stage'+str(s['stage'])+'/false_feasible' for s in all_stages if s['false_feasible'])
    failures.extend(p['task']+'/whole_shell_false_feasible' for p in points if p['whole_shell_false_feasible'])
    write(out/'validation.json',dict(version='frozen-multiclock-stage-validation-v1',status='failed_full_stage_validation' if failures else 'passed_full_stage_validation_pending_ranking',
        complete_stage_error=timing,total_area_error=area,per_structure_stage_error=classes,owner_area_error=owners,bank_class_error=bank_classes,failures=failures,points=points,
        false_feasible_count=sum(p['whole_shell_false_feasible'] for p in points),conservative_rejection_count=sum(p['conservative_rejection'] for p in points),
        ranking='pending second structurally selected placement; no ranking claim for single placement',G_delay_ps=0,reserve_ps=50,parameters_changed=False,independent_test_unlocked=False,zero_G_joint_qualified=False,full_D_ready=False))
    write(out/'witness-decomposition.json',dict(witnesses=witnesses,rule='node-function error, independent-max conservatism, inter-node wire and S/clock/adjacent wire separate; no G fitting'))
    print({k:read(out/'validation.json')[k] for k in ('status','complete_stage_error','total_area_error','bank_class_error','failures','false_feasible_count','conservative_rejection_count')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('admit','analyze'));p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='admit':admit(a.root.resolve())
    else:analyze(a.root.resolve(),a.out.resolve())
