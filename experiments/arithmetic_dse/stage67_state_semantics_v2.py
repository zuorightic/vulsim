"""Same exact Boolean proof with a net-incidence index for arithmetic cuts.

The original all-cells scan is equivalent but quadratic on large products.
This successor changes only how external net incidences are found, preserving
every state/reset/enable/clock comparison and the cut definition verbatim.
"""
from collections import defaultdict
import inspect
from . import stage67_state_semantics_v1 as parent


def verify(directory,state,rtl,contract):
    text=inspect.getsource(parent.verify)
    old="if any(n in bits for other,row in cells.items() if not other.startswith(name.rsplit('/',1)[0]+'/') for bits in row['connections'].values()):cut.add(n)"
    new="if any(not other.startswith(name.rsplit('/',1)[0]+'/') for other in net_incidence.get(n,())):cut.add(n)"
    pre="for n,(name,term) in drivers.items():"
    index="net_incidence=defaultdict(set)\n    for other,row in cells.items():\n        for bits in row['connections'].values():\n            for net in bits:net_incidence[net].add(other)\n    "+pre
    if text.count(old)!=1 or text.count(pre)!=1:raise ValueError('frozen Boolean cut callsite drift')
    ns=dict(parent.verify.__globals__);ns['defaultdict']=defaultdict
    exec(compile(text.replace(old,new).replace(pre,index),__file__,'exec'),ns)
    return ns['verify'](directory,state,rtl,contract)
