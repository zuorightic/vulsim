"""Exact nominal/binary32-second clock-period serialization plus strict v3 IO.

No general relative tolerance: every period token must match the requested
value or its computed IEEE binary32-second representation at write_sdc's
registered decimal precision. All other constraints retain the v3 contract.
"""
import hashlib
import math
import re
import struct
from . import sdc
from . import sdc_storage_v3 as previous
from .platforms import unit_scale

VERSION='serialized-sdc-contract-v4-binary32-period-and-IO'


def stored_period_native(nominal,native_ps):
    # Unit::userToSta(double) multiplies by a float scale; Clock stores float
    # seconds; Unit::asString(float) divides into a float scaled_value before
    # formatting. Reproduce both float assignments, not an arbitrary ULP band.
    f32=lambda value:struct.unpack('f',struct.pack('f',value))[0]
    scale=f32(native_ps*1e-12)
    return f32(f32(nominal*scale)/scale)


def verify_sdc(text,selected,period_ps,ports,*,io_delay_max_ps=None,digits=4):
    native_ps=unit_scale(1,selected['time_unit'],kind='time');nominal=period_ps/native_ps
    stored=stored_period_native(nominal,native_ps);tolerance=.500001*10**(-digits)
    normalized=[];actual={}
    for words in sdc.commands(text):
        w=list(words)
        if w[0]=='create_clock':
            if len(w) not in (5,6) or w[1]!='-name' or w[3]!='-period':raise sdc.SdcContractError('unsupported SDC clock declaration')
            if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',w[4]):raise sdc.SdcContractError('non-numeric SDC period')
            value=float(w[4])
            accepted=min(abs(value-nominal),abs(value-stored))<=tolerance
            if not math.isfinite(value) or value<=0 or not accepted:
                raise sdc.SdcContractError('SDC period outside exact nominal/binary32 storage rounding')
            if w[2] in actual:raise sdc.SdcContractError('duplicate SDC clock')
            actual[w[2]]=value;w[4]=format(nominal,'.17g')
        normalized.append(' '.join(w))
    result=previous.verify_sdc('\n'.join(normalized)+'\n',selected,period_ps,ports,io_delay_max_ps=io_delay_max_ps,digits=digits)
    result.update(version=VERSION,sdc_sha256=hashlib.sha256(text.encode()).hexdigest(),actual_clock_periods_native=actual,
        nominal_clock_period_native=nominal,binary32_stored_clock_period_native=stored,
        clock_period_storage_policy='exact Unit::userToSta scale, Clock float seconds and Unit::asString float native value; half decimal quantum only')
    return result
