"""Thirteen-target sampler restricted to the declared numerical price domain.

Keeps the same slack-only offline selection and immutable source roles. It
does not spend points outside T500..3000 just to manufacture three regions.
"""
from copy import deepcopy
from types import FunctionType,SimpleNamespace
from . import common_function_sampling as common,model_three_region_scan as base

VERSION='wide-function-domain-three-region-v3-default-bindings'


def decide(history,source_id,role):
    cfg=deepcopy(base.policy());cfg.update(minimum_ps=500,maximum_ps=3000,minimum_relative_target_separation='1/20')
    facade=SimpleNamespace(policy=lambda:cfg,_next=base._next,decide=base.decide,number=base.number)
    ns=dict(common.decide.__globals__);ns['parent']=facade
    decision=FunctionType(common.decide.__code__,ns,argdefs=common.decide.__defaults__,
                          closure=common.decide.__closure__)
    return decision(history,source_id,role)
