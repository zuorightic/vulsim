"""Qualified-reader interface with explicit ownership and actual physical pins."""
from types import FunctionType
from . import model_physical_labels_v2 as parent
from .model_qualification_labels import with_timing_arcs
from .model_logical_ownership_v2 import extract


def read_snapshot(prefix,period_ps,time_to_ps,liberty,nodes,banks,*,top_ports,ownership_certificate):
    namespace=dict(parent.read_snapshot.__globals__)
    namespace['extract']=lambda packet,*args:extract(packet,nodes,banks,top_ports,ownership_certificate)
    fn=FunctionType(parent.read_snapshot.__code__,namespace);fn.__kwdefaults__=parent.read_snapshot.__kwdefaults__
    return fn(prefix,period_ps,time_to_ps,liberty,nodes,banks)
