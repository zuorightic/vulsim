"""Sparse reduction shells with explicit constant and passthrough certificates.

Independent unsigned bit terms permit exact output classification without
physical observations. Only dynamic output bits receive capture FFs. Mapped
ports must agree with the certificate; no path is invented for a wire or zero.
"""
from . import reduction_sampling as parent

VERSION='register-reduction-sampling-v2-sparse-output-contract'
evaluate=parent.evaluate


def geometry(query):
    if query.get('consumers'):raise ValueError('first sparse region scope uses direct capture only')
    g=parent.geometry(query);w=g['output_bits'];columns=[[] for _ in range(w)]
    for term in query['terms']:
        for source,bit,column in term:columns[column].append(g['offsets'][source,bit])
    maximum_lower=0;semantics=[];tokens=[]
    for bit,inputs in enumerate(columns):
        carry_possible=maximum_lower>=(1<<bit)
        if not inputs and not carry_possible:
            row=dict(bit=bit,kind='constant',value='0');token='0'
        elif len(inputs)==1 and not carry_possible:
            row=dict(bit=bit,kind='passthrough',input_bit=inputs[0]);token=('input',inputs[0])
        else:row=dict(bit=bit,kind='node_logic');token=('producer',bit)
        semantics.append(row);tokens.append(token);maximum_lower+=len(inputs)*(1<<bit)
    if not any(r['kind']=='node_logic' for r in semantics):
        raise ValueError('pure wiring reduction needs a separate zero-intrinsic-cost lowering')
    live=list(dict.fromkeys(t for t in tokens if not isinstance(t,str)))
    return dict(g,output_semantics=semantics,captures=[dict(id='direct0bank0',tokens=tokens,live_tokens=live)])


def geometry_contract(query):
    g=geometry(query)
    return dict(version=VERSION,launch_FF_bits=g['input_bits']+1,
                capture_FF_bits=len(g['captures'][0]['live_tokens'])+1,
                output_semantics=g['output_semantics'])


def source(query,name='ModelBundle'):
    g=geometry(query);text=parent.source(query,name);w=g['output_bits']
    bits=[r['bit'] for r in g['output_semantics'] if r['kind']!='constant'];rank={b:i for i,b in enumerate(bits)}
    declaration=f'(* keep,dont_touch *) reg [{w-1}:0] storage0;'
    update='(* keep *) always @(posedge clk)storage0<=value;'
    assign='assign data=storage0;'
    if any(text.count(x)!=1 for x in (declaration,update,assign)):raise ValueError('unsupported predecessor capture template')
    text=text.replace(declaration,f'(* keep,dont_touch *) reg [{len(bits)-1}:0] storage0;')
    text=text.replace(update,'(* keep *) always @(posedge clk)storage0<={'+','.join(f'value[{b}]' for b in reversed(bits))+'};')
    assignments=[f'assign data[{r["bit"]}]='+('1\'b0;' if r['kind']=='constant' else f'storage0[{rank[r["bit"]]}];') for r in g['output_semantics']]
    return text.replace(assign,'\n'.join(assignments))


def mapped_port_contract(design,query,pins):
    g=geometry(query);modules=design['modules'];core=modules[modules['ModelBundle']['cells']['core']['type']]
    inputs={b:i for i,b in enumerate(core['ports']['a']['bits']) if type(b) is int};drivers={}
    for name,cell in core['cells'].items():
        if pins[cell['type']]['sequential']:raise ValueError('state inside fused arithmetic region')
        for pin,meta in pins[cell['type']]['pins'].items():
            if meta['direction']=='output':
                for bit in cell['connections'].get(pin,[]):
                    if bit in drivers:raise ValueError('multiple mapped drivers')
                    drivers[bit]=(name,pin,cell)
    def alias(bit):
        seen=set();inverted=False
        while type(bit) is int:
            if bit in inputs:return ('input',inputs[bit],inverted)
            if bit in seen:raise ValueError('cyclic mapped output alias')
            seen.add(bit)
            if bit not in drivers:return None
            _,pin,cell=drivers[bit];meta=pins[cell['type']]
            ins=[p for p,v in meta['pins'].items() if v['direction']=='input']
            fn=(meta['pins'][pin].get('function') or '').replace(' ','').replace('(','').replace(')','')
            if not ins and fn in ('0','1',"1'b0","1'b1"):return ('constant',str(int(fn[-1])^inverted))
            if len(ins)!=1 or fn not in (ins[0],'!'+ins[0],'~'+ins[0]):return None
            inverted^=fn!=ins[0];bit=cell['connections'][ins[0]][0]
        return ('constant',str(int(bit)^inverted)) if bit in ('0','1') else None
    mapped=core['ports']['value']['bits']
    if len(mapped)!=g['output_bits']:raise ValueError('mapped output width changed')
    rows=[]
    for expected,bit in zip(g['output_semantics'],mapped,strict=True):
        value=alias(bit);kind=expected['kind']
        if kind=='constant' and value!=('constant','0'):raise ValueError('mapped constant output violates independent-bit sum')
        if kind=='passthrough' and value!=('input',expected['input_bit'],False):raise ValueError('mapped passthrough violates independent-bit sum')
        if kind=='node_logic' and (value is not None or bit not in drivers):raise ValueError('missing true arithmetic output')
        row=dict(expected)
        if bit in drivers:row['driver_pin']='core/'+drivers[bit][0]+'/'+drivers[bit][1]
        rows.append(row)
    return dict(version=VERSION,outputs=rows,constants_and_passthrough_explicit=True,
                whole_region=True,individual_internal_Add_labels_required=False)
