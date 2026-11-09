"""Real local producer/consumer shells. No physical labels or model prices.

Only demanded unsigned bits are implemented. Independent consumer inputs are
explicit; source correlations belong to the subsequent frozen-base G study.
"""
import hashlib
import json
from copy import deepcopy

from . import model_fast_samples as arithmetic
from .model_fast_measurement import known_result

VERSION = 'arithmetic-local-consumer-shell-v1'


def identity(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def validate(features):
    if set(features) != {'producer', 'consumers', 'captures'}:
        raise ValueError('explicit producer, consumers and captures required')
    producer = arithmetic.validate(features['producer'])
    if not features['consumers'] and not features['captures']:
        raise ValueError('unobserved producer')
    for consumer in features['consumers']:
        if set(consumer) != {'spec', 'bindings', 'other_dynamic_inputs'}:
            raise ValueError('unknown consumer field')
        arithmetic.validate(consumer['spec'])
        if consumer['other_dynamic_inputs'] != 'independent_launch; source correlations require G validation':
            raise ValueError('undeclared consumer input correlation')
        operands = set()
        for binding in consumer['bindings']:
            if set(binding) != {'operand_index', 'result_bit_map'} or type(binding['operand_index']) is not int:
                raise ValueError('invalid operand binding')
            index = binding['operand_index']
            if index not in (0, 1) or index in operands:
                raise ValueError('duplicate or invalid bound operand')
            operands.add(index)
            prefix = ('lhs', 'rhs')[index]
            check_map(binding['result_bit_map'], consumer['spec'][prefix + '_width'], producer['result_width'])
            if any(bit != 'undemanded' for bit in binding['result_bit_map'][consumer['spec']['result_width']:]):
                raise ValueError('unused high operand bits must be explicit undemanded')
        if not operands or not any(type(bit) is int for b in consumer['bindings'] for bit in b['result_bit_map']):
            raise ValueError('consumer does not use producer')
    for capture in features['captures']:
        if set(capture) != {'banks', 'declared_width', 'result_bit_map'} or type(capture['banks']) is not int or not 1 <= capture['banks'] <= 4:
            raise ValueError('invalid capture bank geometry')
        check_map(capture['result_bit_map'], capture['declared_width'], producer['result_width'])
    return features


def check_map(mapping, width, producer_width):
    if type(width) is not int or not 1 <= width <= 257 or len(mapping) != width:
        raise ValueError('incomplete bit map')
    for bit in mapping:
        if type(bit) is int:
            if not 0 <= bit < producer_width:
                raise ValueError('producer bit outside demanded result')
        elif type(bit) is not str or bit not in ('0', '1', 'external', 'undemanded'):
            raise ValueError('unknown bit origin')


def layout(features):
    validate(features)
    inputs = []; node_inputs = []; captures = []
    pzero, pone = known_result(features['producer'])

    def allocate(label):
        inputs.append(label)
        return ('input', len(inputs) - 1)

    def mapped(bit):
        if type(bit) is int:
            return '0' if pzero >> bit & 1 else '1' if pone >> bit & 1 else ('producer', bit)
        return allocate('capture_external') if bit == 'external' else '0' if bit == 'undemanded' else bit

    def operands(spec, bindings, label):
        result = []
        for index, prefix in enumerate(('lhs', 'rhs')):
            zero, one = (int(spec.get(prefix + '_' + k + '_hex', '0'), 16) for k in ('zero', 'one'))
            row = []
            for i in range(spec[prefix + '_width']):
                if i >= spec['result_width']:
                    token = '0'
                elif zero >> i & 1 or one >> i & 1:
                    token = '1' if one >> i & 1 else '0'
                    if index in bindings and bindings[index][i] not in (token, 'external'):
                        supplied = mapped(bindings[index][i])
                        if supplied != token:
                            raise ValueError('bound operand contradicts known bit')
                elif index in bindings:
                    token = mapped(bindings[index][i])
                else:
                    token = allocate(label + '/' + prefix + '/' + str(i))
                row.append(token)
            result.append(row)
        carry = spec.get('carry', 'zero')
        result.append([allocate(label + '/carry') if carry == 'dynamic' else '1' if carry == 'one' else '0'])
        return result

    node_inputs.append(operands(features['producer'], {}, 'producer'))
    for i, consumer in enumerate(features['consumers']):
        node_inputs.append(operands(consumer['spec'], {b['operand_index']: b['result_bit_map'] for b in consumer['bindings']}, 'consumer' + str(i)))
        z, o = known_result(consumer['spec'])
        tokens = ['0' if z >> bit & 1 else '1' if o >> bit & 1 else ('consumer' + str(i), bit)
                  for bit in range(consumer['spec']['result_width'])]
        captures.append(dict(id='consumer' + str(i), tokens=tokens))
    for i, capture in enumerate(features['captures']):
        tokens = [mapped(bit) for bit in capture['result_bit_map']]
        for bank in range(capture['banks']):
            captures.append(dict(id='direct' + str(i) + 'bank' + str(bank), tokens=tokens))
    for capture in captures:
        # A duplicated bit within one logical bank is one physical state bit.
        capture['live_tokens'] = list(dict.fromkeys(t for t in capture['tokens'] if isinstance(t, tuple)))
    if not inputs or not any(c['live_tokens'] for c in captures):
        raise ValueError('fully constant local context has no measured operator')
    return dict(inputs=inputs, node_inputs=node_inputs, captures=captures,
                input_bits=len(inputs), output_bits=sum(len(c['tokens']) for c in captures),
                undemanded_policy='zero substitution only above proven unsigned low-result demand',
                independent_consumer_inputs=True)


def evaluate(features, input_word):
    geometry = layout(features); values = {}
    def bit(token):
        if isinstance(token, str):
            return int(token)
        kind, index = token
        return (input_word if kind == 'input' else values[kind]) >> index & 1
    def vector(tokens):
        return sum(bit(t) << i for i, t in enumerate(tokens))
    specs = [features['producer']] + [c['spec'] for c in features['consumers']]
    for index, (spec, operands) in enumerate(zip(specs, geometry['node_inputs'])):
        a, b, carry = [vector(row) for row in operands]
        # Independent arbitrary-precision reference, including finite-bit masks.
        for prefix, value in (('lhs', a), ('rhs', b)):
            mask = (1 << spec[prefix + '_width']) - 1
            value = (value & mask & ~int(spec.get(prefix + '_zero_hex', '0'), 16)) | int(spec.get(prefix + '_one_hex', '0'), 16)
            if prefix == 'lhs': a = value
            else: b = value
        result = a * b if spec['operation'] == 'mul' else a + b + carry
        values['producer' if index == 0 else 'consumer' + str(index - 1)] = result & ((1 << spec['result_width']) - 1)
    result = 0; offset = 0
    for capture in geometry['captures']:
        result |= vector(capture['tokens']) << offset
        offset += len(capture['tokens'])
    return result


def source(features, name='ModelBundle'):
    if not name.isidentifier():
        raise ValueError('safe module identifier required')
    g = layout(features); parts = []; specs = [features['producer']] + [c['spec'] for c in features['consumers']]
    for i, spec in enumerate(specs):
        child = name + ('Producer' if i == 0 else 'Consumer' + str(i - 1))
        marker = '(* keep_hierarchy=1 *) module ' + child + '('
        parts.append(arithmetic.source(spec, child).split(marker)[0])
    n, r = g['input_bits'], g['output_bits']
    parts.append(f'''(* keep_hierarchy=1 *) module {name}Launch(input wire clk,rstn,iv,input wire [{n-1}:0] data,output reg [{n-1}:0] value,output reg valid);
always @(posedge clk)if(!rstn)begin value<=0;valid<=0;end else begin valid<=iv;if(iv)value<=data;end
endmodule
(* keep_hierarchy=1 *) module {name}Capture(input wire clk,rstn,iv,input wire [{r-1}:0] value,output wire [{r-1}:0] data,output reg valid);
always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;
''')
    offset = 0
    for i, capture in enumerate(g['captures']):
        live = capture['live_tokens']; positions = {t: j for j, t in enumerate(live)}
        if live:
            first = {t: capture['tokens'].index(t) + offset for t in live}
            expr = ','.join('value[' + str(first[t]) + ']' for t in reversed(live))
            parts.append(f'(* keep,dont_touch *) reg [{len(live)-1}:0] storage{i};always @(posedge clk)storage{i}<={{{expr}}};\n')
        for j, token in enumerate(capture['tokens']):
            rhs = "1'b" + token if isinstance(token, str) else f'storage{i}[{positions[token]}]'
            parts.append(f'assign data[{offset+j}]={rhs};\n')
        offset += len(capture['tokens'])
    parts.append(f'''endmodule
(* keep_hierarchy=1 *) module {name}Observer(input wire [{r-1}:0] data,output wire y);assign y=^data;endmodule
module {name}(input wire clk,rstn,iv,input wire [{n-1}:0] data,output wire y,ov);
wire [{n-1}:0] launched;wire launch_valid;wire [{r-1}:0] observed,results;
{name}Launch launch(.clk(clk),.rstn(rstn),.iv(iv),.data(data),.value(launched),.valid(launch_valid));
''')
    def token(t):
        return "1'b" + t if isinstance(t, str) else ('launched' if t[0] == 'input' else t[0]+'_value') + '[' + str(t[1]) + ']'
    def expr(tokens):
        return '{' + ','.join(token(t) for t in reversed(tokens)) + '}'
    for i, (spec, operands) in enumerate(zip(specs, g['node_inputs'])):
        net = 'producer' if i == 0 else 'consumer' + str(i - 1)
        module = name + ('ProducerCore' if i == 0 else 'Consumer' + str(i - 1) + 'Core')
        parts.append(f'wire [{spec["result_width"]-1}:0] {net}_value;\n')
        for j, row in enumerate(operands):
            parts.append(f'wire [{len(row)-1}:0] {net}_in{j}={expr(row)};\n')
        parts.append(f'{module} {"core" if i == 0 else net}(.a({net}_in0),.b({net}_in1),.cin({net}_in2),.value({net}_value));\n')
    offset = 0
    for capture in g['captures']:
        width = len(capture['tokens'])
        parts.append(f'assign results[{offset+width-1}:{offset}]={expr(capture["tokens"])};\n')
        offset += width
    parts.append(f'''{name}Capture capture(.clk(clk),.rstn(rstn),.iv(launch_valid),.value(results),.data(observed),.valid(ov));
{name}Observer observer(.data(observed),.y(y));
endmodule
''')
    return ''.join(parts)


def independent_context(spec, variant):
    """A fresh connection/consumer source; no full evaluation graph is copied."""
    r = spec['result_width']; shift = variant % 2
    width = min(257, r + shift)
    mapping = ['0'] * shift + list(range(r))
    consumer = dict(operation='add', lhs_width=width, rhs_width=max(1, width - 2 - variant), result_width=width,
                    carry='zero', capture_banks=1)
    return dict(producer=deepcopy(spec), consumers=[dict(spec=consumer,
        bindings=[dict(operand_index=0, result_bit_map=mapping)],
        other_dynamic_inputs='independent_launch; source correlations require G validation')], captures=[])


def generic_geometry(design, top, features):
    g = layout(features); module = design['modules'][top]
    def child(instance):
        return design['modules'][module['cells'][instance]['type']]
    launch, capture = child('launch'), child('capture')
    def flops(m):
        result = {}
        for name, cell in m['cells'].items():
            if 'DFF' in cell['type'].upper():
                if len(cell['connections'].get('Q', [])) != 1:
                    raise ValueError('scalar generic FF required')
                q = cell['connections']['Q'][0]
                if q in result: raise ValueError('multiply driven FF bit')
                result[q] = name
            elif 'LATCH' in cell['type'].upper():
                raise ValueError('unexpected latch')
        return result
    launch_ff, capture_ff = flops(launch), flops(capture)
    # Every statically demanded launch bit must survive; no padded state bank.
    for value in launch['ports']['value']['bits']:
        if value not in launch_ff: raise ValueError('lost demanded launch bit')
    if len(launch_ff) != g['input_bits'] + 1:
        raise ValueError('launch data/valid geometry differs')
    banks = {}; offset = 0; all_q = set()
    for bank in g['captures']:
        bits = capture['ports']['data']['bits'][offset:offset + len(bank['tokens'])]; offset += len(bits)
        variable = set()
        for token, value in zip(bank['tokens'], bits):
            if isinstance(token, str):
                if value != token: raise ValueError('proven capture constant differs')
            elif isinstance(value, int):
                if value not in capture_ff: raise ValueError('capture is not retained state')
                variable.add(value)
            elif value not in ('0', '1'):
                raise ValueError('undefined captured data')
        if variable & all_q: raise ValueError('independent banks merged')
        all_q |= variable; banks[bank['id']] = dict(FF_bits=len(variable), logical_width=len(bits))
    if len(capture_ff) != len(all_q) + 1:
        raise ValueError('unaccounted capture FF')
    operator_ports = {}
    for instance in ['core'] + ['consumer'+str(i) for i in range(len(features['consumers']))]:
        core = child(instance); inputs = {}
        for port in ('a','b','cin'):
            for i,bit in enumerate(core['ports'][port]['bits']):
                if isinstance(bit,int): inputs.setdefault(bit,[]).append([port,i])
        outputs=[]
        for i,bit in enumerate(core['ports']['value']['bits']):
            outputs.append(dict(bit=i,kind='constant' if isinstance(bit,str) else 'passthrough' if bit in inputs else 'logic',
                constant=bit if isinstance(bit,str) else None,aliases=inputs.get(bit,[])))
        operator_ports[instance]=dict(outputs=outputs,physical_port_binding_qualified=False,
            note='generic constants/pass-through are explicit; revalidate semantic port-to-net binding on mapped physical snapshot')
    return dict(owner_FF_bits={'input_service': len(launch_ff), 'native_state': len(capture_ff)}, banks=banks,
                operator_ports=operator_ports,source_role='software_geometry_only', mapped_physical_qualification=False)
