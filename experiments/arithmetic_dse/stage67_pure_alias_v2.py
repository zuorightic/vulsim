"""Exact alias successor includes ANSI core input/output declarations.

The original parser started after the port header, so pure aliases involving
core inputs lacked declarations. No arithmetic or state proof is weakened.
"""
import inspect
from types import FunctionType,SimpleNamespace
from . import stage67_pure_alias_v1 as parent


def body_and_terms(rtl,contract):
    text=inspect.getsource(parent.body_and_terms)
    old="r'\\b(?:logic|wire)\\s*(?:\\[(\\d+):0\\])?\\s*(\\w+)\\s*(?:[,;]|//|\\))',body"
    new="r'\\b(?:logic|wire)\\s*(?:\\[(\\d+):0\\])?\\s*(\\w+)\\s*(?:[,;]|//|\\))',match[0]"
    if text.count(old)!=1:raise ValueError('pure-bit parser declaration callsite drift')
    ns=dict(parent.body_and_terms.__globals__);exec(compile(text.replace(old,new),__file__,'exec'),ns)
    return ns['body_and_terms'](rtl,contract)


def augment(design,pins,rtl,contract):
    ns=dict(parent.augment.__globals__);ns['body_and_terms']=body_and_terms
    return FunctionType(parent.augment.__code__,ns)(design,pins,rtl,contract)


def verify(design,pins,contract,source,rtl):
    ns=dict(parent.verify.__globals__);ns['augment']=augment
    value=FunctionType(parent.verify.__code__,ns)(design,pins,contract,source,rtl)
    value['version']='pure-bit-state-alias-census-v2'
    return value


def semantics(directory,state,rtl,contract):
    from . import stage67_state_semantics_v2 as exact
    def flatten(d,p):
        cells,aliases,_=augment(d,p,rtl,contract)
        return cells,aliases
    # v2 builds a function from v1 globals. Substitute only its flatten helper.
    ns=dict(exact.parent.verify.__globals__);ns['flatten']=flatten
    shim=SimpleNamespace(verify=FunctionType(exact.parent.verify.__code__,ns))
    outer=dict(exact.verify.__globals__);outer['parent']=shim
    return FunctionType(exact.verify.__code__,outer)(directory,state,rtl,contract)
