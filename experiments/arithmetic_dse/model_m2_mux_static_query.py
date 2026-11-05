"""Explicit Mux-only query adapter; missing context never selects a zero price."""
from .model_m2_mux_static_features import VERSION,descriptor,features,predict


def query(bundle,base,cut,query_id,*,candidate_numerical_mode=False,profile_sha256=None):
    if bundle.get('mux_feature_schema')!=VERSION or bundle.get('target_platform')!='asap7' or bundle.get('ABC_ps')!=1500 or base.get('abc_target_ps')!=1500:
        raise ValueError('Mux model schema/platform/mapping mismatch')
    model=bundle['stages']['grt']['operations']['mux']
    if not candidate_numerical_mode:
        if bundle.get('quality_status')!='passed' or model.get('quality_status')!='passed':raise ValueError('Mux model quality not qualified')
        if profile_sha256 is None or bundle.get('platform_profile_sha256')!=profile_sha256:raise ValueError('Mux model profile not qualified')
    f=features(base,cut,query_id);target=next(o for o in cut['operations'] if o['id']==query_id)
    family='parallel_dynamic_mux' if all(o['operation']=='mux' for o in cut['operations']) else 'legacy_mixed_control'
    if not candidate_numerical_mode and family not in model['context_domain'].get('independently_qualified_families',[]):
        raise ValueError('Mux context family has no independent qualification')
    if (base['lhs_width']!=target['result_width'] or base['rhs_width']!=0 or base['result_width']!=target['result_width']
        or base['fanout']!=target['capture_banks'] or base.get('lhs_zero_bits') or base.get('rhs_zero_bits')):
        raise ValueError('Mux context differs from queried node')
    if any(base.get(k,False) for k in ('literal_operands','known_one_operands','constant_carry','correlated_operands')):raise ValueError('unsupported dynamic Mux operand condition')
    if not any(c['lhs_width']==base['lhs_width'] and c['rhs_width']==base['rhs_width'] and c['result_width']==base['result_width']
               and c['sdc_period_ps']==base['sdc_period_ps'] and c['abc_target_ps']==base['abc_target_ps'] for c in model['joint_domain']):
        raise ValueError('outside Mux exact width/target domain')
    if not candidate_numerical_mode and base['fanout']!=model['context_domain']['production_capture_banks']:raise ValueError('outside Mux production capture domain')
    row={'spec':{'lhs_width':base['lhs_width'],'rhs_width':0,'result_width':base['result_width']},'period_ps':base['sdc_period_ps'],
        'features':base,'static_features':f}
    return {'feature_schema':VERSION,'features':f,'delay_ps':predict(model['delay'],row,'delay'),'comb_area_um2':predict(model['area'],row,'area'),
        'candidate_numerical_mode':candidate_numerical_mode,'PPA_calls':0}
