"""Recover only RTL-proven constant bits missing from a split mapped alias.

Nangate45 can retain a register's dynamic scalar aliases while deleting its
constant low part. All explicit reset/update assignments must prove the same
constant for a missing bit. Compiler masks are never a source for this proof.
"""
import re
from copy import deepcopy
from unittest.mock import patch
from . import nangate45_pipeline_alias as inherited
from . import stage67_mapped_state_v3 as mapped

INHERITED_VERIFY = inherited.verify


def verify(design, pins, contract, source, rtl):
    # This is a physical census copy. The compiler's graph, logical mask,
    # candidate features and RTL remain unchanged, including known overcounts.
    contract = deepcopy(contract)
    original = mapped.base.flatten
    proof = []
    overcounts = []

    def flatten(design, pins):
        cells, aliases = original(design, pins)
        core = re.search(r'\bmodule\s+\w+_core\s*\([^;]*;(?P<body>.*?)\bendmodule', rtl, re.S)
        if core is None:
            raise ValueError('missing unchanged native core for partial alias proof')
        body = core['body']
        widths = {name:(int(hi)-int(lo)+1 if hi else 1)
            for hi,lo,name in re.findall(r'\b(?:logic|wire|reg)\s*(?:\[(\d+):(\d+)\])?\s*(\w+)\s*;', body)}
        assignments = dict(re.findall(r'\bassign\s+(\w+)\s*=\s*([^;]+);', body))
        slices = {}
        for name,hi,lo,expr in re.findall(r'\bassign\s+(\w+)\[(\d+):(\d+)\]\s*=\s*([^;]+);', body):
            slices.setdefault(name, []).append((int(hi),int(lo),expr.strip()))
        sequential = {}
        for lhs,rhs in re.findall(r'\b(\w+)\s*<=\s*([^;]+);', body):
            sequential.setdefault(lhs, []).append(rhs)
        for slot in contract['state_slots']:
            if not slot['external_capture']:
                widths.setdefault(slot['name'], slot['declared_width'])

        def expression(text, seen):
            text = text.strip()
            while text.startswith('(') and text.endswith(')'):
                depth = 0
                whole = True
                for index,c in enumerate(text):
                    depth += (c=='(')-(c==')')
                    if depth==0 and index<len(text)-1:
                        whole = False
                        break
                if not whole:
                    break
                text = text[1:-1].strip()
            literal = re.fullmatch(r"(\d+)'([hbd])([0-9a-fA-F]+)", text)
            if literal:
                width,base,value = literal.groups()
                number = int(value, {'h':16,'b':2,'d':10}[base])
                return [str(number>>i&1) for i in range(int(width))]
            part = re.fullmatch(r'(\w+)\[(\d+)(?::(\d+))?\]', text)
            if part:
                name,hi,lo = part.groups()
                value = signal(name, seen)
                return None if value is None else value[int(lo or hi):int(hi)+1]
            if re.fullmatch(r'\w+', text):
                return signal(text, seen)
            if text.startswith('{') and text.endswith('}'):
                parts = [expression(p, seen) for p in text[1:-1].split(',')]
                if all(p is not None for p in parts):
                    return [b for p in reversed(parts) for b in p]
            return None

        def signal(name, seen):
            if name in seen:
                return [None]*widths[name] if name in widths else None
            key = 'core/'+name
            if key in aliases:
                return aliases[key]
            if name not in widths:
                return None
            result = [aliases.get(key+'['+str(i)+']', [None])[0] for i in range(widths[name])]
            seen = seen|{name}
            value = expression(assignments[name], seen) if name in assignments else None
            if value is not None and len(value)==len(result):
                result = [x if x is not None else y for x,y in zip(result,value)]
            for hi,lo,expr in slices.get(name, []):
                value = [expr[-1]]*(hi-lo+1) if expr in ("'0", "'1") else expression(expr, seen)
                if value is not None and len(value)==hi-lo+1:
                    for i,bit in enumerate(value, lo):
                        if result[i] is None:
                            result[i] = bit
            return result

        for name,expressions in sequential.items():
            if name not in widths or 'core/'+name in aliases:
                continue
            actual = signal(name, set())
            values = [expression(e, {name}) for e in expressions]
            if any(v is None or len(v)!=len(actual) for v in values):
                continue
            recovered = []
            for i,bit in enumerate(actual):
                if bit is not None:
                    continue
                candidates = {v[i] for v in values}
                if len(candidates)==1 and candidates <= {'0','1'}:
                    actual[i] = next(iter(candidates))
                    recovered.append(i)
            if recovered and all(v is not None for v in actual):
                aliases['core/'+name] = actual
                proof.append(dict(name=name, constant_bits=recovered,
                    reason='each explicit reset/update RHS has the same constant at each absent bit; implicit hold preserves it'))
                slot = next(s for s in contract['state_slots'] if s['name']==name and not s['external_capture'])
                mask = sum(int(v,16)<<(64*i) for i,v in enumerate(slot['variable_mask_hex']))
                reset = sum(int(v,16)<<(64*i) for i,v in enumerate(slot['reset_hex']))
                removed = [i for i in recovered if mask>>i&1]
                for i in removed:
                    if actual[i] != str(reset>>i&1):
                        raise ValueError('proven constant update and reset disagree')
                    mask &= ~(1<<i)
                if removed:
                    slot['variable_mask_hex'] = [format(mask>>(64*i)&((1<<64)-1),'x') for i in range((slot['declared_width']+63)//64)]
                    slot['variable_bits'] = mask.bit_count()
                    overcounts.append(dict(name=name, bits=removed, physical_census_only=True,
                        compiler_state_and_pricing_features_unchanged=True))
        return cells, aliases

    with patch.object(mapped.base, 'flatten', flatten):
        result = INHERITED_VERIFY(design, pins, contract, source, rtl)
    result['Nangate45_partial_constant_alias_proof'] = proof
    result['compiler_variable_mask_overcounts'] = overcounts
    result['original_compiler_mask_exactly_matches_physical_census'] = not overcounts
    result['origin_stage_mask_compiler_contract_checked'] = not overcounts
    result['physical_census_contract_derived_from_RTL_proof'] = True
    return result
