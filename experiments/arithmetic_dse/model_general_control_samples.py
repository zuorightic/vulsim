"""Fresh control-load S contexts; no previous physical test label is read."""
import math

from . import model_general_state_samples as base
from . import model_general_state_samples_v2 as retained

VERSION = 'general-state-control-load-contract-v1'
source = retained.source
step = retained.step


def control_features(s):
    stages = []
    for stage in range(1, s['depth'] + 1):
        slots = [x for x in s['slots'] if x['stage'] == stage]
        stages.append({'stage': stage, 'enable_data_bits': sum(x['variable_bits'] for x in slots),
            'enable_words': len(slots), 'reset_one_bits': sum(x['reset'].bit_count() for x in slots),
            'valid_D_targets': 1, 'observer_valid_targets': 1})
    largest = max(x['enable_data_bits'] for x in stages)
    return {'one': 1, 'native_enable_bits_max': largest,
        'native_enable_bits_sqrt': math.sqrt(largest), 'native_enable_bits_log2': math.log2(1 + largest),
        'native_enable_words_max': max(x['enable_words'] for x in stages),
        'native_valid_targets_max': largest + 2,
        'native_data_bits': sum(x['variable_bits'] for x in s['slots']),
        'native_reset_one_bits': sum(x['reset'].bit_count() for x in s['slots']),
        'input_data_bits': sum(r['width'] for r in s['roots']),
        'external_data_bits': sum(s['words'][j]['variable_bits'] for j in s['external_words'])}


def features(s, period):
    return {**base.features(s, period), **{'control_' + k: v for k, v in control_features(s).items()}}


def specifications(cfg):
    original = retained.specifications(cfg)
    old_signatures = {s['semantic_signature'] for s in original}
    result = []
    for number, previous in enumerate(original):
        # Rebuild semantic geometry, then re-salt all reset and source relations.
        s = {**previous}; split = s['split']; index = int(s['id'].rsplit('-', 1)[1])
        s['id'] = f'general-control-{split}-{index:02d}'; s['depth'] = 2
        seed = cfg['new_source_seed'] + '/' + split + '/' + str(index)
        s['roots'] = [{**r, 'reset': base.bits(seed + '/root/' + str(j), r['width'])} for j, r in enumerate(s['roots'])]
        count = sum(r['width'] for r in s['roots'])
        packed = sum(r['reset'] << sum(q['width'] for q in s['roots'][:j]) for j, r in enumerate(s['roots']))
        pairs = [(a, b) for b in range(1, count) for a in range(b)]
        cursor = base.bits(seed + '/pairs', 64) % len(pairs)
        s['words'] = []
        # Fractions include low, mixed, and almost-all second-cut enables.
        phase = {'train': 0, 'validation': 2, 'test': 4}[split]
        threshold = [2, 3, 4, 5, 6, 7][(index + phase) % 6]
        for j, old in enumerate(previous['words']):
            w = {**old}; width = w['variable_bits']
            selected = [pairs[(cursor + k) % len(pairs)] for k in range(width)]; cursor += width
            w['source_positions'] = [a for a, _ in selected]; w['source_positions_second'] = [b for _, b in selected]
            w['reset'] = base.bits(seed + '/word/' + str(j), width)
            initial = sum((((packed >> a) ^ (packed >> b)) & 1) << k for k, (a, b) in enumerate(selected))
            w['invert'] = initial ^ w['reset']
            stage = 2 if (j * 3 + index + phase) % 8 < threshold else 1
            w['start'] = w['end'] = stage
            if j == 0 and index % 3 != 0:
                w['start'], w['end'] = 1, 2
            s['words'].append(w)
        # Keep an input-enabled bank and terminal external data in every source.
        s['words'][-1]['start'] = s['words'][-1]['end'] = 2
        s['words'][1]['start'] = s['words'][1]['end'] = 1
        s['slots'] = [{'name': f'data_{j}_s{k}', 'word': j, 'stage': k,
            'variable_bits': w['variable_bits'], 'reset': w['reset']}
            for j, w in enumerate(s['words']) for k in range(w['start'], w['end'] + 1)]
        s['external_words'] = []; external_bits = 0
        for j, w in enumerate(s['words']):
            if w['end'] == 2 and external_bits + w['variable_bits'] <= cfg['max_external_data_bits']:
                s['external_words'].append(j); external_bits += w['variable_bits']
        s['expected_FF_bits'] = {'input_service': count + 1,
            'native_state': sum(x['variable_bits'] for x in s['slots']) + 2, 'external_state': external_bits + 1}
        s['features'] = features(s, 1500); s['semantic_signature'] = base.semantic_signature(s)
        if (s['semantic_signature'] in old_signatures or not s['external_words']
                or s['features']['native_data_bits'] > cfg['max_native_data_bits']):
            raise ValueError('control-load source duplicate or outside frozen S geometry')
        result.append(s)
    if len({s['semantic_signature'] for s in result}) != 24:
        raise ValueError('control-load sources not semantically independent')
    return result
