"""Static, portable features for target-conditioned native multiplier intervals."""
import math
import struct
from .model_mul_intervals import context_features, key
from .model_features import infer as portable_infer

BASE_FEATURES = ('width', 'width_squared', 'log_width', 'capture_bits', 'input_bits',
                 'block_width', 'first', 'last', 'capture_fanout', 'width_fanout', 'log_width_fanout')
TARGET_FEATURES = ('sdc_period_ps', 'reference_delay_ps', 'reference_overhead_ps',
                   'pressure', 'tightness', 'width_tightness', 'load_tightness', 'width_squared_tightness')
FEATURES = BASE_FEATURES + TARGET_FEATURES


def f32(x): return struct.unpack('f', struct.pack('f', x))[0]


def sta_roundtrip_ps(x):
    scale = f32(1e-12)
    return f32(f32(x*scale)/scale)


def clock_request(raw, quantum=25):
    if not math.isfinite(raw) or raw <= 0: raise ValueError('positive finite target required')
    nominal = math.ceil(raw/quantum)*quantum
    for _ in range(40):
        period = sta_roundtrip_ps(nominal)
        scale = f32(1e-12)
        stable = f32(period*scale) == f32(nominal*scale)
        for desired in (period, .2*period):
            value = desired
            for _ in range(10):
                value = float(format(sta_roundtrip_ps(value), '.4f'))
                stable &= abs(value-desired) <= .500001e-4 and value > 0
        if stable: return {'requested_period_ps': period, 'nominal_grid_ps': nominal, 'unrounded_target_ps': raw}
        nominal += quantum
    raise ValueError('no stable representable clock in declared finite grid search')


def reference_values(reference, interval_key, width):
    entry = reference['intervals'][interval_key]
    anchors = entry['delay_anchors']
    if not anchors[0][0] <= width <= anchors[-1][0]: raise ValueError('reference width outside trained domain')
    for (w0, d0), (w1, d1) in zip(anchors, anchors[1:]):
        if w0 <= width <= w1:
            return d0+(d1-d0)*(width-w0)/(w1-w0), entry['overhead_ps']
    raise ValueError('missing reference anchor')


def features(spec, period, reference):
    d, h = reference_values(reference, key(spec), spec['width'])
    if not math.isfinite(period) or period <= h: raise ValueError('target has nonpositive reference data budget')
    pressure = (period-h)/d
    tightness = max(0., 1.5-pressure)
    result = context_features(spec, spec['fanout'])
    return {**result, 'sdc_period_ps': period, 'reference_delay_ps': d, 'reference_overhead_ps': h,
            'pressure': pressure, 'tightness': tightness, 'width_tightness': spec['width']*tightness,
            'load_tightness': spec['fanout']*tightness, 'width_squared_tightness': spec['width']**2*tightness}


def infer(predictor, values): return portable_infer(predictor, values, feature_names=FEATURES)
