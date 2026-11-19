"""Frozen v10 runtime functions; extracted without numerical edits from semantic_reset_features_v9.py."""
from collections import Counter

import math

from . import semantic_fanout_features_v8 as previous

def cone_spans(circuit, outputs):
    live, pending = set(), list(outputs)
    while pending:
        node = pending.pop()
        if node not in circuit.nodes or node in live:
            continue
        live.add(node); kind,a,b = circuit.nodes[node]
        pending.append(a)
        if kind != 'not': pending.append(b)
    spans = {node:(name[-1],name[-1]) for name,node in circuit.leaves.items()
             if isinstance(name,tuple) and len(name)==2 and name[0]!='cin'}
    ranges = []
    for node in sorted(live):
        kind,a,b = circuit.nodes[node]
        children = [spans[n] for n in ([a] if kind=='not' else [a,b]) if n in spans]
        if children:
            lo,hi = min(v[0] for v in children),max(v[1] for v in children)
            spans[node]=(lo,hi);ranges.append((lo,hi))
    cuts = Counter()
    for lo,hi in ranges:
        cuts[lo]+=1;cuts[hi]-=1
    count=peak=0
    for _,delta in sorted(cuts.items()):
        count+=delta;peak=max(peak,count)
    return dict(log2_total_span=math.log2(1+sum(hi-lo for lo,hi in ranges)),
                log2_peak_cut=math.log2(1+peak),
                local_fraction=sum(lo==hi for lo,hi in ranges)/max(1,len(ranges)))


def reduction_features(query):
    f = previous.reduction_features(query)
    extra = {}
    for serial in (False,True):
        c,outputs,_ = previous.circuits.reduction_circuit(query,serial=serial)
        extra.update({'cone_'+('serial_' if serial else 'fused_')+k:v for k,v in cone_spans(c,outputs).items()})
    extra['cone_serial_cut_gap'] = extra['cone_serial_log2_peak_cut']-extra['cone_fused_log2_peak_cut']
    extra['cone_cut_pressure'] = extra['cone_fused_log2_peak_cut']*f['intensive']['clock_pressure']
    for values in f.values(): values.update(extra)
    return f
