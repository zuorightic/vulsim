"""Check serialized OpenSTA SDC against the requested physical-unit contract.

This reads a deliberately small write_sdc dialect without evaluating Tcl. It
rejects unknown constraint commands, duplicates, missing ports and exceptions.
"""
import hashlib
import math
import re
from .platforms import unit_scale

VERSION='serialized-sdc-contract-v2'


class SdcContractError(ValueError):
    """An actual stage SDC is outside the supported contract."""


def commands(text):
    """Read one command per physical line; never evaluate archived Tcl.

    The write_sdc subset has no continuations, substitutions (other than the
    exact get_ports/get_clocks collections), or semicolon command separators.
    Reject these even in literal words: accepting more Tcl is unnecessary for
    this dialect and makes command-boundary reasoning harder.
    """
    for number,raw in enumerate(text.split('\n'),1):
        line=raw.strip(' \t\r')
        # Tcl performs backslash-newline folding even inside comments.
        if '\\' in raw:raise ValueError(f'unsupported SDC continuation or escape at line {number}')
        if not line or line.startswith('#'):continue
        if any(c in line for c in ';$\\') or any(ord(c)<32 and c!='\t' for c in line):
            raise ValueError(f'unsupported SDC command boundary or substitution at line {number}')
        yield words(line)


def words(line):
    """Tokenize literal words and a single, non-nested collection command.

    Braced bus names may contain literal brackets. Quotes cannot contain Tcl
    substitutions. A closing brace/quote/bracket must end its word, so Tcl word
    concatenation and adjacent command substitutions are rejected as well.
    """
    if any(c in line for c in ';$\\\r\n'):
        raise ValueError('unsupported SDC command boundary or substitution')
    result=[];i=0
    while i<len(line):
        if line[i] in ' \t':i+=1;continue
        start=i;first=line[i];i+=1
        if first in '{"':
            end='}' if first=='{' else '"'
            while i<len(line) and line[i]!=end:
                if line[i] in ('{}' if first=='{' else '{}[]'):
                    raise ValueError('unsupported SDC literal nesting or substitution')
                i+=1
            if i==len(line):raise ValueError('unterminated SDC word')
            i+=1
        elif first=='[':
            brace=False;quote=False
            while i<len(line):
                c=line[i]
                if brace:
                    if c=='{':raise ValueError('unsupported SDC literal nesting')
                    if c=='}':brace=False
                elif c=='"':quote=not quote
                elif quote:
                    if c in '{}[]':raise ValueError('unsupported dynamic SDC collection')
                elif c=='{':brace=True
                elif c=='[':raise ValueError('unsupported nested SDC substitution')
                elif c=='}':raise ValueError('invalid SDC collection nesting')
                elif c==']':break
                i+=1
            if i==len(line) or brace or quote:raise ValueError('unterminated SDC collection')
            i+=1
        else:
            if first in '}]':raise ValueError('invalid SDC word')
            while i<len(line) and line[i] not in ' \t':
                if line[i] in '{}[]"':raise ValueError('unsupported SDC word concatenation or substitution')
                i+=1
        if i<len(line) and line[i] not in ' \t':
            raise ValueError('unsupported SDC word concatenation')
        result.append(line[start:i])
    return result


def atom(value):
    if value.startswith('{') and value.endswith('}'):value=value[1:-1]
    elif value.startswith('"') and value.endswith('"'):value=value[1:-1]
    if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_./:]*(?:\[[0-9]+\])?',value):
        raise ValueError('unsupported dynamic or non-literal SDC atom')
    return value


def collection(value,kind):
    w=words(value[1:-1]) if value.startswith('[') and value.endswith(']') else []
    if len(w)!=2 or w[0]!='get_'+kind:raise ValueError('unsupported SDC '+kind+' collection')
    # write_sdc emits a single port (possibly with a bus index) or clock here.
    return atom(w[1])


def rtl_ports(text):
    ports={}
    for direction,high,low,name in re.findall(
            r'\b(input|output)\s+(?:wire\s+|logic\s+|reg\s+)?(?:\[(\d+)\s*:\s*(\d+)\]\s*)?(\\?[^\s,;()]+)',text):
        name=name.lstrip('\\')
        names=([name] if not high else [f'{name}[{i}]' for i in range(int(low),int(high)+1)])
        for bit in names:
            if bit in ports:raise ValueError('duplicate RTL port')
            ports[bit]=direction
    if ports.get('clk')!='input' or ports.get('rstn')!='input':raise ValueError('probe ports missing clk/rstn')
    modules=re.findall(r'\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(',text)
    if len(modules)!=1:raise ValueError('probe RTL must declare exactly one top module')
    return {'design':modules[0],'inputs':sorted(n for n,d in ports.items() if d=='input' and n!='clk'),
            'outputs':sorted(n for n,d in ports.items() if d=='output')}


def verify_sdc(text,selected,period_ps,ports,*,io_delay_max_ps=None,digits=4):
    """Apply the same fail-closed static rules at runtime and offline."""
    try:
        return _verify_sdc(text,selected,period_ps,ports,io_delay_max_ps=io_delay_max_ps,digits=digits)
    except ValueError as error:
        raise SdcContractError(str(error)) from error


def _verify_sdc(text,selected,period_ps,ports,*,io_delay_max_ps=None,digits=4):
    """Validate actual numeric constraints, including write_sdc rounding bounds.

    OpenSTA write_sdc defaults to four decimal places. The permitted absolute
    error is exactly half that native-unit decimal quantum, never a relative
    tolerance that could permit truncating a positive sub-unit value to zero.
    """
    time=unit_scale(1,selected['time_unit'],kind='time')
    cap=unit_scale(1,selected['capacitance_unit'],kind='capacitance')
    clocks={};transition={};uncertainty={};delays={};drivers={};loads={};design=None
    tolerance=0.500001*10**(-digits)
    def numeric(token,expected,label):
        if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',token):
            raise ValueError('non-numeric SDC '+label)
        try:value=float(token)
        except ValueError:raise ValueError('non-numeric SDC '+label) from None
        if not math.isfinite(value) or abs(value-expected)>tolerance:
            raise ValueError(f'SDC {label} mismatch: {value} != {expected} (native units)')
        if expected>0 and value<=0:raise ValueError('SDC positive '+label+' became zero')
        return value
    def put(table,key,value):
        if key in table:raise ValueError('duplicate SDC constraint: '+str(key))
        table[key]=value
    for w in commands(text):
        cmd=w[0]
        if cmd=='current_design':
            if len(w)!=2 or design is not None or clocks:
                raise ValueError('unsupported SDC current_design declaration')
            design=atom(w[1])
            if design!=ports['design']:raise ValueError('SDC current_design identity mismatch')
            continue
        if design is None:raise ValueError('missing SDC current_design before constraints')
        if cmd=='create_clock':
            if len(w) not in (5,6) or w[1]!='-name' or w[3]!='-period':raise ValueError('unsupported SDC clock declaration')
            name=atom(w[2]);source=collection(w[5],'ports') if len(w)==6 else None
            if (name,source) not in (('core_clk','clk'),('io_clk',None)):raise ValueError('wrong SDC clock source')
            put(clocks,name,numeric(w[4],period_ps/time,'period'))
        elif cmd=='set_clock_transition':
            if len(w)!=3:raise ValueError('unsupported SDC transition')
            name=collection(w[2],'clocks')
            put(transition,name,numeric(w[1],selected['clock_transition_ps']/time,'transition'))
        elif cmd=='set_clock_uncertainty':
            if len(w)==4 and w[1] in ('-setup','-hold'):
                kinds=[w[1][1:]];number=w[2];name=atom(w[3])
            elif len(w)==3:
                kinds=['setup','hold'];number=w[1];name=atom(w[2])
            else:raise ValueError('unsupported SDC uncertainty')
            for kind in kinds:
                put(uncertainty,(name,kind),numeric(number,selected[kind+'_uncertainty_ps']/time,kind+' uncertainty'))
        elif cmd in ('set_input_delay','set_output_delay'):
            if len(w)!=7 or w[2]!='-clock' or w[4] not in ('-min','-max') or w[5]!='-add_delay':
                raise ValueError('unsupported SDC IO delay')
            if collection(w[3],'clocks')!='io_clk':raise ValueError('IO delay uses wrong clock')
            port=collection(w[-1],'ports');kind=w[4][1:];direction='inputs' if cmd=='set_input_delay' else 'outputs'
            expected=(0 if kind=='min' else (0.2*period_ps if io_delay_max_ps is None else io_delay_max_ps)/time)
            put(delays,(direction,port,kind),numeric(w[1],expected,'IO '+kind))
        elif cmd=='set_driving_cell':
            if len(w)!=10 or w[1]!='-lib_cell' or w[3]!='-pin' or w[5]!='-input_transition_rise' or w[7]!='-input_transition_fall':
                raise ValueError('unsupported SDC driving cell')
            if atom(w[2])!=selected['driver_cell'] or atom(w[4])!=selected['driver_pin']:
                raise ValueError('SDC driver identity mismatch')
            numeric(w[6],0,'driver rise');numeric(w[8],0,'driver fall')
            put(drivers,collection(w[9],'ports'),atom(w[2]))
        elif cmd=='set_load':
            if len(w)!=4 or w[1]!='-pin_load':raise ValueError('unsupported SDC load')
            put(loads,collection(w[3],'ports'),numeric(w[2],selected['output_load_fF']/cap,'output load'))
        elif cmd=='set_propagated_clock':
            if len(w)!=2 or collection(w[1],'clocks')!='core_clk':raise ValueError('unsupported propagated clock')
        else:raise ValueError('unsupported SDC constraint command: '+cmd)
    if design is None or set(clocks)!={'core_clk','io_clk'} or set(transition)!={'core_clk'}:
        raise ValueError('missing SDC clock or transition')
    if set(uncertainty)!={(c,k) for c in clocks for k in ('setup','hold')}:
        raise ValueError('missing SDC setup/hold uncertainty')
    expected_delays={(direction,port,kind) for direction in ('inputs','outputs') for port in ports[direction] for kind in ('min','max')}
    if set(delays)!=expected_delays or set(drivers)!=set(ports['inputs']) or set(loads)!=set(ports['outputs']):
        raise ValueError('SDC IO coverage mismatch (includes reset/valid/data)')
    return {'version':VERSION,'status':'passed','sdc_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'platform':selected['platform'],'time_to_ps':time,'capacitance_to_fF':cap,
            'clock_periods_native':clocks,'clock_transition_native':transition['core_clk'],
            'setup_uncertainty_native':uncertainty['core_clk','setup'],
            'hold_uncertainty_native':uncertainty['core_clk','hold'],
            'output_load_native':next(iter(loads.values())),
            'input_ports_checked':len(ports['inputs']),'output_ports_checked':len(ports['outputs']),
            'write_sdc_decimal_digits':digits,'native_rounding_tolerance':tolerance}
