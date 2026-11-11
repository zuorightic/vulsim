"""Complete stage, bypass, owner and ranking validation; never calibrates.

Predictions were frozen before the four physical requests. Every measured
dynamic data bank remains in the report, including pure forwarding banks.
"""
import argparse
from collections import defaultdict
from copy import deepcopy
import math
from pathlib import Path
import statistics

from .model_fast_preflight import read,write,sha
from .stage67_parse_v2 import parse_stage
from .stage67_owned_timing_v1 import connections,WIRES
from . import backend,model_fast_sdc_v3 as sdc
from .platforms import profile,verify_wire_readback
from .stage67_physical_probe_v1 import SUFFIX


def stats(values):
    values=sorted(values)
    return dict(count=len(values),median=statistics.median(values),P95=values[math.ceil(.95*len(values))-1])


def normalized_signature(prediction,cut,node):
    c=deepcopy(cut);c['captures']=[dict(node=node)]
    # Alias matching only: allow proof-preserving bit operations outside a
    # canonical cut's member list. Priced arithmetic and registers remain
    # hard stops. This cannot add an unpriced arithmetic source.
    c['members']=sorted(set(c['members'])|{n['id'] for n in prediction['graph']['nodes'] if n['kind'] in WIRES})
    arcs=connections(prediction['graph'],c,prediction['queries'])
    return [(e['source_kind'],e['source'],e['bit_pairs']) for e in arcs if e['sink_kind']=='capture']


def banks(prediction,actual,policy):
    rows=[];slots=prediction['state']['slots']
    for cut,stage in zip(prediction['cuts'],prediction['owned_timing']['stages'],strict=True):
        i=cut['stage'];captured={c['node']:c for c in stage['captures']};signatures={n:normalized_signature(prediction,cut,n) for n in captured}
        for slot in slots:
            if slot['valid'] or slot['stage']!=i+1 or not slot['variable_bits']:continue
            word=('external_capture/' if slot['external_capture'] else 'core/')+slot['name']
            paths=[p for p in actual['functional_paths'] if p['word']==word and p['stage']==i and p['path_class'] in ('native_data','external_data')]
            if not paths:raise ValueError('dynamic data bank has no physical path '+word)
            try:signature=normalized_signature(prediction,cut,slot['origin'])
            except ValueError:
                # An input stored only for later use is not an arithmetic
                # capture in the cut. It must prove a pure wire to a launch.
                graph=prediction['graph'];nodes={n['id']:n for n in graph['nodes']};seen=set()
                def pure(n):
                    if n in seen:raise ValueError('cyclic forwarding bank')
                    seen.add(n);v=nodes[n]
                    if v['kind']=='input' or n in cut['launches']:return
                    if v['kind']=='constant':return
                    if v['kind'] not in WIRES:raise ValueError('unpriced arithmetic hidden in forwarding bank')
                    for o in v['operands']:
                        if o['kind']=='symbol':pure(o['node'])
                pure(slot['origin']);signature=None
            matches=[captured[n] for n,sig in signatures.items() if signature is not None and sig==signature]
            if matches:
                pred=max(c['point_required_period_ps'] for c in matches);basis='exact_dynamic_bit_signature_of_priced_capture'
            else:
                if signature and any(kind=='operator' for kind,_,_ in signature):raise ValueError('arithmetic state bank lacks matching predicted capture')
                role=('input_service' if i==0 else 'native_state')+'->'+('external_state' if slot['external_capture'] else 'native_state')
                pred=policy['boundary_point_ps'][role];basis='proven_S_only_forwarding_or_bypass'
            worst=max(paths,key=lambda p:1500-p['slack_ps']);observed=1500-worst['slack_ps']
            node=math.fsum(worst['node_delay_ps'].values());inter=math.fsum(s['delay_ps'] for s in worst['segments'] if s['kind']=='inter_owner_wire' and set(s['owner'].split('->'))<=set(actual['nodes']))
            row=dict(stage=i,word=word,point_required_ps=pred,decision_required_ps=pred+policy['reserve']['joint_reserve_ps'],observed_required_ps=observed,
                relative_error=abs(pred-observed)/max(10,observed),prediction_basis=basis,arithmetic_path=bool(worst['node_order']),
                measured_nodes_ps=node,measured_inter_arithmetic_wire_ps=inter,measured_S_clock_adjacent_wire_ps=observed-node-inter,
                endpoint=worst['end'],node_order=worst['node_order'],timed_endpoints=len(paths))
            if not math.isclose(node+inter+row['measured_S_clock_adjacent_wire_ps'],observed,abs_tol=1e-8):raise ValueError('bank partition fails to conserve')
            rows.append(row)
    return rows


def compare(root,out):
    if out.exists():raise ValueError('preserve batch analysis')
    out.mkdir(parents=True);a=read(root/'admission.json');policy=read(a['timing_policy']['path']);points=[];all_stages=[];failures=[];owner_errors=defaultdict(list)
    if sha(a['timing_policy']['path'])!=a['timing_policy']['sha256'] or policy['reserve']['joint_reserve_ps']!=50:raise ValueError('frozen policy changed')
    for task in a['tasks']:
        bank=root/'runs'/task['id'];prediction=read(Path(task['input_directory'])/'prediction.json')
        if sha(Path(task['input_directory'])/'prediction.json')!=task['prediction_sha256']:raise ValueError('premeasurement prediction changed')
        labels={};metrics={}
        for stage,stem in (('synth','1_synth'),('grt','5_1_grt')):
            label=parse_stage(root/'readout-v2'/task['id']/stage);cells=read(bank/'liberty_cells.json')['cells'];p=profile('asap7')
            g=backend.stage_metrics(bank/'reports'/SUFFIX,stage,cells,1500,selected=p)
            g['wire_RC_readback']=verify_wire_readback(bank/'reports'/SUFFIX/('vulsim_'+stage+'_layer_rc.tsv'),p)
            g['stored_SDC']=sdc.verify_sdc((bank/'results'/SUFFIX/(stem+'.sdc')).read_text(),p,1500,sdc.rtl_ports((bank/'input.sv').read_text(),'ModelBundle'),serialization_stage=stage)
            native=read(bank/'logs'/SUFFIX/(stem+'.json'))[('synth' if stage=='synth' else 'globalroute')+'__design__instance__area__stdcell'];backend.verify_orfs_area(g['cell_area_um2'],native)
            if not math.isclose(label['total_area_um2'],g['cell_area_um2'],abs_tol=1e-5):raise ValueError('owner area sum differs from whole design')
            label['whole_shell_metrics']=g;write(out/(task['id']+'-'+stage+'-labels.json'),label);labels[stage]=label;metrics[stage]=g
        actual=labels['grt'];score=prediction['owned_timing'];b=banks(prediction,actual,policy);stages=[]
        for s in score['stages']:
            rows=[r for r in b if r['stage']==s['stage']]
            if not rows:raise ValueError('missing complete data stage')
            point=max([c['point_required_period_ps'] for c in s['captures']]+[r['point_required_ps'] for r in rows])
            needed=max(r['observed_required_ps'] for r in rows);decision=point+50
            stage=dict(task=task['id'],source=task['source'],placement=task['placement'],stage=s['stage'],point_required_ps=point,
                decision_required_ps=decision,observed_required_ps=needed,point_relative_error=abs(point-needed)/max(10,needed),
                decision_relative_distance=abs(decision-needed)/max(10,needed),setup_false_feasible=decision<=1500<needed,
                conservative_rejection=needed<=1500<decision,nonarithmetic_guard_violation_ps=s['nonarithmetic_guard_violation_ps'],
                dynamic_data_banks=len(rows),includes_pure_forwarding_or_bypass=any(not r['arithmetic_path'] for r in rows))
            stages.append(stage);all_stages.append(stage)
        nodes={'node_'+str(p['node']):p for p in prediction['prices']};node_errors={n:dict(delay_error=(nodes[n]['operator_delay_ps']-v['operator_delay_ps'])/max(10,v['operator_delay_ps']),
            area_error=(nodes[n]['comb_area_um2']-v['comb_area_um2'])/max(.01,v['comb_area_um2'])) for n,v in actual['nodes'].items()}
        owners={}
        for owner,value in score['owner_area_um2'].items():
            observed=math.fsum(v['comb_area_um2'] for v in actual['nodes'].values()) if owner=='operators' else actual['owner_area_um2'].get(owner,0)
            error=abs(value-observed)/max(.01,observed);owners[owner]=dict(predicted_um2=value,observed_um2=observed,relative_error=error);owner_errors[owner].append(error)
        whole=metrics['grt'];observed=actual['total_area_um2'];area_error=abs(score['total_area_um2']-observed)/max(.01,observed)
        predicted_setup=score['decision_violation_ps']<=0;actual_setup=whole['setup_worst_slack_ps']>=0
        if predicted_setup and not actual_setup:failures.append(task['id']+'/whole_shell_false_setup_feasible')
        points.append(dict(task=task['id'],source=task['source'],placement=task['placement'],target_ps=1500,stages=stages,banks=b,
            node_errors=node_errors,owner_area=owners,total_area=dict(predicted_um2=score['total_area_um2'],observed_um2=observed,relative_error=area_error),
            predicted_setup_feasible=predicted_setup,measured_setup_feasible=actual_setup,measured_setup_and_hold_feasible=actual_setup and whole['hold_worst_slack_ps']>=0,
            setup_slack_ps=whole['setup_worst_slack_ps'],hold_slack_ps=whole['hold_worst_slack_ps'],hold_review_required=whole['hold_worst_slack_ps']<5,
            predicted_worst_violation_ps=score['decision_violation_ps'],measured_worst_violation_ps=max(0,-whole['setup_worst_slack_ps']),whole_shell=whole))
    timing=stats([r['point_relative_error'] for r in all_stages]);area=stats([p['total_area']['relative_error'] for p in points]);by_class={s:stats([r['point_relative_error'] for r in all_stages if r['source']==s]) for s in sorted({r['source'] for r in all_stages})}
    if timing['median']>.15 or timing['P95']>.35:failures.append('full_stage_point_error_gate')
    if area['median']>.15 or area['P95']>.35:failures.append('total_area_error_gate')
    for name,value in by_class.items():
        if value['P95']>.50:failures.append(name+'/per_class_point_error_gate')
    for r in all_stages:
        if r['setup_false_feasible']:failures.append(r['task']+'/stage'+str(r['stage'])+'/false_setup_feasible')
    ranking=[]
    for kind in sorted({p['source'] for p in points}):
        pair=[p for p in points if p['source']==kind]
        if len(pair)!=2:raise ValueError('ranking needs two placements')
        def order(p,pred):
            feasible=p['predicted_setup_feasible' if pred else 'measured_setup_feasible'];ar=p['total_area']['predicted_um2' if pred else 'observed_um2'];v=p['predicted_worst_violation_ps' if pred else 'measured_worst_violation_ps'];return (not feasible,0 if feasible else v,ar)
        pred=sorted(pair,key=lambda p:order(p,True));observed=sorted(pair,key=lambda p:order(p,False));x,y=pair
        area_tie=abs(x['total_area']['observed_um2']-y['total_area']['observed_um2'])/max(x['total_area']['observed_um2'],y['total_area']['observed_um2'])<=.05
        both_feasible=all(p['measured_setup_feasible'] for p in pair);violation_tie=abs(x['measured_worst_violation_ps']-y['measured_worst_violation_ps'])<=5
        tied=area_tie and (both_feasible or (not any(p['measured_setup_feasible'] for p in pair) and violation_tie))
        agrees=[p['placement'] for p in pred]==[p['placement'] for p in observed]
        ranking.append(dict(source=kind,predicted_order=[p['placement'] for p in pred],observed_order=[p['placement'] for p in observed],within_observed_tie_band=tied,agrees=agrees))
        if not agrees and not tied:failures.append(kind+'/non_tied_ranking_disagreement')
    # Ownership diagnostics never get hidden by a small total-area error.
    owner_gates={n:stats(v) for n,v in owner_errors.items()};shared_failed=[n for n,v in owner_gates.items() if v['median']>.15 or v['P95']>.35]
    boundary_groups=defaultdict(list)
    for point in points:
        for bank in point['banks']:
            if not bank['arithmetic_path']:
                name='S_only_input_service_to_native' if bank['stage']==0 else 'S_only_native_to_external'
                boundary_groups[name].append(bank['relative_error'])
    boundary_stats={name:stats(values) for name,values in boundary_groups.items()}
    boundary_failures=[name for name,value in boundary_stats.items() if value['P95']>.50]
    joint_failures=failures+[name+'/boundary_class_P95_above_50percent' for name in boundary_failures]+[name+'/owner_area_diagnostic_gate' for name in shared_failed]
    result=dict(version='stage67-batch1-validation-v1',status='batch1_numerical_validation_failed' if failures else 'batch1_numerical_validation_passed_not_joint',
        failures=failures,points=points,complete_stage_point_error=timing,total_area_error=area,per_class_stage_error=by_class,owner_area_error=owner_gates,
        owners_outside_diagnostic_15_35_gates=shared_failed,ranking=ranking,setup_false_feasible_count=sum(p['predicted_setup_feasible'] and not p['measured_setup_feasible'] for p in points),
        boundary_class_error=boundary_stats,boundary_classes_outside_50percent_gate=boundary_failures,joint_validation_failures=joint_failures,
        setup_conservative_rejections=sum(not p['predicted_setup_feasible'] and p['measured_setup_feasible'] for p in points),
        frozen_prebatch_policy_sha256=a['timing_policy']['sha256'],reserve_ps=50,reserve_recalibrated=False,new_parameters_fitted=False,
        independence='combination_validation only; no locked joint test labels',zero_G_joint_qualified=False,full_D_ready=False,
        verdict_scope='point/stage/total-area/ranking gates reported separately from owner-specific, hold and independent joint qualification')
    write(out/'validation.json',result);print({k:result[k] for k in ('status','failures','complete_stage_point_error','total_area_error','owners_outside_diagnostic_15_35_gates','ranking','full_D_ready')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();compare(a.root.resolve(),a.out.resolve())
