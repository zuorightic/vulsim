"""Check serialized OpenSTA SDC against the requested physical-unit contract.

This reads a deliberately small write_sdc dialect without evaluating Tcl. It
rejects unknown constraint commands, duplicates, missing ports and exceptions.
"""
import hashlib
import math
import re
from .platforms import unit_scale

VERSION='serialized-sdc-contract-v1'


def words(line):
    """Split the emitted Tcl words, preserving quoted/braced collections."""
    result=[];start=None;brace=0;bracket=0;quote=False;escaped=False
    for i,c in enumerate(line):
        if start is None:
            if c.isspace():continue
            start=i
        if escaped:
            escaped=False;continue
        if c=='\\':escaped=True;continue
        if brace:
            if c=='{':brace+=1
            elif c=='}':brace-=1
        elif c=='"':quote=not quote
        elif not quote:
            if c=='{':brace=1
            elif c=='[':bracket+=1
            elif c==']':bracket-=1
        if c.isspace() and not brace and not bracket and not quote:
            result.append(line[start:i]);start=None
        if bracket<0:raise ValueError('invalid SDC collection nesting')
    if brace or bracket or quote or escaped:raise ValueError('unterminated SDC word')
    if start is not None:result.append(line[start:])
    return result


def atom(value):
    if value.startswith('{') and value.endswith('}'):return value[1:-1]
    if value.startswith('"') and value.endswith('"'):return value[1:-1]
    if any(c in value for c in '[]$;\\'):raise ValueError('unsupported dynamic SDC atom')
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
    return {'inputs':sorted(n for n,d in ports.items() if d=='input' and n!='clk'),
            'outputs':sorted(n for n,d in ports.items() if d=='output')}


def verify_sdc(text,selected,period_ps,ports,*,io_delay_max_ps=None,digits=4):
    """Validate actual numeric constraints, including write_sdc rounding bounds.

    OpenSTA write_sdc defaults to four decimal places. The permitted absolute
    error is exactly half that native-unit decimal quantum, never a relative
    tolerance that could permit truncating a positive sub-unit value to zero.
    """
    time=unit_scale(1,selected['time_unit'],kind='time')
    cap=unit_scale(1,selected['capacitance_unit'],kind='capacitance')
    clocks={};transition={};uncertainty={};delays={};drivers={};loads={}
    tolerance=0.500001*10**(-digits)
    def numeric(token,expected,label):
        try:value=float(token)
        except ValueError:raise ValueError('non-numeric SDC '+label) from None
        if not math.isfinite(value) or abs(value-expected)>tolerance:
            raise ValueError(f'SDC {label} mismatch: {value} != {expected} (native units)')
        if expected>0 and value<=0:raise ValueError('SDC positive '+label+' became zero')
        return value
    def put(table,key,value):
        if key in table:raise ValueError('duplicate SDC constraint: '+str(key))
        table[key]=value
    for raw in text.replace('\\\n',' ').splitlines():
        line=raw.strip()
        if not line or line.startswith('#'):continue
        w=words(line);cmd=w[0]
        if cmd=='current_design':continue
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
    if set(clocks)!={'core_clk','io_clk'} or set(transition)!={'core_clk'}:
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
