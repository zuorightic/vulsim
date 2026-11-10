"""Source-role/quality freeze and freeze-gated bounded collection interface.

prepare/next are software only. execute-next requires a separate stage-4
admission and verifies the exact sampler proposal before spending EDA resources.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .model_fast_preflight import read,write,sha,key
from .model_fast_samples import from_shape
from .model_context_samples import independent_context,layout
from . import model_sampling_v2 as samples
from . import model_three_region_scan as scan
from . import operator_query

ROOT=Path(__file__).resolve().parents[2]


def measurement_sources():
    """Required runtime producers; an empty/subset hash map cannot release EDA."""
    names=('operator_collection.py operator_query.py model_three_region_scan.py '
        'model_steps123_qualification.py model_sampling_v2.py model_context_samples.py '
        'model_fast_samples.py model_samples.py model_fast_preflight.py model_fast_sdc.py '
        'model_mapped_contract.py model_qualification_labels.py model_physical_labels_v2.py '
        'model_physical_path_v2.py model_context_labels.py model_fast_path.py '
        'model_reference_labels.py model_m2_mux_collection.py model_m2_live_cec_v3.py '
        'model_m2_aig.py model_m2_state.py model_m2_cec.py backend.py platforms.py '
        'platform_probe.py budget.py processes.py sdc.py sdc_storage_v3.py characterization.py').split()
    # Include local Python dependencies transitively, including function-local
    # imports used only after admission. Do not execute a module to discover it.
    import ast
    paths=[];pending=[Path(__file__).with_name(name) for name in names];seen=set()
    while pending:
        path=pending.pop()
        if path in seen:continue
        seen.add(path);paths.append(path)
        for node in ast.walk(ast.parse(path.read_text())):
            if isinstance(node,ast.ImportFrom) and node.level==1:
                modules=([node.module.split('.')[0]] if node.module else [n.name for n in node.names])
                for module in modules:
                    dependency=path.with_name(module+'.py')
                    if dependency.is_file():pending.append(dependency)
    paths += [p for p in (Path(__file__).parent/'backend').iterdir() if p.is_file()]
    paths += [Path(__file__).parent/'reference_assets'/name for name in ('context_readout_v2.tcl','boundary_census.tcl')]
    paths += [scan.CONFIG,ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json']
    return sorted(str(p.relative_to(ROOT)) for p in paths)


def canonical_features(features):
    result=deepcopy(features)
    for spec in [result['producer']]+[c['spec'] for c in result['consumers']]:
        for prefix in ('lhs','rhs'):
            for bit in ('zero','one'):spec[prefix+'_'+bit+'_hex']=hex(int(spec.get(prefix+'_'+bit+'_hex','0'),16))
        spec.setdefault('carry','zero');spec.setdefault('capture_banks',1)
    return result


def sources():
    from regression.arithmetic_target_round1 import cohort,capacity_sources
    old=cohort(read(ROOT/'experiments/arithmetic/evidence/step7_fast_loads_v1/loads.json'))
    roles={key(canonical_features(r['features'])):r['role'] for r in old}
    diagnostic={key(canonical_features(r['features'])) for r in capacity_sources()}
    rows=[];seen=set()
    def add(features,role,why):
        features=canonical_features(features);signature=key(features)
        if signature in diagnostic:raise ValueError('diagnostic source cannot change role')
        if signature in roles and roles[signature]!=role:raise ValueError('frozen source role cannot change')
        if signature in seen:return
        seen.add(signature);samples.geometry_contract(features)
        rows.append(dict(id='s'+signature[:16],source_group=signature,role=role,features=features,purpose=why,
            predecessor_role=roles.get(signature),boundary_policy='unsigned-op-hierarchy-v1'))
    required=read(ROOT/'experiments/arithmetic/evidence/step7_fast_preflight_v3/requirements.json')
    # One minimal load per required operator shape, not one predictor per shape.
    for item in required['operator_shapes'].values():
        spec=from_shape(item['shape']);r=spec['result_width'];add(dict(producer=spec,consumers=[],captures=[dict(banks=1,declared_width=r,result_bit_map=list(range(r)))]),'train','required arithmetic shape, direct observable capture')
    for w in (8,16,32):
        spec=dict(operation='mul',lhs_width=w,rhs_width=w,result_width=2*w,carry='zero',capture_banks=1)
        add(dict(producer=spec,consumers=[],captures=[dict(banks=2,declared_width=2*w,result_bit_map=list(range(2*w)))]),'train','load/bank variation at supported multiplication width')
        add(independent_context(spec,6),'train','new consumer load without copying complete MAC graph')
        low={**spec,'result_width':w};add(dict(producer=low,consumers=[],captures=[dict(banks=1,declared_width=w,result_bit_map=list(range(w)))]),'train','finite low-result multiplication response')
    for a,b in ((8,16),(16,24)):
        spec=dict(operation='mul',lhs_width=a,rhs_width=b,result_width=a+b,carry='zero',capture_banks=1)
        add(dict(producer=spec,consumers=[],captures=[dict(banks=1,declared_width=a+b,result_bit_map=list(range(a+b)))]),'train','asymmetric operand training support')
    for row in old:
        if row['role'] in ('validation','locked_test'):add(row['features'],row['role'],'preserve prior unconsumed held-out local source role')
    for role,pairs in [('validation',[(12,20,32),(15,27,19)]),('locked_test',[(13,17,11),(9,23,32)])]:
        for a,b,r in pairs:
            spec=dict(operation='mul',lhs_width=a,rhs_width=b,result_width=r,carry='zero',capture_banks=1)
            add(independent_context(spec,4 if role=='validation' else 5),role,'preregister unseen asymmetric/result shape and connection')
    return rows


def descriptor(row,target):
    f=row['features'];r=f['producer']['result_width']
    return dict(version=operator_query.VERSION,semantics='unsigned-modulo-v1',declared_result_width=r,required_result_bits=list(range(r)),local_context=f,
        topology=dict(operand_shared_input_roots=0,same_stage_remaining_depth=1+bool(f['consumers'])),
        flow_context=dict(target_platform='asap7',evaluation_stage='grt',target_period_ps=target,abc_target_ps=target,
            profile_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json'),boundary_policy='unsigned-op-hierarchy-v1'))


def planned_domain(query):
    """Semantic candidate support only. Actual fitted qualification is separate."""
    try:f=operator_query.features(query)
    except (ValueError,KeyError,TypeError):return dict(status='cost_uncovered',reason='invalid_or_unsupported_semantics')
    op=query['local_context']['producer']['operation']
    if op not in ('mul','add') or (op=='mul' and max(f['lhs_width'],f['rhs_width'])>32) or (op=='add' and max(f['lhs_width'],f['rhs_width'])>67) or f['result_width']>65:
        return dict(status='cost_uncovered',reason='outside_first_model_semantic_width_scope')
    if f['lhs_one_count'] or f['rhs_one_count'] or f['carry_dynamic'] or f['carry_one']:
        return dict(status='cost_uncovered',reason='known_one_or_nonzero_carry_not_in_first_collection')
    if f['consumer_mul'] or f['consumer_addcarry'] or f['consumer_count']>1:
        return dict(status='cost_uncovered',reason='consumer_semantics_outside_first_local_domain')
    if not 25<=f['target_period_ps']<=12000:return dict(status='cost_uncovered',reason='outside_registered_sampling_envelope')
    return dict(status='candidate_semantic_domain_only',production_status='cost_uncovered',
        reason='fit, independent function domain and complete-stage qualification not yet available; no exact shape/consumer-ID lookup')


def prepare(folder):
    rows=sources();folder.mkdir(parents=True,exist_ok=False);feature_names=set()
    for row in rows:
        d=folder/'sources'/row['id'];d.mkdir(parents=True);(d/'input.sv').write_text(samples.source(row['features']));write(d/'contract.json',samples.geometry_contract(row['features']))
        row['rtl_sha256']=sha(d/'input.sv');row['contract_sha256']=sha(d/'contract.json');feature_names.update(operator_query.features(descriptor(row,1500)))
    protocol=read(ROOT/'experiments/arithmetic_dse/configs/model_target_round1_v1.json')
    protocol.update(version='arithmetic-operator-collection-protocol-v2',scope='steps123 successor: shared function interface and minimal fixed source roles; no stage4 admission',
        revision=4,flow_context=dict(target_platform='asap7',evaluation_stage='grt',profile_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json'),
            operator_boundary_policy='unsigned-op-hierarchy-v1',ABC_equals_SDC=True,IO='0.2T',source_generator_sha256=sha(Path(samples.__file__))),
        source_roles='see explicit immutable source groups, all target/stage/repeat variants inherit role',
        S_G_order='software interleaved; formal residuals and independent evaluation retain frozen dependencies',
        operator_query_schema=operator_query.VERSION,operator_boundary_policy='unsigned-op-hierarchy-v1',sampler_sha256=sha(scan.CONFIG),
        source_counts={role:sum(r['role']==role for r in rows) for role in ('train','validation','locked_test')},
        feature_schema=dict(available=sorted(feature_names),excluded_from_operator_predictor=['declared_result_width','operand_shared_input_roots','same_stage_remaining_depth'],
            exclusion_reason='price models use canonical demanded precision; declaration-only padding remains in semantic certificates; upstream correlation/longer topology require G checks'),
        measurement_boundary=dict(capture='unconditional, separately observable FF bank adapter',launch='registered data with explicit valid/enable/reset protocol',
            native_S_G_note='actual native enable/reset/capture loading does not automatically inherit this local measurement scope; explicit S/G joint-domain validation required',
            native_padding_note='declaration-only padding is not a learned extrapolation input; validate canonicalization/implementation effects in real composition before production pricing'),
        function_support='semantic operation/width/result/mask/load rules and source-neighbor support selected with validation, frozen before test; no shape-ID price table',
        reserved_generalization=['non-aligned/asymmetric operand widths','unseen low result and known-bit pattern','unseen consumer wiring','new exact target within supported training interval'],
        static_ablation=dict(required=True,scope='same views/T/L/II/search/ranking; only cost function or explicitly dependency-complete cost package differs',
            delay_unit_bridge='single nonnegative global alpha_d from source-equal train least squares through origin on fixed delay proxy',
            area_unit_bridge='single nonnegative global alpha_A from source-equal train least squares through origin on fixed area proxy',
            G='prefer common zero correction; never transplant base-dependent residual between models'),
        capacity=dict(status='finite diagnostic qualification complete; formal source/target admission still separate',
            role='not_training',successor_source_targets=['mul-load-1500','mul-load-750','sparse-add-250','wide-add-750'],
            earlier_synth_only_boundary_points=2,total_preparation_points=6,automatic_retries=0,
            synth_timeout_s=300,grt_timeout_s=1200,memory_limit_MiB=8192,parallel_jobs_max=3,
            measured_plan='steps123 evidence capacity-plan.json; measurements do not qualify arbitrary tighter targets'),
        collection_execution=dict(first_batch_source_targets_max=12,formal_roles=['train','validation'],locked_test_separate=True,
            shared_source_freeze_per_admission=True,exact_sampler_requests_required=True,
            runtime_producer_hashes_and_qualification_receipt_required=True,live_later_work_and_storage_reserve_required=True,
            total_train_validation_target_ceiling=572,total_locked_test_target_ceiling=182,
            ceiling_is_not_admission=True,persistent_artifact_destination_and_restore_receipt='required by batch storage protocol; not yet selected'),
        physical_admission_allowed=False,independent_test_allowed=False,fitting_allowed=False,full_D_ready=False)
    write(folder/'protocol.json',protocol)
    write(folder/'manifest.json',dict(version='operator-source-role-manifest-v2',sources=rows,protocol_sha256=sha(folder/'protocol.json'),sampler_sha256=sha(scan.CONFIG),
        profile_sha256=protocol['flow_context']['profile_sha256'],query_source_sha256=sha(Path(operator_query.__file__)),
        source_generator_sha256=sha(Path(samples.__file__)),role_mutation_allowed=False,physical_admission_allowed=False,independent_test_allowed=False))
    print(json.dumps(dict(status='prepared',sources=len(rows),counts=protocol['source_counts'],unique_target_calls_max=13*len(rows),physical_admission_allowed=False)),flush=True)


def next_request(folder,source_id,history,selection_freeze=None):
    m=read(folder/'manifest.json');row=next(r for r in m['sources'] if r['id']==source_id)
    if sha(folder/'protocol.json')!=m['protocol_sha256'] or sha(scan.CONFIG)!=m['sampler_sha256']:raise ValueError('protocol/sampler changed')
    if m.get('profile_sha256') and sha(ROOT/'experiments/arithmetic_dse/configs/platforms/asap7.json')!=m['profile_sha256']:raise ValueError('frozen physical profile changed')
    if m.get('query_source_sha256') and sha(Path(operator_query.__file__))!=m['query_source_sha256']:raise ValueError('frozen query feature producer changed')
    if sha(Path(samples.__file__))!=m['source_generator_sha256']:raise ValueError('frozen source generator changed')
    if (key(canonical_features(row['features']))!=row['source_group']
            or sha(folder/'sources'/row['id']/'input.sv')!=row['rtl_sha256']
            or sha(folder/'sources'/row['id']/'contract.json')!=row['contract_sha256']):
        raise ValueError('immutable source features/RTL/geometry changed')
    if row['role']=='locked_test':
        if selection_freeze is None:raise ValueError('locked_test requires a real frozen candidate before proposal or physical execution')
        freeze=read(selection_freeze)
        if not freeze.get('validation_passed') or freeze.get('source_manifest_sha256')!=sha(folder/'manifest.json') or not freeze.get('model_sha256') or freeze.get('test_consumed'):
            raise ValueError('invalid independent-test selection freeze')
        def resolved(name):
            path=Path(freeze[name]);return path if path.is_absolute() else selection_freeze.parent/path
        try:
            model=resolved('model_path');validation=resolved('validation_path')
            if sha(model)!=freeze['model_sha256'] or sha(validation)!=freeze['validation_sha256']:
                raise ValueError('candidate or validation receipt changed')
            receipt=read(validation)
            if receipt.get('status')!='passed' or receipt.get('model_sha256')!=freeze['model_sha256'] or receipt.get('source_manifest_sha256')!=sha(folder/'manifest.json'):
                raise ValueError('validation receipt does not bind this candidate and source split')
        except (OSError,KeyError,TypeError) as e:raise ValueError('real frozen model and bound validation receipt required before test') from e
    decision=scan.decide(history,source_id,row['role'])
    return dict(source=row,decision=decision)


def execute_next(folder,source_id,state_folder,admission,selection_freeze=None):
    """Concrete physical adapter; unreachable without separately frozen stage4 release."""
    release=read(admission)
    if (release.get('version')!='operator-stage4-admission-v1' or not release.get('physical_admission_allowed')
            or release.get('source_manifest_sha256')!=sha(folder/'manifest.json')):raise ValueError('no valid stage4 physical admission; steps123 never starts formal collection')
    requests=release.get('source_target_requests',[])
    if not 1<=len(requests)<=12 or len({key(r) for r in requests})!=len(requests):
        raise ValueError('stage4 release requires 1--12 unique exact source/target requests')
    hashes=release.get('measurement_source_sha256',{})
    if not set(measurement_sources()) <= set(hashes):raise ValueError('stage4 release omits required measurement producers')
    for name,h in hashes.items():
        if Path(name).is_absolute() or '..' in Path(name).parts or sha(ROOT/name)!=h:
            raise ValueError('measurement adapter differs from stage4 freeze')
    qualification=Path(release['qualification_proof_path'])
    if sha(qualification)!=release['qualification_proof_sha256']:raise ValueError('qualification proof changed')
    proof=read(qualification)
    if proof.get('status')!='passed' or proof.get('points')!=4 or proof.get('stages')!=8 or proof.get('source_role')!='not_training':
        raise ValueError('finite physical qualification receipt missing')
    history_path=state_folder/'history.json';history=read(history_path) if history_path.exists() else []
    requested=next_request(folder,source_id,history,selection_freeze);row=requested['source'];q=requested['decision']['next_request']
    if q is None:return requested['decision']
    exact=dict(source_id=source_id,role=row['role'],SDC_ps=q['SDC_ps'],ABC_ps=q['ABC_ps'])
    if exact not in release.get('source_target_requests',[]):raise ValueError('sampler request outside finite stage4 source/target admission')
    if row['role']=='locked_test' and not release.get('independent_test_allowed'):raise ValueError('test stage not admitted')
    # Each point gets an immutable physical manifest binding the exact sampler
    # proposal; the reused measured adapter never changes a data source's role.
    from . import model_steps123_qualification as implementation
    from .budget import POLICY,usage
    from types import FunctionType
    class CollectionLedger(implementation.QualificationLedger):
        def reserve(self,stage,timeout_s,threads,purpose,command,output,*,context=None):
            import shutil
            limits=read(POLICY)['resources'];total=usage(read(self.path)['entries']);later=read(folder/'protocol.json')['later_work_reserved']
            if ((stage in ('synth','grt') and total[stage]+1+later[stage]>limits['max_synthesis_calls' if stage=='synth' else 'max_global_route_calls'])
                    or total['walltime_s']+timeout_s+later['walltime_s']>limits['max_global_walltime_h']*3600
                    or total['CPU_time_s']+timeout_s*threads+later['CPU_time_s']>limits['max_tool_CPU_time_h']*3600):
                raise ValueError('point would consume explicitly reserved later-work resources')
            if shutil.disk_usage(state_folder).free < later['storage_bytes']+1024**3:
                raise ValueError('point would consume later-work storage reserve')
            return super().reserve(stage,timeout_s,threads,purpose,command,output,context=context)
    state_folder.mkdir(parents=True,exist_ok=True);point=state_folder/('target-'+str(q['SDC_ps']))
    if point.exists():raise ValueError('point already attempted; no automatic retries')
    point.mkdir();task=dict(id=source_id+'-T'+str(q['SDC_ps']),source_group=row['source_group'],features=row['features'],rtl=str(folder/'sources'/row['id']/'input.sv'),
        rtl_sha256=row['rtl_sha256'],period_ps=q['SDC_ps'],abc_target_ps=q['ABC_ps'],source_role=row['role'])
    inherited=release.get('inherit_synth_by_source',{}).get(source_id)
    if inherited and inherited['target_ps']==q['SDC_ps']:
        if inherited['source_role']!=row['role']:raise ValueError('inherited source role mismatch')
        task['inherit_synth']=inherited
    shared=admission.parent/('measurement-source-'+sha(admission)[:16])
    import fcntl
    with shared.with_suffix('.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        for name,h in release['measurement_source_sha256'].items():
            dest=shared/name
            if dest.exists():
                if sha(dest)!=h:raise ValueError('shared measurement source freeze changed')
            else:
                dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    (point/'source').symlink_to(shared.resolve(),target_is_directory=True)
    admission_id='conditional-'+source_id+'-'+str(q['SDC_ps'])
    if task.get('inherit_synth'):admission_id+='-reader-continuation-'+key(task['inherit_synth'])[:12]
    write(point/'admission.json',dict(version='operator-conditional-point-v1',id=admission_id,tasks=[task],
        source_sha256=release['measurement_source_sha256'],synth_timeout_s=300,grt_timeout_s=1200,support_max=12,
        source_manifest_sha256=sha(folder/'manifest.json'),stage4_admission_sha256=sha(admission),exact_proposal=q,immutable_role=row['role'],physical_training_admitted=True))
    try:
        namespace=dict(implementation.task_run.__globals__);namespace['QualificationLedger']=CollectionLedger
        measure=FunctionType(implementation.task_run.__code__,namespace,closure=implementation.task_run.__closure__)
        measure(point,task);label=read(point/'runs'/task['id']/'grt-labels.json')
        if label['source_role']!=row['role'] or not label['physical_training_label_eligible']:raise ValueError('physical role or label qualification mismatch')
        observed=dict(**q,status='completed',source_id=source_id,role=row['role'],implementation_id=sha(point/'runs'/task['id']/'grt-labels.json'),
            operator_delay_ps=label['operator_delay_ps'],comb_area_um2=label['comb_area_um2'],data_setup_slack_ps=label['data_setup_slack_ps'],
            operator_maximum_covered=label['operator_maximum_covered'],data_through_operator_covered=label['data_through_operator_covered'],ownership_complete=label['ownership_complete'])
    except Exception as e:
        observed=dict(**q,status='failed',source_id=source_id,role=row['role'],failure_reason=str(e));history.append(observed);write(history_path,history);raise
    history.append(observed);scan.decide(history,source_id,row['role']);write(history_path,history);return next_request(folder,source_id,history,selection_freeze)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('prepare','next','execute-next'));p.add_argument('--folder',type=Path,required=True);p.add_argument('--source');p.add_argument('--history',type=Path);p.add_argument('--admission',type=Path);p.add_argument('--state',type=Path);p.add_argument('--selection-freeze',type=Path);a=p.parse_args()
    if a.action=='prepare':prepare(a.folder.resolve())
    elif a.action=='next':print(json.dumps(next_request(a.folder.resolve(),a.source,read(a.history) if a.history else [],a.selection_freeze),ensure_ascii=False))
    else:print(json.dumps(execute_next(a.folder.resolve(),a.source,a.state.resolve(),a.admission.resolve(),a.selection_freeze),ensure_ascii=False))
