"""Pure offline Nangate45 prices and frozen-D budget/selection integration.

Loading materializes parameters before inference. Arithmetic remains the frozen
N4 function; N5 supplies separate S/shared/boundary parameters. No EDA, labels,
application PPA, source IDs, or exact-clock lookup enters numerical prediction.
"""
from contextlib import contextmanager
from copy import deepcopy
import math
from pathlib import Path
from unittest.mock import patch

from . import prospective_cell_cover as cells
from . import workload_platform_entry as entry
from . import workload_diagnostic as diagnostic
from . import nangate45_artifacts as arithmetic
from .nangate45_samples import ROOT,read,write,sha
from .platforms import profile

SCHEMA='nangate45-frozen-D-N56-package-v1'
ASAP7_COVER=dict(cells.AREA)


class PipelinePrices:
    def __init__(self,component,bundle,cover):
        self.component=component;self.bundle=bundle;self.cover_area=cover
        self.selected=profile('nangate45');self.cache={}

    @contextmanager
    def context(self):
        # Functional logic uses Nangate45 legal covers. The inherited ASAP7
        # regression basis retains its own original feature/cover definition.
        with patch.object(cells,'AREA',self.cover_area):yield

    def operator_price(self,query):
        with patch.object(cells,'AREA',ASAP7_COVER):result=self.component.operator_price(query)
        return dict(result,source='N4 offline arithmetic function; frozen during N5/N6')

    def reduction_price(self,query):
        q=deepcopy(query)
        for name,value in [('target_platform','nangate45'),('profile_sha256',self.selected['profile_sha256'])]:
            if name in q and q[name]!=value:raise ValueError('G platform/profile mismatch')
            q[name]=value
        with patch.object(cells,'AREA',ASAP7_COVER):result=self.component.reduction_price(q)
        return dict(result,source='N4 offline G function; accepted by user with recorded original residual')


def rebind(owners):
    result=entry.rebind_owners(owners,'nangate45')
    for g in result['G_regions']:
        g['query'].update(target_platform='nangate45',profile_sha256=result['profile_sha256'])
    return result


class PipelineRuntime(entry.PlatformRuntime):
    def check(self,owners):
        super().check(owners)
        for g in owners['G_regions']:
            if (g['query'].get('target_platform')!='nangate45' or
                g['query'].get('profile_sha256')!=self.prices.selected['profile_sha256']):raise ValueError('G requires owner-bound explicit platform identity')


def load_package(path):
    path=Path(path).resolve();doc=read(path);p=profile('nangate45')
    if (doc['schema']!=SCHEMA or doc['platform']!='nangate45' or doc['profile_sha256']!=p['profile_sha256'] or
        doc['evaluation_stage']!='grt' or doc['status']!='ready_for_finite_three_case_experiments'):
        raise ValueError('N56 package not ready or wrong platform/stage')
    if doc['exact_lookup'] or doc['online_backend_feedback'] or doc['application_PPA_used']:raise ValueError('offline function contract')
    payload={}
    for key in ('arithmetic','state_shared','characterization','cell_cover'):
        member=(path.parent/doc[key]['path']).resolve()
        if sha(member)!=doc[key]['sha256']:raise ValueError('N56 payload hash mismatch: '+key)
        payload[key]=member
    functions=arithmetic.load(payload['arithmetic']);state=read(payload['state_shared']);contract=read(payload['characterization']);cover=read(payload['cell_cover'])
    for obj in (state,contract,cover):
        if obj['profile_sha256']!=p['profile_sha256']:raise ValueError('N56 embedded profile mismatch')
    if contract['application_PPA_used'] or contract['operator_response_refitted']:raise ValueError('N56 sampling conversion contract')
    if set(cover['area_um2'])!=set(ASAP7_COVER) or any(not math.isfinite(x) or x<=0 for x in cover['area_um2'].values()):raise ValueError('N56 complete positive cell cover required')
    bundle=dict(version=diagnostic.VERSION,profile_sha256=p['profile_sha256'],S=state['S'],shared=state['shared'],
        inter_owner_wire_ps=state['inter_owner_wire_ps'],static_bridge=state['static_bridge'],numerical_floors=state['numerical_floors'])
    return PipelineRuntime(doc,PipelinePrices(functions,bundle,cover['area_um2']),contract)
