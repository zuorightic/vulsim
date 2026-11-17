"""Use the frozen control ridge with already materialized S features.

control_query returns its feature vector, whereas the legacy fit helper expects
raw fields and transforms them itself. Only that interface is adapted here;
the fixed ridge, source weights, feature names and prediction remain unchanged.
"""
import inspect
from types import FunctionType
from unittest.mock import patch
from . import nangate45_pipeline_fit as base
from . import nangate45_pipeline_runtime as runtime
from . import nangate45_pipeline_evaluate as evaluated
from . import nangate45_artifacts as component
from . import workload_diagnostic as diagnostic


def fit_controls(rows):
    def materialized(features):
        if set(features)!=set(diagnostic.S_FEATURES):
            raise ValueError('S materialized feature vector differs from frozen schema')
        return features
    namespace = dict(diagnostic.fit_state.__globals__, s_features=materialized)
    return FunctionType(diagnostic.fit_state.__code__, namespace)(rows)


def freeze(root):
    text = inspect.getsource(base.freeze)
    replacements = {
        "min(x['operator_delay_ps'] for r in train for x in r['labels']['nodes'].values())":
            "min(step['delay_ps'] for r in train for path in r['labels']['functional_paths'] for step in path['segments'] if step['kind']=='node_cell' and step['delay_ps']>0)",
        'ctrl,audit=diagnostic.fit_state(controls)': 'ctrl,audit=fit_controls(controls)'}
    for old,new in replacements.items():
        if text.count(old)!=1:
            raise ValueError('N56 fitting interface callsite drift')
        text = text.replace(old,new)
    namespace = dict(base.freeze.__globals__, fit_controls=fit_controls)
    exec(compile(text,__file__,'exec'),namespace)
    with patch.object(component,'load',runtime.load_component):
        return namespace['freeze'](root)


evaluate = evaluated.evaluate
