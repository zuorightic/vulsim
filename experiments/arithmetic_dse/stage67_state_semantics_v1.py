"""Exact Boolean checks of mapped reset, hold, update and clock semantics.

Arithmetic outputs are cut as independent symbolic inputs.  The proof compares
each physical FF D cone with the unchanged compiler RTL's state assignment,
including Q alias inversion and the actual Liberty-derived sequential model.
"""
import argparse
import ast
from functools import lru_cache
from pathlib import Path
import re

from .model_fast_preflight import read,write,sha
from .stage67_mapped_state_v1 import flatten
from .stage67_physical_probe_v1 import SUFFIX


class BDD:
    def __init__(self):self.nodes={};self.unique={};self.variables={}
    def node(self,var,low,high):
        if low==high:return low
        key=(var,low,high)
        if key not in self.unique:
            n=len(self.nodes)+2;self.unique[key]=n;self.nodes[n]=key
        return self.unique[key]
    def variable(self,name):
        if name not in self.variables:self.variables[name]=len(self.variables)
        return self.node(self.variables[name],0,1)
    @lru_cache(maxsize=None)
    def apply(self,op,a,b):
        if a<2 and b<2:return {'and':a&b,'or':a|b,'xor':a^b}[op]
        va=self.nodes[a][0] if a>1 else float('inf');vb=self.nodes[b][0] if b>1 else float('inf');v=min(va,vb)
        al,ah=self.nodes[a][1:] if va==v else (a,a);bl,bh=self.nodes[b][1:] if vb==v else (b,b)
        return self.node(v,self.apply(op,al,bl),self.apply(op,ah,bh))
    def inv(self,a):return self.apply('xor',1,a)
    def mux(self,s,a,b):return self.apply('or',self.apply('and',s,a),self.apply('and',self.inv(s),b))


def sequential_polarity(module,qpin,dpin,cpin):
    inputs={module['ports'][dpin]['bits'][0]:None};cells=module['cells'];drivers={}
    for row in cells.values():
        for p,di in row['port_directions'].items():
            if di=='output':
                for bit in row['connections'][p]:drivers[bit]=(row,p)
    clock=module['ports'][cpin]['bits'][0]
    def run(value):
        @lru_cache(maxsize=None)
        def bit(n):
            if n==module['ports'][dpin]['bits'][0]:return value
            if isinstance(n,str):return int(n)
            row,p=drivers[n];kind=row['type'];c=row['connections']
            if kind=='$_DFF_P_':
                if c['C']!=[clock]:raise ValueError('Liberty state clock is not a direct positive edge clock')
                return bit(c['D'][0])
            if kind=='$_NOT_':return 1^bit(c['A'][0])
            raise ValueError('unsupported actual sequential primitive '+kind)
        return bit(module['ports'][qpin]['bits'][0])
    pair=[run(0),run(1)]
    if pair not in ([0,1],[1,0]):raise ValueError('FF output is not D or inverted D')
    return pair[0]


def verify(directory,state,rtl,contract):
    pins=read(directory/'liberty-pins.json');design=read(directory/'mapped.json');cells,aliases=flatten(design,pins)
    cec=read(directory/'logs'/SUFFIX/'structural_cec/gold-hier.json')['modules'];bdd=BDD();drivers={};cut=set();top=design['modules']['ModelBundle']
    # Ports and FF Qs are arbitrary inputs; arithmetic output nets are arbitrary
    # inputs too, so no numerical arithmetic sample can make this proof pass.
    for name,row in cells.items():
        for term,meta in pins[row['type']]['pins'].items():
            if meta['direction']!='output':continue
            n=row['connections'][term][0]
            if not isinstance(n,str):drivers[n]=(name,term)
    for n,(name,term) in drivers.items():
        meta=pins[cells[name]['type']]
        if meta['sequential']:cut.add(n)
        if any(name.startswith(s['scope']+'/') for s in contract['operator_scopes']):
            # Only outputs crossing the arithmetic owner's boundary are needed.
            if any(n in bits for other,row in cells.items() if not other.startswith(name.rsplit('/',1)[0]+'/') for bits in row['connections'].values()):cut.add(n)
    top_inputs={n for p,v in top['ports'].items() if v['direction']=='input' for n in aliases.get(p,[])}
    cut|=top_inputs
    # Stable ordering is fixed before recursive evaluation.
    for n in sorted(cut,key=repr):bdd.variable(repr(n))
    @lru_cache(maxsize=None)
    def evaluate(n):
        if isinstance(n,str):
            if n not in ('0','1'):raise ValueError('unknown mapped constant')
            return int(n)
        if n in cut:return bdd.variable(repr(n))
        if n not in drivers:raise ValueError('undriven Boolean data cone')
        name,terminal=drivers[n];row=cells[name];meta=pins[row['type']]
        if meta['sequential']:raise ValueError('uncut sequential boundary')
        function=meta['pins'][terminal].get('function')
        if not function:raise ValueError('missing actual Liberty Boolean function')
        text=function.replace('*','&').replace('+','|').replace('!','~')
        expr=ast.parse(text,mode='eval')
        def walk(x):
            if isinstance(x,ast.Name):return evaluate(row['connections'][x.id][0])
            if isinstance(x,ast.Constant) and x.value in (0,1):return x.value
            if isinstance(x,ast.UnaryOp) and isinstance(x.op,ast.Invert):return bdd.inv(walk(x.operand))
            if isinstance(x,ast.BinOp) and type(x.op) in (ast.BitAnd,ast.BitOr,ast.BitXor):return bdd.apply({ast.BitAnd:'and',ast.BitOr:'or',ast.BitXor:'xor'}[type(x.op)],walk(x.left),walk(x.right))
            raise ValueError('unsupported Liberty Boolean expression')
        return walk(expr.body)
    modules={}
    for match in re.finditer(r'\bmodule\s+(\w+)\s*\([^;]*;(?P<body>.*?)\bendmodule',rtl,re.S):modules[match[1]]=match['body']
    core=next(body for name,body in modules.items() if name.endswith('_core'))
    bodies={'core':core,'launch':next(body for name,body in modules.items() if name.endswith('_Launch')),
            'external_capture':next(body for name,body in modules.items() if name.endswith('_Capture'))}
    @lru_cache(maxsize=None)
    def signal(scope,expr,width):
        expr=expr.strip()
        while expr.startswith('(') and expr.endswith(')'):expr=expr[1:-1].strip()
        key=scope+'/'+expr
        if key in aliases:
            bits=aliases[key]
            if len(bits)!=width:raise ValueError('original source/semantic word width mismatch')
            return tuple(evaluate(n) for n in bits)
        scalar=[aliases.get(key+'['+str(i)+']') for i in range(width)]
        if all(v is not None and len(v)==1 for v in scalar):return tuple(evaluate(v[0]) for v in scalar)
        number=re.fullmatch(r"(?:(\d+)'([hbd]))?([0-9a-fA-F]+)",expr)
        if number:
            value=int(number[3],{'h':16,'b':2,'d':10,None:10}[number[2]]);return tuple(value>>i&1 for i in range(width))
        if expr.startswith('{') and expr.endswith('}'):
            pieces=expr[1:-1].split(',');out=[]
            for piece in reversed(pieces):
                m=re.fullmatch(r"\s*(\d+)'[hbd][0-9a-fA-F]+\s*",piece)
                w=int(m[1]) if m else width-len(out)-sum(int(k) for k in re.findall(r"(\d+)'[hbd]",','.join(pieces[:pieces.index(piece)])))
                out.extend(signal(scope,piece,w))
            if len(out)!=width:raise ValueError('unsupported RTL concatenation width')
            return tuple(out)
        if not re.fullmatch(r'\w+',expr):raise ValueError('unsupported original state source expression '+expr)
        direct=re.search(r'\bassign\s+'+re.escape(expr)+r'\s*=\s*([^;]+);',bodies[scope])
        if direct:return signal(scope,direct[1],width)
        for line in bodies[scope].splitlines():
            match=re.search(r'\b(\w+)\s*\(([^;]*)\)\s*;',line)
            if not match:continue
            for port,argument in re.findall(r'\.(\w+)\s*\(\s*(\w+)\s*\)',match[2]):
                key=scope+'/'+match[1]+'/'+port
                if argument==expr and key in aliases and len(aliases[key])==width:return tuple(evaluate(n) for n in aliases[key])
        raise ValueError('original state source has no checked mapped alias '+scope+'/'+expr)
    checked=[]
    for w in state['words']:
        scope,name=w['name'].split('/',1);assigns=re.findall(r'\b'+re.escape(name)+r'\s*<=\s*([^;]+);',bodies[scope])
        if len(assigns)!=2:raise ValueError('expected one reset and one update assignment per state word')
        reset=signal(scope,assigns[0],w['width']);source=signal(scope,assigns[1],w['width'])
        if tuple(w['reset']>>i&1 for i in range(w['width']))!=reset:raise ValueError('compiler reset differs from original RTL')
        enable=signal(scope,w['enable'] if isinstance(w['enable'],str) and w['enable']!='unconditional' else 'iv',1)[0] if w['enable']!='unconditional' else 1
        rstn=signal(scope,'rstn',1)[0]
        for r in w['rows']:
            if 'cell' not in r:continue
            cell=cells[r['cell']];meta=pins[cell['type']];clocks=meta['clock_pins']
            if len(clocks)!=1:raise ValueError('unsupported state clock inventory')
            polarity=sequential_polarity(cec[cell['type']],r['Q'],r['D'],clocks[0])
            q=evaluate(cell['connections'][r['Q']][0]);old=bdd.inv(q) if r['logical_output_inverted'] else q
            expected=bdd.mux(rstn,bdd.mux(enable,source[r['bit']],old),reset[r['bit']])
            actual=evaluate(cell['connections'][r['D']][0])
            if polarity^r['logical_output_inverted']:actual=bdd.inv(actual)
            if actual!=expected:raise ValueError('mapped FF reset/hold/update differs: '+w['name']+'/'+str(r['bit']))
            if evaluate(cell['connections'][clocks[0]][0])!=signal(scope,'clk',1)[0]:raise ValueError('mapped FF clock changed')
            checked.append(dict(word=w['name'],bit=r['bit'],cell=r['cell'],actual_boolean_root=actual,expected_boolean_root=expected,clock_positive_edge=True))
    return dict(version='stage67-actual-state-semantics-v1',status='passed_exact_Boolean_state_functions',checked_FF_bits=len(checked),checks=checked,
        symbolic_variables=len(bdd.variables),BDD_nodes=len(bdd.nodes),reset_enable_hold_update_and_clock=True,arithmetic_outputs_independent=True,
        no_fitting_or_physical_calls=True,full_D_ready=False)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('preserve actual-state proof attempt')
    a.out.mkdir(parents=True)
    for t in read(a.root/'admission.json')['tasks']:
        bank=a.root/'runs'/t['id'];directory=Path(read(bank/'physical-directory.json')['path']) if (bank/'physical-directory.json').exists() else bank
        value=verify(directory,read(bank/'mapped-state.json'),(directory/'input.sv').read_text(),read(t['endpoint_contract']))
        write(a.out/(t['id']+'.json'),value);print(t['id'],value['status'],value['checked_FF_bits'],flush=True)
