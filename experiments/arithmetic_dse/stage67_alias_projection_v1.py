"""Prediction-time pure-bit state equivalence, independent of mapped FF names.

Only same-owner, stage, enable and exact bit/reset identities merge. This
projection is a candidate accounting input; existing S/node functions stay
unchanged until the normalized physical context is independently qualified.
"""
import argparse
from collections import Counter
from .model_fast_preflight import read,write
from .stage67_pure_alias_v2 import body_and_terms


def project(rtl,contract):
    words=body_and_terms(rtl,contract)[-1];members={};signatures=[];logical=0
    for name,w in words.items():
        slot=w['slot'];keys=[];reset=0
        for bit,(data,rst) in enumerate(zip(w['data'],w['reset'])):
            if data[0]=='constant':
                if data!=rst:raise ValueError('state constant update differs from reset; cannot omit FF')
                continue
            key=('native_state',slot['stage'],slot['enable_stage'],data,rst)
            keys.append(key);members.setdefault(key,[]).append((name,bit));logical+=1;reset+=rst[1]
        if len(set(keys))!=len(keys):raise ValueError('within-word repeated bits require separate projection qualification')
        signatures.append(dict(word=name,keys=frozenset(keys),logical_bits=len(keys),reset_one_bits=reset))
    # Exact same bit-set banks coalesce. Partial overlaps need their own S
    # word-count contract, so this first projection explicitly refuses them.
    sets=[s['keys'] for s in signatures if s['keys']]
    if any(a!=b and a&b for i,a in enumerate(sets) for b in sets[i+1:]):raise ValueError('partially overlapping state banks outside projection qualification')
    unique_words=len(set(sets));owners=Counter()
    for key in members:owners[key[0]]+=1
    return dict(version='pure-bit-state-projection-v1',native_logical_data_bits=logical,native_unique_data_bits=len(members),native_unique_data_signals=unique_words,
        native_unique_reset_one_bits=sum(key[-1][1] for key in members),native_enable_domains=len({key[2] for key in members}),
        equivalent_logical_bits=[[dict(word=n,bit=b) for n,b in group] for group in members.values() if len(group)>1],
        semantic_only=True,mapped_FF_names_used=False,existing_model_support_changed=False,full_D_ready=False)


def check(root,out):
    if out.exists():raise ValueError('preserve alias projection verification')
    a=read(root/'shared-probe/admission.json');rows=[]
    for t in a['tasks']:
        from pathlib import Path
        rtl=Path(t['rtl']).read_text();contract=read(t['endpoint_contract']);mapped=read(root/'shared-probe/runs'/t['id']/'mapped-state.json');p=project(rtl,contract)
        native={r['cell'] for w in mapped['words'] if w['owner']=='native_state' and not w['valid'] for r in w['rows'] if 'cell' in r}
        if len(native)!=p['native_unique_data_bits']:raise ValueError('prediction-time FF equivalence differs from actual mapped inventory')
        observed={frozenset((r['word'].split('/',1)[1],r['bit']) for r in group) for group in mapped['physical_alias_groups'].values()}
        predicted={frozenset((r['word'],r['bit']) for r in group) for group in p['equivalent_logical_bits']}
        if observed!=predicted:raise ValueError('pure projection actual alias members differ')
        rows.append(dict(task=t['id'],projection=p,actual_native_data_FF=len(native)))
    # Change a lifetime before inference: its bit-set no longer aliases.
    from copy import deepcopy
    t=a['tasks'][0];rtl=__import__('pathlib').Path(t['rtl']).read_text();c=read(t['endpoint_contract']);negative=[]
    original=rows[0]['projection']['native_unique_data_bits']
    candidates=[s for s in c['state_slots'] if not s['external_capture'] and not s['valid']]
    for field,value in [('stage',8),('enable_stage','other_enable')]:
        mutant=deepcopy(c);next(s for s in mutant['state_slots'] if s['name']==candidates[0]['name'])[field]=value
        p=project(rtl,mutant)
        if p['native_unique_data_bits']<=original:raise ValueError('different lifetime incorrectly merged')
        negative.append(dict(field=field,unique_data_bits=p['native_unique_data_bits'],prevented_merge=True))
    write(out,dict(status='passed_prediction_time_alias_projection_on_two_probes',rows=rows,negative_checks=negative,physical_context_qualified=False,full_D_ready=False))
    print('ALIAS_PROJECTION_PASS probes=2 lifetime_negative=2 no_mapped_identity_inputs',flush=True)


if __name__=='__main__':
    from pathlib import Path
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();check(a.root.resolve(),a.out.resolve())
