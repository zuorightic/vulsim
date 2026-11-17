"""Prospective gate-first N4 selection, following inherited fitting priorities.

Nearest-rank median of two sources is the smaller error. Gate-first selection
prevents that one easy source from selecting a function that fails the other.
This affects offline parameter selection only, never the frozen D selector.
"""
import argparse
from collections import defaultdict
import inspect
import json
from pathlib import Path
from unittest.mock import patch

from . import nangate45_fit as original
from . import nangate45_fit_sealed as statistics
from . import nangate45_response_features as features
from .nangate45_samples import read,write,sha,verify

OLD_KEY="key=lambda i:(candidates[i]['validation']['median_APE'],candidates[i]['validation']['P95_APE'],ranks[candidates[i]['function']['form']],i)"
NEW_KEY="key=lambda i:(not candidates[i]['validation']['passed'],candidates[i]['validation']['source_mean_APE'],candidates[i]['validation']['P95_APE'],ranks[candidates[i]['function']['form']],i)"


def metrics(rows,predicted,key):
    result=statistics.metrics(rows,predicted,key);groups=defaultdict(list)
    for r,p in zip(rows,predicted,strict=True):groups[r['source']].append(abs(p/r[key]-1.))
    result['source_mean_APE']=sum(sum(v)/len(v) for v in groups.values())/len(groups)
    return result


def preregister(root):
    root=Path(root).resolve();a=verify(root)
    if any((root/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train'):
        raise ValueError('selection amendment must precede validation/test collection')
    p=root/'selection-contract.json'
    if p.exists():raise ValueError('selection already sealed')
    write(p,dict(version='nangate45-N4-gate-first-selection-v1',admission_sha256=sha(root/'admission.json'),
        implementation_sha256=sha(__file__),reason='nearest-rank median with two validation sources would prefer the easier source; inherit gate-first fit selection',
        priority=['all validation gates passed','equal-source mean clock APE','source-macro P95','registered form complexity','stable candidate index'],
        D_algorithm_changed=False,validation_labels_read=False,test_labels_read=False,
        candidate_forms_features_request_axis_grid_and_ridge_grid_unchanged=True))
    # A waiting older orchestrator must stop before fitting its superseded
    # selection rule. This is explicitly a guard, never a fitted model.
    guard=root/'frozen-model.json'
    if guard.exists():raise ValueError('model/guard already exists')
    write(guard,dict(status='prospective_selection_rule_guard_not_a_model',selection_contract_sha256=sha(p),parameters_fitted=False))
    return dict(status='gate-first selection sealed before validation; old orchestrator guarded at fit step',sha256=sha(p))


def freeze(root):
    root=Path(root).resolve();contract=read(root/'selection-contract.json')
    if sha(__file__)!=contract['implementation_sha256'] or sha(root/'admission.json')!=contract['admission_sha256']:
        raise ValueError('selection contract drift')
    guard=root/'frozen-model.json';g=read(guard)
    if g.get('status')!='prospective_selection_rule_guard_not_a_model' or g['selection_contract_sha256']!=sha(root/'selection-contract.json'):
        raise ValueError('expected retained prospective guard')
    status=read(root/'finish-status.json')
    if status['phase']!='stopped_on_error' or status.get('error')!='selected model already frozen':
        raise ValueError('older orchestrator has not stopped at its declared guard')
    if any((root/'runs'/t['id']).exists() for t in verify(root)['tasks'] if t['role']=='test'):
        raise ValueError('test collection started before correct selection freeze')
    guard.rename(root/'superseded-selection-guard.json')
    text=inspect.getsource(original.freeze)
    if text.count(OLD_KEY)!=1:raise ValueError('superseded selection implementation changed')
    ns=dict(original.freeze.__globals__);exec(compile(text.replace(OLD_KEY,NEW_KEY),__file__,'exec'),ns)
    # Keep inherited acceptance statistics and add only a source-balanced
    # mean for choosing among functions. The immutable coefficients are then
    # sealed by the same response-feature pipeline.
    base_metrics=statistics.metrics
    def selection_metrics(rows,predicted,key):
        result=base_metrics(rows,predicted,key);groups=defaultdict(list)
        for r,p in zip(rows,predicted,strict=True):groups[r['source']].append(abs(p/r[key]-1.))
        result['source_mean_APE']=sum(sum(v)/len(v) for v in groups.values())/len(groups)
        return result
    ns['metrics']=selection_metrics
    with patch.object(original,'freeze',ns['freeze']),patch.object(statistics,'metrics',selection_metrics):
        result=features.run(root,'freeze')
    payload=read(root/'frozen-model.json');payload['selection_contract_sha256']=sha(root/'selection-contract.json')
    write(root/'frozen-model.json',payload);seal=read(root/'model-freeze.json')
    seal.update(model_sha256=sha(root/'frozen-model.json'),selection_contract_sha256=sha(root/'selection-contract.json'))
    write(root/'model-freeze.json',seal)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('preregister','freeze'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    print(json.dumps(preregister(a.root) if a.action=='preregister' else freeze(a.root),indent=2))
