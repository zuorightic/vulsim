"""Small portable N4 parameter export and strict offline loading.

The existing frozen ASAP7 response is referenced by its content hash rather
than duplicated into Git. Loading is explicit and occurs before inference;
the numerical consumer receives fully materialized parameters.
"""
import argparse
from copy import deepcopy
import math
from pathlib import Path

from .nangate45_samples import ROOT,read,write,sha
from .platforms import profile
from . import nangate45_model as numerical

SCHEMA='nangate45-N4-offline-arithmetic-package-v1'


class ArithmeticPrices:
    def __init__(self,payload):
        from . import nangate45_response_features as features
        if payload.get('feature_schema')!=features.SCHEMA:raise ValueError('N4 feature schema differs')
        self.response=features.OperatorFunctions(payload)
        self.profile_sha256=payload['profile_sha256']

    def operator_price(self,query):
        op=query['local_context']['producer']['operation']
        family={'mul':'Mul','add':'Add','adc':'Add'}.get(op)
        if family is None:raise ValueError('N4 arithmetic type not calibrated')
        flow=query['flow_context']
        if flow['evaluation_stage']!='grt':raise ValueError('N4 labels are grt only')
        target=flow['target_period_ps']
        if (query['version']!='arithmetic-workload-query-v2' or flow['target_platform']!='nangate45' or
            flow['profile_sha256']!=self.profile_sha256 or flow['abc_target_ps']!=target or
            not math.isfinite(target) or target<=0):
            raise ValueError('N4 query/platform/request identity mismatch')
        from . import wide_arithmetic as arithmetic
        if arithmetic.aliases(query['local_context']['producer']) is not None:
            # The frozen D semantics already eliminate constants and wires.
            # A proof of zero arithmetic work never needs a fitted log price.
            return dict(delay_ps=0.,area_um2=0.,qualified=False,full_D_ready=False,
                        source='existing unsigned semantic constant/wire certificate',
                        flags=['proven_constant_or_wire_alias'])
        return self.response.predict(family,query)

    def reduction_price(self,query):
        # The explicit platform identity is mandatory at this component
        # interface. A future N6 owner adapter must bind it from its package.
        if 'local_context' in query:raise ValueError('reduction requires whole-region terms')
        return self.response.predict('G',query)


def load(path):
    path=Path(path).resolve();doc=read(path);selected=profile('nangate45')
    if (doc['schema']!=SCHEMA or doc['target_platform']!='nangate45' or
        doc['profile_sha256']!=selected['profile_sha256'] or doc['evaluation_stage']!='grt'):
        raise ValueError('N4 platform/profile/stage mismatch')
    if doc['online_backend_feedback'] or doc['exact_lookup'] or doc['application_PPA_used'] or doc['full_D_ready']:
        raise ValueError('component package must preserve offline N4 boundary')
    payload=deepcopy(doc['numerical_payload']);ref=doc['ASAP7_response_reference'];member=ROOT/ref['path']
    if not member.resolve().is_relative_to(ROOT) or sha(member)!=ref['sha256']:
        raise ValueError('frozen inherited response content differs')
    payload['ASAP7_response']=read(member)
    if payload['profile_sha256']!=doc['profile_sha256']:raise ValueError('numerical payload profile differs')
    if set(payload['functions'])!=set(numerical.FEATURES):raise ValueError('missing fitted arithmetic type')
    for family,metrics in payload['functions'].items():
        if set(metrics)!={'delay_ps','area_um2'}:raise ValueError('separate delay/area responses required')
        for fn in metrics.values():
            if fn['form'] not in ('global_scale','family_scale','family_affine','shared_log_feature_ridge'):
                raise ValueError('response form outside frozen grammar')
            if not math.isfinite(fn['time_scale']) or fn['time_scale']<=0:raise ValueError('invalid request-axis parameter')
    return ArithmeticPrices(payload)


def export(root,destination):
    root=Path(root).resolve();seal=read(root/'model-freeze.json');payload=read(root/'frozen-model.json')
    if sha(root/'frozen-model.json')!=seal['model_sha256']:raise ValueError('fitted model changed after freeze')
    evaluation=read(root/'evaluation.json')
    if evaluation['model_sha256']!=seal['model_sha256']:raise ValueError('evaluation/model differs')
    del payload['ASAP7_response']
    write(destination,dict(schema=SCHEMA,target_platform='nangate45',profile_sha256=payload['profile_sha256'],evaluation_stage='grt',
        status='arithmetic_components_evaluated',full_D_ready=False,
        qualification='test_gates_passed_on_sampled_arithmetic_sources' if evaluation['arithmetic_test_gates_passed'] else 'diagnostic_arithmetic_some_test_gates_failed',
        numerical_payload=payload,ASAP7_response_reference=dict(path=str(fit_old().relative_to(ROOT)),sha256=payload['ASAP7_response_sha256']),
        exact_lookup=False,online_backend_feedback=False,application_PPA_used=False,
        external_model_sha256=seal['model_sha256'],statistical_contract_sha256=sha(root/'statistical-contract.json'),
        evaluation_sha256=sha(root/'evaluation.json'),
        exclusions=['S/shared/control','H_char and equivalent-time contract','G embedding/compositions','full D selection/RTL/ABCD qualification'],
        measured_support=dict(clock_ps=[500,1500,3000],paired_sources=20,
            Mul='six contexts: 4/8/16/64/128 square full products and 32x64 full product; limited consumers',
            Add='ten contexts: full add up to 512, ADC64/128, one known-bit case, direct/two-bank/consumer loads',
            G='four sparse full-region contexts: outputs 24/64/96/128, term counts 3/4/11/7; no G consumer'),
        extrapolation='unsampled widths, slices, masks, large G and load combinations carry no additional qualification'))
    load(destination)
    return dict(path=str(destination),sha256=sha(destination),bytes=Path(destination).stat().st_size)


def fit_old():
    return ROOT/'experiments/arithmetic/evidence/workload_equivalent_mac32_v1/diagnostic-model.json'


if __name__=='__main__':
    import json
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    print(json.dumps(export(a.root,a.out),indent=2))
