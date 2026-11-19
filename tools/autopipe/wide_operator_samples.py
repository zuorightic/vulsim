"""Frozen v10 runtime functions; extracted without numerical edits from wide_operator_samples.py."""
from . import wide_arithmetic as arithmetic

def input_demand(s,prefix):
    alias=arithmetic.aliases(s)
    if alias is not None:return {v[1] for v in alias if isinstance(v,list) and v[0]==prefix}
    if s['operation']=='mux':return set(range(s['result_lo'],s['result_lo']+s['value_width']))
    if s['operation'] in ('ult','ule','eq'):return set(range(s[prefix+'_width']))
    high=s['arithmetic_width'] if s['status']!='none' else s['result_lo']+s['value_width']
    return set(range(min(s[prefix+'_width'],high)))
