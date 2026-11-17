"""Verification-only successor: select an arithmetic identity probe by kind.

G can be the first budget owner. It has a region query, so it must not be used
as the arithmetic flow_context negative control. Numerical models are unchanged.
The failed verification and its traces remain in the original software folder.
"""
import inspect
from . import nangate45_pipeline_check as base


def adapted(function, replacements, root):
    text = inspect.getsource(function)
    for old,new in replacements.items():
        if text.count(old)!=1:
            raise ValueError('N56 verification successor callsite drift')
        text = text.replace(old,new)
    namespace = dict(function.__globals__)
    exec(compile(text,__file__,'exec'),namespace)
    return namespace[function.__name__](root)


def integration(root):
    return adapted(base.integration, {
        "out = root/'software'": "out = root/'software-v2'",
        "query = deepcopy(rows[0]['bindings'][0]['query'])":
            "query = deepcopy(next(x['query'] for row in rows for x in row['bindings'] if x['kind']=='operator'))"}, root)


def functional(root):
    return adapted(base.functional, {
        "root/'software/integration.json'": "root/'software-v2/integration.json'",
        "root/'software/functional'": "root/'software-v2/functional'"}, root)


detailed_panels = base.detailed_panels
numerical_guard = base.numerical_guard


def receipts(root):
    return adapted(base.receipts, {
        "('readout.', 'readout-v2.')": "('readout.', 'readout-v2.', 'readout-v3.')"}, root)
