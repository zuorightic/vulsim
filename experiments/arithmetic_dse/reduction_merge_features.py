"""Post-compression carry geometry for a prospective common G successor.

This defines numerical features only. It neither changes a published predictor
nor accepts a query rejected by that predictor's existing support rules.
"""
import math
from .reduction_function_v2 import features as predecessor_features

FEATURE_VERSION='bit-column-features-v3-final-merge'


def features(width,terms,target):
    result=predecessor_features(width,terms,target);heights=[0]*width
    for term in terms:
        for _,_,column in term:heights[column]+=1
    while max(heights)>2:
        following=[0]*width
        for i,h in enumerate(heights):
            counters=h//3;following[i]+=h%3+counters
            if i+1<width:following[i+1]+=counters
        heights=following
    full=half=increment=wire=segments=maximum=span=0;carry=False
    for h in heights:
        if h==2:
            if carry:full+=1
            else:half+=1;segments+=1
            carry=True;span+=1
        elif h==1 and carry:increment+=1;span+=1
        else:
            if h==1 or carry:wire+=1
            carry=False;maximum=max(maximum,span);span=0
        maximum=max(maximum,span)
    result.update(post_merge_full_adder_columns=float(full),post_merge_half_adder_columns=float(half),
                  post_merge_increment_columns=float(increment),post_merge_wire_columns=float(wire),
                  post_merge_carry_segments=float(segments),post_merge_max_carry_span=float(maximum),
                  log2_post_merge_carry_span=math.log2(maximum+1),
                  post_merge_pressure_work=(result['counter_count']+full+half+increment)*1500/target)
    return result
