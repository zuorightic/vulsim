"""Explicit affine state semantics and logical cone spans, before mapping.

Masks are validated semantic data, not numerical price keys. Models consume
permutation-invariant load/polarity moments and per-word transition fractions.
The affine adapter is intentionally explicit; unknown birth logic is rejected.
"""
from collections import Counter
import math
from . import semantic_fanout_features_v8 as previous
from . import common_mechanism_features_v1 as legacy
from . import centered_response as response

VERSION = 'semantic-reset-cone-features-v9'
SEMANTICS = 'retained-affine-state-semantics-v1'


def state_structure(spec, target):
    query = legacy.state_structure(spec, target)
    query['reset_semantics'] = dict(version=SEMANTICS,
        input_bits=[[(r['reset'] >> bit) & 1 for bit in range(r['width'])] for r in spec['roots']],
        words=[dict(reset_bits=[(w['reset'] >> bit) & 1 for bit in range(w['variable_bits'])],
                    invert_bits=[(w['invert'] >> bit) & 1 for bit in range(w['variable_bits'])],
                    start=w['start'], end=w['end'], external=i in spec['external_words'])
               for i, w in enumerate(spec['words']) if w['variable_bits']])
    validate_semantics(query)
    return query


def validate_semantics(query):
    meta = query['reset_semantics']
    if meta['version'] != SEMANTICS:
        raise ValueError('explicit retained affine reset semantics required')
    roots, words = meta['input_bits'], meta['words']
    widths, stages, sinks = query['input_widths'], query['stage_words'], query['input_sink_inputs']
    if (not isinstance(roots, list) or len(roots) != len(widths) or not isinstance(words, list)
            or not 1 <= len(words) <= 4096 or sum(widths) > 1048576):
        raise ValueError('bounded reset semantics dimensions required')
    def bits(values, width):
        if not isinstance(values, list) or len(values) != width or any(type(v) is not int or v not in (0,1) for v in values):
            raise ValueError('explicit reset/polarity bits required')
    for reset, width in zip(roots, widths, strict=True):
        bits(reset, width)
    packed = [b for reset in roots for b in reset]
    if sum(packed) != query['input_reset_one_bits']:
        raise ValueError('input reset count contradicts semantics')
    offset = 0
    for word in words:
        reset, invert = word['reset_bits'], word['invert_bits']
        if not isinstance(reset, list) or not 1 <= len(reset) <= 4096:
            raise ValueError('bounded retained word required')
        bits(reset, len(reset)); bits(invert, len(reset))
        start, end = word['start'], word['end']
        if (type(start) is not int or type(end) is not int or not 1 <= start <= end <= len(stages)
                or type(word['external']) is not bool or (word['external'] and end != len(stages))):
            raise ValueError('reset word lifetime/external contract differs')
        for bit, (r, inv) in enumerate(zip(reset, invert, strict=True)):
            if offset + bit >= len(sinks):
                raise ValueError('reset adapter sink dimensions differ')
            inputs = sinks[offset + bit]
            if (not isinstance(inputs, list) or len(inputs) not in (1,2) or len(set(inputs)) != len(inputs)
                    or any(type(n) is not int or not 0 <= n < len(packed) for n in inputs)):
                raise ValueError('affine adapter requires one or two distinct input roots')
            if (sum(packed[n] for n in inputs) + inv) % 2 != r:
                raise ValueError('reset and affine birth polarity disagree')
        offset += len(reset)
    if offset != len(sinks):
        raise ValueError('reset adapter sink dimensions differ')
    expected = [[len(w['reset_bits']) for w in words if w['start'] <= stage <= w['end']]
                for stage in range(1, len(stages)+1)]
    ones = [sum(sum(w['reset_bits']) for w in words if w['start'] <= stage <= w['end'])
            for stage in range(1, len(stages)+1)]
    if (expected != stages or ones != query['stage_reset_one_bits']
            or sum(len(w['reset_bits']) for w in words if w['external']) != query['external_bits']):
        raise ValueError('retained reset semantics contradict stage projection')
    return roots, words


def transition(groups):
    edges = sum(max(0,len(g)-1) for g in groups)
    return sum(a != b for g in groups for a,b in zip(g,g[1:])) / max(1,edges)


def base_state_controls(query):
    roots, words = validate_semantics(query)
    controls = previous.base_state_controls(query)
    root_bits = [b for group in roots for b in group]
    counts = Counter(n for sink in query['input_sink_inputs'] for n in sink)
    pairs = Counter(tuple(sorted(sink)) for sink in query['input_sink_inputs'])
    extra = {'input_'+k:v for k,v in previous.load_moments(counts.values()).items()}
    extra['input_pair_reuse_fraction'] = (sum(pairs.values())-len(pairs))/max(1,sum(pairs.values()))
    invert = [b for word in words for b in word['invert_bits']]
    polarized = Counter((tuple(sorted(sink)), inv) for sink,inv in zip(query['input_sink_inputs'],invert,strict=True))
    mass = sum(counts.values())
    global_features = dict(
        reset_root_weighted_fraction=sum(degree*root_bits[n] for n,degree in counts.items())/max(1,mass),
        reset_root_transition_fraction=transition(roots),
        reset_birth_invert_fraction=sum(invert)/max(1,len(invert)),
        reset_birth_transition_fraction=transition([w['invert_bits'] for w in words]),
        reset_polarized_unique_fraction=len(polarized)/max(1,len(invert)),
        reset_opposite_pair_fraction=sum((pair,0) in polarized and (pair,1) in polarized for pair in pairs)/max(1,len(pairs)))
    for q in controls:
        f, stage = q['features'], q['stage']
        native, reset, logt = f['branch_native'], f['reset_has_one'], f['log2_target']
        f.update(extra)
        for name in ['input_log2_concentration','input_pair_reuse_fraction','input_log2_repair_excess']:
            f['native_'+name] = native*extra[name]
            f['reset_'+name] = reset*extra[name]
        f['input_concentration_log_T'] = extra['input_log2_concentration']*logt
        f['native_input_concentration_log_T'] = native*extra['input_log2_concentration']*logt
        if q['path_class'] == 'input_valid':
            capture = roots
        elif q['path_class'] == 'external_valid':
            capture = [w['reset_bits'] for w in words if w['external']]
        else:
            capture = [w['reset_bits'] for w in words if w['start'] <= stage+1 <= w['end']]
        source = roots if not native else [w['reset_bits'] for w in words if w['start'] <= stage <= w['end']]
        f.update(global_features)
        f['reset_capture_transition_fraction'] = transition(capture)
        f['reset_source_transition_fraction'] = transition(source)
        for name in ['reset_root_weighted_fraction','reset_birth_invert_fraction','reset_capture_transition_fraction','reset_birth_transition_fraction']:
            f['native_'+name] = native*f[name]
            f[name+'_log_T'] = f[name]*logt
    return controls


def state_controls(query, context_function):
    controls = base_state_controls(query)
    enable = {q['stage']:response.predict(context_function,q['features']) for q in controls if q['path_class']=='native_enable'}
    if not enable or any(not math.isfinite(v) or v <= 0 for v in enable.values()):
        raise ValueError('nonpositive predicted enable context')
    target = query['target_ps']
    for q in controls:
        f = q['features']; value = enable[min(q['stage'],max(enable))]
        pressure = math.log2(1+value/target)
        relaxation = (.25*max(0.,target-value)+.01*value)/target
        native, reset = f['branch_native'],f['reset_has_one']
        f.update(enable_context_R_ps=value,predicted_enable_pressure=pressure,
                 native_enable_pressure=native*pressure,reset_enable_pressure=reset*pressure,
                 native_reset_enable_pressure=native*reset*pressure,predicted_enable_relaxation=relaxation,
                 native_enable_relaxation=native*relaxation)
    return controls


def cone_spans(circuit, outputs):
    live, pending = set(), list(outputs)
    while pending:
        node = pending.pop()
        if node not in circuit.nodes or node in live:
            continue
        live.add(node); kind,a,b = circuit.nodes[node]
        pending.append(a)
        if kind != 'not': pending.append(b)
    spans = {node:(name[-1],name[-1]) for name,node in circuit.leaves.items()
             if isinstance(name,tuple) and len(name)==2 and name[0]!='cin'}
    ranges = []
    for node in sorted(live):
        kind,a,b = circuit.nodes[node]
        children = [spans[n] for n in ([a] if kind=='not' else [a,b]) if n in spans]
        if children:
            lo,hi = min(v[0] for v in children),max(v[1] for v in children)
            spans[node]=(lo,hi);ranges.append((lo,hi))
    cuts = Counter()
    for lo,hi in ranges:
        cuts[lo]+=1;cuts[hi]-=1
    count=peak=0
    for _,delta in sorted(cuts.items()):
        count+=delta;peak=max(peak,count)
    return dict(log2_total_span=math.log2(1+sum(hi-lo for lo,hi in ranges)),
                log2_peak_cut=math.log2(1+peak),
                local_fraction=sum(lo==hi for lo,hi in ranges)/max(1,len(ranges)))


def operator_features(query):
    f = previous.operator_features(query)
    c,outputs = previous.circuits.operator_circuit(query['local_context']['producer'])
    f.update({'cone_'+k:v for k,v in cone_spans(c,outputs).items()})
    f['cone_cut_pressure'] = f['cone_log2_peak_cut']*f['clock_pressure']
    return f


def reduction_features(query):
    f = previous.reduction_features(query)
    extra = {}
    for serial in (False,True):
        c,outputs,_ = previous.circuits.reduction_circuit(query,serial=serial)
        extra.update({'cone_'+('serial_' if serial else 'fused_')+k:v for k,v in cone_spans(c,outputs).items()})
    extra['cone_serial_cut_gap'] = extra['cone_serial_log2_peak_cut']-extra['cone_fused_log2_peak_cut']
    extra['cone_cut_pressure'] = extra['cone_fused_log2_peak_cut']*f['intensive']['clock_pressure']
    for values in f.values(): values.update(extra)
    return f
