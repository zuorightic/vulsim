"""Prospective protocol acceptance; artificial test freezes stay in temp roots."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil
import sys
import tempfile
from types import FunctionType

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha,key
from experiments.arithmetic_dse import operator_condition_wide as wide
from experiments.arithmetic_dse import operator_stage4 as stages
from experiments.arithmetic_dse.budget import Ledger,usage


def gates(root,sampler,out):
    if out.exists():raise ValueError('preserve acceptance attempts')
    out.mkdir(parents=True)
    passed=[]
    def reject(name,fn):
        try:fn()
        except (ValueError,KeyError,FileNotFoundError):passed.append(name)
        else:raise ValueError('gate accepted '+name)
    proof=read(sampler);wide.validate_sampler_proof(proof)
    for field in ('producer_sha256','policy_sha256','parent_sampler_sha256','parent_sampler_policy_sha256'):
        bad=deepcopy(proof);bad[field]='0'*64
        reject('sampler_'+field,lambda:wide.validate_sampler_proof(bad))
    for name,change in (('missing_negative',lambda p:p['negative_checks'].pop()),
                        ('duplicate_negative',lambda p:p['negative_checks'].__setitem__(0,p['negative_checks'][1])),
                        ('fit_interpolation_leak',lambda p:p['cases'][0]['targets'].__setitem__(-1,1000)),
                        ('wrong_guard_order',lambda p:p['cases'][0]['targets'].reverse()),
                        ('missing_role',lambda p:p['cases'].pop())):
        bad=deepcopy(proof);change(bad)
        reject(name,lambda:wide.validate_sampler_proof(bad))
    # Exercise the rare reserved-target branch independently of real measurements.
    namespace=dict(wide.guarded_next.__globals__)
    class Scan:
        number=wide.scan.number
        @staticmethod
        def policy():return wide.scan.policy()
        @staticmethod
        def _next(*args):return dict(SDC_ps=1000,ABC_ps=1000,proposal='fixture',reference_ratio=None)
    namespace['scan']=Scan
    guarded=FunctionType(wide.guarded_next.__code__,namespace)
    rows=[dict(SDC_ps=t,status='completed') for t in (1500,500,3000)]
    proposal=guarded(rows,'train',wide.scan.policy())
    if (proposal['SDC_ps'],proposal['ABC_ps'],proposal['proposal'])!=(1001,1001,'reserved_target_nudge'):
        raise ValueError('reserved-target nudge differs')
    if guarded(rows+[dict(SDC_ps=1100+i,status='completed') for i in range(10)],'train',wide.scan.policy()) is not None:
        raise ValueError('13 point cap bypassed')
    passed.extend(('reserved_target_nudge','thirteen_point_cap'))
    manifest=read(root/'corpus/manifest.json')
    # Metadata fixtures test admission logic, never a fitted model or real test.
    with tempfile.TemporaryDirectory(prefix='test-freeze-fixture-',dir=out) as temporary:
        temp=Path(temporary);folder=temp/'corpus';folder.mkdir()
        write(folder/'manifest.json',manifest);write(temp/'fit-data.json',dict(fixture=True))
        parent=temp/'ancestor';parent.mkdir();write(temp/'collection.json',dict(parent_collection_root=str(parent)))
        sources={name:sha(ROOT/name) for name in read(wide.FIT_PROTOCOL)['required_freeze_sources']}
        model=dict(version='operator-condition-function-v1',quality_status='awaiting_independent',
            source_manifest_sha256=sha(folder/'manifest.json'),fit_dataset_sha256=sha(temp/'fit-data.json'),
            profile_sha256=manifest['profile_sha256'],feature_protocol_sha256=sha(wide.FEATURE_PROTOCOL),
            fit_protocol_sha256=sha(wide.FIT_PROTOCOL),full_D_ready=False,
            operations={op:dict(status='awaiting_independent') for op in ('mul','add')})
        write(temp/'model.json',model)
        validation=dict(status='passed',model_sha256=sha(temp/'model.json'),source_manifest_sha256=sha(folder/'manifest.json'))
        write(temp/'validation.json',validation)
        freeze=dict(validation_passed=True,test_consumed=False,source_manifest_sha256=sha(folder/'manifest.json'),
            fit_dataset_sha256=sha(temp/'fit-data.json'),implementation_sources=sources,
            fit_producer='experiments/arithmetic_dse/operator_condition_fit.py',model_path='model.json',
            validation_path='validation.json',model_sha256=sha(temp/'model.json'),validation_sha256=sha(temp/'validation.json'),
            fit_protocol_sha256=sha(wide.FIT_PROTOCOL))
        path=temp/'freeze.json';write(path,freeze);wide.verify_selection(folder,path)
        for name,change in (
            ('stale_implementation',lambda p:p['implementation_sources'].update({next(iter(sources)):'0'*64})),
            ('missing_implementation',lambda p:p['implementation_sources'].pop(next(iter(sources)))),
            ('missing_fitter',lambda p:p.update(fit_producer=None)),
            ('wrong_model',lambda p:p.update(model_sha256='0'*64)),
            ('wrong_validation',lambda p:p.update(validation_sha256='0'*64)),
            ('wrong_dataset',lambda p:p.update(fit_dataset_sha256='0'*64)),
            ('wrong_manifest',lambda p:p.update(source_manifest_sha256='0'*64)),
            ('consumed_boolean',lambda p:p.update(test_consumed=True)),
            ('validation_false',lambda p:p.update(validation_passed=False)),
            ('old_fit_freeze',lambda p:p.update(fit_protocol_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/operator_condition_fit_v1.json')))):
            bad=deepcopy(freeze);change(bad);write(path,bad)
            reject(name,lambda:wide.verify_selection(folder,path))
        for name,change in (
            ('failed_model_quality',lambda p:p.update(quality_status='failed')),
            ('failed_operation_quality',lambda p:p['operations']['mul'].update(status='failed')),
            ('old_features',lambda p:p.update(feature_protocol_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/operator_condition_features_v1.json'))),
            ('old_fit_model',lambda p:p.update(fit_protocol_sha256='0'*64)),
            ('wrong_profile',lambda p:p.update(profile_sha256='0'*64)),
            ('incomplete_operations',lambda p:p['operations'].pop('mul'))):
            bad=deepcopy(model);change(bad);write(temp/'model.json',bad)
            f=deepcopy(freeze);f['model_sha256']=sha(temp/'model.json')
            v=dict(validation,model_sha256=f['model_sha256']);write(temp/'validation.json',v)
            f['validation_sha256']=sha(temp/'validation.json');write(path,f)
            reject(name,lambda:wide.verify_selection(folder,path))
        write(temp/'model.json',model);write(temp/'validation.json',validation);write(path,freeze)
        for directory,name in ((temp,'consumed_marker'),(parent,'ancestor_consumed_marker')):
            marker=directory/'independent-evaluation-consumed.json';write(marker,{})
            reject(name,lambda:wide.verify_selection(folder,path));marker.unlink()
    locked=next(r for r in manifest['sources'] if r['role']=='locked_test')
    reject('real_locked_source_without_freeze',lambda:wide.adapter(root/'corpus').next_request(root/'corpus',locked['id'],[]))
    for row in manifest['sources']:
        if row['role']=='locked_test' and (root/'raw'/row['id']).exists():raise ValueError('real physical test touched')
    result=dict(status='passed',negative_and_edge_checks=passed,count=len(passed),fixture_test_freeze_positive=True,
        actual_locked_source_refused_before_creation=True,real_test_physical_dirs=0,new_EDA_calls=0,
        physical_test_labels_read=False,sampler_sha256=sha(sampler),full_D_ready=False)
    write(out/'proof.json',result);print(dict(status='passed',gate_checks=len(passed)),flush=True)


def amend(root,work):
    active=read(root/'active-collection.json');oldpath=root/active['path'];old=read(oldpath)
    if read(root/'progress.json')['phase'] not in ('fitting_bounded_batch_complete','batch_settled'):
        raise ValueError('settled bounded batch required')
    if any(j['status']=='unsettled' for j in read(Ledger().path).get('jobs',[])):raise ValueError('unsettled jobs')
    # All original measurement dependencies must still be identical.
    drift=[n for n,h in old['measurement_sources'].items() if sha(ROOT/n)!=h]
    if drift!=['experiments/arithmetic_dse/operator_condition_wide.py']:raise ValueError('unexpected measurement drift '+str(drift))
    for n,h in old['measurement_sources'].items():
        if sha(root/old['source_freeze_directory']/n)!=h:raise ValueError('historical freeze modified')
    bindings={str(p):sha(p) for p in (work/'feature-vectors-v2/demand-audit.json',work/'feature-vectors-v2/feature-proof.json',work/'gates-v1/proof.json',work/'sampler-proof-v4.json')}
    for p in bindings:
        if read(p).get('status') not in ('passed','passed_interface_expressibility'):raise ValueError('acceptance proof failed')
    freeze=root/'measurement-source-amendment-2'
    if freeze.exists():raise ValueError('preserve successor freeze')
    hashes={}
    for name in sorted(set(old['measurement_sources'])|{str(p.relative_to(ROOT)) for p in (wide.FIT_PROTOCOL,wide.FEATURE_PROTOCOL)}):
        dest=freeze/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(ROOT/name,dest);hashes[name]=sha(dest)
    fit=root/'fit-protocol-v2.json';shutil.copy2(wide.FIT_PROTOCOL,fit)
    addendum=root/'steps123-addendum-v2.json'
    write(addendum,dict(version='steps123-wide-incremental-v2',parent_config_sha256=sha(oldpath),
        purpose='general operator function plus S/DAG; no per-view prices',proof_bindings=bindings,
        new_roles=old['new_source_counts'],inherited_roles_immutable=True,all_locked_test_sources=18,
        formal_clock_checks_ps=[500,1500,3000],independent_reserved_exact_T_ps=1000,
        quality='unchanged source macro median<=15%, P95<=35%, per-op P95<=50%; coverage/refusal separate; stage5 still pending',
        qualification='existing three Add points plus at most three fitting-role pilot points; no repeated stages',
        max_additional_qualification_targets=3,max_synth=3,max_grt=3,max_physical_leaf_wall_s=8820,
        max_physical_CPU_s=35280,working_and_archive_budget_bytes=8*1024**3,
        full_collection_ceiling_is_not_admission=True,later_work_reserved=old['later_work_reserved'],
        unmeasured_contexts_unqualified=True,test_still_locked=True,full_D_ready=False))
    cfg=dict(old,measurement_sources=hashes,source_freeze_directory=freeze.name,
        parent_active_config_path=active['path'],parent_active_config_sha256=sha(oldpath),
        amendment_reason='Prospective consumer numerical features, guarded clocks and full software/test admission; preserve first batch and all roles',
        feature_protocol_sha256=sha(wide.FEATURE_PROTOCOL),fit_protocol_sha256=sha(wide.FIT_PROTOCOL),
        fit_protocol_path=fit.name,incremental_acceptance_addendum_sha256=sha(addendum),acceptance_proofs=bindings)
    path=root/'amendments/steps123-incremental-002.json';write(path,cfg)
    stages.archive(root,[freeze,path,fit,addendum],'steps123-incremental-source-freeze-v2.tar.gz')
    stages.atomic(root/'active-collection.json',dict(path=str(path.relative_to(root)),sha256=sha(path)))
    wide.verify_measurement_sources(root)
    print(dict(status='successor_frozen',measurement_sources=len(hashes),original_dependencies_unchanged=93),flush=True)


def admission(root,out):
    if out.exists():raise ValueError('preserve acceptance attempt')
    out.mkdir(parents=True)
    accepted=wide.validate_admission(root);checks=[]
    with tempfile.TemporaryDirectory(prefix='admission-fixture-',dir=out) as directory:
        temp=Path(directory)
        for name in ('corpus','amendments','measurement-source-amendment-2','new-sources.json'):
            (temp/name).symlink_to(root/name,target_is_directory=(root/name).is_dir())
        shutil.copy2(root/'active-collection.json',temp/'active-collection.json')
        def test(name,change):
            bad=deepcopy(accepted);change(bad);path=temp/'admission.json';write(path,bad)
            write(temp/'active-software-admission.json',dict(path=path.name,sha256=sha(path)))
            try:wide.validate_admission(temp)
            except (ValueError,KeyError):checks.append(name)
            else:raise ValueError('admission accepted '+name)
        test('incomplete_inventory',lambda p:p['proof_files'].pop(next(iter(p['proof_files']))))
        test('changed_inventory_hash',lambda p:p['proof_files'].update({next(iter(p['proof_files'])):'0'*64}))
        test('wrong_source_count',lambda p:p.update(software_sources=15))
        test('wrong_cycle_count',lambda p:p.update(cycles_each=1))
        test('stale_producer',lambda p:p.update(producer_sha256='0'*64))
        test('old_fit_protocol',lambda p:p.update(fit_protocol_sha256='0'*64))
        test('old_features',lambda p:p.update(feature_protocol_sha256='0'*64))
    write(out/'proof.json',dict(status='passed',checks=checks,count=len(checks),
        positive_sources=accepted['software_sources'],cycles_each=accepted['cycles_each'],bound_proof_files=len(accepted['proof_files']),
        new_EDA_calls=0,physical_test_labels_read=False,full_D_ready=False))
    print(dict(status='passed',negative_admission_checks=len(checks)),flush=True)


def pilot(root,out):
    wide.validate_admission(root)
    rows=read(root/'new-sources.json')['sources'];train=[r for r in rows if r['role']=='train']
    mul=[r for r in train if r['features']['producer']['operation']=='mul']
    # Selection depends only on structural dimensions, never observed prices.
    largest=max(mul,key=lambda r:r['features']['producer']['lhs_width']*r['features']['producer']['rhs_width'])
    small=[r for r in mul if r['features']['producer']['lhs_width']==8]
    shifted=max(small,key=lambda r:max(c['spec']['result_width'] for c in r['features']['consumers']))
    adds=[r for r in train if r['features']['producer']['operation']=='add' and (root/'raw'/r['id']/'history.json').exists()]
    add=max(adds,key=lambda r:r['features']['producer']['result_width'])
    requests=[]
    for r,target in ((largest,1500),(shifted,1500),(add,500)):
        history=root/'raw'/r['id']/'history.json';history=read(history) if history.exists() else []
        q=wide.adapter(root/'corpus').next_request(root/'corpus',r['id'],history)['decision']['next_request']
        if q is None or q['SDC_ps']!=target:raise ValueError('planned qualification not next deterministic request')
        requests.append(dict(source_id=r['id'],role=r['role'],SDC_ps=target,ABC_ps=target,
            structural_features=r['features'],purpose='dual-use qualification/capacity pilot; original fitting role unchanged'))
    write(out,dict(version='steps123-limited-qualification-v2',requests=requests,max_batches=1,
        no_test_sources=True,no_bulk_collection=True,no_price_based_source_selection=True,full_D_ready=False))
    print(dict(requests=[(r['source_id'],r['SDC_ps']) for r in requests]),flush=True)


def audit(root,work,out):
    cfg=wide.verify_measurement_sources(root);wide.validate_admission(root)
    parent=Path(cfg['parent_collection_root']);old=stages.verify_sources(parent)
    if len(old['measurement_sources'])!=93:raise ValueError('original measurement scope changed')
    if sha(parent/'fit-v1/candidate.json')!='a9d8f8739722352f536bb2e69aaaf0605318dc5150187aba9abdbf25702c1ad1':
        raise ValueError('original candidate bytes changed')
    sources=read(root/'corpus/manifest.json')['sources'];byid={r['id']:r for r in sources}
    for row in read(parent/'corpus/manifest.json')['sources']:
        if row!=byid[row['id']]:raise ValueError('inherited source or role changed')
    for row in sources:
        if row['role']=='locked_test' and (root/'raw'/row['id']).exists():raise ValueError('physical test touched')
    if any((r/'independent-evaluation-consumed.json').exists() for r in (root,parent)):
        raise ValueError('independent test consumed')
    original_data=read(parent/'fit-data.json')['rows']
    if any(r['target_ps']==1000 for r in original_data):raise ValueError('reserved exact T already in original fitting')
    progress=read(root/'progress.json')
    if progress['phase']!='fitting_bounded_batch_complete' or progress['completed_points']!=411 or progress['errors']:
        raise ValueError('limited collection not cleanly settled')
    result=dict(status='passed',original_measurement_dependencies_unchanged=93,current_frozen_dependencies=97,
        inherited_source_roles_and_bytes_unchanged=58,total_sources=74,locked_test_sources_untouched=18,
        original_candidate_sha256=sha(parent/'fit-v1/candidate.json'),total_valid_raw_points=411,
        original_fitting_dataset_rows=len(original_data),original_training_has_exact1000ps=False,
        no_new_model_fitted=True,no_independent_evaluation=True,full_D_ready=False,
        frozen_S_sha256=sha(ROOT/'experiments/arithmetic/evidence/step7_general_state_v1/asap7-general-state.json'))
    write(out,result);print(result,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('gates','amend','admission','pilot','audit'))
    for name in ('root','sampler','out','work'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if a.action=='gates':gates(a.root.resolve(),a.sampler.resolve(),a.out.resolve())
    elif a.action=='amend':amend(a.root.resolve(),a.work.resolve())
    elif a.action=='admission':admission(a.root.resolve(),a.out.resolve())
    elif a.action=='pilot':pilot(a.root.resolve(),a.out.resolve())
    else:audit(a.root.resolve(),a.work.resolve(),a.out.resolve())
