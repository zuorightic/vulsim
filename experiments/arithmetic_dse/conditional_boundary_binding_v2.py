"""Prospective 65--67-variable-bit reuse extension; no S parameter changes."""
import argparse
from copy import deepcopy
from pathlib import Path
import shutil

from . import conditional_boundary_binding as base
from .model_fast_preflight import read,write,sha


def new_specs():
    from .model_general_state_samples import bits,features,semantic_signature
    result=deepcopy(base.new_specs());s=result[1];packed=sum(r['reset']<<sum(x['width'] for x in s['roots'][:j]) for j,r in enumerate(s['roots']))
    pairs=[(a,b) for b in range(1,128) for a in range(b)];cursor=7121
    for j,width in [(5,65),(6,66),(7,67)]:
        w=s['words'][j];selected=[pairs[(cursor+k)%len(pairs)] for k in range(width)];cursor+=width;reset=bits('actual-state-65-67-validation/'+str(j),width)
        old=sum((((packed>>a)^(packed>>b))&1)<<k for k,(a,b) in enumerate(selected))
        w.update(declared_width=width,variable_bits=width,variable_mask=(1<<width)-1,reset=reset,source_positions=[a for a,b in selected],source_positions_second=[b for a,b in selected],invert=old^reset)
    s['slots']=[dict(name=f'data_{j}_s{k}',word=j,stage=k,variable_bits=w['variable_bits'],reset=w['reset']) for j,w in enumerate(s['words']) for k in range(w['start'],w['end']+1)]
    s['expected_FF_bits']=dict(input_service=129,native_state=sum(x['variable_bits'] for x in s['slots'])+s['depth'],external_state=sum(s['words'][j]['variable_bits'] for j in s['external_words'])+1)
    s['features']=features(s,1500);s['semantic_signature']=semantic_signature(s);return result


def prepare(out,parent):
    from .model_general_state_samples_v2 import source
    base.prepare(out)
    prior=out/'pre-extension';prior.mkdir()
    for name in ('binding-candidate.json','proposal.json'):shutil.copy2(out/name,prior/name)
    b=read(out/'binding-candidate.json');b['candidate_domain']['max_variable_word_bits']=67
    b['required_validation'].append('65_66_67_variable_bits_beyond_legacy_64bit_S_domain')
    b['extension']=dict(parent_proposal_sha256=sha(parent/'proposal.json'),parent_binding_sha256=sha(parent/'binding-candidate.json'),
        reason='actual MAC32 placements retain 65--67 variable state bits; old S 64-bit scope unchanged; new limited validation required',
        old_S_parameter_or_domain_modified=False,new_candidate_domain_is_unqualified=True)
    write(out/'binding-candidate.json',b);proposal=read(out/'proposal.json');specs={s['id']:s for s in new_specs()}
    for sid,spec in specs.items():
        d=out/'sources'/sid;old=prior/sid;shutil.copytree(d,old)
        (d/'input.sv').write_text(source(spec));write(d/'contract.json',dict(spec=spec,source_role='binding_validation',old_test_reused=False))
    for task in proposal['tasks']:
        task['rtl_sha256']=sha(task['rtl']);task['contract_sha256']=sha(task['contract'])
    proposal['frozen_candidate_sha256']=sha(out/'binding-candidate.json');proposal['parent_proposal_sha256']=sha(parent/'proposal.json')
    proposal['source_sha256'][str(Path(__file__).relative_to(base.ROOT))]=sha(Path(__file__))
    write(out/'proposal.json',proposal)
    print('REAL_VARIABLE_WIDTH_EXTENSION_PREPARED 65/66/67; old S untouched; same six validation points',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--parent',type=Path,required=True);a=p.parse_args();prepare(a.out.resolve(),a.parent.resolve())
