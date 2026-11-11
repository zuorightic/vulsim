"""Frozen successor vs six existing validation placements; no fitting."""
import argparse
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
import math

from .model_fast_preflight import read,write,sha
from .stage67_factored_timing_v1 import complete_variant,estimate
from .stage67_batch1_analyze_v1 import banks,stats


def evaluate(native,policy,model,S,packet_manifest,out):
    if out.exists():raise ValueError('preserve successor validation')
    out.mkdir(parents=True);n=read(native);p=read(policy);m=read(model);s=read(S);manifest=read(packet_manifest)
    if n['policy_sha256']!=sha(policy) or p['state_model_sha256']!=sha(S) or n['model_sha256']!=sha(model):raise ValueError('frozen validation dependencies differ')
    sources={row['source']:row for row in n['sources']};points=[];stage_rows=[];bank_groups=defaultdict(list);owner_groups=defaultdict(list)
    for packet in manifest['packets']:
        if packet['role']!='combination_validation':raise ValueError('independent packet may not calibrate/validate candidate here')
        if sha(packet['labels'])!=packet['labels_sha256']:raise ValueError('certified physical label changed')
        actual=read(packet['labels']);v=next(v for v in sources[packet['source']]['variants'] if v['id']==packet['placement']);target=next(t for t in v['targets'] if t['target_ps']==1500)
        if target['owned_timing']['status']!='candidate_covered':raise ValueError('validation request outside successor area/node domain')
        v=complete_variant(v['graph'],v);score=target['owned_timing'];prediction=dict(graph=v['graph'],cuts=v['cuts'],state=v['state'],owned_timing=score,queries=target['queries'])
        typed=deepcopy(p);typed['boundary_point_ps']=typed['forward_boundary_point_ps']
        bank_rows=banks(prediction,actual,typed);stages=[]
        for row in bank_rows:
            group=('arithmetic' if row['arithmetic_path'] else 'S_only_input_service_to_native' if row['stage']==0 else 'S_only_native_to_external')
            bank_groups[group].append(row['relative_error'])
        for stage in score['stages']:
            measured=[b for b in bank_rows if b['stage']==stage['stage']]
            needed=max(b['observed_required_ps'] for b in measured);predicted=max(c['point_required_period_ps'] for c in stage['captures']);decision=predicted+50
            value=dict(source=packet['source'],placement=packet['placement'],stage=stage['stage'],point_required_ps=predicted,observed_required_ps=needed,
                decision_required_ps=decision,relative_error=abs(predicted-needed)/max(10,needed),false_setup_feasible=decision<=1500<needed,conservative_rejection=needed<=1500<decision)
            stages.append(value);stage_rows.append(value)
        areas={}
        for owner,predicted in score['owner_area_um2'].items():
            observed=math.fsum(v['comb_area_um2'] for v in actual['nodes'].values()) if owner=='operators' else actual['owner_area_um2'].get(owner,0)
            error=abs(predicted-observed)/max(.01,observed);areas[owner]=dict(predicted_um2=predicted,observed_um2=observed,relative_error=error);owner_groups[owner].append(error)
        observed=actual['total_area_um2'];whole=actual['whole_shell_metrics']
        points.append(dict(source=packet['source'],placement=packet['placement'],stages=stages,banks=bank_rows,owner_area=areas,
            total_area=dict(predicted_um2=score['total_area_um2'],observed_um2=observed,relative_error=abs(score['total_area_um2']-observed)/max(.01,observed)),
            setup_slack_ps=whole['setup_worst_slack_ps'],hold_slack_ps=whole['hold_worst_slack_ps'],hold_review_required=whole['hold_worst_slack_ps']<5,
            predicted_setup_feasible=score['decision_violation_ps']<=0,measured_setup_feasible=whole['setup_worst_slack_ps']>=0,
            predicted_violation_ps=score['decision_violation_ps'],observed_violation_ps=max(0,-whole['setup_worst_slack_ps'])))
    timing=stats([r['relative_error'] for r in stage_rows]);area=stats([r['total_area']['relative_error'] for r in points]);owners={k:stats(v) for k,v in owner_groups.items()};bank_classes={k:stats(v) for k,v in bank_groups.items()};failures=[]
    if timing['median']>.15 or timing['P95']>.35:failures.append('complete_stage_error')
    if area['median']>.15 or area['P95']>.35:failures.append('total_area_error')
    for name,value in bank_classes.items():
        if name.startswith('S_only') and value['P95']>.50:failures.append(name+'/bank_class_error')
    for name,value in owners.items():
        if name in ('root_repair','shared_clock','shared_physical') and (value['median']>.15 or value['P95']>.35):failures.append(name+'/owner_area_error')
    for row in stage_rows:
        if row['false_setup_feasible']:failures.append(row['source']+'/'+row['placement']+'/false_setup_feasible')
    ranking=[]
    for source in sorted({r['source'] for r in points}):
        pair=[r for r in points if r['source']==source]
        if len(pair)!=2:raise ValueError('two fixed placements required per source')
        def order(row,pred):
            feasible=row['predicted_setup_feasible' if pred else 'measured_setup_feasible'];return (not feasible,0 if feasible else row['predicted_violation_ps' if pred else 'observed_violation_ps'],row['total_area']['predicted_um2' if pred else 'observed_um2'])
        predicted=[r['placement'] for r in sorted(pair,key=lambda r:order(r,True))];observed=[r['placement'] for r in sorted(pair,key=lambda r:order(r,False))]
        a,b=pair;tied=abs(a['total_area']['observed_um2']-b['total_area']['observed_um2'])/max(a['total_area']['observed_um2'],b['total_area']['observed_um2'])<=.05 and all(r['measured_setup_feasible'] for r in pair)
        ranking.append(dict(source=source,predicted=predicted,observed=observed,tie=tied,agrees=predicted==observed))
        if not tied and predicted!=observed:failures.append(source+'/non_tied_ranking_disagreement')
    result=dict(version='state-shared-successor-validation-v1',status='failed_joint_validation' if failures else 'passed_finite_validation_not_independent',
        point_stage_error=timing,total_area_error=area,owner_area_error=owners,bank_class_error=bank_classes,failures=failures,points=points,ranking=ranking,
        policy_sha256=sha(policy),model_sha256=sha(model),reserve_ps=50,reserve_recalibrated=False,parameters_changed_after_validation=False,
        independent_tests_unlocked=False,zero_G_joint_qualified=False,full_D_ready=False,physical_calls=0)
    write(out/'validation.json',result);print({k:result[k] for k in ('status','point_stage_error','total_area_error','owner_area_error','bank_class_error','failures','full_D_ready')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('native','policy','model','S','packets','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();evaluate(a.native.resolve(),a.policy.resolve(),a.model.resolve(),a.S.resolve(),a.packets.resolve(),a.out.resolve())
