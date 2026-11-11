"""Resolve real compiler state words to mapped FFs without arithmetic labels.

This is a semantic FF/constant census.  It does not infer reset/enable timing
qualification from a name, nor grant S/G qualification.  Only Liberty-declared
unary buffers/inverters may connect a logical state alias to an FF output.
"""
from collections import Counter
import re


def flatten(design, pins, top='ModelBundle'):
    modules=design['modules']; cells={}; aliases={}
    def walk(kind,scope,portmap):
        module=modules[kind]
        local={}
        for name,port in module.get('ports',{}).items():
            if name in portmap:
                if len(port['bits'])!=len(portmap[name]):raise ValueError('mapped hierarchical port width mismatch')
                for bit,value in zip(port['bits'],portmap[name],strict=True):
                    if isinstance(bit,int):
                        if bit in local and local[bit]!=value:raise ValueError('mapped hierarchical port alias conflict')
                        local[bit]=value
        def net(bit):
            if isinstance(bit,str):return bit
            return local.setdefault(bit,(scope,bit))
        for name,row in module.get('netnames',{}).items():aliases[scope+name.lstrip('\\')]=[net(b) for b in row['bits']]
        for name,row in module.get('cells',{}).items():
            name=scope+name.lstrip('\\'); connections={p:[net(b) for b in bits] for p,bits in row['connections'].items()}
            if row['type'] in pins:
                if name in cells:raise ValueError('duplicate mapped cell path')
                cells[name]=dict(type=row['type'],connections=connections)
            elif row['type'] in modules:walk(row['type'],name+'/',connections)
            else:raise ValueError('unknown mapped master '+row['type'])
    walk(top,'',{})
    return cells,aliases


def verify(design,pins,contract,source):
    cells,aliases=flatten(design,pins);drivers={}
    for name,row in cells.items():
        for term,meta in pins[row['type']]['pins'].items():
            if meta['direction']!='output':continue
            bits=row['connections'].get(term,[])
            if len(bits)!=1:raise ValueError('mapped library output not scalar')
            net=bits[0]
            if not isinstance(net,str):
                if net in drivers:raise ValueError('mapped signal has multiple drivers')
                drivers[net]=(name,term)
    def resolve(net):
        seen=set();inverted=False
        while not isinstance(net,str):
            if net in seen or net not in drivers:raise ValueError('unresolved or cyclic mapped state alias')
            seen.add(net);name,term=drivers[net];cell=cells[name];meta=pins[cell['type']]
            if meta['sequential']:
                data=meta['data_pins']
                if len(data)!=1:raise ValueError('unsupported multi-data FF')
                return dict(cell=name,Q=term,D=data[0],logical_output_inverted=inverted)
            function=re.sub(r'[\s()]','',meta['pins'][term].get('function') or '')
            inputs=[p for p,v in meta['pins'].items() if v['direction']=='input']
            if not inputs and function in ('0','1',"1'b0","1'b1"):
                return dict(constant=str(int(function[-1])^inverted))
            if not meta['buffer_or_inverter'] or len(inputs)!=1 or function not in (inputs[0],'!'+inputs[0],'~'+inputs[0]):
                raise ValueError('state alias is driven by non-unary combinational logic')
            inverted^=function!=inputs[0];net=cell['connections'][inputs[0]][0]
        if net not in ('0','1'):raise ValueError('unknown mapped constant')
        return dict(constant=str(int(net)^inverted))
    words=[]
    for p in source['inputs']:
        words.append(dict(name='launch/'+p['name'],owner='input_service',width=p['width'],mask=(1<<p['width'])-1,
                          valid=False,stage=0,origin=p['name'],enable=p['name']+'_wen',reset=0))
    words.append(dict(name='launch/iv',owner='input_service',width=1,mask=1,valid=True,stage=0,origin='iv',enable='iv_wen',reset=0))
    for slot in contract['state_slots']:
        mask=sum(int(word,16)<<(64*i) for i,word in enumerate(slot['variable_mask_hex']))
        reset=sum(int(word,16)<<(64*i) for i,word in enumerate(slot['reset_hex']))
        prefix='external_capture/' if slot['external_capture'] else 'core/'
        words.append(dict(name=prefix+slot['name'],owner='external_state' if slot['external_capture'] else 'native_state',
            width=slot['declared_width'],mask=mask,valid=slot['valid'],stage=slot['stage'],origin=slot['origin'],
            enable='unconditional' if slot['valid'] or slot['external_capture'] else slot['enable_stage'],reset=reset))
    used=set();counts=Counter();result=[]
    for word in words:
        if word['name'] not in aliases or len(aliases[word['name']])!=word['width']:raise ValueError('logical mapped state name/width lost: '+word['name'])
        rows=[]
        for i,net in enumerate(aliases[word['name']]):
            resolved=resolve(net)
            if word['mask']>>i&1:
                if 'constant' in resolved:raise ValueError('variable state bit was optimized away: '+word['name'])
                if resolved['cell'] in used:raise ValueError('independent state bits share a mapped FF')
                used.add(resolved['cell']);counts[word['owner']]+=1
            elif resolved!=dict(constant=str(word['reset']>>i&1)):raise ValueError('state constant differs from compiler variable mask')
            rows.append(dict(bit=i,**resolved))
        result.append(dict(**word,rows=rows))
    actual={n for n,row in cells.items() if pins[row['type']]['sequential']}
    if actual!=used:raise ValueError('missing or extra mapped FFs: '+repr(sorted(actual^used)))
    return dict(version='stage67-mapped-state-v1',status='passed_variable_bit_FF_census',words=result,
        owner_FF_bits=dict(counts),all_FFs_accounted_once=True,constant_bits_checked=True,
        origin_stage_mask_compiler_contract_checked=True,reset_enable_functional_proof='pending_separate_gate',
        S_G_qualified=False,full_D_ready=False)
