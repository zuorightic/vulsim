"""Parameterized unsigned operator sampling kernels, independent of case names.

This is a software-checked source generator, not physical sampling admission.
Known bits and demanded output precision are explicit finite-bit semantics.
"""
import argparse
import hashlib
import json
import random
from pathlib import Path


def validate(spec):
    allowed = {'operation', 'lhs_width', 'rhs_width', 'result_width', 'lhs_zero_hex', 'lhs_one_hex',
               'rhs_zero_hex', 'rhs_one_hex', 'carry', 'capture_banks'}
    if set(spec) - allowed: raise ValueError('unknown semantic sample field')
    if spec['operation'] not in ('mul', 'add', 'addcarry'):
        raise ValueError('unregistered fast sampling operation')
    for name in ('lhs_width', 'rhs_width', 'result_width'):
        if type(spec[name]) is not int or not 1 <= spec[name] <= 257:
            raise ValueError('positive bounded scalar width required')
    for prefix in ('lhs', 'rhs'):
        zero, one = (int(spec.get(prefix + '_' + k + '_hex', '0'), 16) for k in ('zero', 'one'))
        if min(zero, one) < 0 or (zero | one) >> spec[prefix + '_width'] or zero & one:
            raise ValueError('invalid known-bit masks')
    if spec.get('carry', 'zero') not in ('zero', 'one', 'dynamic'):
        raise ValueError('unknown carry semantics')
    if spec['operation'] != 'addcarry' and spec.get('carry', 'zero') != 'zero':
        raise ValueError('carry on a non-carry operation')
    if type(spec.get('capture_banks', 1)) is not int or not 1 <= spec.get('capture_banks', 1) <= 4:
        raise ValueError('bounded independent logical capture banks required')
    return spec


def evaluate(spec, a, b, cin):
    validate(spec)
    values = []
    for prefix, value in (('lhs', a), ('rhs', b)):
        width = spec[prefix + '_width']; mask = (1 << width) - 1
        zero = int(spec.get(prefix + '_zero_hex', '0'), 16); one = int(spec.get(prefix + '_one_hex', '0'), 16)
        values.append(((value & mask) & ~zero) | one)
    a, b = values; operation = spec['operation']
    carry = {'zero': 0, 'one': 1, 'dynamic': cin & 1}[spec.get('carry', 'zero')]
    return ((a * b if operation == 'mul' else a + b + carry) & ((1 << spec['result_width']) - 1))


def source(spec, name):
    validate(spec)
    if not name.isidentifier(): raise ValueError('safe module identifier required')
    a, b, r = (spec[k] for k in ('lhs_width', 'rhs_width', 'result_width'))
    banks = spec.get('capture_banks', 1)
    def masked(prefix, width, value):
        zero = int(spec.get(prefix + '_zero_hex', '0'), 16); one = int(spec.get(prefix + '_one_hex', '0'), 16)
        dynamic = ((1 << width) - 1) & ~(zero | one)
        return f"(({value} & {width}'h{dynamic:x}) | {width}'h{one:x})"
    carry = {'zero': "1'b0", 'one': "1'b1", 'dynamic': 'cin'}[spec.get('carry', 'zero')]
    expression = 'aa * bb' if spec['operation'] == 'mul' else f"aa + bb + {r}'({carry})"
    text = f'''(* keep_hierarchy=1 *) module {name}Core(input wire [{a-1}:0] a,input wire [{b-1}:0] b,input wire cin,output wire [{r-1}:0] value);
wire [{a-1}:0] masked_a={masked('lhs', a, 'a')};
wire [{b-1}:0] masked_b={masked('rhs', b, 'b')};
wire [{r-1}:0] aa={r}'(masked_a);
wire [{r-1}:0] bb={r}'(masked_b);
assign value={expression};
endmodule
(* keep_hierarchy=1 *) module {name}(input wire clk,rstn,iv,input wire [{a-1}:0] a,input wire [{b-1}:0] b,input wire cin,output reg ov,'''
    text += ','.join(f'output wire [{r-1}:0] y{k}' for k in range(banks)) + ');\n'
    text += f'''(* keep *) reg [{a-1}:0] src_a;(* keep *) reg [{b-1}:0] src_b;(* keep *) reg src_c;reg src_valid;
always @(posedge clk)if(!rstn)begin src_a<=0;src_b<=0;src_c<=0;src_valid<=0;end else begin src_valid<=iv;if(iv)begin src_a<=a;src_b<=b;src_c<=cin;end end
always @(posedge clk)if(!rstn)ov<=0;else ov<=src_valid;
wire [{r-1}:0] value;{name}Core core(.a(src_a),.b(src_b),.cin(src_c),.value(value));
'''
    for k in range(banks):
        text += f'(* keep,dont_touch *) reg [{r-1}:0] dst{k};(* keep *) always @(posedge clk)dst{k}<=value;assign y{k}=dst{k};\n'
    return text + 'endmodule\n'


def from_shape(shape):
    operands = shape['operands']; carry = shape.get('carry')
    if any(a['signed'] or a['literal_hex'] is not None for a in operands):
        raise ValueError('unsigned dynamic data operands required')
    mode = 'zero' if not carry or carry['literal_hex'] == '0x0' else 'one' if carry['literal_hex'] == '0x1' else 'dynamic'
    if carry and carry['literal_hex'] not in (None, '0x0', '0x1'): raise ValueError('non-bit carry literal')
    return validate(dict(operation='addcarry' if mode != 'zero' else shape['operation'],
        lhs_width=operands[0]['billing_width'], rhs_width=operands[1]['billing_width'],
        lhs_zero_hex=operands[0]['known_zero_hex'], lhs_one_hex=operands[0]['known_one_hex'],
        rhs_zero_hex=operands[1]['known_zero_hex'], rhs_one_hex=operands[1]['known_one_hex'],
        result_width=shape['result_width'], carry=mode, capture_banks=1))


def prepare(requirements, out):
    out.mkdir(parents=True, exist_ok=False)
    audit = json.loads(requirements.read_text())
    if audit['PPA_calls'] or audit['independent_labels_read']: raise ValueError('static-only requirements required')
    specs = {}; aliases = {}
    for signature, entry in audit['operator_shapes'].items():
        s = from_shape(entry['shape']); canonical = json.dumps(s, sort_keys=True);specs.setdefault(canonical, s);aliases[signature] = canonical
    # Extra contexts exercise the same generator beyond the pilot's widths and masks.
    extras = [dict(operation='mul', lhs_width=12, rhs_width=20, result_width=32),
              dict(operation='add', lhs_width=17, rhs_width=29, result_width=30, lhs_zero_hex='7'),
              dict(operation='addcarry', lhs_width=63, rhs_width=65, result_width=66, carry='dynamic', rhs_one_hex='100'),
              dict(operation='mul', lhs_width=13, rhs_width=17, result_width=11, capture_banks=2)]
    for s in extras: validate(s);specs.setdefault(json.dumps(s, sort_keys=True), s)
    modules = []; declarations = []; checks = []; assignments = []; cases = []; rows = 96
    for index, (canonical, s) in enumerate(sorted(specs.items())):
        name = 'FastSample' + str(index);a, b, r = (s[k] for k in ('lhs_width', 'rhs_width', 'result_width'))
        modules.append(source(s, name)); seed = int(hashlib.sha256(canonical.encode()).hexdigest()[:16], 16);rng = random.Random(seed)
        vectors = []; old = (0, 0, 0); old_valid = 0
        for cycle in range(rows):
            av = [0, (1 << a) - 1, 1, 1 << (a-1)][cycle] if cycle < 4 else rng.getrandbits(a)
            bv = [0, (1 << b) - 1, 1 << (b-1), 1][cycle] if cycle < 4 else rng.getrandbits(b)
            cin = cycle & 1; rstn = int(cycle not in (0, 1, 40, 41));iv = int(cycle % 5 not in (1, 3))
            captured = evaluate(s, *old); expected_valid = 0 if not rstn else old_valid
            fields = [(av, a), (bv, b), (cin, 1), (rstn, 1), (iv, 1), (evaluate(s, av, bv, cin), r), (captured, r), (expected_valid, 1)]
            word = 0
            for value, width in fields: word = (word << width) | value
            vectors.append(format(word, 'x'))
            if not rstn: old = (0, 0, 0);old_valid = 0
            else:
                old_valid = iv
                if iv: old = (av, bv, cin)
        width = a+b+4+2*r; path = out / (name + '.hex');path.write_text('\n'.join(vectors) + '\n')
        declarations.append(f'reg [{width-1}:0] vec{index}[0:{rows-1}];reg [{a-1}:0] a{index};reg [{b-1}:0] b{index};reg c{index},r{index},v{index};wire [{r-1}:0] comb{index};wire ov{index};')
        declarations += [f'wire [{r-1}:0] y{index}_{k};' for k in range(s.get('capture_banks', 1))]
        declarations.append(f'{name}Core c_{index}(.a(a{index}),.b(b{index}),.cin(c{index}),.value(comb{index}));')
        connections = [f'.clk(clk)', f'.rstn(r{index})', f'.iv(v{index})', f'.a(a{index})', f'.b(b{index})', f'.cin(c{index})', f'.ov(ov{index})']
        connections += [f'.y{k}(y{index}_{k})' for k in range(s.get('capture_banks', 1))]
        declarations.append(name + f' s_{index}(' + ','.join(connections) + ');')
        assignments.append(f'{{a{index},b{index},c{index},r{index},v{index}}}=vec{index}[i][{width-1}:{2*r+1}];')
        checks.append(f'if(comb{index}!==vec{index}[i][{2*r}:{r+1}])$fatal(1,"comb shape{index} row%0d",i);')
        for k in range(s.get('capture_banks', 1)):
            checks.append(f'if(i>0 && y{index}_{k}!==vec{index}[i][{r}:1])$fatal(1,"capture shape{index} bank{k} row%0d",i);')
        checks.append(f'if(ov{index}!==vec{index}[i][0])$fatal(1,"valid shape{index} row%0d",i);')
        cases.append(dict(module=name, spec=s, seed=seed, rows=rows, vector_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            origin='required_shape' if canonical in aliases.values() else 'independent_parameter_context'))
    (out / 'kernels.sv').write_text('\n'.join(modules))
    init = '\n'.join(f'$readmemh("{out / (c["module"] + ".hex")}",vec{i});' for i, c in enumerate(cases))
    # Combinational and capture checks occur after the same rising edge; inputs remain stable.
    tb = 'module SampleTb;reg clk=0;integer i;\n'+'\n'.join(declarations)+'\ninitial begin\n'+init+'\n'
    tb += f'for(i=0;i<{rows};i=i+1)begin clk=0;\n'+'\n'.join(assignments)+'\n#5;clk=1;#1;\n'+'\n'.join(checks)+'\n#4;end\n'
    tb += f'$display("FAST_SAMPLE_PASS shapes={len(cases)} rows={rows} arithmetic_checks={len(cases)*rows}");$finish;end\nendmodule\n'
    (out / 'testbench.sv').write_text(tb)
    result = dict(version='arithmetic-fast-sample-software-v1', source_role='software_preflight_only_not_training',
        independent_physical_labels_read=False, physical_admission_allowed=False, shape_aliases=aliases,
        cases=cases, expected_marker=f'FAST_SAMPLE_PASS shapes={len(cases)} rows={rows} arithmetic_checks={len(cases)*rows}')
    (out / 'samples.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(dict(status='prepared', unique_shapes=len(cases), demanded_shapes=len(aliases), physical_admission_allowed=False)), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--requirements', type=Path, required=True);p.add_argument('--out', type=Path, required=True);a = p.parse_args();prepare(a.requirements.resolve(), a.out.resolve())
