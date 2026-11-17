"""Reconstruct removed state aliases only through unchanged RTL wiring.

The original mapped census remains authoritative. Bidirectional direct-wire
and concatenation equalities recover output-concatenated forwarding state;
no variable mask or expected reset value supplies an absent mapped bit.
"""
import re
from unittest.mock import patch
from . import stage67_mapped_state_v3 as mapped


def verify(design,pins,contract,source,rtl):
    original=mapped.base.flatten
    proof=[]
    def flatten(d,p):
        cells,aliases=original(d,p)
        drivers={}
        for name,row in cells.items():
            for term,meta in p[row['type']]['pins'].items():
                if meta['direction']=='output':
                    for bit in row['connections'].get(term,[]):drivers[bit]=(name,term)
        def normal(bit):
            seen=set();inv=False
            while bit in drivers:
                if bit in seen:raise ValueError('cyclic mapped unary alias')
                seen.add(bit);name,term=drivers[bit];cell=cells[name];meta=p[cell['type']]
                inputs=[n for n,v in meta['pins'].items() if v['direction']=='input']
                fn=re.sub(r'[\s()]','',meta['pins'][term].get('function') or '')
                if not meta['buffer_or_inverter'] or len(inputs)!=1 or fn not in (inputs[0],'!'+inputs[0],'~'+inputs[0]):break
                inv^=fn!=inputs[0];bit=cell['connections'][inputs[0]][0]
            return bit,inv
        def same(a,b):return len(a)==len(b) and all(normal(x)==normal(y) for x,y in zip(a,b))
        core=re.search(r'\bmodule\s+\w+_core\s*\([^;]*;(?P<body>.*?)\bendmodule',rtl,re.S)
        if core is None:raise ValueError('missing unchanged native core')
        body=core['body']
        widths={name:(int(a)-int(b)+1 if a else 1) for a,b,name in re.findall(r'\b(?:logic|wire|reg)\s*(?:\[(\d+):(\d+)\])?\s*(\w+)\s*;',body)}
        for n,v in list(aliases.items()):
            if n.startswith('core/') and '[' not in n:widths.setdefault(n[5:],len(v))
        for slot in contract['state_slots']:
            if not slot['external_capture']:widths.setdefault(slot['name'],slot['declared_width'])
        def get(name):
            key='core/'+name
            if key in aliases:return aliases[key]
            if name in widths:
                scalar=[aliases.get(key+'['+str(i)+']') for i in range(widths[name])]
                if all(v is not None and len(v)==1 for v in scalar):return [v[0] for v in scalar]
            return None
        def bind(name,bits,reason):
            old=get(name)
            if old is not None:
                if not same(old,bits):raise ValueError('actual mapped wiring aliases disagree: '+name)
                return False
            if widths.get(name)!=len(bits):return False
            for i,bit in enumerate(bits):
                scalar=aliases.get('core/'+name+'['+str(i)+']')
                if scalar is not None and not same(scalar,[bit]):raise ValueError('scalar wiring mismatch')
            aliases['core/'+name]=list(bits);proof.append(dict(name=name,width=len(bits),reason=reason));return True
        def expression(text):
            text=text.strip()
            while text.startswith('(') and text.endswith(')'):
                depth=0;whole=True
                for j,c in enumerate(text):
                    depth+=(c=='(')-(c==')')
                    if depth==0 and j<len(text)-1:whole=False;break
                if not whole:break
                text=text[1:-1].strip()
            literal=re.fullmatch(r"(\d+)'([hbd])([0-9a-fA-F]+)",text)
            if literal:
                w,base,value=literal.groups();number=int(value,{'h':16,'b':2,'d':10}[base]);return [str(number>>i&1) for i in range(int(w))]
            part=re.fullmatch(r'(\w+)\[(\d+)(?::(\d+))?\]',text)
            if part:
                name,hi,lo=part.groups();value=get(name)
                return None if value is None else value[int(lo or hi):int(hi)+1]
            if re.fullmatch(r'\w+',text):return get(text)
            if text.startswith('{') and text.endswith('}'):
                parts=[expression(p) for p in text[1:-1].split(',')]
                if all(p is not None for p in parts):return [b for p in reversed(parts) for b in p]
            return None
        assignments=re.findall(r'\bassign\s+(\w+)\s*=\s*([^;]+);',body)
        sequential={}
        for lhs,rhs in re.findall(r'\b(\w+)\s*<=\s*([^;]+);',body):sequential.setdefault(lhs,[]).append(rhs)
        for _ in range(len(assignments)+len(sequential)+1):
            changed=False
            for lhs,expr in assignments:
                expr=expr.strip();left=get(lhs)
                forward=expression(expr)
                if forward is not None and lhs in widths:changed=bind(lhs,forward,'unchanged RTL wiring expression') or changed
                if re.fullmatch(r'\w+',expr):
                    right=get(expr)
                    if right is not None:changed=bind(lhs,right,'unchanged direct assignment') or changed
                    if left is not None:changed=bind(expr,left,'unchanged direct assignment inverse') or changed
                elif re.fullmatch(r'\{\s*\w+(?:\s*,\s*\w+)*\s*\}',expr):
                    names=list(reversed(re.findall(r'\w+',expr)));parts=[get(n) for n in names]
                    if all(v is not None for v in parts):changed=bind(lhs,[b for v in parts for b in v],'unchanged concatenation') or changed
                    if left is not None and all(n in widths for n in names) and sum(widths[n] for n in names)==len(left):
                        pos=0
                        for n in names:
                            changed=bind(n,left[pos:pos+widths[n]],'unchanged concatenation inverse bit slice') or changed;pos+=widths[n]
            for lhs,expressions in sequential.items():
                if get(lhs) is not None:continue
                values=[expression(x) for x in expressions]
                if all(v is not None and all(b in ('0','1') for b in v) for v in values) and all(v==values[0] for v in values):
                    changed=bind(lhs,values[0],'all explicit reset/update RHS prove same constant; implicit hold preserves it') or changed
            if not changed:break
        return cells,aliases
    with patch.object(mapped.base,'flatten',flatten):result=mapped.verify(design,pins,contract,source,rtl)
    result.update(Nangate45_wiring_alias_reconstruction=proof,expected_mask_used_for_reconstruction=False)
    return result
