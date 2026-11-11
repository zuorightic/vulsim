"""Read unchanged alternate snapshots and compare paired candidate rankings.

Reuse first nine labels and their errors, never fit a parameter from the pair.
The physical call identity is disjoint from read-only report admissions.
"""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil

from .model_fast_preflight import read,write,sha
from . import stage67_multiclock_v1 as stage
from . import stage67_state_semantics_v2 as semantics
from .model_m2_live_cec_v4 import verify_proof
from .stage67_batch1_analyze_v1 import stats


def prepare(first,root):
    if root.exists():raise ValueError('preserve alternate report admission')
    physical=first/'paired-physical';a=read(physical/'admission.json');p=read(physical/'progress.json')
    if p['phase']!='physical_batch_complete' or p['errors'] or len(p['completed'])!=9:raise ValueError('all exact alternate snapshots must settle')
    for n,h in a['sources'].items():
        if sha(stage.ROOT/n)!=h or sha(physical/'source'/n)!=h:raise ValueError('frozen physical producer drift '+n)
    for n,h in read(stage.FREEZE)['files'].items():
        if sha(n)!=h:raise ValueError('node/S/shared inference drift '+n)
    root.mkdir(parents=True);tasks=[];boolean=[]
    for value in a['tasks']:
        t=deepcopy(value);directory=physical/'runs'/t['id'];t['physical_directory']=str(directory)
        t['snapshot_files']={str(x):sha(x) for x in directory.rglob('*') if x.is_file() and (x.is_relative_to(directory/'results') or x.name in ('mapped.json','mapped-state.json','liberty-pins.json','input.sv','manifest.json','pilot-metrics.json') or x.name.startswith('census-'))}
        proof=semantics.verify(directory,read(directory/'mapped-state.json'),Path(t['rtl']).read_text(),read(t['endpoint_contract']))
        write(root/'state-proofs'/(t['id']+'.json'),proof)
        verify_proof(directory/'logs'/stage.SUFFIX/'structural_cec/proof.json',directory/'results'/stage.SUFFIX/'4_before_rsz_lec.v',directory/'results'/stage.SUFFIX/'4_after_rsz_lec.v')
        boolean.append(dict(task=t['id'],checked_FF_bits=proof['checked_FF_bits'],CEC=True));tasks.append(t)
    names=stage.dependencies()
    for n,h in names.items():
        d=root/'source'/n;d.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(stage.ROOT/n,d)
    write(root/'admission.json',dict(version='alternate-multiclock-readout-v1',id=root.name,tasks=tasks,sources=names,
        freeze_path=str(stage.FREEZE),freeze_sha256=sha(stage.FREEZE),policy_path=str(stage.POLICY_PATH),policy_sha256=sha(stage.POLICY_PATH),
        synth_max=0,grt_max=0,support_max=64,parent_physical_admission=str(physical/'admission.json'),parent_physical_admission_sha256=sha(physical/'admission.json'),
        first_validation=str(first/'analysis-v1/validation.json'),first_validation_sha256=sha(first/'analysis-v1/validation.json'),parameters_changed=False,full_D_ready=False))
    write(root/'progress.json',dict(phase='physical_batch_complete',inherited_alternate_snapshots=9,new_physical_calls=0))
    write(root/'state-proof-summary.json',dict(status='passed_actual_alternate_state_and_CEC',rows=boolean,logical_FF_checks=sum(r['checked_FF_bits'] for r in boolean),full_D_ready=False))
    reader=stage.ROOT/'experiments/arithmetic_dse/stage67_physical_readout_v4.py';write(root/'readout-implementation.json',dict(path=str(reader),sha256=sha(reader),registered_before_first_readout=True))
    print('ALTERNATE_REPORT_ADMITTED cases=9 state_CEC=passed no_new_EDA=1',flush=True)


def combined(first,second,out):
    if out.exists():raise ValueError('preserve paired final judgment')
    a=read(first/'analysis-v1/validation.json');b=read(second/'analysis-v1/validation.json')
    if any(p['placement']!='placement-0' for p in a['points']) or any(p['placement']!='placement-1' for p in b['points']):raise ValueError('paired placements differ from declared inventory')
    points=deepcopy(a['points']+b['points']);stages=[s for p in points for s in p['stages']]
    # Inherited and newly measured variants have exactly the same source role,
    # combinational source bytes, target T, L=2, II=1 and service protocol.
    for source in {p['source'] for p in points}:
        old=read(stage.PARENT/'preparation-v2/sources'/source/'request.json');new=read(first/'paired-software/sources'/source/'request.json')
        if old['source_sha256']!=new['source_sha256'] or old['role']!=new['role'] or old['role']!='validation':raise ValueError('source or role changed across pair')
    timing=stats([s['relative_error'] for s in stages]);area=stats([p['total_area']['relative_error'] for p in points]);failures=[]
    if timing['median']>.15 or timing['P95']>.35:failures.append('paired_complete_stage_error')
    if area['median']>.15 or area['P95']>.35:failures.append('paired_total_area_error')
    failures.extend(a['failures']);failures.extend(b['failures']);ranking=[]
    for source,t in sorted({(p['source'],p['target_ps']) for p in points}):
        pair=[p for p in points if (p['source'],p['target_ps'])==(source,t)]
        if len(pair)!=2:raise ValueError('exact two variants required per source/T')
        def key(p,pred):
            feasible=p['predicted_setup_feasible' if pred else 'observed_setup_feasible'];return (not feasible,0 if feasible else p['predicted_violation_ps' if pred else 'observed_violation_ps'],p['total_area']['predicted' if pred else 'observed'])
        predicted=[p['placement'] for p in sorted(pair,key=lambda p:key(p,True))];observed=[p['placement'] for p in sorted(pair,key=lambda p:key(p,False))]
        x,y=pair;ar=abs(x['total_area']['observed']-y['total_area']['observed'])/max(x['total_area']['observed'],y['total_area']['observed'])
        samefeasible=x['observed_setup_feasible']==y['observed_setup_feasible'];vt=abs(x['observed_violation_ps']-y['observed_violation_ps'])<=5
        tied=samefeasible and ar<=.05 and (x['observed_setup_feasible'] or vt)
        agrees=predicted==observed
        ranking.append(dict(source=source,target_ps=t,predicted=predicted,observed=observed,agrees=agrees,within_observed_tie_band=tied,observed_relative_area_difference=ar,
            predicted_selection=predicted[0],observed_selection=observed[0]))
        if not agrees and not tied:failures.append(source+'/T'+str(t)+'/non_tied_ranking_disagreement')
    bank_classes={}
    for name,first_stage in [('S_only_input_service_to_native',0),('S_only_native_to_external',1)]:
        values=[r['relative_error'] for p in points for r in p['banks'] if not r['arithmetic_path'] and r['stage']==first_stage]
        if values:bank_classes[name]=stats(values)
    owners={n:stats([p['owner_errors'][n]['relative_error'] for p in points]) for n in points[0]['owner_errors']}
    failures=list(dict.fromkeys(failures));out.mkdir(parents=True)
    result=dict(version='frozen-paired-multiclock-validation-v1',status='failed_paired_stage_validation' if failures else 'passed_paired_stage_validation_not_independent',
        complete_stage_error=timing,total_area_error=area,owner_area_error=owners,bank_class_error=bank_classes,failures=failures,points=points,ranking=ranking,
        false_feasible_count=sum(p['whole_shell_false_feasible'] for p in points),conservative_rejection_count=sum(p['conservative_rejection'] for p in points),
        hold_negative_count=sum(p['whole_shell']['hold_worst_slack_ps']<0 for p in points),non_tied_rank_disagreements=sum(not r['agrees'] and not r['within_observed_tie_band'] for r in ranking),
        structure_classes=['parallel independent products','wide reduction','serial'],unqualified_remaining_classes=['shared arithmetic node','explicit bypass','cross-stage saved/reconvergent value'],
        exact_Ts=[500,1500,3000],reserve_ps=50,G_delay_ps=0,parameters_changed=False,independent_tests_unlocked=False,zero_G_joint_qualified=False,full_D_ready=False)
    write(out/'validation.json',result);print({k:result[k] for k in ('status','complete_stage_error','total_area_error','failures','false_feasible_count','conservative_rejection_count','non_tied_rank_disagreements')},flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','combined'));p.add_argument('--first',type=Path,required=True);p.add_argument('--root',type=Path);p.add_argument('--second',type=Path);p.add_argument('--out',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.first.resolve(),a.root.resolve())
    else:combined(a.first.resolve(),a.second.resolve(),a.out.resolve())
