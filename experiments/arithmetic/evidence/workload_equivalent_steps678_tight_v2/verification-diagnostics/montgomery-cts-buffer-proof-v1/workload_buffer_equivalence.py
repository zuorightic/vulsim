"""Conservative graph isomorphism proof for mapped buffer/size repairs.

After eliminating Liberty-proven identity buffers, every non-buffer instance
must retain its functional cell signature and every input must have the same
primary-input/constant/instance-output driver. All output drivers and the
interface must match too. This is a sufficient condition for equivalence,
including corresponding sequential state. Unsupported syntax or any change
outside that condition fails closed; this is not a general SAT checker.
"""
import argparse
import gzip
import json
from pathlib import Path
import re
import sys


def norm_expr(value):
    return tuple(re.findall(r'[A-Za-z_][A-Za-z_0-9]*|[^\s]',value))


def brace_body(text,start):
    depth=0;quoted=False;escape=False
    for i in range(start,len(text)):
        c=text[i]
        if escape:escape=False;continue
        if c=='\\' and quoted:escape=True;continue
        if c=='"':quoted=not quoted
        if quoted:continue
        if c=='{':depth+=1
        elif c=='}':
            depth-=1
            if depth==0:return text[start+1:i],i+1
    raise ValueError('unterminated Liberty block')


def library(paths):
    cells={}
    for path in paths:
        p=Path(path);raw=p.read_bytes();text=(gzip.decompress(raw) if p.suffix=='.gz' else raw).decode()
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
        for match in re.finditer(r'\bcell\s*\(\s*"?([^\s"()]+)"?\s*\)\s*\{',text):
            body,_=brace_body(text,match.end()-1);ports={};functions={};tristate=False
            for pin in re.finditer(r'\bpin\s*\(\s*"?([^\s"()]+)"?\s*\)\s*\{',body):
                pb,_=brace_body(body,pin.end()-1);name=pin.group(1)
                direction=re.search(r'\bdirection\s*:\s*"?(input|output|inout|internal)\b',pb)
                if not direction:raise ValueError('Liberty pin direction unavailable')
                ports[name]=direction.group(1)
                f=re.search(r'\bfunction\s*:\s*"([^"]*)"',pb)
                functions[name]=norm_expr(f.group(1)) if f else None
                tristate=tristate or bool(re.search(r'\bthree_state\s*:',pb))
            state=[]
            for seq in re.finditer(r'\b(ff|latch|statetable)\s*\(([^)]*)\)\s*\{',body):
                sb,_=brace_body(body,seq.end()-1)
                state.append((seq.group(1),' '.join(seq.group(2).split()),' '.join(sb.split())))
            inputs=sorted(p for p,d in ports.items() if d=='input');outputs=sorted(p for p,d in ports.items() if d=='output')
            buffer=None
            if not state and not tristate and len(inputs)==len(outputs)==1 and 'inout' not in ports.values():
                expr=functions[outputs[0]]
                if expr in ((inputs[0],),('(',inputs[0],')')):buffer=(inputs[0],outputs[0])
            # Missing functional data is opaque: only the exact same cell
            # type can match it. No guessed drive-name alias is permitted.
            opaque=tristate or any(functions[p] is None for p in outputs)
            signature=(tuple(sorted(ports.items())),tuple((p,functions[p]) for p in outputs),tuple(state),
                       match.group(1) if opaque else None)
            cells[match.group(1)]=dict(ports={p:d for p,d in ports.items() if d!='internal'},signature=signature,buffer=buffer)
    return cells


class Netlist:
    def __init__(self,path,cells):
        self.cells={};self.drivers={};self.interface={};self.buffer_count=0;self.cache={};self.instances=set()
        statement='';module=False;ended=False
        with Path(path).open() as stream:
            for raw in stream:
                line=raw.strip()
                if not line or line.startswith('//'):continue
                if line=='endmodule':
                    if statement or not module or ended:raise ValueError('invalid module ending')
                    ended=True;continue
                if ended:raise ValueError('multiple modules or trailing unsupported text')
                statement+=' '+line
                if ';' not in line:continue
                if statement.count(';')!=1:raise ValueError('multiple or embedded statements unsupported')
                s=statement.strip();statement=''
                if s.startswith('module '):
                    if module:raise ValueError('multiple modules unsupported')
                    module=True;continue
                if not module:raise ValueError('statement outside module')
                port=re.fullmatch(r'(input|output)\s+(?:\[(\d+)\s*:\s*(\d+)\]\s*)?(\\[^\s]+|[A-Za-z_][\w$]*)\s*;',s)
                if port:
                    direction,hi,lo,name=port.groups();name=sys.intern(name)
                    bits=[name] if hi is None else [sys.intern(f'{name}[{i}]') for i in range(min(int(hi),int(lo)),max(int(hi),int(lo))+1)]
                    if name in self.interface:raise ValueError('duplicate port')
                    self.interface[name]=(direction,hi,lo,tuple(bits))
                    if direction=='input':
                        for bit in bits:self.drive(bit,('PI',bit))
                    continue
                if s.startswith('wire '):continue
                instance=re.fullmatch(r'(\w+)\s+(\\[^\s]+|[\w$]+)\s*\((.*)\)\s*;',s)
                if not instance:raise ValueError('unsupported mapped statement: '+s[:100])
                kind,name,body=instance.groups();name=sys.intern(name)
                if name in self.instances:raise ValueError('duplicate instance')
                self.instances.add(name)
                if kind not in cells:raise ValueError('unknown mapped cell: '+kind)
                spec=cells[kind];pins={};position=0
                for pin in re.finditer(r'\.([A-Za-z_][\w$]*)\s*\(\s*([^()]*)\s*\)',body):
                    if body[position:pin.start()].strip(' ,'):raise ValueError('unsupported port connection')
                    p,value=pin.groups();value=sys.intern(value.strip())
                    if p in pins:raise ValueError('duplicate cell pin')
                    if not re.fullmatch(r"(?:\\[^\s]+|[A-Za-z_$][\w$]*(?:\[\d+\])?|1'b[01])",value):
                        raise ValueError('non-scalar or unknown connection: '+value)
                    pins[p]=value;position=pin.end()
                if body[position:].strip(' ,') or set(pins)!=set(spec['ports']):raise ValueError('incomplete mapped pin list')
                if 'inout' in spec['ports'].values():raise ValueError('inout cell unsupported')
                if spec['buffer']:
                    a,y=spec['buffer'];self.drive(pins[y],('BUF',pins[a]));self.buffer_count+=1
                else:
                    if name in self.cells:raise ValueError('duplicate instance')
                    inputs=tuple((p,pins[p]) for p,d in spec['ports'].items() if d=='input')
                    self.cells[name]=(spec['signature'],inputs,kind)
                    for p,d in spec['ports'].items():
                        if d=='output':self.drive(pins[p],('CELL',name,p))
        if statement or not ended:raise ValueError('incomplete mapped module')

    def drive(self,net,driver):
        if net in self.drivers:raise ValueError('multiple drivers: '+net)
        self.drivers[net]=driver

    def source(self,net):
        chain=[];seen=set()
        while net not in self.cache:
            if net in ("1'b0","1'b1"):
                self.cache[net]=('CONST',net);break
            if net in seen:raise ValueError('buffer cycle')
            seen.add(net);chain.append(net)
            if net not in self.drivers:raise ValueError('undriven mapped signal: '+net)
            driver=self.drivers[net]
            if driver[0]!='BUF':self.cache[net]=driver;break
            net=driver[1]
        result=self.cache[net]
        for wire in chain:self.cache[wire]=result
        return result


def prove(before,after,paths):
    cells=library(paths);a=Netlist(before,cells);b=Netlist(after,cells)
    if a.interface!=b.interface:raise ValueError('primary interface changed')
    if a.cells.keys()!=b.cells.keys():raise ValueError('non-buffer instance set changed')
    resized=0;checked=0
    for name,(signature,inputs,kind) in a.cells.items():
        other,connections,kind_b=b.cells[name]
        if signature!=other:raise ValueError('logical cell function changed: '+name)
        if dict((p,a.source(net)) for p,net in inputs)!=dict((p,b.source(net)) for p,net in connections):
            raise ValueError('input driver changed: '+name)
        resized+=kind!=kind_b;checked+=len(inputs)
    outputs=0
    for name,(direction,hi,lo,bits) in a.interface.items():
        if direction!='output':continue
        for bit in bits:
            if a.source(bit)!=b.source(bit):raise ValueError('primary output driver changed: '+bit)
            outputs+=1
    return dict(status='proven',method='mapped-graph-isomorphism-after-identity-buffers-v1',
        nonbuffer_instances=len(a.cells),input_connections_checked=checked,output_bits_checked=outputs,
        before_buffers=a.buffer_count,after_buffers=b.buffer_count,function_equivalent_resized_cells=resized,
        sequential_scope='same Liberty state signatures, state-instance correspondence and every data/control/clock input',
        unsupported_changes_fail_closed=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--before',type=Path,required=True)
    parser.add_argument('--after',type=Path,required=True);parser.add_argument('--liberty',type=Path,nargs='+',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    try:result=prove(args.before,args.after,args.liberty)
    except Exception as error:
        result=dict(status='not_proven',reason=str(error));args.output.write_text(json.dumps(result)+'\n');print(result);raise SystemExit(2)
    args.output.write_text(json.dumps(result,indent=2)+'\n');print(result)
