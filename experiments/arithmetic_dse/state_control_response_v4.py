"""One S response function with prospective source-kind/T/load interactions."""
import math
from . import state_control_geometry as parent, state_control_consumer as consumer

VERSION = 'per-source-control-features-v4-native-T-load'


def extend(control):
    q = dict(control)
    f = dict(q['features'])
    native = float(q['control_source'] == 'native_valid')
    f.update(native_log_target=native * f['log2_target'],
             native_load_log_target=native * f['log2_logical_sinks'] * f['log2_target'],
             native_sqrt_logical_sinks=native * math.sqrt(f['total_logical_sinks']))
    q['features'] = f
    return q


def bank_queries(spec, target):
    return [extend(q) for q in parent.bank_queries(spec, target)]


def controls(structure):
    return [extend(q) for q in consumer.controls(structure)]


def predict(model, structure, *, diagnostic=False):
    try:
        if model['version'] != VERSION:
            raise ValueError('S response feature identity mismatch')
        if not diagnostic:
            raise ValueError('S response successor lacks public qualification')
        queries = controls(structure)
        if set(model['functions']) != {'native_valid', 'native_enable', 'input_valid', 'external_valid'}:
            raise ValueError('incomplete S response functions')
        paths = {}
        for name, entry in model['functions'].items():
            reserve = entry['reserve_ps']
            if not math.isfinite(reserve) or reserve < 0:
                raise ValueError('invalid S response reserve')
            prices = []
            m = entry['function']
            for q in queries:
                if q['path_class'] != name:
                    continue
                value = m.get('intercept', 0.) + sum(q['features'][n] * c for n, c in zip(
                    m['features'], m['coefficients'], strict=True))
                if not math.isfinite(value):
                    raise ValueError('nonfinite S response')
                value = max(0., value)
                prices.append(dict(stage=q['stage'], control_source=q['control_source'],
                                   required_ps=value, guarded_required_ps=value + reserve))
            paths[name] = dict(required_ps=max(p['required_ps'] for p in prices),
                               guarded_required_ps=max(p['guarded_required_ps'] for p in prices),
                               sources=prices)
        return dict(status='diagnostic_estimate', paths=paths,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, ValueError, TypeError, OverflowError) as error:
        return dict(status='cost_uncovered', reason=str(error))
