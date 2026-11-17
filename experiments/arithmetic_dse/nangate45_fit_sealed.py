"""N4 evaluation using the inherited source-macro nearest-rank statistics.

The initial campaign draft said NumPy interpolated quantiles. The inherited
operator contract uses nearest rank instead. This explicit amendment is sealed
before any new-backend validation/test labels are collected or consumed. The
physical admission, source roles and candidate functions remain unchanged.
"""
import argparse
from collections import defaultdict
import math
from pathlib import Path
from statistics import median
from unittest.mock import patch

from . import nangate45_fit as fit
from .nangate45_samples import read,write,sha,verify


def metrics(rows,predicted,key):
    groups=defaultdict(list)
    for r,p in zip(rows,predicted,strict=True):groups[r['source']].append(abs(p/r[key]-1.))
    by={s:median(v) for s,v in groups.items()};values=sorted(by.values())
    if not values:raise ValueError('at least one complete source required')
    q=lambda p:values[max(0,math.ceil(len(values)*p)-1)]
    return dict(rows=len(rows),sources=len(values),median_APE=q(.5),P95_APE=q(.95),
                per_source_median_APE=by,quantile='inherited nearest rank',
                passed=bool(q(.5)<=.15 and q(.95)<=.35 and max(values)<=.35))


def preregister(root):
    root=Path(root).resolve();a=verify(root);p=root/'statistical-contract.json'
    if p.exists():raise ValueError('statistics already sealed')
    if any((root/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train'):
        raise ValueError('amendment must precede all validation/test labels')
    write(p,dict(version='nangate45-N4-statistics-amendment-v1',admission_sha256=sha(root/'admission.json'),
        reason='inherit operator_condition_fit.metrics nearest-rank source macro quantiles; correct draft interpolated quantiles',
        inherited_implementation='experiments/arithmetic_dse/operator_condition_fit.py',
        inherited_implementation_sha256=sha(Path(fit.ROOT)/'experiments/arithmetic_dse/operator_condition_fit.py'),
        source_aggregation='median APE over every clock within a source, then nearest-rank median and P95 across sources',
        thresholds=dict(median_APE=.15,P95_APE=.35,maximum_source_median_APE=.35),
        validation_labels_read=False,test_labels_read=False,selection_changed=False,
        implementation_sha256=sha(__file__)))
    return dict(status='statistics sealed before new validation/test collection',sha256=sha(p))


def run(root,action):
    root=Path(root).resolve();s=read(root/'statistical-contract.json')
    if s['implementation_sha256']!=sha(__file__) or s['admission_sha256']!=sha(root/'admission.json'):
        raise ValueError('statistical contract drift')
    with patch.object(fit,'metrics',metrics):
        return fit.freeze(root) if action=='freeze' else fit.evaluate(root)


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('preregister','freeze','evaluate'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    print(json.dumps(preregister(a.root) if a.action=='preregister' else run(a.root,a.action),indent=2))
