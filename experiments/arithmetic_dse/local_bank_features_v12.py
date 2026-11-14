"""Capture-local affine sharing, before mapping or physical implementation.

Expressions are used only to count equivalence classes. Root identifiers,
bit masks, source names and target-specific keys never leave the extractor.
This remains the explicit affine bank adapter, not arbitrary arithmetic S.
"""
from collections import Counter, defaultdict
import math

from . import transition_incidence_features_v10 as previous

VERSION = 'capture-local-affine-sharing-v12'


def bank_profiles(query):
    roots, words = previous.validate_semantics(query)
    packed = [bit for root in roots for bit in root]
    indexed = []
    offset = 0
    for word in words:
        size = len(word['reset_bits'])
        indexed.append((word,query['input_sink_inputs'][offset:offset+size]))
        offset += size
    profiles = []
    for stage in range(1,len(query['stage_words'])+1):
        born, raw, normalized = Counter(), Counter(), Counter()
        phases, degrees = Counter(), Counter()
        total = ones = births = cross = uses = 0
        for index,(word,inputs) in enumerate(indexed):
            if not word['start'] <= stage <= word['end']:
                continue
            for bit,(reset,invert,sink) in enumerate(zip(
                    word['reset_bits'],word['invert_bits'],inputs,strict=True)):
                total += 1
                ones += reset
                if word['start'] != stage:
                    # Kept FFs remain distinct even when their reset matches.
                    raw['retained',index,bit] += 1
                    normalized['retained',index,bit] += 1
                    continue
                births += 1
                key = tuple(sorted(sink))
                born[key] += 1
                raw['birth',key,invert] += 1
                normalized['birth',key,invert ^ reset] += 1
                for root in key:
                    phases[root,invert] += 1
                    degrees[root] += 1
                    cross += packed[root] != reset
                    uses += 1
        root_mass = sum(n*n for n in degrees.values())
        phase_mass = sum(n*n for n in phases.values())
        values = dict(
            local_log2_capture_bits=math.log2(1+total),
            local_reset_one_fraction=ones/max(1,total),
            local_birth_fraction=births/max(1,total),
            local_birth_alias_fraction=(births-len(born))/max(1,births),
            local_raw_alias_fraction=(total-len(raw))/max(1,total),
            local_normalized_alias_fraction=(total-len(normalized))/max(1,total),
            local_log2_peak_birth_uses=math.log2(1+max(born.values(),default=0)),
            local_log2_phase_concentration=math.log2(1+phase_mass/max(1,uses)),
            local_phase_split_fraction=(root_mass-phase_mass)/max(1,root_mass),
            local_reset_cross_fraction=cross/max(1,uses))
        profiles.append(values)
    return profiles


def augment(query, controls):
    profiles = bank_profiles(query)
    result = []
    for control in controls:
        item = dict(control,features=dict(control['features']))
        if item['path_class'] in ('native_valid','native_enable'):
            values = profiles[item['stage']]
            f = item['features']
            f.update(values)
            for name in ('local_raw_alias_fraction','local_phase_split_fraction',
                         'local_reset_cross_fraction','local_log2_phase_concentration'):
                f['native_'+name] = f['branch_native']*values[name]
                f['T_'+name] = f['log2_target']*values[name]
        result.append(item)
    return result


def state_controls(query, context_function):
    return augment(query,previous.state_controls(query,context_function))
