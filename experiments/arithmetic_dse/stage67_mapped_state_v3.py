"""Mapped census permits explicit same-owner/same-lifetime state aliases.

This is a census candidate. Every aliased logical word still requires the
separate exact Boolean reset/enable/hold/update proof before qualification.
"""
from collections import defaultdict
import inspect
from types import FunctionType

from . import stage67_mapped_state_v1 as base,stage67_mapped_state_v2 as previous


def verify(design,pins,contract,source,rtl):
    text=inspect.getsource(base.verify)
    old="if resolved['cell'] in used:raise ValueError('independent state bits share a mapped FF')\n                used.add(resolved['cell']);counts[word['owner']]+=1"
    new="if resolved['cell'] not in used:counts[word['owner']]+=1\n                used.add(resolved['cell'])"
    if text.count(old)!=1:raise ValueError('frozen state census changed')
    namespace=dict(base.verify.__globals__);exec(compile(text.replace(old,new),__file__,'exec'),namespace)
    # v2's alias reconstruction executes this base function with a checked
    # flatten adapter. Inject only the changed census, preserving that adapter.
    shim=type('Base',(object,),dict(flatten=staticmethod(base.flatten),verify=staticmethod(namespace['verify'])))
    ns=dict(previous.verify.__globals__);ns['parent']=shim
    result=FunctionType(previous.verify.__code__,ns)(design,pins,contract,source,rtl)
    members=defaultdict(list)
    for word in result['words']:
        for row in word['rows']:
            if 'cell' in row:members[row['cell']].append(dict(word=word['name'],bit=row['bit'],owner=word['owner'],stage=word['stage'],
                enable=word['enable'],reset_bit=word['reset']>>row['bit']&1,valid=word['valid'],logical_output_inverted=row['logical_output_inverted']))
    groups={}
    for cell,rows in members.items():
        if len(rows)<2:continue
        keys={(r['owner'],r['stage'],r['enable'],r['reset_bit'],r['valid'],r['logical_output_inverted']) for r in rows}
        if len(keys)!=1:raise ValueError('mapped FF aliases differ in owner/stage/enable/reset/polarity')
        if len({r['word'] for r in rows})!=len(rows):raise ValueError('two variable bits inside one word share a mapped FF')
        groups[cell]=rows
    result.update(version='stage67-mapped-state-v3',physical_alias_groups=groups,logical_FF_bit_references=sum(len(v) for v in members.values()),
        unique_physical_FF_bits=len(members),alias_reset_enable_update_qualification='requires_exact_Boolean_proof_for_every_logical_reference',
        all_FFs_accounted_once=True,logical_references_preserved=True)
    return result
