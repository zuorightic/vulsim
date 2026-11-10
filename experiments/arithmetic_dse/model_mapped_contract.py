"""Reconcile mapped semantic aliases, FFs and independent capture banks.

Every logical variable bit must resolve to one distinct mapped FF per bank.
Aliases are followed only through Liberty-declared buffers/inverters; losses
are errors, never an inferred zero-cost operator or invented state bank.
"""
from collections import Counter
from pathlib import Path
import re

from .model_fast_preflight import read,write
from .model_fast_path import canonical


def mapped_contract(design,features,pins):
    from .model_sampling_v2 import geometry_contract
    from .model_context_samples import layout
    expected=geometry_contract(features);g=layout(features);modules=design['modules'];top=modules['ModelBundle']
    def child(name):return modules[top['cells'][name]['type']]
    def resolve(module,net):
        if isinstance(net,str):return ('constant',net)
        drivers={}
        for name,cell in module['cells'].items():
            master=cell['type']
            if master not in pins:raise ValueError('mapped cell master absent from actual Liberty')
            for pin,meta in pins[master]['pins'].items():
                if meta['direction']=='output':
                    for bit in cell['connections'].get(pin,[]):
                        if isinstance(bit,int):
                            if bit in drivers:raise ValueError('mapped net multiply driven')
                            drivers[bit]=(name,pin,master)
        visited=set();inverted=False
        while isinstance(net,int):
            if net in visited or net not in drivers:raise ValueError('unresolved/cyclic mapped state alias')
            visited.add(net);name,pin,master=drivers[net];meta=pins[master]
            if meta['sequential']:return (name,pin,inverted)
            if not meta['buffer_or_inverter']:raise ValueError('logical FF output driven by arithmetic instead of storage')
            inputs=[p for p,v in meta['pins'].items() if v['direction']=='input']
            if len(inputs)!=1:raise ValueError('non-unary alias repair')
            fn=re.sub(r'[\s()]','',meta['pins'][pin]['function'] or '')
            if fn not in (inputs[0],'!'+inputs[0],"~"+inputs[0]):raise ValueError('unknown buffer/inverter alias semantics')
            inverted^=fn!=inputs[0];connection=module['cells'][name]['connections'][inputs[0]]
            if len(connection)!=1:raise ValueError('non-scalar mapped pin')
            net=connection[0]
        if isinstance(net,str):return ('constant',net)
        raise ValueError('unknown net type')
    launch=child('launch');capture=child('capture');launch_rows=[];banks=[];used=set()
    for i,bit in enumerate(launch['ports']['value']['bits']):
        cell,pin,inv=resolve(launch,bit)
        if cell=='constant':raise ValueError('lost variable launch bit')
        if cell in used:raise ValueError('independent launch data bits merged')
        used.add(cell);launch_rows.append(dict(bit=i,cell='launch/'+cell,Q=pin,logical_output_inverted=inv))
    if len(launch_rows)!=g['input_bits']:raise ValueError('mapped launch width differs')
    captured_bits=capture['ports']['data']['bits'];offset=0;all_bank_cells=set()
    for i,bank in enumerate(g['captures']):
        bits=captured_bits[offset:offset+len(bank['tokens'])];offset+=len(bits);seen_tokens={};cells=set();rows=[]
        for j,(token,bit) in enumerate(zip(bank['tokens'],bits)):
            resolved=resolve(capture,bit)
            if isinstance(token,str):
                if resolved!=('constant',token):raise ValueError('mapped captured constant disagrees with semantic proof')
                rows.append(dict(logical_bit=j,constant=token));continue
            cell,pin,inv=resolved
            if cell=='constant':raise ValueError('variable capture bit lost')
            token=tuple(token)
            if token in seen_tokens and seen_tokens[token]!=cell:raise ValueError('same-bank duplicate bit storage differs')
            if token not in seen_tokens and cell in cells:raise ValueError('different logical captured bits merged')
            seen_tokens[token]=cell;cells.add(cell)
            ff=capture['cells'][cell];data_pins=pins[ff['type']]['data_pins']
            if len(data_pins)!=1:raise ValueError('unsupported multi-data state cell')
            rows.append(dict(logical_bit=j,cell='capture/'+cell,Q=pin,D=data_pins[0],logical_output_inverted=inv))
        if cells & all_bank_cells:raise ValueError('independent capture banks merged after mapping')
        all_bank_cells |= cells
        if len(cells)!=len(bank['live_tokens']):raise ValueError('mapped bank FF geometry differs')
        banks.append(dict(index=i,id=bank['id'],rows=rows,FF_bits=len(cells)))
    seq_counts={}
    for name,module in (('launch',launch),('capture',capture)):
        seq_counts[name]=sum(pins[cell['type']]['sequential'] for cell in module['cells'].values())
    if seq_counts!={'launch':expected['launch_FF_bits'],'capture':expected['capture_FF_bits']}:raise ValueError('mapped data/valid FF census differs from declaration')
    return dict(status='passed',version='mapped-context-bank-contract-v1',launch=launch_rows,banks=banks,mapped_sequential_cells=seq_counts,
        independent_banks=True,semantic_constants_checked=True,actual_Liberty_pin_aliases=True,physical_timing_qualified=False)


def render_query_contract(contract,connections,features):
    """Resolve canonical Yosys instance aliases back to exact OpenDB pin names."""
    from .model_context_samples import layout
    index={canonical(r['instance'])+'/'+r['pin']:r['instance']+'/'+r['pin'] for r in connections}
    def pin(cell,terminal):
        name=canonical(cell)+'/'+terminal
        if name not in index:raise ValueError('mapped FF pin absent from actual physical census: '+name)
        return index[name]
    launch=[pin(r['cell'],r['Q']) for r in contract['launch']]
    banks={};prefixes={}
    for bank in contract['banks']:
        cells={r['cell']:r['D'] for r in bank['rows'] if 'cell' in r}
        if cells:
            banks['bank'+str(bank['index'])]=[pin(cell,d) for cell,d in sorted(cells.items())]
            prefixes['bank'+str(bank['index'])]=[pin(cell,d).rsplit('/',1)[0] for cell,d in cells.items()]
    scopes={'producer':'core/',**{'consumer'+str(i):'consumer'+str(i)+'/' for i in range(len(features['consumers']))}}
    def tcl_list(values):
        if any('}' in v or '{' in v or '\n' in v for v in values):raise ValueError('unsafe Tcl pin spelling')
        return '{'+' '.join('{'+v+'}' for v in values)+'}'
    text='set context_nodes '+tcl_list([x for item in scopes.items() for x in item])+'\nset context_launch_data '+tcl_list(launch)+'\n'
    text+='set context_banks {'+' '.join('{'+name+'} '+tcl_list(values) for name,values in banks.items())+'}\n'
    return text,scopes,prefixes


def operator_port_contract(design,features,pins):
    modules=design['modules'];top=modules['ModelBundle'];result={}
    for name in ['core']+['consumer'+str(i) for i in range(len(features['consumers']))]:
        module=modules[top['cells'][name]['type']];inputs={}
        for port in ('a','b','cin'):
            for i,bit in enumerate(module['ports'][port]['bits']):
                if isinstance(bit,int):inputs.setdefault(bit,[]).append([port,i])
        drivers={}
        for cell,c in module['cells'].items():
            for pin,meta in pins[c['type']]['pins'].items():
                if meta['direction']=='output':
                    for bit in c['connections'].get(pin,[]):drivers[bit]=name+'/'+cell+'/'+pin
        bits=[]
        for i,bit in enumerate(module['ports']['value']['bits']):
            if isinstance(bit,str):bits.append(dict(bit=i,kind='constant',value=bit))
            elif bit in inputs:bits.append(dict(bit=i,kind='passthrough',input_aliases=inputs[bit]))
            elif bit in drivers:bits.append(dict(bit=i,kind='node_logic',driver_pin=drivers[bit]))
            else:raise ValueError('semantic operator result has no mapped driver/alias certificate')
        result[name]=bits
    return dict(version='mapped-operator-semantic-output-certificate-v1',nodes=result,constant_and_passthrough_explicit=True)
