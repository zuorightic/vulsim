"""Diagnostic consumption of frozen prospective S control functions.

This successor rebuilds features from retained words and control semantics.
Mapped trees, measured timing and user-supplied feature dictionaries are not
accepted as inputs. Passing this software contract grants no S qualification.
"""
import math
from . import state_control_queries as queries, state_control_geometry as geometry

VERSION = 'diagnostic-state-control-consumer-v1'


def controls(structure):
    inputs = structure['input_widths']
    words = structure['stage_words']
    external = structure['external_bits']
    mode = structure['service_mode']
    target = structure['target_ps']
    if (not isinstance(inputs, list) or not inputs or len(inputs) > 4096
            or any(type(w) is not int or not 1 <= w <= 4096 for w in inputs)
            or not isinstance(words, list) or not words or len(words) > 4096
            or any(not isinstance(group, list) or len(group) > 4096
                   or any(type(w) is not int or not 1 <= w <= 4096 for w in group)
                   for group in words)
            or type(external) is not int or not 0 <= external <= 1048576
            or type(mode) is not int or mode not in (0, 1, 2)
            or type(target) not in (int, float) or not math.isfinite(target)
            or not 500 <= target <= 3000
            or sum(inputs) + sum(map(sum, words)) + external > 1048576):
        raise ValueError('bounded prospective state/control structure required')
    base = queries.queries(inputs, list(map(sum, words)), mode, target)
    return geometry.attach(base, inputs, words, external)


def predict(model, structure, *, diagnostic=False):
    try:
        if model['version'] != geometry.VERSION:
            raise ValueError('S control feature identity mismatch')
        if not diagnostic:
            raise ValueError('S successor has no public price qualification')
        rebuilt = controls(structure)
        result = {}
        for name, entry in model['functions'].items():
            if name not in ('native_valid', 'native_enable', 'input_valid', 'external_valid'):
                raise ValueError('unknown S control path family')
            reserve = entry['reserve_ps']
            m = entry['function']
            if not math.isfinite(reserve) or reserve < 0:
                raise ValueError('invalid S control reserve')
            source_prices = []
            for q in rebuilt:
                if q['path_class'] != name:
                    continue
                f = q['features']
                value = m.get('intercept', 0.) + sum(f[n] * c for n, c in zip(
                    m['features'], m['coefficients'], strict=True))
                if not math.isfinite(value):
                    raise ValueError('nonfinite S control estimate')
                value = max(0., value)
                source_prices.append(dict(stage=q['stage'], control_source=q['control_source'],
                                          required_ps=value, guarded_required_ps=value + reserve))
            if not source_prices:
                raise ValueError('missing prospective S control source')
            result[name] = dict(required_ps=max(p['required_ps'] for p in source_prices),
                                guarded_required_ps=max(p['guarded_required_ps'] for p in source_prices),
                                sources=source_prices)
        if set(result) != {'native_valid', 'native_enable', 'input_valid', 'external_valid'}:
            raise ValueError('incomplete S control functions')
        return dict(status='diagnostic_estimate', paths=result,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        return dict(status='cost_uncovered', reason=str(error))
