"""Software-only source split, unseen query and actual scan execution gates."""
import argparse
from copy import deepcopy
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha,key
from experiments.arithmetic_dse import operator_collection as collect
from experiments.arithmetic_dse import model_three_region_scan as scan
from experiments.arithmetic_dse import operator_query


def verify(folder,out):
    out.mkdir(parents=True,exist_ok=False);m=read(folder/'manifest.json');rows=m['sources'];roles={r['source_group']:r['role'] for r in rows}
    if len(roles)!=len(rows) or {role:sum(r['role']==role for r in rows) for role in roles.values()}!={'train':30,'validation':14,'locked_test':14}:raise ValueError('source split incomplete or leaked')
    expected=collect.sources()
    if expected!=[{k:v for k,v in row.items() if k not in ('rtl_sha256','contract_sha256')} for row in rows]:raise ValueError('source-role/required-shape regeneration differs')
    for row in rows:
        if row['predecessor_role'] and row['role']!=row['predecessor_role']:raise ValueError('source role changed')
        if sha(folder/'sources'/row['id']/'input.sv')!=row['rtl_sha256']:raise ValueError('source bytes changed')
        if collect.planned_domain(collect.descriptor(row,1500))['production_status']!='cost_uncovered':raise ValueError('planned scope falsely production-qualified')
    train=next(r for r in rows if r['role']=='train');test=next(r for r in rows if r['role']=='locked_test');rejected=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError):rejected.append(name)
        else:raise ValueError('execution guard accepted '+name)
    reject('locked_test_before_freeze',lambda:collect.next_request(folder,test['id'],[]))
    fake=out/'false-freeze.json';write(fake,dict(validation_passed=True,source_manifest_sha256=sha(folder/'manifest.json'),model_sha256='not-a-model',test_consumed=False))
    reject('boolean_only_test_freeze',lambda:collect.next_request(folder,test['id'],[],fake))
    no_release=out/'not-admitted.json';write(no_release,dict(version='operator-stage4-admission-v1',physical_admission_allowed=False,source_manifest_sha256=sha(folder/'manifest.json')))
    reject('formal_EDA_before_stage4',lambda:collect.execute_next(folder,train['id'],out/'must-not-execute',no_release))
    missing=out/'incomplete-admission.json';write(missing,dict(version='operator-stage4-admission-v1',physical_admission_allowed=True,
        source_manifest_sha256=sha(folder/'manifest.json'),measurement_source_sha256={},
        source_target_requests=[dict(source_id=train['id'],role='train',SDC_ps=1500,ABC_ps=1500)]))
    reject('formal_EDA_with_missing_producer_freeze',lambda:collect.execute_next(folder,train['id'],out/'must-not-execute',missing))
    if not all((ROOT/name).is_file() for name in collect.measurement_sources()):raise ValueError('required runtime source absent')
    if (out/'must-not-execute').exists():raise ValueError('denied execution created physical task')
    first=collect.next_request(folder,train['id'],[])['decision']['next_request']
    history=[dict(**first,status='failed',source_id=train['id'],role=train['role'],failure_reason='synthetic timeout fixture; no EDA executed')]
    stopped=collect.next_request(folder,train['id'],history)['decision']
    if stopped['next_request'] is not None or stopped['eligible_rows_retained']:raise ValueError('failed row retried or created labels')
    bad=deepcopy(history);bad[0]['role']='validation';reject('same_source_role_mutation',lambda:collect.next_request(folder,train['id'],bad))
    q=collect.descriptor(train,1500);new=deepcopy(q);new['local_context']['producer'].update(lhs_width=11,rhs_width=19,result_width=30,lhs_zero_hex='0x0',lhs_one_hex='0x0',rhs_zero_hex='0x0',rhs_one_hex='0x0',operation='mul');new['declared_result_width']=30;new['required_result_bits']=list(range(30));new['local_context']['consumers']=[];new['local_context']['captures']=[dict(banks=1,declared_width=30,result_bit_map=list(range(30)))]
    if collect.planned_domain(new)['status']!='candidate_semantic_domain_only':raise ValueError('unseen exact width pair blocked by shape-ID lookup')
    feature_before=operator_query.features(new);renamed=deepcopy(new);renamed['flow_context']['profile_sha256']='same-semantic-profile-identity-for-name-fixture'
    if operator_query.features(renamed)!=feature_before:raise ValueError('opaque identity became numerical feature')
    reject('posterior_feature',lambda:operator_query.features({**new,'slack':1}))
    write(out/'proof.json',dict(status='passed',sources=len(rows),counts={'train':30,'validation':14,'locked_test':14},negative_guards=rejected,
        unseen_shape_is_not_exact_ID_lookup=True,source_roles_and_required_shapes_regenerated=True,failure_stops_without_zero_label=True,formal_EDA_executed=False,test_labels_read=False))
    print(read(out/'proof.json'),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--folder',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();verify(a.folder.resolve(),a.out.resolve())
