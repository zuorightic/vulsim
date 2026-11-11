"""Successor for scalarized FF aliases and removed direct-wire aliases.

Vector reconstruction is permitted only from every exact scalar alias, or an
exact mapped consumer port connected to the word in the unchanged RTL.  No
missing variable bit or missing constant is filled from an expected mask.
"""
from types import FunctionType
import re

from . import stage67_mapped_state_v1 as parent


def verify(design,pins,contract,source,rtl):
    core=re.search(r'\bmodule\s+\w+_core\s*\([^;]*;(?P<body>.*?)\bendmodule',rtl,re.S)
    if core is None:raise ValueError('original compiled core module absent')
    body=core['body'];proof=[]
    def flatten(d,p):
        cells,aliases=parent.flatten(d,p)
        direct=re.findall(r'\bassign\s+(\w+)\s*=\s*(\w+)\s*;',body)
        for slot in contract['state_slots']:
            prefix='external_capture/' if slot['external_capture'] else 'core/'
            name=prefix+slot['name'];width=slot['declared_width']
            if name in aliases:continue
            candidates=[]
            scalar=[aliases.get(name+'['+str(i)+']') for i in range(width)]
            if all(v is not None and len(v)==1 for v in scalar):candidates.append(('all_exact_scalar_aliases',[v[0] for v in scalar]))
            if not slot['external_capture']:
                for lhs,rhs in direct:
                    if rhs==slot['name'] and 'core/'+lhs in aliases:candidates.append(('unchanged_RTL_direct_alias/core/'+lhs,aliases['core/'+lhs]))
                for line in body.splitlines():
                    match=re.search(r'\b(\w+)\s*\(([^;]*)\)\s*;',line)
                    if not match:continue
                    for port,argument in re.findall(r'\.(\w+)\s*\(\s*(\w+)\s*\)',match[2]):
                        key='core/'+match[1]+'/'+port
                        if argument==slot['name'] and key in aliases:candidates.append(('unchanged_RTL_consumer_port/'+key,aliases[key]))
            candidates=[(kind,bits) for kind,bits in candidates if len(bits)==width]
            if not candidates:continue
            vector=candidates[0][1]
            if any(bits!=vector for _,bits in candidates):raise ValueError('mapped word aliases disagree')
            for i,value in enumerate(scalar):
                if value is not None and value!=[vector[i]]:raise ValueError('mapped scalar and connected consumer differ')
            aliases[name]=vector;proof.append(dict(name=name,evidence=[kind for kind,_ in candidates],width=width))
        return cells,aliases
    namespace=dict(parent.verify.__globals__);namespace['flatten']=flatten
    value=FunctionType(parent.verify.__code__,namespace)(design,pins,contract,source)
    value.update(version='stage67-mapped-state-v2',alias_reconstruction=proof,expected_mask_never_used_to_fill_absent_alias=True)
    return value
