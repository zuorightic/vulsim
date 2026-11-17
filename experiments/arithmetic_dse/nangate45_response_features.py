"""Train-diagnosed, prospectively sealed width/request interaction features.

The wide Add training source has a strong 500ps area response absent in Add8.
One width/clock interaction can express this across widths without shape keys.
It is sealed before the first new-backend validation label is collected.
"""
import argparse
from copy import deepcopy
import inspect
import json
from pathlib import Path
from types import FunctionType
from unittest.mock import patch

from . import nangate45_model as parent
from . import nangate45_fit_sealed as fitting
from .nangate45_samples import read,write,sha,verify

SCHEMA='nangate45-shared-width-clock-features-v2'
BASE_BASIS=parent.basis
FEATURES={k:[*v,'width_clock'] for k,v in parent.FEATURES.items()}


def basis(family,query,target,metric,old_prices,time_scale=1.):
    ref,f=BASE_BASIS(family,query,target,metric,old_prices,time_scale)
    f['width_clock']=f['log_width']*f['log_clock']
    return ref,f


class OperatorFunctions(parent.OperatorFunctions):
    def predict(self,family,query):
        ns=dict(parent.OperatorFunctions.predict.__globals__);ns.update(basis=basis,FEATURES=FEATURES)
        return FunctionType(parent.OperatorFunctions.predict.__code__,ns)(self,family,query)


def preregister(root):
    root=Path(root).resolve();a=verify(root);p=root/'feature-contract.json'
    if p.exists() or any((root/'runs'/t['id']).exists() for t in a['tasks'] if t['role']!='train'):
        raise ValueError('feature amendment must precede validation/test collection')
    sources=['operator-7ab4f32d7bb9b588','wide-6c1e33e2246ff438']
    evidence={}
    for source in sources:
        for t in a['tasks']:
            if t['source']==source:
                path=root/'runs'/t['id']/'grt-labels.json'
                if not path.exists():raise ValueError('declared training contrast incomplete')
                evidence[str(path)]=sha(path)
    write(p,dict(schema=SCHEMA,admission_sha256=sha(root/'admission.json'),
        reason='Add128 training area has clock pressure absent at Add8; add the same continuous log(width)*log(clock) feature to each family',
        features=FEATURES,added_feature='log(1+max operand width or G output width) * log(T/1500)',
        observed_training_sources=sources,training_evidence=evidence,
        validation_labels_read=False,test_labels_read=False,source_or_exact_clock_keys=False,
        response_forms_time_scale_grid_and_ridge_grid_unchanged=True,implementation_sha256=sha(__file__)))
    return dict(status='shared feature sealed before validation/test',sha256=sha(p))


def run(root,action):
    root=Path(root).resolve();contract=read(root/'feature-contract.json')
    if sha(__file__)!=contract['implementation_sha256'] or sha(root/'admission.json')!=contract['admission_sha256']:
        raise ValueError('feature contract drift')
    with patch.object(parent,'basis',basis),patch.object(parent,'FEATURES',FEATURES):
        result=fitting.run(root,action)
    if action=='freeze':
        payload=read(root/'frozen-model.json');payload['feature_schema']=SCHEMA
        payload['feature_contract_sha256']=sha(root/'feature-contract.json')
        write(root/'frozen-model.json',payload)
        seal=read(root/'model-freeze.json');seal.update(model_sha256=sha(root/'frozen-model.json'),feature_contract_sha256=sha(root/'feature-contract.json'))
        write(root/'model-freeze.json',seal)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=('preregister','freeze','evaluate'));p.add_argument('--root',type=Path,required=True);a=p.parse_args()
    print(json.dumps(preregister(a.root) if a.action=='preregister' else run(a.root,a.action),indent=2))
