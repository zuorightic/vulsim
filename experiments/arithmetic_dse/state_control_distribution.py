"""Shared S features from prospective root connections and reset polarity."""
import math
from . import state_control_response_v4 as parent, common_state_features as loads

VERSION = 'per-source-control-features-v5-root-distribution-reset'


def extend(controls, input_widths, sink_inputs, stage_bits, stage_reset_ones):
    if (len(stage_bits) != len(stage_reset_ones)
            or any(type(n) is not int or not 0 <= n <= bits
                   for n, bits in zip(stage_reset_ones, stage_bits, strict=True))):
        raise ValueError('explicit retained reset polarity required')
    f = loads.input_load_features(input_widths, sink_inputs)
    result = []
    for control in controls:
        q = dict(control)
        values = dict(q['features'])
        native = float(q['control_source'] == 'native_valid')
        stage = q['stage']
        fraction = stage_reset_ones[stage] / max(1, stage_bits[stage]) if stage < len(stage_bits) else 0.
        values.update(native_root_spread=native * math.sqrt(f['input_loaded_bits']),
                      native_log_input_max_load=native * math.log2(f['input_max_bit_load'] + 1),
                      native_mean_log_input_load=native * f['input_log_load_sum'] / max(1, f['input_loaded_bits']),
                      native_reset_one_fraction=native * fraction)
        q['features'] = values
        result.append(q)
    return result


def structure(spec, target):
    sinks = []
    for w in spec['words']:
        a = w['source_positions']
        b = w.get('source_positions_second')
        sinks.extend([[i] for i in a] if b is None else [list(pair) for pair in zip(a, b, strict=True)])
    words = [[s['variable_bits'] for s in spec['slots'] if s['stage'] == stage and s['variable_bits'] > 0]
             for stage in range(1, spec['depth'] + 1)]
    reset = [sum(s['reset'].bit_count() for s in spec['slots'] if s['stage'] == stage)
             for stage in range(1, spec['depth'] + 1)]
    return dict(input_widths=[r['width'] for r in spec['roots']], stage_words=words,
                external_bits=sum(spec['words'][i]['variable_bits'] for i in spec['external_words']),
                service_mode=spec['service_mode'], target_ps=target,
                input_sink_inputs=sinks, stage_reset_one_bits=reset)


def controls(s):
    return extend(parent.controls(s), s['input_widths'], s['input_sink_inputs'],
                  list(map(sum, s['stage_words'])), s['stage_reset_one_bits'])


def bank_queries(spec, target):
    return controls(structure(spec, target))


def predict(model, s, *, diagnostic=False):
    try:
        if model['version'] != VERSION or not diagnostic:
            raise ValueError('S distribution successor lacks public qualification or matching identity')
        qs = controls(s)
        if set(model['functions']) != {'native_valid', 'native_enable', 'input_valid', 'external_valid'}:
            raise ValueError('incomplete S control functions')
        paths = {}
        for name, entry in model['functions'].items():
            m = entry['function']
            reserve = entry['reserve_ps']
            if not math.isfinite(reserve) or reserve < 0:
                raise ValueError('invalid S reserve')
            prices = []
            for q in qs:
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
                               guarded_required_ps=max(p['guarded_required_ps'] for p in prices), sources=prices)
        return dict(status='diagnostic_estimate', paths=paths,
                    actual_arithmetic_S_qualified=False, price_qualification_granted=False)
    except (KeyError, ValueError, TypeError, OverflowError) as error:
        return dict(status='cost_uncovered', reason=str(error))
