"""Frozen v10 runtime functions; extracted without numerical edits from nangate45_artifacts.py."""
from copy import deepcopy

import math

from pathlib import Path

from .nangate45_samples import ROOT, read, sha

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
