"""Audit complete binary AIG interfaces, including constant output symbols."""
from pathlib import Path
import re


def read_aig(path):
    data=Path(path).read_bytes()
    line,body=data.split(b'\n',1);fields=line.split()
    if fields[0]!=b'aig' or len(fields)<6:raise ValueError('binary AIG required')
    maximum,inputs,latches,outputs,gates=map(int,fields[1:6])
    if latches or any(map(int,fields[6:])) or maximum!=inputs+gates:
        raise ValueError('only complete combinational AIGs supported')
    parts=body.split(b'\n',outputs)
    if len(parts)!=outputs+1:raise ValueError('truncated AIG outputs')
    literals=[int(v) for v in parts[:-1]];tail=parts[-1]
    if any(v<0 or v>2*maximum+1 for v in literals):raise ValueError('invalid AIG output literal')
    offset=0
    def delta():
        nonlocal offset
        value=0;shift=0
        while True:
            if offset>=len(tail) or shift>63:raise ValueError('truncated AIG gates')
            byte=tail[offset];offset+=1;value|=(byte&127)<<shift
            if not byte&128:return value
            shift+=7
    for index in range(gates):
        lhs=2*(inputs+index+1);rhs0=lhs-delta();rhs1=rhs0-delta()
        if not 0<=rhs1<=rhs0<lhs:raise ValueError('invalid AIG gate order')
    symbols={'input':{},'output':{}}
    for line in tail[offset:].decode('utf-8').splitlines():
        if line=='c':break
        match=re.fullmatch(r'([io])(\d+) (\S+)',line)
        if not match:raise ValueError('invalid or aliased AIG symbol')
        kind='input' if match[1]=='i' else 'output';index=int(match[2])
        if index in symbols[kind]:raise ValueError('duplicate AIG symbol')
        symbols[kind][index]=match[3]
    for kind,count in (('input',inputs),('output',outputs)):
        if set(symbols[kind])!=set(range(count)):raise ValueError('incomplete AIG symbol table')
    return inputs,outputs,literals,symbols


def full_map(aig_path,map_path,flat,inputs,outputs):
    actual_i,actual_o,literals,symbols=read_aig(aig_path)
    if (actual_i,actual_o)!=(inputs,outputs):raise ValueError('AIG boundary count mismatch')
    expected={}
    for name,port in flat['ports'].items():
        if port['direction'] not in ('input','output'):raise ValueError('unsupported AIG port')
        for i,bit in enumerate(port['bits']):
            if not isinstance(bit,int) and bit not in ('0','1'):raise ValueError('undefined AIG port')
            symbol=name if len(port['bits'])==1 else f'{name}[{i}]'
            if symbol in expected:raise ValueError('ambiguous AIG port symbol')
            expected[symbol]=(port['direction'],str(i),name,bit)
    for cell in flat['cells'].values():
        if cell['type'] not in ('$_AND_','$_NOT_'):raise ValueError('noncombinational AIG cell')
        for bits in cell['connections'].values():
            if any(not isinstance(v,int) and v not in ('0','1') for v in bits):raise ValueError('undefined AIG connection')
    full=[];constants=[];seen=set()
    for kind in ('input','output'):
        for index,symbol in sorted(symbols[kind].items()):
            if symbol not in expected or symbol in seen:raise ValueError('unmatched AIG symbol')
            direction,bitindex,name,bit=expected[symbol];seen.add(symbol)
            if direction!=kind:raise ValueError('AIG symbol direction mismatch')
            full.append([kind,str(index),bitindex,name])
            if kind=='output' and isinstance(bit,str):
                if literals[index]!=int(bit):raise ValueError('constant AIG output differs from flattened port')
                constants.append({'index':index,'symbol':symbol,'literal':int(bit)})
    if seen!=set(expected):raise ValueError('flattened interface omitted from AIG')
    short=[line.split() for line in Path(map_path).read_text().splitlines()]
    if len({tuple(v) for v in short})!=len(short) or any(v not in full for v in short):raise ValueError('invalid AIG map row')
    omitted=[v for v in full if v not in short]
    constant_indices={v['index'] for v in constants}
    if any(v[0]!='output' or int(v[1]) not in constant_indices for v in omitted):
        raise ValueError('nonconstant boundary missing from AIG map')
    return full,constants
