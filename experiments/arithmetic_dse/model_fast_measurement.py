"""Hierarchy-preserving fast-operator shells and strict physical observations.

Arithmetic is the already software-tested parameterized generator. This adapter
separates launch/capture/observer ownership; observations never become features.
"""
import csv
from fnmatch import fnmatchcase
import math
from pathlib import Path
import re

from . import model_fast_samples as samples
from .model_collection import sha
from .model_reference_labels_v2 import canonical_instances, partition

VERSION = 'arithmetic-fast-measurement-v2-live-bits'
READER_VERSION = 'fast-register-declared-port-aliases-v3'


def known_result(spec):
    """Sound bit-constant transfer for independent unsigned scalar operands."""
    r=spec['result_width'];mask=(1<<r)-1
    def operand(prefix):
        width=spec[prefix+'_width'];z=int(spec.get(prefix+'_zero_hex','0'),16);o=int(spec.get(prefix+'_one_hex','0'),16)
        return (z | (mask ^ ((1<<min(width,r))-1))) & mask, o & mask
    def add(a,b,carry):
        z=o=0;cs=carry
        for i in range(r):
            av=(0,) if a[0]>>i&1 else (1,) if a[1]>>i&1 else (0,1)
            bv=(0,) if b[0]>>i&1 else (1,) if b[1]>>i&1 else (0,1)
            sums={x+y+c for x in av for y in bv for c in cs};outs={x&1 for x in sums};cs={x>>1 for x in sums}
            if outs=={0}:z|=1<<i
            if outs=={1}:o|=1<<i
        return z,o
    a,b=operand('lhs'),operand('rhs')
    if spec['operation']!='mul':return add(a,b,{'zero':{0},'one':{1},'dynamic':{0,1}}[spec.get('carry','zero')])
    value=(mask,0)
    for i in range(min(spec['lhs_width'],r)):
        z=mask;o=0
        for j in range(min(spec['rhs_width'],r-i)):
            bit=1<<(i+j)
            if not (a[0]>>i&1 or b[0]>>j&1):
                z&=~bit
                if a[1]>>i&1 and b[1]>>j&1:o|=bit
        value=add(value,(z,o),{0})
    return value


def live_operand(spec,prefix):
    z=int(spec.get(prefix+'_zero_hex','0'),16);o=int(spec.get(prefix+'_one_hex','0'),16)
    return [i for i in range(min(spec[prefix+'_width'],spec['result_width'])) if not ((z|o)>>i&1)]


def source(spec, name='ModelBundle'):
    samples.validate(spec)
    original = samples.source(spec, name)
    marker = f'(* keep_hierarchy=1 *) module {name}('
    if original.count(marker) != 1: raise ValueError('unsupported arithmetic source boundary')
    core = original.split(marker)[0]
    a, b, r = (spec[k] for k in ('lhs_width', 'rhs_width', 'result_width'))
    banks = spec.get('capture_banks', 1);dynamic = spec.get('carry', 'zero') == 'dynamic'
    zeros,ones=known_result(spec);live=[i for i in range(r) if not ((zeros|ones)>>i&1)]
    if not live:raise ValueError('fully constant result needs no physical operator characterization')
    text = core + f'''(* keep_hierarchy=1 *) module {name}Launch(input wire clk,rstn,iv,input wire [{a-1}:0] a,input wire [{b-1}:0] b,input wire cin,
output wire [{a-1}:0] data_a,output wire [{b-1}:0] data_b,output wire data_c,output reg valid);
always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;
'''
    for prefix,label,width in (('lhs','a',a),('rhs','b',b)):
        positions=live_operand(spec,prefix);packed={bit:i for i,bit in enumerate(positions)};one=int(spec.get(prefix+'_one_hex','0'),16)
        if positions:
            text+=f'(* keep *) reg [{len(positions)-1}:0] storage_{label};always @(posedge clk)if(!rstn)storage_{label}<=0;else if(iv)storage_{label}<={{'+','.join(f'{label}[{i}]' for i in reversed(positions))+'};\n'
        text+=f'assign data_{label}={{'+','.join(f'storage_{label}[{packed[i]}]' if i in packed else "1'b1" if one>>i&1 else "1'b0" for i in reversed(range(width)))+'};\n'
    if dynamic:
        text += '(* keep *) reg carry;always @(posedge clk)if(!rstn)carry<=0;else if(iv)carry<=cin;assign data_c=carry;\n'
    else: text += "assign data_c=1'b0;\n"
    text += f'''endmodule
(* keep_hierarchy=1 *) module {name}Capture(input wire clk,rstn,iv,input wire [{r-1}:0] value,output reg valid,'''
    text += ','.join(f'output wire [{r-1}:0] data{k}' for k in range(banks)) + ');\n'
    text += 'always @(posedge clk)if(!rstn)valid<=0;else valid<=iv;\n'
    packed={bit:i for i,bit in enumerate(live)}
    for k in range(banks):
        text+=f'(* keep,dont_touch *) reg [{len(live)-1}:0] storage{k};(* keep *) always @(posedge clk)storage{k}<={{'+','.join(f'value[{i}]' for i in reversed(live))+'};\n'
        text+=f'assign data{k}={{'+','.join(f'storage{k}[{packed[i]}]' if i in packed else "1'b1" if ones>>i&1 else "1'b0" for i in reversed(range(r)))+'};\n'
    text += f'endmodule\n(* keep_hierarchy=1 *) module {name}Observer(input wire [{banks*r-1}:0] data,output wire [{banks-1}:0] y);\n'
    for k in range(banks): text += f'assign y[{k}]=^data[{k*r}+:{r}];\n'
    text += f'''endmodule
module {name}(input wire clk,rstn,iv,input wire [{a-1}:0] a,input wire [{b-1}:0] b,input wire cin,output wire [{banks-1}:0] y,output wire ov);
wire [{a-1}:0] data_a;wire [{b-1}:0] data_b;wire data_c,launch_valid;wire [{r-1}:0] value;
'''
    for k in range(banks): text += f'wire [{r-1}:0] data{k};\n'
    text += f'''{name}Launch launch(.clk(clk),.rstn(rstn),.iv(iv),.a(a),.b(b),.cin(cin),.data_a(data_a),.data_b(data_b),.data_c(data_c),.valid(launch_valid));
{name}Core core(.a(data_a),.b(data_b),.cin(data_c),.value(value));
{name}Capture capture(.clk(clk),.rstn(rstn),.iv(launch_valid),.value(value),.valid(ov),'''
    text += ','.join(f'.data{k}(data{k})' for k in range(banks)) + ');\n'
    text += f'{name}Observer observer(.data({{'+','.join(f'data{k}' for k in reversed(range(banks)))+'}),.y(y));\nendmodule\n'
    return text


def requests(spec):
    rows = [dict(id='data' + str(k), kind='register',
        source=['launch/storage_a*', 'launch/data_a*', 'launch/storage_b*', 'launch/data_b*', 'launch/carry*', 'launch/data_c*'],
        target=['capture/storage' + str(k) + '*', 'capture/data' + str(k) + '*'])
        for k in range(spec.get('capture_banks', 1))]
    return rows + [dict(id='valid', kind='register', source=['launch/valid*'], target=['capture/valid*'])]


def render_requests(spec):
    return 'set vulsim_reference_requests {\n' + ''.join(
        '  {' + r['id'] + ' register {' + ' '.join(r['source']) + '} {' + ' '.join(r['target']) + '}}\n'
        for r in requests(spec)) + '}\n'


def generic_geometry(design, top, spec):
    modules = design['modules']; counts = {}; instance_q = {}; bank_info = {}
    def visit(module, prefix):
        for name, c in module.get('cells', {}).items():
            typ = c['type'];path = prefix + name
            if typ in modules: visit(modules[typ], path + '/')
            elif 'DFF' in typ.upper():
                if not typ.startswith('$_') or len(c['connections'].get('Q', [])) != 1:
                    raise ValueError('unsupported generic sequential primitive')
                owner = 'input_service' if path.startswith('launch/') else 'native_state' if path.startswith('capture/') else None
                if owner is None: raise ValueError('generic FF outside declared ownership')
                counts[owner] = counts.get(owner, 0) + 1;instance_q[path] = c['connections']['Q'][0]
            elif typ.startswith('$') and ('latch' in typ.lower() or 'ff' in typ.lower()):
                raise ValueError('unsupported generic state')
    visit(modules[top], '')
    capture = modules[modules[top]['cells']['capture']['type']];q_to_cells = {}
    for name, c in capture['cells'].items():
        if 'DFF' in c['type'].upper():
            for bit in c['connections']['Q']: q_to_cells.setdefault(bit, set()).add(name)
    used = set(); r = spec['result_width']
    for k in range(spec.get('capture_banks', 1)):
        bits = capture['netnames']['data' + str(k)]['bits']
        if len(bits) != r: raise ValueError('generic capture result width differs')
        states = set(); variable = []; constants = {}
        for index, bit in enumerate(bits):
            if isinstance(bit, int):
                cells = q_to_cells.get(bit, set())
                if len(cells) != 1: raise ValueError('capture bit is not exactly one retained generic FF')
                states.update(cells); variable.append(index)
            elif bit in ('0', '1'): constants[str(index)] = bit
            else: raise ValueError('unknown generic captured bit')
        if not states or used & states or len(states) != len(variable):
            raise ValueError('generic banks merged or state bits aliased')
        used.update(states);bank_info['data' + str(k)] = dict(variable_bits=variable, constant_bits=constants, FF_bits=len(states))
    if len({tuple(x['variable_bits']) for x in bank_info.values()}) != 1:
        raise ValueError('generic capture banks have unequal live geometry')
    zeros,ones=known_result(spec);expected=[i for i in range(r) if not ((zeros|ones)>>i&1)]
    if any(g['variable_bits']!=expected for g in bank_info.values()):raise ValueError('generic observed bits differ from static known-bit proof')
    launch_bits=len(live_operand(spec,'lhs'))+len(live_operand(spec,'rhs'))+int(spec.get('carry','zero')=='dynamic')+1
    if counts.get('input_service')!=launch_bits:raise ValueError('generic launch bits differ from static packed-input proof')
    if counts.get('native_state') != len(used) + 1:
        raise ValueError('generic capture state is not banks plus one valid FF')
    return dict(owner_FF_bits=counts, banks=bank_info, registered_protocol='enabled_launch_unconditional_capture',
        geometry_role='software_proof_only_not_prediction_feature', post_mapping_qualified=False)


def capture_bank_bindings(instances,geometry,pins):
    bank_states={};used=set()
    for name,g in geometry['banks'].items():
        number=name.removeprefix('data');selectors=['capture/storage'+number+'*','capture/data'+number+'*']
        found={n for n,typ in instances.items() if pins.get(typ,{}).get('sequential') and any(fnmatchcase(n,p) for p in selectors)}
        if len(found)!=g['FF_bits'] or used & found:raise ValueError('mapped capture bank pruned, merged or duplicated')
        used.update(found);bank_states[name]=len(found)
    return bank_states


def observations(prefix, spec, period, time_to_ps, pins, profile, geometry):
    ownership, raw_instances, _ = partition(prefix, pins, profile, expected=geometry['owner_FF_bits'])
    instances = canonical_instances(raw_instances)
    expected = {r['id']: r for r in requests(spec)}
    table = list(csv.DictReader(Path(str(prefix) + '_reference_paths.tsv').read_text().splitlines(), delimiter='\t'))
    if len(table) != len(expected) or {r['id'] for r in table} != set(expected):
        raise ValueError('fast measurement path coverage differs')
    def meta(pin):
        cell, terminal = pin.rsplit('/', 1)
        if cell not in instances or instances[cell] not in pins: raise ValueError('unknown fast path cell')
        if terminal not in pins[instances[cell]]['pins']: raise ValueError('unknown fast timing pin')
        return cell, terminal, pins[instances[cell]]
    bank_states=capture_bank_bindings(instances,geometry,pins)
    rows = []
    for row in table:
        request = expected[row['id']];start, q, sm = meta(row['start']);end, d, em = meta(row['end'])
        if (not sm['sequential'] or sm['pins'][q]['direction'] != 'output'
                or not any(fnmatchcase(start, pattern) for pattern in request['source'])
                or d not in em['data_pins'] or not any(fnmatchcase(end, pattern) for pattern in request['target'])):
            raise ValueError('fast Q/D path outside declared physical boundary')
        a, b, delay, slack = (float(row[k]) for k in ('start_arrival', 'end_arrival', 'delay', 'slack'))
        if not all(math.isfinite(x) for x in (a, b, delay, slack)) or delay < 0 or not math.isclose(b-a, delay, abs_tol=1e-6, rel_tol=1e-6):
            raise ValueError('invalid fast Q-to-D arrival difference')
        file = Path(str(prefix) + '_reference_' + row['id'] + '_points.tsv')
        points = [(name, float(v)) for name, v in (line.split('\t') for line in file.read_text().splitlines())]
        starts = [v for name, v in points if name == row['start']]
        if (not all(math.isfinite(v) for _, v in points) or len(points) != int(row['points']) or len(starts) != 1 or not math.isclose(starts[0], a, abs_tol=1e-6)
                or points[-1][0] != row['end'] or not math.isclose(points[-1][1], b, abs_tol=1e-6)):
            raise ValueError('fast raw path points differ from label')
        H = period - delay * time_to_ps - slack * time_to_ps
        setup, skew = float(row['setup_margin_s']) * 1e12, float(row['clk_skew_s']) * 1e12
        if not all(math.isfinite(x) for x in (H, setup, skew)): raise ValueError('invalid fast clock/setup terms')
        result = dict(id=row['id'], data_delay_ps=delay*time_to_ps, slack_ps=slack*time_to_ps, boundary_H_ps=H,
            raw_setup_ps=setup, raw_clock_skew_ps=skew, start_pin=row['start'], end_pin=row['end'],
            points_sha256=sha(file), report_sha256=sha(Path(str(prefix) + '_reference_' + row['id'] + '.rpt')))
        if row['id'].startswith('data'):
            outputs = [(name, v) for name, v in points if name.startswith('core/') and meta(name)[2]['pins'][meta(name)[1]]['direction'] == 'output']
            if not outputs: raise ValueError('arithmetic core absent from fast data path')
            last, value = outputs[-1];core = (value-a)*time_to_ps;suffix = (b-value)*time_to_ps
            if core <= 0 or suffix < -1e-6 or not math.isclose(core+suffix, delay*time_to_ps, abs_tol=1e-6):
                raise ValueError('invalid fast core/capture decomposition')
            result.update(core_delay_ps=core, capture_suffix_ps=suffix, core_end_pin=last)
        rows.append(result)
    data = [r for r in rows if r['id'].startswith('data')]
    worst = max(data, key=lambda r: (r['data_delay_ps'], r['id']))
    return dict(paths=rows, data_delay_ps=worst['data_delay_ps'], data_witness=worst['id'],
        combinational_area_um2=ownership['owner_area_um2'].get('arithmetic', 0.),
        ownership=ownership, mapped_capture_banks=bank_states,
        label_definition='whole launch_Q-to-capture_D data delay; clkQ/setup excluded; core and suffix retained separately',
        prediction_features_use_mapped_counts=False)
