"""Control load plus prospective retained-bank geometry, never mapped prices.

The same features come from synthetic banks or actual materialized slots.
The square-root FF count is a floorplan scale proxy; it grants no electrical
or full arithmetic-state qualification by itself.
"""
import math
from . import state_control_queries as queries,state_control_response_v2 as parent

VERSION='per-source-control-features-v3-bank-geometry'


def attach(controls,input_widths,stage_words,external_bits):
    if not stage_words or any(any(type(w) is not int or w<=0 for w in group) for group in stage_words):
        raise ValueError('explicit retained variable words required')
    native_bits=sum(sum(group) for group in stage_words)
    total=sum(input_widths)+1+native_bits+len(stage_words)+external_bits+1
    result=[]
    for query in controls:
        q=dict(query);f=parent.features(query);stage=query['stage'];words=stage_words[stage] if stage<len(stage_words) else []
        native=float(query['control_source']=='native_valid')
        f.update(total_FF_bits=float(total),sqrt_total_FF_bits=math.sqrt(total),
            enabled_word_count=float(len(words)),max_enabled_word_bits=float(max(words,default=0)),
            native_footprint=native*math.sqrt(total),native_word_load=native*len(words),
            native_log_word_load=native*math.log2(len(words)+1),
            load_fraction=f['total_logical_sinks']/max(1.,native_bits),
            pressure_native_footprint=native*math.sqrt(total)*f['clock_pressure'])
        q['features']=f;result.append(q)
    return result


def bank_queries(spec,target):
    words=[[s['variable_bits'] for s in spec['slots'] if s['stage']==stage and s['variable_bits']>0]
           for stage in range(1,spec['depth']+1)]
    widths=[r['width'] for r in spec['roots']]
    external=sum(spec['words'][i]['variable_bits'] for i in spec['external_words'])
    return attach(queries.bank_queries(spec,target),widths,words,external)


def materialized_queries(state_query,input_widths,service_mode,target):
    q=queries.materialized_queries(state_query,input_widths,service_mode,target)
    if sum(input_widths)+1!=state_query['input_variable_bits']:raise ValueError('service/state FF census mismatch')
    words=[[] for _ in range(state_query['internal_stages'])];external=0
    for slot in state_query['slots']:
        if slot['valid'] or not slot['variable_bits']:continue
        if slot['external_capture']:external+=slot['variable_bits']
        else:words[slot['stage']-1].append(slot['variable_bits'])
    q.update(version=VERSION,controls=attach(q['controls'],input_widths,words,external),
             actual_arithmetic_S_qualified=False)
    return q
