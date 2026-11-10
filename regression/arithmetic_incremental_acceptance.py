"""Incremental steps 1--3 checks; software fixtures never grant model prices."""
import argparse
from collections import Counter,defaultdict
from copy import deepcopy
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from experiments.arithmetic_dse.model_fast_preflight import read,write,sha,key
from experiments.arithmetic_dse import operator_collection as collection
from experiments.arithmetic_dse import operator_condition_model as model

EXCLUDED={'declared_result_width','operand_shared_input_roots','same_stage_remaining_depth'}


def oracle(query):
    """Independent bit-set oracle, including demanded-width clipping."""
    result=dict.fromkeys(model.CONSUMER_FEATURES,0)
    for consumer in query['local_context']['consumers']:
        spec=consumer['spec'];ends=[];ones=0
        for prefix in ('lhs','rhs'):
            width=min(spec[prefix+'_width'],spec['result_width'])
            zero={i for i in range(width) if int(spec.get(prefix+'_zero_hex','0'),16)&(1<<i)}
            one={i for i in range(width) if int(spec.get(prefix+'_one_hex','0'),16)&(1<<i)}
            variable=set(range(width))-zero-one;not_zero=set(range(width))-zero
            lower=min(not_zero,default=width);upper=max(not_zero,default=-1)+1
            result['consumer_'+prefix+'_active_bits']=max(result['consumer_'+prefix+'_active_bits'],len(variable))
            result['consumer_'+prefix+'_zero_lsb_run']=max(result['consumer_'+prefix+'_zero_lsb_run'],lower)
            result['consumer_'+prefix+'_zero_msb_run']=max(result['consumer_'+prefix+'_zero_msb_run'],width-upper)
            ends.append((lower,upper));ones+=len(one)
        (al,ah),(bl,bh)=ends;r=spec['result_width']
        result['consumer_add_overlap_bits']=max(result['consumer_add_overlap_bits'],len(set(range(al,ah))&set(range(bl,bh))&set(range(r))))
        result['consumer_add_carry_span']=max(result['consumer_add_carry_span'],max(0,min(max(ah,bh)+1,r)-max(al,bl)))
        result['consumer_known_one_bits']=max(result['consumer_known_one_bits'],ones)
        result['consumer_nonzero_carry']=max(result['consumer_nonzero_carry'],int(spec.get('carry','zero')!='zero'))
    return result


def example(profile):
    producer=dict(operation='mul',lhs_width=8,rhs_width=8,result_width=16,carry='zero',capture_banks=1)
    consumer=dict(operation='add',lhs_width=16,rhs_width=64,result_width=64,carry='zero',capture_banks=1,
                  lhs_zero_hex='0x0',lhs_one_hex='0x0',rhs_zero_hex='0x0',rhs_one_hex='0x0')
    features=collection.canonical_features(dict(producer=producer,consumers=[dict(spec=consumer,
        bindings=[dict(operand_index=0,result_bit_map=list(range(16)))],
        other_dynamic_inputs='independent_launch; source correlations require G validation')],captures=[]))
    return collection.descriptor(dict(features=features),1500)


def prepare(root,witness,out):
    if out.exists():raise ValueError('preserve acceptance attempt')
    out.mkdir(parents=True)
    manifest=read(root/'corpus/manifest.json');new=read(root/'new-sources.json')['sources']
    report=read(witness);unique={}
    for row in report['runs'][1]['candidates']:
        for node in row['node_prices']:
            descriptor=node['descriptor'];unique[key(descriptor)]=descriptor
    queries=[]
    for descriptor in unique.values():
        for target in (500,1000,1500,3000):
            q=deepcopy(descriptor);q['flow_context'].update(target_period_ps=target,abc_target_ps=target)
            queries.append(dict(descriptor=q,allow_candidate=True))
    for row in manifest['sources']:
        queries.append(dict(descriptor=collection.descriptor(row,1234.5),allow_candidate=True))
    dense=example(manifest['profile_sha256']);sparse=deepcopy(dense)
    sparse['local_context']['consumers'][0]['spec']['rhs_zero_hex']='0xffff'
    old_dense={k:v for k,v in model.features(dense).items() if k not in model.CONSUMER_FEATURES}
    old_sparse={k:v for k,v in model.features(sparse).items() if k not in model.CONSUMER_FEATURES}
    if old_dense!=old_sparse or model.consumer_features(dense)==model.consumer_features(sparse):
        raise ValueError('consumer-mask collision was not resolved')
    dead=deepcopy(sparse);dead['local_context']['consumers'][0]['spec'].update(rhs_width=67,rhs_one_hex=hex(1<<66))
    if model.consumer_features(dead)!=model.consumer_features(sparse):raise ValueError('dead declaration bits affect load features')
    for q in (dense,sparse,dead):queries.append(dict(descriptor=q,allow_candidate=True))
    all_zero=deepcopy(dense);all_zero['local_context']['consumers'][0]['spec']['rhs_zero_hex']=hex((1<<64)-1)
    queries.append(dict(descriptor=all_zero,allow_candidate=True))
    for q in queries:
        expected=oracle(q['descriptor']);actual=model.consumer_features(q['descriptor'])
        if expected!=actual:raise ValueError('independent bit-set oracle differs')
    base=deepcopy(queries[-4]);negative=[]
    def corrupt(name,fn):
        q=deepcopy(base);fn(q['descriptor']);q['negative_name']=name;negative.append(q)
    def spec(q):return q['local_context']['consumers'][0]['spec']
    corrupt('consumer_overlap_masks',lambda q:spec(q).update(rhs_zero_hex='0x1',rhs_one_hex='0x1'))
    corrupt('consumer_overflow_mask',lambda q:spec(q).update(rhs_zero_hex=hex(1<<64)))
    corrupt('consumer_underscore_mask',lambda q:spec(q).update(rhs_zero_hex='0x_ff'))
    corrupt('consumer_space_mask',lambda q:spec(q).update(rhs_zero_hex=' 0xff'))
    corrupt('consumer_mask_type',lambda q:spec(q).update(rhs_zero_hex=3))
    corrupt('consumer_live_known_one',lambda q:spec(q).update(rhs_one_hex='0x1'))
    corrupt('consumer_carry_type',lambda q:spec(q).update(carry=3))
    corrupt('consumer_carry_one',lambda q:spec(q).update(carry='one'))
    corrupt('consumer_carry_unknown',lambda q:spec(q).update(carry='invalid'))
    corrupt('view_identity_injected',lambda q:q.update(view_id='candidate/quarter/view31'))
    corrupt('source_identity_injected',lambda q:q.update(source_id='special-price'))
    contexts=[collection.operator_query.features(q) for q in unique.values()]
    fields=('lhs_width','rhs_width','result_width','consumer_count','consumer_lhs_max','consumer_rhs_max','consumer_result_max',
            'capture_banks','mapped_zero_bits','mapped_undemanded_bits','mapped_repeated_bits','mapping_shift_min','mapping_shift_max')
    ranges={op:{field:[min(f[field] for q,f in zip(unique.values(),contexts) if q['local_context']['producer']['operation']==op),
                             max(f[field] for q,f in zip(unique.values(),contexts) if q['local_context']['producer']['operation']==op)] for field in fields}
            for op in ('mul','add')}
    audit=dict(version='operator-demand-audit-v2',status='passed_interface_expressibility',descriptor_ABI_unchanged=True,
        actual_query_descriptors=len(unique),
        actual_local_contexts=len({key(collection.canonical_features(q['local_context'])) for q in unique.values()}),
        actual_candidates=len(report['runs'][1]['candidates']),ranges=ranges,
        numerical_feature_gap='consumer known masks already in descriptor; ten derived numerical summaries added',
        collision=dict(old_features_equal=True,new_features_different=True,dense=oracle(dense),zero_padded=oracle(sparse)),
        declaration_only_bits_excluded=True,all_new_source_roles=dict(Counter(r['role'] for r in new)),
        feature_protocol_sha256=sha(ROOT/'experiments/arithmetic_dse/configs/operator_condition_features_v2.json'),
        source_and_view_ids_are_not_predictors=True,exact_shapes_are_not_whitelisted=True,physical_test_labels_read=False,
        source_queries_are_demand_examples_not_domain_permission=True,full_D_ready=False)
    write(out/'demand-audit.json',audit)
    fixture=dict(version=model.VERSION,quality_status='TEST_ONLY',profile_sha256=manifest['profile_sha256'],
                 operator_boundary_policy='unsigned-op-hierarchy-v1',full_D_ready=False,operations={})
    files=[]
    names=list(model.CONSUMER_FEATURES)
    for index in range(5):
        b=deepcopy(fixture)
        for op in ('mul','add'):
            b['operations'][op]=dict(status='awaiting_independent',delay_reserve_ps=0,
                delay=dict(kind='linear',features=[names[2*index]],coefficients=[1.],intercept=100.),
                area=dict(kind='linear',features=[names[2*index+1]],coefficients=[1.],intercept=10.),
                domain=dict(numeric_support={'target_period_ps':[25,12000]}))
        path=out/('input-'+str(index)+'.json');write(path,dict(model=b,queries=queries+negative));files.append(path.name)
    clock=deepcopy(fixture)
    for op in ('mul','add'):
        clock['operations'][op]=dict(status='awaiting_independent',delay_reserve_ps=0,
            delay=dict(kind='linear',features=['target_period_ps','log2_target_ps'],coefficients=[.01,2.],intercept=100.),
            area=dict(kind='linear',features=['result_width'],coefficients=[.1],intercept=10.),domain=dict(numeric_support={'target_period_ps':[25,12000]}))
    write(out/'input-5.json',dict(model=clock,queries=queries+negative));files.append('input-5.json')
    legacy=root.parent/'operator-conditional-20261110/fit-v1/inference'
    (out/'input-6.json').write_bytes((legacy/'input-0.json').read_bytes());files.append('input-6.json')
    (out/'legacy-expected.json').write_bytes((legacy/'output-0.json').read_bytes())
    write(out/'vectors.json',dict(inputs=files,valid_queries=len(queries),negative_queries=len(negative),feature_names=names,
                                  descriptor_ABI='arithmetic-operator-query-v1',mode='TEST_ONLY',full_D_ready=False))
    print(dict(status='prepared',demand_contexts=len(unique),inputs=len(files),valid_queries=len(queries),negative_queries=len(negative)),flush=True)


def verify(folder):
    vector=read(folder/'vectors.json');total=accepted=refused=0
    for index,name in enumerate(vector['inputs']):
        data=read(folder/name);answers=read(folder/('output-'+str(index)+'.json'))
        if len(data['queries'])!=len(answers):raise ValueError('incomplete native vector output')
        expected_old=read(folder/'legacy-expected.json') if index==6 else None
        for pos,(q,a) in enumerate(zip(data['queries'],answers,strict=True)):
            total+=1;p=model.query(data['model'],q['descriptor'],q['allow_candidate'])
            if p['status']!=a['status']:raise ValueError('native/Python coverage differs')
            if q.get('negative_name') and p['status']!='cost_uncovered':raise ValueError('invalid consumer/identity accepted')
            if a['status']=='covered':
                accepted+=1
                if index<5:
                    f=oracle(q['descriptor']);expected=(100.+f[vector['feature_names'][2*index]],10.+f[vector['feature_names'][2*index+1]])
                    if not all(math.isclose(a[k],v,rel_tol=1e-12,abs_tol=1e-9) for k,v in zip(('operator_delay_ps','comb_area_um2'),expected)):
                        raise ValueError('native consumer feature does not match bit-set oracle')
                for k in ('operator_delay_ps','comb_area_um2','delay_reserve_ps','conservative_operator_delay_ps'):
                    if not math.isclose(a[k],p[k],rel_tol=1e-10,abs_tol=1e-8):raise ValueError('native/Python price differs')
            else:refused+=1
            if expected_old:
                previous=expected_old[pos]
                if a['status']!=previous['status']:raise ValueError('legacy candidate coverage changed')
                if a['status']=='covered' and any(not math.isclose(a[k],previous[k],rel_tol=1e-10,abs_tol=1e-8) for k in
                        ('operator_delay_ps','comb_area_um2','delay_reserve_ps','conservative_operator_delay_ps')):
                    raise ValueError('legacy frozen prediction changed')
    proof=dict(status='passed',queries=total,covered=accepted,refused=refused,consumer_features_verified=10,
               mask_bit_set_oracle_passed=True,unseen_numeric_clock_passed=True,legacy_frozen_predictions_unchanged=True,
               interface_ABI_unchanged=True,mode='TEST_ONLY',new_EDA_calls=0,physical_test_labels_read=False,full_D_ready=False)
    write(folder/'feature-proof.json',proof);print(proof,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=('prepare','verify'))
    for name in ('root','witness','out','folder'):p.add_argument('--'+name,type=Path)
    a=p.parse_args()
    if a.action=='prepare':prepare(a.root.resolve(),a.witness.resolve(),a.out.resolve())
    else:verify(a.folder.resolve())
