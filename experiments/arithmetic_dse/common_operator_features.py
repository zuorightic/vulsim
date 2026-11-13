"""Analytical narrow/wide operator features from the existing runtime Query."""
import math
from .operator_condition_model import features as predecessor_features

VERSION = 'common-operator-numerical-features-v1'


def features(query):
    f = predecessor_features(query)
    for name in ('lhs', 'rhs', 'result'):
        f['log2_' + name] = math.log2(max(1., f[name + '_width']))
    f['target_pressure'] = 1500. / f['target_period_ps']
    f['pressure_product_terms'] = f['retained_product_terms'] * f['target_pressure']
    f['pressure_add_span'] = f['add_carry_span'] * f['target_pressure']
    return f
