"""Pure diagnostic consumption of the frozen flow-structure successor.

The predecessor retains ownership of semantic/profile/support gates. This
module adds no public qualification and makes no backend calls. Component
predictions for S are added on the same witnessed-path definition of R.
"""
import math
from . import common_centered_model_v1 as inherited
from . import centered_response as response
from . import flow_structure_features_v4 as geometry

VERSION = 'W345-flow-word-context-functions-v4'


def gate(model, kind, query, diagnostic):
    if not diagnostic or model['version'] != VERSION or model['feature_version'] != geometry.VERSION:
        raise ValueError('flow-structure successor requires explicit diagnostics and matching identity')
    result = {'operator': inherited.predict_operator, 'G': inherited.predict_reduction,
              'S': inherited.predict_state}[kind](model['inherited_centered'], query, diagnostic=True)
    if result['status'] == 'cost_uncovered':
        raise ValueError(result['reason'])
    return result


def predict_operator(model, query, *, diagnostic=False):
    try:
        previous = gate(model, 'operator', query, diagnostic)
        f = geometry.operator_features(query)
        name = 'Mux' if query['local_context']['producer']['operation'] == 'mux' else 'Add'
        m = model['models'][name]
        value = response.predict(m['function'], f)
        if name == 'Mux':
            return dict(status='diagnostic_delay_only', operator_delay_ps=value,
                        qualified_for_public_D=False)
        area = value * f[m['reference']]
        if not math.isfinite(area) or area <= 0:
            raise ValueError('nonpositive operator price')
        return dict(status='diagnostic_estimate', comb_area_um2=area,
                    operator_delay_ps=previous['operator_delay_ps'], qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))


def predict_reduction(model, query, *, diagnostic=False):
    try:
        gate(model, 'G', query, diagnostic)
        f = geometry.reduction_features(query)['intensive']
        m = model['models']['G']
        area = f['ks_fused_area'] * response.predict(m['area'], f)
        delay = response.predict(m['delay'], f)
        if min(area, delay) <= 0 or not all(map(math.isfinite, (area, delay))):
            raise ValueError('nonpositive reduction price')
        return dict(status='diagnostic_estimate', comb_area_um2=area,
                    operator_delay_ps=delay, qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))


def predict_state(model, structure, *, diagnostic=False):
    try:
        gate(model, 'S', structure, diagnostic)
        controls = geometry.state_controls(structure)
        paths = {}
        log = math.log2(structure['target_ps'] / 500.)
        for name, entry in model['models']['S'].items():
            c = entry['reserve_function']['coefficients']
            if len(c) != 2:
                raise ValueError('reserve dimensions')
            guard = c[0] + c[1] * log / (1. + log)
            if not math.isfinite(guard) or guard < 0:
                raise ValueError('invalid reserve')
            prices = []
            for q in controls:
                if q['path_class'] != name:
                    continue
                value = math.fsum(response.predict(fn, q['features'])
                                  for fn in entry['functions'].values())
                if not math.isfinite(value) or value <= 0:
                    raise ValueError('nonpositive complete state response')
                prices.append(dict(stage=q['stage'], control_source=q['control_source'],
                                   required_ps=value, guarded_required_ps=value + guard))
            paths[name] = dict(required_ps=max(p['required_ps'] for p in prices),
                               guarded_required_ps=max(p['guarded_required_ps'] for p in prices),
                               sources=prices)
        return dict(status='diagnostic_estimate', paths=paths,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))
