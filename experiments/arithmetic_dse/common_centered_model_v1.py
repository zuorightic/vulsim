"""Explicit diagnostic consumption of the frozen W3--W5 successor.

This entry does not replace the public provider or its qualification. Query
semantics and structural support remain mandatory, including in diagnostics.
"""
import math
from . import centered_response as response, common_mechanism_features_v1 as geometry
from . import conditional_function_support_v2 as support
from . import wide_function_model as operator
from . import operator_function_successor as semantic_operator

VERSION = 'W345-common-centered-functions-v1'


def identity(model, diagnostic):
    if (model['version'] != VERSION or model['feature_version'] != geometry.VERSION
            or not diagnostic):
        raise ValueError('centered successor requires explicit unqualified diagnostics')


def require_support(domain, features, target):
    verdict = support.check(domain, features, target)
    if verdict['status'] != 'structurally_supported':
        raise ValueError(verdict['reason'])


def predict_operator(model, query, *, diagnostic=False):
    try:
        identity(model, diagnostic)
        gate = semantic_operator.predict(model['semantic_operator_model'], query, diagnostic=True)
        if gate['status'] == 'cost_uncovered':
            raise ValueError(gate['reason'])
        f = geometry.operator_features(query)
        operator.semantic_scope(query)
        if query['topology']['operand_shared_input_roots']:
            raise ValueError('correlated operator operands require qualification')
        family = operator.family(query['local_context']['producer'])
        name = {'add': 'Add', 'mux': 'Mux'}[family]
        m = model['models'][name]
        if (query['flow_context']['boundary_policy'] != 'unsigned-wide-family-hierarchy-v1'
                or query['flow_context']['profile_sha256'] != model['operator_profile_sha256']):
            raise ValueError('operator measurement profile mismatch')
        require_support(m['support'], f, query['flow_context']['target_period_ps'])
        if name == 'Add':
            value = response.predict(m['function'], f) * math.fsum(f[n] * w for n, w in m['reference_weights'].items())
            delay = operator.linear(m['retained_delay'], f)
            return dict(status='diagnostic_estimate', comb_area_um2=value,
                        operator_delay_ps=delay, qualified_for_public_D=False)
        return dict(status='diagnostic_delay_only', operator_delay_ps=response.predict(m['function'], f),
                    qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))


def predict_reduction(model, query, *, diagnostic=False):
    try:
        identity(model, diagnostic)
        if (query.get('launch_type', 'register') != 'register'
                or query.get('capture_banks', 1) != 1 or query.get('consumer_count', 0) != 0):
            raise ValueError('unqualified reduction boundary')
        f = geometry.reduction_features(query)
        m = model['models']['G']
        require_support(m['support'], f['area'], query['target_ps'])
        area = math.fsum(f['area'][n] * w for n, w in m['reference_area_weights'].items())
        area *= response.predict(m['area'], f['intensive'])
        delay = response.predict(m['delay'], f['intensive'])
        if min(area, delay) <= 0:
            raise ValueError('nonpositive reduction price')
        return dict(status='diagnostic_estimate', comb_area_um2=area,
                    operator_delay_ps=delay, qualified_for_public_D=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))


def predict_state(model, structure, *, diagnostic=False):
    try:
        identity(model, diagnostic)
        controls = geometry.state_controls(structure)
        m = model['models']['S']
        paths = {}
        for name, entry in m['functions'].items():
            log = math.log2(structure['target_ps'] / 500.)
            c = entry['reserve_function']['coefficients']
            guard = c[0] + c[1] * log / (1. + log)
            if not math.isfinite(guard) or guard < 0:
                raise ValueError('invalid numerical state reserve')
            prices = []
            for q in controls:
                if q['path_class'] != name:
                    continue
                require_support(m['support'][name], q['features'], structure['target_ps'])
                value = response.predict(entry['function'], q['features'])
                if value <= 0:
                    raise ValueError('nonpositive control response')
                prices.append(dict(stage=q['stage'], control_source=q['control_source'],
                                   required_ps=value, guarded_required_ps=value + guard))
            paths[name] = dict(required_ps=max(p['required_ps'] for p in prices),
                               guarded_required_ps=max(p['guarded_required_ps'] for p in prices),
                               sources=prices)
        return dict(status='diagnostic_estimate', paths=paths,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, ValueError, TypeError, OverflowError, ZeroDivisionError) as error:
        return dict(status='cost_uncovered', reason=str(error))
