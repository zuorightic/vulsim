"""Bit-exact aliases through compiler pure wiring and equal state updates.

No expected variable mask fills an absent mapped bit. A missing register is
reconstructed only from an unchanged RTL update, reset, enable and stage that
matches a surviving mapped state bit. Arithmetic is a symbolic hard boundary.
"""
from collections import defaultdict
import inspect
import re
from types import FunctionType,SimpleNamespace

from . import stage67_mapped_state_v1 as original
from . import stage67_mapped_state_v3 as previous


def body_and_terms(rtl,contract):
    match=re.search(r'\bmodule\s+\w+_core\s*\([^;]*;(?P<body>.*?)\bendmodule',rtl,re.S)
    if not match:raise ValueError('compiler core absent')
    body=match['body'];widths={}
    for m in re.finditer(r'\b(?:logic|wire)\s*(?:\[(\d+):0\])?\s*(\w+)\s*(?:[,;]|//|\))',body):widths[m[2]]=int(m[1])+1 if m[1] else 1
    assigns={m[1]:m[2] for m in re.finditer(r'\bassign\s+(\w+)\s*=\s*([^;]+);',body)}
    cache={};visiting=set()
    def expr(text):
        text=text.strip()
        while text.startswith('(') and text.endswith(')'):text=text[1:-1].strip()
        literal=re.fullmatch(r"(\d+)'([hbd])([0-9a-fA-F]+)",text)
        if literal:
            v=int(literal[3],{'h':16,'b':2,'d':10}[literal[2]]);return [('constant',v>>i&1) for i in range(int(literal[1]))]
        if text in ('0','1'):return [('constant',int(text))]
        if text.startswith('{') and text.endswith('}'):
            parts=[];start=0;depth=0
            for i,ch in enumerate(text[1:-1]):
                if ch in '{(':depth+=1
                elif ch in '})':depth-=1
                elif ch==',' and not depth:parts.append(text[1:-1][start:i]);start=i+1
            parts.append(text[1:-1][start:]);return [bit for p in reversed(parts) for bit in expr(p)]
        selection=re.fullmatch(r'(\w+)\[(\d+)(?::(\d+))?\]',text)
        if selection:
            hi=int(selection[2]);lo=int(selection[3]) if selection[3] else hi;bits=signal(selection[1])
            if not 0<=lo<=hi<len(bits):raise ValueError('pure-wire slice outside declaration')
            return bits[lo:hi+1]
        if re.fullmatch(r'\w+',text):return signal(text)
        raise ValueError('not a supported exact pure bit expression: '+text)
    def signal(name):
        if name in cache:return cache[name]
        if name in visiting:raise ValueError('cycle in pure wiring')
        visiting.add(name)
        if name in assigns:bits=expr(assigns[name])
        elif name in widths:bits=[('signal',name,i) for i in range(widths[name])]
        else:raise ValueError('pure-wire signal has no declaration '+name)
        visiting.remove(name);cache[name]=bits;return bits
    words={}
    for s in contract['state_slots']:
        if s['external_capture'] or s['valid']:continue
        name=s['name'];updates=re.findall(r'\b'+re.escape(name)+r'\s*<=\s*([^;]+);',body)
        if len(updates)!=2:raise ValueError('one reset and one data update required')
        reset=expr(updates[0]);data=expr(updates[1])
        if len(data)!=s['declared_width'] or len(reset)!=s['declared_width'] or any(x[0]!='constant' for x in reset):raise ValueError('exact update/reset width mismatch')
        words[name]=dict(slot=s,data=data,reset=reset)
    return body,widths,assigns,expr,signal,words


def augment(design,pins,rtl,contract):
    cells,aliases=original.flatten(design,pins);body,widths,assigns,expr,signal,words=body_and_terms(rtl,contract)
    # Direct physical aliases and original consumer terminals are evidence for
    # a state word, only when their bit is a surviving actual FF-Q/buffer chain.
    drivers={}
    for name,c in cells.items():
        for term,meta in pins[c['type']]['pins'].items():
            if meta['direction']=='output':
                for net in c['connections'][term]:
                    if not isinstance(net,str):drivers[net]=(name,term)
    def sequential(net):
        seen=set()
        while not isinstance(net,str):
            if net in seen or net not in drivers:return False
            seen.add(net);name,term=drivers[net];c=cells[name];meta=pins[c['type']]
            if meta['sequential']:return True
            ins=[p for p,v in meta['pins'].items() if v['direction']=='input'];fn=re.sub(r'[\s()]','',meta['pins'][term].get('function') or '')
            if len(ins)!=1 or not meta['buffer_or_inverter'] or fn not in (ins[0],'!'+ins[0],'~'+ins[0]):return False
            net=c['connections'][ins[0]][0]
        return False
    evidence=defaultdict(list);word_candidates={}
    ports=[]
    for line in body.splitlines():
        m=re.search(r'\b(\w+)\s*\(([^;]*)\)\s*;',line)
        if m:ports += [(arg,'core/'+m[1]+'/'+port) for port,arg in re.findall(r'\.(\w+)\s*\(\s*(\w+)\s*\)',m[2])]
    for name,w in words.items():
        slot=w['slot'];candidates=[];key='core/'+name
        if key in aliases:candidates.append((key,aliases[key]))
        for lhs,rhs in assigns.items():
            if rhs.strip()==name and 'core/'+lhs in aliases:candidates.append(('core/'+lhs,aliases['core/'+lhs]))
        candidates += [(port,aliases[port]) for arg,port in ports if arg==name and port in aliases]
        word_candidates[name]=candidates
        for candidate,bits in candidates:
            if len(bits)!=len(w['data']):continue
            for i,(token,reset,net) in enumerate(zip(w['data'],w['reset'],bits)):
                if token[0]=='constant' or not sequential(net):continue
                semantic=(slot['stage'],slot['enable_stage'],token,reset)
                evidence[semantic].append(dict(word=name,bit=i,alias=candidate,net=net))
    proof=[]
    for name,w in words.items():
        key='core/'+name
        if key in aliases:continue
        slot=w['slot'];bits=[];witness=[]
        for i,(token,reset) in enumerate(zip(w['data'],w['reset'])):
            if token[0]=='constant':bits.append(str(token[1]));continue
            semantic=(slot['stage'],slot['enable_stage'],token,reset);found=evidence.get(semantic,[])
            if not found:raise ValueError('no surviving FF evidence for exact update bit '+name+'/'+str(i))
            # Different raw net aliases may be buffers; the mapped census and
            # independent exact Boolean proof still resolve polarity/FF owner.
            bits.append(found[0]['net']);witness.append(dict(bit=i,semantic_update=list(token),reset=reset[1],witness_word=found[0]['word'],witness_bit=found[0]['bit'],mapped_alias=found[0]['alias']))
        aliases[key]=bits;proof.append(dict(word=name,rule='same stage/enable/exact pure data update/reset as surviving mapped FF',bits=witness))
    # Restore absent combinational aliases only from exact original bit terms
    # and mapped public/arithmetic output signals; never overwrite real pins.
    signal_nets={}
    for name,bits in aliases.items():
        if name.startswith('core/') and '/' not in name[len('core/'):]:
            for i,net in enumerate(bits):signal_nets['signal',name[len('core/'):],i]=net
    for arg,port in ports:
        if port in aliases:
            for i,net in enumerate(aliases[port]):signal_nets.setdefault(('signal',arg,i),net)
    for name in assigns:
        if 'core/'+name in aliases:continue
        tokens=signal(name)
        if all(t[0]=='constant' or t in signal_nets for t in tokens):aliases['core/'+name]=[str(t[1]) if t[0]=='constant' else signal_nets[t] for t in tokens]
    return cells,aliases,proof


def verify(design,pins,contract,source,rtl):
    def flatten(d,p):
        cells,aliases,_=augment(d,p,rtl,contract);return cells,aliases
    shim=SimpleNamespace(verify=original.verify,flatten=flatten)
    ns=dict(previous.verify.__globals__);ns['base']=shim
    result=FunctionType(previous.verify.__code__,ns)(design,pins,contract,source,rtl)
    _,_,proof=augment(design,pins,rtl,contract)
    result.update(version='pure-bit-state-alias-census-v1',pure_bit_alias_proof=proof,physical_state_functional_proof_required=True)
    return result
