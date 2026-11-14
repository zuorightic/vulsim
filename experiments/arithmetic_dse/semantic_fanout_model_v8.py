"""Pure diagnostic v8 consumption; no physical tools or measured-price lookup.

The frozen v4 bundle retains semantic/profile/support gates and Add delay.
Reference choices are frozen per shared function, never per query or source.
"""
import math
from . import flow_structure_model as inherited
from . import centered_response as response
from . import semantic_fanout_features_v8 as geometry
from .conditional_function_support_v2 import check

VERSION = 'W345-semantic-fanout-functions-v8'


def gate(model, kind, query, diagnostic):
    if not diagnostic or model['version'] != VERSION or model['feature_version'] != geometry.VERSION:
        raise ValueError('semantic-fanout successor requires explicit diagnostics and matching identity')
    result = {'operator': inherited.predict_operator, 'G': inherited.predict_reduction,
              'S': inherited.predict_state}[kind](model['inherited_flow'], query, diagnostic=True)
    if result['status'] == 'cost_uncovered':
        raise ValueError(result['reason'])
    return result


def price(entry, features):
    value = response.predict(entry['function'], features)
    if entry['reference'] is not None:
        value *= features[entry['reference']]
    if not math.isfinite(value) or value <= 0:
        raise ValueError('nonpositive semantic-fanout price')
    return value


def predict_operator(model, query, *, diagnostic=False):
    try:
        previous = gate(model, 'operator', query, diagnostic)
        features = geometry.operator_features(query)
        name = 'Mux' if query['local_context']['producer']['operation'] == 'mux' else 'Add'
        value = price(model['models'][name], features)
        if name == 'Mux':
            return dict(status='diagnostic_delay_only', operator_delay_ps=value,
                        qualified_for_public_D=False)
        return dict(status='diagnostic_estimate', comb_area_um2=value,
                    operator_delay_ps=previous['operator_delay_ps'], qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))


def predict_reduction(model, query, *, diagnostic=False):
    try:
        gate(model, 'G', query, diagnostic)
        features = geometry.reduction_features(query)['intensive']
        entry = model['models']['G']
        return dict(status='diagnostic_estimate', comb_area_um2=price(entry['area'], features),
                    operator_delay_ps=price(entry['delay'], features), qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))


def state_estimates(model, structure):
    classes = {'native_valid', 'native_enable', 'input_valid', 'external_valid'}
    if set(model['models']['S']) != classes or set(model['state_support']) != classes:
        raise ValueError('incomplete state classes/support')
    if model['context_function'] != model['models']['S']['native_enable']['functions']['R']:
        raise ValueError('enable price/context dependency differs')
    controls = geometry.state_controls(structure, model['context_function'])
    paths = {}
    log = math.log2(structure['target_ps'] / 500.)
    for name, entry in model['models']['S'].items():
        coeff = entry['reserve_function']['coefficients']
        if len(coeff) != 2:
            raise ValueError('reserve dimensions')
        guard = coeff[0] + coeff[1] * log / (1. + log)
        if not math.isfinite(guard) or guard < 0:
            raise ValueError('invalid reserve')
        prices = []
        for query in controls:
            if query['path_class'] != name:
                continue
            value = math.fsum(response.predict(fn, query['features']) for fn in entry['functions'].values())
            if not math.isfinite(value) or value <= 0:
                raise ValueError('nonpositive complete state response')
            prices.append(dict(stage=query['stage'], control_source=query['control_source'],
                               required_ps=value, guarded_required_ps=value + guard))
        paths[name] = dict(required_ps=max(p['required_ps'] for p in prices),
                           guarded_required_ps=max(p['guarded_required_ps'] for p in prices), sources=prices)
    return controls, paths


def predict_state(model, structure, *, diagnostic=False):
    try:
        if not diagnostic or model['version'] != VERSION or model['feature_version'] != geometry.VERSION:
            raise ValueError('semantic-fanout successor requires explicit diagnostics and matching identity')
        controls, paths = state_estimates(model, structure)
        for query in controls:
            verdict = check(model['state_support'][query['path_class']], query['features'], structure['target_ps'])
            if verdict['status'] != 'structurally_supported':
                raise ValueError(verdict['reason'])
        return dict(status='diagnostic_estimate', paths=paths,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))
