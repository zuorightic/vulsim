"""Constant-folded logical ALU DAG from the actual demanded result.

The prefix topology is a work proxy for the generic Yosys ALU. Gate counts
are computed before mapping, never read from a candidate's physical netlist.
"""
import math
from . import wide_arithmetic as arithmetic,wide_operator_samples as samples

VERSION='wide-demanded-ALU-geometry-v1'


def circuit(spec):
    arithmetic.validate(spec);nodes={};leaves={};intern={};next_id=2
    def leaf(name,bit):
        nonlocal next_id
        key=(name,bit)
        if key not in leaves:leaves[key]=next_id;next_id+=1
        return leaves[key]
    def gate(kind,a,b=0):
        nonlocal next_id
        if kind=='not':
            if a<2:return 1-a
            if a in nodes and nodes[a][0]=='not':return nodes[a][1]
        elif kind=='and':
            if not a or not b:return 0
            if a==1:return b
            if b==1 or a==b:return a
        elif kind=='or':
            if a==1 or b==1:return 1
            if not a:return b
            if not b or a==b:return a
        elif kind=='xor':
            if not a:return b
            if not b:return a
            if a==b:return 0
            if a==1:return gate('not',b)
            if b==1:return gate('not',a)
        if kind!='not' and a>b:a,b=b,a
        key=(kind,a,b)
        if key not in intern:intern[key]=next_id;nodes[next_id]=key;next_id+=1
        return intern[key]
    w=spec['arithmetic_width'];op=spec['operation'];ctrl=leaf('cin',0) if spec['carry']=='dynamic' else int(spec['carry']=='one')
    def inputs(name):
        needed=samples.input_demand(spec,name);bits=[]
        for i in range(w):
            possible=arithmetic.bit_values(spec,name,i)
            bits.append(leaf(name,i) if len(possible)==2 and i in needed else possible[0] if len(possible)==1 else 0)
        return bits
    aa=inputs('lhs');bb=inputs('rhs');status=0
    if op=='mux':
        native=[gate('or',gate('and',gate('not',ctrl),a),gate('and',ctrl,b)) for a,b in zip(aa,bb)]
    elif op=='eq':
        diff=[gate('xor',a,b) for a,b in zip(aa,bb)]
        while len(diff)>1:diff=[gate('or',diff[i],diff[i+1] if i+1<len(diff) else 0) for i in range(0,len(diff),2)]
        native=[gate('not',diff[0])]+[0]*(w-1)
    elif op=='mul':
        return dict(nodes={},leaves=leaves,outputs=[],mul=True)
    else:
        subtract=op in ('sub','sbb','ult','ule')
        if op=='ule':aa,bb=bb,aa
        if subtract:bb=[gate('not',b) for b in bb];ctrl=gate('not',ctrl) if op in ('sub','sbb') else 1
        p=[gate('xor',a,b) for a,b in zip(aa,bb)];original=p.copy();g=[gate('and',a,b) for a,b in zip(aa,bb)];g[0]=gate('or',g[0],gate('and',p[0],ctrl))
        levels=math.ceil(math.log2(w))
        for i in range(1,levels+1):
            for j in range((1<<i)-1,w,1<<i):g[j]=gate('or',g[j],gate('and',p[j],g[j-(1<<(i-1))]));p[j]=gate('and',p[j],p[j-(1<<(i-1))])
        for i in range(levels,0,-1):
            for j in range((1<<i)+(1<<(i-1))-1,w,1<<i):g[j]=gate('or',g[j],gate('and',p[j],g[j-(1<<(i-1))]));p[j]=gate('and',p[j],p[j-(1<<(i-1))])
        native=[gate('xor',original[i],g[i-1] if i else ctrl) for i in range(w)]
        if op in ('ult','ule'):native=[gate('not',g[-1]) if op=='ult' else g[-1]]+[0]*(w-1)
        status=gate('not',g[-1]) if subtract else g[-1]
    outputs=native[spec['result_lo']:spec['result_lo']+spec['value_width']]+([status] if spec['status']!='none' else [])
    return dict(nodes=nodes,leaves=leaves,outputs=outputs,mul=False)


def geometry(spec):
    c=circuit(spec);nodes=c['nodes'];live=set();inputs=set();depth={0:0,1:0}
    def visit(n):
        if n<2:return 0
        if n not in nodes:inputs.add(n);return 0
        if n in live:return depth[n]
        live.add(n);kind,a,b=nodes[n];depth[n]=max(visit(a),visit(b))+1;return depth[n]
    for n in c['outputs']:visit(n)
    used={name:sorted(bit for (name_,bit),n in c['leaves'].items() if name_==name and n in inputs) for name in ('lhs','rhs')}
    if c['mul']:
        used={name:sorted(i for i in samples.input_demand(spec,name) if len(arithmetic.bit_values(spec,name,i))==2) for name in ('lhs','rhs')}
    f={name:float(sum(nodes[n][0]==kind for n in live)) for name,kind in (('alu_xor','xor'),('alu_and','and'),('alu_or','or'),('alu_not','not'))}
    f.update(alu_work=float(len(live)),alu_depth=float(max((depth.get(n,0) for n in c['outputs']),default=0)))
    return dict(features=f,used=used,dynamic_outputs=[i for i,n in enumerate(c['outputs']) if n>=2],mul=c['mul'])


def evaluate(spec,a,b,control=0):
    c=circuit(spec)
    if c['mul']:raise ValueError('ALU graph excludes multiplication')
    values={0:0,1:1}
    for (name,bit),n in c['leaves'].items():values[n]=((a if name=='lhs' else b if name=='rhs' else int(bool(control)))>>bit)&1
    for n,(kind,x,y) in c['nodes'].items():
        aa=values[x];bb=values[y];values[n]=(1-aa) if kind=='not' else aa&bb if kind=='and' else aa|bb if kind=='or' else aa^bb
    return sum(values[n]<<i for i,n in enumerate(c['outputs']))
