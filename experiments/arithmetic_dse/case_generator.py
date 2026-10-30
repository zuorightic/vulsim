"""Generate revised case definitions and real VUL combination kernels.

The source DAG is a versioned experiment representation, not compiler BEIR.
It retains semantic FP calls; compiler lowering/grouping remains a later step.
"""
import argparse
import json
from pathlib import Path

from .contracts import (ContractError, GROUPS, PLATFORMS, ROOT, WIDTHS,
                           content_hash, positive_int, topological)

INTEGER_FAMILIES = ('MUL', 'MAC', 'DOT2', 'UDR', 'DIVSEL', 'MIX', 'H_M', 'H_D')


class Builder:
    def __init__(self):
        self.nodes = []
        self.outputs = {}

    def node(self, name, op, width, *deps, **params):
        self.nodes.append({'id': name, 'op': op, 'width': width,
                           'deps': list(deps), 'params': params})
        return name

    def input(self, name, width):
        return self.node(name, 'Input', width)

    def constant(self, name, width, value):
        return self.node(name, 'Constant', width, value=value)

    def divrem(self, prefix, a, d, w, *, quotient=True, remainder=True):
        zero = self.constant(prefix+'zero', w, 0)
        one = self.constant(prefix+'one', w, 1)
        ones = self.constant(prefix+'ones', w, (1 << w)-1)
        is_zero = self.node(prefix+'is_zero', 'Eq', 1, d, zero)
        safe = self.node(prefix+'safe_d', 'Ite', w, is_zero, one, d)
        q = r = None
        if quotient:
            raw = self.node(prefix+'raw_q', 'Div', w, a, safe)
            q = self.node(prefix+'q', 'Ite', w, is_zero, ones, raw)
        if remainder:
            raw = self.node(prefix+'raw_r', 'Mod', w, a, safe)
            r = self.node(prefix+'r', 'Ite', w, is_zero, a, raw)
        return q, r


def build_graph(family, width=None):
    b = Builder()
    if family in INTEGER_FAMILIES:
        w = positive_int(width, 'width')
        if w > 128:
            raise ContractError('template_ineligible', 'source generator supports integer inputs up to 128 bits')
        a = b.input('a', w)
        if family in ('MUL', 'MAC', 'DOT2', 'H_M'):
            x = b.input('b', w)
            r = w if family == 'H_M' else 2*w
            p = b.node('product', 'Mul', r, a, x)
            if family == 'MUL':
                b.outputs = {'y': p}
            elif family == 'MAC':
                c = b.input('c', 2*w)
                b.outputs = {'y': b.node('sum', 'Add', 2*w, p, c)}
            elif family == 'DOT2':
                c, d = b.input('c', w), b.input('d', w)
                q = b.node('product2', 'Mul', 2*w, c, d)
                ep, eq = b.node('wide_p', 'ZExt', 2*w+1, p), b.node('wide_q', 'ZExt', 2*w+1, q)
                b.outputs = {'y': b.node('sum', 'Add', 2*w+1, ep, eq)}
            else:
                c, select = b.input('c', w), b.input('select', 1)
                zero = b.constant('zero', w, 0)
                chosen = b.node('chosen_c', 'Ite', w, select, c, zero)
                b.outputs = {'y': b.node('sum', 'Add', w, p, chosen)}
        elif family in ('UDR', 'DIVSEL', 'H_D'):
            d = b.input('d', w)
            q, r = b.divrem('first_', a, d, w)
            if family == 'UDR':
                b.outputs = {'q': q, 'r': r}
            elif family == 'DIVSEL':
                bias, bypass, select = b.input('bias', w), b.input('bypass', w), b.input('select', 1)
                added = b.node('biased_q', 'Add', w, q, bias)
                b.outputs = {'y': b.node('chosen', 'Ite', w, select, added, bypass), 'r': r}
            else:
                e = b.input('e', w)
                q2, r2 = b.divrem('second_', q, e, w)
                b.outputs = {'q': q2, 'r1': r, 'r2': r2}
        else:
            x, mask, d = b.input('b', w), b.input('mask', w), b.input('d', w)
            sw = w.bit_length()+1  # includes s=W, s=2W and larger encodings
            s = b.input('s', sw)
            zero_s, limit = b.constant('zero_s', sw, 0), b.constant('limit', sw, w)
            zero = b.constant('zero', w, 0)
            in_range = b.node('in_range', 'Lt', 1, s, limit)
            safe_s = b.node('safe_s', 'Ite', sw, in_range, s, zero_s)
            u, v = b.node('u', 'Add', w, a, x), b.node('v', 'Sub', w, a, x)
            raw_l, raw_r = b.node('raw_l', 'Shl', w, u, safe_s), b.node('raw_r', 'Shr', w, v, safe_s)
            left = b.node('left', 'Ite', w, in_range, raw_l, zero)
            right = b.node('right', 'Ite', w, in_range, raw_r, zero)
            inverse = b.node('inverse_mask', 'BitNot', w, mask)
            ml, mr = b.node('masked_l', 'BitAnd', w, left, mask), b.node('masked_r', 'BitAnd', w, right, inverse)
            merged = b.node('merged', 'BitOr', w, ml, mr)
            _, rem = b.divrem('mod_', a, d, w, quotient=False)
            b.outputs = {'y': b.node('answer', 'BitXor', w, merged, rem),
                         'less': b.node('less', 'Lt', 1, a, x)}
    elif family in ('F1', 'F2', 'H_F1'):
        a, x = b.input('a', 32), b.input('b', 32)
        fp = b.node('fp1', 'F32MulRNE', 37, a, x)
        bits = b.node('bits1', 'Slice', 32, fp, low=0)
        flags = b.node('flags1', 'Slice', 5, fp, low=32)
        if family == 'F2':
            c = b.input('c', 32)
            fp2 = b.node('fp2', 'F32MulRNE', 37, bits, c)
            bits = b.node('bits2', 'Slice', 32, fp2, low=0)
            flags2 = b.node('flags2', 'Slice', 5, fp2, low=32)
            flags = b.node('flags_or', 'BitOr', 5, flags, flags2)
        elif family == 'H_F1':
            bypass, select = b.input('bypass', 32), b.input('select', 1)
            zero = b.constant('zero_flags', 5, 0)
            bits = b.node('selected_bits', 'Ite', 32, select, bits, bypass)
            flags = b.node('selected_flags', 'Ite', 5, select, flags, zero)
        b.outputs = {'bits': bits, 'flags': flags}
    else:
        raise ContractError('template_ineligible', f'unknown source family: {family}')
    graph = {'version': 'arithmetic-source-dag-v1', 'nodes': b.nodes, 'outputs': b.outputs}
    validate_graph(graph)
    return graph


def validate_graph(graph):
    nodes = topological(graph['nodes'])
    by_id = {n['id']: n for n in nodes}
    arity = {'Input': 0, 'Constant': 0, 'ZExt': 1, 'Trunc': 1, 'Slice': 1,
             'BitNot': 1, 'Add': 2, 'Sub': 2, 'Mul': 2, 'Div': 2, 'Mod': 2,
             'Eq': 2, 'Lt': 2, 'Shl': 2, 'Shr': 2, 'BitAnd': 2, 'BitOr': 2,
             'BitXor': 2, 'Ite': 3, 'F32MulRNE': 2}
    for n in nodes:
        w = positive_int(n['width'], n['id']+' width')
        op, deps, params = n['op'], n['deps'], n['params']
        if op not in arity or len(deps) != arity[op]:
            raise ContractError('invalid_expansion_graph', 'unsupported source operation/arity', node=n['id'])
        allowed_params = {'Constant':{'value'}, 'Slice':{'low'}}.get(op,set())
        if not isinstance(params,dict) or set(params)-allowed_params:
            raise ContractError('invalid_expansion_graph', 'unsupported source operation parameter', node=n['id'])
        widths = [by_id[d]['width'] for d in deps]
        valid = True
        if op == 'Constant':
            valid = type(params.get('value')) is int and 0 <= params['value'] < 1 << w
        elif op in ('Eq', 'Lt'):
            valid = w == 1 and widths[0] == widths[1]
        elif op == 'Ite':
            valid = widths == [1, w, w]
        elif op == 'ZExt':
            valid = widths[0] <= w
        elif op == 'Trunc':
            valid = widths[0] >= w
        elif op == 'Slice':
            low = params.get('low')
            valid = type(low) is int and low >= 0 and low+w <= widths[0]
        elif op == 'F32MulRNE':
            valid = widths == [32, 32] and w == 37
        elif op in ('Shl', 'Shr'):
            valid = widths[0] == w
        elif op not in ('Input', 'Mul', 'Add', 'Sub'):
            valid = all(x == w for x in widths)
        if not valid:
            raise ContractError('width_contract_violation', 'invalid source width relation', node=n['id'])
    if not graph['outputs'] or any(n not in by_id for n in graph['outputs'].values()):
        raise ContractError('invalid_expansion_graph', 'invalid output reference')
    return nodes


def graph_signatures(graph):
    by_id = {n['id']: n for n in graph['nodes']}
    return ({n['id']: n['width'] for n in graph['nodes'] if n['op'] == 'Input'},
            {name: by_id[ref]['width'] for name, ref in graph['outputs'].items()})


def reference_graph(graph):
    """Original semantic graph for target calibration; no measured values."""
    by_id = {n['id']: n for n in graph['nodes']}
    result = []
    for n in graph['nodes']:
        op, w = n['op'], n['width']
        primitive = None
        if op == 'Mul':
            data_width = max(by_id[x]['width'] for x in n['deps'])
            primitive = f'mul_u{data_width}_r{w}'
        elif op in ('Div', 'Mod'):
            primitive = f'{op.lower()}_u{w}'
        elif op == 'F32MulRNE':
            primitive = 'f32_mul_rne'
        elif op not in ('Input', 'Constant', 'ZExt', 'Trunc', 'Slice'):
            data_width = max(by_id[x]['width'] for x in n['deps'])
            primitive = f'{op.lower()}_u{max(w, data_width)}'
        result.append({'id': n['id'], 'deps': n['deps'], 'primitive': primitive,
                       'heavy': op in ('Mul', 'Div', 'Mod', 'F32MulRNE')})
    return result


def case_spec(family, width=None):
    graph = build_graph(family, width)
    inputs, outputs = graph_signatures(graph)
    return {'id': f'{family}_{width}' if width is not None else family,
            'family': family, 'width': width,
            'partition': 'holdout' if family.startswith('H_') else 'formal',
            'semantic_profile': ('unsigned_integer' if width is not None else 'binary32_mul_rne'),
            'inputs': inputs, 'outputs': outputs,
            'source_graph_sha256': content_hash(graph), 'reference_graph': reference_graph(graph),
            'divrem_sharing': 'not_assumed; actual_implementation_identity_required'}


def generate_manifest():
    cases = [case_spec(family, w) for family in INTEGER_FAMILIES[:6] for w in WIDTHS]
    cases += [case_spec('F1'), case_spec('F2')]
    cases += [case_spec(family, w) for family in INTEGER_FAMILIES[6:] for w in WIDTHS]
    cases += [case_spec('H_F1')]
    return {'version': 'arithmetic-cases-v2', 'generator_version': 'arithmetic-source-dag-v1',
            'semantics_version': 'arithmetic-semantics-v2', 'platforms': list(PLATFORMS),
            'groups': list(GROUPS), 'integer_widths': list(WIDTHS), 'cases': cases,
            'training_identity_policy': {
                'registered_training_ids': [], 'namespace': 'microbenchmark/<platform>/<version>/<sample>',
                'formal_and_holdout_graphs_allowed_for_training_or_tuning': False,
                'structure_variants_and_target_sweeps_share_group': True,
                'actual_sample_list_and_model_splits': 'freeze_at_stage7_admission'},
            'legacy_mapping': {'M1': 'MAC_32', 'M2': 'DOT2_16', 'D1': 'UDR_16',
                               'D2': 'DIVSEL_32', 'F1': 'F1', 'F2': 'F2',
                               'H_M1': 'H_M_32', 'H_D1': 'H_D_32', 'H_F1': 'H_F1'}}


def evaluate_graph(graph, inputs):
    """Execute generated graph separately from the family-level reference."""
    from .reference import f32_mul
    nodes = validate_graph(graph)
    signature, _ = graph_signatures(graph)
    if inputs.keys() != signature.keys():
        raise ValueError('source graph input signature mismatch')
    values = {}
    for n in nodes:
        op, width, p = n['op'], n['width'], n['params']
        a = [values[d] for d in n['deps']]
        if op == 'Input':
            value = inputs[n['id']]
            if type(value) is not int or not 0 <= value < 1 << width:
                raise ValueError('source graph input out of range')
        elif op == 'Constant': value = p['value']
        elif op in ('ZExt', 'Trunc'): value = a[0]
        elif op == 'Slice': value = a[0] >> p['low']
        elif op == 'Mul': value = a[0]*a[1]
        elif op == 'Add': value = a[0]+a[1]
        elif op == 'Sub': value = a[0]-a[1]
        elif op in ('Div', 'Mod'):
            if a[1] == 0:
                raise ValueError('unsafe internal division reached')
            value = a[0]//a[1] if op == 'Div' else a[0] % a[1]
        elif op in ('Shl', 'Shr'):
            if a[1] >= width:
                raise ValueError('unsafe internal shift reached')
            value = a[0] << a[1] if op == 'Shl' else a[0] >> a[1]
        elif op == 'Eq': value = int(a[0] == a[1])
        elif op == 'Lt': value = int(a[0] < a[1])
        elif op == 'BitAnd': value = a[0] & a[1]
        elif op == 'BitOr': value = a[0] | a[1]
        elif op == 'BitXor': value = a[0] ^ a[1]
        elif op == 'BitNot': value = ~a[0]
        elif op == 'Ite': value = a[1] if a[0] else a[2]
        elif op == 'F32MulRNE':
            fp = f32_mul(*a)
            value = fp.bits | (fp.flags << 32)
        else: raise ValueError(f'unimplemented source graph operation: {op}')
        values[n['id']] = value & ((1 << width)-1)
    return {name: values[ref] for name, ref in graph['outputs'].items()}


def vul_type(width):
    return 'bool' if width == 1 else f'Int<{width}>'


def kernel_body(graph):
    symbols = {}
    lines = []
    binary = {'Mul': '*', 'Add': '+', 'Sub': '-', 'Div': '/', 'Mod': '%',
              'Eq': '==', 'Lt': '<', 'BitAnd': '&', 'BitOr': '|', 'BitXor': '^'}
    for n in validate_graph(graph):
        name, op, w, p = n['id'], n['op'], n['width'], n['params']
        a = [symbols[d] for d in n['deps']]
        cast = lambda value: f'Int<{w}>({value})'
        if op == 'Input':
            symbols[name] = 'value.'+name
            continue
        if op == 'Constant':
            value = p['value']
            if w == 1: expr = 'true' if value else 'false'
            elif value == (1 << w)-1: expr = f'~Int<{w}>(0)'
            elif value < 1 << 64: expr = cast(str(value)+'ull')
            else: raise ValueError('constant source lowering requires explicit limbs')
        elif op in ('ZExt', 'Trunc'): expr = cast(a[0])
        elif op == 'Slice': expr = cast(f'({a[0]} >> {p["low"]}u)')
        elif op == 'BitNot': expr = f'~{a[0]}'
        elif op == 'Ite': expr = f'({a[0]} ? {a[1]} : {a[2]})'
        elif op == 'F32MulRNE': expr = f'vularith::F32MulRNE({a[0]}, {a[1]})'
        elif op in ('Shl', 'Shr'):
            expr = f'({a[0]} {"<<" if op == "Shl" else ">>"} {a[1]}.to<uint32_t>())'
        elif op in binary:
            if op in ('Add', 'Sub'):
                a = [cast(x) for x in a]
            expr = f'({a[0]} {binary[op]} {a[1]})'
        else: raise ValueError(f'missing VUL expression: {op}')
        symbol = 'n_'+name
        lines.append(f'    {vul_type(w)} {symbol} = {expr};')
        symbols[name] = symbol
    lines += [f'    result.{name} = {symbols[ref]};' for name, ref in graph['outputs'].items()]
    return '\n'.join(lines)+'\n'


def source_files(case):
    graph = build_graph(case['family'], case['width'])
    inputs, outputs = graph_signatures(graph)
    header = '#include <defhelper.hpp>\n'
    for name, fields in (('CaseInput', inputs), ('CaseOutput', outputs)):
        header += f'STRUCT({name}) {{\n'+''.join(f'    {vul_type(w)} {field};\n' for field, w in fields.items())+'};\n'
    top = ('INTERFACE() { SERVICE(calculate, ARG(CaseInput) value, RESP(CaseOutput) result); }\n'
           'SERVICE(calculate, ARG(CaseInput) value, RESP(CaseOutput) result) {\n'
           + kernel_body(graph) + '}\n')
    return {'header.uh': header, 'Case.vul': top, 'graph.json': json.dumps(graph, indent=2)+'\n'}


def validation_vectors(case, random_count=128):
    import random
    rng = random.Random(20261030 + int(content_hash(case)[:8], 16))
    signature = case['inputs']
    rows = [{name: 0 for name in signature}, {name: (1 << w)-1 for name, w in signature.items()}]
    baseline = {name: rng.getrandbits(w) for name, w in signature.items()}
    for name, w in signature.items():
        values = {0, 1, 2, (1 << w)-1, (1 << w)-2, 1 << (w-1), (1 << (w-1))-1}
        if name == 's':
            width = case['width']
            values.update([width-1, width, width+1, 2*width])
        if name in ('d', 'e'):
            values.update([3, 5, 1 << (w//2)])
        for value in sorted(v for v in values if 0 <= v < 1 << w):
            rows.append({**baseline, name: value})
    if case['width'] is None:
        edges = [0, 0x80000000, 1, 3, 0x007fffff, 0x00800000, 0x3f000000,
                 0x3f7fffff, 0x3f800000, 0x3f800001, 0x40000000, 0x7f7fffff,
                 0x7f800000, 0xff800000, 0x7fc12345, 0x7f812345]
        for a in edges:
            for b in edges:
                row = {**baseline, 'a': a, 'b': b}
                if 'c' in row: row['c'] = edges[(a ^ b) % len(edges)]
                rows.append(row)
        if 'select' in signature:
            rows += [{**baseline, 'select': 0, 'bypass': 0x7f812345},
                     {**baseline, 'select': 1, 'a': 0, 'b': 0x7f800000}]
    rows += [{name: rng.getrandbits(w) for name, w in signature.items()} for _ in range(random_count)]
    return rows


def validation_main(case, vectors_path):
    # All words and tail bits travel through hex/limbs, including 256/257 bits.
    text = r'''#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <string>
#include <run.hpp>
TOP("Case.vul"); PROJECT(".");
REQUEST(calculate, ARG(CaseInput) value, RESP(CaseOutput) result);
GLOBAL() {
template<uint32_t W> Int<W> read_hex(std::istream& stream) {
    std::string token;
    if (!(stream >> token)) std::exit(1);
    Int<W> value{};
    for (size_t i=0; i<token.size(); ++i) {
        char c=token[token.size()-1-i];
        unsigned digit=c>='a' ? unsigned(c-'a'+10) : unsigned(c-'0');
        for (unsigned j=0; j<4; ++j) {
            unsigned bit=unsigned(i)*4+j;
            if (bit<W) {
                if constexpr (W==1) value=(digit>>j)&1;
                else value.template pick<1>(bit)=(digit>>j)&1;
            } else if ((digit>>j)&1) std::exit(2);
        }
    }
    return value;
}
template<uint32_t W> void print_hex(const Int<W>& value) {
    const auto words=value.get_data();
    std::putchar(' ');
    for (int nibble=int((W+3)/4)-1; nibble>=0; --nibble) {
        unsigned digit=0;
        for (unsigned j=0; j<4; ++j) {
            unsigned bit=unsigned(nibble)*4+j;
            if (bit<W && ((words[bit/64]>>(bit%64))&1)) digit|=1u<<j;
        }
        std::putchar("0123456789abcdef"[digit]);
    }
}
}
SIMULATION() {
'''
    text += f'    std::ifstream stream({json.dumps(str(vectors_path))});\n'
    text += '    unsigned count=0; if (!(stream >> count)) std::exit(3);\n'
    text += '    for (unsigned i=0; i<count; ++i) {\n        CaseInput input{}; CaseOutput output{};\n'
    for name, width in case['inputs'].items():
        expr = f'read_hex<{width}>(stream)' + ('.to<bool>()' if width == 1 else '')
        text += f'        input.{name} = {expr};\n'
    text += '        calculate(input, output);\n        std::printf("ROW %u",i);\n'
    text += ''.join(f'        print_hex(Int<{width}>(output.{name}));\n' for name, width in case['outputs'].items())
    text += '        std::putchar(\'\\n\'); sim_nextcycle();\n    }\n'
    text += '    std::printf("CASE RUN PASS rows=%u\\n",count);\n}\n'
    return text


def write_suite(output):
    output.mkdir(parents=True, exist_ok=False)
    manifest = generate_manifest()
    for case in manifest['cases']:
        directory = output / case['id']
        directory.mkdir()
        for name, text in source_files(case).items():
            (directory / name).write_text(text)
    (output / 'cases_v2.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True, help='new suite directory')
    args = parser.parse_args()
    manifest = write_suite(args.out.resolve())
    print(json.dumps({'status': 'generated', 'cases': len(manifest['cases']), 'out': str(args.out)}))


if __name__ == '__main__':
    main()
