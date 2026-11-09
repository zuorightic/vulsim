"""Versioned interface spelling adapter, without relaxing timing constraints.

Pinned Yosys/OpenSTA serialize a literal ANSI [0:0] port as a scalar. Only that
selected-top spelling is canonicalized; widths/counts and all SDC values remain
strictly checked by the existing binary32-storage validator.
"""
import re
from . import sdc
from .sdc_storage_v3 import verify_sdc

VERSION='fast-scalar-zero-range-and-sdc-storage-v1'


def rtl_ports(text,top=None):
    original=sdc.rtl_ports(text,top);top=original['design']
    clean=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    matches=list(re.finditer(r'\bmodule\s+'+re.escape(top)+r'\s*\((.*?)\)\s*;',clean,re.S))
    if len(matches)!=1:raise ValueError('explicit unique fast RTL top required')
    match=matches[0];header=re.sub(r'\[\s*0\s*:\s*0\s*\]','',match[1])
    changed=clean[:match.start(1)]+header+clean[match.end(1):]
    normalized=sdc.rtl_ports(changed,top)
    if any(len(original[k])!=len(normalized[k]) for k in ('inputs','outputs')):
        raise ValueError('port scalarization changed interface coverage')
    return normalized
