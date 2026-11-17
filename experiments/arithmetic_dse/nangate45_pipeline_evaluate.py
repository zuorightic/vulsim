"""Checked train/evaluation adapters; aliases retain exact zero delay and area."""
import inspect
from pathlib import Path
from unittest.mock import patch
from . import nangate45_pipeline_fit as base
from . import nangate45_pipeline as pipeline
from . import nangate45_artifacts as component
from . import nangate45_pipeline_runtime as runtime


def freeze(root):
    text=inspect.getsource(base.freeze)
    old="min(x['operator_delay_ps'] for r in train for x in r['labels']['nodes'].values())"
    new="min(step['delay_ps'] for r in train for path in r['labels']['functional_paths'] for step in path['segments'] if step['kind']=='node_cell' and step['delay_ps']>0)"
    if text.count(old)!=1:raise ValueError('N56 train floor callsite drift')
    namespace=dict(base.freeze.__globals__)
    exec(compile(text.replace(old,new),__file__,'exec'),namespace)
    with patch.object(component,'load',runtime.load_component):return namespace['freeze'](root)


def evaluate(root):
    text=inspect.getsource(base.evaluate)
    replacements={
        "p['delay_ps']/actual_node['operator_delay_ps']-1":"(p['delay_ps']-actual_node['operator_delay_ps'])/max(1e-9,actual_node['operator_delay_ps'])",
        "p['area_um2']/actual_node['comb_area_um2']-1":"(p['area_um2']-actual_node['comb_area_um2'])/max(1e-9,actual_node['comb_area_um2'])"}
    for a,b in replacements.items():
        if text.count(a)!=1:raise ValueError('N56 zero-work evaluator callsite drift')
        text=text.replace(a,b)
    namespace=dict(base.evaluate.__globals__);namespace['pipeline']=type('Pipeline',(),dict(load_package=staticmethod(runtime.load_package)))
    exec(compile(text,__file__,'exec'),namespace);return namespace['evaluate'](root)
