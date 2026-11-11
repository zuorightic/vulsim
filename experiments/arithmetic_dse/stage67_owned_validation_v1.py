"""Replay existing validation pilots against prospective exclusive accounting.

The point policy is train-only. This module calibrates only the predeclared
once-per-stage reserve, and never grants independent or production quality.
"""
import argparse
from copy import deepcopy
import math
from pathlib import Path
import statistics

from .model_fast_preflight import read,write,sha


def summarize(rows,key):
    values=sorted(r[key] for r in rows)
    return dict(median=statistics.median(values),P95=values[math.ceil(.95*len(values))-1],count=len(values))


def analyze(native,policy,diagnosis,labels,out):
    if out.exists():raise ValueError('preserve owned-accounting validation')
    out.mkdir(parents=True);n=read(native);p=read(policy);old=read(diagnosis)
    if old['status']!='pilot_quality_failed' or old['full_D_ready']:raise ValueError('prior failure identity changed')
    if n['policy_sha256']!=sha(policy):raise ValueError('native timing policy identity differs')
    sources={s['source']:s for s in n['sources']};rows=[];placements=[];decompositions=[];residuals=[]
    for previous in old['points']:
        source=sources[previous['source']];variant=next(v for v in source['variants'] if v['id']==previous['placement'])
        target=next(t for t in variant['targets'] if t['target_ps']==previous['target_ps']);estimate=target['owned_timing']
        if estimate['status']!='candidate_covered':raise ValueError('validation pilot lacks prices')
        actual=read(labels/(previous['task']+'-grt-labels.json'))
        if not actual['strict_actual_Liberty_arcs'] or not actual['area_and_path_increments_owned_once']:raise ValueError('uncertified measurement')
        seen={x['node'] for x in estimate['node_prices']}
        if len(seen)!=len(estimate['node_prices']):raise ValueError('duplicate shared node area')
        expected_area=math.fsum(x['area_um2'] for x in estimate['node_prices'])
        if not math.isclose(estimate['owner_area_um2']['operators'],expected_area,abs_tol=1e-8):raise ValueError('node area counted twice')
        if not math.isclose(estimate['total_area_um2'],previous['total_area']['predicted_um2'],abs_tol=1e-8):raise ValueError('timing successor changed areas')
        for stage in estimate['stages']:
            i=stage['stage'];pred=max(c['point_required_period_ps'] for c in stage['captures'])
            decision=max(c['decision_required_period_ps'] for c in stage['captures']);nodeguard=max(c['legacy_node_guard_required_period_ps'] for c in stage['captures'])
            prev=next(s for s in previous['arithmetic_stages'] if s['stage']==i);observed=prev['observed_required_period_ps']
            paths=[v for v in actual['functional_paths'] if v['stage']==i and v['node_order'] and v['path_class'] in ('native_data','external_data')]
            path=max(paths,key=lambda v:1500-v['slack_ps']);full=1500-path['slack_ps']
            if not math.isclose(full,observed,abs_tol=1e-6):raise ValueError('validation maximum witness differs')
            witness=next(w for w in previous['witness_decomposition'] if w['stage']==i and w['endpoint']==path['end'])
            # Every measured increment belongs to exactly one node, S or
            # arithmetic-to-arithmetic wire. Clock/Q/setup are the remainder
            # of the same full T-slack budget; never add a second wire bill.
            node=math.fsum(path['node_delay_ps'].values());inter=math.fsum(s['delay_ps'] for s in path['segments'] if s['kind']=='inter_owner_wire' and set(s['owner'].split('->'))<=set(actual['nodes']))
            S=full-node-inter
            if not math.isclose(node+inter+S,full,abs_tol=1e-8):raise ValueError('physical exclusive ownership does not conserve')
            arithmetic_count=len(path['node_order']);wire=p['inter_arithmetic_wire_point_ps']*max(0,arithmetic_count-1)
            predicted_nodes=witness['predicted_node_sum_ps'];boundary_and_wire=pred-predicted_nodes
            error_parts=dict(node_function_error_ps=witness['node_function_error_on_independent_max_sum_ps'],
                independent_node_maxima_conservatism_ps=witness['independent_max_sum_conservatism_ps'],
                S_and_inter_wire_error_ps=boundary_and_wire-(S+inter))
            if not math.isclose(math.fsum(error_parts.values()),pred-full,abs_tol=1e-6):raise ValueError('stage error attribution fails to conserve')
            decompositions.append(dict(task=previous['task'],stage=i,endpoint=path['end'],observed_required_ps=full,
                observed_node_ps=node,observed_S_clock_and_adjacent_wire_ps=S,observed_inter_arithmetic_wire_ps=inter,
                predicted_node_sum_ps=predicted_nodes,predicted_S_plus_inter_wire_ps=boundary_and_wire,
                predicted_inter_wire_on_witness_ps=wire,error_parts=error_parts,
                measured_segments=path['segments'],increments_owned_once=True))
            residuals.append(observed-pred)
            rows.append(dict(task=previous['task'],source=previous['source'],placement=previous['placement'],stage=i,target_ps=1500,
                old_guard_required_ps=prev['predicted_required_period_ps'],observed_required_ps=observed,
                point_required_ps=pred,decision_required_ps=decision,legacy_node_guard_after_fix_ps=nodeguard,
                point_relative_error=abs(pred-observed)/max(10,observed),decision_relative_distance=abs(decision-observed)/max(10,observed),
                old_relative_distance=prev['relative_error'],positive_residual_ps=max(0,observed-pred),
                setup_false_feasible=decision<=1500<observed,setup_conservative_rejection=observed<=1500<decision,
                reserve_added_once_ps=decision-pred,nonarithmetic_guard_violation_ps=stage['nonarithmetic_guard_violation_ps']))
        whole=previous['whole_shell'];placements.append(dict(placement=previous['placement'],
            point_required_ps=max(r['point_required_ps'] for r in rows if r['placement']==previous['placement']),
            observed_required_ps=max(r['observed_required_ps'] for r in rows if r['placement']==previous['placement']),
            total_area=previous['total_area'],predicted_nonnode_areas=estimate['owner_area_um2'],observed_nonnode_areas=actual['owner_area_um2'],
            setup_slack_ps=whole['setup_worst_slack_ps'],hold_slack_ps=whole['hold_worst_slack_ps'],
            setup_and_hold_measured_feasible=whole['setup_worst_slack_ps']>=0 and whole['hold_worst_slack_ps']>=0))
    errors=summarize(rows,'point_relative_error');distance=summarize(rows,'decision_relative_distance')
    point_pass=errors['median']<=.15 and errors['P95']<=.35
    point_rank=[x['placement'] for x in sorted(placements,key=lambda x:x['point_required_ps'])]
    actual_rank=[x['placement'] for x in sorted(placements,key=lambda x:x['observed_required_ps'])]
    area_rank=[x['placement'] for x in sorted(placements,key=lambda x:x['total_area']['predicted_um2'])]
    observed_area_rank=[x['placement'] for x in sorted(placements,key=lambda x:x['total_area']['observed_um2'])]
    reserve=max(0,max(residuals))+p['reserve']['engineering_ps']
    calibrated=deepcopy(p);calibrated['reserve'].update(joint_reserve_ps=reserve,calibration_status='validation_calibrated_not_independent',
        maximum_positive_validation_residual_ps=max(0,max(residuals)),validation_source_count=len({r['source'] for r in rows}),validation_stages=len(rows),
        validation_native_sha256=sha(native),validation_pilot_sha256=sha(diagnosis))
    write(out/'candidate-calibrated.json',calibrated)
    report=dict(version='owned-composition-pilot-validation-v1',status='pilot_point_numerical_gates_passed_not_independent' if point_pass else 'pilot_point_quality_failed',
        point_accuracy=errors,decision_guard_distance_not_accuracy=distance,old_guard_distance=summarize(rows,'old_relative_distance'),
        stages=rows,placements=placements,ownership_audit=decompositions,setup_false_feasible_count=sum(r['setup_false_feasible'] for r in rows),
        ranking=dict(predicted_delay=point_rank,observed_delay=actual_rank,delay_order_agrees=point_rank==actual_rank,
            predicted_area=area_rank,observed_area=observed_area_rank,area_order_agrees=area_rank==observed_area_rank,
            scope='two fixed validation placements, no search or independent ranking claim'),
        reserve_rule='maximum positive validation stage residual + inherited 50ps engineering reserve; once per path/stage',
        calibrated_joint_reserve_ps=reserve,training_point_policy_sha256=sha(policy),calibrated_policy_sha256=sha(out/'candidate-calibrated.json'),
        prior_failed_verdict_preserved=True,node_parameters_changed=False,original_S_parameters_changed=False,
        shared_clock_area_qualified=False,hold_qualification=False,independent_joint_tests_unlocked=False,zero_G_joint_qualified=False,full_D_ready=False,
        physical_calls=0)
    write(out/'validation.json',report)
    print(dict(status=report['status'],point_accuracy=errors,guard_distance=distance,joint_reserve_ps=reserve,
        delay_ranking_agrees=point_rank==actual_rank,full_D_ready=False),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('native','policy','diagnosis','labels','out'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();analyze(a.native.resolve(),a.policy.resolve(),a.diagnosis.resolve(),a.labels.resolve(),a.out.resolve())
