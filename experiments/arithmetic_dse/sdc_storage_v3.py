"""Strict SDC v2 syntax plus explicit OpenSTA binary32-second IO storage.

Only IO delay tokens get a second exact expected value: the nominal physical
delay rounded once to IEEE binary32 seconds, then write_sdc decimal rounding.
This is not a relative timing tolerance or a changed constraint policy.
"""
import hashlib
import math
import re
import struct

from . import sdc as base
from .platforms import unit_scale

VERSION='serialized-sdc-contract-v3-binary32-IO-storage'


def stored_io_native(expected_ps,native_ps):
    seconds=struct.unpack('f',struct.pack('f',expected_ps*1e-12))[0]
    return seconds/(native_ps*1e-12)


def verify_sdc(text,selected,period_ps,ports,*,io_delay_max_ps=None,digits=4):
    native_ps=unit_scale(1,selected['time_unit'],kind='time');tolerance=.500001*10**(-digits)
    normalized=[];errors=[];actuals=[]
    for words in base.commands(text):
        w=list(words)
        if w[0] in ('set_input_delay','set_output_delay'):
            if len(w)!=7 or w[4] not in ('-min','-max'):raise base.SdcContractError('unsupported SDC IO delay')
            token=w[1]
            if not re.fullmatch(r'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?',token):
                raise base.SdcContractError('non-numeric SDC IO delay')
            value=float(token);expected_ps=0 if w[4]=='-min' else (.2*period_ps if io_delay_max_ps is None else io_delay_max_ps)
            expected=expected_ps/native_ps;stored=stored_io_native(expected_ps,native_ps)
            if (not math.isfinite(value) or min(abs(value-expected),abs(value-stored))>tolerance
                or expected>0 and value<=0):
                raise base.SdcContractError('SDC IO delay outside exact nominal/binary32 storage rounding')
            errors.append(abs(value-expected)*native_ps);actuals.append(value)
            w[1]=format(expected,'.17g')
        normalized.append(' '.join(w))
    result=base.verify_sdc('\n'.join(normalized)+'\n',selected,period_ps,ports,
        io_delay_max_ps=io_delay_max_ps,digits=digits)
    result.update(version=VERSION,sdc_sha256=hashlib.sha256(text.encode()).hexdigest(),
        IO_storage_model='exact IEEE binary32 seconds or nominal; decimal write_sdc rounding only',
        actual_IO_delay_native_values=sorted(set(actuals)),maximum_IO_storage_error_ps=max(errors,default=0),
        nominal_IO_max_ps=.2*period_ps if io_delay_max_ps is None else io_delay_max_ps)
    return result
