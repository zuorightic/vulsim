"""Synthetic state banks with explicit variable slots, resets and valid/control chains."""
VERSION = 'arithmetic-state-bank-features-v1'


def reset_value(width, pattern, word, level):
    if pattern not in ('zero', 'one', 'alternating', 'one_in_three'):
        raise ValueError('unregistered reset pattern')
    if pattern == 'zero':
        return 0
    if pattern == 'one':
        return (1 << width)-1
    modulus = 2 if pattern == 'alternating' else 3
    return sum(1 << bit for bit in range(width) if (bit+word+level) % modulus == 0)


def specifications(config):
    result = []
    for w in config['word_widths']:
        result.append(dict(id=f'state-train-small-w{w}', split='train', max_width=w,
            words=[{'declared_width': w, 'variable_width': w}], depth=1,
            enable_domains=1, enable_source_policy='valid_chain', reset_pattern='zero'))
    for index, w in enumerate(config['large_train_max_widths']):
        count = min(config['max_parallel_words'], 608//w,
                    (config['max_state_bits']-8)//(4*w))
        result.append(dict(id=f'state-train-large-w{w}', split='train', max_width=w,
            words=words(config, w, count, index % 2 == 1, index), depth=3,
            enable_domains=3, enable_source_policy='separate_registered' if index % 2 else 'valid_chain', reset_pattern='one'))
    for split, count, depth, groups, pattern in (
        ('validation', 6, 2, 2, 'alternating'), ('test', 7, 3, 3, 'one_in_three')):
        for index, w in enumerate(config['validation_test_max_widths']):
            result.append(dict(id=f'state-{split}-w{w}', split=split, max_width=w,
                words=words(config, w, count, index % 2 == (0 if split == 'validation' else 1), index+3),
                depth=depth, enable_domains=groups, enable_source_policy='valid_chain', reset_pattern=pattern))
    for s in result:
        s['slots'] = []
        for level in range(s['depth']+1):
            for word, geometry in enumerate(s['words']):
                v = geometry['variable_width']
                s['slots'].append({**geometry, 'word': word, 'level': level,
                    'name': f'src{word}' if level == 0 else f'dst{level}_{word}',
                    'enable_domain': (word+level) % s['enable_domains'],
                    'reset_value': reset_value(v, s['reset_pattern'], word, level)})
        s['valid_registers'] = s['depth']+1
        s['separate_enable_registers'] = s['enable_domains'] if s['enable_source_policy'] == 'separate_registered' else 0
        s['features'] = features(s, 1500)
        s['input_bits'] = sum(w['variable_width'] for w in s['words'])+s['separate_enable_registers']+1
        s['capture_bits'] = sum(w['variable_width'] for w in s['words'])*s['depth']+s['valid_registers']
        if (s['input_bits'] > config['max_input_bits'] or s['capture_bits'] > config['max_capture_bits']
            or s['features']['state_bits'] > config['max_state_bits']
            or s['features']['state_signals'] > config['max_state_signals']):
            raise ValueError('state bank exceeds preregistered capacity: '+s['id'])
    return result


def words(config, maximum, count, mixed, offset):
    palette = [w for w in config['word_widths'] if w <= maximum]
    values = [maximum]+[palette[(offset+3*i) % len(palette)] if mixed else maximum for i in range(1, count)]
    result = [{'declared_width': w, 'variable_width': w} for w in values]
    if mixed and maximum == 65:
        result[0]['variable_width'] = 64
    return result


def features(s, period):
    slots = s['slots']
    data_bits = sum(x['variable_width'] for x in slots)
    valid_bits = s['valid_registers']+s['separate_enable_registers']
    return {'state_bits': data_bits+valid_bits, 'state_signals': len(slots)+valid_bits,
        'data_bits': data_bits, 'data_signals': len(slots), 'valid_bits': valid_bits,
        'valid_signals': valid_bits, 'enable_domains': s['enable_domains'],
        'reset_one_bits': sum(x['reset_value'].bit_count() for x in slots),
        'max_declared_width': max(x['declared_width'] for x in slots),
        'min_variable_width': min(x['variable_width'] for x in slots), 'sdc_period_ps': period}


def source(s):
    ports = ['input wire clk,rstn,iv']
    ports += [f'input wire [{w["variable_width"]-1}:0] in{j}' for j, w in enumerate(s['words'])]
    ports += [f'input wire en{j}' for j in range(s['separate_enable_registers'])]
    bank_ports = ports+['output wire y,ov']
    text = ['(* keep_hierarchy=1 *) module StateBank('+','.join(bank_ports)+');']
    for j in range(s['separate_enable_registers']):
        text += [f'(* keep *) reg enable_q{j};',
            f'(* keep *) always @(posedge clk) if(!rstn)enable_q{j}<=0;else enable_q{j}<=en{j};']
    for j in range(s['valid_registers']):
        previous = 'iv' if j == 0 else f'valid_q{j-1}'
        text += [f'(* keep *) reg valid_q{j};',
            f'(* keep *) always @(posedge clk) if(!rstn)valid_q{j}<=0;else valid_q{j}<={previous};']
    for slot in s['slots']:
        name, w = slot['name'], slot['variable_width']
        level, word = slot['level'], slot['word']
        previous = f'in{word}' if level == 0 else f'src{word}' if level == 1 else f'dst{level-1}_{word}'
        enable = ('enable_q' if s['separate_enable_registers'] else 'valid_q')+str(slot['enable_domain'])
        text += [f'(* keep *) reg [{w-1}:0] {name};',
            f'(* keep *) always @(posedge clk) if(!rstn){name}<={w}\'h{slot["reset_value"]:x};else if({enable}){name}<={previous};']
        if slot['declared_width'] > w:
            padding = slot['declared_width']-w
            text.append(f'wire [{slot["declared_width"]-1}:0] logical_{name}={{{padding}\'b0,{name}}};')
    result_bits = sum(w['declared_width'] for w in s['words'])
    captured = ','.join(('logical_' if s['words'][word]['declared_width'] > s['words'][word]['variable_width'] else '')+
        f'dst{s["depth"]}_{word}' for word in reversed(range(len(s['words']))))
    text += [f'wire [{result_bits-1}:0] observed={{{captured}}};',
        f'assign ov=valid_q{s["valid_registers"]-1};',
        f'StateObserver observer(.value(observed),.y(y));', 'endmodule',
        f'(* keep_hierarchy=1 *) module StateObserver(input wire [{result_bits-1}:0] value,output wire y);assign y=^value;endmodule']
    top_ports = ports+['output wire y,ov']
    connections = ['.clk(clk)', '.rstn(rstn)', '.iv(iv)', '.y(y)', '.ov(ov)']
    connections += [f'.in{j}(in{j})' for j in range(len(s['words']))]
    connections += [f'.en{j}(en{j})' for j in range(s['separate_enable_registers'])]
    text += ['module ModelBundle('+','.join(top_ports)+');StateBank bank('+','.join(connections)+');endmodule']
    data = ['bank/src*', 'bank/dst*', 'bank/y*']
    labels = [
        {'id': 'state_data', 'source_cells': data, 'target_cells': data, 'role': 'state_data'},
        {'id': 'state_enable', 'source_cells': 'bank/enable_q*' if s['separate_enable_registers'] else ['bank/valid_q*', 'bank/ov*'],
         'target_cells': data, 'role': 'state_enable'},
        {'id': 'state_valid', 'source_cells': ['bank/valid_q*', 'bank/ov*'],
         'target_cells': ['bank/valid_q*', 'bank/ov*'], 'role': 'state_valid'}]
    return '\n'.join(text)+'\n', labels


def step(s, state, inputs, reset):
    """Independent simultaneous-register transition for software/RTL checks."""
    old = dict(state)
    result = {}
    for slot in s['slots']:
        name, level, word = slot['name'], slot['level'], slot['word']
        previous = f'in{word}' if level == 0 else f'src{word}' if level == 1 else f'dst{level-1}_{word}'
        value = inputs[previous] if level == 0 else old[previous]
        enable = ('enable_q' if s['separate_enable_registers'] else 'valid_q')+str(slot['enable_domain'])
        result[name] = slot['reset_value'] if reset else value if old[enable] else old[name]
    for j in range(s['separate_enable_registers']):
        result[f'enable_q{j}'] = 0 if reset else inputs[f'en{j}']
    for j in range(s['valid_registers']):
        result[f'valid_q{j}'] = 0 if reset else inputs['iv'] if j == 0 else old[f'valid_q{j-1}']
    return result
