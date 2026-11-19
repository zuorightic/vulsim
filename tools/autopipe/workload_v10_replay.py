"""Frozen v10 runtime functions; extracted without numerical edits from workload_v10_replay.py."""
from copy import deepcopy

def retarget(plan, target):
    p = deepcopy(plan); p['target_ps'] = target
    for op in p['operators']:
        for q in (op['query'], op['predecessor_projection']):
            if q is not None:
                q['flow_context']['target_period_ps'] = target
                q['flow_context']['abc_target_ps'] = target
        op['interface_features']['target_ps'] = target
        op['interface_features']['clock_pressure'] = 1500 / target
    for region in p['G_regions']:
        region['query']['target_ps'] = target
    return p
