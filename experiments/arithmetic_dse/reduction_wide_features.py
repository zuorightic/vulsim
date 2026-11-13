"""Wide successor geometry; preserves separate area and delay conventions.

The inherited delay uses a balanced height estimate, while prefix area uses
actual column compression rounds. Keeping both prevents a silent basis change.
"""
import math
from . import reduction_prefix_features as prefix

VERSION='wide-reduction-paired-features-v1'


def features(width,terms,target):
    if len(terms)>4096 or sum(len(t) for t in terms)>1048576:
        raise ValueError('wide G input capacity exceeded')
    area=prefix.features(width,terms,target)  # Includes all semantic validation.
    heights=[0]*width
    for term in terms:
        for _,_,column in term:heights[column]+=1
    maximum=max(heights);total=sum(heights)
    lo=next(i for i,h in enumerate(heights) if h);hi=max(i for i,h in enumerate(heights) if h)
    first=next((i for i,h in enumerate(heights) if h>=2),width)
    counters=rounds=0
    while max(heights)>2:
        following=[0]*width
        for i,h in enumerate(heights):
            n=h//3;counters+=n;following[i]+=h%3+n
            if i+1<width:following[i+1]+=n
        heights=following;rounds+=1
    carry=max(0,hi-first+1);rows=maximum;balanced=0
    while rows>2:rows=2*(rows//3)+rows%3;balanced+=1
    full=half=increment=wire=segments=maxspan=span=0;active=False
    for h in heights:
        if h==2:
            if active:full+=1
            else:half+=1;segments+=1
            active=True;span+=1
        elif h==1 and active:increment+=1;span+=1
        else:
            if h==1 or active:wire+=1
            active=False;span=0
        maxspan=max(maxspan,span)
    delay=dict(one=1.,output_bits=float(width),term_count=float(len(terms)),active_bits=float(total),
        max_column_height=float(maximum),counter_count=float(counters),compressor_depth=float(rounds),
        compression_levels=float(balanced),carry_span=float(carry),log2_carry_span=math.log2(carry+1.),
        active_span=float(hi-lo+1),clock_pressure=1500./target,log2_target=math.log2(target/500.),
        pressure_work=(counters+carry)*1500./target,
        post_merge_full_adder_columns=float(full),post_merge_half_adder_columns=float(half),
        post_merge_increment_columns=float(increment),post_merge_wire_columns=float(wire),
        post_merge_carry_segments=float(segments),post_merge_max_carry_span=float(maxspan),
        log2_post_merge_carry_span=math.log2(maxspan+1.),
        post_merge_pressure_work=(counters+full+half+increment)*1500./target)
    return dict(area=area,delay=delay)
