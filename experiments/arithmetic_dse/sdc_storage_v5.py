"""Stage-aware exact OpenSTA clock serialization, with strict existing IO.

Clock float seconds and float unit conversion can settle after multiple SDC
read/write passes. Synthesis permits one pass; grt permits only the bounded
computed roundtrip sequence, not an arbitrary absolute/relative error band.
"""
import hashlib
import math
import re
from . import sdc
from . import sdc_storage_v3 as previous
from .sdc_storage_v4 import stored_period_native
from .platforms import unit_scale

VERSION='serialized-sdc-contract-v5-stage-exact-clock-roundtrips'


def period_values(nominal,native_ps,digits,stage):
    if stage not in ('synth','grt'):raise ValueError('explicit synth/grt serialization stage required')
    centers=[nominal];value=nominal;seen={nominal}
    for _ in range(1 if stage=='synth' else 8):
        stored=stored_period_native(value,native_ps);centers.append(stored);serialized=float(format(stored,'.'+str(digits)+'f'))
        if serialized in seen:break
        seen.add(serialized);value=serialized
    else:
        if stage=='grt':raise ValueError('clock serialization did not settle in registered eight roundtrips')
    return centers


def verify_sdc(text,selected,period_ps,ports,*,io_delay_max_ps=None,digits=4,serialization_stage='synth'):
    native_ps=unit_scale(1,selected['time_unit'],kind='time');nominal=period_ps/native_ps;tolerance=.500001*10**(-digits)
    centers=period_values(nominal,native_ps,digits,serialization_stage);normalized=[];actual={}
    for words in sdc.commands(text):
        w=list(words)
        if w[0]=='create_clock':
            if len(w) not in (5,6) or w[1]!='-name' or w[3]!='-period':raise sdc.SdcContractError('unsupported SDC clock declaration')
            if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',w[4]):raise sdc.SdcContractError('non-numeric SDC period')
            value=float(w[4])
            if not math.isfinite(value) or value<=0 or min(abs(value-c) for c in centers)>tolerance:raise sdc.SdcContractError('SDC period outside stage-exact serialized clock sequence')
            if w[2] in actual:raise sdc.SdcContractError('duplicate SDC clock')
            actual[w[2]]=value;w[4]=format(nominal,'.17g')
        normalized.append(' '.join(w))
    result=previous.verify_sdc('\n'.join(normalized)+'\n',selected,period_ps,ports,io_delay_max_ps=io_delay_max_ps,digits=digits)
    result.update(version=VERSION,sdc_sha256=hashlib.sha256(text.encode()).hexdigest(),actual_clock_periods_native=actual,
        nominal_clock_period_native=nominal,exact_serialization_centers_native=centers,serialization_stage=serialization_stage,
        clock_period_storage_policy='pinned Unit::userToSta, Clock float seconds, Unit::asString; bounded stage-specific roundtrips and half decimal quantum')
    return result
