"""Portable conditional operator inference; contains no fitting or EDA."""
import math
from . import operator_query

VERSION='operator-condition-function-v1'


def features(query):
    values=operator_query.features(query)
    values.update(width_product=values['lhs_width']*values['rhs_width'],
        width_result_product=values['result_width']**2,lhs_result_product=values['lhs_width']*values['result_width'],
        rhs_result_product=values['rhs_width']*values['result_width'])
    al,bl=values['lhs_zero_lsb_run'],values['rhs_zero_lsb_run']
    ah=values['lhs_width']-values['lhs_zero_msb_run'];bh=values['rhs_width']-values['rhs_zero_msb_run'];r=values['result_width']
    values['lhs_active_bits']=values['lhs_width']-values['lhs_zero_count'];values['rhs_active_bits']=values['rhs_width']-values['rhs_zero_count']
    values['active_width_product']=values['lhs_active_bits']*values['rhs_active_bits']
    values['add_overlap_bits']=max(0,min(ah,bh,r)-max(al,bl))
    values['add_carry_span']=max(0,min(max(ah,bh)+1,r)-max(al,bl));values['log2_add_carry_span']=math.log2(max(1,values['add_carry_span']))
    values['retained_product_terms']=sum(max(0,min(bh,r-i)-bl) for i in range(int(al),int(ah)))
    return values


def infer(predictor,values):
    kind=predictor['kind']
    if kind=='linear':
        value=predictor['intercept']
        for name,c in zip(predictor['features'],predictor['coefficients'],strict=True):value+=c*values[name]
    elif kind=='segmented':
        at=sum(values['log2_target_ps']>k for k in predictor['knots'])
        return infer(predictor['segments'][at],values)
    elif kind=='width_grouped':
        group='small' if max(values['lhs_width'],values['rhs_width'])<=predictor['split'] else 'large'
        return infer(predictor['groups'][group],values)
    elif kind=='tree':
        at=0;seen=set()
        while True:
            if at in seen or not 0<=at<len(predictor['nodes']):raise ValueError('invalid portable tree')
            seen.add(at);node=predictor['nodes'][at]
            if 'value' in node:value=node['value'];break
            at=node['left'] if values[node['feature']]<=node['threshold'] else node['right']
    else:raise ValueError('unknown conditional predictor')
    if not math.isfinite(value):raise ValueError('nonfinite prediction')
    return max(0.,value)


def joint_covered(entry,values):
    support=entry['domain'].get('joint_support')
    if not support:return True
    reference=dict(values);t=support['reference_target_ps'];reference.update(target_period_ps=t,abc_target_ps=t,log2_target_ps=math.log2(t))
    ratio=values['target_period_ps']/max(support['reference_floor_ps'],infer(entry['delay'],reference))
    distances=[]
    for anchor in support['anchors']:
        d=math.sqrt(sum(((values[n]-v)/scale)**2 for n,v,scale in zip(support['features'],anchor['vector'],support['scales'],strict=True)))
        distances.append((d,anchor))
    nearby=sorted(distances,key=lambda item:item[0])[:support['k']]
    return (len(nearby)==support['k'] and nearby[-1][0]<=support['radius']+1e-12
        and any(a['clock_ratio_min']-1e-12<=ratio<=a['clock_ratio_max']+1e-12 for _,a in nearby))


def query(model,descriptor,allow_candidate=False):
    try:
        f=features(descriptor);ctx=descriptor['flow_context'];op=descriptor['local_context']['producer']['operation']
        if (model['version']!=VERSION or ctx['profile_sha256']!=model['profile_sha256']
                or ctx['boundary_policy']!=model['operator_boundary_policy']
                or ctx['target_platform']!='asap7' or ctx['evaluation_stage']!='grt'
                or ctx['target_period_ps']!=ctx['abc_target_ps']):raise ValueError('model flow context mismatch')
        entry=model['operations'][op]
        if entry['status']!='passed_independent' and not (allow_candidate and entry['status']=='awaiting_independent'):raise ValueError('operator function unqualified')
        domain=entry['domain']
        if f['lhs_one_count'] or f['rhs_one_count'] or f['carry_dynamic'] or f['carry_one'] or f['consumer_mul'] or f['consumer_addcarry'] or f['consumer_count']>1:raise ValueError('unsupported operand or consumer semantics')
        if any(f[p+'_zero_count']!=f[p+'_zero_lsb_run']+f[p+'_zero_msb_run'] for p in ('lhs','rhs')):
            raise ValueError('interior known-zero pattern outside first interval domain')
        if domain.get('local_load_family'):
            if f['capture_banks']>2 or max(f['consumer_lhs_max'],f['consumer_rhs_max'],f['consumer_result_max'])>f['result_width']+1:
                raise ValueError('outside validated local load family')
        for name,bounds in domain['numeric_support'].items():
            if not bounds[0]<=f[name]<=bounds[1]:raise ValueError('outside trained numerical feature support '+name)
        if not joint_covered(entry,f):raise ValueError('outside joint semantic-neighbor/clock support')
        d=infer(entry['delay'],f);a=infer(entry['area'],f)
        return dict(status='covered',operator_delay_ps=d,delay_reserve_ps=entry['delay_reserve_ps'],
            conservative_operator_delay_ps=d+entry['delay_reserve_ps'],comb_area_um2=a,full_stage_price_qualified=False)
    except (KeyError,ValueError,TypeError) as e:return dict(status='cost_uncovered',reason=str(e))
