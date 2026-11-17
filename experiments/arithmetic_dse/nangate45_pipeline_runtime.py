"""N56 runtime adapter preserving exact, zero-work Boolean owners."""
from unittest.mock import patch
from . import nangate45_artifacts as component
from . import nangate45_pipeline as base
from .nangate45_pipeline_wire import is_wire,zero_price

ORIGINAL_LOAD=component.load


class AliasAwarePrices:
    def __init__(self,prices):self.prices=prices;self.profile_sha256=prices.profile_sha256
    def operator_price(self,query):
        # Always validate identity even when the arithmetic work folds away.
        flow=query['flow_context']
        if (flow['target_platform']!='nangate45' or flow['profile_sha256']!=self.profile_sha256 or
            flow['target_period_ps']!=flow['abc_target_ps'] or flow['target_period_ps']<=0 or
            flow['evaluation_stage']!='grt' or query['version']!='arithmetic-workload-query-v2'):
            raise ValueError('zero-work query still requires platform/clock identity')
        if is_wire(query):return zero_price()
        return self.prices.operator_price(query)
    def reduction_price(self,query):return self.prices.reduction_price(query)


def load_component(path):return AliasAwarePrices(ORIGINAL_LOAD(path))


def load_package(path):
    with patch.object(component,'load',load_component):return base.load_package(path)
