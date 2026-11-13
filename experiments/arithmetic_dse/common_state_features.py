"""Logical state/load features; no mapped cells or workload identifiers.

The load proxy counts distinct logical sink pins per variable input bit. It is
available before synthesis. A fitting experiment cannot by itself qualify its
use with a new source-adapter or actual arithmetic boundary.
"""
import math

VERSION = 'logical-state-load-numerical-period-v1'


def input_load_features(input_widths, sink_inputs):
    if (not input_widths or any(type(w) is not int or w <= 0 for w in input_widths)):
        raise ValueError('positive variable input widths required')
    n = sum(input_widths)
    counts = [0] * n
    for inputs in sink_inputs:
        if not inputs or any(type(bit) is not int or not 0 <= bit < n for bit in inputs):
            raise ValueError('logical sink outside input bits')
        # Multiple occurrences at the same sink do not create extra pins.
        for bit in set(inputs):
            counts[bit] += 1
    return dict(input_logical_uses=float(sum(counts)),
                input_loaded_bits=float(sum(c > 0 for c in counts)),
                input_max_bit_load=float(max(counts, default=0)),
                input_log_load_sum=sum(math.log2(c + 1) for c in counts),
                input_sqrt_load_sum=sum(math.sqrt(c) for c in counts))


def bank_features(spec, target):
    if not math.isfinite(target) or target <= 0:
        raise ValueError('positive numerical target required')
    sinks = []
    for word in spec['words']:
        first = word['source_positions']
        second = word.get('source_positions_second')
        if second is None:
            sinks.extend([[bit] for bit in first])
        else:
            if len(first) != len(second):
                raise ValueError('state adapter operand dimensions')
            sinks.extend([list(pair) for pair in zip(first, second)])
    roots, slots = spec['roots'], spec['slots']
    external = [spec['words'][i] for i in spec['external_words']]
    mode = spec['service_mode']
    owners = dict(
        input_service=dict(data_bits=sum(r['width'] for r in roots),
                           data_signals=len(roots), valid_bits=1,
                           enable_domains=1 if mode == 1 else len(roots) + (mode != 2),
                           reset_one_bits=sum(r['reset'].bit_count() for r in roots)),
        native_state=dict(data_bits=sum(s['variable_bits'] for s in slots),
                          data_signals=len(slots), valid_bits=spec['depth'],
                          enable_domains=len({s['stage'] for s in slots}),
                          reset_one_bits=sum(s['reset'].bit_count() for s in slots)),
        external_state=dict(data_bits=sum(w['variable_bits'] for w in external),
                            data_signals=len(external), valid_bits=1, enable_domains=0,
                            reset_one_bits=sum(w['reset'].bit_count() for w in external)))
    load = input_load_features([r['width'] for r in roots], sinks)
    total = sum(spec['expected_FF_bits'].values())
    common = dict(one=1., target_ps=float(target), log2_target=math.log2(target / 500.),
                  clock_pressure=1500. / target, total_FF_bits=float(total),
                  sqrt_FF_bits=math.sqrt(total), parallel_words=float(len(spec['words'])),
                  max_variable_word_bits=float(max(w['variable_bits'] for w in spec['words'])),
                  native_enable_data_bits=float(sum(s['variable_bits'] for s in slots)),
                  service_mode=float(mode), **load)
    for owner, f in owners.items():
        f.update(common)
        f['pressure_data_bits'] = f['data_bits'] * common['clock_pressure']
        f['log2_data_bits'] = math.log2(f['data_bits'] + 1)
    return owners
