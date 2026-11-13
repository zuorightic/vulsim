"""Shared S response and numerical-period reserve, diagnostic until qualified."""
import math
from . import state_control_distribution as geometry

VERSION = 'shared-state-control-response-v8'


def reserve(entry, target):
    if 'reserve_function' not in entry:
        return entry['reserve_ps']
    log = math.log2(target / 500.)
    f = dict(one=1., control_log_relaxation=log / (1. + log))
    m = entry['reserve_function']
    value = sum(f[n] * c for n, c in zip(m['features'], m['coefficients'], strict=True))
    if not math.isfinite(value) or value < 0:
        raise ValueError('invalid numerical S reserve')
    return value


def predict(model, structure, *, diagnostic=False):
    try:
        if model['version'] != VERSION or not diagnostic:
            raise ValueError('shared S candidate lacks public qualification or matching identity')
        qs = geometry.controls(structure)
        if set(model['functions']) != {'native_valid', 'native_enable', 'input_valid', 'external_valid'}:
            raise ValueError('incomplete S functions')
        paths = {}
        for name, entry in model['functions'].items():
            m = entry['function']
            guard = reserve(entry, structure['target_ps'])
            values = []
            for q in qs:
                if q['path_class'] != name:
                    continue
                latent = math.fsum([m.get('intercept', 0.), *(q['features'][n] * c for n, c in zip(
                    m['features'], m['coefficients'], strict=True))])
                if m['kind'] == 'positive_log_linear':
                    value = math.exp(latent)
                elif m['kind'] == 'linear':
                    value = max(0., latent)
                else:
                    raise ValueError('unknown shared S function kind')
                if not math.isfinite(value):
                    raise ValueError('nonfinite S price')
                values.append(dict(stage=q['stage'], control_source=q['control_source'],
                                   required_ps=value, guarded_required_ps=value + guard))
            paths[name] = dict(required_ps=max(v['required_ps'] for v in values),
                               guarded_required_ps=max(v['guarded_required_ps'] for v in values), sources=values)
        return dict(status='diagnostic_estimate', paths=paths,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, ValueError, TypeError, OverflowError) as error:
        return dict(status='cost_uncovered', reason=str(error))
