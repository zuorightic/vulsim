"""Frozen v10 runtime functions; extracted without numerical edits from nangate45_response_features.py."""
from types import FunctionType

from . import nangate45_model as parent

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
